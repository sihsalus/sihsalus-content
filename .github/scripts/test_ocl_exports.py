#!/usr/bin/env python3
"""Prevent draft terminology from entering the distributed package."""
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


class PublishedOclExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exports = {}
        for path in sorted(VALIDATOR.OCL_DIR.glob("*.zip")):
            with zipfile.ZipFile(path) as archive:
                cls.exports[path] = json.loads(archive.read("export.json"))

    def test_packaged_exports_are_published_versions(self):
        errors = []
        for path, export in self.exports.items():
            VALIDATOR.validate_released_export(path, export, errors)
        self.assertEqual(errors, [])

    def test_rejects_draft_snapshot_or_missing_release_flag(self):
        for export in (
            {"version": "2026-10-16-1", "released": False},
            {"version": "HEAD", "released": True},
            {"version": "2026-10-16-1"},
            {"version": "2026-10-16-1", "released": "true"},
            {"released": True},
        ):
            with self.subTest(export=export):
                errors = []
                VALIDATOR.validate_released_export(Path("draft.zip"), export, errors)
                self.assertTrue(errors)

    def test_neighborhood_identities_cannot_return_in_the_main_source_even_retired(self):
        concepts = {concept["id"]: concept for concept in self.exports[
            VALIDATOR.EXPECTED_SIHSALUS_CONCEPTS_EXPORT]["concepts"]}
        neighborhood = dict(self.exports[VALIDATOR.NEIGHBORHOOD_CONCEPTS_EXPORT]["concepts"][0],
                            id="historical-neighborhood", retired=True)
        concepts[neighborhood["id"]] = neighborhood
        errors = []
        VALIDATOR.validate_neighborhood_terminology(self.exports, concepts, errors)
        self.assertTrue(any("must not bundle neighborhood UUIDs" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
