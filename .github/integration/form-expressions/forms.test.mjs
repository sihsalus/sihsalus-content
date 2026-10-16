import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';
import vm from 'node:vm';
import dayjs from 'dayjs';

// Neonatal regressions must use the form engine's evaluator: its logical
// operators are eager, unlike node:vm. Never substitute JavaScript on failure.
assert.ok(process.env.SIHSALUS_EXPRESSION_EVALUATOR,
  'Set SIHSALUS_EXPRESSION_EVALUATOR to the pinned frontend esm-expression-evaluator/dist/index.js; see README.md');
const { evaluateAsBoolean, extractVariableNames } = await import(
  pathToFileURL(process.env.SIHSALUS_EXPRESSION_EVALUATOR).href
);
const evaluateNative = (expression, values) => evaluateAsBoolean(expression, { dayjs, ...values });

// These tests read shipped expressions, not copies of their clinical rules.
// Existing non-neonatal cases retain JavaScript evaluation; neither suite proves
// browser rendering or encounter persistence.
function fields(filename) {
  const form = JSON.parse(readFileSync(new URL(`../../../configuration/ampathforms/${filename}`, import.meta.url)));
  const walk = ({ questions = [] }) => questions.flatMap((question) => [question, ...walk(question)]);
  return Object.fromEntries(form.pages.flatMap((page) => page.sections.flatMap(walk)).map((q) => [q.id, q]));
}

const anemia = fields('CRED-001-TAMIZAJE DE ANEMIA.json');
const obstetrics = fields('OBST-002-EMBARAZO ACTUAL.json');
const history = fields('OBST-001-ANTECEDENTES.json');
const mentalHealth = fields('CRED-011-SALUD MENTAL NIÑO Y CUIDADOR.json');
const birth = fields('(CRED) Detalles de Nacimiento.json');
const evaluate = (expression, values) => vm.runInNewContext(expression, { dayjs, ...values });
const date = (value) => dayjs(value).toDate();

test('native evaluator: neonatal discharge rejects days before birth and allows the birth day', () => {
  const validator = birth.fechaAltaRecienNacido.validators.find((v) => v.type === 'js_expression');
  const isEmpty = (value) => value == null || value === '';
  for (const [value, expected] of [
    ['2026-10-14T23:59:00', true], ['2026-10-15T00:00:00', false], ['2026-10-16T10:30:00', false],
  ]) {
    assert.equal(evaluateNative(validator.failsWhenExpression, {
      myValue: date(value), patient: { birthDate: '2026-10-15' }, isEmpty,
    }), expected);
  }
  for (const patient of [undefined, null, {}, { birthDate: null }, { birthDate: '' }, { birthDate: 'invalid' }]) {
    assert.equal(evaluateNative(validator.failsWhenExpression, { myValue: date('2026-10-15'), patient, isEmpty }), true);
    for (const myValue of [undefined, null, '']) {
      assert.equal(evaluateNative(validator.failsWhenExpression, { myValue, patient, isEmpty }), false);
    }
  }
  assert.ok(birth.fechaAltaRecienNacido.validators.some((v) => v.type === 'date' && v.allowFutureDates === 'false'));
});

test('native evaluator: hospitalization duration disables unless Yes and rejects contradictions without clearing', () => {
  const yes = birth.requirioHospitalizacion.questionOptions.answers.find((answer) => answer.label === 'Sí').concept;
  const no = birth.requirioHospitalizacion.questionOptions.answers.find((answer) => answer.label === 'No').concept;
  const isEmpty = (value) => value == null || value === '';
  for (const response of [yes, no, undefined, null]) {
    assert.equal(evaluateNative(birth.tiempoDeHospitalizacion.disabled.disableWhenExpression, {
      requirioHospitalizacion: response,
    }), response !== yes);
    for (const duration of [undefined, null, '', 0, 3]) {
      assert.equal(evaluateNative(birth.requirioHospitalizacion.validators[0].failsWhenExpression, {
        myValue: response, tiempoDeHospitalizacion: duration, isEmpty,
      }), response !== yes && !isEmpty(duration));
    }
  }
  assert.equal(birth.tiempoDeHospitalizacion.hide, undefined);
  assert.equal(birth.tiempoDeHospitalizacion.questionOptions.calculate, undefined);
  assert.ok(extractVariableNames(birth.tiempoDeHospitalizacion.disabled.disableWhenExpression)
    .includes('requirioHospitalizacion'));
  assert.ok(extractVariableNames(birth.requirioHospitalizacion.validators[0].failsWhenExpression)
    .includes('tiempoDeHospitalizacion'));
});

test('altitude warning includes the first nonzero adjustment band', () => {
  for (const [altitud, expected] of [[0, false], [499, false], [500, true], [501, true], [5500, true]]) {
    assert.equal(evaluate(anemia.altitud.alert.alertWhenExpression, { altitud }), expected, `altitude ${altitud}`);
  }
  assert.ok(Number(anemia.altitud.questionOptions.max) >= 5500);
});

