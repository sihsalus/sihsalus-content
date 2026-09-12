#!/usr/bin/env python3
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("split_ocl_export", Path(__file__).with_name("split_ocl_export.py"))
SPLITTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SPLITTER)


class SplitOclExportTest(unittest.TestCase):
    def setUp(self):
        source = {"id": "sihsalus", "owner": "SIHSALUS", "owner_type": "Organization",
                  "url": "/orgs/SIHSALUS/sources/sihsalus/"}
        retired = {"id": "2", "external_id": "neighborhood-uuid", "retired": True,
                   "url": source["url"] + "concepts/2/", "names": [{"name": "Barrio histórico"}]}
        mapping = {"id": "3", "external_id": "neighborhood-mapping-uuid", "retired": True,
                   "from_concept_url": retired["url"], "to_concept_url": retired["url"]}
        self.export = {
            "type": "Source Version", "owner": "SIHSALUS", "owner_type": "Organization",
            "short_code": "sihsalus", "id": "2026-09-09-1", "version": "2026-09-09-1",
            "released": True, "source": source, "extras": {"preserve": "official metadata"},
            "concepts": [
                {"id": "1", "external_id": "new-concept-uuid", "retired": False}, retired,
                {"id": "4", "external_id": "unrelated-history-uuid", "retired": True},
            ],
            "mappings": [mapping, {"id": "5", "external_id": "unrelated-mapping", "retired": True}],
        }
        self.manifest = {"source": source, "version": "2026-09-09-1",
                         "concepts": [self.entry(retired)], "mappings": [self.entry(mapping)]}

    @staticmethod
    def entry(item):
        return {"id": item["id"], "external_id": item["external_id"],
                "sha256": hashlib.sha256(SPLITTER.canonical_json_bytes(item)).hexdigest()}

    def test_preserves_new_concepts_unrelated_history_and_all_other_metadata(self):
        before = copy.deepcopy(self.export)
        actual = SPLITTER.exclude_retired_records(self.export, self.manifest)
        expected = copy.deepcopy(self.export)
        expected["concepts"].pop(1)
        expected["mappings"].pop(0)
        self.assertEqual(actual, expected)
        self.assertEqual(self.export, before)

    def test_rejects_another_source_version_or_unreleased_export(self):
        for key, value in (("owner", "Other"), ("short_code", "laboratorio"),
                           ("version", "HEAD"), ("id", "other-release"), ("released", False)):
            with self.subTest(key=key):
                export = copy.deepcopy(self.export)
                export[key] = value
                with self.assertRaisesRegex(ValueError, "released source version"):
                    SPLITTER.exclude_retired_records(export, self.manifest)
        export = copy.deepcopy(self.export)
        export["source"]["url"] = "/orgs/Other/sources/sihsalus/"
        with self.assertRaisesRegex(ValueError, "source identity"):
            SPLITTER.exclude_retired_records(export, self.manifest)

    def test_rejects_missing_duplicate_modified_or_reactivated_exclusions(self):
        for kind in ("concepts", "mappings"):
            for change in ("missing", "duplicate", "modified", "reactivated", "wrong-id", "wrong-uuid"):
                with self.subTest(kind=kind, change=change):
                    export = copy.deepcopy(self.export)
                    index = 1 if kind == "concepts" else 0
                    item = export[kind][index]
                    if change == "missing":
                        export[kind].pop(index)
                    elif change == "duplicate":
                        export[kind].append(copy.deepcopy(item))
                    elif change == "modified":
                        item["extras"] = {"changed": True}
                    elif change == "reactivated":
                        item["retired"] = False
                    elif change == "wrong-id":
                        item["id"] = "999"
                    else:
                        item["external_id"] = "different-uuid"
                    with self.assertRaises(ValueError):
                        SPLITTER.exclude_retired_records(export, self.manifest)
        manifest = copy.deepcopy(self.manifest)
        manifest["concepts"].append(copy.deepcopy(manifest["concepts"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate concepts exclusions"):
            SPLITTER.exclude_retired_records(self.export, manifest)

    def test_rejects_active_exclusion_even_when_fingerprint_matches(self):
        export = copy.deepcopy(self.export)
        export["concepts"][1]["retired"] = False
        manifest = copy.deepcopy(self.manifest)
        manifest["concepts"] = [self.entry(export["concepts"][1])]
        with self.assertRaisesRegex(ValueError, "cannot exclude active"):
            SPLITTER.exclude_retired_records(export, manifest)

    def test_rejects_additional_references_to_excluded_concepts(self):
        for field in ("from_concept_url", "to_concept_url"):
            for retired in (False, True):
                with self.subTest(field=field, retired=retired):
                    export = copy.deepcopy(self.export)
                    export["mappings"].append({"id": "6", "external_id": "additional-reference",
                                              "retired": retired,
                                              field: "https://api.openconceptlab.org" + export["concepts"][1]["url"]})
                    with self.assertRaisesRegex(ValueError, "retained mapping references"):
                        SPLITTER.exclude_retired_records(export, self.manifest)

    def test_split_is_reproducible_with_and_without_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, concepts, mappings = [root / name for name in ("source.zip", "concepts.zip", "mappings.zip")]
            manifest = root / "exclusions.json"
            manifest.write_text(json.dumps(self.manifest), encoding="utf-8")
            SPLITTER.write_export(source, self.export)
            SPLITTER.split_export(source, concepts, mappings)
            self.assertEqual(SPLITTER.read_export(concepts)["concepts"], self.export["concepts"])
            self.assertEqual(SPLITTER.read_export(mappings)["mappings"], self.export["mappings"])
            SPLITTER.split_export(source, concepts, mappings, manifest)
            initial_bytes = (concepts.read_bytes(), mappings.read_bytes())
            expected = SPLITTER.exclude_retired_records(self.export, self.manifest)
            reconstructed = SPLITTER.read_export(concepts)
            self.assertEqual(reconstructed["mappings"], [])
            self.assertEqual(SPLITTER.read_export(mappings)["concepts"], [])
            reconstructed["mappings"] = SPLITTER.read_export(mappings)["mappings"]
            self.assertEqual(reconstructed, expected)
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("export.json", json.dumps(self.export, indent=4))
            SPLITTER.split_export(source, concepts, mappings, manifest)
            self.assertEqual((concepts.read_bytes(), mappings.read_bytes()), initial_bytes)


if __name__ == "__main__":
    unittest.main()
