#!/usr/bin/env python3
"""Static changelog contracts and portable, read-only SQL policy tests.

SQLite executes only the marked preflight SELECTs, unchanged. These tests do
not execute migration writes, PREPARE, Liquibase, MariaDB transactions, rollback,
Initializer, or OpenMRS authorization. The MariaDB harness covers migration
execution separately; successful policy queries are not evidence of atomicity.
"""

import csv
import hashlib
import importlib.util
import re
import sqlite3
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LIQUIBASE_PATH = (
    REPOSITORY_ROOT / "configuration/backend_configuration/liquibase/liquibase.xml"
)
ROLES_PATH = (
    REPOSITORY_ROOT / "configuration/backend_configuration/roles/roles-core.csv"
)
HISTORICAL_ROLES_PATH = REPOSITORY_ROOT / (
    ".github/integration/admission-role-reconciliation/src/test/resources/"
    "admission-role-1.25.15.csv"
)
NAMESPACE = "http://www.liquibase.org/xml/ns/dbchangelog/1.9"
CANONICAL_ROLE = "Admision"
LEGACY_ROLE = "SIHSALUS Admision"
CANONICAL_UUID = "71dcb611-756a-4ad3-a9bb-73b6cfe28066"
RECONCILIATION_ID = "reconcile-admission-role-20260907"
OPERATIONAL_RECONCILIATION_ID = "reconcile-admission-operational-alias-20260921"
SUPPLEMENT_RETIREMENT_ID = "retire-admission-hospital-supplement-20260921"
HISTORICAL_NORMALIZATION_ID = "normalize-admission-role-name-20260722"
PORTABLE_POLICY_MARKERS = (
    "uuid-owner", "privileges", "inheritance", "role-names", "reference-role-names",
    "delete-relationships-privilege",
)

# Frozen once from origin/main 8000b27f48bf124fe9a553d4ba41c678e9acc231.
# Hashes cover each literal <changeSet ...>...</changeSet> block, not a SQLite
# translation or a regenerated XML representation. Running tests needs no Git.
HISTORICAL_CHANGE_SET_SHA256 = {
    "increase-name-varchar-20250325":
        "59c582f5f48e91281f757847449230bf667abf8d76a0b32ecb1e8c5d727a6bf4",
    "ensure-canonical-visit-note-encounter-type-20260823":
        "eef386716089b3a6b74d4c1b79867fff5d034ae41715d666859eab8d22132f38",
    "ensure-canonical-visit-note-form-20260823":
        "909b60bb4919b9d9331e1456247de0e99636a7568e4c9d021e03ab1505814766",
    "link-canonical-visit-note-form-encounter-type-20260823":
        "fdc6b2dff5c8d01115f4103081f264bf9e11ae1200b87b4be5acd0370dd4b534",
    "assert-canonical-visit-note-form-contract-20260823":
        "950262c079f2494d0f2803cba2ca3f9c057fa25c8b35d3c45b256dbc48b1a1a0",
    "retire-legacy-ce001-form-1-0-1-20260825":
        "60b601b5a638fb8dfc8db9ca24c6a2fe2d634792e41cf2ebbfe5c9031e3421eb",
    "assert-exclusive-canonical-ce001-form-20260825":
        "67619d5422d22bfd8421872f03e529cd97f16558eec0e881aba83ffce5c22305",
    "normalize-admission-role-name-20260722":
        "bbe7ac66c3789d7059b21f2f42e19d9ce134934c4fc775bb39a4edfb5cd56f92",
    "normalize-triage-nurse-role-uuid-20260811":
        "bd6d8d59e7dc3dd79fff505477031ace5e37f4b26045387ee9a7e45823f05fa8",
}

# Share the frozen 1.25.15 fixture with MariaDB tests, not the current CSV.
# The byte-level check below prevents this historical input from drifting with
# the migration. Its source is recorded in the integration README.
with HISTORICAL_ROLES_PATH.open(newline="", encoding="utf-8-sig") as handle:
    historical_role, = csv.DictReader(handle)
