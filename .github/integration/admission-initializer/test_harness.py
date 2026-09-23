#!/usr/bin/env python3
"""Pure harness contracts. No Docker, network, backend, or existing credentials."""

import io
import json
import subprocess
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import guards
import harness
from guards import HarnessFailure, CANONICAL_ROLE, LEGACY_ROLE, CANONICAL_UUID


def archive(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as handle:
        for name, value in entries:
            item = tarfile.TarInfo(name)
            if isinstance(value, bytes):
                item.size = len(value)
                handle.addfile(item, io.BytesIO(value))
            else:
                item.type = value[0]
                item.linkname = "outside"
                handle.addfile(item)
    return output.getvalue()


def completed(code=0, stdout=b"", stderr=b""):
    return subprocess.CompletedProcess(["synthetic"], code, stdout, stderr)


def clinical_drug_result():
    concept = "00d9cb0c-4aef-4614-ab38-a9978e3d62e1"
    drug = "07c2b995-5619-4d82-8b55-e4cdf96f94d1"
    tablet = "bd1e9059-62b4-4967-a804-a63eda4f8657"
    name = "ÁCIDO URSODESOXICÓLICO 250 mg - Tableta"
    rows = [
        ["310\t" + concept + "\t0\tDrug\tN/A"],
        ["en\tUrsodeoxycholic acid", "es\tÁCIDO URSODESOXICÓLICO"],
        ["410\t" + drug + "\t" + name + "\t0\t250 mg\t" + concept + "\t" + tablet + "\t0\t1"],
    ]
    response = {"results": [{"uuid": drug, "name": name, "display": "synthetic-private-display",
        "strength": "250 mg", "concept": {"uuid": concept, "display": "ÁCIDO URSODESOXICÓLICO"},
        "dosageForm": {"uuid": tablet, "display": "Tableta"}}]}
    return rows, response


def ocl_refresh_result():
    return [
        ["510\t3fb84698-488a-447d-acbc-72e8665cffdc\t0\tMisc\tN/A\t1:512"],
        ["511\td14f251d-82a1-4ecf-aa45-f17f57a193db\t0\tFinding\tN/A\tCuatro cruces"],
        ["512\t0fd3e744-6d2c-4cb3-9b7e-1f88899635d9\t0\t1"],
        [f"{610 + index}\t10000000-0000-4000-8000-{index:012d}\t{710 + index}"
         f"\t20000000-0000-4000-8000-{index:012d}\t0" for index in range(10)],
    ]


class HarnessContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="admission-harness-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.env = {
            "GITHUB_ACTIONS": "true", "CI": "true",
            "RUNNER_ENVIRONMENT": "github-hosted", "RUNNER_OS": "Linux",
            "GITHUB_REPOSITORY": "sihsalus/sihsalus-content",
            "ADMISSION_INITIALIZER_DISPOSABLE": "github-runner-only",
            "GITHUB_SHA": "a" * 40, "RUNNER_TEMP": str(self.root),
        }
        self.runtime = object.__new__(harness.Harness)
        self.runtime.hospital_roles = []

    def test_explicit_hosted_runner_authority_required_before_subprocess(self):
        self.assertEqual(guards.validate_runner(self.env), self.root)
        for key in self.env:
            if key == "RUNNER_TEMP":
                continue
            with self.subTest(key=key), patch.object(guards.subprocess, "run") as run:
                invalid = {**self.env, key: ""}
                with self.assertRaises(HarnessFailure):
                    harness.Harness(invalid)
                run.assert_not_called()

    def test_fresh_scenario_is_independent_and_cleanup_remains_mandatory(self):
        for cleanup_ok in (True, False):
            with self.subTest(cleanup_ok=cleanup_ok), patch.object(harness, "Harness") as runtime, \
                    patch.object(harness.signal, "signal"), patch.object(harness, "emit"):
                instance = runtime.return_value
                instance.cleanup.return_value = cleanup_ok
                self.assertEqual(harness.main("fresh"), 0 if cleanup_ok else 1)
                instance.prepare.assert_called_once_with()
                instance.fresh.assert_called_once_with()
                instance.baseline.assert_not_called()
                instance.upgrade.assert_not_called()
                instance.rejection.assert_not_called()
                instance.cleanup.assert_called_once_with()
        with patch.object(harness, "Harness") as runtime, patch.object(harness.signal, "signal"), \
                patch.object(harness, "emit") as emit:
            self.assertEqual(harness.main("invalid"), 1)
        runtime.assert_not_called()
        emit.assert_any_call("harness", "FAILED", reason="invalid_initializer_scenario")

    def test_baseline_snapshot_requires_restart_with_unchanged_history(self):
        for changed in (False, True):
            with self.subTest(changed=changed), patch.object(harness, "emit"):
                events = []
                runtime = self.runtime
                runtime.baseline_config = self.root / "baseline"
                runtime.baseline_data = self.root / "snapshot"
                runtime.baseline_dump = self.root / "dump.sql"
                runtime.role_md5, runtime.fixtures = "fixed-checksum", []
                runtime.remaining = Mock(return_value=180)
                runtime.start_database = Mock(return_value="db")
                runtime.start_backend = Mock(side_effect=[("first", "volume"), ("second", "volume")])
                runtime.wait_initializer = Mock(side_effect=lambda backend, stage: events.append(stage))
                runtime.assert_checksums = Mock()
                runtime.candidate_recorded = Mock(return_value=False)
                original = ["normalize-admission-role-name-20260722"]
                runtime.history = Mock(side_effect=[original, ["changed"] if changed else original, original])
                runtime.docker = Mock(return_value=completed(stdout=b"synthetic-dump"))
                runtime.remove_container = Mock()
                runtime.check_emrapi_roles = Mock()
                runtime.create_fixtures = Mock(side_effect=lambda backend: events.append("fixtures"))
                runtime.check_admission = Mock()
                runtime.copy_tree = Mock(side_effect=lambda *args: events.append("snapshot"))
                if changed:
                    with self.assertRaisesRegex(HarnessFailure, "^baseline_restart_changed_history$"):
                        runtime.baseline()
                    runtime.copy_tree.assert_not_called()
                    runtime.create_fixtures.assert_not_called()
                else:
                    runtime.baseline()
                    self.assertEqual(events, ["baseline", "baseline_restart", "fixtures", "snapshot"])
                    runtime.start_backend.assert_called_with("baseline-restart", runtime.baseline_config,
                                                             data_volume="volume")
                    self.assertEqual(runtime.baseline_dump.read_bytes(), b"synthetic-dump")

    def test_operational_scenario_uses_real_baseline_and_always_cleans_up(self):
        for cleanup_ok in (True, False):
            with self.subTest(cleanup_ok=cleanup_ok), patch.object(harness, "Harness") as runtime, \
                    patch.object(harness.signal, "signal"), patch.object(harness, "emit"):
                instance = runtime.return_value
                instance.cleanup.return_value = cleanup_ok
                self.assertEqual(harness.main("operational"), 0 if cleanup_ok else 1)
                instance.prepare.assert_called_once_with()
                instance.baseline.assert_called_once_with()
                instance.upgrade.assert_called_once_with(operational=True)
                instance.fresh.assert_not_called()
                instance.rejection.assert_not_called()
                instance.cleanup.assert_called_once_with()

    def test_rejection_preserves_prior_history_and_only_records_preparatory_noop(self):
        before = ["historical\tauthor\tchecksum"]
        preparatory = harness.OPERATIONAL_CHANGESET + "\tauthor\tchecksum"
        self.runtime.candidate_recorded = Mock(return_value=True)
        for rows, accepted in ((before + [preparatory], True), (before, False),
                               (before + [preparatory, "unexpected"], False),
                               (["historical\tchanged", preparatory], False)):
            with self.subTest(rows=rows):
                self.runtime.history = Mock(return_value=rows)
                if accepted:
                    self.runtime.assert_rejected_history("db", before)
                else:
                    with self.assertRaisesRegex(HarnessFailure, "^rejected_migration_changed_history$"):
                        self.runtime.assert_rejected_history("db", before)

    def test_arrival_payment_requires_one_active_optional_freetext_attribute(self):
        valid = "0\t0\t1\torg.openmrs.customdatatype.datatype.FreeTextDatatype"
        for rows in ([valid], [], [valid, valid], [valid.replace("0\t0", "1\t0")],
                     [valid.replace("0\t0", "0\t1")], [valid.replace("0\t1", "0\t2")],
                     [valid.replace("FreeText", "Integer")]):
            with self.subTest(rows=rows), patch.object(harness, "emit") as emit:
                self.runtime.query = Mock(return_value=rows)
                if rows == [valid]:
                    self.runtime.check_arrival_payment("db")
                    emit.assert_called_once()
                else:
                    with self.assertRaisesRegex(HarnessFailure, "^arrival_payment_metadata_invalid$"):
                        self.runtime.check_arrival_payment("db")
                    emit.assert_not_called()
                self.assertTrue(self.runtime.query.call_args.args[1].startswith("SELECT "))

    def test_external_docker_and_broad_or_symlink_temp_rejected(self):
        for key in ("DOCKER_HOST", "DOCKER_CONTEXT"):
            with self.subTest(key=key), self.assertRaises(HarnessFailure):
                guards.validate_runner({**self.env, key: "synthetic-forbidden"})
        link = self.root / "link"
        link.symlink_to(self.root, target_is_directory=True)
        for value in ("/", ".", str(link), str(self.root / "missing")):
            with self.subTest(value=value), self.assertRaises(HarnessFailure):
                guards.validate_runner({**self.env, "RUNNER_TEMP": value})

    def test_command_errors_report_only_static_operation_and_exit_code(self):
        failures = [
            completed(19, b"synthetic-private-output", b"synthetic-private-error"),
            subprocess.TimeoutExpired(["synthetic-private-argument"], 1),
            OSError("synthetic-private-path"),
        ]
        for result, expected in zip(failures, ("docker_exec_exit_19", "docker_exec_timeout", "docker_exec_unavailable")):
            with self.subTest(expected=expected), patch.object(guards.subprocess, "run") as run:
                if isinstance(result, Exception):
                    run.side_effect = result
                else:
                    run.return_value = result
                with self.assertRaisesRegex(HarnessFailure, "^" + expected + "$"):
                    guards.checked(["synthetic-private-argument"], operation="docker_exec")
        with self.assertRaisesRegex(HarnessFailure, "unsafe_diagnostic_operation"):
            guards.checked(["unused"], operation="synthetic-private-operation")

    def test_docker_always_uses_empty_owned_config_and_local_socket(self):
        self.runtime.docker_config = self.root / "empty-config"
        self.runtime.env = {"PATH": "/usr/bin"}
        self.runtime.cleanup_deadline = None
        with patch.object(harness, "checked", return_value=completed()) as checked:
            self.runtime.docker("image", "inspect", guards.BACKEND)
        args = checked.call_args.args[0]
        self.assertEqual(args[:5], ["docker", "--config", str(self.runtime.docker_config),
                                    "--host", "unix:///var/run/docker.sock"])
        self.assertEqual(checked.call_args.kwargs["env"], {"PATH": "/usr/bin"})
        self.assertEqual(checked.call_args.kwargs["operation"], "docker_image")

    def test_archive_keeps_owned_files_and_honors_exact_packaging_excludes(self):
        for index, prefix in enumerate(("configuration", "configuration/backend_configuration")):
            with self.subTest(prefix=prefix):
                entries = [
                    (prefix, (tarfile.DIRTYPE,)),
                    (prefix + "/roles/roles-core.csv", b"synthetic"),
                    (prefix + "/roles/.gitkeep", b""),
                    (prefix + "/.DS_Store", b""),
                    (prefix + "/ampathforms/Readme", b"ignored"),
                    (prefix + "/ampathforms/_deprecated/a.json", b"ignored"),
                ]
                destination = self.root / str(index)
                guards.extract_archive(archive(entries), destination, prefix, package=True)
                self.assertEqual(set(guards.manifest(destination)), {"roles/roles-core.csv"})
                self.assertEqual((destination / "roles/roles-core.csv").read_bytes(), b"synthetic")

    def test_git_configuration_preserves_runtime_paths_for_current_and_historical_sources(self):
        current = (harness.ROOT / "assembly.xml").read_bytes()
        ns = {"a": "http://maven.apache.org/plugins/maven-assembly-plugin/assembly/1.1.3"}
        old = ET.fromstring(current)
        content = old.findall("a:fileSets/a:fileSet", ns)[1]
        content.remove(content.find("a:outputDirectory", ns))
        content.find("a:includes/a:include", ns).text = "backend_configuration/**/*"
        for node in content.findall("a:excludes/a:exclude", ns):
            if node.text.startswith("ampathforms/"):
                node.text = "backend_configuration/" + node.text
        historical = ET.tostring(old)
        cases = (
            (guards.IMAGE_CONTENT_SHA, "1.25.12", "configuration/backend_configuration", historical),
            (guards.BASELINE_SHA, "1.25.15", "configuration/backend_configuration", historical),
            ("a" * 40, None, "configuration", current),
        )
        for index, (sha, version, prefix, assembly) in enumerate(cases):
            with self.subTest(sha=sha):
                pom = ('<project xmlns="http://maven.apache.org/POM/4.0.0"><version>'
                       + (version or "1.25.24") + '</version></project>').encode()
                data = archive([(prefix + "/roles/roles-core.csv", b"synthetic")])
                with patch.object(harness, "checked", side_effect=[
                    completed(), completed(stdout=pom), completed(stdout=assembly), completed(stdout=data),
                ]) as checked:
                    destination = self.root / str(index)
                    self.runtime.git_configuration(sha, version, destination)
                self.assertEqual(checked.call_args.args[0], ["git", "archive", sha, prefix])
                self.assertEqual(set(guards.manifest(destination)), {"roles/roles-core.csv"})
                self.assertEqual((destination / "roles/roles-core.csv").read_bytes(), b"synthetic")
        with self.assertRaises(HarnessFailure):
            guards.validate_assembly(historical)

    def test_assembly_rejects_changed_source_or_runtime_layout(self):
        assembly = (harness.ROOT / "assembly.xml").read_bytes()
        mutations = (
            (b"<outputDirectory>configuration/backend_configuration</outputDirectory>", b"", "output"),
            (b"<outputDirectory>configuration/backend_configuration", b"<outputDirectory>backend_configuration", "output"),
            (b"<includeBaseDirectory>false", b"<includeBaseDirectory>true", "output"),
            (b"${project.basedir}/configuration", b"${project.basedir}/docs", "directories"),
            (b"<include>**/*</include>", b"<include>roles/**/*</include>", "includes"),
        )
        for before, after, reason in mutations:
            with self.subTest(before=before), self.assertRaisesRegex(HarnessFailure, "unreviewed_assembly_" + reason):
                guards.validate_assembly(assembly.replace(before, after))

    def test_assembly_rejects_filters_moved_to_another_file_set(self):
        ns = {"a": "http://maven.apache.org/plugins/maven-assembly-plugin/assembly/1.1.3"}
        for kind in ("includes", "excludes"):
            with self.subTest(kind=kind):
                root = ET.fromstring((harness.ROOT / "assembly.xml").read_bytes())
                properties, metadata = root.findall("a:fileSets/a:fileSet", ns)
                filters = metadata.find("a:" + kind, ns)
                metadata.remove(filters)
                properties.append(filters)
                with self.assertRaisesRegex(HarnessFailure, "unreviewed_assembly_" + kind):
                    guards.validate_assembly(ET.tostring(root))

    def test_archive_rejects_traversal_links_duplicates_and_other_prefix(self):
        cases = [
            [("/config/file", b"x")], [("config/../outside", b"x")],
            [("config//file", b"x")], [("config\\outside", b"x")],
            [("elsewhere/file", b"x")], [("config/link", (tarfile.SYMTYPE,))],
            [("config/link", (tarfile.LNKTYPE,))], [("config/fifo", (tarfile.FIFOTYPE,))],
            [("config/file", b"x"), ("config/file", b"y")],
        ]
        for index, entries in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(HarnessFailure):
                guards.extract_archive(archive(entries), self.root / str(index), "config")

    def test_single_file_archive_does_not_accept_extra_or_link_members(self):
        self.assertEqual(guards.single_file_archive(archive([("startup.sh", b"x")]), "startup.sh"), b"x")
        for entries in ([("other", b"x")], [("startup.sh", (tarfile.SYMTYPE,))],
                        [("startup.sh", b"x"), ("extra", b"x")]):
            with self.subTest(entries=entries), self.assertRaises(HarnessFailure):
                guards.single_file_archive(archive(entries), "startup.sh")

    def make_configuration(self, name, files):
        directory = self.root / name
        directory.mkdir()
        for relative, content in files.items():
            target = directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return directory

    def test_overlay_removes_only_verified_old_owned_paths_and_preserves_remainder(self):
        image = self.make_configuration("image", {"old.csv": b"old", "shared/ref.csv": b"reference"})
        old = self.make_configuration("old", {"old.csv": b"old"})
        new = self.make_configuration("new", {"new.csv": b"candidate"})
        receipt = guards.assemble(image, old, new, self.root / "assembled")
        self.assertEqual(receipt, {"preserved_files": 1, "candidate_files": 1})
        self.assertEqual(set(guards.manifest(self.root / "assembled")), {"new.csv", "shared/ref.csv"})
        self.assertEqual((self.root / "assembled/shared/ref.csv").read_bytes(), b"reference")

    def test_overlay_rejects_unproven_ownership_or_unowned_collision(self):
        image = self.make_configuration("image", {"old.csv": b"old", "ref.csv": b"reference"})
        old = self.make_configuration("old", {"old.csv": b"wrong"})
        new = self.make_configuration("new", {"ref.csv": b"candidate"})
        with self.assertRaisesRegex(HarnessFailure, "image_content_manifest_does_not_match"):
            guards.assemble(image, old, new, self.root / "out-1")
        (old / "old.csv").write_bytes(b"old")
        with self.assertRaisesRegex(HarnessFailure, "replacement_collides_with_unowned"):
            guards.assemble(image, old, new, self.root / "out-2")
        (new / "ref.csv").write_bytes(b"reference")
        guards.assemble(image, old, new, self.root / "out-3")

    def test_manifest_rejects_symlinks(self):
        directory = self.make_configuration("config", {"a": b"a"})
        (directory / "link").symlink_to(directory / "a")
        with self.assertRaisesRegex(HarnessFailure, "configuration_symlink_forbidden"):
            guards.manifest(directory)

    def test_actual_assembly_and_csv_contracts_are_recognized(self):
        guards.validate_assembly((harness.ROOT / "assembly.xml").read_bytes())
        policy = guards.admission_privileges(harness.ROOT / guards.CONFIG_PREFIX, guards.CURRENT_ADMISSION_ADDITIONS)
        self.assertEqual(len(policy), 59)
        self.assertIn("Delete Relationships", policy)
        self.assertNotIn("Purge Relationships", policy)
        fixture = harness.ROOT / ".github/integration/admission-role-reconciliation/src/test/resources/admission-role-1.25.15.csv"
        historical = self.make_configuration("historical", {guards.ROLES_FILE: fixture.read_bytes()})
        baseline_policy = guards.admission_privileges(historical)
        self.assertEqual(len(baseline_policy), 58)
        self.assertEqual(policy, baseline_policy | {"app:home.libroAtenciones"})
        self.assertNotIn("app:home.libroAtenciones.editar", policy)
        changed = (harness.ROOT / "assembly.xml").read_bytes().replace(b"**/.gitkeep", b"**/extra")
        with self.assertRaisesRegex(HarnessFailure, "unreviewed_assembly_excludes"):
            guards.validate_assembly(changed)

    def test_numeric_image_user_and_real_effective_group_required(self):
        identity = b"1001\n17\n"
        self.assertEqual(guards.backend_owner("1001", identity), "1001:17")
        self.assertEqual(guards.backend_owner("1001", b"1001\n0\n"), "1001:0")
        self.assertEqual(guards.backend_owner("1001:0", b"1001\n0\n"), "1001:0")
        for user in ("", "0", "root", "1001:root", "1001;echo"):
            with self.subTest(user=user), self.assertRaises(HarnessFailure):
                guards.backend_owner(user, identity)
        for invalid in (b"", identity + identity, b"1001\ngroup\n", b"0\n0\n", b"1002\n17\n"):
            with self.subTest(invalid=invalid), self.assertRaises(HarnessFailure):
                guards.backend_owner("1001", invalid)
        with self.assertRaisesRegex(HarnessFailure, "backend_effective_identity_mismatch"):
            guards.backend_owner("1001:0", identity)

    def test_runtime_properties_reject_duplicate_overrides(self):
        self.assertEqual(guards.properties(b"# comment\ninitializer.startup.load=fail_on_error\n"),
                         {"initializer.startup.load": "fail_on_error"})
        with self.assertRaisesRegex(HarnessFailure, "duplicate_runtime_property"):
            guards.properties(b"a=true\na=false\n")

    def module(self, **updates):
        return {"uuid": "initializer", "version": guards.INITIALIZER_VERSION,
                "started": True, **updates}

    def test_module_state_uses_actual_uuid_and_boolean_not_health(self):
        self.runtime.request = Mock(return_value=(200, self.module()))
        self.assertIs(self.runtime.module_status("owned"), True)
        self.runtime.request.assert_called_once_with("owned", "GET", "/module/initializer?v=full")
        self.runtime.request.return_value = (200, self.module(started=False))
        self.assertIs(self.runtime.module_status("owned"), False)
        for code, body in ((200, []), (200, self.module(uuid="other")),
                           (200, self.module(version="other")), (200, self.module(started="false")),
                           (401, None), (403, None), (500, None)):
            with self.subTest(code=code, body=body), self.assertRaises(HarnessFailure):
                self.runtime.request.return_value = (code, body)
                self.runtime.module_status("owned")
        for code in (None, 302, 502, 503, 504):
            with self.subTest(code=code), self.assertRaisesRegex(HarnessFailure, "^module_state_unavailable$"):
                self.runtime.request.return_value = (code, None)
                self.runtime.module_status("owned")

    def setup_lifecycle(self, logs):
        self.runtime.remaining = Mock(return_value=30)
        self.runtime.owned = Mock(return_value={"State": {"Running": True}})
        self.runtime.docker = Mock(return_value=completed(stdout=logs.encode()))
        self.runtime.lifecycle_logs = Mock(return_value=(logs, None, None))
        self.runtime.effective_strict = Mock()
        self.runtime.bootstrap = Mock(return_value=None)
        self.runtime.installation_progress = Mock(return_value=(None, None, None, None))

    def test_bootstrap_http_precedes_lifecycle_and_real_module_checks(self):
        self.setup_lifecycle(harness.COMPLETION)
        events = []
        self.runtime.bootstrap = Mock(side_effect=lambda backend: events.append("bootstrap") or 200)
        self.runtime.lifecycle_logs.side_effect = lambda backend: events.append("logs") or (harness.COMPLETION, True, 44)
        self.runtime.module_status = Mock(side_effect=lambda backend: events.append("module") or True)
        with patch.object(harness, "emit"):
            self.runtime.wait_initializer("owned", "baseline")
        self.assertEqual(events, ["bootstrap", "logs", "module"])

    def test_bootstrap_request_is_anonymous_loopback_bounded_and_body_free(self):
        self.runtime.owned = Mock()
        self.runtime.docker = Mock(return_value=completed(stdout=b"302"))
        self.assertEqual(self.runtime.bootstrap("owned"), 302)
        self.runtime.owned.assert_called_once_with("container", "owned")
        call = self.runtime.docker.call_args
        self.assertEqual(call.args, ("exec", "-i", "owned", "curl", "--disable", "--config", "-"))
        config = call.kwargs["data"].decode()
        self.assertIn('url = "http://127.0.0.1:8080/openmrs/initialsetup"\n', config)
        self.assertIn('request = "GET"\n', config)
        self.assertIn('output = "/dev/null"\n', config)
        self.assertIn('proxy = ""\nnoproxy = "*"\n', config)
        self.assertIn("connect-timeout = 2\nmax-time = 5\n", config)
        self.assertIn("max-redirs = 0\nretry = 0\n", config)
        self.assertNotIn("Authorization", config)
        self.assertNotIn("user =", config)
        self.assertNotIn("location", config)
        self.assertNotIn("?", config)
        self.assertNotIn("auto_run_openmrs", config)
        self.assertEqual(call.kwargs["timeout"], 10)
        self.assertTrue(call.kwargs["allow_failure"])

    def test_bootstrap_reports_only_http_code_or_transport_unavailability(self):
        self.runtime.owned = Mock()
        self.runtime.docker = Mock(return_value=completed(28, b"000", b"synthetic-private-error"))
        self.assertIsNone(self.runtime.bootstrap("owned"))
        for output in (b"200", b"503"):
            with self.subTest(output=output):
                self.runtime.docker.return_value = completed(stdout=output)
                self.assertEqual(self.runtime.bootstrap("owned"), int(output))
        self.runtime.docker.return_value = completed(stdout=b"synthetic-private-body\n200")
        with self.assertRaisesRegex(HarnessFailure, "^invalid_bootstrap_http_code$"):
            self.runtime.bootstrap("owned")

    def test_installation_progress_extracts_only_typed_fields_from_fixed_internal_get(self):
        self.runtime.owned = Mock()
        self.runtime.docker = Mock()
        for has_errors, complete in ((False, False), (True, False), (False, True),
                                     ("false", True), (False, "true")):
            with self.subTest(has_errors=has_errors, complete=complete):
                body = {"hasErrors": has_errors, "initializationComplete": complete,
                        "message": "synthetic-private-message", "errorPage": "synthetic-private-page",
                        "logLines": ["synthetic-private-log"], "extra": "synthetic-private-value"}
                self.runtime.docker.return_value = completed(stdout=json.dumps(body).encode() + b"\n200")
                self.assertEqual(self.runtime.installation_progress("owned"), (
                    has_errors if isinstance(has_errors, bool) else None,
                    complete if isinstance(complete, bool) else None, None, None))
        call = self.runtime.docker.call_args
        self.assertEqual(call.args, ("exec", "-i", "owned", "curl", "--disable", "--config", "-"))
        config = call.kwargs["data"].decode()
        self.assertIn('url = "http://127.0.0.1:8080/openmrs/initialsetup?page=progress.vm.ajaxRequest"\n', config)
        self.assertIn('request = "GET"\n', config)
        self.assertIn('proxy = ""\nnoproxy = "*"\n', config)
        self.assertIn("max-time = 5\nmax-redirs = 0\nretry = 0\n", config)
        for forbidden in ("Authorization", "user =", "cookie", "location", "auto_run_openmrs"):
            self.assertNotIn(forbidden, config)
        self.assertEqual(call.kwargs["timeout"], 10)
        self.assertTrue(call.kwargs["allow_failure"])
        self.runtime.owned.assert_called_with("container", "owned")

    def test_installation_counters_preserve_zero_and_over_100_but_reject_invalid_values(self):
        self.runtime.owned = Mock()
        self.runtime.docker = Mock()
        for value, expected in ((0, 0), (12, 12), (200, 200), (-1, None),
                                (True, None), (False, None), (1.5, None),
                                ("12", None), (None, None), ([], None)):
            with self.subTest(value=value):
                body = {"hasErrors": False, "initializationComplete": False,
                        "actionCounter": value, "completedPercentage": value,
                        "message": "synthetic-private-message", "logLines": ["synthetic-private-log"],
                        "executingTask": "synthetic-private-task", "executedTasks": ["synthetic-private-task"]}
                self.runtime.docker.return_value = completed(stdout=json.dumps(body).encode() + b"\n200")
                result = self.runtime.installation_progress("owned")
                self.assertEqual(result, (False, False, expected, expected))
                self.assertNotIn("synthetic-private", json.dumps(result))

    def test_installation_progress_unavailable_or_malformed_is_never_healthy(self):
        self.runtime.owned = Mock()
        self.runtime.docker = Mock()
        for result in (completed(28, b"000", b"synthetic-private-error"),
                       completed(stdout=b"synthetic-private-html\n200"),
                       completed(stdout=b'[]\n200'), completed(stdout=b'{}\n200'),
                       completed(stdout=b'{"hasErrors":false,"initializationComplete":true}\n404'),
                       completed(stdout=b'{"hasErrors":false,"initializationComplete":true}\n503'),
                       completed(stdout=b"synthetic-private-undelimited-response")):
            with self.subTest(code=result.returncode):
                self.runtime.docker.return_value = result
                self.assertEqual(self.runtime.installation_progress("owned"), (None, None, None, None))

    def test_reported_installation_error_fails_without_lifecycle_success(self):
        self.setup_lifecycle("synthetic-private-log")
        self.runtime.installation_progress = Mock(return_value=(True, False, None, None))
        self.runtime.module_status = Mock(return_value=True)
        with patch.object(harness.time, "monotonic", side_effect=[0, 0, 0, 31]), \
                patch.object(harness.time, "sleep") as sleep, patch.object(harness, "emit") as emit:
            with self.assertRaisesRegex(HarnessFailure, "^installation_reported_errors$"):
                self.runtime.wait_initializer("owned", "baseline")
        self.runtime.module_status.assert_not_called()
        self.runtime.effective_strict.assert_not_called()
        sleep.assert_not_called()
        self.assertIs(emit.call_args.kwargs["installation_has_errors"], True)
        self.assertIs(emit.call_args.kwargs["installation_complete"], False)
        self.assertEqual(emit.call_args.args, ("baseline", "WAITING"))

    def test_bootstrap_200_never_completes_lifecycle_and_progress_is_sanitized_periodic(self):
        self.setup_lifecycle("synthetic-private-log")
        self.runtime.remaining.return_value = 65
        self.runtime.bootstrap = Mock(return_value=200)
        self.runtime.installation_progress = Mock(return_value=(False, True, 123, None))
        self.runtime.lifecycle_logs.return_value = ("synthetic-private-log", True, 20)
        self.runtime.module_status = Mock(return_value=True)
        clock = {"now": 0}
        def advance(seconds):
            clock["now"] += 30
        with patch.object(harness.time, "monotonic", side_effect=lambda: clock["now"]), \
                patch.object(harness.time, "sleep", side_effect=advance), patch.object(harness, "emit") as emit:
            with self.assertRaisesRegex(HarnessFailure, "initializer_lifecycle_not_proven"):
                self.runtime.wait_initializer("owned", "baseline")
        self.assertEqual(self.runtime.bootstrap.call_count, 3)
        self.assertEqual(self.runtime.installation_progress.call_count, 2)
        self.runtime.module_status.assert_not_called()
        self.runtime.effective_strict.assert_not_called()
        self.assertEqual(emit.call_count, 2)
        for call in emit.call_args_list:
            self.assertEqual(call.args, ("baseline", "WAITING"))
            self.assertEqual(call.kwargs, {
                "backend_running": True, "bootstrap_http_code": 200,
                "completion_seen": False, "abort_seen": False,
                "candidate_marker_seen": False, "csv_error_seen": False,
                "installation_has_errors": False, "installation_complete": True,
                "installation_action_counter": 123, "installation_completed_percentage": None,
                "initializer_log_present": True, "initializer_log_bytes": 20,
                "initializer_last_loading_domain": None,
                "initializer_last_completed_domain": None,
                "initializer_failure_hints": [],
            })

    def test_lifecycle_waits_for_real_module_after_completion_log(self):
        self.setup_lifecycle(harness.COMPLETION)
        self.runtime.request = Mock(side_effect=[(302, None), (200, self.module())])
        with patch.object(harness.time, "sleep"), patch.object(harness, "emit") as emit:
            self.runtime.wait_initializer("new-container", "upgrade")
        self.assertEqual(self.runtime.request.call_count, 2)
        self.runtime.lifecycle_logs.assert_called_with("new-container")
        emit.assert_any_call("upgrade", "PASSED", initializer_started=True)
        self.assertEqual(sum(call.args[1] == "PASSED" for call in emit.call_args_list), 1)

    def test_persistent_module_redirect_never_proves_startup(self):
        self.setup_lifecycle(harness.COMPLETION)
        self.runtime.request = Mock(return_value=(302, None))
        with patch.object(harness.time, "monotonic", side_effect=[0, 0, 1, 31]), \
                patch.object(harness.time, "sleep"), patch.object(harness, "emit") as emit:
            with self.assertRaisesRegex(HarnessFailure, "^initializer_lifecycle_not_proven_before_timeout$"):
                self.runtime.wait_initializer("new-container", "fresh_candidate")
        self.assertFalse(any(call.args[1] == "PASSED" for call in emit.call_args_list))

    def test_lifecycle_reads_unique_attempt_file_when_completion_is_absent_from_console(self):
        filename = "admission-initializer-" + "a" * 32 + "-retry.log"
        self.runtime.lifecycle_files = {"owned": filename}
        self.runtime.owned = Mock()
        self.runtime.docker = Mock(side_effect=[completed(stdout=b"startup"), completed(stdout=harness.COMPLETION.encode())])
        logs, present, size = self.runtime.lifecycle_logs("owned")
        self.assertIn(harness.COMPLETION, logs)
        self.assertIs(present, True)
        self.assertEqual(size, len(harness.COMPLETION.encode()))
        call = self.runtime.docker.call_args
        self.assertEqual(call.args[-1], "/openmrs/data/" + filename)
        self.assertNotIn("/openmrs/data/initializer.log", call.args)
        self.assertIn('test ! -L "$1"', call.args[4])

    def test_missing_attempt_file_is_pending_but_unreadable_file_is_a_failure(self):
        self.runtime.lifecycle_files = {"owned": "admission-initializer-" + "a" * 32 + "-baseline.log"}
        self.runtime.owned = Mock()
        self.runtime.docker = Mock(side_effect=[completed(stdout=b"startup"), completed(44)])
        self.assertEqual(self.runtime.lifecycle_logs("owned"), ("startup", False, None))
        self.runtime.docker.side_effect = [completed(stdout=b"startup"), completed()]
        self.assertEqual(self.runtime.lifecycle_logs("owned"), ("startup", True, 0))
        self.runtime.docker.side_effect = [completed(), completed(1, stderr=b"synthetic-private-path")]
        with self.assertRaisesRegex(HarnessFailure, "^initializer_log_unreadable$"):
            self.runtime.lifecycle_logs("owned")
        self.runtime.lifecycle_files["owned"] = "initializer.log"
        self.runtime.docker.reset_mock()
        with self.assertRaisesRegex(HarnessFailure, "^invalid_initializer_log_path$"):
            self.runtime.lifecycle_logs("owned")
        self.runtime.docker.assert_not_called()

    def test_rejection_requires_current_abort_and_initializer_classloader_disposal(self):
        aborted = harness.ABORT + guards.CHANGESET
        stopped = "Disposing of ModuleClassLoader: {ModuleClassLoader: uid=123; initializer}"
        self.setup_lifecycle(aborted)
        self.runtime.lifecycle_logs.side_effect = [(aborted, True, 40), (aborted + stopped, True, 40)]
        self.runtime.module_status = Mock(side_effect=HarnessFailure("module_state_unavailable"))
        with patch.object(harness.time, "sleep"), patch.object(harness, "emit") as emit:
            self.runtime.wait_initializer("new-container", "reject", reject=True)
        self.assertEqual(self.runtime.lifecycle_logs.call_count, 2)
        self.runtime.lifecycle_logs.assert_called_with("new-container")
        self.runtime.module_status.assert_not_called()
        emit.assert_any_call("reject", "PASSED", initializer_started=False)
        self.assertEqual(sum(call.args[1] == "PASSED" for call in emit.call_args_list), 1)

    def test_rejection_never_accepts_missing_abort_or_another_modules_disposal(self):
        aborted = harness.ABORT + guards.CHANGESET
        stopped = "Disposing of ModuleClassLoader: {ModuleClassLoader: uid=123; initializer}"
        for logs in (stopped, aborted, aborted + stopped.replace("initializer}", "webservices.rest}"),
                     aborted + stopped.replace("initializer}", "initializer-other}"),
                     aborted + stopped.replace("uid=123", "uid=invalid")):
            with self.subTest(logs=logs):
                self.setup_lifecycle(logs)
                self.runtime.module_status = Mock(return_value=False)
                with patch.object(harness.time, "sleep"), patch.object(harness, "emit"), \
                        patch.object(harness.time, "monotonic", side_effect=[0, 0, 0, 31]):
                    with self.assertRaisesRegex(HarnessFailure, "initializer_lifecycle_not_proven"):
                        self.runtime.wait_initializer("new-container", "reject", reject=True)
                self.runtime.module_status.assert_not_called()

    def assert_unexpected_loader_abort(self, logs, reject):
        self.setup_lifecycle(logs)
        self.runtime.module_status = Mock(return_value=False if reject else True)
        with patch.object(harness.time, "monotonic", side_effect=[0, 0, 0, 31]), \
                patch.object(harness.time, "sleep") as sleep, patch.object(harness, "emit") as emit:
            with self.assertRaisesRegex(HarnessFailure, "^unexpected_initializer_abort$"):
                self.runtime.wait_initializer("owned", "reject" if reject else "baseline", reject=reject)
        self.runtime.module_status.assert_not_called()
        self.runtime.effective_strict.assert_not_called()
        sleep.assert_not_called()
        self.assertEqual(emit.call_count, 1)
        self.assertEqual(emit.call_args.args[1], "WAITING")
        diagnostic = emit.call_args.kwargs
        self.assertIsNone(diagnostic["initializer_last_loading_domain"])
        self.assertIsNone(diagnostic["initializer_last_completed_domain"])
        self.assertEqual(diagnostic["initializer_failure_hints"], [])
        self.assertTrue(all(isinstance(value, bool) or value is None
                            for name, value in diagnostic.items() if name != "initializer_failure_hints"))
        self.assertNotIn("synthetic-private", json.dumps(emit.call_args.kwargs))
        return emit.call_args.kwargs

    def test_other_domain_and_preloading_abort_fail_without_waiting_for_timeout(self):
        for phase, domain in (("loading", "roles"), ("loading", "ocl"),
                              ("pre-loading", "liquibase"), ("pre-loading", "synthetic-private-domain")):
            signal = f"The {phase} of the '{domain}' configuration file was aborted:"
            for reject in (False, True):
                with self.subTest(phase=phase, domain=domain, reject=reject):
                    diagnostic = self.assert_unexpected_loader_abort(signal + "\nsynthetic-private-path", reject)
                    self.assertIs(diagnostic["abort_seen"], True)

    def test_expected_liquibase_rejection_never_masks_another_abort_or_csv_error(self):
        expected = harness.ABORT + "\n" + guards.CHANGESET
        for other in ("The loading of the 'ocl' configuration file was aborted:",
                      "The pre-loading of the 'liquibase' configuration file was aborted:",
                      "BEGINNING OF CSV FILE ERROR SUMMARY"):
            for logs in (expected + "\n" + other, other + "\n" + expected):
                with self.subTest(other=other, expected_first=logs.startswith(expected)):
                    diagnostic = self.assert_unexpected_loader_abort(logs, reject=True)
                    self.assertIs(diagnostic["abort_seen"], True)
                    self.assertIs(diagnostic["candidate_marker_seen"], True)

    def test_liquibase_abort_without_candidate_marker_is_not_expected_rejection(self):
        diagnostic = self.assert_unexpected_loader_abort(harness.ABORT, reject=True)
        self.assertIs(diagnostic["abort_seen"], True)
        self.assertIs(diagnostic["candidate_marker_seen"], False)

    def test_rejection_never_accepts_later_completion_or_unavailable_module(self):
        stopped = "Disposing of ModuleClassLoader: {ModuleClassLoader: uid=123; initializer}"
        self.setup_lifecycle(harness.ABORT + guards.CHANGESET + stopped + harness.COMPLETION)
        self.runtime.module_status = Mock(return_value=False)
        with patch.object(harness, "emit"), self.assertRaisesRegex(HarnessFailure, "initializer_continued_after_rejection"):
            self.runtime.wait_initializer("new-container", "reject", reject=True)
        self.runtime.module_status.assert_not_called()
        self.setup_lifecycle(harness.ABORT + guards.CHANGESET)
        self.runtime.module_status = Mock(side_effect=HarnessFailure("module_state_unavailable"))
        with patch.object(harness.time, "sleep"), patch.object(harness.time, "monotonic", side_effect=[0, 0, 0, 31]), \
                patch.object(harness, "emit"):
            with self.assertRaisesRegex(HarnessFailure, "initializer_lifecycle_not_proven"):
                self.runtime.wait_initializer("new-container", "reject", reject=True)

    def test_checksum_absence_requires_test_exit_one_not_arbitrary_failure(self):
        self.runtime.docker = Mock(return_value=completed(1))
        self.runtime.absent_checksum("owned", guards.LIQUIBASE_CHECKSUM)
        for code in (0, 2, 125):
            with self.subTest(code=code), self.assertRaisesRegex(HarnessFailure, "unexpected_checksum_file"):
                self.runtime.docker.return_value = completed(code)
                self.runtime.absent_checksum("owned", guards.LIQUIBASE_CHECKSUM)

    def test_history_snapshot_keeps_all_columns_not_partial_projection(self):
        self.runtime.query = Mock(return_value=["synthetic-full-row"])
        self.assertEqual(self.runtime.history("owned-db"), ["synthetic-full-row"])
        self.runtime.query.assert_called_once_with(
            "owned-db", "SELECT * FROM liquibasechangelog ORDER BY ID,AUTHOR,FILENAME")

    def test_upgrade_oracle_preserves_unrelated_multiplicity_and_audit_columns(self):
        columns = {
            "role": ["role", "description", "uuid"],
            "role_privilege": ["role", "privilege"],
            "user_role": ["user_id", "role"],
            "role_role": ["parent_role", "child_role"],
            "patientflags_tag_role": ["tag_id", "role"],
            "stockmgmt_user_role_scope": ["user_role_scope_id", "role", "uuid", "date_changed"],
        }
        self.runtime.query = Mock(side_effect=lambda db, sql: columns[sql.removeprefix("SHOW COLUMNS FROM ")])
        self.runtime.privileges = {"Approved", "Delete Relationships"}
        before = {
            "role": ["Admision\tkept-description\told", "SIHSALUS Admision\tlegacy\tcanonical", "Other\tkept\tother"],
            "role_privilege": ["Admision\tApproved", "SIHSALUS Admision\tApproved", "Other\tUnchanged"],
            "user_role": ["1\tSIHSALUS Admision", "2\tAdmision", "2\tSIHSALUS Admision", "3\tOther"],
            "role_role": ["Other\tAnother"],
            "patientflags_tag_role": [
                "1\tAdmision", "1\tAdmision", "1\tSIHSALUS Admision",
                "2\tSIHSALUS Admision", "2\tSIHSALUS Admision", "3\tOther", "3\tOther"],
            "stockmgmt_user_role_scope": ["7\tSIHSALUS Admision\tfixed-uuid\t2026-01-01", "8\tOther\tother-uuid\tNULL"],
        }
        # The operational upgrade has both the historical alias and its later
        # supplement. Retirement removes only the latter's reviewed rows.
        before["role"].append("SIHSALUS Admision Hospitalaria\tsupplement\tfixed-supplement")
        before["role_privilege"].append("SIHSALUS Admision Hospitalaria\tDelete Visits")
        before["user_role"].extend(["1\tSIHSALUS Admision Hospitalaria", "2\tSIHSALUS Admision Hospitalaria"])
        expected = self.runtime.expected_upgrade_state("owned-db", before)
        self.assertEqual(expected["role"], sorted(["Admision\tkept-description\t" + CANONICAL_UUID, "Other\tkept\tother"]))
        self.assertEqual(expected["role_privilege"], ["Admision\tApproved", "Admision\tDelete Relationships", "Other\tUnchanged"])
        self.assertEqual(expected["user_role"], ["1\tAdmision", "2\tAdmision", "3\tOther"])
        self.assertEqual(expected["role_role"], before["role_role"])
        self.assertEqual(expected["patientflags_tag_role"],
                         ["1\tAdmision", "1\tAdmision", "2\tAdmision", "3\tOther", "3\tOther"])
        self.assertEqual(expected["stockmgmt_user_role_scope"],
                         ["7\tAdmision\tfixed-uuid\t2026-01-01", "8\tOther\tother-uuid\tNULL"])
        self.assertEqual(before["stockmgmt_user_role_scope"][0].split("\t")[1], LEGACY_ROLE)

    def test_state_comparison_preserves_multiplicity_without_logging_rows(self):
        before = {"role_privilege": ["synthetic-private-grant"],
                  "patientflags_tag_role": ["synthetic-private-tag"] * 2}
        self.runtime.state = Mock(return_value={
            "role_privilege": ["synthetic-private-grant", "synthetic-private-extra"],
            "patientflags_tag_role": ["synthetic-private-tag"],
        })
        with patch.object(harness, "emit") as emit, self.assertRaisesRegex(HarnessFailure, "^unexpected_rbac$"):
            self.runtime.assert_state("owned-db", before, "unexpected_rbac")
        self.assertEqual(emit.call_count, 2)
        emit.assert_any_call("rbac_snapshot", "FAILED", table="role_privilege",
                             expected_present=True, actual_present=True, removed_rows=0, added_rows=1)
        emit.assert_any_call("rbac_snapshot", "FAILED", table="patientflags_tag_role",
                             expected_present=True, actual_present=True, removed_rows=1, added_rows=0)
        self.assertNotIn("synthetic-private", str(emit.call_args_list))

    def test_hospital_role_upgrade_preserves_local_uuid_and_every_external_reference(self):
        self.runtime.hospital_roles = [{"Role name": "SIHSALUS Soporte", "Uuid": "canonical",
            "Description": "Reviewed support", "Inherited roles": "", "Privileges": "Get Patients;Manage Roles"}]
        self.runtime.query = Mock(side_effect=[["role", "description", "uuid"], ["role", "privilege"]])
        before = {"role": ["SIHSALUS Soporte\tOld\tlocal", "Other\tKeep\tother"],
            "role_privilege": ["SIHSALUS Soporte\tUnapproved", "Other\tKeep"],
            "role_role": ["Other\tSIHSALUS Soporte", "SIHSALUS Soporte\tChild"],
            "user_role": ["42\tSIHSALUS Soporte"], "patientflags_tag_role": ["1\tOther"] * 2,
            "stockmgmt_user_role_scope": ["7\tSIHSALUS Soporte\tuuid\t2026-01-01"]}
        actual = self.runtime.expected_hospital_role_state("owned", before)
        self.assertEqual(actual["role"], ["Other\tKeep\tother", "SIHSALUS Soporte\tReviewed support\tlocal"])
        self.assertEqual(actual["role_privilege"], ["Other\tKeep", "SIHSALUS Soporte\tGet Patients", "SIHSALUS Soporte\tManage Roles"])
        self.assertEqual(actual["role_role"], ["SIHSALUS Soporte\tChild"])
        for table in ("user_role", "patientflags_tag_role", "stockmgmt_user_role_scope"):
            self.assertEqual(actual[table], before[table])
        self.assertIn("SIHSALUS Soporte\tOld\tlocal", before["role"])

    def test_hospital_role_upgrade_rejects_canonical_uuid_owned_by_another_name(self):
        self.runtime.hospital_roles = [{"Role name": "SIHSALUS Soporte", "Uuid": "canonical",
            "Description": "Reviewed", "Inherited roles": "", "Privileges": "Get Patients"}]
        self.runtime.query = Mock(side_effect=[["role", "description", "uuid"], ["role", "privilege"]])
        with self.assertRaisesRegex(HarnessFailure, "hospital_role_uuid_collision"):
            self.runtime.expected_hospital_role_state("owned", {"role": ["Other\tKeep\tcanonical"],
                "role_privilege": [], "role_role": [], "user_role": []})

    def test_canonical_laboratory_delta_is_applied_only_with_current_roles_csv(self):
        self.runtime.hospital_roles = []
        laboratory = [{"Role name": "Laboratorio", "Uuid": "lab",
            "Description": "Laboratory", "Inherited roles": "", "Privileges": "Add Observations;Get Patient Programs"}]
        self.runtime.query = Mock(side_effect=[["role", "description", "uuid"], ["role", "privilege"]])
        before = {"role": ["Laboratorio\tLaboratory\tlab", "Other\tKeep\tother"],
            "role_privilege": ["Laboratorio\tAdd Observations", "Other\tKeep"],
            "role_role": [], "user_role": ["42\tLaboratorio"]}
        historical = self.runtime.expected_hospital_role_state("owned", before)
        self.assertEqual(historical, before)
        self.runtime.query.assert_not_called()
        current = self.runtime.expected_hospital_role_state("owned", before, laboratory)
        self.assertEqual(current["role_privilege"],
                         ["Laboratorio\tAdd Observations", "Laboratorio\tGet Patient Programs", "Other\tKeep"])
        for table in ("role", "role_role", "user_role"):
            self.assertEqual(current[table], before[table])
        self.assertNotIn("Laboratorio\tGet Patient Programs", before["role_privilege"])

    def test_emrapi_refresh_adds_only_declared_compatibility_and_then_is_stable(self):
        self.runtime.hospital_compatibility = {"app:home.editar"}
        before = {"role_privilege": ["Other\tKeep", "Privilege Level: Full\tapp:home.editar"],
                  "user_role": ["42\tOther"], "patientflags_tag_role": ["1\tOther"] * 2}
        expected = self.runtime.expected_emrapi_refresh(before)
        self.assertEqual(expected["role_privilege"], ["Other\tKeep",
            "Privilege Level: Full\tapp:home.editar", "Privilege Level: High\tapp:home.editar"])
        self.assertEqual(expected["user_role"], before["user_role"])
        self.assertEqual(expected["patientflags_tag_role"], before["patientflags_tag_role"])
        self.assertEqual(self.runtime.expected_emrapi_refresh(expected), expected)
        self.assertEqual(len(before["role_privilege"]), 2)

    def test_state_comparison_distinguishes_missing_tables_and_ignores_row_order(self):
        self.runtime.state = Mock(return_value={"role": ["b", "a"]})
        with patch.object(harness, "emit") as emit:
            self.runtime.assert_state("owned-db", {"role": ["a", "b"]}, "unexpected_rbac")
            emit.assert_not_called()
            with self.assertRaisesRegex(HarnessFailure, "^unexpected_rbac$"):
                self.runtime.assert_state("owned-db", {"role": ["a", "b"], "user_role": []}, "unexpected_rbac")
        emit.assert_called_once_with("rbac_snapshot", "FAILED", table="user_role",
                                     expected_present=True, actual_present=False, removed_rows=0, added_rows=0)

    def test_clinical_drug_search_and_restart_require_the_same_persisted_entities(self):
        rows, response = clinical_drug_result()
        self.runtime.query = Mock(side_effect=rows * 2)
        self.runtime.request = Mock(return_value=(200, response))
        with patch.object(harness, "emit") as emit:
            previous = self.runtime.check_clinical_drug("owned", "db", "upgrade")
            self.assertEqual(self.runtime.check_clinical_drug("owned", "db", "idempotence", previous), previous)
        self.assertTrue(previous[0][0].startswith("310\t"))
        self.assertTrue(previous[1][0].startswith("410\t"))
        self.runtime.request.assert_called_with("owned", "GET",
            "/drug?q=URSODESOX&v=custom:(uuid,display,name,strength,dosageForm:(display,uuid),concept:(display,uuid))")
        emit.assert_any_call("clinical_drug", "PASSED", phase="idempotence", concepts=1,
                             presentations=1, search_http=200, restart_checked=True)
        self.assertNotIn("synthetic-private-display", str(emit.call_args_list))
        self.assertNotIn("URSODESOX", str(emit.call_args_list))
        for table in (0, 2):
            with self.subTest(recreated_table=table), patch.object(harness, "emit") as emit:
                changed, response = clinical_drug_result()
                changed[table][0] = "999" + changed[table][0][changed[table][0].index("\t"):]
                self.runtime.query = Mock(side_effect=changed)
                with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_changed_on_restart$"):
                    self.runtime.check_clinical_drug("owned", "db", "idempotence", previous)
                emit.assert_not_called()

    def test_database_queries_preserve_accented_catalog_names(self):
        statement = "SELECT 'ÁCIDO URSODESOXICÓLICO'"
        self.runtime.owned = Mock()
        self.runtime.docker = Mock(return_value=completed(stdout="ÁCIDO URSODESOXICÓLICO\n".encode()))
        self.assertEqual(self.runtime.query("owned-db", statement), ["ÁCIDO URSODESOXICÓLICO"])
        self.runtime.owned.assert_called_once_with("container", "owned-db")
        call = self.runtime.docker.call_args
        self.assertIn("--default-character-set=utf8mb4", call.args)
        self.assertEqual(call.kwargs["data"], statement.encode("utf-8"))

    def test_ocl_refresh_checks_active_concepts_and_preserves_all_catalog_identities_on_restart(self):
        self.runtime.query = Mock(side_effect=ocl_refresh_result() * 2)
        with patch.object(harness, "emit") as emit:
            previous = self.runtime.check_ocl_refresh("db", "upgrade")
            self.assertEqual(self.runtime.check_ocl_refresh("db", "idempotence", previous), previous)
        self.assertTrue(all(call.args[1].startswith("SELECT ") for call in self.runtime.query.call_args_list))
        emit.assert_any_call("ocl_refresh", "PASSED", phase="idempotence", concepts=2,
                             neighborhood_sets=1, neighborhood_members=10, restart_checked=True)
        self.assertNotIn("Cuatro cruces", str(emit.call_args_list))
        self.assertNotIn("3fb84698", str(emit.call_args_list))
        for table, column, changed in ((0, 0, "999"), (1, 0, "999"), (2, 0, "999"),
                                      (3, 0, "999"), (3, 2, "999"),
                                      (3, 1, "30000000-0000-4000-8000-000000000000"),
                                      (3, 3, "30000000-0000-4000-8000-000000000000")):
            with self.subTest(table=table, column=column), patch.object(harness, "emit") as emit:
                rows = ocl_refresh_result()
                fields = rows[table][0].split("\t")
                fields[column] = changed
                rows[table][0] = "\t".join(fields)
                self.runtime.query = Mock(side_effect=rows)
                with self.assertRaisesRegex(HarnessFailure, "^ocl_refresh_changed_on_restart$"):
                    self.runtime.check_ocl_refresh("db", "idempotence", previous)
                emit.assert_not_called()

    def test_ocl_refresh_rejects_missing_or_duplicate_concepts_set_and_members(self):
        for table in range(4):
            for count in (0, 2):
                with self.subTest(table=table, count=count), patch.object(harness, "emit") as emit:
                    rows = ocl_refresh_result()
                    rows[table] *= count
                    self.runtime.query = Mock(side_effect=rows)
                    with self.assertRaisesRegex(HarnessFailure, "^ocl_refresh_"):
                        self.runtime.check_ocl_refresh("db", "fresh")
                    emit.assert_not_called()
        rows = ocl_refresh_result()
        rows[3][1] = rows[3][0]
        self.runtime.query = Mock(side_effect=rows)
        with self.assertRaisesRegex(HarnessFailure, "^ocl_refresh_neighborhood_members_invalid$"):
            self.runtime.check_ocl_refresh("db", "fresh")

    def test_ocl_refresh_rejects_retired_records_wrong_types_and_missing_spanish_names(self):
        cases = [(table, column, value) for table in (0, 1)
                 for column, value in ((1, "wrong-uuid"), (2, "1"), (3, "Test"),
                                       (4, "Coded"), (5, "NULL"))]
        cases.extend([(2, 1, "wrong-uuid"), (2, 2, "1"), (2, 3, "0"), (3, 4, "1")])
        for table, column, invalid in cases:
            with self.subTest(table=table, column=column), patch.object(harness, "emit") as emit:
                rows = ocl_refresh_result()
                fields = rows[table][0].split("\t")
                fields[column] = invalid
                rows[table][0] = "\t".join(fields)
                self.runtime.query = Mock(side_effect=rows)
                with self.assertRaisesRegex(HarnessFailure, "^ocl_refresh_.*invalid$"):
                    self.runtime.check_ocl_refresh("db", "fresh")
                emit.assert_not_called()

    def test_clinical_drug_rejects_missing_duplicate_retired_or_incorrect_metadata(self):
        cases = [(0, 1, "wrong-uuid"), (0, 2, "1"), (0, 3, "Test"), (0, 4, "Text"),
                 (2, 1, "wrong-uuid"), (2, 2, "Free text"), (2, 3, "1"), (2, 4, "500 mg"),
                 (2, 5, "wrong-concept"), (2, 6, "wrong-form"), (2, 7, "1"), (2, 8, "0")]
        for table, column, invalid in cases:
            with self.subTest(table=table, column=column):
                rows, _ = clinical_drug_result()
                fields = rows[table][0].split("\t")
                fields[column] = invalid
                rows[table][0] = "\t".join(fields)
                self.runtime.query = Mock(side_effect=rows)
                with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_(concept|presentation)_invalid$"):
                    self.runtime.check_clinical_drug("owned", "db", "fresh")
        for table in (0, 2):
            for count in (0, 2):
                with self.subTest(table=table, count=count):
                    rows, _ = clinical_drug_result()
                    rows[table] *= count
                    self.runtime.query = Mock(side_effect=rows)
                    with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_.*missing_or_duplicated$"):
                        self.runtime.check_clinical_drug("owned", "db", "fresh")
        rows, _ = clinical_drug_result()
        rows[1] = ["en\tUrsodeoxycholic acid"]
        self.runtime.query = Mock(side_effect=rows)
        with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_concept_names_invalid$"):
            self.runtime.check_clinical_drug("owned", "db", "fresh")

    def test_clinical_drug_search_rejects_free_text_missing_and_malformed_results(self):
        _, duplicate = clinical_drug_result()
        duplicate["results"] *= 2
        invalid_bodies = [None, {}, {"results": None}, {"results": [None]}, {"results": []},
                          {"results": [{"display": "Free text"}]}, duplicate]
        for body in invalid_bodies:
            with self.subTest(body=body):
                rows, _ = clinical_drug_result()
                self.runtime.query = Mock(side_effect=rows)
                self.runtime.request = Mock(return_value=(200, body))
                with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_search_"):
                    self.runtime.check_clinical_drug("owned", "db", "fresh")
        for field, invalid in (("name", "wrong"), ("strength", "500 mg"), ("display", " "),
                               ("concept", None), ("dosageForm", {"uuid": "wrong", "display": "Tablet"})):
            with self.subTest(field=field):
                rows, body = clinical_drug_result()
                body["results"][0][field] = invalid
                self.runtime.query = Mock(side_effect=rows)
                self.runtime.request = Mock(return_value=(200, body))
                with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_search_entry_invalid$"):
                    self.runtime.check_clinical_drug("owned", "db", "fresh")
        rows, body = clinical_drug_result()
        self.runtime.query = Mock(side_effect=rows)
        self.runtime.request = Mock(return_value=(403, body))
        with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_search_invalid$"):
            self.runtime.check_clinical_drug("owned", "db", "fresh")

    def test_internal_requests_never_follow_redirects_retry_or_pass_auth_in_argv(self):
        self.runtime.owned = Mock()
        self.runtime.admin_password = "synthetic-generated-only"
        self.runtime.docker = Mock(return_value=completed(stdout=b'{"authenticated":true}\n200'))
        self.assertEqual(self.runtime.request("owned", "GET", "/session"), (200, {"authenticated": True}))
        call = self.runtime.docker.call_args
        self.assertEqual(call.args, ("exec", "-i", "owned", "curl", "--config", "-"))
        configuration = call.kwargs["data"].decode()
        self.assertIn('url = "http://127.0.0.1:8080/openmrs/ws/rest/v1/session"', configuration)
        self.assertIn("max-redirs = 0\nretry = 0\n", configuration)
        self.assertNotIn("location", configuration)
        self.runtime.owned.assert_called_once_with("container", "owned")
        for resource in ('/session"\nurl="https://invalid"', "/session\\unsafe"):
            with self.subTest(resource=resource), self.assertRaises(HarnessFailure):
                self.runtime.request("owned", "GET", resource)

    def test_fresh_active_relationship_required_before_permission_deletes(self):
        identifier = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        self.runtime.nonce = "synthetic"
        self.runtime.fixtures = [{"person": identifier}, {"person": identifier}]
        self.runtime.request = Mock(side_effect=[
            (200, {"results": []}), (201, {"uuid": identifier}), (201, {"uuid": identifier})])
        self.runtime.query = Mock(side_effect=[["synthetic-row"], ["1"]])
        with self.assertRaisesRegex(HarnessFailure, "synthetic_relationship_not_active"):
            self.runtime.rbac("owned", "owned-db")
        self.assertEqual(self.runtime.request.call_count, 3)

    def test_repeated_rbac_creates_distinct_active_relationships(self):
        self.runtime.nonce = "synthetic"
        self.runtime.fixtures = [{"person": "synthetic-a"}, {"person": "synthetic-b"}]
        types, relationships, deletes = {}, {}, []

        def request(backend, method, path, data=None, restricted=False):
            if method == "GET":
                self.assertTrue(restricted)
                return 200, {"results": []}
            if path == "/relationshiptype":
                names = data["aIsToB"], data["bIsToA"]
                if names in types:
                    return 400, {}
                identifier = f"00000000-0000-4000-8000-{len(types) + 1:012d}"
                types[names] = identifier
                return 201, {"uuid": identifier}
            if path == "/relationship":
                self.assertIn(data["relationshipType"], types.values())
                identifier = f"00000000-0000-4000-8001-{len(relationships) + 1:012d}"
                relationships[identifier] = "0"
                return 201, {"uuid": identifier}
            self.assertEqual(method, "DELETE")
            self.assertTrue(restricted)
            identifier, query = path.removeprefix("/relationship/").split("?")
            self.assertEqual(relationships[identifier], "0")
            deletes.append((identifier, query))
            if query == "purge=true":
                return 403, {}
            self.assertEqual(query, "reason=synthetic-ci")
            relationships[identifier] = "1"
            return 204, None

        def query(db, sql):
            select, literal = sql.split(" WHERE uuid=")
            identifier = next(value for value in relationships if guards.sql_string(value) == literal)
            voided = relationships[identifier]
            if select == "SELECT voided FROM relationship":
                return [voided]
            self.assertEqual(select, "SELECT * FROM relationship")
            return [identifier + "\t" + voided]

        self.runtime.request, self.runtime.query = request, query
        with patch.object(harness, "emit"):
            self.runtime.rbac("historical-policy", "owned-db")
            self.runtime.rbac("current-policy", "owned-db")
        self.assertEqual(len(types), 2)
        self.assertEqual(list(relationships.values()), ["1", "1"])
        self.assertEqual(deletes, [
            (identifier, action) for identifier in relationships
            for action in ("purge=true", "reason=synthetic-ci")
        ])

    def test_wrong_owner_prevents_container_deletion(self):
        self.runtime.prefix, self.runtime.nonce = "owned", "nonce"
        self.runtime.inspect = Mock(return_value={"Config": {"Labels": {guards.OWNER_LABEL: "another"}}})
        self.runtime.docker = Mock()
        with self.assertRaisesRegex(HarnessFailure, "resource_ownership_mismatch"):
            self.runtime.remove_container("owned-container")
        self.runtime.docker.assert_not_called()
        with self.assertRaisesRegex(HarnessFailure, "resource_name_not_owned"):
            self.runtime.remove_container("another-container")

    def test_volume_creation_intent_survives_uncertain_docker_failure(self):
        self.runtime.prefix, self.runtime.nonce = "owned", "nonce"
        self.runtime.volumes = []
        def interrupted(*args):
            self.assertEqual(self.runtime.volumes, ["owned-data"])
            raise HarnessFailure("docker_volume_timeout")
        self.runtime.docker = Mock(side_effect=interrupted)
        with self.assertRaisesRegex(HarnessFailure, "docker_volume_timeout"):
            self.runtime.volume("data")
        self.assertEqual(self.runtime.volumes, ["owned-data"])

    def test_container_creation_intent_survives_uncertain_docker_failure(self):
        self.runtime.prefix, self.runtime.nonce = "owned", "nonce"
        self.runtime.containers = []
        def interrupted(*args):
            self.assertEqual(self.runtime.containers, ["owned-backend"])
            raise HarnessFailure("docker_create_timeout")
        self.runtime.docker = Mock(side_effect=interrupted)
        with self.assertRaisesRegex(HarnessFailure, "docker_create_timeout"):
            self.runtime.container("backend", [], guards.BACKEND)
        self.assertEqual(self.runtime.containers, ["owned-backend"])

    def test_cleanup_budget_stops_commands_without_unbounded_resource_waits(self):
        self.runtime.cleanup_deadline = 180
        self.runtime.docker_config, self.runtime.env = self.root, {}
        with patch.object(harness.time, "monotonic", return_value=179), patch.object(harness, "checked") as checked:
            self.runtime.docker("volume", "rm", "owned", timeout=60)
        self.assertEqual(checked.call_args.kwargs["timeout"], 1)
        with patch.object(harness.time, "monotonic", return_value=180), patch.object(harness, "checked") as checked:
            with self.assertRaisesRegex(HarnessFailure, "cleanup_time_budget_exhausted"):
                self.runtime.docker("volume", "rm", "owned")
        checked.assert_not_called()


