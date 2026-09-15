#!/usr/bin/env python3
"""Regression checks for privilege drift and unsafe role reconciliation."""
import csv
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_hospital_access_profiles import CONFIG, CONTRACT, ROOT, validate


class HospitalAccessProfilesTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ("roles", "privileges"):
            shutil.copytree(ROOT / CONFIG / name, self.root / CONFIG / name)
        (self.root / CONTRACT).parent.mkdir(parents=True)
        shutil.copy2(ROOT / CONTRACT, self.root / CONTRACT)

    def change_role(self, name, mutate):
        for path in (self.root / CONFIG / "roles").glob("*.csv"):
            with path.open(newline="") as stream:
                reader = csv.DictReader(stream)
                fields, rows = reader.fieldnames, list(reader)
            for row in rows:
                if row["Role name"] == name:
                    mutate(row)
                    with path.open("w", newline="") as stream:
                        writer = csv.DictWriter(stream, fieldnames=fields)
                        writer.writeheader()
                        writer.writerows(rows)
                    return
        self.fail("Missing fixture role: " + name)

    def change_contract(self, mutate):
        path = self.root / CONTRACT
        contract = json.loads(path.read_text())
        mutate(contract)
        path.write_text(json.dumps(contract))

    def test_current_metadata_matches_reviewed_effective_access(self):
        self.assertEqual(validate(self.root)["farmacia"], 103)

    def test_shared_login_cannot_gain_administration(self):
        self.change_role("SIHSALUS Login", lambda r: r.update(Privileges=r["Privileges"] + ";Manage Roles"))
        with self.assertRaisesRegex(ValueError, "differs for admision"):
            validate(self.root)

    def test_pharmacy_inheritance_is_required(self):
        self.change_role("Inventory Manager", lambda r: r.update(**{"Inherited roles": ""}))
        # Other inventory roles may also grant the base role: remove the actual
        # dispensing capability to exercise effective access, not just a role count.
        self.change_role("Inventory Dispensing", lambda r: r.update(Privileges=""))
        with self.assertRaisesRegex(ValueError, "differs for farmacia"):
            validate(self.root)

    def test_retired_consultation_fua_grants_do_not_become_default(self):
        self.change_role("SIHSALUS Consulta Externa", lambda r: r.update(Privileges=r["Privileges"] + ";app:home.fua"))
        with self.assertRaises(ValueError):
            validate(self.root)

    def test_support_does_not_inherit_future_module_privileges(self):
        self.change_role("SIHSALUS Soporte", lambda r: r.update(**{"Inherited roles": "Privilege Level: Full"}))
        with self.assertRaisesRegex(ValueError, "explicit grants"):
            validate(self.root)

    def test_supplement_does_not_recreate_admission_migration_alias(self):
        self.change_role("SIHSALUS Admision Hospitalaria", lambda r: r.update(**{"Role name": "SIHSALUS Admision"}))
        with self.assertRaisesRegex(ValueError, "legacy admission alias"):
            validate(self.root)

    def test_role_uuid_collision_is_rejected(self):
        self.change_role("SIHSALUS Laboratorio", lambda r: r.update(Uuid="ac0ac0e6-2520-4181-9023-7891a82dabd2"))
        with self.assertRaisesRegex(ValueError, "Duplicate role identity"):
            validate(self.root)

    def test_privilege_spelling_is_case_sensitive(self):
        self.change_role("SIHSALUS Soporte", lambda r: r.update(Privileges=r["Privileges"].replace("Manage Roles", "manage roles")))
        with self.assertRaisesRegex(ValueError, "Undefined privilege"):
            validate(self.root)

    def test_inheritance_cycle_fails_without_recursion_overflow(self):
        self.change_role("SIHSALUS Login", lambda r: r.update(**{"Inherited roles": "SIHSALUS Login"}))
        with self.assertRaisesRegex(ValueError, "inheritance cycle"):
            validate(self.root)

    def test_support_is_not_a_template_for_admission(self):
        self.change_contract(lambda c: c["profiles"]["admision"]["roles"].append("SIHSALUS Soporte"))
        with self.assertRaisesRegex(ValueError, "differs for admision"):
            validate(self.root)

    def test_qlty_does_not_accidentally_receive_dev_audit_privileges(self):
        self.change_contract(lambda c: c["environmentExtensions"]["qlty"].update(c["environmentExtensions"]["dev"]))
        with self.assertRaisesRegex(ValueError, "DEV-only"):
            validate(self.root)


if __name__ == "__main__":
    unittest.main()
