"""Check CRED field compatibility against the terminology actually distributed."""
import json
import unittest
from pathlib import Path

from validate_form_concept_integrity import form_questions, load_concept_index


class CredBirthContextTest(unittest.TestCase):
    def test_birth_discharge_is_a_separate_optional_datetime(self):
        form = json.loads(Path('configuration/ampathforms/(CRED) Detalles de Nacimiento.json').read_text())
        fields = {question.get('id'): question for question in form_questions(form)}
        discharge = fields['fechaAltaRecienNacido']
        errors = []
        concepts = load_concept_index(errors)
        self.assertEqual([], errors)
        self.assertEqual('Datetime', concepts[discharge['questionOptions']['concept']]['datatype'])
        self.assertEqual('datetime', discharge['questionOptions']['rendering'])
        self.assertFalse(discharge.get('required', False))
        self.assertEqual('false', discharge['validators'][0]['allowFutureDates'])
        self.assertNotIn('calculate', discharge['questionOptions'])
        self.assertEqual('1.2', form['version'])
        self.assertEqual('a99e704f-46f6-4461-937d-606481fb0fc3', form['encounterType'])

    def test_anemia_retains_raw_hemoglobin_and_covers_the_amended_altitude_table(self):
        form = json.loads(Path('configuration/ampathforms/CRED-001-TAMIZAJE DE ANEMIA.json').read_text())
        fields = {question.get('id'): question for question in form_questions(form)}
        altitude = fields['altitud']
        self.assertEqual('5500', altitude['questionOptions']['max'])
        self.assertEqual('altitud >= 500', altitude['alert']['alertWhenExpression'])
        raw = [q for q in fields.values() if q.get('questionOptions', {}).get('concept') == '0ffe780c-a3ee-4c9c-b4dd-bf2e0f79dc7f']
        self.assertEqual(1, len(raw))
        self.assertNotIn('calculate', raw[0]['questionOptions'])


if __name__ == '__main__':
    unittest.main()
