#!/usr/bin/env python3
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

sys.dont_write_bytecode = True
import check_rxnorm_mappings as checker
from split_ocl_export import write_export


class RxNormMappingCheckTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.mapping = {
            "type": "Mapping", "id": "1", "retired": False, "map_type": "SAME-AS",
            "owner": "SIHSALUS", "source": "medicamentos", "from_concept_code": "10",
            "from_source_url": "/orgs/SIHSALUS/sources/medicamentos/",
            "to_source_name": "RxNORM", "to_concept_code": "123",
        }
        self.export = {
            "type": "Source Version", "short_code": "medicamentos", "version": "future-release",
            "id": "future-release", "released": True, "owner": "SIHSALUS",
            "source": {"id": "medicamentos", "short_code": "medicamentos", "owner": "SIHSALUS"},
            "concepts": [], "mappings": [self.mapping],
        }
        self.version = {"version": "synthetic-release", "apiVersion": "synthetic-api"}
        self.active = {"rxcuiStatusHistory": {
            "metaData": {"status": "Active", "isCurrent": "YES"},
            "attributes": {"rxcui": "123", "name": "Synthetic ingredient", "tty": "IN"},
        }}
        self.calls = []

    def write(self):
        write_export(self.root / "arbitrary-filename.zip", self.export)

    def fetch(self, endpoint):
        self.calls.append(endpoint)
        return copy.deepcopy(self.version if endpoint == "version.json" else self.active)

    def check(self, fetch=None):
        self.write()
        return checker.check(self.root, fetch or self.fetch)

    def test_current_mapping_retains_source_relationship_and_nlm_attributes(self):
        report, code = self.check()
        self.assertEqual(code, 0)
        result = report["results"][0]
        self.assertEqual((result["result"], result["name"], result["tty"]),
                         ("CURRENT", "Synthetic ingredient", "IN"))
        self.assertEqual(result["references"][0]["map_type"], "SAME-AS")
        self.assertEqual(report["sources"][0]["version"], "future-release")
        self.assertEqual(self.calls, ["version.json", "rxcui/123/historystatus.json", "version.json"])

    def test_remapped_obsolete_or_not_current_require_review_without_remapping(self):
        for status, current in (("Remapped", "NO"), ("Obsolete", "NO"), ("Active", "NO")):
            with self.subTest(status=status):
                self.active["rxcuiStatusHistory"]["metaData"] = {"status": status, "isCurrent": current}
                report, code = self.check()
                self.assertEqual(code, 1)
                self.assertEqual(report["results"][0]["nlm_status"], status)
                self.assertEqual(report["results"][0]["rxcui"], "123")

    def test_http_or_json_error_never_reports_current(self):
        for error in (URLError("synthetic network failure"), json.JSONDecodeError("invalid", "x", 0)):
            with self.subTest(error=type(error).__name__):
                def fetch(endpoint):
                    if endpoint != "version.json":
                        raise error
                    return self.version
                report, code = self.check(fetch)
                self.assertEqual((code, report["results"][0]["result"]), (2, "ERROR"))

    def test_unknown_status_without_descriptive_attributes_requires_review(self):
        self.active = {"rxcuiStatusHistory": {
            "metaData": {"status": "Unknown", "isCurrent": "NO"}, "attributes": {"rxcui": "123"},
        }}
        report, code = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(report["results"][0]["nlm_status"], "Unknown")
        self.assertIsNone(report["results"][0]["name"])
        self.assertIsNone(report["results"][0]["tty"])

    def test_incomplete_history_or_mismatched_rxcui_is_an_error(self):
        for section, key in (("metaData", "status"), ("metaData", "isCurrent"),
                             ("attributes", "rxcui"), ("attributes", "name"), ("attributes", "tty")):
            with self.subTest(section=section, key=key):
                response = copy.deepcopy(self.active)
                del response["rxcuiStatusHistory"][section][key]
                report, code = self.check(lambda endpoint: self.version if endpoint == "version.json" else response)
                self.assertEqual(code, 2)
        self.active["rxcuiStatusHistory"]["attributes"]["rxcui"] = "999"
        report, code = self.check()
        self.assertEqual(code, 2)
        self.assertIn("does not match", report["results"][0]["error"])

    def test_version_failure_or_change_is_an_error(self):
        for final in ({}, {**self.version, "version": "changed"}, {**self.version, "apiVersion": "changed"}):
            with self.subTest(final=final):
                versions = iter([self.version, final])
                report, code = self.check(lambda endpoint: next(versions) if endpoint == "version.json" else self.active)
                self.assertEqual((code, report["result"]), (2, "ERROR"))
                self.assertTrue(report["errors"])
        report, code = self.check(lambda _endpoint: {})
        self.assertEqual(code, 2)

    def test_retired_or_other_source_mapping_is_not_queried(self):
        self.export["mappings"] += [
            {**self.mapping, "id": "2", "retired": True, "to_concept_code": "456"},
            {**self.mapping, "id": "3", "to_source_name": "SNOMED-CT", "to_concept_code": "789"},
            {"retired": True},
        ]
        report, code = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(len(report["results"]), 1)
        self.assertNotIn("rxcui/456/historystatus.json", self.calls)
        self.assertNotIn("rxcui/789/historystatus.json", self.calls)

    def test_invalid_rxcui_is_an_error_and_is_never_queried(self):
        for value in ("", "abc", "12/../3", "１２３", None):
            with self.subTest(value=value):
                self.calls.clear()
                self.mapping["to_concept_code"] = value
                report, code = self.check()
                self.assertEqual((code, report["results"][0]["result"]), (2, "ERROR"))
                self.assertEqual(self.calls, ["version.json", "version.json"])

    def test_empty_inventory_or_no_active_rxnorm_mapping_is_an_error(self):
        report, code = checker.check(self.root, self.fetch)
        self.assertEqual((code, report["result"]), (2, "ERROR"))
        for mappings in ([], [{**self.mapping, "retired": True}], [{**self.mapping, "to_source_name": "Other"}]):
            with self.subTest(mappings=mappings):
                self.export["mappings"] = mappings
                report, code = self.check()
                self.assertEqual(code, 2)
        self.assertEqual(self.calls, [])

    def test_deduplicates_queries_but_keeps_every_mapping_reference(self):
        self.export["mappings"].append({**self.mapping, "id": "2", "map_type": "NARROWER-THAN"})
        report, code = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(self.calls.count("rxcui/123/historystatus.json"), 1)
        self.assertEqual([item["mapping_id"] for item in report["results"][0]["references"]], ["1", "2"])

    def test_active_mapping_without_target_source_blocks_even_with_another_valid_mapping(self):
        unidentified = {key: value for key, value in self.mapping.items() if key != "to_source_name"}
        unidentified["id"] = "2"
        self.export["mappings"].append(unidentified)
        report, code = self.check()
        self.assertEqual((code, report["result"]), (2, "ERROR"))
        self.assertIn("target source identity is missing", report["errors"][0])
        self.assertEqual(self.calls, [])

    def test_non_string_target_name_or_url_fails_before_querying_nlm(self):
        for change in ({"to_source_name": 0, "to_source_url": "/orgs/NLM/sources/RxNORM/"},
                       {"to_source_name": False}, {"to_source_name": ["RxNORM"]},
                       {"to_source_url": 0}, {"to_source_url": {}}, {"to_source_url": ["RxNORM"]}):
            with self.subTest(change=change):
                self.export["mappings"] = [{**self.mapping, **change}]
                report, code = self.check()
                self.assertEqual((code, report["result"]), (2, "ERROR"))
        self.assertEqual(self.calls, [])

    def test_discovers_source_from_metadata_and_rejects_conflicting_identity(self):
        del self.export["short_code"]
        self.assertEqual(self.check()[1], 0)
        self.export["short_code"] = "another-source"
        report, code = self.check()
        self.assertEqual(code, 2)
        self.assertIn("Conflicting", report["errors"][0])

    def test_rxnorm_target_name_and_url_are_case_insensitive_but_must_agree(self):
        self.mapping["to_source_name"] = "RxNorm"
        self.assertEqual(self.check()[1], 0)
        self.mapping["to_source_name"] = None
        self.mapping["to_source_url"] = "/orgs/NLM/sources/RxNORM/"
        self.assertEqual(self.check()[1], 0)
        self.mapping["to_source_name"] = "Other"
        report, code = self.check()
        self.assertEqual(code, 2)
        self.assertIn("Conflicting RxNorm", report["errors"][0])

    def test_rejects_unreleased_head_unidentified_or_foreign_source_versions(self):
        original = copy.deepcopy(self.export)
        for change in ({"released": False}, {"version": "HEAD", "id": "HEAD"}, {"version": ""},
                       {"version": None}, {"id": "another-version"}, {"owner": "Other"},
                       {"source": {**self.export["source"], "owner": "Other"}}):
            with self.subTest(change=change):
                self.export = {**original, **change}
                report, code = self.check()
                self.assertEqual((code, report["result"]), (2, "ERROR"))
        self.assertEqual(self.calls, [])

    def test_rejects_mixed_releases_before_querying_nlm(self):
        self.write()
        write_export(self.root / "another.zip", {**self.export, "version": "another", "id": "another"})
        report, code = checker.check(self.root, self.fetch)
        self.assertEqual(code, 2)
        self.assertIn("Multiple medicamentos releases", report["errors"][0])
        self.assertEqual(self.calls, [])

    def test_rejects_missing_mapping_references_or_conflicting_owner(self):
        original = copy.deepcopy(self.mapping)
        for change in ({"id": ""}, {"from_concept_code": None}, {"map_type": ""}, {"source": "Other"},
                       {"owner": "Other"}, {"type": "Concept"}):
            with self.subTest(change=change):
                self.export["mappings"] = [{**original, **change}]
                report, code = self.check()
                self.assertEqual((code, report["result"]), (2, "ERROR"))
        self.assertEqual(self.calls, [])

    def test_cli_outputs_public_json_and_preserves_archive_bytes(self):
        self.write()
        before = (self.root / "arbitrary-filename.zip").read_bytes()
        output = io.StringIO()
        with patch.object(checker, "get_json", self.fetch), contextlib.redirect_stdout(output):
            code = checker.main(["--ocl-dir", str(self.root)])
        report = json.loads(output.getvalue())
        self.assertEqual((code, report["result"]), (0, "CURRENT"))
        self.assertEqual(report["nlm_url"], checker.NLM_URL)
        self.assertEqual(report["sources"][0]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual((self.root / "arbitrary-filename.zip").read_bytes(), before)

    def test_http_request_uses_fixed_nlm_get_and_timeout(self):
        with patch.object(checker.urllib.request, "urlopen") as request:
            request.return_value.__enter__.return_value.read.return_value = b'{"version":"synthetic"}'
            self.assertEqual(checker.get_json("version.json"), {"version": "synthetic"})
        self.assertEqual(request.call_args.args[0].full_url, checker.NLM_URL + "version.json")
        self.assertEqual(request.call_args.args[0].get_method(), "GET")
        self.assertEqual(request.call_args.kwargs["timeout"], checker.TIMEOUT)


if __name__ == "__main__":
    unittest.main()
