#!/usr/bin/env python3
import csv
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


CONFIG_DIR = Path("configuration/backend_configuration")
PRIVILEGES_PATH = CONFIG_DIR / "privileges" / "privileges_core-demo.csv"
ATTRIBUTE_TYPES_PATH = CONFIG_DIR / "attributetypes" / "attribute_types.csv"
GLOBAL_PROPERTIES_PATH = (
    CONFIG_DIR / "globalproperties" / "globalproperties-sihsalus.xml"
)
SERVICE_DEFINITIONS_PATH = (
    CONFIG_DIR / "appointmentservicedefinitions" / "servicedefinitions.csv"
)
SERVICE_TYPES_PATH = CONFIG_DIR / "appointmentservicetypes" / "servicetypes.csv"
SPECIALITIES_PATH = CONFIG_DIR / "appointmentspecialities" / "specialities.csv"
LOCATIONS_PATH = CONFIG_DIR / "locations" / "sihsalus-locations.csv"
QUEUES_PATH = CONFIG_DIR / "queues" / "sihsalus-queues.csv"
VISIT_TYPES_PATH = CONFIG_DIR / "visittypes" / "sihsalus-visittypes.csv"
QUEUE_SERVICE_CONCEPTS_PATH = CONFIG_DIR / "concepts" / "queue_service_concepts.csv"
QUEUE_SERVICE_CONCEPT_SET_PATH = (
    CONFIG_DIR / "conceptsets" / "queue_service_concepts.csv"
)
CARE_ROUTING_CONTRACT_PATH = Path("docs/contracts/hsc-care-routing.csv")

OBSOLETE_LIFECYCLE_PRIVILEGE_UUID = "ef67b22e-25c8-4d0f-ab6e-427be7f72cc4"
OBSOLETE_LIFECYCLE_PRIVILEGE = "Manage Appointment Queue Lifecycle"
QUEUE_ENTRY_MUTATION_PRIVILEGE = "Manage Queue Entries"
GENERATE_FUA_PRIVILEGE_UUID = "2293389f-8595-491f-b842-5da867f59608"
GENERATE_FUA_PRIVILEGE = "Generate Fua from Visit"
QUEUE_NUMBER_ATTRIBUTE_UUID = "06a0b8c6-cbdf-4b42-9cbd-871129db8758"
APPOINTMENT_UUID_ATTRIBUTE_UUID = "193508ab-20c6-5291-9f23-0257335eaabd"
PROVIDER_SCHEDULING_CATEGORY_ATTRIBUTE_UUID = (
    "3961cbdd-3240-4b70-99ca-5f63af488b15"
)
OBSOLETE_PARENT_VISIT_TYPE_ATTRIBUTE_UUID = "d6c9e7a5-8134-49e3-a2c5-b8f4c3d2e1a9"
QUEUE_SERVICE_CONCEPT_SET_UUID = "4bf3f465-ac91-44fa-9b1f-173daf0c89a0"
GENERIC_AMBULATORY_VISIT_TYPE_UUID = "b1f0e8a1-9c5d-4f0e-8892-81f3140fbc09"
HOSPITALIZATION_VISIT_TYPE_UUID = "e4c8b6d9-7f3a-4e7b-91a2-58b9f6c2d4b5"
APPROVED_ACTIVE_VISIT_TYPE_UUIDS = {
    GENERIC_AMBULATORY_VISIT_TYPE_UUID,
    "23939157-9af0-457b-8f6c-211eb5459311",
    HOSPITALIZATION_VISIT_TYPE_UUID,
    "c2a1d3e2-4b8f-4326-94d9-7f6c9a1b7c98",
    "c80410d7-e0cb-488f-9b23-be78bd244548",
}
DENTAL_SERVICE_UUID = "b3c2d4e5-f6a7-48d9-93e1-8f7a6b5c4d02"
GENERAL_DENTISTRY_CATEGORY_UUID = "a0d4e64e-eb63-4271-bdf1-ffa10392c282"
CBMF_SPECIALITY_UUID = "4e6f8d2c-3a5b-495e-9d78-2f4c6a8b1e09"
OBSTETRIC_SERVICE_UUID = "a6d7f9b3-2c5e-48d1-93e4-7f8a6b5c2d02"
NUTRITION_SERVICE_UUID = "3663f478-80fb-4585-b92f-7f82873198ee"
HOSPITALIZATION_SURGERY_SERVICE_UUID = "115b9e98-0bb4-4791-afa6-d21d071cfd87"
TOPICAL_SERVICE_UUID = "d4e5f6a7-b8c9-41e2-93f3-1a9b8c7d6e04"
NEWBORN_SERVICE_UUID = "f7a8b9c0-d1e2-43f4-93e5-3b1a9c8d7e06"
OUTPATIENT_LOCATION_UUID = "35d2234e-129a-4c40-abb2-1ae0b2400001"
HOSPITALIZATION_LOCATION_UUID = "35d2234e-129a-4c40-abb2-1ae0b2400002"

