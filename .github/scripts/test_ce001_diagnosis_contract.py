#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("validate_ce001_diagnosis_contract.py")
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location(
    "validate_ce001_diagnosis_contract", SCRIPT_PATH
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class CE001DiagnosisContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.form = json.loads(VALIDATOR.CE001_PATH.read_text(encoding="utf-8"))

    def test_accepts_current_visit_notes_only_contract(self):
        self.assertEqual([], VALIDATOR.validate_contract(self.form))

    def test_rejects_reintroduced_diagnosis_as_observation(self):
        form = copy.deepcopy(self.form)
        form["pages"].append(
            {
                "label": "Evaluación adicional",
                "sections": [
                    {
                        "label": "Clasificación clínica",
                        "questions": [
                            {
                                "id": "otroCampo",
                                "label": "Diagnóstico clasificado CIE-10",
                                "type": "obs",
                                "questionOptions": {
                                    "concept": "162169AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                                    "rendering": "text",
                                },
                            }
                        ],
                    }
                ],
            }
        )

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(any("diagnosis-as-observation" in error for error in errors))

    def test_rejects_legacy_field_even_if_renamed(self):
        form = copy.deepcopy(self.form)
        form["pages"][0]["sections"][0]["questions"].append(
            {
                "id": "certezaDiagnostica",
                "label": "Clasificación",
                "type": "obs",
                "questionOptions": {
                    "concept": "2d53d39f-c93f-4128-8f7c-1bb45b498497",
                    "rendering": "select",
                },
            }
        )

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(any("legacy diagnosis field" in error for error in errors))

    def test_rejects_diagnosis_page_even_without_fields(self):
        form = copy.deepcopy(self.form)
        form["pages"].append({"label": "Diagnóstico", "sections": []})

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(
            any("must not expose a diagnosis page" in error for error in errors)
        )

    def test_rejects_renamed_form(self):
        form = copy.deepcopy(self.form)
        form["name"] = "CE-001-CONSULTA EXTERNA NUEVA"

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(
            any("identity from name plus version" in error for error in errors)
        )

    def test_rejects_new_form_version(self):
        form = copy.deepcopy(self.form)
        form["version"] = "1.0.5"

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(any("version must be 1.0.4" in error for error in errors))

    def test_rejects_historical_version_that_would_overwrite_clob(self):
        form = copy.deepcopy(self.form)
        form["version"] = VALIDATOR.PREVIOUS_VERSION

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(any("overwrite the historical schema CLOB" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
