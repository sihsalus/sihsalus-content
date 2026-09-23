#!/usr/bin/env python3
"""Keep social history separate from legacy generic encounters and clinical defaults."""
import csv
import json
from pathlib import Path

from validate_ampath_forms import walk
from validate_ce001_diagnosis_contract import ampath_persisted_form_uuid

FORM_PATH = Path('configuration/ampathforms/CE-SOC-001-HISTORIA SOCIAL.json')
ENCOUNTER_PATH = Path('configuration/encountertypes/encountertypes.csv')
FORM_UUID = '76067e7a-48e5-3f69-92a4-70cf53e3e994'
ENCOUNTER_UUID = 'c7059f4b-385f-45e7-82ad-204e5b380196'
CONCEPTS = {
    'consumoAlcohol': 'fcd7736e-39d4-4ecd-84e0-9129e9690809',
    'consumoTabaco': 'a79047b1-aa5c-44ab-9410-02afb350c80a',
    'cigarrillosDia': '1546AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    'duracionTabaquismo': '159931AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
}
ANSWERS = {'372a262c-8d57-4b57-ad29-b24a2941b749', '5b2a0f81-22df-4ee1-ae2e-3c547cd7ec9f'}


def validate_contract(form, encounter_types):
    errors = []
    if ampath_persisted_form_uuid(form.get('name', ''), form.get('version', '')) != FORM_UUID:
        errors.append('Persisted form identity differs from the frontend contract')
    if form.get('encounterType') != ENCOUNTER_UUID:
        errors.append('Social history must use its dedicated encounter type')
    if form.get('published') is not True or form.get('retired') is not False:
        errors.append('The social history form must be available')
    matches = [row for row in encounter_types if row['Uuid'] == ENCOUNTER_UUID]
    if len(matches) != 1 or matches[0].get('View privilege') != 'app:hoja.clinica.historiaSocial' or matches[0].get('Edit privilege') != 'app:hoja.clinica.historiaSocial.editar':
        errors.append('Encounter privileges must preserve the social-history boundary')
    fields = [node for node in walk(form) if node.get('type') == 'obs']
    if {field.get('id') for field in fields} != set(CONCEPTS) or len(fields) != 4:
        errors.append('The initial scope is alcohol, tobacco, cigarettes/day and duration in years')
    for field in fields:
        options = field.get('questionOptions', {})
        field_id = field.get('id')
        if options.get('concept') != CONCEPTS.get(field_id):
            errors.append(f'{field_id}: incorrect clinical concept')
        if field.get('required') or any(key in node for node in walk(field) for key in ('default', 'defaultValue', 'calculateExpression', 'enablePreviousValue', 'hideWhenExpression')):
            errors.append(f'{field_id}: do not infer or prepopulate a clinical answer')
        if field_id in ('consumoAlcohol', 'consumoTabaco'):
            if options.get('rendering') != 'radio' or {answer.get('concept') for answer in options.get('answers', [])} != ANSWERS:
                errors.append(f'{field_id}: use only the existing mapped yes/no answers')
        else:
            if options.get('rendering') != 'number' or str(options.get('min')) != '0':
                errors.append(f'{field_id}: allow zero and disallow negative measurements')
    return errors


def main():
    form = json.loads(FORM_PATH.read_text())
    with ENCOUNTER_PATH.open(newline='') as stream:
        errors = validate_contract(form, list(csv.DictReader(stream)))
    if errors:
        for error in errors:
            print(error)
        return 1
    print('Validated social-history identity, scope, privileges and absence of inferred answers.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
