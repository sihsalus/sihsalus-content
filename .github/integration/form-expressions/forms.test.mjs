import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import dayjs from 'dayjs';

// Evaluate the shipped expressions with the date library exposed by the form engine.
// This tests schema behavior, not browser rendering or encounter persistence.
function fields(filename) {
  const form = JSON.parse(readFileSync(new URL(`../../../configuration/ampathforms/${filename}`, import.meta.url)));
  const walk = ({ questions = [] }) => questions.flatMap((question) => [question, ...walk(question)]);
  return Object.fromEntries(form.pages.flatMap((page) => page.sections.flatMap(walk)).map((q) => [q.id, q]));
}

const anemia = fields('CRED-001-TAMIZAJE DE ANEMIA.json');
const obstetrics = fields('OBST-002-EMBARAZO ACTUAL.json');
const evaluate = (expression, values) => vm.runInNewContext(expression, { dayjs, ...values });
const date = (value) => dayjs(value).toDate();

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