APPROVED_PRIVILEGES = frozenset(
    privilege.strip() for privilege in historical_role["Privileges"].split(";")
)
PREVIOUS_PRIVILEGES = APPROVED_PRIVILEGES - {"Delete Relationships"}
CURRENT_PRIVILEGES = APPROVED_PRIVILEGES | {"app:home.libroAtenciones"}


def get_change_sets():
    return ET.parse(LIQUIBASE_PATH).getroot().findall(f"{{{NAMESPACE}}}changeSet")


def get_reconciliation():
    matches = [
        item for item in get_change_sets()
        if item.get("id") == RECONCILIATION_ID
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected exactly one {RECONCILIATION_ID}, found {len(matches)}"
        )
    return matches[0]


def get_policy_check(marker):
    matches = [
        item
        for item in get_reconciliation().findall(f".//{{{NAMESPACE}}}sqlCheck")
        if f"/* admission:{marker} */" in "".join(item.itertext())
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one admission:{marker} sqlCheck, found {len(matches)}"
        )
    return matches[0]


def get_policy_query(marker):
    return "".join(get_policy_check(marker).itertext()).strip()


def snapshot(connection):
    return tuple(connection.iterdump())


class AdmissionChangelogStructureTest(unittest.TestCase):
    def test_reviewed_migrations_precede_historical_normalization(self):
        ids = [item.get("id") for item in get_change_sets()]
        expected = list(HISTORICAL_CHANGE_SET_SHA256)
        expected.insert(
            expected.index(HISTORICAL_NORMALIZATION_ID), RECONCILIATION_ID
        )
        expected.insert(expected.index(RECONCILIATION_ID), OPERATIONAL_RECONCILIATION_ID)
        expected.insert(expected.index(HISTORICAL_NORMALIZATION_ID) + 1, SUPPLEMENT_RETIREMENT_ID)
        self.assertEqual(expected, ids)

    def test_published_change_sets_are_byte_for_byte_unchanged(self):
        blocks = re.findall(
            r"<changeSet\b.*?</changeSet>",
            LIQUIBASE_PATH.read_text(encoding="utf-8"),
            re.DOTALL,
        )
        by_id = {}
        for block in blocks:
            identifier = ET.fromstring(block).get("id")
            self.assertNotIn(identifier, by_id)
            by_id[identifier] = hashlib.sha256(block.encode()).hexdigest()
        published = {
            **HISTORICAL_CHANGE_SET_SHA256,
            # Published by #223; its preconditions and SQL are now immutable too.
            RECONCILIATION_ID:
                "d2deb4caccce550305b335840175e769e8bd3d35cd1185de1cd966f715b5eef8",
        }
        for identifier, digest in published.items():
            with self.subTest(change_set=identifier):
                self.assertEqual(digest, by_id.get(identifier))

    def test_historical_policy_fixture_is_byte_for_byte_unchanged(self):
        self.assertEqual(
            "7564e74ee357e422f8a33eff6b76c158c2da715ea7623b722b001702df0b579e",
            hashlib.sha256(HISTORICAL_ROLES_PATH.read_bytes()).hexdigest(),
        )

    def test_historical_sql_policy_and_current_csv_policy_remain_distinct(self):
        for path, expected in (
            (HISTORICAL_ROLES_PATH, APPROVED_PRIVILEGES),
            (ROLES_PATH, CURRENT_PRIVILEGES),
        ):
            with self.subTest(path=path):
                with path.open(newline="", encoding="utf-8-sig") as handle:
                    roles = [
                        row for row in csv.DictReader(handle)
                        if row["Uuid"] == CANONICAL_UUID
                        or row["Role name"] == CANONICAL_ROLE
                    ]
                self.assertEqual(1, len(roles))
                role = roles[0]
                self.assertEqual(CANONICAL_ROLE, role["Role name"])
                self.assertEqual(CANONICAL_UUID, role["Uuid"])
                self.assertEqual("", role["Inherited roles"])
                self.assertEqual(
                    expected,
                    {privilege.strip() for privilege in role["Privileges"].split(";")},
                )
        spec = importlib.util.spec_from_file_location(
            "admission_csv_validator",
            Path(__file__).with_name("validate_csv_widths.py"),
        )
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        self.assertEqual(
            CURRENT_PRIVILEGES, validator.ADMISSION_REQUIRED_PRIVILEGES
        )
        self.assertEqual(CANONICAL_UUID, validator.ADMISSION_ROLE_UUID)
        self.assertEqual(CANONICAL_ROLE, validator.ADMISSION_ROLE_NAME)
        literals = set(re.findall(r"'([^']*)'", get_policy_query("privileges")))
        self.assertEqual(
            APPROVED_PRIVILEGES, literals - {CANONICAL_ROLE, LEGACY_ROLE}
        )
        self.assertEqual(58, len(APPROVED_PRIVILEGES))
        self.assertEqual(57, len(PREVIOUS_PRIVILEGES))
        self.assertEqual(59, len(CURRENT_PRIVILEGES))


