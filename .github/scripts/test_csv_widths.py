#!/usr/bin/env python3

import copy
import csv
import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("validate_csv_widths.py")
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("validate_csv_widths", SCRIPT_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def read_csv(relative_path):
    with (REPOSITORY_ROOT / relative_path).open(
        newline="", encoding="utf-8-sig"
    ) as handle:
        return list(csv.reader(handle))


class AdmissionRoleContractTest(unittest.TestCase):
    EXPECTED_UUID = "71dcb611-756a-4ad3-a9bb-73b6cfe28066"
    EXPECTED_NAME = "Admision"
    # Independent oracle: changing the validator and CSV together must not
    # silently broaden the permission-only contract.
    EXPECTED_PRIVILEGES = {
        "Add Patients",
        "Add Patient Identifiers",
        "Add People",
        "Add Relationships",
        "Add Visits",
        "Appointments: Invite Providers",
        "Delete Relationships",
        "Edit Patient Identifiers",
        "Edit Patients",
        "Edit People",
        "Edit Relationships",
        "Edit Visits",
        "Get Admission Locations",
        "Get Beds",
        "Get Concept Attribute Types",
        "Get Concept Sources",
        "Get Concepts",
        "Get Encounters",
        "Get Identifier Types",
        "Get Location Attribute Types",
        "Get Locations",
        "Get Patient Identifiers",
        "Get Patients",
        "Get People",
        "Get Person Attribute Types",
        "Get Providers",
        "Get Queue Entries",
        "Get Queues",
        "Get Relationship Types",
        "Get Relationships",
        "Get Visit Attribute Types",
        "Get Visit Types",
        "Get Visits",
        "Manage Appointments",
        "Manage Own Appointments",
        "Manage Queue Entries",
        "View Appointment Services",
        "View Appointments",
        "View Identifier Types",
        "View Locations",
        "View Navigation Menu",
        "View Patient Identifiers",
        "View Patients",
        "View People",
        "View Person Attribute Types",
        "View Relationship Types",
        "View Relationships",
        "app:appointments.issueDate.edit",
        "app:appointments.startDate.edit",
        "app:home",
        "app:home.admision",
        "app:home.citas",
        "app:home.citas.editar",
        "app:home.colasAtencion",
        "app:home.colasAtencion.editar",
        "app:home.libroAtenciones",
        "app:opciones.busquedaPaciente",
        "app:opciones.registrarAcompanante",
        "app:opciones.registrarPaciente",
    }

    @classmethod
    def setUpClass(cls):
        cls.core_rows = read_csv(VALIDATOR.ROLES_CORE_PATH)

    def admission_row(self, rows):
        uuid_index = rows[0].index("Uuid")
        return next(
            row for row in rows[1:] if row[uuid_index] == self.EXPECTED_UUID
        )

    def validate_rows(self, rows):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory)
            roles_path = config_dir / "roles-core.csv"
            with roles_path.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerows(rows)
            with mock.patch.multiple(
                VALIDATOR, CONFIG_DIR=config_dir, ROLES_CORE_PATH=roles_path
            ):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = VALIDATOR.main()
        return result, stderr.getvalue()

    def assert_rejected(self, rows, message):
        result, errors = self.validate_rows(rows)
        self.assertEqual(1, result)
        self.assertIn(message, errors)

    def test_repository_admission_role_has_exact_canonical_contract(self):
        rows = self.core_rows
        uuid_index = rows[0].index("Uuid")
        role_index = rows[0].index("Role name")
        matching_rows = [
            row
            for row in rows[1:]
            if row[uuid_index] == self.EXPECTED_UUID
            or row[role_index] == self.EXPECTED_NAME
        ]
        self.assertEqual(1, len(matching_rows))
        admission = matching_rows[0]
        self.assertEqual(self.EXPECTED_UUID, admission[uuid_index])
        self.assertEqual(self.EXPECTED_NAME, admission[role_index])
        self.assertEqual("", admission[rows[0].index("Inherited roles")])
        self.assertEqual(
            self.EXPECTED_PRIVILEGES,
            VALIDATOR.split_privileges(admission[rows[0].index("Privileges")]),
        )
        self.assertEqual(self.EXPECTED_UUID, VALIDATOR.ADMISSION_ROLE_UUID)
        self.assertEqual(self.EXPECTED_NAME, VALIDATOR.ADMISSION_ROLE_NAME)
        self.assertEqual(
            self.EXPECTED_PRIVILEGES, VALIDATOR.ADMISSION_REQUIRED_PRIVILEGES
        )
        self.assertEqual((0, ""), self.validate_rows(rows))

    def test_requires_approved_relationship_and_logbook_privileges(self):
        for privilege in (
            "Add Relationships",
            "Delete Relationships",
            "Edit Relationships",
            "Get Relationships",
            "View Relationships",
            "app:home.libroAtenciones",
        ):
            with self.subTest(privilege=privilege):
                rows = copy.deepcopy(self.core_rows)
                privileges_index = rows[0].index("Privileges")
                admission = self.admission_row(rows)
                privileges = VALIDATOR.split_privileges(
                    admission[privileges_index]
                )
                privileges.remove(privilege)
                admission[privileges_index] = ";".join(sorted(privileges))

                self.assert_rejected(
                    rows, f"'Admision' is missing required privileges: {privilege}"
                )

    def test_rejects_purge_relationships(self):
        rows = copy.deepcopy(self.core_rows)
        self.admission_row(rows)[rows[0].index("Privileges")] += ";Purge Relationships"

        self.assert_rejected(
            rows, "'Admision' has unapproved privileges: Purge Relationships"
        )

    def test_rejects_other_unapproved_privileges(self):
        for privilege in (
            "Manage Roles", "Get Global Properties", "app:home.libroAtenciones.editar"
        ):
            with self.subTest(privilege=privilege):
                rows = copy.deepcopy(self.core_rows)
                self.admission_row(rows)[rows[0].index("Privileges")] += (
                    f";{privilege}"
                )

                self.assert_rejected(
                    rows, f"'Admision' has unapproved privileges: {privilege}"
                )

    def test_rejects_inherited_roles(self):
        for inherited_role in ("Privilege Level: Full", "System Developer"):
            with self.subTest(inherited_role=inherited_role):
                rows = copy.deepcopy(self.core_rows)
                self.admission_row(rows)[rows[0].index("Inherited roles")] = (
                    inherited_role
                )

                self.assert_rejected(
                    rows, f"'Admision' must not inherit roles; found: {inherited_role}"
                )

    def test_rejects_wrong_canonical_uuid(self):
        rows = copy.deepcopy(self.core_rows)
        self.admission_row(rows)[rows[0].index("Uuid")] = (
            "00000000-0000-0000-0000-000000000001"
        )

        self.assert_rejected(
            rows, f"'Admision' must keep UUID {self.EXPECTED_UUID}"
        )

    def test_rejects_wrong_canonical_name(self):
        rows = copy.deepcopy(self.core_rows)
        self.admission_row(rows)[rows[0].index("Role name")] = "Admision alternativa"

        self.assert_rejected(rows, "expected exactly one 'Admision' role, found 0")

    def test_rejects_duplicate_canonical_role(self):
        rows = copy.deepcopy(self.core_rows)
        rows.append(copy.deepcopy(self.admission_row(rows)))

        self.assert_rejected(rows, "expected exactly one 'Admision' role, found 2")

    def test_rejects_missing_canonical_role(self):
        rows = copy.deepcopy(self.core_rows)
        rows.remove(self.admission_row(rows))

        self.assert_rejected(rows, "expected exactly one 'Admision' role, found 0")


class LaboratoryAttachmentRoleContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core_rows = read_csv(VALIDATOR.ROLES_CORE_PATH)
        cls.peru_rows = read_csv(VALIDATOR.ROLES_PERU_HCE_PATH)

    def laboratory_row(self, rows):
        uuid_index = rows[0].index("Uuid")
        return next(
            row
            for row in rows[1:]
            if row[uuid_index] == VALIDATOR.LABORATORY_ROLE_UUID
        )

    def attachment_role_row(self, rows, role_uuid):
        uuid_index = rows[0].index("Uuid")
        return next(row for row in rows[1:] if row[uuid_index] == role_uuid)

    def test_repository_attachment_role_contracts_are_valid(self):
        self.assertEqual(
            [],
            VALIDATOR.validate_generic_attachment_role_contracts(self.core_rows),
        )
        self.assertEqual(
            [],
            VALIDATOR.validate_laboratory_attachment_contract(self.core_rows),
        )
        self.assertEqual(
            [],
            VALIDATOR.validate_legacy_laboratory_attachment_scope(self.peru_rows),
        )

    def test_generic_attachment_reader_remains_read_only(self):
        rows = copy.deepcopy(self.core_rows)
        privileges_index = rows[0].index("Privileges")
        reader = self.attachment_role_row(
            rows, VALIDATOR.ATTACHMENT_READER_ROLE_UUID
        )
        privileges = VALIDATOR.split_privileges(reader[privileges_index])
        privileges.remove("View Attachments")
        privileges.add("Create Attachments")
        reader[privileges_index] = ";".join(sorted(privileges))

        errors = "\n".join(
            VALIDATOR.validate_generic_attachment_role_contracts(rows)
        )

        self.assertIn("View Attachments", errors)
        self.assertIn("Create Attachments", errors)

    def test_generic_attachment_editor_keeps_complete_contract(self):
        rows = copy.deepcopy(self.core_rows)
        privileges_index = rows[0].index("Privileges")
        editor = self.attachment_role_row(
            rows, VALIDATOR.ATTACHMENT_EDITOR_ROLE_UUID
        )
        privileges = VALIDATOR.split_privileges(editor[privileges_index])
        for privilege in (
            "Add Observations",
            "Create Attachments",
            "Delete Observations",
            "View Attachments",
        ):
            privileges.remove(privilege)
        editor[privileges_index] = ";".join(sorted(privileges))

        errors = "\n".join(
            VALIDATOR.validate_generic_attachment_role_contracts(rows)
        )

        for privilege in (
            "Add Observations",
            "Create Attachments",
            "Delete Observations",
            "View Attachments",
        ):
            self.assertIn(privilege, errors)

    def test_generic_attachment_roles_do_not_receive_global_property_access(self):
        rows = copy.deepcopy(self.core_rows)
        privileges_index = rows[0].index("Privileges")
        editor = self.attachment_role_row(
            rows, VALIDATOR.ATTACHMENT_EDITOR_ROLE_UUID
        )
        editor[privileges_index] += ";Get Global Properties"

        errors = "\n".join(
            VALIDATOR.validate_generic_attachment_role_contracts(rows)
        )

        self.assertIn("Get Global Properties", errors)

    def test_requires_both_attachment_markers_and_add_observations(self):
        rows = copy.deepcopy(self.core_rows)
        privileges_index = rows[0].index("Privileges")
        laboratory = self.laboratory_row(rows)
        privileges = VALIDATOR.split_privileges(laboratory[privileges_index])
        privileges.remove("Create Attachments")
        privileges.remove("Add Observations")
        laboratory[privileges_index] = ";".join(sorted(privileges))

        errors = "\n".join(
            VALIDATOR.validate_laboratory_attachment_contract(rows)
        )

        self.assertIn("Create Attachments", errors)
        self.assertIn("must preserve Add Observations", errors)

    def test_rejects_general_attachments_ui_edit_marker(self):
        rows = copy.deepcopy(self.core_rows)
        privileges_index = rows[0].index("Privileges")
        laboratory = self.laboratory_row(rows)
        laboratory[privileges_index] += ";app:hoja.clinica.adjuntos.editar"

        errors = "\n".join(
            VALIDATOR.validate_laboratory_attachment_contract(rows)
        )

        self.assertIn("outside the declarative", errors)
        self.assertIn("app:hoja.clinica.adjuntos.editar", errors)

    def test_rejects_attachment_markers_on_legacy_laboratory_role(self):
        rows = copy.deepcopy(self.peru_rows)
        uuid_index = rows[0].index("Uuid")
        privileges_index = rows[0].index("Privileges")
        legacy = next(
            row
            for row in rows[1:]
            if row[uuid_index] == VALIDATOR.LEGACY_LABORATORY_ROLE_UUID
        )
        legacy[privileges_index] += ";View Attachments"

        errors = "\n".join(
            VALIDATOR.validate_legacy_laboratory_attachment_scope(rows)
        )

        self.assertIn("legacy role", errors)
        self.assertIn("View Attachments", errors)

    def test_rejects_global_property_access_as_attachment_workaround(self):
        rows = copy.deepcopy(self.core_rows)
        privileges_index = rows[0].index("Privileges")
        laboratory = self.laboratory_row(rows)
        laboratory[privileges_index] += ";Get Global Properties"

        errors = "\n".join(
            VALIDATOR.validate_laboratory_attachment_contract(rows)
        )

        self.assertIn("outside the declarative", errors)
        self.assertIn("Get Global Properties", errors)

    def test_rejects_canonical_laboratory_identity_drift(self):
        rows = copy.deepcopy(self.core_rows)
        role_index = rows[0].index("Role name")
        self.laboratory_row(rows)[role_index] = "Laboratorio alterno"

        errors = "\n".join(
            VALIDATOR.validate_laboratory_attachment_contract(rows)
        )

        self.assertIn("must keep the name 'Laboratorio'", errors)


if __name__ == "__main__":
    unittest.main()
