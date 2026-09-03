#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


CONFIG_DIR = Path("configuration/backend_configuration")
LOCATION_TAGS_PATH = CONFIG_DIR / "locationtags" / "locationtags.csv"
LOCATIONS_PATH = CONFIG_DIR / "locations" / "sihsalus-locations.csv"
ROLES_CORE_PATH = CONFIG_DIR / "roles" / "roles-core.csv"
MODULE_LOCATION_TAGS = {"Appointment Location", "Queue Location"}
CARE_UPSS_TAG_NAME = "Care UPSS"
CARE_UPSS_TAG_UUID = "f1fa0d61-ca3e-4cf1-a58b-b3458f7db1b3"
HOSPITAL_LOCATION_UUID = "35d2234e-129a-4c40-abb2-1ae0b72c1602"
CASITA_AZUL_LOCATION_UUID = "35d2234e-129a-4c40-abb2-1ae0b72c1603"
CONSULTA_EXTERNA_LOCATION_UUID = "35d2234e-129a-4c40-abb2-1ae0b2400001"
PHARMACY_LOCATION_UUID = "35d2234e-129a-4c40-abb2-1ae0b2400007"
ADMISSION_ROLE_UUID = "71dcb611-756a-4ad3-a9bb-73b6cfe28066"
# OpenMRS treats the role name as immutable. Keep the production identity stable
# so Initializer can update the UUID-matched role instead of rejecting the row.
ADMISSION_ROLE_NAME = "Admision"
CONSULTA_EXTERNA_ROLE_UUID = "e832327b-7fc2-4e64-a527-7e6ae0cdd041"
CONSULTA_EXTERNA_ROLE_NAME = "SIHSALUS Consulta Externa"
PATIENT_SUMMARY_ROLE_UUID = "564b560e-3fe8-4829-8be4-68ddb40cf106"
PATIENT_SUMMARY_ROLE_NAME = "Application: Uses Patient Summary"
ATTACHMENT_PRIVILEGES = {
    "Add Observations",
    "Create Attachments",
    "View Attachments",
}
ADMISSION_REQUIRED_PRIVILEGES = {
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
    # Scheduling an appointment for a day other than today, and correcting the
    # date a paper appointment was issued on. Both are gated in the frontend;
    # without them Admision can only ever book same-day appointments.
    "app:appointments.issueDate.edit",
    "app:appointments.startDate.edit",
    "app:home",
    "app:home.admision",
    "app:home.citas",
    "app:home.citas.editar",
    "app:home.colasAtencion",
    "app:home.colasAtencion.editar",
    "app:opciones.busquedaPaciente",
    "app:opciones.registrarAcompanante",
    "app:opciones.registrarPaciente",
}


def is_true(value):
    return value.strip().lower() in {"1", "true", "yes"}


