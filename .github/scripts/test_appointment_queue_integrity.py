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

    def test_general_nursing_uses_its_local_category_and_shared_outpatient_route(self):
        category_uuid = "83cc14ae-0774-437e-8697-0d93b999ddf3"
        service_uuid = "4ec5c4fe-cfe0-48ff-9e4d-2f201078feae"
        local_categories = VALIDATOR.read_csv(
            self.catalog / "specialities_categorias_locales.csv"
        )
        category = next(row for row in local_categories if row["Uuid"] == category_uuid)
        self.assertEqual("Enfermería", category["Name"])
        self.assertFalse(VALIDATOR.is_retired(category["Void/Retire"]))
        professional_categories = VALIDATOR.read_csv(
            self.catalog / "specialities_enfermeria.csv"
        )
        self.assertNotIn(category_uuid, [row["Uuid"] for row in professional_categories])
        service = next(
            row for row in VALIDATOR.read_csv(VALIDATOR.SERVICE_DEFINITIONS_PATH)
            if row["Uuid"] == service_uuid
        )
        routes = VALIDATOR.read_csv(VALIDATOR.CARE_ROUTING_CONTRACT_PATH)
        route = next(row for row in routes if row["Appointment Service Uuid"] == service_uuid)
        medical_route = next(
            row for row in routes
            if row["Appointment Service Uuid"] == "7ba3aa21-cc56-47ca-bb4d-a60549f666c0"
        )
        self.assertEqual(category_uuid, service["Speciality"])
        self.assertEqual(category_uuid, route["Scheduling Category Uuid"])
        self.assertEqual("local-scheduling", route["Category Basis"])
        self.assertEqual("queue-optional", route["Arrival Policy"])
        self.assertEqual(medical_route["Queue Uuid"], route["Queue Uuid"])
        self.assertEqual(VALIDATOR.OUTPATIENT_LOCATION_UUID, route["Appointment Location Uuid"])
        self.assertEqual(VALIDATOR.GENERIC_AMBULATORY_VISIT_TYPE_UUID, route["Required Visit Type Uuid"])
        self.assertEqual([], self.validate())

    def test_rejects_missing_or_retired_general_nursing_category(self):
        path = self.catalog / "specialities_categorias_locales.csv"
        rows = VALIDATOR.read_csv(path)
        category_uuid = "83cc14ae-0774-437e-8697-0d93b999ddf3"
        for state in ("missing", "retired"):
            with self.subTest(state=state):
                changed = [
                    dict(row, **{"Void/Retire": "true"})
                    if row["Uuid"] == category_uuid else row
                    for row in rows
                    if state != "missing" or row["Uuid"] != category_uuid
                ]
                self.write_rows(path, changed)
                self.assertTrue(any(
                    f"category {category_uuid}" in error and "must be active" in error
                    for error in self.validate()
                ))

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

    def test_speciality_names_fit_the_native_column(self):
        for name, valid in (("á" * 50, True), ("á" * 51, False), (" ", False)):
            with self.subTest(name_length=len(name)):
                self.write_rows(self.catalog / "length.csv", [{
                    "Uuid": "00000000-0000-4000-8000-000000000001",
                    "Void/Retire": "", "Name": name,
                }])
                errors = self.validate()
                self.assertEqual(not errors, valid)
                if not valid:
                    self.assertTrue(any("1–50 characters" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
