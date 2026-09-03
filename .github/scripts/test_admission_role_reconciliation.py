#!/usr/bin/env python3

import sqlite3
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


LIQUIBASE_PATH = Path("configuration/backend_configuration/liquibase/liquibase.xml")
NAMESPACE = "http://www.liquibase.org/xml/ns/dbchangelog/1.9"
CANONICAL_ROLE = "Admision"
LEGACY_ROLE = "SIHSALUS Admision"
CANONICAL_UUID = "71dcb611-756a-4ad3-a9bb-73b6cfe28066"
OWNER_ASSERTION_ID = "assert-admission-role-uuid-owner-20260903"
CORE_MERGE_ID = "merge-admission-role-core-references-20260903"
PATIENT_FLAGS_MERGE_ID = "merge-admission-role-patientflags-references-20260903"
STOCK_MERGE_ID = "merge-admission-role-stock-references-20260903"
FINALIZE_ID = "finalize-admission-role-identity-20260903"
FINAL_ASSERTION_ID = "assert-canonical-admission-role-identity-20260903"


def get_change_set(change_set_id: str) -> ET.Element:
    root = ET.parse(LIQUIBASE_PATH).getroot()
    for change_set in root.findall(f"{{{NAMESPACE}}}changeSet"):
        if change_set.get("id") == change_set_id:
            return change_set
    raise AssertionError(f"Missing Liquibase changeSet: {change_set_id}")


def get_sql(change_set_id: str) -> str:
    sql_element = get_change_set(change_set_id).find(f"{{{NAMESPACE}}}sql")
    if sql_element is None:
        raise AssertionError(f"Missing SQL for Liquibase changeSet: {change_set_id}")
    sql = "".join(sql_element.itertext())
    return sql.replace("INSERT IGNORE INTO", "INSERT OR IGNORE INTO").replace(
        "UUID()", "'generated-admission-role-uuid'"
    )


def get_assertion_query(change_set_id: str) -> str:
    sql_check = get_change_set(change_set_id).find(
        f".//{{{NAMESPACE}}}sqlCheck"
    )
    if sql_check is None:
        raise AssertionError(
            f"Missing assertion query for Liquibase changeSet: {change_set_id}"
        )
    return "".join(sql_check.itertext()).strip()


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return (
        connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()[0]
        == 1
    )


def role_exists(connection: sqlite3.Connection, role_name: str) -> bool:
    return (
        connection.execute(
            "SELECT COUNT(*) FROM role WHERE role = ?", (role_name,)
        ).fetchone()[0]
        == 1
    )


def apply_reconciliation(connection: sqlite3.Connection) -> None:
    if connection.execute(get_assertion_query(OWNER_ASSERTION_ID)).fetchone()[0] != 0:
        raise RuntimeError("The canonical admission UUID belongs to an unrelated role")

    if role_exists(connection, LEGACY_ROLE):
        connection.executescript(get_sql(CORE_MERGE_ID))
        if table_exists(connection, "patientflags_tag_role"):
            connection.executescript(get_sql(PATIENT_FLAGS_MERGE_ID))
        if table_exists(connection, "stockmgmt_user_role_scope"):
            connection.executescript(get_sql(STOCK_MERGE_ID))

    connection.executescript(get_sql(FINALIZE_ID))

    if connection.execute(get_assertion_query(FINAL_ASSERTION_ID)).fetchone()[0] != 0:
        raise RuntimeError("The admission role was not normalized")


