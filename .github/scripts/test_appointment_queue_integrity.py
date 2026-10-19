#!/usr/bin/env python3
import csv
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.dont_write_bytecode = True
SCRIPT_PATH = Path(__file__).with_name("validate_appointment_queue_integrity.py")
SPEC = importlib.util.spec_from_file_location("appointment_integrity", SCRIPT_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class AppointmentSpecialityCatalogTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.catalog = Path(self.directory.name)
        for path in VALIDATOR.SPECIALITIES_DIR.glob("*.csv"):
            shutil.copyfile(path, self.catalog / path.name)

    def write_rows(self, path, rows):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["Uuid", "Void/Retire", "Name"])
            writer.writeheader()
            writer.writerows(rows)

    def validate(self):
        errors = []
        with mock.patch.object(VALIDATOR, "SPECIALITIES_DIR", self.catalog):
            VALIDATOR.validate_canonical_care_routing(errors)
        return errors

    def test_accepts_references_across_multiple_csv_files(self):
        # Repartition referenced categories without depending on file names.
        rows = [
            row
            for path in self.catalog.glob("*.csv")
            for row in VALIDATOR.read_csv(path)
        ]
        for path in self.catalog.glob("*.csv"):
            path.unlink()
        self.write_rows(self.catalog / "first.csv", rows[::2])
        self.write_rows(self.catalog / "second.csv", rows[1::2])
        (self.catalog / "notes.md").write_text("Not metadata", encoding="utf-8")
        self.assertEqual([], self.validate())

    def test_rejects_duplicate_uuid_across_files(self):
        row = VALIDATOR.read_csv(next(self.catalog.glob("*.csv")))[0]
        self.write_rows(self.catalog / "duplicate.csv", [dict(row, Name="Duplicada")])
        self.assertTrue(any("duplicate Uuid" in error for error in self.validate()))

    def test_rejects_duplicate_name_across_files(self):
        row = VALIDATOR.read_csv(next(self.catalog.glob("*.csv")))[0]
        self.write_rows(self.catalog / "duplicate.csv", [dict(
            row, Uuid="00000000-0000-4000-8000-000000000001"
        )])
        self.assertTrue(any("duplicate Name" in error for error in self.validate()))

    def test_rejects_missing_referenced_category(self):
        for path in self.catalog.glob("*.csv"):
            rows = VALIDATOR.read_csv(path)
            self.write_rows(path, [
                row for row in rows if row["Uuid"] != VALIDATOR.GENERAL_DENTISTRY_CATEGORY_UUID
            ])
        self.assertTrue(any("must be active" in error for error in self.validate()))

    def test_rejects_case_insensitive_name_collision_across_files(self):
        row = VALIDATOR.read_csv(next(self.catalog.glob("*.csv")))[0]
        self.write_rows(self.catalog / "case-collision.csv", [dict(
            row, Uuid="00000000-0000-4000-8000-000000000001", Name=row["Name"].swapcase()
        )])
        self.assertTrue(any("duplicate Name" in error for error in self.validate()))

    def test_rejects_empty_catalog(self):
        for path in self.catalog.glob("*.csv"):
            path.unlink()
        self.assertTrue(any("catalog is empty" in error for error in self.validate()))


if __name__ == "__main__":
    unittest.main()
