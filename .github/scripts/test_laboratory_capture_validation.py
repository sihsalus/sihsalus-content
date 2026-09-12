#!/usr/bin/env python3
import copy
import importlib.util
import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location(
    "validate_ocl_exports", Path(__file__).with_name("validate_ocl_exports.py")
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class LaboratoryCaptureValidationTest(unittest.TestCase):
    def setUp(self):
        self.records = [
            (Path("laboratory.zip"), "laboratorio", {
                "id": code, "external_id": uuid, "datatype": datatype, "retired": False,
                "extras": {"Units": "mg/24h"} if code == "5400" else {},
            })
            for code, uuid, datatype in (
                ("5282", "6576cf12-ca50-4234-be46-ac74a4e7814d", "Coded"),
                ("5286", "a0d91c80-4e2f-4f12-8007-3a5c40931bf8", "Coded"),
                ("2470", "267b3f53-10ff-498f-a37e-f33b945bd1ce", "Numeric"),
                ("5400", "bc79bdb5-5bbe-4864-a2ed-81c7ad77ff88", "Numeric"),
            )
        ]

    def errors(self, records):
        errors = []
        VALIDATOR.validate_laboratory_capture(records, errors)
        return errors

    def test_accepts_historical_capture_without_freezing_names_ranges_or_other_concepts(self):
        for _, _, concept in self.records:
            concept["display_name"] = "Nombre actualizado"
            concept["extras"]["hi_normal"] = 123
        self.records.append((Path("new.zip"), "laboratorio", {
            "id": "new", "external_id": "new-uuid", "datatype": "Text", "retired": False,
        }))
        self.assertEqual(self.errors(self.records), [])

    def test_rejects_each_september_release_datatype_change(self):
        for index, datatype in ((0, "Text"), (1, "Text"), (2, "Coded")):
            with self.subTest(index=index):
                records = copy.deepcopy(self.records)
                records[index][2]["datatype"] = datatype
                self.assertEqual(len(self.errors(records)), 1)
                self.assertIn("datatype", self.errors(records)[0])

    def test_rejects_missing_retired_duplicate_or_reidentified_concepts(self):
        for index in range(len(self.records)):
            for change in ("missing", "retired", "duplicate", "uuid", "code", "source"):
                with self.subTest(index=index, change=change):
                    records = copy.deepcopy(self.records)
                    concept = records[index][2]
                    if change == "missing":
                        records.pop(index)
                    elif change == "retired":
                        concept["retired"] = True
                    elif change == "duplicate":
                        records.append(copy.deepcopy(records[index]))
                    elif change == "uuid":
                        concept["external_id"] = "replacement-uuid"
                    elif change == "code":
                        concept["id"] = "replacement-code"
                    else:
                        records[index] = (Path("other.zip"), "other-source", concept)
                    self.assertTrue(self.errors(records))

    def test_rejects_uuid_reused_by_another_source(self):
        self.records.append((Path("other.zip"), "other-source", {
            **self.records[0][2], "id": "another-code",
        }))
        self.assertIn("found 2", self.errors(self.records)[0])

    def test_accepts_lowercase_legacy_or_matching_unit_keys(self):
        for extras in ({"units": "mg/24h"}, {"Units": "mg/24h"},
                       {"units": "mg/24h", "Units": "mg/24h"}):
            with self.subTest(extras=extras):
                self.records[3][2]["extras"] = extras
                self.assertEqual(self.errors(self.records), [])

    def test_rejects_missing_changed_or_conflicting_declared_units(self):
        for extras in ({}, None, [], "mg/24h", {"units": None}, {"Units": ""},
                       {"units": "mg/kg/24h"}, {"Units": "mg/kg/24h"},
                       {"units": "mg/24h", "Units": "mg/kg/24h"},
                       {"units": "mg/kg/24h", "Units": "mg/24h"}):
            with self.subTest(extras=extras):
                self.records[3][2]["extras"] = extras
                self.assertEqual(len(self.errors(self.records)), 1)
                self.assertIn("declare mg/24h consistently", self.errors(self.records)[0])


if __name__ == "__main__":
    unittest.main()
