#!/usr/bin/env python3
"""Pure harness contracts. No Docker, network, backend, or existing credentials."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import guards
import harness
from guards import HarnessFailure, LEGACY_ROLE, CANONICAL_UUID


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


def procedure_anatomy_result():
    """Synthetic database/search responses; no clinical data or persisted codes."""
    root_uuid = "90000000-0000-4000-8000-000000000000"
    expected, terms, members, mappings = {}, set(), [], []
    codes = ["ADB", "DELT", "ESO"] + ["synthetic-" + str(index) for index in range(130)]
    by_code = {}
    for index, code in enumerate(codes):
        identifier = f"10000000-0000-4000-8000-{index:012d}"
        mapping_uuid = f"20000000-0000-4000-8000-{index:012d}"
        by_code[code] = identifier
        expected[identifier] = ("Anatomy", "N/A", "Sitio sintético " + str(index))
        terms.add((identifier, code, mapping_uuid))
        members.append(f"{100 + index}\t30000000-0000-4000-8000-{index:012d}\t{500 + index}\t"
                       + identifier + "\t0\t" + "\t".join(expected[identifier]))
        mappings.append(f"{identifier}\t{code}\t{mapping_uuid}\t{900 + index}\t{1200 + index}")
    association = ("40000000-0000-4000-8000-000000000000", "50000000-0000-4000-8000-000000000000",
                   "http://terminology.hl7.org/CodeSystem/v2-0550")
    rows = [["50\t" + root_uuid + "\t0\t1"], members, mappings,
            ["60\t" + association[0] + "\t0\t70\t" + association[1] + "\tv2-0550\t0\t" + association[2]], ["0"]]
    responses = [(200, {"results": [{"uuid": by_code[code], "display": "Sitio sintético"}]})
                 for code in ("ADB", "DELT", "ESO")] + [(200, {"results": []})]
    return (root_uuid, expected, terms, association), rows, responses


class HarnessContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="admission-harness-unit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.runtime = object.__new__(harness.Harness)
        self.runtime.hospital_roles = []

    def test_procedure_anatomy_checks_native_search_and_preserves_database_identities(self):
        contract, rows, responses = procedure_anatomy_result()
        self.runtime.procedure_anatomy_contract = Mock(return_value=contract)
        self.runtime.query = Mock(side_effect=rows * 2)
        self.runtime.request = Mock(side_effect=responses * 2)
        with patch.object(harness, "emit"):
            previous = self.runtime.check_procedure_anatomy("owned", "db", "upgrade")
            self.assertEqual(self.runtime.check_procedure_anatomy("owned", "db", "restart", previous), previous)
        paths = [call.args[2] for call in self.runtime.request.call_args_list[:4]]
        self.assertIn("q=es%C3%B3fago", paths[2])
        self.assertTrue(all("memberOf=" + contract[0] in path and "name=" not in path for path in paths))
        contract, changed, responses = procedure_anatomy_result()
        changed[1][0] = "9999" + changed[1][0][changed[1][0].index("\t"):]
        self.runtime.query = Mock(side_effect=changed)
        self.runtime.request = Mock(side_effect=responses)
        with self.assertRaisesRegex(HarnessFailure, "procedure_anatomy_changed_on_restart"):
            self.runtime.check_procedure_anatomy("owned", "db", "restart", previous)

    def test_procedure_anatomy_rejects_incomplete_members_and_changed_hl7_mapping(self):
        for section in (1, 2):
            with self.subTest(section=section):
                contract, rows, responses = procedure_anatomy_result()
                rows[section].pop()
                self.runtime.procedure_anatomy_contract = Mock(return_value=contract)
                self.runtime.query = Mock(side_effect=rows)
                self.runtime.request = Mock(side_effect=responses)
                with self.assertRaisesRegex(HarnessFailure, "procedure_anatomy_(members|hl7_mappings)_invalid"):
                    self.runtime.check_procedure_anatomy("owned", "db", "fresh")

    def test_procedure_anatomy_rejects_changed_datatype_or_missing_spanish(self):
        for field, value in ((6, "Coded"), (7, "NULL")):
            with self.subTest(field=field):
                contract, rows, _ = procedure_anatomy_result()
                fields = rows[1][0].split("\t")
                fields[field] = value
                rows[1][0] = "\t".join(fields)
                self.runtime.procedure_anatomy_contract = Mock(return_value=contract)
                self.runtime.query = Mock(side_effect=rows)
                with self.assertRaisesRegex(HarnessFailure, "procedure_anatomy_member_metadata_invalid"):
                    self.runtime.check_procedure_anatomy("owned", "db", "fresh")

    def test_procedure_anatomy_rejects_accent_insensitive_spanish_collision(self):
        contract, rows, responses = procedure_anatomy_result()
        rows[-1] = ["1"]
        self.runtime.procedure_anatomy_contract = Mock(return_value=contract)
        self.runtime.query = Mock(side_effect=rows)
        self.runtime.request = Mock(side_effect=responses)
        with self.assertRaisesRegex(HarnessFailure, "procedure_anatomy_spanish_name_collision"):
            self.runtime.check_procedure_anatomy("owned", "db", "fresh")
        self.runtime.request.assert_not_called()

    def test_procedure_anatomy_rejects_search_results_outside_the_set(self):
        contract, rows, responses = procedure_anatomy_result()
        responses[-1] = (200, {"results": [{"uuid": "90000000-0000-4000-8000-999999999999"}]})
        self.runtime.procedure_anatomy_contract = Mock(return_value=contract)
        self.runtime.query = Mock(side_effect=rows)
        self.runtime.request = Mock(side_effect=responses)
        with self.assertRaisesRegex(HarnessFailure, "procedure_anatomy_search_membership_invalid"):
            self.runtime.check_procedure_anatomy("owned", "db", "fresh")

    def test_procedure_anatomy_rejects_missing_duplicate_or_incorrect_fhir_association(self):
        for defect in ("missing", "duplicate", "retired", "source", "url"):
            with self.subTest(defect=defect):
                contract, rows, responses = procedure_anatomy_result()
                if defect == "missing":
                    rows[3] = []
                elif defect == "duplicate":
                    rows[3] *= 2
                else:
                    fields = rows[3][0].split("\t")
                    field, value = {"retired": (2, "1"), "source": (4, "wrong-source"),
                                    "url": (7, "https://example.org/wrong-system")}[defect]
                    fields[field] = value
                    rows[3][0] = "\t".join(fields)
                self.runtime.procedure_anatomy_contract = Mock(return_value=contract)
                self.runtime.query = Mock(side_effect=rows)
                self.runtime.request = Mock(side_effect=responses)
                with self.assertRaisesRegex(HarnessFailure, "procedure_anatomy_fhir_source_invalid"):
                    self.runtime.check_procedure_anatomy("owned", "db", "fresh")
                self.runtime.request.assert_not_called()

    def test_procedure_anatomy_preserves_fhir_association_identity_on_restart(self):
        contract, rows, responses = procedure_anatomy_result()
        self.runtime.procedure_anatomy_contract = Mock(return_value=contract)
        self.runtime.query = Mock(side_effect=rows)
        self.runtime.request = Mock(side_effect=responses)
        with patch.object(harness, "emit"):
            previous = self.runtime.check_procedure_anatomy("owned", "db", "upgrade")
        rows[3][0] = "99" + rows[3][0][rows[3][0].index("\t"):]
        self.runtime.query = Mock(side_effect=rows)
        self.runtime.request = Mock(side_effect=responses)
        with self.assertRaisesRegex(HarnessFailure, "procedure_anatomy_changed_on_restart"):
            self.runtime.check_procedure_anatomy("owned", "db", "restart", previous)

    def test_clinical_form_updates_preserve_history_and_require_loaded_criteria(self):
        self.runtime.candidate_config = self.root
        (self.root / "ampathforms").mkdir()
        (self.root / "conceptreferencerange").mkdir()
        schema = b' \t{"name":"Synthetic form","version":"2","published":true,"retired":false}\r\n'
        for filename in harness.REVIEWED_FORMS:
            (self.root / "ampathforms" / filename).write_bytes(schema)
        (self.root / "conceptreferencerange/conceptreferencerange_laboratory.csv").write_text(
            "Uuid,Criteria\n" + "".join(identifier + ",false\n" for identifier in harness.REVIEWED_RANGES))
        schema_hash = harness.hashlib.md5(b'{"name":"Synthetic form","version":"2","published":true,"retired":false}').hexdigest()
        criteria_hash = harness.hashlib.md5(b"false").hexdigest()
        previous = ["old-uuid\t10\t1\t0\told-schema-hash"]
        current = ["old-uuid\t10\t1\t1\told-schema-hash", f"new-uuid\t11\t2\t0\t{schema_hash}"]
        self.runtime.form_schema_snapshot = Mock(return_value=current)
        self.runtime.query = Mock(side_effect=lambda db, sql:
            [criteria_hash] if "concept_reference_range" in sql else [f"2\t1\t0\t{schema_hash}"])
        with patch.object(harness, "emit"):
            self.assertEqual(current, self.runtime.check_clinical_form_updates("synthetic", "upgrade", previous))
            self.runtime.form_schema_snapshot.return_value = [current[0].replace("old-schema-hash", "changed")]
            with self.assertRaisesRegex(HarnessFailure, "historical_form_identity_or_schema_changed"):
                self.runtime.check_clinical_form_updates("synthetic", "upgrade", previous)
            self.runtime.form_schema_snapshot.return_value = current
            self.runtime.query.side_effect = lambda db, sql: ["stale"] if "concept_reference_range" in sql else [f"2\t1\t0\t{schema_hash}"]
            with self.assertRaisesRegex(HarnessFailure, "clinical_reference_range_not_updated"):
                self.runtime.check_clinical_form_updates("synthetic", "upgrade", previous)

    def test_clinical_form_updates_honor_declarative_retirement(self):
        self.runtime.candidate_config = self.root
        (self.root / "ampathforms").mkdir()
        (self.root / "conceptreferencerange").mkdir()
        (self.root / "conceptreferencerange/conceptreferencerange_laboratory.csv").write_text("Uuid,Criteria\n")
        schema = b'{"name":"Retired synthetic form","version":"2","published":false,"retired":true}'
        (self.root / "ampathforms/retired.json").write_bytes(schema)
        schema_hash = harness.hashlib.md5(schema).hexdigest()
        current = [f"retired-uuid\t10\t2\t1\t{schema_hash}"]
        self.runtime.form_schema_snapshot = Mock(return_value=current)
        with patch.object(harness, "REVIEWED_FORMS", ("retired.json",)), \
             patch.object(harness, "REVIEWED_RANGES", ()), patch.object(harness, "emit"):
            self.runtime.query = Mock(return_value=[f"2\t0\t1\t{schema_hash}"])
            self.assertEqual(current, self.runtime.check_clinical_form_updates("synthetic", "restart", current))
            for published, retired in ((1, 1), (0, 0)):
                with self.subTest(published=published, retired=retired):
                    self.runtime.query.return_value = [f"2\t{published}\t{retired}\t{schema_hash}"]
                    with self.assertRaisesRegex(HarnessFailure, "clinical_form_schema_not_loaded"):
                        self.runtime.check_clinical_form_updates("synthetic", "restart", current)

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

    def make_configuration(self, name, files):
        directory = self.root / name
        directory.mkdir()
        for relative, content in files.items():
            target = directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return directory

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

    def history_snapshot(self, changes=None):
        row = {
            "ID": "sihsalusaudit-20260819-09-validate", "AUTHOR": "sihsalus", "FILENAME": "liquibase.xml",
            "DATEEXECUTED": "2026-09-23 12:00:00", "ORDEREXECUTED": "100", "EXECTYPE": "EXECUTED",
            "MD5SUM": "9:" + "a" * 32, "DESCRIPTION": "sql", "COMMENTS": "", "TAG": "NULL",
            "LIQUIBASE": "4.33.0", "CONTEXTS": "NULL", "LABELS": "NULL", "DEPLOYMENT_ID": "1234567890",
            "FUTURE_COLUMN": "retained",
        }
        row.update(changes or {})
        self.runtime.query = Mock(side_effect=lambda db, sql:
            ["\t".join(row.values())] if sql.startswith("SELECT *") else list(row))
        result = self.runtime.history("owned-db")
        self.runtime.query.assert_any_call(
            "owned-db", "SELECT * FROM liquibasechangelog ORDER BY ID,AUTHOR,FILENAME")
        return result

    def test_native_audit_runalways_preserves_history_despite_execution_metadata(self):
        for identifier in ("07-no-update", "08-no-delete", "09-validate", "10-mariadb-validate"):
            with self.subTest(identifier=identifier):
                original = {"ID": "sihsalusaudit-20260819-" + identifier}
                before = self.history_snapshot(original)
                after = self.history_snapshot({**original, "DATEEXECUTED": "2026-09-23 12:05:00",
                    "ORDEREXECUTED": "200", "EXECTYPE": "RERAN", "DEPLOYMENT_ID": "1234567900"})
                self.assertEqual(before, after)

    def test_history_keeps_checksums_identity_and_all_nonexecution_columns(self):
        before = self.history_snapshot()
        for column, value in {"ID": "other", "AUTHOR": "other", "FILENAME": "other.xml",
                "MD5SUM": "9:" + "b" * 32, "DESCRIPTION": "changed", "COMMENTS": "changed",
                "TAG": "changed", "LIQUIBASE": "changed", "CONTEXTS": "changed",
                "LABELS": "changed", "FUTURE_COLUMN": "changed"}.items():
            with self.subTest(column=column):
                self.assertNotEqual(before, self.history_snapshot({column: value}))

    def test_unrelated_and_content_history_preserve_every_execution_column(self):
        for identity in ({"ID": guards.CHANGESET}, {"ID": "sihsalusaudit-20260819-01-table"},
                         {"AUTHOR": "other"}, {"FILENAME": "other.xml"}):
            before = self.history_snapshot(identity)
            for column, value in {"DATEEXECUTED": "2026-09-23 12:05:00", "ORDEREXECUTED": "200",
                                  "EXECTYPE": "RERAN", "DEPLOYMENT_ID": "1234567900"}.items():
                with self.subTest(identity=identity, column=column):
                    self.assertNotEqual(before, self.history_snapshot({**identity, column: value}))

    def test_native_audit_history_rejects_failed_or_skipped_executions(self):
        for execution in ("FAILED", "SKIPPED", "MARK_RAN", "NULL", "unexpected"):
            with self.subTest(execution=execution), self.assertRaisesRegex(
                    HarnessFailure, "native_audit_execution_invalid"):
                self.history_snapshot({"EXECTYPE": execution})

    def test_native_trigger_preconditions_can_record_mark_ran(self):
        for suffix in ("07-no-update", "08-no-delete"):
            with self.subTest(suffix=suffix):
                identity = {"ID": "sihsalusaudit-20260819-" + suffix}
                self.assertEqual(self.history_snapshot(identity),
                                 self.history_snapshot({**identity, "EXECTYPE": "MARK_RAN"}))

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

    def test_current_core_role_additions_are_applied_only_when_reviewed(self):
        self.runtime.hospital_roles = []
        roles = [{"Role name": name, "Uuid": rule["uuid"], "Description": "Reviewed role",
                  "Inherited roles": "", "Privileges": ";".join(sorted(rule["privileges"]))}
                 for name, rule in guards.CURRENT_CORE_ROLE_ADDITIONS.items()]
        self.runtime.query = Mock(side_effect=[["role", "description", "uuid"], ["role", "privilege"]])
        before = {"role": ["Other\tKeep\tother"], "role_privilege": ["Other\tKeep"], "role_role": [], "user_role": []}
        actual = self.runtime.expected_hospital_role_state("owned", before, roles)
        self.assertEqual(set(actual["role"]), {
            "Other\tKeep\tother",
            "SIHSALUS Indicadores\tReviewed role\tda21e37c-246e-4a1f-8ace-ca17b03ff4b5",
            "SIHSALUS Indicadores editar\tReviewed role\t9437d70d-2195-4b93-84ed-a4e6e17558a9",
        })
        self.assertEqual(set(actual["role_privilege"]), {"Other\tKeep"} | {
            role + "\t" + privilege
            for role, rule in guards.CURRENT_CORE_ROLE_ADDITIONS.items()
            for privilege in rule["privileges"]
        })
        self.assertEqual(actual["role_role"], [])
        self.assertEqual(actual["user_role"], [])
        self.assertEqual(before["role"], ["Other\tKeep\tother"])

    def test_emrapi_refresh_adds_only_declared_compatibility_and_then_is_stable(self):
        self.runtime.hospital_compatibility = {"app:home.editar"}
        with patch.object(harness, "CURRENT_EMRAPI_ADDITIONS", frozenset()):
            before = {"role_privilege": ["Other\tKeep", "Privilege Level: Full\tapp:home.editar"],
                      "user_role": ["42\tOther"], "patientflags_tag_role": ["1\tOther"] * 2}
            expected = self.runtime.expected_emrapi_refresh(before)
            self.assertEqual(expected["role_privilege"], ["Other\tKeep",
                "Privilege Level: Full\tapp:home.editar", "Privilege Level: High\tapp:home.editar"])
            self.assertEqual(expected["user_role"], before["user_role"])
            self.assertEqual(expected["patientflags_tag_role"], before["patientflags_tag_role"])
            self.assertEqual(self.runtime.expected_emrapi_refresh(expected), expected)
            self.assertEqual(len(before["role_privilege"]), 2)

    def test_emrapi_refresh_declares_the_current_revision_additions(self):
        self.runtime.hospital_compatibility = set()
        before = {"role_privilege": ["Other\tKeep", "Privilege Level: Full\tapp:indicadores.editar"],
                  "user_role": ["42\tOther"]}
        expected = self.runtime.expected_emrapi_refresh(before)
        self.assertEqual(expected["role_privilege"], ["Other\tKeep",
            "Privilege Level: Full\tapp:indicadores.editar",
            "Privilege Level: High\tapp:indicadores.editar"])
        self.assertEqual(expected["user_role"], before["user_role"])
        self.assertEqual(self.runtime.expected_emrapi_refresh(expected), expected)
        self.assertEqual(harness.CURRENT_EMRAPI_ADDITIONS, frozenset({"app:indicadores.editar"}))

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
        for table in (0, 2):
            with self.subTest(recreated_table=table), patch.object(harness, "emit") as emit:
                changed, response = clinical_drug_result()
                changed[table][0] = "999" + changed[table][0][changed[table][0].index("\t"):]
                self.runtime.query = Mock(side_effect=changed)
                with self.assertRaisesRegex(HarnessFailure, "^clinical_drug_changed_on_restart$"):
                    self.runtime.check_clinical_drug("owned", "db", "idempotence", previous)
                emit.assert_not_called()

    def test_ocl_refresh_checks_active_concepts_and_preserves_all_catalog_identities_on_restart(self):
        self.runtime.query = Mock(side_effect=ocl_refresh_result() * 2)
        with patch.object(harness, "emit") as emit:
            previous = self.runtime.check_ocl_refresh("db", "upgrade")
            self.assertEqual(self.runtime.check_ocl_refresh("db", "idempotence", previous), previous)
        self.assertTrue(all(call.args[1].startswith("SELECT ") for call in self.runtime.query.call_args_list))
        emit.assert_any_call("ocl_refresh", "PASSED", phase="idempotence", concepts=2,
                             neighborhood_sets=1, neighborhood_members=10, restart_checked=True)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
