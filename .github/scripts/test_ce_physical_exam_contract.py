#!/usr/bin/env python3
import copy
import json
import unittest

import validate_ce_physical_exam_contract as contract
from validate_ampath_forms import ampath_persisted_form_uuid


class PhysicalExamContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.form = json.loads(contract.FORM_PATH.read_text())
        cls.legacy = json.loads(contract.LEGACY_FORM_PATH.read_text())

    def test_accepts_dedicated_examination_and_retired_history(self):
        self.assertEqual([], contract.validate_contract(self.form))
        self.assertEqual([], contract.validate_legacy_contract(self.legacy))
        self.assertNotEqual(
            ampath_persisted_form_uuid(self.form['name'], self.form['version']),
            ampath_persisted_form_uuid(self.legacy['name'], self.legacy['version']),
        )

    def test_all_active_outpatient_forms_exclude_soap(self):
        for path in contract.FORM_PATH.parent.glob("CE-*.json"):
            with self.subTest(form=path.name):
                form = json.loads(path.read_text())
                self.assertEqual([], contract.validate_no_soap_capture(form))

    def test_preserves_existing_segmented_fields_and_encounter_type(self):
        def questions(form):
            return {node.get('id'): node for node in contract.walk(form) if node.get('type') == 'obs'}

        current, historical = questions(self.form), questions(self.legacy)
        self.assertEqual(self.form['encounterType'], self.legacy['encounterType'])
        self.assertEqual(set(current), set(contract.SEGMENTED_FIELD_CONCEPTS))
        for field in current:
            self.assertEqual(current[field], historical[field])

    def test_rejects_soap_questions_even_when_renamed(self):
        for field, concept in contract.LEGACY_SOAP_FIELDS.items():
            with self.subTest(field=field):
                form = copy.deepcopy(self.form)
                form['pages'][0]['sections'][0]['questions'].append({
                    'type': 'obs', 'id': 'renamedField',
                    'questionOptions': {'rendering': 'textarea', 'concept': concept},
                })
                self.assertTrue(any('SOAP capture' in error for error in contract.validate_contract(form)))

    def test_rejects_invented_normal_findings_and_missing_general_state(self):
        form = copy.deepcopy(self.form)
        question = next(node for node in contract.walk(form) if node.get('id') == 'estadoGeneral')
        question['questionOptions']['default'] = 'Normal'
        question['required'] = False
        errors = contract.validate_contract(form)
        self.assertTrue(any('auto-populate' in error for error in errors))
        self.assertTrue(any('required' in error for error in errors))

    def test_rejects_removal_of_historical_fields(self):
        legacy = copy.deepcopy(self.legacy)
        question = next(node for node in contract.walk(legacy) if node.get('id') == 'neurologico')
        question['questionOptions']['concept'] = 'different-concept'
        self.assertTrue(contract.validate_legacy_contract(legacy))

    def test_rejects_reactivation_of_outpatient_soap(self):
        legacy = copy.deepcopy(self.legacy)
        legacy.update(published=True, retired=False)
        self.assertTrue(any('retired' in error for error in contract.validate_legacy_contract(legacy)))


if __name__ == '__main__':
    unittest.main()
