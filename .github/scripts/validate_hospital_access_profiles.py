#!/usr/bin/env python3
"""Check effective functional access against the reviewed hospital baseline.

This validates metadata only. It never connects to a server or provisions users.
Module-owned roles are read-only inputs to the contract, not Initializer rows.
"""
import csv
import json
from pathlib import Path
import sys
from uuid import UUID


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("docs/contracts/hospital-access-profiles.json")
CONFIG = Path("configuration")
OPERATIONS = {
    "SIHSALUS Laboratorio": "cf57784d-c859-40ee-b3f2-a3075388d6d4",
    "SIHSALUS Soporte": "ac0ac0e6-2520-4181-9023-7891a82dabd2",
}
PROFILES = {"admision", "consulta.externa", "enfermeria.triaje", "farmacia", "laboratorio", "soporte"}
PRESERVED = {"gestion", "obstetricia", "cred", "auditor"}
UNBOUNDED_ROLES = {"System Developer", "Privilege Level: Full", "Privilege Level: High"}
ADMIN_PRIVILEGES = {
    "Manage Roles", "Manage Privileges", "Add Users", "Edit Users", "Delete Users",
    "Purge Users", "Manage Modules", "Assign System Developer Role",
}


def split(value):
    return [item.strip() for item in value.split(";") if item.strip()]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_roles(root):
    roles = {}
    uuids = set()
    for path in sorted((root / CONFIG / "roles").glob("*.csv")):
        for row in read_csv(path):
            name = row.get("Role name")
            if not name:
                continue
            identifier = str(UUID(row["Uuid"]))
            if name in roles or identifier in uuids:
                raise ValueError("Duplicate role identity: " + name)
            uuids.add(identifier)
            privileges = split(row["Privileges"])
            parents = split(row["Inherited roles"])
            if len(privileges) != len(set(privileges)) or len(parents) != len(set(parents)):
                raise ValueError("Duplicate role grant or inheritance: " + name)
            roles[name] = {"uuid": identifier, "privileges": privileges, "inheritedRoles": parents}
    return roles


def effective(roles, names):
    privileges, visited, pending = set(), set(), set()

    def visit(name):
        if name in UNBOUNDED_ROLES:
            raise ValueError("Unbounded role in functional profile: " + name)
        if name in pending:
            raise ValueError("Role inheritance cycle: " + name)
        if name in visited:
            return
        if name not in roles:
            raise ValueError("Missing role definition: " + name)
        pending.add(name)
        for parent in roles[name]["inheritedRoles"]:
            visit(parent)
        privileges.update(roles[name]["privileges"])
        pending.remove(name)
        visited.add(name)

    for name in list(names) + ["Anonymous", "Authenticated"]:
        visit(name)
    return privileges


def validate(root=ROOT):
    contract = json.loads((root / CONTRACT).read_text())
    if contract["schemaVersion"] != 1 or set(contract["profiles"]) != PROFILES:
        raise ValueError("Expected six reviewed hospital profiles")
    if set(contract["preservedTestProfiles"]) != PRESERVED:
        raise ValueError("Expected four explicitly preserved test profiles")
    if set(contract["moduleOwnedRoles"]) != {"Anonymous", "Authenticated", "Provider"}:
        raise ValueError("Unexpected module-owned role reference")
    roles = load_roles(root)
    if "SIHSALUS Admision" in roles or "SIHSALUS Admision Hospitalaria" in roles:
        raise ValueError("Do not recreate the legacy admission alias or supplement")
    if set(roles) & set(contract["moduleOwnedRoles"]):
        raise ValueError("Initializer must not overwrite module-owned role references")
    operation_rows = read_csv(root / contract["roleFile"])
    if {row["Role name"] for row in operation_rows} != set(OPERATIONS):
        raise ValueError("Hospital operations CSV must contain only its two owned roles")
    for name, identifier in OPERATIONS.items():
        if roles[name]["uuid"] != identifier:
            raise ValueError("Unstable hospital role UUID: " + name)
        if roles[name]["inheritedRoles"]:
            raise ValueError("Hospital operation roles must keep explicit grants: " + name)
    declared_privileges, privilege_uuids = set(), set()
    for path in sorted((root / CONFIG / "privileges").glob("*.csv")):
        for row in read_csv(path):
            name = row.get("Privilege name")
            if not name:
                continue
            identifier = str(UUID(row["Uuid"]))
            if name in declared_privileges or identifier in privilege_uuids:
                raise ValueError("Duplicate privilege identity: " + name)
            declared_privileges.add(name)
            privilege_uuids.add(identifier)
    roles.update(contract["moduleOwnedRoles"])
    known_privileges = declared_privileges | set(contract["externalPrivilegeNames"])
    for name, profile in contract["profiles"].items():
        actual = effective(roles, profile["roles"])
        expected = set(profile["expectedPrivileges"])
        if len(expected) != len(profile["expectedPrivileges"]):
            raise ValueError("Duplicate expected privilege: " + name)
        if actual - known_privileges:
            raise ValueError("Undefined privilege in " + name + ": " + repr(sorted(actual - known_privileges)))
        if actual != expected:
            raise ValueError("Effective access differs for " + name
                             + "; missing=" + repr(sorted(expected - actual))
                             + "; extra=" + repr(sorted(actual - expected)))
        if name != "soporte" and actual & ADMIN_PRIVILEGES:
            raise ValueError("Administrative grants outside the support profile: " + name)
        if name != "soporte" and "SIHSALUS Soporte" in profile["roles"]:
            raise ValueError("Support must not be assigned as a general-purpose template")
    for name, profile in contract["preservedTestProfiles"].items():
        if set(profile["roles"]) & (UNBOUNDED_ROLES | {"SIHSALUS Soporte"}):
            raise ValueError("Broad administrative role in preserved test profile: " + name)
        if set(profile["expectedPrivileges"]) & ADMIN_PRIVILEGES:
            raise ValueError("Administrative grants in preserved test profile: " + name)
    extensions = contract["environmentExtensions"]
    if set(extensions) != {"dev", "qlty"} or extensions["qlty"]:
        raise ValueError("Audit experiment extensions must remain explicit and DEV-only")
    recording = extensions["dev"]["recordClinicalAudit"]
    reviewing = extensions["dev"]["reviewClinicalAudit"]
    if set(recording["accounts"]) != PROFILES - {"soporte"} | {"obstetricia", "cred"}:
        raise ValueError("Unexpected clinical audit recording accounts")
    if recording["privileges"] != ["Record Clinical Audit Events"]:
        raise ValueError("Unexpected clinical audit recording privilege")
    if reviewing != {"accounts": ["auditor"], "privileges": ["View Clinical Audit Events"]}:
        raise ValueError("Unexpected clinical audit review extension")
    return {name: len(profile["expectedPrivileges"]) for name, profile in contract["profiles"].items()}


if __name__ == "__main__":
    try:
        print("Hospital access profiles valid: " + json.dumps(validate(), sort_keys=True))
    except (ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