class LoaderDiagnostics(unittest.TestCase):
    def test_reports_loader_phase_without_paths_names_or_raw_errors(self):
        logs = (
            "Loading file /openmrs/data/configuration/roles/private-role.csv\n"
            "The 'roles' configuration file has finished loading:\n/private/secret-path\n"
            "Loading file /openmrs/data/configuration/ocl/private-bundle.json\n"
            "java.net.SocketTimeoutException: private-credential-or-patient-value\n"
        )
        self.assertEqual(harness.loader_progress(logs), {
            "initializer_last_loading_domain": "ocl",
            "initializer_last_completed_domain": "roles",
            "initializer_failure_hints": ["connection_timeout"],
        })

    def test_unknown_domains_and_exception_names_are_never_copied_to_output(self):
        logs = (
            "Loading file /openmrs/data/configuration/roles/known.csv\n"
            "Loading file /openmrs/data/configuration/privatevalue/private-name.csv\n"
            "The 'privatevalue' configuration file has finished loading:\n"
            "private.package.PrivateException: confidential\n"
        )
        self.assertEqual(harness.loader_progress(logs), {
            "initializer_last_loading_domain": None,
            "initializer_last_completed_domain": None,
            "initializer_failure_hints": [],
        })

    def test_failure_hints_are_bounded_and_do_not_repeat_raw_matches(self):
        logs = "java.lang.OutOfMemoryError: private\n" * 100
        logs += "Lock wait timeout exceeded; private SQL\n"
        self.assertEqual(harness.loader_progress(logs)["initializer_failure_hints"],
                         ["out_of_memory", "database_lock_timeout"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
