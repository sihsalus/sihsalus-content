#!/usr/bin/env python3
"""Prevent draft terminology from entering the distributed package."""
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

    def test_etnias_release_preserves_internal_identity_and_resolves_official_codes(self):
        errors = []
        VALIDATOR.validate_split_export(self.exports, errors, "etnias", VALIDATOR.ETNIAS_CONCEPTS_EXPORT,
                                       VALIDATOR.ETNIAS_MAPPINGS_EXPORT, VALIDATOR.ETNIAS_CANONICAL_SHA256)
        self.assertEqual(errors, [])
        concepts = {c["id"]: c for c in self.exports[VALIDATOR.ETNIAS_CONCEPTS_EXPORT]["concepts"]}
        mappings = self.exports[VALIDATOR.ETNIAS_MAPPINGS_EXPORT]["mappings"]
        equivalents = [m for m in mappings if m.get("to_source_name") == "MINSA-ETNIAS"]
        self.assertEqual(len(concepts), 62)
        self.assertEqual(len(mappings), 122)
        self.assertEqual(len(equivalents), 58)
        self.assertEqual({m["to_concept_code"] for m in equivalents}, {str(i) for i in range(1, 61)} - {"5", "60"})
        self.assertTrue(all(m["map_type"] == "SAME-AS" and m["from_concept_code"] not in {"2", "61", "62"}
                            for m in equivalents))
        aimara = next(m for m in equivalents if m["to_concept_code"] == "2")
        self.assertEqual(aimara["from_concept_url"], concepts["4"]["url"])
        self.assertEqual(concepts["4"]["external_id"], "c79ac7a1-1cef-4524-bbc4-bb21fd5d5331")
        aliases = {(c["id"], n["name"]) for c in concepts.values() for n in c["names"]
                   if n.get("name_type") is None and not n.get("locale_preferred") and not n.get("retired")}
        self.assertEqual(aliases, {("8", "Aguaruna"), ("45", "Chayawita"), ("48", "Ticuna"),
                                   ("55", "Amuesha"), ("47", "Jebero")})
        answers = [m for m in mappings if m["map_type"] == "Q-AND-A"]
        self.assertEqual(sorted(m["sort_weight"] for m in answers), list(range(1, 63)))

    def test_etnias_pinned_release_rejects_drift_in_codes_weights_names_or_metadata(self):
        for kind in ("code", "weight", "name", "metadata", "missing"):
            exports = dict(self.exports)
            for path in (VALIDATOR.ETNIAS_CONCEPTS_EXPORT, VALIDATOR.ETNIAS_MAPPINGS_EXPORT):
                exports[path] = copy.deepcopy(self.exports[path])
            concepts, mappings = exports[VALIDATOR.ETNIAS_CONCEPTS_EXPORT], exports[VALIDATOR.ETNIAS_MAPPINGS_EXPORT]
            if kind == "code":
                next(m for m in mappings["mappings"] if m.get("to_source_name") == "MINSA-ETNIAS")["to_concept_code"] = "99999"
            elif kind == "weight":
                next(m for m in mappings["mappings"] if m["map_type"] == "Q-AND-A")["sort_weight"] = None
            elif kind == "name":
                concepts["concepts"][0]["names"][0]["name"] = "Alterado"
            elif kind == "metadata":
                mappings["version"] = "HEAD"
            else:
                del exports[VALIDATOR.ETNIAS_CONCEPTS_EXPORT]
            errors = []
            VALIDATOR.validate_split_export(exports, errors, "etnias", VALIDATOR.ETNIAS_CONCEPTS_EXPORT,
                                           VALIDATOR.ETNIAS_MAPPINGS_EXPORT, VALIDATOR.ETNIAS_CANONICAL_SHA256)
            with self.subTest(kind=kind):
                self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
