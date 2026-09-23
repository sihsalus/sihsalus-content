package org.sihsalus.content;

import static org.junit.Assert.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

import com.opencsv.CSVReaderHeaderAware;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.mockito.MockedStatic;
import org.openmrs.*;
import org.openmrs.api.*;
import org.openmrs.api.context.Context;
import org.openmrs.api.impl.ConceptServiceImpl;
import org.openmrs.util.ConceptReferenceRangeUtility;

/** Executes the distributed criteria with Core; only clinical data services are synthetic. */
public class LaboratoryRangePopulationTest {
    private static final String PREMATURITY = "c2380004-0000-4000-8000-000000000004";
    private static final String GESTATION = "1e35f0dd-3bbb-4b45-96fd-2fc590c1b385";
    private static final String POSTPARTUM = "931c779c-10f7-4ff5-817e-d3e42155b17f";
    private static final String PRENATAL = "46107dc1-e576-4b41-9f26-04e5aaa7fa1e";
    private static final String[] PRETERM = {"f0c6d3dc-a0d2-497c-921f-b7266d448fcf",
        "a769e98e-e91f-4d4c-b029-1c66e267f32a", "0502ff16-270e-423f-8fa6-95255fdc9b19"};
    private static final String TERM = "a75289e3-427c-4e14-ad67-50fc34dcc733";
    private static final String PUERPERIUM = "1db1f541-ca0b-4f73-9396-f85588ed92a5";
    private static final String THIRD_TRIMESTER = "a486f5a4-3ca6-440f-a8dc-60aab2ea1fd3";
    private final Map<String, String> criteria = new HashMap<>();
    private final Map<String, Map<String, String>> rangeRows = new HashMap<>();
    private final Map<String, Obs> history = new HashMap<>();
    private final ConceptReferenceRangeUtility evaluator = new ConceptReferenceRangeUtility();
    private final Patient patient = new Patient(101);
    private final Obs sample = new Obs();
    private final PatientProgram enrollment = new PatientProgram();
    private MockedStatic<Context> context;
    private ConceptService concepts;

    @Before
    public void setUp() throws Exception {
        try (Reader reader = Files.newBufferedReader(Paths.get(System.getProperty("content.root"),
                "configuration/conceptreferencerange/conceptreferencerange_laboratory.csv"));
                CSVReaderHeaderAware csv = new CSVReaderHeaderAware(reader)) {
            Map<String, String> row;
            while ((row = csv.readMap()) != null) {
                criteria.put(row.get("Uuid"), row.get("Criteria"));
                rangeRows.put(row.get("Uuid"), row);
            }
        }
        patient.setGender("F");
        patient.setBirthdate(date("2025-01-01T12:00:00Z"));
        sample.setPerson(patient);
        sample.setObsDatetime(date("2025-01-08T12:00:00Z"));
        sample.setConcept(new ConceptNumeric(101));
        sample.setValueNumeric(12.0);
        Program program = new Program();
        program.setUuid("3cb4ffd6-1b67-4c52-8398-4bf9844a415e");
        enrollment.setProgram(program);

        context = mockStatic(Context.class);
        concepts = mock(ConceptService.class);
        when(concepts.getConceptByReference(anyString())).thenAnswer(call -> {
            Concept concept = new Concept(102);
            concept.setUuid(call.getArgument(0));
            return concept;
        });
        context.when(Context::getConceptService).thenReturn(concepts);
        ObsService observations = mock(ObsService.class, call -> {
            if (call.getMethod().getName().equals("getObservations")) {
                List<Concept> requested = call.getArgument(2);
                Obs value = history.get(requested.get(0).getUuid());
                return value == null ? Collections.emptyList() : Collections.singletonList(value);
            }
            return RETURNS_DEFAULTS.answer(call);
        });
        context.when(Context::getObsService).thenReturn(observations);
        ProgramWorkflowService programs = mock(ProgramWorkflowService.class, call ->
            call.getMethod().getName().equals("getPatientPrograms")
                ? Collections.singletonList(enrollment) : RETURNS_DEFAULTS.answer(call));
        context.when(Context::getProgramWorkflowService).thenReturn(programs);
    }

    @After
    public void tearDown() {
        if (context != null) context.close();
    }

    @Test
    public void termAndUnknownPrematurityDoNotSelectPretermRanges() {
        for (Double value : Arrays.asList(null, 0.0)) {
            observe(PREMATURITY, value);
            for (String range : PRETERM) assertFalse(matches(range));
            assertEquals(value != null, matches(TERM));
        }
    }

    @Test
    public void pretermRangesUseCompletedWeeksAtTheSampleDateWithoutOverlap() {
        observe(PREMATURITY, 4.0);
        for (int day : new int[] {0, 6, 7, 27, 28, 55, 56}) {
            sample.setObsDatetime(Date.from(patient.getBirthdate().toInstant().plus(day, ChronoUnit.DAYS)));
            for (int i = 0; i < PRETERM.length; i++) {
                int expected = day < 7 ? 0 : day < 28 ? 1 : day < 56 ? 2 : -1;
                assertEquals("day " + day + ", range " + i, i == expected, matches(PRETERM[i]));
            }
            assertFalse(matches(TERM));
        }
    }

