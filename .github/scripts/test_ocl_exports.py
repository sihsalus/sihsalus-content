#!/usr/bin/env python3
"""Regression checks for the institutional catalog transition and birth length."""
import copy
import importlib.util
import json
import sys
import unittest
import zipfile
from pathlib import Path


sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("validate_ocl_exports", Path(__file__).with_name("validate_ocl_exports.py"))
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class InstitutionalOclExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exports = {}
        for path in sorted(VALIDATOR.OCL_DIR.glob("*.zip")):
            with zipfile.ZipFile(path) as archive:
                cls.exports[path] = json.loads(archive.read("export.json"))

    def validate(self, exports):
        errors = []
        VALIDATOR.validate_institutional_exports(exports, errors)
        return errors

    def test_bundled_exports_match_all_reconciled_institutional_pins(self):
        self.assertEqual(self.validate(self.exports), [])

    def test_rejects_missing_catalog_or_duplicate_split(self):
        path = next(path for path, export in self.exports.items() if export["short_code"] == "diagnosis")
        exports = dict(self.exports)
        del exports[path]
        self.assertTrue(self.validate(exports))
        exports = dict(self.exports)
        exports[path.with_name("99_duplicate.zip")] = exports[path]
        self.assertTrue(self.validate(exports))

    def test_rejects_unreleased_or_different_version_for_other_catalogs(self):
        path = VALIDATOR.REFERRAL_CONCEPTS_EXPORT
        for field, value in (("released", False), ("version", "HEAD"), ("owner", "AnotherOrganization")):
            with self.subTest(field=field):
                exports = dict(self.exports)
                exports[path] = dict(exports[path], **{field: value})
                self.assertTrue(self.validate(exports))

    def test_rejects_source_metadata_drift_even_when_concepts_are_unchanged(self):
        path = VALIDATOR.REFERRAL_CONCEPTS_EXPORT
        exports = dict(self.exports)
        exports[path] = dict(exports[path], uuid="different-server-export")
        self.assertTrue(any("reconciled artifact" in error for error in self.validate(exports)))

    def test_rejects_identity_change_in_unrelated_catalog(self):
        path = VALIDATOR.REFERRAL_CONCEPTS_EXPORT
        exports = dict(self.exports)
        exports[path] = copy.deepcopy(exports[path])
        exports[path]["concepts"][0]["external_id"] = "replacement-identity"
        self.assertTrue(any("reconciled artifact" in error for error in self.validate(exports)))

    def test_rejects_mappings_before_concepts(self):
        exports = dict(self.exports)
        concepts = VALIDATOR.NEIGHBORHOOD_CONCEPTS_EXPORT
        mappings = VALIDATOR.NEIGHBORHOOD_MAPPINGS_EXPORT
        exports[concepts], exports[mappings] = exports[mappings], exports[concepts]
        self.assertTrue(any("inventory/order" in error for error in self.validate(exports)))

    def test_main_source_is_the_exact_unpublished_candidate(self):
        errors = []
        VALIDATOR.validate_sihsalus_export(self.exports, errors)
        self.assertEqual(errors, [])
        for field, value in (("released", True), ("version", "HEAD")):
            with self.subTest(field=field):
                exports = dict(self.exports)
                for path in (VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT, VALIDATOR.EXPECTED_SIHSALUS_MAPPINGS_EXPORT):
                    exports[path] = dict(exports[path], **{field: value})
                errors = []
                VALIDATOR.validate_sihsalus_export(exports, errors)
                self.assertTrue(any("exact unpublished" in error for error in errors))

    def test_anatomy_must_remain_the_exact_unpublished_transition_candidate(self):
        exports = dict(self.exports)
        for path in (VALIDATOR.PROCEDURE_ANATOMY_CONCEPTS_EXPORT, VALIDATOR.PROCEDURE_ANATOMY_MAPPINGS_EXPORT):
            self.assertIs(exports[path]["released"], False)
            exports[path] = dict(exports[path], released=True)
        self.assertTrue(any("released must be False" in error for error in self.validate(exports)))

    def test_neighborhood_identities_cannot_return_in_the_main_source_even_retired(self):
        concepts = {concept["id"]: concept for concept in self.exports[
            VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT]["concepts"]}
        neighborhood = dict(self.exports[VALIDATOR.NEIGHBORHOOD_CONCEPTS_EXPORT]["concepts"][0],
                            id="historical-neighborhood", retired=True)
        concepts[neighborhood["id"]] = neighborhood
        errors = []
        VALIDATOR.validate_neighborhood_terminology(self.exports, concepts, errors)
        self.assertTrue(any("must not bundle neighborhood UUIDs" in error for error in errors))


class BirthLengthMetadataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT) as archive:
            cls.export = json.loads(archive.read("export.json"))
        cls.concept = next(concept for concept in cls.export["concepts"] if concept["id"] == "382")

    def validate(self, concepts):
        errors = []
        records = [(VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT, "sihsalus", concept) for concept in concepts]
        VALIDATOR.validate_birth_length(records, errors)
        return errors

    def test_bundled_birth_length_accepts_decimals_and_preserves_cm_and_uuid(self):
        self.assertEqual(self.validate([self.concept]), [])

    def test_rejects_integer_metadata_missing_flag_or_truthy_string(self):
        for value in (False, None, "true", 1):
            with self.subTest(value=value):
                concept = copy.deepcopy(self.concept)
                concept["extras"]["allow_decimal"] = value
                self.assertTrue(self.validate([concept]))

    def test_rejects_unit_datatype_identity_or_retirement_changes(self):
        for field, value in (("datatype", "Text"), ("external_id", "another-uuid"), ("retired", True)):
            with self.subTest(field=field):
                concept = dict(self.concept, **{field: value})
                self.assertTrue(self.validate([concept]))
        concept = copy.deepcopy(self.concept)
        concept["extras"]["units"] = "m"
        self.assertTrue(self.validate([concept]))

    def test_rejects_missing_or_duplicate_birth_length(self):
        self.assertTrue(self.validate([]))
        self.assertTrue(self.validate([self.concept, self.concept]))


if __name__ == "__main__":
    unittest.main()