class AdmissionPortablePolicyTest(unittest.TestCase):
    def database(self, roles=()):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript("""
            CREATE TABLE role (
                role TEXT COLLATE NOCASE PRIMARY KEY,
                description TEXT, uuid TEXT UNIQUE NOT NULL
            );
            CREATE TABLE privilege (privilege TEXT PRIMARY KEY);
            INSERT INTO privilege VALUES ('Delete Relationships');
            CREATE TABLE role_privilege (
                role TEXT NOT NULL REFERENCES role(role), privilege TEXT NOT NULL,
                PRIMARY KEY (role, privilege)
            );
            CREATE TABLE role_role (
                parent_role TEXT NOT NULL REFERENCES role(role),
                child_role TEXT NOT NULL REFERENCES role(role),
                PRIMARY KEY (parent_role, child_role)
            );
            CREATE TABLE user_role (
                user_id INTEGER NOT NULL, role TEXT NOT NULL REFERENCES role(role),
                PRIMARY KEY (user_id, role)
            );
            CREATE TABLE synthetic_unrelated_state (id INTEGER PRIMARY KEY, value TEXT);
            INSERT INTO synthetic_unrelated_state VALUES (1, 'synthetic-sentinel');
        """)
        self.add_role(
            connection, "Other", "synthetic-other-uuid",
            {"Synthetic unrelated privilege"},
        )
        self.add_role(
            connection, "Other child", "synthetic-other-child-uuid", set()
        )
        connection.execute("INSERT INTO role_role VALUES ('Other', 'Other child')")
        for name, uuid, privileges in roles:
            self.add_role(connection, name, uuid, privileges)
        return connection

    @staticmethod
    def add_role(connection, name, uuid, privileges):
        connection.execute(
            "INSERT INTO role VALUES (?, 'synthetic role', ?)", (name, uuid)
        )
        connection.executemany(
            "INSERT INTO role_privilege VALUES (?, ?)",
            [(name, privilege) for privilege in sorted(privileges)],
        )
        connection.execute("INSERT INTO user_role VALUES (1, ?)", (name,))

    def assert_policy(self, connection, rejected_by=None):
        before = snapshot(connection)
        changes_before = connection.total_changes
        results = {
            marker: connection.execute(get_policy_query(marker)).fetchone()[0]
            for marker in PORTABLE_POLICY_MARKERS
        }
        self.assertEqual(before, snapshot(connection))
        self.assertEqual(changes_before, connection.total_changes)
        if rejected_by is None:
            self.assertEqual(dict.fromkeys(PORTABLE_POLICY_MARKERS, 0), results)
        else:
            self.assertGreater(results[rejected_by], 0)
        return results

    def test_absent_admission_roles_pass_read_only_policy_for_initializer(self):
        self.assert_policy(self.database())

    def test_absent_roles_do_not_require_or_create_the_native_privilege(self):
        connection = self.database()
        connection.execute("DELETE FROM privilege")
        self.assert_policy(connection)

    def test_existing_identity_requires_exact_native_delete_relationships_privilege(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for native_privilege in (None, "delete relationships", "Delete Relationships "):
                with self.subTest(role=role, native_privilege=native_privilege):
                    connection = self.database([
                        (role, CANONICAL_UUID, PREVIOUS_PRIVILEGES)
                    ])
                    connection.execute("DELETE FROM privilege")
                    if native_privilege is not None:
                        connection.execute(
                            "INSERT INTO privilege VALUES (?)", (native_privilege,)
                        )
                    self.assert_policy(connection, "delete-relationships-privilege")

    def test_each_identity_accepts_both_approved_privilege_variants(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for privileges in (PREVIOUS_PRIVILEGES, APPROVED_PRIVILEGES):
                with self.subTest(role=role, privileges=len(privileges)):
                    self.assert_policy(
                        self.database([(role, CANONICAL_UUID, privileges)])
                    )

    def test_duplicate_identities_accept_all_combinations_of_the_two_approved_variants(self):
        for canonical_privileges in (PREVIOUS_PRIVILEGES, APPROVED_PRIVILEGES):
            for legacy_privileges in (PREVIOUS_PRIVILEGES, APPROVED_PRIVILEGES):
                with self.subTest(
                    canonical=len(canonical_privileges),
                    legacy=len(legacy_privileges),
                ):
                    self.assert_policy(self.database([
                        (CANONICAL_ROLE, "synthetic-stale-canonical-uuid", canonical_privileges),
                        (LEGACY_ROLE, CANONICAL_UUID, legacy_privileges),
                    ]))

    def test_read_only_policy_is_repeatable_without_changing_any_table(self):
        connection = self.database([
            (CANONICAL_ROLE, "synthetic-stale-canonical-uuid", PREVIOUS_PRIVILEGES),
            (LEGACY_ROLE, CANONICAL_UUID, APPROVED_PRIVILEGES),
        ])
        self.assertEqual(
            self.assert_policy(connection), self.assert_policy(connection)
        )

    def test_rejects_each_missing_required_privilege_from_either_identity(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for privilege in sorted(PREVIOUS_PRIVILEGES):
                for approved in (PREVIOUS_PRIVILEGES, APPROVED_PRIVILEGES):
                    with self.subTest(
                        role=role, missing=privilege, variant=len(approved)
                    ):
                        self.assert_policy(
                            self.database([
                                (role, CANONICAL_UUID, approved - {privilege})
                            ]),
                            "privileges",
                        )

    def test_rejects_extra_privileges_in_either_identity(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for extra in (
                "Purge Relationships", "Manage Roles", "Get Global Properties",
                "Synthetic extra privilege",
            ):
                for approved in (PREVIOUS_PRIVILEGES, APPROVED_PRIVILEGES):
                    with self.subTest(role=role, extra=extra, variant=len(approved)):
                        self.assert_policy(
                            self.database([
                                (role, CANONICAL_UUID, approved | {extra})
                            ]),
                            "privileges",
                        )

    def test_valid_identity_does_not_mask_an_unsafe_second_identity(self):
        for unsafe_role in (CANONICAL_ROLE, LEGACY_ROLE):
            with self.subTest(unsafe_role=unsafe_role):
                roles = [
                    (CANONICAL_ROLE, "synthetic-stale-uuid", APPROVED_PRIVILEGES),
                    (LEGACY_ROLE, CANONICAL_UUID, PREVIOUS_PRIVILEGES),
                ]
                roles = [
                    (name, uuid, privileges | {"Purge Relationships"})
                    if name == unsafe_role else (name, uuid, privileges)
                    for name, uuid, privileges in roles
                ]
                self.assert_policy(self.database(roles), "privileges")

    def test_rejects_complementary_partial_lists_even_when_union_is_approved(self):
        first_half = frozenset(sorted(APPROVED_PRIVILEGES)[:29])
        second_half = APPROVED_PRIVILEGES - first_half
        self.assertEqual(APPROVED_PRIVILEGES, first_half | second_half)
        self.assert_policy(self.database([
            (CANONICAL_ROLE, "synthetic-stale-uuid", first_half),
            (LEGACY_ROLE, CANONICAL_UUID, second_half),
        ]), "privileges")

    def test_rejects_ascii_case_variants_of_privilege_names(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            with self.subTest(role=role):
                privileges = (
                    APPROVED_PRIVILEGES - {"Get Patients"}
                ) | {"get patients"}
                self.assert_policy(
                    self.database([(role, CANONICAL_UUID, privileges)]),
                    "privileges",
                )

    def test_rejects_case_and_space_variants_of_role_names(self):
        # SQLite's own NOCASE collation makes these aliases compare equal.
        # This does not model MariaDB accent or trailing-space collations.
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for alias in (role.lower(), role + " ", " " + role):
                with self.subTest(role=role, alias=alias):
                    self.assert_policy(self.database([
                        (alias, CANONICAL_UUID, APPROVED_PRIVILEGES)
                    ]), "role-names")

    def test_rejects_reference_aliases_without_changing_any_table(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for table in ("user_role", "role_privilege"):
                with self.subTest(role=role, table=table):
                    connection = self.database([
                        (role, CANONICAL_UUID, APPROVED_PRIVILEGES)
                    ])
                    # Table names are the fixed fixture tables above. SQLite
                    # NOCASE on the referenced key permits these alias rows.
                    connection.execute(
                        f"UPDATE {table} SET role = ? WHERE role = ?",
                        (role.lower(), role),
                    )
                    self.assert_policy(connection, "reference-role-names")

    def test_rejects_replacing_a_required_privilege_even_when_count_is_unchanged(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            with self.subTest(role=role):
                privileges = (
                    APPROVED_PRIVILEGES - {"Get Patients"}
                ) | {"Purge Relationships"}
                self.assert_policy(
                    self.database([(role, CANONICAL_UUID, privileges)]),
                    "privileges",
                )

    def test_rejects_an_empty_privilege_set_for_an_existing_identity(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            with self.subTest(role=role):
                self.assert_policy(
                    self.database([(role, CANONICAL_UUID, set())]), "privileges"
                )

    def test_rejects_inheritance_in_both_directions_for_either_identity(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for parent, child in ((role, "Other"), ("Other", role), (role, role)):
                with self.subTest(parent=parent, child=child):
                    connection = self.database([
                        (role, CANONICAL_UUID, APPROVED_PRIVILEGES)
                    ])
                    connection.execute(
                        "INSERT INTO role_role VALUES (?, ?)", (parent, child)
                    )
                    self.assert_policy(connection, "inheritance")

    def test_rejects_inheritance_between_the_two_identities(self):
        for parent, child in (
            (CANONICAL_ROLE, LEGACY_ROLE), (LEGACY_ROLE, CANONICAL_ROLE)
        ):
            with self.subTest(parent=parent, child=child):
                connection = self.database([
                    (CANONICAL_ROLE, "synthetic-stale-canonical-uuid", APPROVED_PRIVILEGES),
                    (LEGACY_ROLE, CANONICAL_UUID, PREVIOUS_PRIVILEGES),
                ])
                connection.execute(
                    "INSERT INTO role_role VALUES (?, ?)", (parent, child)
                )
                self.assert_policy(connection, "inheritance")

    def test_rejects_canonical_uuid_owned_by_a_third_role_without_any_changes(self):
        for role in (CANONICAL_ROLE, LEGACY_ROLE):
            for uuid in (
                CANONICAL_UUID, CANONICAL_UUID.upper(), " " + CANONICAL_UUID + " ",
            ):
                with self.subTest(role=role, uuid=uuid):
                    connection = self.database([
                        (role, "synthetic-stale-uuid", APPROVED_PRIVILEGES)
                    ])
                    connection.execute(
                        "UPDATE role SET uuid = ? WHERE role = 'Other'", (uuid,),
                    )
                    self.assert_policy(connection, "uuid-owner")

    def test_rejects_uuid_collision_even_when_both_admission_identities_are_absent(self):
        for uuid in (
            CANONICAL_UUID, CANONICAL_UUID.upper(), " " + CANONICAL_UUID + " ",
        ):
            with self.subTest(uuid=uuid):
                connection = self.database()
                connection.execute(
                    "UPDATE role SET uuid = ? WHERE role = 'Other'", (uuid,)
                )
                self.assert_policy(connection, "uuid-owner")


class OperationalAdmissionAliasPolicyTest(unittest.TestCase):
    def setUp(self):
        self.change = next(item for item in get_change_sets() if item.get("id") == OPERATIONAL_RECONCILIATION_ID)
        self.legacy = frozenset((REPOSITORY_ROOT / ".github/integration/admission-role-reconciliation/src/test/resources/admission-operational-legacy-privileges.txt").read_text().splitlines())
        self.assertEqual(55, len(self.legacy))
        self.helper = AdmissionPortablePolicyTest()
        self.addCleanup(self.helper.doCleanups)

    def query(self, marker):
        checks = [item for item in self.change.findall(f".//{{{NAMESPACE}}}sqlCheck")
                  if f"/* operational-admission:{marker} */" in "".join(item.itertext())]
        self.assertEqual(1, len(checks))
        return "".join(checks[0].itertext()).strip()

    def database(self, legacy=None, canonical=None):
        return self.helper.database([
            (CANONICAL_ROLE, CANONICAL_UUID, APPROVED_PRIVILEGES if canonical is None else canonical),
            (LEGACY_ROLE, "synthetic-operational-uuid", self.legacy if legacy is None else legacy),
        ])

    def test_published_reconciliation_bytes_are_unchanged(self):
        block = re.search(r'<changeSet id="reconcile-admission-role-20260907".*?</changeSet>', LIQUIBASE_PATH.read_text(), re.DOTALL).group()
        self.assertEqual("d2deb4caccce550305b335840175e769e8bd3d35cd1185de1cd966f715b5eef8", hashlib.sha256(block.encode()).hexdigest())

    def test_reviewed_input_has_one_canonical_target(self):
        db = self.database()
        for marker, expected in (("scope", 1), ("canonical-target", 1), ("legacy-policy", 0), ("privileges", 0)):
            self.assertEqual(expected, db.execute(self.query(marker)).fetchone()[0], marker)

    def test_every_unapproved_replacement_in_the_55_entry_input_is_rejected(self):
        for privilege in sorted(self.legacy):
            with self.subTest(privilege=privilege):
                db = self.database((self.legacy - {privilege}) | {"Synthetic unexpected access"})
                self.assertEqual(1, db.execute(self.query("scope")).fetchone()[0])
                self.assertEqual(1, db.execute(self.query("legacy-policy")).fetchone()[0])

    def test_changed_canonical_target_cannot_authorize_cleanup(self):
        db = self.database(canonical=(APPROVED_PRIVILEGES - {"Add Patients"}) | {"Synthetic unexpected access"})
        self.assertEqual(1, db.execute(self.query("privileges")).fetchone()[0])

    def test_ordinary_historical_inputs_remain_owned_by_published_migration(self):
        for privileges in (APPROVED_PRIVILEGES, PREVIOUS_PRIVILEGES):
            db = self.database(legacy=privileges)
            self.assertEqual(0, db.execute(self.query("scope")).fetchone()[0])

    def test_cleanup_never_unions_legacy_privileges_or_creates_an_alternate_role(self):
        sql = "".join(self.change.find(f"{{{NAMESPACE}}}sql").itertext())
        self.assertNotRegex(sql, r"(?i)INSERT\s+INTO\s+(?:role_privilege|role)\s*\(")
        self.assertNotRegex(sql, r"(?i)UPDATE\s+role_privilege")
        self.assertIn("INSERT INTO user_role", sql)
        self.assertIn("DELETE FROM role WHERE @canonicalize_admission_alias = 1", sql)
        self.assertEqual("true", self.change.get("runInTransaction"))
        self.assertEqual("HALT", self.change.find(f"{{{NAMESPACE}}}preConditions").get("onFail"))


class AdmissionSupplementPolicyTest(unittest.TestCase):
    NAME = "SIHSALUS Admision Hospitalaria"
    UUID = "5aaa1628-a7be-5a4f-847c-a1c593bd364e"

    def setUp(self):
        self.change = next(item for item in get_change_sets() if item.get("id") == SUPPLEMENT_RETIREMENT_ID)
        self.privileges = frozenset((REPOSITORY_ROOT / ".github/integration/admission-role-reconciliation/src/test/resources/admission-supplement-privileges.txt").read_text().splitlines())
        self.assertEqual(15, len(self.privileges))
        self.helper = AdmissionPortablePolicyTest()
        self.addCleanup(self.helper.doCleanups)

    def query(self, marker):
        matches = [item for item in self.change.findall(f".//{{{NAMESPACE}}}sqlCheck")
                   if f"/* admission-supplement:{marker} */" in "".join(item.itertext())]
        self.assertEqual(1, len(matches))
        return "".join(matches[0].itertext()).strip()

    def database(self, canonical=None, supplement=None):
        db = self.helper.database([
            (CANONICAL_ROLE, CANONICAL_UUID, APPROVED_PRIVILEGES if canonical is None else canonical),
            (self.NAME, self.UUID, self.privileges if supplement is None else supplement),
        ])
        return db

    def test_known_supplement_accepts_only_supported_canonical_policies(self):
        for policy in (APPROVED_PRIVILEGES, APPROVED_PRIVILEGES | {"app:home.libroAtenciones"}):
            db = self.database(canonical=policy)
            for marker, expected in (("scope", 1), ("canonical-target", 1), ("supplement-identity", 1),
                                     ("privileges", 0), ("legacy-policy", 0), ("paired-users", 0),
                                     ("inheritance", 0), ("unreconciled-alias", 0)):
                self.assertEqual(expected, db.execute(self.query(marker)).fetchone()[0], marker)

    def test_each_changed_supplement_privilege_fails_the_frozen_contract(self):
        for privilege in self.privileges:
            with self.subTest(privilege=privilege):
                db = self.database(supplement=(self.privileges - {privilege}) | {"Synthetic Unexpected Access"})
                self.assertEqual(1, db.execute(self.query("scope")).fetchone()[0])
                self.assertEqual(1, db.execute(self.query("legacy-policy")).fetchone()[0])

    def test_missing_supplement_grant_is_rejected_even_if_all_others_are_known(self):
        db = self.database(supplement=self.privileges - {"Delete Visits"})
        self.assertEqual(1, db.execute(self.query("scope")).fetchone()[0])
        self.assertEqual(0, db.execute(self.query("supplement-identity")).fetchone()[0])

    def test_unpaired_user_requires_review_without_implicitly_granting_a_role(self):
        db = self.database()
        db.execute("DELETE FROM user_role WHERE role = ?", (CANONICAL_ROLE,))
        self.assertEqual(1, db.execute(self.query("paired-users")).fetchone()[0])

    def test_foreign_uuid_owner_is_in_scope_but_not_an_approved_supplement(self):
        db = self.database()
        db.execute("UPDATE role SET uuid = 'unreviewed' WHERE role = ?", (self.NAME,))
        db.execute("UPDATE role SET uuid = ? WHERE role = 'Other'", (self.UUID,))
        self.assertEqual(2, db.execute(self.query("scope")).fetchone()[0])
        self.assertEqual(0, db.execute(self.query("supplement-identity")).fetchone()[0])

    def test_canonical_missing_required_grant_or_extra_privilege_cannot_authorize_retirement(self):
        for policy in (APPROVED_PRIVILEGES - {"Delete Relationships"},
                       (APPROVED_PRIVILEGES - {"Add Patients"}) | {"Synthetic Unexpected Access"}):
            db = self.database(canonical=policy)
            self.assertTrue(db.execute(self.query("canonical-target")).fetchone()[0] != 1
                            or db.execute(self.query("privileges")).fetchone()[0] != 0)

    def test_retirement_never_changes_canonical_grants_or_creates_accounts(self):
        sql = "".join(self.change.find(f"{{{NAMESPACE}}}sql").itertext())
        self.assertNotRegex(sql, r"(?im)^\s*(?:INSERT|UPDATE)\s+")
        self.assertNotRegex(sql, r"(?i)DELETE\s+FROM\s+users\b")
        self.assertIn("WHERE @retire_admission_supplement = 1", sql)
        self.assertEqual("true", self.change.get("runInTransaction"))
        self.assertEqual("HALT", self.change.find(f"{{{NAMESPACE}}}preConditions").get("onFail"))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    unittest.main()