    @Test
    public void futureAndInvalidPrematurityDoNotEstablishTheBirthCondition() {
        for (Double value : Arrays.asList(null, -1.0, 21.0)) {
            observe(PREMATURITY, value);
            for (String range : PRETERM) assertFalse(matches(range));
        }
        observe(PREMATURITY, 4.0);
        history.get(PREMATURITY).setObsDatetime(date("2026-01-01T12:00:00Z"));
        for (String range : PRETERM) assertFalse(matches(range));
    }

    @Test
    public void historicalNeonatalSamplesDoNotAlsoMatchCurrentAgeBands() {
        patient.setBirthdate(date("2020-01-01T12:00:00Z"));
        sample.setObsDatetime(date("2020-01-08T12:00:00Z"));
        observe(PREMATURITY, 0.0);
        for (String sex : new String[] {"M", "F"}) {
            patient.setGender(sex);
            assertTrue(matches(TERM));
            for (String uuid : Arrays.asList("e63ce18d-b109-4097-9257-0258fbd54340",
                    "ca4e4986-5945-4dd3-bba6-57cb87b267ed", "380b13ad-995a-4adc-83bc-454222e81c04",
                    "4a7b9f10-7d7b-4cb5-ab6c-3f9fe96809ed", "44dcad2a-1a4d-432a-928d-a7b2f15303c4",
                    "d42fd5b0-8aa6-44ec-8bab-8b415569da26", "7ec23591-4ea6-41ae-b97e-d06b2fe2fce1")) {
                assertFalse("An older age band must not match the neonatal sample: " + uuid, matches(uuid));
            }
        }
    }

    @Test
    public void fortyWeeksOfGestationDoesNotMeanPostpartum() {
        state(PRENATAL);
        observe(GESTATION, 40.0);
        assertFalse(matches(PUERPERIUM));
        assertTrue(matches(THIRD_TRIMESTER));
    }

    @Test
    public void postpartumUsesActiveProgramStateInsteadOfLastGestationalAge() {
        PatientState state = state(POSTPARTUM);
        observe(GESTATION, 39.0);
        assertTrue(matches(PUERPERIUM));
        assertFalse(matches(THIRD_TRIMESTER));
        state.setEndDate(date("2025-01-07T12:00:00Z"));
        assertFalse(matches(PUERPERIUM));
        state.setEndDate(null);
        state.setVoided(true);
        assertFalse(matches(PUERPERIUM));
    }

    @Test
    public void normalizedUrineRangesCannotOverrideTheAbsoluteMeasurement() {
        ConceptNumeric urine = new ConceptNumeric(5400);
        ConceptDatatype numeric = new ConceptDatatype();
        numeric.setUuid(ConceptDatatype.NUMERIC_UUID);
        urine.setDatatype(numeric);
        urine.setUnits("mg/24h");
        // Existing ConceptNumeric bounds: fallback must retain its own magnitude.
        urine.setLowNormal(1000.0);
        urine.setHiNormal(1500.0);
        urine.setHiAbsolute(5000.0);
        List<ConceptReferenceRange> shipped = new ArrayList<>();
        for (String uuid : new String[] {"45c9787e-8d00-417e-8d1b-c969dc4e0d9e",
                "90a78c49-0304-47e9-932a-cab13fde4055"}) {
            Map<String, String> row = rangeRows.get(uuid);
            ConceptReferenceRange range = new ConceptReferenceRange();
            range.setUuid(uuid);
            range.setConceptNumeric(urine);
            range.setCriteria(row.get("Criteria"));
            range.setLowNormal(Double.valueOf(row.get("Normal low")));
            range.setHiNormal(Double.valueOf(row.get("Normal high")));
            range.setHiAbsolute(Double.valueOf(row.get("Absolute high")));
            shipped.add(range);
        }
        when(concepts.getConceptReferenceRangesByConceptId(5400)).thenReturn(shipped);
        for (String sex : new String[] {"M", "F"}) {
            patient.setGender(sex);
            ConceptReferenceRange result = new ConceptServiceImpl().getConceptReferenceRange(
                new ConceptReferenceRangeContext(patient, urine, sample.getObsDatetime()));
            assertEquals(1000.0, result.getLowNormal(), 0.0);
            assertEquals(1500.0, result.getHiNormal(), 0.0);
            assertEquals(5000.0, result.getHiAbsolute(), 0.0);
        }
    }

    private PatientState state(String uuid) {
        ProgramWorkflowState definition = new ProgramWorkflowState();
        definition.setUuid(uuid);
        PatientState state = new PatientState();
        state.setState(definition);
        state.setStartDate(date("2024-12-01T12:00:00Z"));
        enrollment.setStates(new HashSet<>(Collections.singletonList(state)));
        return state;
    }

    private void observe(String concept, Double value) {
        if (value == null) {
            history.remove(concept);
            return;
        }
        Obs obs = new Obs();
        obs.setValueNumeric(value);
        obs.setObsDatetime(patient.getBirthdate());
        history.put(concept, obs);
    }

    private boolean matches(String uuid) {
        assertNotNull("Distributed range " + uuid, criteria.get(uuid));
        return evaluator.evaluateCriteria(criteria.get(uuid), sample);
    }

    private static Date date(String value) {
        return Date.from(Instant.parse(value));
    }
}