def main():
    errors = []
    checked = 0

    for path in sorted(CONFIG_DIR.rglob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))

        if not rows:
            continue

        checked += 1
        header_width = len(rows[0])
        for line_number, row in enumerate(rows[1:], start=2):
            if len(row) != header_width:
                errors.append(
                    f"{path}:{line_number}: expected {header_width} columns, "
                    f"found {len(row)}"
                )

        if path == LOCATION_TAGS_PATH:
            uuid_index = rows[0].index("Uuid")
            name_index = rows[0].index("Name")
            module_tag_rows = {
                name: [
                    row
                    for row in rows[1:]
                    if len(row) > name_index and row[name_index] == name
                ]
                for name in MODULE_LOCATION_TAGS
            }
            for name, matching_rows in sorted(module_tag_rows.items()):
                if len(matching_rows) != 1:
                    errors.append(
                        f"{path}: expected exactly one {name!r} row, found {len(matching_rows)}"
                    )
                elif matching_rows[0][uuid_index]:
                    errors.append(
                        f"{path}: {name!r} must have an empty UUID so Initializer "
                        "resolves the module-created tag by name"
                    )
            care_upss_rows = [
                row
                for row in rows[1:]
                if len(row) > name_index and row[name_index] == CARE_UPSS_TAG_NAME
            ]
            if len(care_upss_rows) != 1:
                errors.append(
                    f"{path}: expected exactly one {CARE_UPSS_TAG_NAME!r} row, "
                    f"found {len(care_upss_rows)}"
                )
            elif care_upss_rows[0][uuid_index] != CARE_UPSS_TAG_UUID:
                errors.append(
                    f"{path}: {CARE_UPSS_TAG_NAME!r} must keep UUID {CARE_UPSS_TAG_UUID}"
                )

        if path == LOCATIONS_PATH:
            uuid_index = rows[0].index("Uuid")
            retired_index = rows[0].index("Void/Retire")
            name_index = rows[0].index("Name")
            parent_index = rows[0].index("Parent")
            active_rows = [
                row
                for row in rows[1:]
                if len(row) == header_width and not is_true(row[retired_index])
            ]
            hospital_rows = [
                row for row in active_rows if row[uuid_index] == HOSPITAL_LOCATION_UUID
            ]
            if len(hospital_rows) != 1:
                errors.append(
                    f"{path}: expected exactly one active Hospital Santa Clotilde row "
                    f"with UUID {HOSPITAL_LOCATION_UUID}, found {len(hospital_rows)}"
                )
            else:
                hospital_row = hospital_rows[0]
                if hospital_row[name_index] != "Hospital Santa Clotilde":
                    errors.append(
                        f"{path}: location {HOSPITAL_LOCATION_UUID} must keep the name "
                        "'Hospital Santa Clotilde'"
                    )

                expected_hospital_tags = {
                    "Tag|Login Location": True,
                    "Tag|Visit Location": False,
                    "Tag|Care UPSS": False,
                    "Tag|Facility Location": True,
                    "Tag|Queue Location": True,
                    "Tag|Admission Location": False,
                    "Tag|Transfer Location": False,
                    "Tag|Appointment Location": False,
                }
                for column, expected in expected_hospital_tags.items():
                    actual = is_true(hospital_row[rows[0].index(column)])
                    if actual != expected:
                        errors.append(
                            f"{path}: Hospital Santa Clotilde must have {column}="
                            f"{'TRUE' if expected else 'FALSE'}"
                        )

            login_index = rows[0].index("Tag|Login Location")
            facility_index = rows[0].index("Tag|Facility Location")
            active_login_rows = [row for row in active_rows if is_true(row[login_index])]
            for row in active_login_rows:
                if not is_true(row[facility_index]):
                    errors.append(
                        f"{path}: active Login Location {row[name_index]} "
                        f"({row[uuid_index]}) must also be a Facility Location"
                    )
            active_login_uuids = [row[uuid_index] for row in active_login_rows]
            if active_login_uuids != [HOSPITAL_LOCATION_UUID]:
                login_locations = ", ".join(
                    f"{row[name_index]} ({row[uuid_index]})" for row in active_login_rows
                )
                errors.append(
                    f"{path}: Hospital Santa Clotilde must be the only active Login "
                    f"Location; found: {login_locations or 'none'}"
                )

            active_location_names = {row[name_index] for row in active_rows}
            for row in active_rows:
                parent = row[parent_index].strip()
                if parent and parent not in active_location_names:
                    errors.append(
                        f"{path}: active location {row[name_index]} references missing or "
                        f"retired parent {parent}"
                    )

            protected_locations = {
                CASITA_AZUL_LOCATION_UUID: {
                    "name": "Casita Azul",
                    "parent": "",
                    "tags": {
                        "Tag|Login Location": False,
                        "Tag|Visit Location": False,
                        "Tag|Care UPSS": False,
                        "Tag|Facility Location": True,
                        "Tag|Queue Location": True,
                        "Tag|Admission Location": False,
                        "Tag|Transfer Location": False,
                        "Tag|Appointment Location": False,
                    },
                },
                CONSULTA_EXTERNA_LOCATION_UUID: {
                    "name": "UPSS - CONSULTA EXTERNA",
                    "parent": "Hospital Santa Clotilde",
                    "tags": {
                        "Tag|Login Location": False,
                        "Tag|Visit Location": True,
                        "Tag|Care UPSS": True,
                        "Tag|Facility Location": False,
                        "Tag|Queue Location": True,
                        "Tag|Admission Location": False,
                        "Tag|Transfer Location": False,
                        "Tag|Appointment Location": True,
                    },
                },
            }
            for location_uuid, expected in protected_locations.items():
                matching_rows = [row for row in active_rows if row[uuid_index] == location_uuid]
                if len(matching_rows) != 1:
                    errors.append(
                        f"{path}: expected exactly one active {expected['name']} row with "
                        f"UUID {location_uuid}, found {len(matching_rows)}"
                    )
                    continue

                location_row = matching_rows[0]
                if location_row[name_index] != expected["name"]:
                    errors.append(
                        f"{path}: location {location_uuid} must keep the name "
                        f"{expected['name']!r}"
                    )
                if location_row[parent_index] != expected["parent"]:
                    errors.append(
                        f"{path}: {expected['name']} must have parent "
                        f"{expected['parent'] or '<root>'}"
                    )
                for column, expected_value in expected["tags"].items():
                    actual = is_true(location_row[rows[0].index(column)])
                    if actual != expected_value:
                        errors.append(
                            f"{path}: {expected['name']} must have {column}="
                            f"{'TRUE' if expected_value else 'FALSE'}"
                    )

            care_upss_index = rows[0].index("Tag|Care UPSS")
            visit_location_index = rows[0].index("Tag|Visit Location")
            active_care_upss_rows = [
                row for row in active_rows if is_true(row[care_upss_index])
            ]
            non_visit_care_upss = [
                row
                for row in active_care_upss_rows
                if not is_true(row[visit_location_index])
            ]
            if non_visit_care_upss:
                errors.append(
                    f"{path}: every active Care UPSS must also be a Visit Location; "
                    "invalid UUIDs: "
                    + ", ".join(
                        sorted(row[uuid_index] for row in non_visit_care_upss)
                    )
                )

            pharmacy_rows = [
                row for row in active_rows if row[uuid_index] == PHARMACY_LOCATION_UUID
            ]
            if len(pharmacy_rows) != 1:
                errors.append(
                    f"{path}: expected exactly one active UPSS - FARMACIA row with "
                    f"UUID {PHARMACY_LOCATION_UUID}, found {len(pharmacy_rows)}"
                )
            else:
                pharmacy_row = pharmacy_rows[0]
                for column in ("Tag|Visit Location", "Tag|Queue Location"):
                    if not is_true(pharmacy_row[rows[0].index(column)]):
                        errors.append(
                            f"{path}: UPSS - FARMACIA must have {column}=TRUE"
                        )
                if is_true(pharmacy_row[login_index]):
                    errors.append(
                        f"{path}: UPSS - FARMACIA must not be a Login Location"
                    )

        if path == ROLES_CORE_PATH:
            uuid_index = rows[0].index("Uuid")
            role_index = rows[0].index("Role name")
            inherited_roles_index = rows[0].index("Inherited roles")
            privileges_index = rows[0].index("Privileges")
            patient_summary_rows = [
                row
                for row in rows[1:]
                if len(row) > role_index
                and row[role_index] == PATIENT_SUMMARY_ROLE_NAME
            ]
            if len(patient_summary_rows) != 1:
                errors.append(
                    f"{path}: expected exactly one {PATIENT_SUMMARY_ROLE_NAME!r} role, "
                    f"found {len(patient_summary_rows)}"
                )
            else:
                patient_summary_row = patient_summary_rows[0]
                if patient_summary_row[uuid_index] != PATIENT_SUMMARY_ROLE_UUID:
                    errors.append(
                        f"{path}: {PATIENT_SUMMARY_ROLE_NAME!r} must keep UUID "
                        f"{PATIENT_SUMMARY_ROLE_UUID}"
                    )
                patient_summary_privileges = {
                    privilege.strip()
                    for privilege in patient_summary_row[privileges_index].split(";")
                    if privilege.strip()
                }
                if "View Attachments" not in patient_summary_privileges:
                    errors.append(
                        f"{path}: {PATIENT_SUMMARY_ROLE_NAME!r} must include "
                        "View Attachments"
                    )
                if "Create Attachments" in patient_summary_privileges:
                    errors.append(
                        f"{path}: {PATIENT_SUMMARY_ROLE_NAME!r} must not include "
                        "Create Attachments"
                    )
            admission_rows = [
                row
                for row in rows[1:]
                if len(row) > role_index and row[role_index] == ADMISSION_ROLE_NAME
            ]
            if len(admission_rows) != 1:
                errors.append(
                    f"{path}: expected exactly one {ADMISSION_ROLE_NAME!r} role, "
                    f"found {len(admission_rows)}"
                )
            else:
                admission_row = admission_rows[0]
                if admission_row[uuid_index] != ADMISSION_ROLE_UUID:
                    errors.append(
                        f"{path}: {ADMISSION_ROLE_NAME!r} must keep UUID {ADMISSION_ROLE_UUID}"
                    )
                inherited_roles = admission_row[inherited_roles_index].strip()
                if inherited_roles:
                    errors.append(
                        f"{path}: {ADMISSION_ROLE_NAME!r} must not inherit roles; "
                        f"found: {inherited_roles}"
                    )
                privileges = {
                    privilege.strip()
                    for privilege in admission_row[privileges_index].split(";")
                    if privilege.strip()
                }
                missing_privileges = ADMISSION_REQUIRED_PRIVILEGES - privileges
                if missing_privileges:
                    errors.append(
                        f"{path}: {ADMISSION_ROLE_NAME!r} is missing required privileges: "
                        f"{', '.join(sorted(missing_privileges))}"
                    )
                unapproved_privileges = privileges - ADMISSION_REQUIRED_PRIVILEGES
                if unapproved_privileges:
                    errors.append(
                        f"{path}: {ADMISSION_ROLE_NAME!r} has unapproved privileges: "
                        f"{', '.join(sorted(unapproved_privileges))}"
                    )

            consulta_externa_rows = [
                row
                for row in rows[1:]
                if len(row) > role_index
                and row[role_index] == CONSULTA_EXTERNA_ROLE_NAME
            ]
            if len(consulta_externa_rows) != 1:
                errors.append(
                    f"{path}: expected exactly one {CONSULTA_EXTERNA_ROLE_NAME!r} role, "
                    f"found {len(consulta_externa_rows)}"
                )
            else:
                consulta_externa_row = consulta_externa_rows[0]
                if consulta_externa_row[uuid_index] != CONSULTA_EXTERNA_ROLE_UUID:
                    errors.append(
                        f"{path}: {CONSULTA_EXTERNA_ROLE_NAME!r} must keep UUID "
                        f"{CONSULTA_EXTERNA_ROLE_UUID}"
                    )
                consulta_externa_privileges = {
                    privilege.strip()
                    for privilege in consulta_externa_row[privileges_index].split(";")
                    if privilege.strip()
                }
                missing_attachment_privileges = (
                    ATTACHMENT_PRIVILEGES - consulta_externa_privileges
                )
                if missing_attachment_privileges:
                    errors.append(
                        f"{path}: {CONSULTA_EXTERNA_ROLE_NAME!r} is missing "
                        "attachment privileges: "
                        f"{', '.join(sorted(missing_attachment_privileges))}"
                    )

    if errors:
        print("CSV width validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "Validated column counts, module-owned location tags, the single hospital "
        "login location, and clinical role invariants for "
        f"{checked} CSV files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
