#!/usr/bin/env python3
"""Static changelog contracts: changeSet order, byte-for-byte freezes and the
historical policy fixture. Migration execution runs in the MariaDB harness."""

import csv
import hashlib
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LIQUIBASE_PATH = (
    REPOSITORY_ROOT / "configuration/liquibase/liquibase.xml"
)
ROLES_PATH = (
    REPOSITORY_ROOT / "configuration/roles/roles-core.csv"
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
            # Verified against the public Maven Central 1.25.24 ZIP on 2026-09-22.
            OPERATIONAL_RECONCILIATION_ID:
                "66684444789d2e0676ebd0ed79915a67487821d11860aa8bb4bc348557e78ef6",
            SUPPLEMENT_RETIREMENT_ID:
                "28ad32c1c5c5b745230347aeba266ea99029f7179b8cc535c1921c6d3839ea39",
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
        literals = set(re.findall(r"'([^']*)'", get_policy_query("privileges")))
        self.assertEqual(
            APPROVED_PRIVILEGES, literals - {CANONICAL_ROLE, LEGACY_ROLE}
        )
        self.assertEqual(58, len(APPROVED_PRIVILEGES))
        self.assertEqual(57, len(PREVIOUS_PRIVILEGES))
        self.assertEqual(59, len(CURRENT_PRIVILEGES))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    unittest.main()