def create_database(include_optional_tables: bool = True) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE role (
            role TEXT PRIMARY KEY,
            description TEXT,
            uuid TEXT NOT NULL UNIQUE
        );
        CREATE TABLE user_role (
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL REFERENCES role(role),
            PRIMARY KEY (user_id, role)
        );
        CREATE TABLE role_privilege (
            role TEXT NOT NULL REFERENCES role(role),
            privilege TEXT NOT NULL,
            PRIMARY KEY (role, privilege)
        );
        CREATE TABLE role_role (
            parent_role TEXT NOT NULL REFERENCES role(role),
            child_role TEXT NOT NULL REFERENCES role(role),
            PRIMARY KEY (parent_role, child_role)
        );
        """
    )
    if include_optional_tables:
        connection.executescript(
            """
            CREATE TABLE patientflags_tag_role (
                tag_id INTEGER NOT NULL,
                role TEXT NOT NULL REFERENCES role(role)
            );
            CREATE TABLE stockmgmt_user_role_scope (
                user_role_scope_id INTEGER PRIMARY KEY,
                role TEXT NOT NULL REFERENCES role(role),
                uuid TEXT NOT NULL UNIQUE
            );
            """
        )
    return connection


class AdmissionRoleReconciliationTest(unittest.TestCase):
    def test_merges_duplicate_roles_without_losing_or_duplicating_references(self):
        connection = create_database()
        connection.executemany(
            "INSERT INTO role(role, description, uuid) VALUES (?, ?, ?)",
            [
                (CANONICAL_ROLE, "canonical", "temporary-canonical-uuid"),
                (LEGACY_ROLE, "legacy", CANONICAL_UUID),
                ("Other", "other", "other-role-uuid"),
            ],
        )
        connection.executemany(
            "INSERT INTO user_role(user_id, role) VALUES (?, ?)",
            [(1, CANONICAL_ROLE), (1, LEGACY_ROLE), (2, LEGACY_ROLE)],
        )
        connection.executemany(
            "INSERT INTO role_privilege(role, privilege) VALUES (?, ?)",
            [
                (CANONICAL_ROLE, "Shared"),
                (LEGACY_ROLE, "Shared"),
                (LEGACY_ROLE, "Legacy only"),
            ],
        )
        connection.executemany(
            "INSERT INTO role_role(parent_role, child_role) VALUES (?, ?)",
            [
                (CANONICAL_ROLE, "Other"),
                (LEGACY_ROLE, "Other"),
                ("Other", CANONICAL_ROLE),
                ("Other", LEGACY_ROLE),
                (LEGACY_ROLE, CANONICAL_ROLE),
                (CANONICAL_ROLE, LEGACY_ROLE),
            ],
        )
        connection.executemany(
            "INSERT INTO patientflags_tag_role(tag_id, role) VALUES (?, ?)",
            [(10, CANONICAL_ROLE), (10, LEGACY_ROLE), (20, LEGACY_ROLE)],
        )
        connection.executemany(
            "INSERT INTO stockmgmt_user_role_scope(user_role_scope_id, role, uuid) VALUES (?, ?, ?)",
            [(1, CANONICAL_ROLE, "scope-1"), (2, LEGACY_ROLE, "scope-2")],
        )

        apply_reconciliation(connection)

        self.assertEqual(
            [(CANONICAL_ROLE, CANONICAL_UUID)],
            connection.execute(
                "SELECT role, uuid FROM role WHERE role IN (?, ?)",
                (CANONICAL_ROLE, LEGACY_ROLE),
            ).fetchall(),
        )
        self.assertEqual(
            [(1, CANONICAL_ROLE), (2, CANONICAL_ROLE)],
            connection.execute(
                "SELECT user_id, role FROM user_role ORDER BY user_id, role"
            ).fetchall(),
        )
        self.assertEqual(
            [(CANONICAL_ROLE, "Legacy only"), (CANONICAL_ROLE, "Shared")],
            connection.execute(
                "SELECT role, privilege FROM role_privilege ORDER BY role, privilege"
            ).fetchall(),
        )
        self.assertEqual(
            [(CANONICAL_ROLE, "Other"), ("Other", CANONICAL_ROLE)],
            connection.execute(
                "SELECT parent_role, child_role FROM role_role ORDER BY parent_role, child_role"
            ).fetchall(),
        )
        self.assertEqual(
            [(10, CANONICAL_ROLE), (20, CANONICAL_ROLE)],
            connection.execute(
                "SELECT tag_id, role FROM patientflags_tag_role ORDER BY tag_id, role"
            ).fetchall(),
        )
        self.assertEqual(
            [(1, CANONICAL_ROLE), (2, CANONICAL_ROLE)],
            connection.execute(
                "SELECT user_role_scope_id, role FROM stockmgmt_user_role_scope ORDER BY user_role_scope_id"
            ).fetchall(),
        )

    def test_migrates_a_legacy_only_role_without_optional_module_tables(self):
        connection = create_database(include_optional_tables=False)
        connection.executemany(
            "INSERT INTO role(role, description, uuid) VALUES (?, ?, ?)",
            [(LEGACY_ROLE, "legacy", CANONICAL_UUID), ("Other", "other", "other-role-uuid")],
        )
        connection.execute(
            "INSERT INTO user_role(user_id, role) VALUES (?, ?)", (7, LEGACY_ROLE)
        )

        apply_reconciliation(connection)

        self.assertEqual(
            [(CANONICAL_ROLE, CANONICAL_UUID)],
            connection.execute(
                "SELECT role, uuid FROM role WHERE role = ?", (CANONICAL_ROLE,)
            ).fetchall(),
        )
        self.assertEqual(
            [(7, CANONICAL_ROLE)],
            connection.execute("SELECT user_id, role FROM user_role").fetchall(),
        )

    def test_normalizes_a_canonical_role_with_a_stale_uuid(self):
        connection = create_database()
        connection.execute(
            "INSERT INTO role(role, description, uuid) VALUES (?, ?, ?)",
            (CANONICAL_ROLE, "canonical", "temporary-canonical-uuid"),
        )

        apply_reconciliation(connection)

        self.assertEqual(
            CANONICAL_UUID,
            connection.execute(
                "SELECT uuid FROM role WHERE role = ?", (CANONICAL_ROLE,)
            ).fetchone()[0],
        )

    def test_refuses_to_steal_the_canonical_uuid_from_an_unrelated_role(self):
        connection = create_database()
        connection.executemany(
            "INSERT INTO role(role, description, uuid) VALUES (?, ?, ?)",
            [
                (CANONICAL_ROLE, "canonical", "temporary-canonical-uuid"),
                ("Unrelated", "unrelated", CANONICAL_UUID),
            ],
        )

        with self.assertRaisesRegex(RuntimeError, "unrelated role"):
            apply_reconciliation(connection)

        self.assertEqual(
            "temporary-canonical-uuid",
            connection.execute(
                "SELECT uuid FROM role WHERE role = ?", (CANONICAL_ROLE,)
            ).fetchone()[0],
        )


if __name__ == "__main__":
    unittest.main()