TARGET_ROLES = {
    "71dcb611-756a-4ad3-a9bb-73b6cfe28066": "Admision",
    "75abd7e6-9dcd-446d-8468-04837f314c4f": "Application: Register Appointments",
    "72dd34eb-0295-4684-ab3f-1ccb0cfaab20": "Application: Gestionar Colas Servicio",
    "cf627580-0372-47fc-87b6-319d4a4d4973": "Personal de Emergencia",
}
CLINICAL_ROLE_UUID = "e832327b-7fc2-4e64-a527-7e6ae0cdd041"
CLINICAL_ROLE_NAME = "SIHSALUS Consulta Externa"
FUA_OPERATOR_ROLE_UUID = "68256ae6-d81c-4ef9-bda9-fc1471022cd3"
FUA_OPERATOR_ROLE_NAME = "Digitadores FUA"
SUPER_ADMIN_ROLE_UUID = "227fa2ff-f7ed-49f8-9fec-3ca63814df9e"
# Explicit hospital baseline: support is an administrative profile and is not
# a general inheritance parent. Canonical admission has no queue-clear supplement.
# See hospital-access-profiles.json.
HOSPITAL_SUPPORT_ROLE_UUID = "ac0ac0e6-2520-4181-9023-7891a82dabd2"
QUEUE_READER_ROLE_UUID = "7f9a9321-0c35-4130-895c-dbca7401be64"
QUEUE_READER_ROLE_NAME = "Colas Servicio Medico"
NURSE_ROLE_UUID = "e70120b5-000c-4e6f-94a5-a139c2b4b25c"
NURSE_ROLE_NAME = "Enfermera"
TRIAGE_NURSE_ROLE_UUID = "c3c9b940-156f-4eaf-83b7-f11db420c51c"
TRIAGE_NURSE_ROLE_NAME = "SIHSALUS Enfermero Triaje"
QUEUE_ATTENTION_EDITOR_ROLE_UUID = "64b3168f-44c5-41e7-9ab4-8f9f338ed4c7"
COMPANION_REGISTRATION_PRIVILEGE = "app:opciones.registrarAcompanante"
QUEUE_CLEAR_PRIVILEGE = "app:home.colasAtencion.limpiar"
VISIT_NOTES_EDIT_PRIVILEGE = "app:hoja.clinica.resumenConsulta.editar"
VISIT_NOTES_EDIT_ROLE_UUID = "82045d24-3a94-4481-bd98-9b5136058034"
VISIT_NOTES_EDIT_ROLE_PRIVILEGES = {
    VISIT_NOTES_EDIT_PRIVILEGE,
    "Get Encounters",
    "Get Concepts",
    "Get Providers",
    "Get Forms",
    "Get Encounter Roles",
    "Get Locations",
    "Get Diagnoses",
    "Get Observations",
    "Add Encounters",
    "Edit Encounters",
    "Add Observations",
    "Edit Observations",
    "Edit Diagnoses",
}
VISIT_NOTES_EDIT_ROLE_FORBIDDEN_PRIVILEGES = {
    "Add Diagnoses",
    "Delete Diagnoses",
}
FRONTEND_UI_PRIVILEGES = {
    "app:home.tabla.consultas.activas": "4cbcf36e-ea9b-4b55-86eb-5e5061922410",
    "app:hoja.clinica.resumenConsulta": "017238da-7b23-48ae-934e-f8eb1835d39a",
    VISIT_NOTES_EDIT_PRIVILEGE: "7e6ad9c9-3842-4a99-95ba-bb16fa2a7bfd",
    "app:hoja.clinica.formulariosClinicos": "b3e9c57b-82a9-4d27-a568-763bd7ac1918",
    "app:hoja.clinica.canastaOrdenes": "4fe1d19e-615e-4b0b-ac16-68ad57ef61d0",
    "app:hoja.clinica.listaTareas": "1314dc5d-e183-4787-8400-67c98d11b870",
    COMPANION_REGISTRATION_PRIVILEGE: "5bde5891-1a46-41d8-a200-e1125bca846a",
    QUEUE_CLEAR_PRIVILEGE: "03d6a1bf-ae86-4d5b-a851-9d6b8be30b2f",
}
FRONTEND_UI_ROLE_GRANTS = {
    CLINICAL_ROLE_UUID: set(FRONTEND_UI_PRIVILEGES)
    - {COMPANION_REGISTRATION_PRIVILEGE, QUEUE_CLEAR_PRIVILEGE},
    "71dcb611-756a-4ad3-a9bb-73b6cfe28066": {
        COMPANION_REGISTRATION_PRIVILEGE,
    },
    "72dd34eb-0295-4684-ab3f-1ccb0cfaab20": {
        QUEUE_CLEAR_PRIVILEGE,
    },
    "cf627580-0372-47fc-87b6-319d4a4d4973": {
        "app:home.tabla.consultas.activas",
        "app:hoja.clinica.formulariosClinicos",
        COMPANION_REGISTRATION_PRIVILEGE,
    },
    QUEUE_ATTENTION_EDITOR_ROLE_UUID: {
        COMPANION_REGISTRATION_PRIVILEGE,
        QUEUE_CLEAR_PRIVILEGE,
    },
    VISIT_NOTES_EDIT_ROLE_UUID: VISIT_NOTES_EDIT_ROLE_PRIVILEGES,
}
SENSITIVE_UI_PRIVILEGE_ASSIGNMENTS = {
    VISIT_NOTES_EDIT_PRIVILEGE: {
        CLINICAL_ROLE_UUID,
        VISIT_NOTES_EDIT_ROLE_UUID,
        HOSPITAL_SUPPORT_ROLE_UUID,
    },
    COMPANION_REGISTRATION_PRIVILEGE: {
        "71dcb611-756a-4ad3-a9bb-73b6cfe28066",
        "cf627580-0372-47fc-87b6-319d4a4d4973",
        QUEUE_ATTENTION_EDITOR_ROLE_UUID,
        HOSPITAL_SUPPORT_ROLE_UUID,
    },
    QUEUE_CLEAR_PRIVILEGE: {
        "72dd34eb-0295-4684-ab3f-1ccb0cfaab20",
        QUEUE_ATTENTION_EDITOR_ROLE_UUID,
        HOSPITAL_SUPPORT_ROLE_UUID,
    },
}
ALLOWED_DIRECT_QUEUE_MUTATION_ASSIGNMENTS = set(TARGET_ROLES) | {
    CLINICAL_ROLE_UUID,
    TRIAGE_NURSE_ROLE_UUID,
    SUPER_ADMIN_ROLE_UUID,
    HOSPITAL_SUPPORT_ROLE_UUID,
}
ALLOWED_DIRECT_FUA_GENERATION_ASSIGNMENTS = {
    FUA_OPERATOR_ROLE_UUID,
    SUPER_ADMIN_ROLE_UUID,
    HOSPITAL_SUPPORT_ROLE_UUID,
}
COMMON_OPERATIONAL_PRIVILEGES = {
    QUEUE_ENTRY_MUTATION_PRIVILEGE,
    "Add Visits",
    "Edit Visits",
    "Get Concepts",
    "Get Locations",
    "Get Queue Entries",
    "Get Queues",
    "Get Visit Attribute Types",
    "Get Visit Types",
    "Get Visits",
    "View Locations",
}
ROLE_REQUIRED_PRIVILEGES = {
    "71dcb611-756a-4ad3-a9bb-73b6cfe28066": {
        "Manage Appointments",
        "Manage Own Appointments",
        "View Appointments",
        "app:home.citas.editar",
        "app:home.colasAtencion",
        "app:home.colasAtencion.editar",
        COMPANION_REGISTRATION_PRIVILEGE,
    },
    "75abd7e6-9dcd-446d-8468-04837f314c4f": {
        "Manage Appointments",
        "Manage Own Appointments",
        "View Appointments",
        "app:home.citas.editar",
    },
    "72dd34eb-0295-4684-ab3f-1ccb0cfaab20": {
        "View Appointments",
        "app:home.colasAtencion",
        "app:home.colasAtencion.editar",
        QUEUE_CLEAR_PRIVILEGE,
    },
    "cf627580-0372-47fc-87b6-319d4a4d4973": {
        "Add Encounters",
        "Add Observations",
        "Add Patient Identifiers",
        "Add Patients",
        "Add People",
        "Edit Encounters",
        "Edit Observations",
        "Form Entry",
        "Get Encounter Types",
        "Get Encounters",
        "Get Forms",
        "Get Identifier Types",
        "Get Observations",
        "Get Patient Identifiers",
        "Get Patients",
        "Get People",
        "View Encounters",
        "View Forms",
        "View Identifier Types",
        "View Observations",
        "View Patient Identifiers",
        "View Patients",
        "View People",
        "app:home.emergencia",
        "app:home.emergencia.editar",
        "app:opciones.registrarPaciente",
        COMPANION_REGISTRATION_PRIVILEGE,
    },
}
ROLE_FORBIDDEN_PRIVILEGES = {
    "71dcb611-756a-4ad3-a9bb-73b6cfe28066": {
        "Add HL7 Inbound Queue",
        "Configure Visits",
        "Delete Visits",
        "Get Global Properties",
        "Get HL7 Inbound Queue",
        "Get Observations",
        "Get Patient Programs",
        "Get Provider Attribute Types",
        "Get Provider Roles",
        "Get Queue Rooms",
        "Manage Appointment Services",
        "Manage Appointment Specialities",
        "Manage Queue Rooms",
        "Manage Queues",
        "Manage Visit Attribute Types",
        "Manage Visit Types",
        "Purge Queue Entries",
        "Purge Queue Rooms",
        "Purge Queues",
        "Reset Appointment Status",
        "View Global Properties",
        "app:appointments:manageServiceAvailability",
        "app:appointments:manageServices",
        "app:hoja.clinica",
        "app:hoja.clinica.citas",
        "app:hoja.clinica.citas.editar",
        "app:hoja.clinica.resumen",
        "app:hoja.clinica.visitas",
        "app:hoja.clinica.visitas.editar",
        "app:home.editar",
        QUEUE_CLEAR_PRIVILEGE,
    },
    "75abd7e6-9dcd-446d-8468-04837f314c4f": {
        "Get Global Properties",
        "Manage Queue Rooms",
        "Manage Queues",
        "Purge Queue Entries",
        "Purge Queue Rooms",
        "Reset Appointment Status",
        "View Global Properties",
        "app:home.colasAtencion",
        "app:home.colasAtencion.editar",
        COMPANION_REGISTRATION_PRIVILEGE,
        QUEUE_CLEAR_PRIVILEGE,
    },
    "72dd34eb-0295-4684-ab3f-1ccb0cfaab20": {
        "Get Global Properties",
        "Manage Appointments",
        "Manage Own Appointments",
        "Purge Queue Entries",
        "Purge Queue Rooms",
        "Reset Appointment Status",
        "View Global Properties",
        COMPANION_REGISTRATION_PRIVILEGE,
    },
    "cf627580-0372-47fc-87b6-319d4a4d4973": {
        "Delete Encounters",
        "Delete Observations",
        "Delete Patients",
        "Delete Visits",
        "Get Global Properties",
        "Manage Appointment Services",
        "Manage Appointment Specialities",
        "Manage Appointments",
        "Manage Global Properties",
        "Manage Queue Rooms",
        "Manage Queues",
        "Purge Queue Entries",
        "Purge Queue Rooms",
        "Reset Appointment Status",
        "View Global Properties",
        QUEUE_CLEAR_PRIVILEGE,
    },
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def is_true(value):
    return value.strip().lower() in {"1", "true", "yes"}


def is_retired(value):
    return is_true(value)


def split_privileges(value):
    return {part.strip() for part in value.split(";") if part.strip()}


def validate_privilege_and_roles(errors):
    privilege_rows = read_csv(PRIVILEGES_PATH)
    obsolete_privilege_rows = [
        row
        for row in privilege_rows
        if row["Uuid"] == OBSOLETE_LIFECYCLE_PRIVILEGE_UUID
        or row["Privilege name"] == OBSOLETE_LIFECYCLE_PRIVILEGE
    ]
    if obsolete_privilege_rows:
        errors.append(
            f"{PRIVILEGES_PATH}: remove obsolete privilege "
            f"{OBSOLETE_LIFECYCLE_PRIVILEGE!r}; OpenMRS has no endpoint that authorizes it"
        )

    matching_fua_uuid = [
        row for row in privilege_rows if row["Uuid"] == GENERATE_FUA_PRIVILEGE_UUID
    ]
    matching_fua_name = [
        row for row in privilege_rows if row["Privilege name"] == GENERATE_FUA_PRIVILEGE
    ]
    if len(matching_fua_uuid) != 1 or len(matching_fua_name) != 1:
        errors.append(
            f"{PRIVILEGES_PATH}: FUA generation privilege must have one UUID and one name row"
        )
    elif matching_fua_uuid[0] is not matching_fua_name[0]:
        errors.append(
            f"{PRIVILEGES_PATH}: {GENERATE_FUA_PRIVILEGE!r} must use UUID "
            f"{GENERATE_FUA_PRIVILEGE_UUID}"
        )

    for privilege_name, privilege_uuid in FRONTEND_UI_PRIVILEGES.items():
        matching_uuid = [row for row in privilege_rows if row["Uuid"] == privilege_uuid]
        matching_name = [
            row for row in privilege_rows if row["Privilege name"] == privilege_name
        ]
        if len(matching_uuid) != 1 or len(matching_name) != 1:
            errors.append(
                f"{PRIVILEGES_PATH}: frontend privilege {privilege_name!r} must have "
                "one UUID and one name row"
            )
        elif matching_uuid[0] is not matching_name[0]:
            errors.append(
                f"{PRIVILEGES_PATH}: {privilege_name!r} must use UUID {privilege_uuid}"
            )

    role_rows = []
    for path in sorted((CONFIG_DIR / "roles").glob("*.csv")):
        for row in read_csv(path):
            row["_path"] = str(path)
            role_rows.append(row)

    roles_by_name = {row["Role name"]: row for row in role_rows}
    effective_privilege_cache = {}

    def effective_privileges(role, stack=()):
        role_uuid = role.get("Uuid")
        if role_uuid in effective_privilege_cache:
            return effective_privilege_cache[role_uuid]
        role_name = role.get("Role name", "")
        if role_name in stack:
            return set()

        privileges = split_privileges(role.get("Privileges", ""))
        for inherited_name in split_privileges(role.get("Inherited roles", "")):
            inherited = roles_by_name.get(inherited_name)
            if inherited is not None:
                privileges |= effective_privileges(inherited, (*stack, role_name))
        effective_privilege_cache[role_uuid] = privileges
        return privileges

    for role_uuid, required_privileges in FRONTEND_UI_ROLE_GRANTS.items():
        matching_roles = [row for row in role_rows if row["Uuid"] == role_uuid]
        if len(matching_roles) != 1:
            errors.append(
                f"roles: expected exactly one frontend UI role row with UUID {role_uuid}"
            )
            continue
        role = matching_roles[0]
        missing = required_privileges - split_privileges(role.get("Privileges", ""))
        if missing:
            errors.append(
                f"{role['_path']}: {role['Role name']!r} is missing frontend workflow "
                "privileges: " + ", ".join(sorted(missing))
            )

        if role_uuid == VISIT_NOTES_EDIT_ROLE_UUID:
            forbidden = VISIT_NOTES_EDIT_ROLE_FORBIDDEN_PRIVILEGES & split_privileges(
                role.get("Privileges", "")
            )
            if forbidden:
                errors.append(
                    f"{role['_path']}: {role['Role name']!r} has diagnosis privileges "
                    "outside the Visit Notes save/void contract: "
                    + ", ".join(sorted(forbidden))
                )

    for privilege, approved_role_uuids in SENSITIVE_UI_PRIVILEGE_ASSIGNMENTS.items():
        assigned_role_uuids = {
            row["Uuid"]
            for row in role_rows
            if privilege in split_privileges(row.get("Privileges", ""))
        }
        if assigned_role_uuids != approved_role_uuids:
            errors.append(
                f"{privilege!r} direct assignments must match its least-privilege "
                "allowlist; found UUIDs: " + ", ".join(sorted(assigned_role_uuids))
            )

    obsolete_assignments = {
        row["Uuid"]
        for row in role_rows
        if OBSOLETE_LIFECYCLE_PRIVILEGE
        in split_privileges(row.get("Privileges", ""))
    }
    if obsolete_assignments:
        errors.append(
            f"roles: remove obsolete privilege {OBSOLETE_LIFECYCLE_PRIVILEGE!r} from "
            "role UUIDs: " + ", ".join(sorted(obsolete_assignments))
        )

    direct_queue_mutation_assignments = {
        row["Uuid"]
        for row in role_rows
        if QUEUE_ENTRY_MUTATION_PRIVILEGE
        in split_privileges(row.get("Privileges", ""))
    }
    if (
        direct_queue_mutation_assignments
        != ALLOWED_DIRECT_QUEUE_MUTATION_ASSIGNMENTS
    ):
        errors.append(
            f"{QUEUE_ENTRY_MUTATION_PRIVILEGE!r} direct assignments must match the "
            "approved admission, appointment check-in, queue, emergency, clinical, "
            "triage, and backend-admin roles; found UUIDs: "
            + ", ".join(sorted(direct_queue_mutation_assignments))
        )

    direct_fua_generation_assignments = {
        row["Uuid"]
        for row in role_rows
        if GENERATE_FUA_PRIVILEGE in split_privileges(row.get("Privileges", ""))
    }
    if direct_fua_generation_assignments != ALLOWED_DIRECT_FUA_GENERATION_ASSIGNMENTS:
        errors.append(
            "FUA generation privilege direct assignments must match the approved FUA "
            "operator and backend-admin roles; found UUIDs: "
            + ", ".join(sorted(direct_fua_generation_assignments))
        )

    for role_uuid, expected_name in TARGET_ROLES.items():
        matching_roles = [row for row in role_rows if row["Uuid"] == role_uuid]
        if len(matching_roles) != 1:
            errors.append(
                f"roles: expected exactly one {expected_name!r} row with UUID {role_uuid}"
            )
            continue

        row = matching_roles[0]
        if row["Role name"] != expected_name:
            errors.append(
                f"{row['_path']}: role UUID {role_uuid} must be named {expected_name!r}"
            )
        privileges = effective_privileges(row)
        required = COMMON_OPERATIONAL_PRIVILEGES | ROLE_REQUIRED_PRIVILEGES[role_uuid]
        missing = required - privileges
        forbidden = ROLE_FORBIDDEN_PRIVILEGES[role_uuid] & privileges
        if missing:
            errors.append(
                f"{row['_path']}: {expected_name!r} is missing workflow privileges: "
                + ", ".join(sorted(missing))
            )
        if forbidden:
            errors.append(
                f"{row['_path']}: {expected_name!r} has forbidden administrative privileges: "
                + ", ".join(sorted(forbidden))
            )

    clinical_matches = [row for row in role_rows if row["Uuid"] == CLINICAL_ROLE_UUID]
    if len(clinical_matches) != 1:
        errors.append(
            f"roles: expected exactly one {CLINICAL_ROLE_NAME!r} row with UUID "
            f"{CLINICAL_ROLE_UUID}"
        )
    else:
        clinical = clinical_matches[0]
        privileges = split_privileges(clinical["Privileges"])
        required = {
            "Add Visits",
            "Edit People",
            "Edit Visits",
            "Get Queue Entries",
            "Get Queues",
            "Get Visits",
            "Manage Appointments",
            "Manage Own Appointments",
            QUEUE_ENTRY_MUTATION_PRIVILEGE,
            "View Appointments",
            "app:hoja.clinica.citas.editar",
            "app:hoja.clinica.estadoVitalPaciente",
        }
        forbidden = {
            COMPANION_REGISTRATION_PRIVILEGE,
            "Get Global Properties",
            "Manage Fua",
            "Manage Queue Rooms",
            "Manage Queues",
            "Purge Queue Entries",
            "Update Fua",
            "View Global Properties",
            QUEUE_CLEAR_PRIVILEGE,
        }
        if required - privileges:
            errors.append(
                f"{clinical['_path']}: {CLINICAL_ROLE_NAME!r} is missing workflow "
                "privileges: " + ", ".join(sorted(required - privileges))
            )
        if forbidden & privileges:
            errors.append(
                f"{clinical['_path']}: {CLINICAL_ROLE_NAME!r} has forbidden queue "
                "administration privileges: "
                + ", ".join(sorted(forbidden & privileges))
            )

    queue_reader_matches = [
        row for row in role_rows if row["Uuid"] == QUEUE_READER_ROLE_UUID
    ]
    if len(queue_reader_matches) != 1:
        errors.append(
            f"roles: expected exactly one {QUEUE_READER_ROLE_NAME!r} row with UUID "
            f"{QUEUE_READER_ROLE_UUID}"
        )
    else:
        queue_reader = queue_reader_matches[0]
        privileges = split_privileges(queue_reader["Privileges"])
        required = {
            "Get Queue Entries",
            "Get Queue Rooms",
            "Get Queues",
            "app:home.colasAtencion",
        }
        forbidden = {
            "Add Visits",
            COMPANION_REGISTRATION_PRIVILEGE,
            "Edit Visits",
            QUEUE_ENTRY_MUTATION_PRIVILEGE,
            "Manage Queue Rooms",
            "Manage Queues",
            "Purge Queue Entries",
            "Purge Queue Rooms",
            "app:home.colasAtencion.editar",
            QUEUE_CLEAR_PRIVILEGE,
        }
        if required - privileges:
            errors.append(
                f"{queue_reader['_path']}: {QUEUE_READER_ROLE_NAME!r} is missing "
                "read-only queue privileges: "
                + ", ".join(sorted(required - privileges))
            )
        if forbidden & privileges:
            errors.append(
                f"{queue_reader['_path']}: {QUEUE_READER_ROLE_NAME!r} has forbidden "
                "queue mutation privileges: "
                + ", ".join(sorted(forbidden & privileges))
            )

    nurse_matches = [row for row in role_rows if row["Uuid"] == NURSE_ROLE_UUID]
    if len(nurse_matches) != 1:
        errors.append(
            f"roles: expected exactly one {NURSE_ROLE_NAME!r} row with UUID "
            f"{NURSE_ROLE_UUID}"
        )
    else:
        nurse = nurse_matches[0]
        inherited_roles = {
            role.strip()
            for role in nurse.get("Inherited roles", "").split(";")
            if role.strip()
        }
        if CLINICAL_ROLE_NAME not in inherited_roles:
            errors.append(
                f"{nurse['_path']}: {NURSE_ROLE_NAME!r} must inherit "
                f"{CLINICAL_ROLE_NAME!r} to preserve visit and queue closure access"
            )

    triage_nurse_matches = [
        row for row in role_rows if row["Uuid"] == TRIAGE_NURSE_ROLE_UUID
    ]
    if len(triage_nurse_matches) != 1:
        errors.append(
            f"roles: expected exactly one {TRIAGE_NURSE_ROLE_NAME!r} row with UUID "
            f"{TRIAGE_NURSE_ROLE_UUID}"
        )
    else:
        triage_nurse = triage_nurse_matches[0]
        privileges = split_privileges(triage_nurse["Privileges"])
        required = {
            "Add Encounters",
            "Add Observations",
            "Edit Encounters",
            "Edit Observations",
            "Edit Visits",
            "Get Queue Entries",
            "Get Queues",
            "Get Visits",
            QUEUE_ENTRY_MUTATION_PRIVILEGE,
            "View Appointments",
            "app:hoja.clinica.signosVitales",
            "app:hoja.clinica.signosVitales.editar",
        }
        forbidden = {
            COMPANION_REGISTRATION_PRIVILEGE,
            "Manage Fua",
            "Manage Queue Rooms",
            "Manage Queues",
            "Purge Queue Entries",
            "Purge Queue Rooms",
            QUEUE_CLEAR_PRIVILEGE,
        }
        if required - privileges:
            errors.append(
                f"{triage_nurse['_path']}: {TRIAGE_NURSE_ROLE_NAME!r} is missing "
                "triage vitals privileges: " + ", ".join(sorted(required - privileges))
            )
        if forbidden & privileges:
            errors.append(
                f"{triage_nurse['_path']}: {TRIAGE_NURSE_ROLE_NAME!r} has forbidden "
                "queue administration privileges: "
                + ", ".join(sorted(forbidden & privileges))
            )

    fua_operator_matches = [
        row for row in role_rows if row["Uuid"] == FUA_OPERATOR_ROLE_UUID
    ]
    if len(fua_operator_matches) != 1:
        errors.append(
            f"roles: expected exactly one {FUA_OPERATOR_ROLE_NAME!r} row with UUID "
            f"{FUA_OPERATOR_ROLE_UUID}"
        )
    else:
        fua_operator = fua_operator_matches[0]
        privileges = split_privileges(fua_operator["Privileges"])
        required = {
            GENERATE_FUA_PRIVILEGE,
            "Fua Privilege",
            "Get Visits",
            "Manage Fua",
            "Read Fua",
            "Update Fua",
            "app:home",
            "app:home.fua",
            "app:home.fua.editar",
        }
        forbidden = {
            "Delete Fua",
            "Delete Visits",
            "Get Global Properties",
            "Manage Global Properties",
            "View Global Properties",
        }
        if required - privileges:
            errors.append(
                f"{fua_operator['_path']}: {FUA_OPERATOR_ROLE_NAME!r} is missing FUA "
                "workflow privileges: " + ", ".join(sorted(required - privileges))
            )
        if forbidden & privileges:
            errors.append(
                f"{fua_operator['_path']}: {FUA_OPERATOR_ROLE_NAME!r} has forbidden "
                "administrative privileges: "
                + ", ".join(sorted(forbidden & privileges))
            )


def validate_visit_attribute_metadata(errors):
    rows = read_csv(ATTRIBUTE_TYPES_PATH)
    matches = [row for row in rows if row["Uuid"] == QUEUE_NUMBER_ATTRIBUTE_UUID]
    if len(matches) != 1:
        errors.append(
            f"{ATTRIBUTE_TYPES_PATH}: expected one queue-number visit attribute row"
        )
    else:
        row = matches[0]
        expected = {
            "Void/Retire": "",
            "Entity name": "Visit",
            "Name": "N\u00famero de turno de cola",
            "Min occurs": "0",
            "Max occurs": "1",
            "Datatype classname": "org.openmrs.customdatatype.datatype.FreeTextDatatype",
        }
        for column, value in expected.items():
            if row[column] != value:
                errors.append(
                    f"{ATTRIBUTE_TYPES_PATH}: queue-number attribute {column!r} must be "
                    f"{value!r}, found {row[column]!r}"
                )

    appointment_matches = [
        row for row in rows if row["Uuid"] == APPOINTMENT_UUID_ATTRIBUTE_UUID
    ]
    if len(appointment_matches) != 1:
        errors.append(
            f"{ATTRIBUTE_TYPES_PATH}: expected one appointment-UUID visit attribute row"
        )
    else:
        row = appointment_matches[0]
        expected = {
            "Void/Retire": "",
            "Entity name": "Visit",
            "Name": "UUID de cita vinculada",
            "Min occurs": "0",
            "Max occurs": "",
            "Datatype classname": "org.openmrs.customdatatype.datatype.FreeTextDatatype",
        }
        for column, value in expected.items():
            if row[column] != value:
                errors.append(
                    f"{ATTRIBUTE_TYPES_PATH}: appointment-UUID attribute {column!r} "
                    f"must be {value!r}, found {row[column]!r}"
                )

    provider_category_matches = [
        row
        for row in rows
        if row["Uuid"] == PROVIDER_SCHEDULING_CATEGORY_ATTRIBUTE_UUID
    ]
    if len(provider_category_matches) != 1:
        errors.append(
            f"{ATTRIBUTE_TYPES_PATH}: expected one provider scheduling-category row"
        )
    else:
        row = provider_category_matches[0]
        expected = {
            "Void/Retire": "",
            "Entity name": "Provider",
            "Name": "Categorías de agenda habilitadas",
            "Min occurs": "0",
            "Max occurs": "",
            "Datatype classname": "org.openmrs.customdatatype.datatype.FreeTextDatatype",
        }
        for column, value in expected.items():
            if row[column] != value:
                errors.append(
                    f"{ATTRIBUTE_TYPES_PATH}: provider scheduling-category attribute "
                    f"{column!r} must be {value!r}, found {row[column]!r}"
                )

    obsolete_parent_matches = [
        row for row in rows if row["Uuid"] == OBSOLETE_PARENT_VISIT_TYPE_ATTRIBUTE_UUID
    ]
    if obsolete_parent_matches:
        errors.append(
            f"{ATTRIBUTE_TYPES_PATH}: obsolete Parent Visit Type attribute must not "
            "be packaged; OpenMRS Core has no VisitType hierarchy"
        )

    root = ET.parse(GLOBAL_PROPERTIES_PATH).getroot()
    properties = defaultdict(list)
    for item in root.findall(".//globalProperty"):
        property_element = item.find("property")
        value_element = item.find("value")
        if property_element is None:
            continue
        properties[(property_element.text or "").strip()].append(
            (value_element.text or "").strip() if value_element is not None else ""
        )

    expected_properties = {
        "sihsalus.queue.visitQueueNumberAttributeUuid": QUEUE_NUMBER_ATTRIBUTE_UUID,
        "sihsalus.timezone": "America/Lima",
    }
    for name, expected_value in expected_properties.items():
        values = properties.get(name, [])
        if values != [expected_value]:
            errors.append(
                f"{GLOBAL_PROPERTIES_PATH}: {name!r} must occur once with value "
                f"{expected_value!r}; found {values!r}"
            )


def validate_service_durations(errors):
    definitions = {
        row["Uuid"]: row
        for row in read_csv(SERVICE_DEFINITIONS_PATH)
        if not is_retired(row["Void/Retire"])
    }
    service_types = read_csv(SERVICE_TYPES_PATH)

    for definition in definitions.values():
        try:
            if int(definition["Duration"]) <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors.append(
                f"{SERVICE_DEFINITIONS_PATH}: {definition['Name']!r} must define a "
                "positive whole-minute operational duration"
            )

    if service_types:
        errors.append(
            f"{SERVICE_TYPES_PATH}: one-to-one service types duplicate appointment "
            "services and must not be packaged. Add a service type only for a real "
            "variant such as initial/follow-up with distinct duration or capacity"
        )
    return len(definitions), len(service_types)


def _index_unique(rows, key, path, errors):
    indexed = {}
    duplicates = set()
    for row in rows:
        value = row.get(key, "")
        if value in indexed:
            duplicates.add(value)
        indexed[value] = row
    if duplicates:
        errors.append(
            f"{path}: duplicate {key} values: " + ", ".join(sorted(duplicates))
        )
    return indexed


def validate_canonical_care_routing(errors):
    definition_rows = read_csv(SERVICE_DEFINITIONS_PATH)
    definitions = _index_unique(
        definition_rows, "Uuid", SERVICE_DEFINITIONS_PATH, errors
    )
    specialities = _index_unique(
        read_csv(SPECIALITIES_PATH), "Uuid", SPECIALITIES_PATH, errors
    )
    locations = _index_unique(read_csv(LOCATIONS_PATH), "Uuid", LOCATIONS_PATH, errors)
    queue_rows = read_csv(QUEUES_PATH)
    queues = _index_unique(queue_rows, "Uuid", QUEUES_PATH, errors)
    visit_type_rows = read_csv(VISIT_TYPES_PATH)
    visit_types = _index_unique(visit_type_rows, "Uuid", VISIT_TYPES_PATH, errors)
    contract_rows = read_csv(CARE_ROUTING_CONTRACT_PATH)
    contract = _index_unique(
        contract_rows,
        "Appointment Service Uuid",
        CARE_ROUTING_CONTRACT_PATH,
        errors,
    )

    with VISIT_TYPES_PATH.open(newline="", encoding="utf-8-sig") as handle:
        visit_type_headers = csv.DictReader(handle).fieldnames or []
    if "Parent Visit Type" in visit_type_headers:
        errors.append(
            f"{VISIT_TYPES_PATH}: remove Parent Visit Type; OpenMRS Core has no "
            "VisitType hierarchy and Initializer ignores this column"
        )

    packaged_visit_type_uuids = {row["Uuid"] for row in visit_type_rows}
    if packaged_visit_type_uuids != APPROVED_ACTIVE_VISIT_TYPE_UUIDS:
        errors.append(
            f"{VISIT_TYPES_PATH}: package only the approved care-setting VisitTypes; "
            "found: " + ", ".join(sorted(packaged_visit_type_uuids))
        )
    retired_packaged_visit_types = [
        row["Uuid"] for row in visit_type_rows if is_retired(row["Void/Retire"])
    ]
    if retired_packaged_visit_types:
        errors.append(
            f"{VISIT_TYPES_PATH}: canonical content must not recreate retired legacy "
            "VisitTypes: " + ", ".join(sorted(retired_packaged_visit_types))
        )

    if set(contract) != set(definitions):
        missing = set(definitions) - set(contract)
        extra = set(contract) - set(definitions)
        if missing:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: undocumented appointment services: "
                + ", ".join(sorted(missing))
            )
        if extra:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: unknown appointment services: "
                + ", ".join(sorted(extra))
            )

    queue_service_concepts = _index_unique(
        read_csv(QUEUE_SERVICE_CONCEPTS_PATH),
        "Uuid",
        QUEUE_SERVICE_CONCEPTS_PATH,
        errors,
    )
    queue_service_members = {
        row["Member"]
        for row in read_csv(QUEUE_SERVICE_CONCEPT_SET_PATH)
        if row["Concept"] == QUEUE_SERVICE_CONCEPT_SET_UUID
        and row["Member Type"].strip().lower() == "concept-set"
    }
    appointment_service_uuids = set(definitions)
    queue_service_collisions = {
        row["Service"]
        for row in queue_rows
        if not is_retired(row["Void/Retire"])
        and row["Service"] in appointment_service_uuids
    }
    if queue_service_collisions:
        errors.append(
            f"{QUEUES_PATH}: Queue.service must use dedicated Concept UUIDs, never "
            "AppointmentServiceDefinition UUIDs: "
            + ", ".join(sorted(queue_service_collisions))
        )

    allowed_category_bases = {
        "local-scheduling",
        "rne-medical",
        "rne-dental",
        "profession",
        "none",
    }
    queue_policies = {"queue-optional", "queue-required"}
    direct_count = 0
    queue_count = 0
    retired_count = 0
    for service_uuid, row in contract.items():
        definition = definitions.get(service_uuid)
        if not definition:
            continue

        status = row["Status"]
        expected_status = (
            "retired" if is_retired(definition["Void/Retire"]) else "enabled"
        )
        if status != expected_status:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: {service_uuid} status must be "
                f"{expected_status!r}, found {status!r}"
            )
        if row["Appointment Service"] != definition["Name"]:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: service name for {service_uuid} is stale"
            )
        if not row["NTS 249 Item"] or not row["NTS 249 Prestacion"]:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: {definition['Name']!r} must document "
                "its NTS 249 basis or explicitly state N/A"
            )
        if not row["Reason"].strip():
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: {definition['Name']!r} must document "
                "the local routing decision"
            )

        location_uuid = row["Appointment Location Uuid"]
        location = locations.get(location_uuid)
        if definition["Location"] != location_uuid:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: location for {definition['Name']!r} "
                "does not match its AppointmentServiceDefinition"
            )
        if not location or location["Name"] != row["Appointment Location"]:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: appointment location name/UUID is "
                f"invalid for {definition['Name']!r}"
            )
        if status == "enabled" and location and not is_true(
            location["Tag|Appointment Location"]
        ):
            errors.append(
                f"{LOCATIONS_PATH}: active service {definition['Name']!r} must use "
                "a location tagged as Appointment Location"
            )

        category_uuid = row["Scheduling Category Uuid"]
        category_name = row["Scheduling Category"]
        category_basis = row["Category Basis"]
        if category_basis not in allowed_category_bases:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: unsupported Category Basis "
                f"{category_basis!r} for {definition['Name']!r}"
            )
        if definition["Speciality"] != category_uuid:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: scheduling category for "
                f"{definition['Name']!r} does not match the speciality FK"
            )
        if category_uuid:
            category = specialities.get(category_uuid)
            if not category or is_retired(category["Void/Retire"]):
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: category {category_uuid} for "
                    f"{definition['Name']!r} must be active"
                )
            elif category["Name"] != category_name:
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: scheduling category name for "
                    f"{category_uuid} is stale"
                )
            if category_basis in {"profession", "none"}:
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: {category_basis} service "
                    f"{definition['Name']!r} cannot claim an AppointmentSpeciality"
                )
        elif category_name or category_basis not in {"profession", "none"}:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: category UUID/name/basis are "
                f"inconsistent for {definition['Name']!r}"
            )

        arrival_policy = row["Arrival Policy"]
        queue_fields = (
            "Queue Uuid",
            "Queue",
            "Queue Service Concept Uuid",
            "Queue Location Uuid",
        )
        if status == "retired":
            retired_count += 1
            if arrival_policy != "not-applicable":
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: retired service "
                    f"{definition['Name']!r} must use not-applicable arrival"
                )
            if any(row[field] for field in (*queue_fields, "Required Visit Type Uuid", "Required Visit Type")):
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: retired service "
                    f"{definition['Name']!r} must not publish runtime routing fields"
                )
            continue

        visit_type_uuid = row["Required Visit Type Uuid"]
        visit_type = visit_types.get(visit_type_uuid)
        if not visit_type or is_retired(visit_type["Void/Retire"]):
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: {definition['Name']!r} must reference "
                "an active care-setting VisitType"
            )
        elif visit_type["Name"] != row["Required Visit Type"]:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: VisitType name for "
                f"{visit_type_uuid} is stale"
            )

        if arrival_policy == "direct":
            direct_count += 1
            if any(row[field] for field in queue_fields):
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: direct service "
                    f"{definition['Name']!r} must not define a queue"
                )
        elif arrival_policy in queue_policies:
            queue_count += 1
            missing = [field for field in queue_fields if not row[field]]
            if missing:
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: queue route for "
                    f"{definition['Name']!r} is missing " + ", ".join(missing)
                )
                continue
            queue = queues.get(row["Queue Uuid"])
            if not queue or is_retired(queue["Void/Retire"]):
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: queue for "
                    f"{definition['Name']!r} must be active"
                )
                continue
            if queue["Name"] != row["Queue"]:
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: queue name for "
                    f"{row['Queue Uuid']} is stale"
                )
            if queue["Location"] != row["Queue Location Uuid"]:
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: queue location for "
                    f"{definition['Name']!r} is stale"
                )
            if row["Queue Location Uuid"] != location_uuid:
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: appointment and queue locations "
                    f"must match for {definition['Name']!r}"
                )
            queue_location = locations.get(row["Queue Location Uuid"])
            if not queue_location or not is_true(queue_location["Tag|Queue Location"]):
                errors.append(
                    f"{LOCATIONS_PATH}: queue for {definition['Name']!r} must use a "
                    "location tagged as Queue Location"
                )
            queue_service_uuid = row["Queue Service Concept Uuid"]
            if queue["Service"] != queue_service_uuid:
                errors.append(
                    f"{CARE_ROUTING_CONTRACT_PATH}: Queue.service concept for "
                    f"{definition['Name']!r} is stale"
                )
            if queue_service_uuid not in queue_service_concepts:
                errors.append(
                    f"{QUEUE_SERVICE_CONCEPTS_PATH}: missing dedicated queue service "
                    f"concept {queue_service_uuid}"
                )
            if queue_service_uuid not in queue_service_members:
                errors.append(
                    f"{QUEUE_SERVICE_CONCEPT_SET_PATH}: queue service concept "
                    f"{queue_service_uuid} is not a member of the configured set"
                )
        else:
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: unsupported Arrival Policy "
                f"{arrival_policy!r} for {definition['Name']!r}"
            )

    semantic_expectations = {
        DENTAL_SERVICE_UUID: (GENERAL_DENTISTRY_CATEGORY_UUID, OUTPATIENT_LOCATION_UUID, "enabled"),
        OBSTETRIC_SERVICE_UUID: ("", OUTPATIENT_LOCATION_UUID, "enabled"),
        NUTRITION_SERVICE_UUID: ("32f2c8e3-79cf-4016-939f-469bed37abdb", OUTPATIENT_LOCATION_UUID, "enabled"),
        HOSPITALIZATION_SURGERY_SERVICE_UUID: (
            "d8e2f4a0-b5c3-41d7-942a-6c4a1e9f3b22",
            HOSPITALIZATION_LOCATION_UUID,
            "enabled",
        ),
        TOPICAL_SERVICE_UUID: ("", OUTPATIENT_LOCATION_UUID, "retired"),
        NEWBORN_SERVICE_UUID: (
            "14106bb7-dad6-4446-809d-737f4c128ae3",
            "35d2234e-129a-4c40-abb2-1ae0b2400004",
            "retired",
        ),
    }
    for service_uuid, (category_uuid, location_uuid, status) in semantic_expectations.items():
        row = contract.get(service_uuid)
        if row and (
            row["Scheduling Category Uuid"] != category_uuid
            or row["Appointment Location Uuid"] != location_uuid
            or row["Status"] != status
        ):
            errors.append(
                f"{CARE_ROUTING_CONTRACT_PATH}: canonical semantic decision changed "
                f"for service {service_uuid}"
            )
    if contract.get(DENTAL_SERVICE_UUID, {}).get("Scheduling Category Uuid") == CBMF_SPECIALITY_UUID:
        errors.append(
            f"{CARE_ROUTING_CONTRACT_PATH}: general dentistry must never be mapped to "
            "Cirugía Bucal y Maxilofacial"
        )

    return queue_count, direct_count, retired_count


def main():
    errors = []
    validate_privilege_and_roles(errors)
    validate_visit_attribute_metadata(errors)
    active_services, packaged_service_types = validate_service_durations(errors)
    queue_routes, direct_routes, retired_services = validate_canonical_care_routing(
        errors
    )
    if errors:
        print("Appointment/visit/queue integrity validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(ALLOWED_DIRECT_QUEUE_MUTATION_ASSIGNMENTS)} direct official "
        "queue-mutation assignments, one inherited clinical role, one read-only queue "
        "role, "
        f"{len(ALLOWED_DIRECT_FUA_GENERATION_ASSIGNMENTS)} narrow FUA generation assignments, "
        f"{len(FRONTEND_UI_PRIVILEGES)} frontend workflow privileges, "
        "queue-number and appointment-link metadata, "
        f"{active_services} active services, {packaged_service_types} one-to-one service-type "
        f"duplicates, {queue_routes} explicit queue routes, {direct_routes} direct "
        f"routes, and {retired_services} non-programmable retired services."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
