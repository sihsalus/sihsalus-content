package org.sihsalus.content;

import static org.junit.Assert.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import com.opencsv.CSVReaderHeaderAware;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.mockito.MockedStatic;
import org.openmrs.*;
import org.openmrs.aop.AuthorizationAdvice;
import org.openmrs.api.*;
import org.openmrs.api.context.Context;
import org.openmrs.messagesource.MessageSourceService;
import org.openmrs.util.ConceptReferenceRangeUtility;

/** Executes shipped SpEL criteria and Core authorization; only data services/session membership are stubbed. */
public class ReferenceRangeAccessTest {
    private static final String PROGRAM_READ = "Get Patient Programs";
    private static final String MATERNAL_PROGRAM = "3cb4ffd6-1b67-4c52-8398-4bf9844a415e";
    private static final String TEMPERATURE_RANGE = "75821f07-5a3e-4842-a499-ca7a5dc56bf6";
    private static final Path ROOT = Paths.get(System.getProperty("content.root"));
    private final Set<String> grants = new HashSet<>();
    private final AuthorizationAdvice authorization = new AuthorizationAdvice();
    private MockedStatic<Context> context;
    private ProgramWorkflowService programs;
    private List<PatientProgram> enrollment;
    private Obs observation;
    private String criteria;

    @Before
    public void setUp() throws Exception {
        criteria = rows(ROOT.resolve("configuration/conceptreferencerange/conceptreferencerange_vital_signs.csv"))
            .stream().filter(row -> TEMPERATURE_RANGE.equals(row.get("Uuid"))).findFirst().get().get("Criteria");
        Patient patient = new Patient(101);
        patient.setGender("F");
        patient.setBirthdate(Date.from(Instant.parse("2000-01-01T00:00:00Z")));
        observation = new Obs();
        observation.setPerson(patient);
        observation.setConcept(new ConceptNumeric(5088));
        observation.setObsDatetime(Date.from(Instant.parse("2026-09-14T12:00:00Z")));
        observation.setValueNumeric(36.6);
        Program program = new Program();
        program.setUuid(MATERNAL_PROGRAM);
        PatientProgram patientProgram = new PatientProgram();
        patientProgram.setProgram(program);
        enrollment = Collections.singletonList(patientProgram);
        context = mockStatic(Context.class);
        context.when(() -> Context.hasPrivilege(anyString())).thenAnswer(call -> grants.contains(call.getArgument(0)));
        context.when(Context::isAuthenticated).thenReturn(true);
        context.when(Context::getAuthenticatedUser).thenReturn(new User(101));
        MessageSourceService messages = mock(MessageSourceService.class);
        when(messages.getMessage(eq("error.privilegesRequired"), any(Object[].class), isNull()))
            .thenAnswer(call -> "Privileges required: " + Arrays.toString(call.getArgument(1, Object[].class)));
        context.when(Context::getMessageSourceService).thenReturn(messages);
        programs = mock(ProgramWorkflowService.class, call -> {
            if (call.getMethod().getName().equals("getPatientPrograms")) {
                authorization.before(call.getMethod(), call.getArguments(), call.getMock());
                return enrollment;
            }
            return RETURNS_DEFAULTS.answer(call);
        });
        context.when(Context::getProgramWorkflowService).thenReturn(programs);
        Concept gestationalAge = new Concept(102);
        ConceptService concepts = mock(ConceptService.class, call -> {
            if (call.getMethod().getName().equals("getConceptByReference")) {
                authorization.before(call.getMethod(), call.getArguments(), call.getMock());
                return gestationalAge;
            }
            return RETURNS_DEFAULTS.answer(call);
        });
        context.when(Context::getConceptService).thenReturn(concepts);
        Obs age = new Obs();
        age.setValueNumeric(22.0);
        ObsService observations = mock(ObsService.class, call -> {
            if (call.getMethod().getName().equals("getObservations")) {
                authorization.before(call.getMethod(), call.getArguments(), call.getMock());
                return Collections.singletonList(age);
            }
            return RETURNS_DEFAULTS.answer(call);
        });
        context.when(Context::getObsService).thenReturn(observations);
    }

