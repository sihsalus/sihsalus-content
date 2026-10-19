#!/usr/bin/env python3
"""Exercise form identity checks with synthetic files through the validator entry point."""

import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import validate_ampath_forms as validator


class AmpathFormIdentityTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.forms = root / "ampathforms"
        self.forms.mkdir()
        ocl = root / "ocl"
        ocl.mkdir()
        with zipfile.ZipFile(ocl / "synthetic.zip", "w") as archive:
            archive.writestr("export.json", json.dumps({
                "source": {"id": "synthetic"},
                "concepts": [{"id": "1", "external_id": "synthetic-concept", "datatype": "Text"}],
            }))
        encounters = root / "encountertypes.csv"
        encounters.write_text("Uuid,Name,Void/Retire\nsynthetic-encounter,Synthetic encounter,false\n")
        for name, value in (("FORM_DIR", self.forms), ("OCL_DIR", ocl),
                            ("ENCOUNTER_TYPES_PATH", encounters)):
            patcher = patch.object(validator, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_form(self, filename, **overrides):
        form = {
            "name": "Synthetic form", "version": "1.0",
            "uuid": "10000000-0000-4000-8000-000000000001",
            "published": True, "retired": False,
            "encounter": "Synthetic encounter", "encounterType": "synthetic-encounter",
            "processor": "EncounterFormProcessor", "referencedForms": [], "pages": [],
        }
        form.update(overrides)
        (self.forms / filename).write_text(json.dumps(form))

    def run_validator(self):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = validator.main()
        return status, output.getvalue() + errors.getvalue()

    def write_native_concept(self, concept_uuid="native-dose", datatype="Numeric"):
        directory = self.forms.parent / "concepts"
        directory.mkdir(exist_ok=True)
        (directory / "measurement.csv").write_text(
            "Uuid,Void/Retire,Fully specified name:es,Data class,Data type,Units\n"
            f"{concept_uuid},,Dosis administrada,Question,{datatype},UI\n"
        )

    def test_resolves_native_numeric_concept_and_keeps_unit(self):
        self.write_native_concept()
        self.write_form("dose.json", pages=[{"sections": [{"questions": [{
            "id": "dose", "type": "obs", "questionOptions": {"concept": "native-dose", "rendering": "number"},
        }]}]}])
        status, output = self.run_validator()
        self.assertEqual(0, status, output)
        bundle, errors = validator.load_ocl_bundle()
        self.assertEqual([], errors)
        self.assertEqual("UI", bundle["active_by_external_id"]["native-dose"][0]["units"])

    def test_rejects_duplicate_operational_definition_in_native_csv_and_ocl(self):
        self.write_native_concept("synthetic-concept", "Text")
        self.write_form("duplicate.json", pages=[{"sections": [{"questions": [{
            "id": "duplicate", "type": "obs", "questionOptions": {"concept": "synthetic-concept", "rendering": "text"},
        }]}]}])
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn("ambiguous", output)

    def test_patient_context_is_native_but_unknown_local_fields_still_fail(self):
        self.assertEqual(
            {'missingDate'},
            validator.expression_references('patient.birthDate && dayjs(missingDate).isBefore(patient.birthDate)'),
        )

    def test_disabled_expression_rejects_missing_local_question(self):
        self.write_form('disabled.json', pages=[{'sections': [{'questions': [{
            'id': 'duration', 'type': 'obs',
            'questionOptions': {'rendering': 'text', 'concept': 'synthetic-concept'},
            'disabled': {'disableWhenExpression': "missingResponse !== 'yes'"},
        }]}]}])
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn('missingResponse', output)

    def test_accepts_literal_options_for_text_observations(self):
        self.write_form("select.json", pages=[{"sections": [{"questions": [{
            "id": "onset", "type": "obs", "questionOptions": {
                "concept": "synthetic-concept", "rendering": "select",
                "answers": [{"value": "Gradual", "label": "Inicio gradual"}],
            },
        }]}]}])
        status, output = self.run_validator()
        self.assertEqual(0, status, output)

    def test_accepts_native_markdown_control_without_an_observation_concept(self):
        self.write_form("hint.json", pages=[{"sections": [{"questions": [{
            "id": "hint", "type": "control", "questionOptions": {"rendering": "markdown"},
            "value": "Synthetic guidance without clinical capture.",
        }]}]}])
        status, output = self.run_validator()
        self.assertEqual(0, status, output)

    def test_markdown_support_preserves_missing_concept_and_unknown_renderer_checks(self):
        for field_type, rendering, expected in (
            ("obs", "markdown", "missing questionOptions.concept"),
            ("control", "invented-renderer", "unsupported rendering"),
        ):
            with self.subTest(field_type=field_type, rendering=rendering):
                self.write_form("hint.json", pages=[{"sections": [{"questions": [{
                    "id": "hint", "type": field_type,
                    "questionOptions": {"rendering": rendering}, "value": "Synthetic hint.",
                }]}]}])
                status, output = self.run_validator()
                self.assertEqual(1, status, output)
                self.assertIn(expected, output)

    def test_rejects_ambiguous_or_invalid_literal_options(self):
        for answers in (
            [{"value": "Gradual", "concept": "synthetic-concept", "label": "Inicio gradual"}],
            [{"value": "", "label": "Vacío"}],
            [{"value": {"unexpected": True}, "label": "Objeto"}],
            [{"value": "Gradual"}],
            [{"value": "Gradual", "label": "Uno"}, {"value": "Gradual", "label": "Dos"}],
        ):
            with self.subTest(answers=answers):
                self.write_form("select.json", pages=[{"sections": [{"questions": [{
                    "id": "onset", "type": "obs", "questionOptions": {
                        "concept": "synthetic-concept", "rendering": "select", "answers": answers,
                    },
                }]}]}])
                status, output = self.run_validator()
                self.assertEqual(1, status, output)
                self.assertIn("literal", output)

    def test_accepts_distinct_versions_without_normalizing_them(self):
        self.write_form("first.json")
        self.write_form("second.json", version="1.0.0", uuid="10000000-0000-4000-8000-000000000002")
        status, output = self.run_validator()
        self.assertEqual(0, status, output)
        self.assertIn("Validated 2 AMPATH", output)

    def test_rejects_same_persisted_identity_with_different_json_uuids(self):
        self.write_form("first.json")
        self.write_form("second.json", uuid="10000000-0000-4000-8000-000000000002")
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn("duplicate persisted form UUID", output)
        self.assertIn("first.json", output)
        self.assertIn("second.json", output)

    def test_rejects_collisions_from_initializers_underscore_separator(self):
        self.write_form("first.json", name="Synthetic_form", version="1")
        self.write_form("second.json", name="Synthetic", version="form_1",
                        uuid="10000000-0000-4000-8000-000000000002")
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn("duplicate persisted form UUID", output)

    def test_still_rejects_duplicate_json_uuids(self):
        self.write_form("first.json")
        self.write_form("second.json", version="2.0")
        status, output = self.run_validator()
        self.assertEqual(1, status, output)
        self.assertIn("duplicate top-level form uuid", output)

    def test_rejects_empty_or_missing_form_directory(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                if missing:
                    self.forms.rmdir()
                status, output = self.run_validator()
                self.assertEqual(1, status, output)
                self.assertIn("no AMPATH form JSON files found", output)

    def test_rejects_blank_or_non_string_identity_fields(self):
        for field in ("name", "version"):
            for value in (None, "", "  ", 1, True, ["value"]):
                with self.subTest(field=field, value=value):
                    self.write_form("first.json", **{field: value})
                    status, output = self.run_validator()
                    self.assertEqual(1, status, output)
                    self.assertIn(f"{field} must be a non-empty string", output)


class ShippedClinicalMetadataContractTest(unittest.TestCase):
    def test_vitamin_a_writes_a_numeric_dose_in_ui_without_reusing_score(self):
        root = Path(__file__).resolve().parents[2]
        path = root / "configuration/ampathforms/CRED-013-ADMINISTRACIÓN DE VITAMINA A.json"
        form = json.loads(path.read_text())
        questions = [question for page in form["pages"] for section in page["sections"]
                     for question in section["questions"]]
        dose = next(question for question in questions if question.get("id") == "dosisUi")
        bundle, errors = validator.load_ocl_bundle()
        concept = validator.resolve_concept(path, dose, dose["questionOptions"]["concept"], "question", bundle, errors)
        self.assertEqual([], errors)
        self.assertEqual(("Numeric", "UI"), (concept["datatype"], concept["units"]))
        self.assertNotEqual("f0000007-0000-4000-8000-000000000007", concept["external_id"])
        self.assertNotEqual(validator.ampath_persisted_form_uuid(form["name"], "1.0.0"),
                            validator.ampath_persisted_form_uuid(form["name"], form["version"]))

    def test_immunization_separates_record_and_administration_dates(self):
        root = Path(__file__).resolve().parents[2]
        path = root / "configuration/ampathforms/INMU-001-REGISTRO DE VACUNACIÓN.json"
        form = json.loads(path.read_text())
        questions = [question for page in form["pages"] for section in page["sections"]
                     for question in section["questions"]]
        record = next(question for question in questions if question.get("id") == "fechaVacunacion")
        administration = next(question for question in questions if question.get("id") == "fechaAdministracion")
        self.assertEqual("encounterDatetime", record["type"])
        self.assertEqual("obs", administration["type"])
        bundle, errors = validator.load_ocl_bundle()
        concept = validator.resolve_concept(path, administration, administration["questionOptions"]["concept"], "question", bundle, errors)
        self.assertEqual([], errors)
        self.assertEqual("Datetime", concept["datatype"])
        self.assertEqual("1.1.0", form["version"])
        self.assertNotEqual(validator.ampath_persisted_form_uuid(form["name"], "1.0.1"),
                            validator.ampath_persisted_form_uuid(form["name"], form["version"]))

    def test_cred_referral_writes_canonical_priority_answers(self):
        root = Path(__file__).resolve().parents[2]
        path = root / "configuration/ampathforms/CRED-024-INTERCONSULTA DERIVACIÓN REFERENCIA.json"
        form = json.loads(path.read_text())
        questions = [question for page in form["pages"] for section in page["sections"]
                     for question in section["questions"]]
        priority = next(question for question in questions if question.get("id") == "prioridad")
        bundle, errors = validator.load_ocl_bundle()
        self.assertEqual([], errors)
        options = priority["questionOptions"]
        concept = validator.resolve_concept(path, priority, options["concept"], "question", bundle, errors)
        self.assertEqual("Prioridad de referencia", concept["display_name"])
        self.assertEqual("Coded", concept["datatype"])
        allowed = bundle["q_and_a_targets"][(concept["source"], concept["code"])]
        self.assertEqual(4, len(options["answers"]))
        for answer in options["answers"]:
            resolved = validator.resolve_concept(path, priority, answer["concept"], "answer", bundle, errors)
            self.assertIn((resolved["source"], resolved["code"]), allowed)
            self.assertNotIn("ESAVI", resolved["display_name"])
        self.assertEqual([], errors)

    def test_corrected_capture_has_distinct_persisted_form_identity(self):
        root = Path(__file__).resolve().parents[2]
        form = json.loads((root / "configuration/ampathforms/CRED-024-INTERCONSULTA DERIVACIÓN REFERENCIA.json").read_text())
        self.assertEqual("1.1.0", form["version"])
        self.assertNotEqual(
            validator.ampath_persisted_form_uuid(form["name"], "1.0.0"),
            validator.ampath_persisted_form_uuid(form["name"], form["version"]),
        )
        self.assertEqual("c2240000-0000-4000-8000-000000000024", form["uuid"])


if __name__ == "__main__":
    unittest.main()
