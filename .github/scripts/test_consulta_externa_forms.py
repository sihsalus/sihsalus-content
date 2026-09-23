"""Regression coverage for the simplified outpatient capture contract."""

import copy
import json
import unittest
from pathlib import Path

import validate_ce_physical_exam_contract as physical


class ConsultaExternaFormsTest(unittest.TestCase):
    def setUp(self):
        self.exam = json.loads(physical.FORM_PATH.read_text())
        self.anamnesis = json.loads(Path(
            "configuration/ampathforms/CE-ANAM-001-ANAMNESIS.json").read_text())

    def test_exam_only_captures_general_and_system_findings(self):
        self.assertEqual([], physical.validate_contract(self.exam))
        for field in physical.LEGACY_SOAP_FIELDS:
            with self.subTest(field=field):
                altered = copy.deepcopy(self.exam)
                altered["pages"][0]["sections"][-1]["questions"].append({
                    "id": field, "type": "obs", "questionOptions": {"rendering": "textarea"}})
                self.assertTrue(any("must not duplicate SOAP" in e
                                    for e in physical.validate_contract(altered)))

    def test_exam_does_not_require_a_second_objective_summary(self):
        required = {q["id"] for q in physical.walk(self.exam)
                    if q.get("type") == "obs" and q.get("required") is True}
        self.assertEqual({"estadoGeneral"}, required)

    def test_anamnesis_uses_choices_without_assuming_normal_findings(self):
        questions = {q["id"]: q for q in physical.walk(self.anamnesis) if q.get("type") == "obs"}
        for field in ("formaInicio", "cursoEnfermedad", "apetito", "sed", "sueno",
                      "estadoAnimo", "orina", "deposiciones"):
            with self.subTest(field=field):
                question = questions[field]
                options = question["questionOptions"]
                self.assertEqual("select", options["rendering"])
                self.assertTrue(options["answers"])
                self.assertNotIn("default", options)
                self.assertNotIn("default", question)
                self.assertNotIn("calculate", question)
                self.assertNotIn("enablePreviousValue", options)
                self.assertTrue(all(isinstance(a.get("value"), str) and "concept" not in a
                                    for a in options["answers"]))
        free_text = {key for key, q in questions.items()
                     if q["questionOptions"]["rendering"] in {"text", "textarea"}}
        self.assertEqual({"motivoConsulta", "tiempoEnfermedad", "relatoEnfermedadActual"}, free_text)
        self.assertIsNot(questions["relatoEnfermedadActual"].get("required"), True)


if __name__ == "__main__":
    unittest.main()