    @After
    public void tearDown() {
        if (context != null) context.close();
    }

    @Test
    public void canonicalLaboratoryCanEvaluateTheShippedMaternalRange() throws Exception {
        useRole("Laboratorio");
        assertTrue(new ConceptReferenceRangeUtility().evaluateCriteria(criteria, observation));
    }

    @Test
    public void operationalLaboratoryCanEvaluateTheShippedMaternalRange() throws Exception {
        useRole("SIHSALUS Laboratorio");
        assertTrue(new ConceptReferenceRangeUtility().evaluateCriteria(criteria, observation));
    }

    @Test
    public void missingProgramReadIsAnAuthorizationErrorEvenWithoutEnrollment() throws Exception {
        useRole("SIHSALUS Laboratorio");
        grants.remove(PROGRAM_READ);
        enrollment = Collections.emptyList();
        APIException error = assertThrows(APIException.class,
            () -> new ConceptReferenceRangeUtility().evaluateCriteria(criteria, observation));
        assertTrue(error.getMessage().contains("evaluating criteria"));
        Throwable cause = error;
        while (cause.getCause() != null) cause = cause.getCause();
        assertTrue(cause instanceof APIAuthenticationException);
        assertTrue(cause.getMessage().contains(PROGRAM_READ));
    }

    @Test
    public void aWomanOutsideTheProgramDoesNotMatchTheMaternalRange() throws Exception {
        useRole("SIHSALUS Laboratorio");
        enrollment = Collections.emptyList();
        assertFalse(new ConceptReferenceRangeUtility().evaluateCriteria(criteria, observation));
    }

    @Test
    public void maleControlDoesNotExerciseProgramAuthorization() throws Exception {
        useRole("SIHSALUS Laboratorio");
        grants.remove(PROGRAM_READ);
        observation.getPerson().setGender("M");
        assertFalse(new ConceptReferenceRangeUtility().evaluateCriteria(criteria, observation));
        verifyNoInteractions(programs);
    }

    @Test
    public void readingProgramsDoesNotAuthorizeCreatingOrDeletingEnrollments() throws Exception {
        useRole("SIHSALUS Laboratorio");
        assertThrows(APIAuthenticationException.class, () -> authorization.before(
            ProgramWorkflowService.class.getMethod("savePatientProgram", PatientProgram.class),
            new Object[] {new PatientProgram()}, programs));
        assertThrows(APIAuthenticationException.class, () -> authorization.before(
            ProgramWorkflowService.class.getMethod("purgePatientProgram", PatientProgram.class),
            new Object[] {new PatientProgram()}, programs));
    }

    private void useRole(String name) throws Exception {
        grants.clear();
        List<Map<String, String>> roles = new ArrayList<>();
        try (Stream<Path> files = Files.list(ROOT.resolve("configuration/roles"))) {
            for (Path path : files.filter(p -> p.toString().endsWith(".csv")).collect(Collectors.toList())) roles.addAll(rows(path));
        }
        List<Map<String, String>> found = roles.stream().filter(row -> name.equals(row.get("Role name"))).collect(Collectors.toList());
        assertEquals("One metadata identity for " + name, 1, found.size());
        assertTrue("Direct clinical role; no implicit elevated inheritance", found.get(0).get("Inherited roles").trim().isEmpty());
        grants.addAll(Arrays.asList(found.get(0).get("Privileges").split(";")));
    }

    private static List<Map<String, String>> rows(Path path) throws Exception {
        List<Map<String, String>> rows = new ArrayList<>();
        try (Reader reader = Files.newBufferedReader(path); CSVReaderHeaderAware csv = new CSVReaderHeaderAware(reader)) {
            Map<String, String> row;
            while ((row = csv.readMap()) != null) rows.add(row);
        }
        return rows;
    }
}
