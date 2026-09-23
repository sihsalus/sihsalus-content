package org.sihsalus.content;

import static org.junit.Assert.*;

import com.opencsv.CSVReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.UUID;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import liquibase.Contexts;
import liquibase.LabelExpression;
import liquibase.Liquibase;
import liquibase.database.core.MariaDBDatabase;
import liquibase.database.jvm.JdbcConnection;
import liquibase.resource.DirectoryResourceAccessor;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.ClassRule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

/** Real-engine tests; intentionally not an OpenMRS or Initializer runtime test. */
public class AdmissionMigrationTest {
    static final String DATABASE = "admission_reconciliation_ci";
    static final String CANONICAL = "Admision";
    static final String LEGACY = "SIHSALUS Admision";
    static final String CANONICAL_UUID = "71dcb611-756a-4ad3-a9bb-73b6cfe28066";
    static final String RECONCILE = "reconcile-admission-role-20260907";
    static final String OPERATIONAL_RECONCILE = "reconcile-admission-operational-alias-20260921";
    static final String SUPPLEMENT_RETIREMENT = "retire-admission-hospital-supplement-20260921";
    static final String SUPPLEMENT = "SIHSALUS Admision Hospitalaria";
    static final String SUPPLEMENT_UUID = "5aaa1628-a7be-5a4f-847c-a1c593bd364e";
    static final String HISTORICAL = "normalize-admission-role-name-20260722";
    static final String CHANGELOG = "configuration/liquibase/liquibase.xml";
    private static final String OWNER = UUID.randomUUID().toString();
    private static final List<String> TABLES = List.of(
        "fixture_stock_scope_child", "fixture_unknown_role_reference", "form", "encounter_type", "concept_name",
        "stockmgmt_user_role_scope", "patientflags_tag_role", "role_role", "role_privilege",
        "user_role", "role", "privilege", "users", "liquibasechangeloglock", "liquibasechangelog", "DATABASECHANGELOG");
    private static final List<String> RBAC_TABLES = List.of(
        "role", "user_role", "role_privilege", "role_role", "patientflags_tag_role",
        "stockmgmt_user_role_scope", "fixture_stock_scope_child", "fixture_unknown_role_reference");
    private static String jdbcUrl;
    private static Set<String> historicalPrivileges;
    private static Path candidate;
    private Path resourceRoot;

    @ClassRule
    public static final TemporaryFolder temporary = new TemporaryFolder();

    static String validatePort(Map<String, String> environment) {
        if (!DATABASE.equals(environment.get("ADMISSION_TEST_DATABASE_DISPOSABLE"))) {
            throw new IllegalArgumentException("An explicitly disposable synthetic database is required");
        }
        String port = environment.getOrDefault("ADMISSION_TEST_DB_PORT", "");
        if (!port.matches("[1-9][0-9]{0,4}") || Integer.parseInt(port) > 65535) {
            throw new IllegalArgumentException("A numeric loopback service port is required");
        }
        return port;
    }

    private static Connection connection() throws Exception {
        return DriverManager.getConnection(jdbcUrl, "admission_fixture", "synthetic-fixture-only");
    }

