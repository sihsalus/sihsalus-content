#!/usr/bin/env python3
import copy
import csv
import json
import unittest

from validate_social_history_contract import FORM_PATH, ENCOUNTER_PATH, validate_contract


class SocialHistoryContractTest(unittest.TestCase):
    def setUp(self):
        self.form = json.loads(FORM_PATH.read_text())
        with ENCOUNTER_PATH.open(newline='') as stream:
            self.encounters = list(csv.DictReader(stream))
        self.fields = self.form['pages'][0]['sections'][1]['questions']

    def test_packaged_contract(self):
        self.assertEqual([], validate_contract(self.form, self.encounters))

    def test_no_inferred_clinical_answers(self):
        for key, value in [('default', 'No'), ('enablePreviousValue', True), ('hideWhenExpression', 'true')]:
            with self.subTest(key=key):
                form = copy.deepcopy(self.form)
                form['pages'][0]['sections'][1]['questions'][0]['questionOptions'][key] = value
                self.assertTrue(validate_contract(form, self.encounters))

    def test_legacy_type_cannot_be_repurposed(self):
        self.form['encounterType'] = '465a92f2-baf8-42e9-9612-53064be868e8'
        self.assertTrue(validate_contract(self.form, self.encounters))

    def test_uuid_changes_require_frontend_coordination(self):
        self.form['version'] = '1.0.1'
        self.assertTrue(validate_contract(self.form, self.encounters))

    def test_answers_must_remain_mapped(self):
        self.fields[0]['questionOptions']['answers'][0]['concept'] = 'unmapped'
        self.assertTrue(validate_contract(self.form, self.encounters))

    def test_negative_numeric_values_not_allowed(self):
        self.fields[2]['questionOptions']['min'] = '-1'
        self.assertTrue(validate_contract(self.form, self.encounters))

    def test_preserve_privileges(self):
        for row in self.encounters:
            if row['Name'] == 'Historia social':
                row['Edit privilege'] = ''
        self.assertTrue(validate_contract(self.form, self.encounters))


if __name__ == '__main__':
    unittest.main()