test('gestational weeks use the encounter date, full weeks and calendar days', () => {
  const expression = obstetrics.edadGestacionalFUM.questionOptions.calculate.calculateExpression;
  const fum = date('2026-01-01');
  for (const [at, expected] of [['2026-03-12', 10], ['2026-03-18', 10], ['2026-03-19', 11]]) {
    assert.equal(evaluate(expression, { fum, fechaAtencion: date(at) }), expected);
  }
  // Includes a daylight-saving boundary in zones that observe one.
  assert.equal(evaluate(expression, { fum: date('2026-03-02'), fechaAtencion: date('2026-03-09') }), 1);
  for (const values of [{ fum }, { fechaAtencion: date('2026-03-12') }, {}]) {
    assert.equal(evaluate(expression, { fum: undefined, fechaAtencion: undefined, ...values }), undefined);
  }
});

test('FUM cannot be after the encounter but can be on its calendar date', () => {
  const expression = obstetrics.fum.validators.find((v) => v.type === 'js_expression').failsWhenExpression;
  for (const [value, expected] of [['2026-03-11', false], ['2026-03-12', false], ['2026-03-13', true]]) {
    assert.equal(evaluate(expression, { myValue: date(value), fechaAtencion: date('2026-03-12') }), expected);
  }
});

test('a past expected delivery date remains recordable; dates before FUM are rejected', () => {
  const validators = obstetrics.fechaProbableDeParto.validators;
  for (const [value, expected] of [['2026-09-07', false], ['2025-11-30', true]]) {
    const fails = validators.some((v) => evaluate(v.failsWhenExpression, {
      myValue: date(value), fum: date('2025-12-01'), today: () => date('2026-09-23'),
      isDateBefore: (left, right) => dayjs(left).isBefore(right),
    }));
    assert.equal(fails, expected);
  }
});

test('obstetric history allows an explicit absence without combining it with a disease', () => {
  const none = 'dbb7efe1-12d9-58b0-8de2-c218f626ff48';
  for (const id of ['antecedentesFamiliares', 'antecedentesPersonales']) {
    const field = history[id];
    assert.equal(field.required, true, `${id}: unanswered is not an explicit absence`);
    assert.ok(field.questionOptions.answers.some((answer) => answer.concept === none), id);
    const conditions = field.questionOptions.answers.filter((answer) => answer.concept !== none);
    const validator = field.validators.find((entry) => entry.type === 'js_expression');
    assert.ok(validator, `${id}: contradictory answers need validation`);
    for (const [myValue, expected] of [
      [undefined, false], [[], false], [[none], false],
      [[conditions[0].concept], false], [[conditions[0].concept, conditions[1].concept], false],
      [[none, conditions[0].concept], true], [[conditions[0].concept, none], true],
    ]) {
      assert.equal(evaluate(validator.failsWhenExpression, {
        myValue,
        arrayContains: (array, member) => Array.isArray(array) && array.includes(member),
      }), expected, `${id}: ${JSON.stringify(myValue)}`);
    }
  }
});

test('a prior preterm birth can retain its route, outcomes and weight without term births', () => {
  for (const partos of [undefined, null, 0, 1]) {
    for (const id of ['vaginales', 'cesaReas', 'nacidosVivos', 'nacidosMuertos', 'rnDeMayorPesoG']) {
      const field = history[id];
      const hidden = field.hide?.hideWhenExpression
        ? evaluate(field.hide.hideWhenExpression, { gestaciones: 1, partos, isEmpty: (value) => value == null })
        : false;
      assert.equal(hidden, false, `${id}: term births ${partos}`);
      assert.equal(field.required, false, `${id}: absence of a count is not zero`);
    }
  }
});

test('child mental-health results and required plans work without a caregiver violence field', () => {
  const instrument = mentalHealth.instrumentoTamizaje.questionOptions.answers[0].concept;
  const isEmpty = (value) => value == null || value === '';
  for (const [result, risk, required, hidden] of [
    [undefined, undefined, false, true],
    ['f1000000-0000-4000-8000-000000000191', 0, false, true],
    ['f1000000-0000-4000-8000-000000000192', 1, true, false],
    ['f1000000-0000-4000-8000-000000000193', 2, true, false],
  ]) {
    // No deleted field is supplied: an obsolete reference must fail evaluation.
    const values = { instrumentoTamizaje: instrument, resultadoTamizaje: result, isEmpty };
    assert.equal(evaluate(mentalHealth.nivelRiesgoCalculado.questionOptions.calculate.calculateExpression, values), risk);
    assert.equal(evaluate(mentalHealth.plan.required, values), required);
    assert.equal(evaluate(mentalHealth.plan.hide.hideWhenExpression, values), hidden);
    assert.equal(mentalHealth.puntajeTamizaje.required, true);
    assert.equal(mentalHealth.puntajeTamizaje.hide?.hideWhenExpression
      ? evaluate(mentalHealth.puntajeTamizaje.hide.hideWhenExpression, values) : false, false);
  }
});