    @BeforeClass
    public static void claimEmptySyntheticDatabase() throws Exception {
        String port = validatePort(System.getenv());
        jdbcUrl = "jdbc:mariadb://127.0.0.1:" + port + "/" + DATABASE
            + "?connectTimeout=5000&socketTimeout=20000";
        try (Connection db = connection()) {
            assertEquals("MariaDB", db.getMetaData().getDatabaseProductName());
            assertTrue("Exact MariaDB service version required",
                db.getMetaData().getDatabaseProductVersion().startsWith("10.11.7-MariaDB"));
        }
        assertEquals(DATABASE, scalar("SELECT DATABASE()"));
        assertEquals("Refuse a nonempty database, even if it has a familiar name", "0",
            scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()"));
        execute("ALTER DATABASE " + DATABASE + " CHARACTER SET utf8mb4 COLLATE utf8mb4_bin");
        execute("CREATE TABLE admission_harness_owner (owner VARCHAR(36) PRIMARY KEY) ENGINE=InnoDB");
        execute("INSERT INTO admission_harness_owner VALUES (?)", OWNER);
        Path content = Path.of(System.getProperty("content.root")).toRealPath();
        candidate = content.resolve("configuration/liquibase/liquibase.xml");
        historicalPrivileges = readHistoricalPrivileges();
        assertEquals(58, historicalPrivileges.size());
        assertTrue(historicalPrivileges.contains("Delete Relationships"));
    }

    static Set<String> readHistoricalPrivileges() throws Exception {
        return readAdmissionPrivileges(Path.of(AdmissionMigrationTest.class
            .getResource("/admission-role-1.25.15.csv").toURI()));
    }

    static Set<String> readAdmissionPrivileges(Path csv) throws Exception {
        try (CSVReader reader = new CSVReader(Files.newBufferedReader(csv, StandardCharsets.UTF_8))) {
            List<String> headers = Arrays.asList(reader.readNext());
            int uuid = headers.indexOf("Uuid");
            int role = headers.indexOf("Role name");
            int privileges = headers.indexOf("Privileges");
            int inherited = headers.indexOf("Inherited roles");
            assertTrue(uuid >= 0 && role >= 0 && privileges >= 0 && inherited >= 0);
            Set<String> result = null;
            for (String[] row; (row = reader.readNext()) != null;) {
                if (CANONICAL_UUID.equals(row[uuid])) {
                    assertNull("Only one canonical CSV role", result);
                    assertEquals(CANONICAL, row[role]);
                    assertTrue("Approved policy has no inherited roles", row[inherited].isBlank());
                    result = new TreeSet<>();
                    for (String privilege : row[privileges].split(";")) {
                        assertTrue(result.add(privilege.trim()));
                    }
                }
            }
            assertNotNull("Canonical role must be present in CSV", result);
            return result;
        }
    }

    @Before
    public void resetOnlyOwnedFixture() throws Exception {
        assertEquals(OWNER, scalar("SELECT owner FROM admission_harness_owner"));
        execute("DROP TRIGGER IF EXISTS fixture_reject_legacy_delete");
        for (String table : TABLES) {
            execute("DROP TABLE IF EXISTS " + table);
        }
        String schema;
        try (var input = getClass().getResourceAsStream("/schema.sql")) {
            assertNotNull(input);
            schema = new String(input.readAllBytes(), StandardCharsets.UTF_8);
        }
        for (String statement : schema.replaceAll("(?m)^--.*$", "").split(";")) {
            if (!statement.isBlank()) {
                execute(statement);
            }
        }
        assertEquals("utf8mb4_bin", scalar("SELECT @@collation_database"));
        for (String privilege : historicalPrivileges) {
            execute("INSERT INTO privilege VALUES (?)", privilege);
        }
        resourceRoot = temporary.newFolder().toPath();
        Path xml = resourceRoot.resolve(CHANGELOG);
        Files.createDirectories(xml.getParent());
        Files.copy(candidate, xml);
    }

    private void optionalTables() throws Exception {
        execute("CREATE TABLE patientflags_tag_role (tag_id INT NOT NULL, role VARCHAR(50) NOT NULL, "
            + "INDEX fixture_tag_index (tag_id), CONSTRAINT fixture_flags_role FOREIGN KEY (role) REFERENCES role(role)) ENGINE=InnoDB");
        execute("CREATE TABLE stockmgmt_user_role_scope (user_role_scope_id INT PRIMARY KEY, role VARCHAR(50) NOT NULL, "
            + "uuid CHAR(38) NOT NULL UNIQUE, creator INT NOT NULL, date_created DATETIME NOT NULL, audit_note TEXT, "
            + "CONSTRAINT fixture_stock_role FOREIGN KEY (role) REFERENCES role(role)) ENGINE=InnoDB");
        execute("CREATE TABLE fixture_stock_scope_child (child_id INT PRIMARY KEY, scope_id INT NOT NULL, "
            + "CONSTRAINT fixture_child_scope FOREIGN KEY (scope_id) REFERENCES stockmgmt_user_role_scope(user_role_scope_id)) ENGINE=InnoDB");
    }

    private void role(String name, String uuid, boolean previousPolicy) throws Exception {
        execute("INSERT INTO role VALUES (?, ?, ?)", name, "synthetic role", uuid);
        for (String privilege : historicalPrivileges) {
            if (!(previousPolicy && privilege.equals("Delete Relationships"))) {
                execute("INSERT INTO role_privilege VALUES (?, ?)", name, privilege);
            }
        }
    }

    private void duplicateRoles(boolean previousPolicy, boolean optional) throws Exception {
        if (optional) {
            optionalTables();
        }
        role(CANONICAL, "synthetic-canonical-uuid", previousPolicy);
        role(LEGACY, CANONICAL_UUID, previousPolicy);
        execute("INSERT INTO user_role VALUES (1, ?), (1, ?), (2, ?)", CANONICAL, LEGACY, LEGACY);
        if (optional) {
            execute("INSERT INTO patientflags_tag_role VALUES (10, ?), (10, ?), (10, ?), (20, ?), (20, ?)",
                CANONICAL, LEGACY, LEGACY, LEGACY, LEGACY);
            execute("INSERT INTO stockmgmt_user_role_scope VALUES "
                + "(1, ?, 'synthetic-scope-1', 1, '2026-01-01 00:00:00', 'synthetic audit one'), "
                + "(2, ?, 'synthetic-scope-2', 2, '2026-01-02 00:00:00', 'synthetic audit two')",
                CANONICAL, LEGACY);
            execute("INSERT INTO fixture_stock_scope_child VALUES (100, 1), (200, 2)");
        }
    }

    private void update() throws Exception {
        try (Connection db = connection(); DirectoryResourceAccessor resources = new DirectoryResourceAccessor(resourceRoot)) {
            MariaDBDatabase database = new MariaDBDatabase();
            database.setConnection(new JdbcConnection(db));
            database.setDatabaseChangeLogTableName("liquibasechangelog");
            database.setDatabaseChangeLogLockTableName("liquibasechangeloglock");
            try (Liquibase liquibase = new Liquibase(CHANGELOG, resources, database)) {
                liquibase.update(new Contexts(), new LabelExpression());
            }
        }
    }

    private void assertCanonical() throws Exception {
        assertEquals("0", scalar("SELECT COUNT(*) FROM role WHERE role = ?", LEGACY));
        assertEquals(CANONICAL_UUID, scalar("SELECT uuid FROM role WHERE role = ?", CANONICAL));
        Set<String> expected = new TreeSet<>(historicalPrivileges);
        Set<String> actual = new TreeSet<>();
        for (List<String> row : rows("SELECT privilege FROM role_privilege WHERE role = ?", CANONICAL)) {
            actual.add(row.get(0));
        }
        assertEquals("SQL explicitly converges to the approved 58-privilege contract without assuming a CSV reload", expected, actual);
        assertEquals("0", scalar("SELECT COUNT(*) FROM role_role WHERE parent_role = ? OR child_role = ?", CANONICAL, CANONICAL));
        assertEquals("EXECUTED", scalar("SELECT EXECTYPE FROM liquibasechangelog WHERE ID = ?", RECONCILE));
    }

    private Map<String, List<List<String>>> snapshot() throws Exception {
        Map<String, List<List<String>>> result = new TreeMap<>();
        for (String table : RBAC_TABLES) {
            if ("1".equals(scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ?", table))) {
                List<List<String>> data = rows("SELECT * FROM " + table);
                data.sort((left, right) -> left.toString().compareTo(right.toString()));
                result.put(table, data);
            }
        }
        return result;
    }

    private String assertRejectedWithoutRbacMutation() throws Exception {
        Map<String, List<List<String>>> before = snapshot();
        var publishedHistory = "1".equals(scalar("SELECT COUNT(*) FROM information_schema.tables "
            + "WHERE table_schema = DATABASE() AND table_name = 'liquibasechangelog'"))
            ? rows("SELECT * FROM liquibasechangelog WHERE ID = ?", RECONCILE) : List.of();
        Exception failure = assertThrows(Exception.class, this::update);
        StringBuilder causes = new StringBuilder();
        for (Throwable cause = failure; cause != null; cause = cause.getCause()) {
            causes.append(cause.getMessage());
        }
        assertTrue("Failure must come from the admission changeset, not an unrelated fixture error: " + causes,
            (causes.toString().contains(RECONCILE) || causes.toString().contains(OPERATIONAL_RECONCILE) || causes.toString().contains(SUPPLEMENT_RETIREMENT)));
        assertEquals(before, snapshot());
        assertEquals("A rejected candidate must preserve the exact published history",
            publishedHistory, rows("SELECT * FROM liquibasechangelog WHERE ID = ?", RECONCILE));
        if (causes.toString().contains(SUPPLEMENT_RETIREMENT)) {
            assertEquals("0", scalar("SELECT COUNT(*) FROM liquibasechangelog WHERE ID = ?", SUPPLEMENT_RETIREMENT));
        }
        return causes.toString();
    }

    private void assertRejectedByGuard(String guard) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        Document document = factory.newDocumentBuilder().parse(candidate.toFile());
        var checks = document.getElementsByTagName("sqlCheck");
        int evaluated = 0;
        for (int index = 0; index < checks.getLength(); index++) {
            String query = checks.item(index).getTextContent();
            if (query.contains("/* admission:" + guard + " */")) {
                // The two historical-table branches are separately optional.
                if (query.contains("FROM liquibasechangelog") && !tableExists("liquibasechangelog")) {
                    continue;
                }
                if (query.contains("FROM DATABASECHANGELOG") && !tableExists("DATABASECHANGELOG")) {
                    continue;
                }
                assertNotEquals("The intended real SQL precondition must detect this fixture: " + guard, "0", scalar(query));
                evaluated++;
            }
        }
        assertTrue("Expected guard marker in candidate XML: " + guard, evaluated > 0);
        assertRejectedWithoutRbacMutation();
    }

    private static boolean tableExists(String table) throws Exception {
        return "1".equals(scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ?", table));
    }

    private void runHistoricalChangelog() throws Exception {
        runHistoricalChangelog(false);
    }

    private void runHistoricalChangelog(boolean includeWithdrawnReconciliation) throws Exception {
        // Retain every historical changeset, its original path, and its SQL text.
        // Only the new reconciliation is absent, as on an upgrade from main.
        Path xml = resourceRoot.resolve(CHANGELOG);
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        Document document = factory.newDocumentBuilder().parse(xml.toFile());
        var changes = document.getElementsByTagName("changeSet");
        int removed = 0;
        for (int index = changes.getLength() - 1; index >= 0; index--) {
            Element change = (Element) changes.item(index);
            if (RECONCILE.equals(change.getAttribute("id")) || OPERATIONAL_RECONCILE.equals(change.getAttribute("id")) || SUPPLEMENT_RETIREMENT.equals(change.getAttribute("id"))) {
                change.getParentNode().removeChild(change);
                removed++;
            }
        }
        assertEquals("All three later reconciliation changesets are absent from the historical release", 3, removed);
        if (includeWithdrawnReconciliation) {
            Document withdrawn;
            try (var input = getClass().getResourceAsStream("/withdrawn-reconciliation.xml")) {
                assertNotNull(input);
                withdrawn = factory.newDocumentBuilder().parse(input);
            }
            var oldChanges = withdrawn.getElementsByTagName("changeSet");
            assertEquals(6, oldChanges.getLength());
            Element triage = null;
            for (int index = 0; index < changes.getLength(); index++) {
                Element change = (Element) changes.item(index);
                if ("normalize-triage-nurse-role-uuid-20260811".equals(change.getAttribute("id"))) {
                    triage = change;
                }
            }
            assertNotNull("Retain the original placement before triage normalization", triage);
            // All six original statements run, not simulated changelog rows.
            for (int index = 0; index < oldChanges.getLength(); index++) {
                document.getDocumentElement().insertBefore(document.importNode(oldChanges.item(index), true), triage);
            }
        }
        TransformerFactory.newInstance().newTransformer().transform(new DOMSource(document), new StreamResult(xml.toFile()));
        update();
        Files.copy(candidate, xml, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
    }

    private void operationalAlias(boolean optional) throws Exception {
        duplicateRoles(false, optional);
        execute("UPDATE role SET uuid = 'synthetic-operational-uuid' WHERE role = ?", LEGACY);
        execute("UPDATE role SET uuid = ? WHERE role = ?", CANONICAL_UUID, CANONICAL);
        execute("DELETE FROM role_privilege WHERE role = ?", LEGACY);
        List<String> privileges = Files.readAllLines(Path.of(getClass()
            .getResource("/admission-operational-legacy-privileges.txt").toURI()), StandardCharsets.UTF_8);
        assertEquals(55, privileges.size());
        assertEquals(55, new TreeSet<>(privileges).size());
        for (String privilege : privileges) {
            if ("0".equals(scalar("SELECT COUNT(*) FROM privilege WHERE privilege = ?", privilege))) {
                execute("INSERT INTO privilege VALUES (?)", privilege);
            }
            execute("INSERT INTO role_privilege VALUES (?, ?)", LEGACY, privilege);
        }
    }

    @Test
    public void operationalAliasAdoptsCanonicalPolicyAndPreservesReferences() throws Exception {
        operationalAlias(true);
        var stockBefore = rows("SELECT user_role_scope_id, uuid, creator, date_created, audit_note FROM stockmgmt_user_role_scope ORDER BY user_role_scope_id");
        var childrenBefore = rows("SELECT * FROM fixture_stock_scope_child ORDER BY child_id");
        update();
        assertCanonical();
        assertEquals(List.of(List.of("1", CANONICAL), List.of("2", CANONICAL)), rows("SELECT * FROM user_role ORDER BY user_id"));
        assertEquals(List.of(List.of("10", CANONICAL), List.of("20", CANONICAL)), rows("SELECT * FROM patientflags_tag_role ORDER BY tag_id"));
        assertEquals(stockBefore, rows("SELECT user_role_scope_id, uuid, creator, date_created, audit_note FROM stockmgmt_user_role_scope ORDER BY user_role_scope_id"));
        assertEquals(childrenBefore, rows("SELECT * FROM fixture_stock_scope_child ORDER BY child_id"));
        assertEquals("0", scalar("SELECT COUNT(*) FROM role_privilege WHERE role = ? AND privilege IN ('Delete Visits', 'Manage Queues', 'app:home.libroAtenciones.editar')", CANONICAL));
        var before = snapshot();
        var history = rows("SELECT * FROM liquibasechangelog ORDER BY ORDEREXECUTED");
        update();
        assertEquals(before, snapshot());
        assertEquals(history, rows("SELECT * FROM liquibasechangelog ORDER BY ORDEREXECUTED"));
    }

    @Test
    public void operationalAliasWithoutOptionalModulesConverges() throws Exception {
        operationalAlias(false);
        update();
        assertCanonical();
        assertEquals("2", scalar("SELECT COUNT(*) FROM user_role WHERE role = ?", CANONICAL));
    }

    @Test
    public void changedOperationalPolicyIsRejectedWithoutMutation() throws Exception {
        operationalAlias(false);
        execute("DELETE FROM role_privilege WHERE role = ? AND privilege = 'Delete Visits'", LEGACY);
        execute("INSERT INTO privilege VALUES ('Synthetic Unexpected Access')");
        execute("INSERT INTO role_privilege VALUES (?, 'Synthetic Unexpected Access')", LEGACY);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void operationalAliasRequiresExistingCanonicalTarget() throws Exception {
        operationalAlias(false);
        execute("DELETE FROM user_role WHERE role = ?", CANONICAL);
        execute("DELETE FROM role_privilege WHERE role = ?", CANONICAL);
        execute("DELETE FROM role WHERE role = ?", CANONICAL);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void operationalAliasRejectsUnknownReferencesBeforeMutation() throws Exception {
        operationalAlias(false);
        execute("CREATE TABLE fixture_unknown_role_reference (id INT PRIMARY KEY, role VARCHAR(50), "
            + "CONSTRAINT fixture_unknown_role FOREIGN KEY (role) REFERENCES role(role)) ENGINE=InnoDB");
        execute("INSERT INTO fixture_unknown_role_reference VALUES (1, ?)", LEGACY);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void operationalAliasDeletionFailureRollsBackAllReferences() throws Exception {
        operationalAlias(true);
        execute("CREATE TRIGGER fixture_reject_legacy_delete BEFORE DELETE ON role FOR EACH ROW "
            + "BEGIN IF OLD.role = 'SIHSALUS Admision' THEN SIGNAL SQLSTATE '45000' "
            + "SET MESSAGE_TEXT = 'synthetic operational rollback injection'; END IF; END");
        String failure = assertRejectedWithoutRbacMutation();
        assertTrue(failure.contains("synthetic operational rollback injection"));
        assertEquals("0", scalar("SELECT COUNT(*) FROM liquibasechangelog WHERE ID = ?", OPERATIONAL_RECONCILE));
        execute("DROP TRIGGER fixture_reject_legacy_delete");
        update();
        assertCanonical();
    }

    private void admissionSupplement(boolean currentPolicy, boolean optional) throws Exception {
        role(CANONICAL, CANONICAL_UUID, false);
        // Actually execute published history before introducing the later supplement.
        Path xml = resourceRoot.resolve(CHANGELOG);
        String full = Files.readString(xml);
        String previous = full.replaceFirst("(?s)\\s*<changeSet id=\"" + SUPPLEMENT_RETIREMENT + "\".*?</changeSet>", "");
        assertNotEquals(full, previous);
        Files.writeString(xml, previous);
        update();
        Files.writeString(xml, full);
        if (currentPolicy) {
            execute("INSERT INTO privilege VALUES ('app:home.libroAtenciones')");
            execute("INSERT INTO role_privilege VALUES (?, 'app:home.libroAtenciones')", CANONICAL);
        }
        if (optional) optionalTables();
        execute("INSERT INTO role VALUES (?, 'Synthetic reviewed supplement', ?)", SUPPLEMENT, SUPPLEMENT_UUID);
        List<String> privileges = Files.readAllLines(Path.of(getClass()
            .getResource("/admission-supplement-privileges.txt").toURI()), StandardCharsets.UTF_8);
        assertEquals(15, new TreeSet<>(privileges).size());
        for (String privilege : privileges) {
            if ("0".equals(scalar("SELECT COUNT(*) FROM privilege WHERE privilege = ?", privilege))) {
                execute("INSERT INTO privilege VALUES (?)", privilege);
            }
            execute("INSERT INTO role_privilege VALUES (?, ?)", SUPPLEMENT, privilege);
        }
        execute("INSERT INTO user_role VALUES (1, ?), (1, ?), (2, ?), (2, ?)", CANONICAL, SUPPLEMENT, CANONICAL, SUPPLEMENT);
    }

    @Test
    public void retiresSupplementWithoutChangingCanonicalPolicyUsersOrUnrelatedReferences() throws Exception {
        admissionSupplement(true, true);
        execute("INSERT INTO patientflags_tag_role VALUES (10, ?)", CANONICAL);
        var grants = rows("SELECT * FROM role_privilege WHERE role = ? ORDER BY privilege", CANONICAL);
        var users = rows("SELECT * FROM users ORDER BY user_id");
        var tags = rows("SELECT * FROM patientflags_tag_role ORDER BY tag_id");
        update();
        assertEquals("0", scalar("SELECT COUNT(*) FROM role WHERE role = ?", SUPPLEMENT));
        assertEquals("0", scalar("SELECT COUNT(*) FROM role_privilege WHERE role = ?", SUPPLEMENT));
        assertEquals(grants, rows("SELECT * FROM role_privilege WHERE role = ? ORDER BY privilege", CANONICAL));
        assertEquals(users, rows("SELECT * FROM users ORDER BY user_id"));
        assertEquals(tags, rows("SELECT * FROM patientflags_tag_role ORDER BY tag_id"));
        assertEquals(List.of(List.of("1", CANONICAL), List.of("2", CANONICAL)), rows("SELECT * FROM user_role ORDER BY user_id"));
        var state = snapshot();
        var history = rows("SELECT * FROM liquibasechangelog ORDER BY ORDEREXECUTED");
        update();
        assertEquals(state, snapshot());
        assertEquals(history, rows("SELECT * FROM liquibasechangelog ORDER BY ORDEREXECUTED"));
    }

    @Test
    public void supplementRetirementAlsoSupportsThe58PrivilegeBaselineWithoutOptionalModules() throws Exception {
        admissionSupplement(false, false);
        update();
        assertCanonical();
        assertEquals("0", scalar("SELECT COUNT(*) FROM role WHERE role = ?", SUPPLEMENT));
    }

    @Test
    public void supplementNeverConvertsAnUnpairedAssignmentIntoCanonicalAccess() throws Exception {
        admissionSupplement(true, false);
        execute("DELETE FROM user_role WHERE user_id = 2 AND role = ?", CANONICAL);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void changedSupplementPrivilegesFailWithoutMutation() throws Exception {
        admissionSupplement(true, false);
        execute("DELETE FROM role_privilege WHERE role = ? AND privilege = 'Delete Visits'", SUPPLEMENT);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void foreignSupplementUuidFailsWithoutMutation() throws Exception {
        admissionSupplement(true, false);
        execute("UPDATE role SET uuid = 'synthetic-unreviewed-identity' WHERE role = ?", SUPPLEMENT);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void supplementUsedForPatientFlagsRequiresReviewInsteadOfRetargetingVisibility() throws Exception {
        admissionSupplement(true, true);
        execute("INSERT INTO patientflags_tag_role VALUES (10, ?)", SUPPLEMENT);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void supplementUsedForStockRequiresReviewInsteadOfRetargetingScope() throws Exception {
        admissionSupplement(true, true);
        execute("INSERT INTO stockmgmt_user_role_scope VALUES (10, ?, 'synthetic-scope', 1, NOW(), 'preserve')", SUPPLEMENT);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void supplementInheritanceFailsWithoutMutation() throws Exception {
        admissionSupplement(true, false);
        role("Synthetic Child", "synthetic-child", false);
        execute("INSERT INTO role_role VALUES (?, 'Synthetic Child')", SUPPLEMENT);
        assertRejectedWithoutRbacMutation();
    }

    @Test
    public void supplementDeleteFailureRollsBackAssignmentsAndAllowsRetry() throws Exception {
        admissionSupplement(true, false);
        execute("CREATE TRIGGER fixture_reject_legacy_delete BEFORE DELETE ON role FOR EACH ROW BEGIN "
            + "IF OLD.role = 'SIHSALUS Admision Hospitalaria' THEN SIGNAL SQLSTATE '45000' "
            + "SET MESSAGE_TEXT = 'synthetic supplement rollback injection'; END IF; END");
        assertTrue(assertRejectedWithoutRbacMutation().contains("synthetic supplement rollback injection"));
        assertEquals("0", scalar("SELECT COUNT(*) FROM liquibasechangelog WHERE ID = ?", SUPPLEMENT_RETIREMENT));
        execute("DROP TRIGGER fixture_reject_legacy_delete");
        update();
        assertEquals("0", scalar("SELECT COUNT(*) FROM role WHERE role = ?", SUPPLEMENT));
    }

    @Test
    public void freshDatabaseLeavesRoleCreationToInitializer() throws Exception {
        update();
        assertEquals("0", scalar("SELECT COUNT(*) FROM role"));
    }

    @Test
    public void pendingHistoryWithLegacyOnlyAndAbsentOptionalModules() throws Exception {
        role(LEGACY, CANONICAL_UUID, false);
        execute("INSERT INTO user_role VALUES (1, ?)", LEGACY);
        update();
        assertCanonical();
        assertEquals(CANONICAL, scalar("SELECT role FROM user_role WHERE user_id = 1"));
        assertEquals("MARK_RAN", scalar("SELECT EXECTYPE FROM liquibasechangelog WHERE ID = ?", HISTORICAL));
    }

    @Test
    public void pendingHistoryMergesDuplicatesAndPreservesOptionalReferences() throws Exception {
        duplicateRoles(false, true);
        var auditBefore = rows("SELECT user_role_scope_id, uuid, creator, date_created, audit_note FROM stockmgmt_user_role_scope ORDER BY user_role_scope_id");
        var childrenBefore = rows("SELECT * FROM fixture_stock_scope_child ORDER BY child_id");
        update();
        assertCanonical();
        assertEquals(List.of(List.of("1", CANONICAL), List.of("2", CANONICAL)), rows("SELECT * FROM user_role ORDER BY user_id"));
        assertEquals(List.of(List.of("10", CANONICAL), List.of("20", CANONICAL)), rows("SELECT * FROM patientflags_tag_role ORDER BY tag_id"));
        assertEquals(List.of(List.of("1", CANONICAL, "synthetic-scope-1"), List.of("2", CANONICAL, "synthetic-scope-2")),
            rows("SELECT user_role_scope_id, role, uuid FROM stockmgmt_user_role_scope ORDER BY user_role_scope_id"));
        assertEquals(auditBefore, rows("SELECT user_role_scope_id, uuid, creator, date_created, audit_note FROM stockmgmt_user_role_scope ORDER BY user_role_scope_id"));
        assertEquals(childrenBefore, rows("SELECT * FROM fixture_stock_scope_child ORDER BY child_id"));
    }

    @Test
    public void previousPolicyConvergesToPublishedPermissionWithoutCsvReload() throws Exception {
        duplicateRoles(true, false);
        assertEquals("57", scalar("SELECT COUNT(*) FROM role_privilege WHERE role = ?", CANONICAL));
        assertEquals("57", scalar("SELECT COUNT(*) FROM role_privilege WHERE role = ?", LEGACY));
        update();
        assertCanonical();
        assertEquals("58", scalar("SELECT COUNT(*) FROM role_privilege WHERE role = ?", CANONICAL));
    }

    @Test
    public void mixedApprovedPoliciesPreserveExistingDeleteRelationships() throws Exception {
        duplicateRoles(true, false);
        execute("INSERT INTO role_privilege VALUES (?, 'Delete Relationships')", CANONICAL);
        update();
        assertCanonical();
    }

    @Test
    public void canonicalOnlyRetainsUserReferencesAndNormalizesUuid() throws Exception {
        role(CANONICAL, "synthetic-stale-uuid", false);
        execute("INSERT INTO user_role VALUES (1, ?)", CANONICAL);
        update();
        assertCanonical();
        assertEquals("1", scalar("SELECT COUNT(*) FROM user_role WHERE role = ?", CANONICAL));
    }

    @Test
    public void historicalExecutedChecksumRemainsValid() throws Exception {
        optionalTables();
        role(LEGACY, CANONICAL_UUID, false);
        execute("INSERT INTO user_role VALUES (1, ?)", LEGACY);
        runHistoricalChangelog();
        assertEquals("EXECUTED", scalar("SELECT EXECTYPE FROM liquibasechangelog WHERE ID = ?", HISTORICAL));
        String checksum = scalar("SELECT MD5SUM FROM liquibasechangelog WHERE ID = ?", HISTORICAL);
        update();
        assertCanonical();
        assertEquals(checksum, scalar("SELECT MD5SUM FROM liquibasechangelog WHERE ID = ?", HISTORICAL));
    }

    @Test
    public void historicalMarkRanChecksumRemainsValid() throws Exception {
        duplicateRoles(false, false);
        runHistoricalChangelog();
        assertEquals("MARK_RAN", scalar("SELECT EXECTYPE FROM liquibasechangelog WHERE ID = ?", HISTORICAL));
        String checksum = scalar("SELECT MD5SUM FROM liquibasechangelog WHERE ID = ?", HISTORICAL);
        update();
        assertCanonical();
        assertEquals(checksum, scalar("SELECT MD5SUM FROM liquibasechangelog WHERE ID = ?", HISTORICAL));
    }

    @Test
    public void secondFullRunIsIdempotent() throws Exception {
        duplicateRoles(false, true);
        update();
        var before = snapshot();
        var history = rows("SELECT ID, AUTHOR, FILENAME, MD5SUM, EXECTYPE, ORDEREXECUTED FROM liquibasechangelog ORDER BY ORDEREXECUTED");
        update();
        assertEquals(before, snapshot());
        assertEquals(history, rows("SELECT ID, AUTHOR, FILENAME, MD5SUM, EXECTYPE, ORDEREXECUTED FROM liquibasechangelog ORDER BY ORDEREXECUTED"));
    }

    @Test
    public void rejectsUnrelatedUuidOwnerBeforeMutation() throws Exception {
        role(CANONICAL, "synthetic-stale-uuid", false);
        execute("INSERT INTO role VALUES ('Synthetic Other', 'unrelated', ?)", CANONICAL_UUID);
        assertRejectedByGuard("uuid-owner");
    }

    @Test
    public void rejectsExtraPrivilegeBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("INSERT INTO privilege VALUES ('Synthetic Extra Privilege')");
        execute("INSERT INTO role_privilege VALUES (?, 'Synthetic Extra Privilege')", LEGACY);
        assertRejectedByGuard("privileges");
    }

    @Test
    public void rejectsLaterCsvGrantBeforeHistoricalReconciliation() throws Exception {
        duplicateRoles(false, false);
        execute("INSERT INTO privilege VALUES ('app:home.libroAtenciones')");
        execute("INSERT INTO role_privilege VALUES (?, 'app:home.libroAtenciones')", CANONICAL);
        assertRejectedByGuard("privileges");
    }

    @Test
    public void rejectsMissingRequiredPrivilegeBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        String required = historicalPrivileges.stream().filter(value -> !value.equals("Delete Relationships")).findFirst().orElseThrow();
        execute("DELETE FROM role_privilege WHERE role = ? AND privilege = ?", LEGACY, required);
        assertRejectedByGuard("privileges");
    }

    @Test
    public void rejectsIncomingInheritanceBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("INSERT INTO role VALUES ('Synthetic Other', '', 'synthetic-other')");
        execute("INSERT INTO role_role VALUES ('Synthetic Other', ?)", LEGACY);
        assertRejectedByGuard("inheritance");
    }

    @Test
    public void rejectsOutgoingInheritanceBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("INSERT INTO role VALUES ('Synthetic Other', '', 'synthetic-other')");
        execute("INSERT INTO role_role VALUES (?, 'Synthetic Other')", CANONICAL);
        assertRejectedByGuard("inheritance");
    }

    @Test
    public void rejectsUnknownForeignKeyBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("CREATE TABLE fixture_unknown_role_reference (id INT PRIMARY KEY, role VARCHAR(50), "
            + "CONSTRAINT fixture_unknown_role FOREIGN KEY (role) REFERENCES role(role)) ENGINE=InnoDB");
        execute("INSERT INTO fixture_unknown_role_reference VALUES (1, ?)", LEGACY);
        assertRejectedByGuard("foreign-keys");
    }

    @Test
    public void rejectsNonTransactionalOptionalTableBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("CREATE TABLE patientflags_tag_role (tag_id INT, role VARCHAR(50)) ENGINE=MyISAM");
        execute("INSERT INTO patientflags_tag_role VALUES (1, ?)", LEGACY);
        assertRejectedByGuard("engines");
    }

    @Test
    public void injectedDeleteFailureRollsBackEntireReconciliationAndAllowsRetry() throws Exception {
        duplicateRoles(true, true);
        assertEquals("57", scalar("SELECT COUNT(*) FROM role_privilege WHERE role = ?", CANONICAL));
        execute("CREATE TRIGGER fixture_reject_legacy_delete BEFORE DELETE ON role FOR EACH ROW "
            + "BEGIN IF OLD.role = 'SIHSALUS Admision' THEN SIGNAL SQLSTATE '45000' "
            + "SET MESSAGE_TEXT = 'synthetic rollback injection'; END IF; END");
        String failure = assertRejectedWithoutRbacMutation();
        assertTrue("A preflight failure is not rollback evidence", failure.contains("synthetic rollback injection"));
        execute("DROP TRIGGER fixture_reject_legacy_delete");
        update();
        assertCanonical();
        assertEquals("2", scalar("SELECT COUNT(*) FROM user_role WHERE role = ?", CANONICAL));
    }

    @Test
    public void rejectsAdditionalCopiedColumnsBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("ALTER TABLE user_role ADD COLUMN synthetic_audit VARCHAR(50) DEFAULT 'must not be discarded'");
        assertRejectedByGuard("copied-table-columns");
    }

    @Test
    public void rejectsCollationEquivalentRoleAliasBeforeMutation() throws Exception {
        role("Admision ", CANONICAL_UUID, false);
        assertRejectedByGuard("role-names");
    }

    @Test
    public void rejectsPreviouslyExecutedWithdrawnReconciliationInInitializerHistory() throws Exception {
        optionalTables();
        role(LEGACY, CANONICAL_UUID, false);
        runHistoricalChangelog(true);
        assertEquals("6", scalar("SELECT COUNT(*) FROM liquibasechangelog WHERE ID LIKE '%-20260903'"));
        assertRejectedByGuard("legacy-history");
    }

    @Test
    public void rejectsPreviouslyExecutedWithdrawnReconciliationInDefaultHistory() throws Exception {
        optionalTables();
        role(LEGACY, CANONICAL_UUID, false);
        runHistoricalChangelog(true);
        execute("RENAME TABLE liquibasechangelog TO DATABASECHANGELOG");
        assertRejectedByGuard("legacy-history");
    }

    @Test
    public void rejectsMissingNativeDeleteRelationshipsPrivilegeBeforeMutation() throws Exception {
        duplicateRoles(true, false);
        execute("DELETE FROM privilege WHERE privilege = 'Delete Relationships'");
        assertRejectedByGuard("delete-relationships-privilege");
        assertEquals("0", scalar("SELECT COUNT(*) FROM privilege WHERE privilege = 'Delete Relationships'"));
    }

    @Test
    public void rejectsMissingCorePrimaryKeyWithoutDisablingForeignKeys() throws Exception {
        duplicateRoles(false, false);
        // Retain the supporting user_id index; do not disable/drop its FK.
        execute("ALTER TABLE user_role ADD INDEX fixture_user_lookup (user_id, role)");
        execute("ALTER TABLE user_role DROP PRIMARY KEY");
        assertRejectedByGuard("core-primary-keys");
    }

    @Test
    public void rejectsMissingUuidUniquenessBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("ALTER TABLE role DROP INDEX uuid");
        assertRejectedByGuard("role-uuid-constraint");
    }

    @Test
    public void rejectsMissingCoreRoleForeignKeyBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("ALTER TABLE role_privilege DROP FOREIGN KEY fixture_role_privilege_role");
        assertRejectedByGuard("core-foreign-keys");
    }

    @Test
    public void rejectsMissingPrivilegeForeignKeyBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("ALTER TABLE role_privilege DROP FOREIGN KEY fixture_role_privilege_privilege");
        assertRejectedByGuard("privilege-foreign-key");
    }

    @Test
    public void rejectsCollationEquivalentReferenceAliasBeforeMutation() throws Exception {
        duplicateRoles(false, false);
        execute("UPDATE user_role SET role = 'SIHSALUS Admision ' WHERE role = ?", LEGACY);
        assertRejectedByGuard("reference-role-names");
    }

    private static void execute(String sql, Object... parameters) throws Exception {
        try (Connection db = connection(); PreparedStatement statement = db.prepareStatement(sql)) {
            for (int index = 0; index < parameters.length; index++) {
                statement.setObject(index + 1, parameters[index]);
            }
            statement.execute();
        }
    }

    private static List<List<String>> rows(String sql, Object... parameters) throws Exception {
        try (Connection db = connection(); PreparedStatement statement = db.prepareStatement(sql)) {
            for (int index = 0; index < parameters.length; index++) {
                statement.setObject(index + 1, parameters[index]);
            }
            try (ResultSet result = statement.executeQuery()) {
                List<List<String>> rows = new ArrayList<>();
                while (result.next()) {
                    List<String> row = new ArrayList<>();
                    for (int index = 1; index <= result.getMetaData().getColumnCount(); index++) {
                        row.add(result.getString(index));
                    }
                    rows.add(row);
                }
                return rows;
            }
        }
    }

    private static String scalar(String sql, Object... parameters) throws Exception {
        List<List<String>> rows = rows(sql, parameters);
        assertEquals("Expected exactly one scalar row", 1, rows.size());
        return rows.get(0).get(0);
    }
}
