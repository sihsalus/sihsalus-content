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
        cls.liquibase = VALIDATOR.LIQUIBASE_PATH.read_text(encoding="utf-8")

    def test_accepts_current_visit_notes_only_contract(self):
        self.assertEqual([], VALIDATOR.validate_contract(self.form))

    def test_accepts_legacy_form_retirement_contract(self):
        self.assertEqual([], VALIDATOR.validate_liquibase_contract(self.liquibase))

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
        form["version"] = "1.0.4"

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(any("version must be 1.0.3" in error for error in errors))

    def test_rejects_historical_version_that_would_overwrite_clob(self):
        form = copy.deepcopy(self.form)
        form["version"] = VALIDATOR.PREVIOUS_VERSION

        errors = VALIDATOR.validate_contract(form)

        self.assertTrue(any("overwrite the historical schema CLOB" in error for error in errors))

    def test_corrected_version_has_a_distinct_deterministic_identity(self):
        previous_uuid = VALIDATOR.ampath_persisted_form_uuid(
            VALIDATOR.EXPECTED_NAME, VALIDATOR.PREVIOUS_VERSION
        )
        active_uuid = VALIDATOR.ampath_persisted_form_uuid(
            VALIDATOR.EXPECTED_NAME, VALIDATOR.EXPECTED_VERSION
        )

        self.assertEqual(VALIDATOR.PREVIOUS_PERSISTED_FORM_UUID, previous_uuid)
        self.assertEqual(VALIDATOR.EXPECTED_PERSISTED_FORM_UUID, active_uuid)
        self.assertNotEqual(previous_uuid, active_uuid)

    def test_rejects_retirement_without_exact_legacy_uuid_scope(self):
        broken = self.liquibase.replace(
            f"WHERE uuid = '{VALIDATOR.PREVIOUS_PERSISTED_FORM_UUID}'\n"
            "              AND name = 'CE-001-CONSULTA EXTERNA'",
            "WHERE name = 'CE-001-CONSULTA EXTERNA'",
            1,
        )

        errors = VALIDATOR.validate_liquibase_contract(broken)

        self.assertTrue(any("missing SQL contract fragment" in error for error in errors))

    def test_rejects_republishing_legacy_form(self):
        broken = self.liquibase.replace("published = 0,", "published = 1,", 1)

        errors = VALIDATOR.validate_liquibase_contract(broken)

        self.assertTrue(any("'PUBLISHED = 0'" in error for error in errors))

    def test_rejects_nonexistent_retire_reason_column(self):
        broken = self.liquibase.replace("retired_reason", "retire_reason")

        errors = VALIDATOR.validate_liquibase_contract(broken)

        self.assertTrue(any("form.retire_reason" in error for error in errors))

    def test_rejects_non_fail_closed_retirement(self):
        marker = (
            f'id="{VALIDATOR.RETIRE_CHANGE_SET_ID}"\n'
            '        author="sihsalus">\n'
            '        <preConditions onFail="HALT" onError="HALT">'
        )
        broken = self.liquibase.replace(
            marker,
            marker.replace('onFail="HALT"', 'onFail="CONTINUE"'),
            1,
        )

        errors = VALIDATOR.validate_liquibase_contract(broken)

        self.assertTrue(any("must HALT" in error for error in errors))

    def test_rejects_missing_exclusive_canonical_assertion(self):
        broken = self.liquibase.replace(
            VALIDATOR.ASSERT_CHANGE_SET_ID,
            f"{VALIDATOR.ASSERT_CHANGE_SET_ID}-removed",
            1,
        )

        errors = VALIDATOR.validate_liquibase_contract(broken)

        self.assertTrue(any("missing changeSet" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
