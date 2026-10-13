#!/usr/bin/env python3

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("validate_visit_note_content_contract.py")
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("validate_visit_note_content_contract", SCRIPT_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class VisitNoteContentContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.contract = json.loads((cls.root / VALIDATOR.CONTRACT_PATH).read_text())
        errors = []
        cls.catalog = VALIDATOR.load_concept_catalog(cls.root, errors)
        if errors:
            raise AssertionError(errors)

    def test_repository_contract_is_valid(self):
        self.assertEqual([], VALIDATOR.validate(self.root))

    def test_rejects_wrong_concept_datatype(self):
        contract = copy.deepcopy(self.contract)
        contract["concepts"][0]["datatype"] = "Coded"
        errors = VALIDATOR.validate_concepts(contract, self.catalog)
        self.assertTrue(any("must be Coded" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
