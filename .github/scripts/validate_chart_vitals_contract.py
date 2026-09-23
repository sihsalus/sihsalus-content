#!/usr/bin/env python3
import csv
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = REPO_ROOT / "configuration"

ENCOUNTER_TYPES_PATH = CONFIG_ROOT / "encountertypes" / "encountertypes.csv"
ENCOUNTER_ROLES_PATH = CONFIG_ROOT / "encounterroles" / "encounterroles.csv"
PRIVILEGES_PATH = CONFIG_ROOT / "privileges" / "privileges_core-demo.csv"
LOCATION_TAGS_PATH = CONFIG_ROOT / "locationtags" / "locationtags.csv"
LOCATIONS_PATH = CONFIG_ROOT / "locations" / "sihsalus-locations.csv"
VISIT_TYPES_PATH = CONFIG_ROOT / "visittypes" / "sihsalus-visittypes.csv"
PATIENT_IDENTIFIER_TYPES_PATH = (
    CONFIG_ROOT / "patientidentifiertypes" / "patientidentifiertypes.csv"
)
REFERENCE_RANGES_PATH = (
    CONFIG_ROOT / "conceptreferencerange" / "conceptreferencerange_vital_signs.csv"
)
DATA_FILTERS_PATH = CONFIG_ROOT / "datafiltermappings"
LIQUIBASE_PATH = CONFIG_ROOT / "liquibase"
FORMS_PATH = CONFIG_ROOT / "ampathforms"
OCL_PATH = CONFIG_ROOT / "ocl"
HANDOFF_PATH = (
    REPO_ROOT / "docs" / "audits" / "2026-07-16-chart-vitals-encounter-contract.md"
)

LEGACY_ENCOUNTER_TYPE_UUID = "67a71486-1a54-468f-ac3e-7091a9a79584"
CHART_VITALS_ENCOUNTER_TYPE_UUID = "20d4a603-8472-484c-b2bf-b45bdecf6b4f"
EMERGENCY_TRIAGE_ENCOUNTER_TYPE_UUID = "978deb64-358e-4c78-bbb0-04cea73df805"
EMERGENCY_CARE_ENCOUNTER_TYPE_UUID = "1b70fe57-92c1-4e35-87f7-13d0e04ff12f"

CHART_VITALS_ENCOUNTER_ROLE_UUID = "bebe2266-abbb-4f3c-b28b-a5b47406fff5"
EMERGENCY_TRIAGE_ENCOUNTER_ROLE_UUID = "bd16c32b-6784-45e6-9504-df1cfe0b62e5"

CHART_VIEW_PRIVILEGE = "app:hoja.clinica.signosVitales"
CHART_EDIT_PRIVILEGE = "app:hoja.clinica.signosVitales.editar"
EMERGENCY_VIEW_PRIVILEGE = "app:home.emergencia"
EMERGENCY_EDIT_PRIVILEGE = "app:home.emergencia.editar"

PRIVILEGE_UUIDS = {
    CHART_VIEW_PRIVILEGE: "4221e393-e02d-422a-8d28-13089f03ade8",
    CHART_EDIT_PRIVILEGE: "3700438c-f5dc-44c6-a87d-c4c47cc074cb",
    EMERGENCY_VIEW_PRIVILEGE: "98ca70b3-2db4-43be-88a7-b896a4326d7e",
    EMERGENCY_EDIT_PRIVILEGE: "8291a525-0233-4599-9cb5-7a3852631f18",
}

CLINICAL_ROLE_UUID = "e832327b-7fc2-4e64-a527-7e6ae0cdd041"
NURSE_ROLE_UUID = "e70120b5-000c-4e6f-94a5-a139c2b4b25c"
EMERGENCY_ROLE_UUID = "cf627580-0372-47fc-87b6-319d4a4d4973"
ADMISSION_ROLE_UUID = "71dcb611-756a-4ad3-a9bb-73b6cfe28066"

VISIT_LOCATION_TAG_UUID = "36671c44-ce2d-47fb-b88e-bace6c85d801"
EMERGENCY_LOCATION_UUID = "35d2234e-129a-4c40-abb2-1ae0b2400003"
EMERGENCY_VISIT_TYPE_UUID = "c2a1d3e2-4b8f-4326-94d9-7f6c9a1b7c98"

REFERENCE_RANGE_CONCEPT_UUIDS = (
    "5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5086AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5242AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5087AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "1343AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5089AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5090AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "18fcbd1f-5b4f-44ed-a664-8637a83cc7eb",
    "c4d39248-c896-433a-bc69-e24d04b7f0e5",
    "911eb398-e7de-4270-af63-e4c615ec22a9",
    "4bcdcee3-54c2-4368-a5cf-733e9c25fe50",
    "98a61b6b-15d3-4064-893c-96e4d8e90bbd",
    "b1fb2d14-92ec-4fda-90e5-40f3227c9c65",
)

REFERENCE_RANGE_GROUP_COUNTS = {
    "5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 12,
    "5086AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 12,
    "5242AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 12,
    "5087AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 12,
    "5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 12,
    "5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 12,
    "1343AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 7,
    "5089AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 7,
    "5090AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA": 7,
    "18fcbd1f-5b4f-44ed-a664-8637a83cc7eb": 2,
    "c4d39248-c896-433a-bc69-e24d04b7f0e5": 7,
    "911eb398-e7de-4270-af63-e4c615ec22a9": 8,
    "4bcdcee3-54c2-4368-a5cf-733e9c25fe50": 2,
    "98a61b6b-15d3-4064-893c-96e4d8e90bbd": 3,
    "b1fb2d14-92ec-4fda-90e5-40f3227c9c65": 3,
}

CHART_NUMERIC_OBSERVATION_CONCEPT_UUIDS = (
    "5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5086AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5242AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5087AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "1343AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5089AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5090AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "18fcbd1f-5b4f-44ed-a664-8637a83cc7eb",
    "c4d39248-c896-433a-bc69-e24d04b7f0e5",
    "911eb398-e7de-4270-af63-e4c615ec22a9",
)

CHART_CONTEXT_OBSERVATION_CONCEPT_UUIDS = (
    "165095AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
)

VITAL_SIGNS_SET_UUID = "1114AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
EXPECTED_VITAL_SIGNS_SET_MEMBERS = set(
    CHART_NUMERIC_OBSERVATION_CONCEPT_UUIDS
    + CHART_CONTEXT_OBSERVATION_CONCEPT_UUIDS
)

FORBIDDEN_CHART_CONCEPT_UUIDS = {
    "5283AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "7e540048-19b4-4261-af10-3b20712a92ef",
    "67f9449e-e7ef-436c-9eb7-837b5afe30e4",
    "98bfda0d-2a22-4ca4-8bc9-b0b6c6505899",
    "9ba86e50-a4fd-48b7-b8b2-f537fde5a382",
}

EXPECTED_HANDOFF_SCALARS = {
    "legacyMixedEncounterTypeUuid": LEGACY_ENCOUNTER_TYPE_UUID,
    "chartVitalsEncounterTypeUuid": CHART_VITALS_ENCOUNTER_TYPE_UUID,
    "emergencyTriageEncounterTypeUuid": EMERGENCY_TRIAGE_ENCOUNTER_TYPE_UUID,
    "emergencyCareEncounterTypeUuid": EMERGENCY_CARE_ENCOUNTER_TYPE_UUID,
    "chartVitalsEncounterRoleUuid": CHART_VITALS_ENCOUNTER_ROLE_UUID,
    "emergencyTriageEncounterRoleUuid": EMERGENCY_TRIAGE_ENCOUNTER_ROLE_UUID,
    "emergencyVisitTypeUuid": EMERGENCY_VISIT_TYPE_UUID,
    "emergencyLocationUuid": EMERGENCY_LOCATION_UUID,
    "patientIdentifierLocationBehavior": "NOT_USED",
    "patientIdentifierLocationPayload": "omit-property",
    "chartVisitSource": "current-chart-visit-context",
    "chartEncounterLocationSource": "active-visit",
}

LEGACY_FINGERPRINT = {
    "Void/Retire": "",
    "Name": "Triaje",
    "Description": (
        "Evaluación inicial de signos vitales y clasificación del paciente según "
        "urgencia. Basado en la NTS N° 021-MINSA."
    ),
    "View privilege": "",
    "Edit privilege": "",
}

EXPECTED_ENCOUNTER_TYPES = {
    CHART_VITALS_ENCOUNTER_TYPE_UUID: {
        "Void/Retire": "",
        "Name": "Registro de signos vitales y antropometría",
        "Description": (
            "Registro longitudinal de funciones vitales y mediciones antropométricas "
            "desde la historia clínica, separado de la clasificación de emergencia. "
            "Alineado con la NTS N° 139-MINSA/2018/DGAIN."
        ),
        "View privilege": CHART_VIEW_PRIVILEGE,
        "Edit privilege": CHART_EDIT_PRIVILEGE,
    },
    EMERGENCY_TRIAGE_ENCOUNTER_TYPE_UUID: {
        "Void/Retire": "",
        "Name": "Triaje de Emergencia",
        "Description": (
            "Clasificación clínica inicial por prioridad dentro del servicio de "
            "emergencia. Basado en la NT N° 042-MINSA/DGSP-V.01."
        ),
        "View privilege": EMERGENCY_VIEW_PRIVILEGE,
        "Edit privilege": EMERGENCY_EDIT_PRIVILEGE,
    },
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_single_ocl_export(pattern, collection, errors):
    matches = sorted(OCL_PATH.glob(pattern))
    if len(matches) != 1:
        errors.append(
            f"{OCL_PATH}: expected exactly one {collection} export matching "
            f"{pattern!r}, found {len(matches)}"
        )
        return []

    with zipfile.ZipFile(matches[0]) as archive:
        try:
            export = json.loads(archive.read("export.json"))
        except KeyError:
            errors.append(f"{matches[0]}: missing export.json")
            return []
    return export.get(collection, [])


def split_values(value):
    return {item.strip() for item in (value or "").split(";") if item.strip()}


def is_retired(value):
    return (value or "").strip().lower() in {"1", "true", "yes"}


def find_one(rows, uuid, path, errors):
    matches = [row for row in rows if (row.get("Uuid") or "").strip() == uuid]
    if len(matches) != 1:
        errors.append(f"{path}: expected exactly one row with UUID {uuid}, found {len(matches)}")
        return None
    return matches[0]


def assert_fields(path, row, expected, errors):
    if row is None:
        return
    for field, expected_value in expected.items():
        actual = row.get(field)
        if actual != expected_value:
            errors.append(
                f"{path}: UUID {row.get('Uuid')}: {field} must be "
                f"{expected_value!r}, got {actual!r}"
            )


def validate_encounter_metadata(errors):
    encounter_types = read_csv(ENCOUNTER_TYPES_PATH)
    legacy = find_one(
        encounter_types, LEGACY_ENCOUNTER_TYPE_UUID, ENCOUNTER_TYPES_PATH, errors
    )
    assert_fields(ENCOUNTER_TYPES_PATH, legacy, LEGACY_FINGERPRINT, errors)

    for uuid, expected in EXPECTED_ENCOUNTER_TYPES.items():
        row = find_one(encounter_types, uuid, ENCOUNTER_TYPES_PATH, errors)
        assert_fields(ENCOUNTER_TYPES_PATH, row, expected, errors)

    emergency_care = find_one(
        encounter_types,
        EMERGENCY_CARE_ENCOUNTER_TYPE_UUID,
        ENCOUNTER_TYPES_PATH,
        errors,
    )
    if emergency_care is not None:
        if emergency_care.get("Name") != "Atención en Emergencia":
            errors.append(
                f"{ENCOUNTER_TYPES_PATH}: emergency care type must remain distinct"
            )
        if "NT N° 042-MINSA/DGSP-V.01" not in emergency_care.get("Description", ""):
            errors.append(
                f"{ENCOUNTER_TYPES_PATH}: Atención en Emergencia must cite NT 042"
            )

    encounter_roles = read_csv(ENCOUNTER_ROLES_PATH)
    chart_role = find_one(
        encounter_roles,
        CHART_VITALS_ENCOUNTER_ROLE_UUID,
        ENCOUNTER_ROLES_PATH,
        errors,
    )
    assert_fields(
        ENCOUNTER_ROLES_PATH,
        chart_role,
        {
            "Void/Retire": "",
            "Name": "Responsable del registro de signos vitales",
            "Description": (
                "Profesional o personal asistencial responsable de tomar y registrar "
                "los signos vitales y mediciones antropométricas en la historia clínica"
            ),
        },
        errors,
    )
    triage_role = find_one(
        encounter_roles,
        EMERGENCY_TRIAGE_ENCOUNTER_ROLE_UUID,
        ENCOUNTER_ROLES_PATH,
        errors,
    )
    assert_fields(
        ENCOUNTER_ROLES_PATH,
        triage_role,
        {
            "Void/Retire": "",
            "Name": "Enfermera de Triaje",
            "Description": (
                "Profesional de enfermería capacitado en clasificación de riesgo "
                "según la NT N° 042-MINSA/DGSP-V.01"
            ),
        },
        errors,
    )


def validate_rbac(errors):
    privileges = read_csv(PRIVILEGES_PATH)
    for privilege_name, privilege_uuid in PRIVILEGE_UUIDS.items():
        row = find_one(privileges, privilege_uuid, PRIVILEGES_PATH, errors)
        if row is not None and row.get("Privilege name") != privilege_name:
            errors.append(
                f"{PRIVILEGES_PATH}: UUID {privilege_uuid} must be {privilege_name!r}"
            )
        name_matches = [
            candidate
            for candidate in privileges
            if candidate.get("Privilege name") == privilege_name
        ]
        if len(name_matches) != 1:
            errors.append(
                f"{PRIVILEGES_PATH}: expected exactly one privilege named "
                f"{privilege_name!r}, found {len(name_matches)}"
            )

    declared_privileges = {
        row.get("Privilege name", "").strip() for row in privileges
    }
    for encounter_type in read_csv(ENCOUNTER_TYPES_PATH):
        view_privilege = encounter_type.get("View privilege", "").strip()
        edit_privilege = encounter_type.get("Edit privilege", "").strip()
        for field, privilege in [
            ("View privilege", view_privilege),
            ("Edit privilege", edit_privilege),
        ]:
            if privilege and privilege not in declared_privileges:
                errors.append(
                    f"{ENCOUNTER_TYPES_PATH}: {encounter_type.get('Name')!r} has "
                    f"unresolved {field}: {privilege!r}"
                )
        if view_privilege and view_privilege == edit_privilege:
            errors.append(
                f"{ENCOUNTER_TYPES_PATH}: {encounter_type.get('Name')!r} must use "
                "different view and edit privileges"
            )

    roles = []
    for path in sorted((CONFIG_ROOT / "roles").glob("*.csv")):
        for row in read_csv(path):
            row["_path"] = str(path)
            roles.append(row)

    clinical = find_one(roles, CLINICAL_ROLE_UUID, "roles", errors)
    nurse = find_one(roles, NURSE_ROLE_UUID, "roles", errors)
    emergency = find_one(roles, EMERGENCY_ROLE_UUID, "roles", errors)
    admission = find_one(roles, ADMISSION_ROLE_UUID, "roles", errors)

    if nurse is not None and "SIHSALUS Consulta Externa" not in split_values(
        nurse.get("Inherited roles")
    ):
        errors.append(
            f"{nurse['_path']}: Enfermera must inherit SIHSALUS Consulta Externa"
        )

    role_by_name = {}
    for role in roles:
        role_name = role.get("Role name", "").strip()
        if role_name in role_by_name:
            errors.append(f"roles: duplicate role name {role_name!r}")
        else:
            role_by_name[role_name] = role

    privilege_cache = {}
    inherited_role_cache = {}

    def effective_privileges(role, stack=()):
        role_uuid = role.get("Uuid")
        if role_uuid in privilege_cache:
            return privilege_cache[role_uuid]
        role_name = role.get("Role name", "")
        if role_name in stack:
            errors.append(
                "roles: inheritance cycle detected: " + " -> ".join((*stack, role_name))
            )
            return set()

        privileges = split_values(role.get("Privileges"))
        for inherited_name in split_values(role.get("Inherited roles")):
            inherited = role_by_name.get(inherited_name)
            if inherited is None:
                errors.append(
                    f"{role['_path']}: {role_name!r} inherits unknown role {inherited_name!r}"
                )
                continue
            privileges |= effective_privileges(inherited, (*stack, role_name))
        privilege_cache[role_uuid] = privileges
        return privileges

    def inherited_role_names(role, stack=()):
        role_uuid = role.get("Uuid")
        if role_uuid in inherited_role_cache:
            return inherited_role_cache[role_uuid]
        role_name = role.get("Role name", "")
        if role_name in stack:
            return set()

        inherited_names = set()
        for inherited_name in split_values(role.get("Inherited roles")):
            inherited_names.add(inherited_name)
            inherited = role_by_name.get(inherited_name)
            if inherited is not None:
                inherited_names |= inherited_role_names(
                    inherited, (*stack, role_name)
                )
        inherited_role_cache[role_uuid] = inherited_names
        return inherited_names

    protected = set(PRIVILEGE_UUIDS)
    expected_access = {
        CLINICAL_ROLE_UUID: (
            {CHART_VIEW_PRIVILEGE, CHART_EDIT_PRIVILEGE},
            protected - {CHART_VIEW_PRIVILEGE, CHART_EDIT_PRIVILEGE},
        ),
        NURSE_ROLE_UUID: (
            {CHART_VIEW_PRIVILEGE, CHART_EDIT_PRIVILEGE},
            protected - {CHART_VIEW_PRIVILEGE, CHART_EDIT_PRIVILEGE},
        ),
        EMERGENCY_ROLE_UUID: (protected, set()),
        ADMISSION_ROLE_UUID: (set(), protected),
    }
    target_roles = {
        CLINICAL_ROLE_UUID: clinical,
        NURSE_ROLE_UUID: nurse,
        EMERGENCY_ROLE_UUID: emergency,
        ADMISSION_ROLE_UUID: admission,
    }
    clinical_rest_privileges = {
        "Add Encounters",
        "Add Observations",
        "Edit Encounters",
        "Edit Observations",
        "Get Concepts",
        "Get Encounter Roles",
        "Get Encounter Types",
        "Get Encounters",
        "Get Locations",
        "Get Observations",
        "Get Providers",
        "Get Visits",
        "View Encounters",
        "View Observations",
    }

    for role_uuid, role in target_roles.items():
        if role is None:
            continue
        effective = effective_privileges(role)
        required, forbidden = expected_access[role_uuid]
        missing = required - effective
        leaked = forbidden & effective
        if missing:
            errors.append(
                f"{role['_path']}: {role.get('Role name')!r} lacks effective encounter "
                f"privileges: {', '.join(sorted(missing))}"
            )
        if leaked:
            errors.append(
                f"{role['_path']}: {role.get('Role name')!r} has forbidden encounter "
                f"privileges: {', '.join(sorted(leaked))}"
            )

        if role_uuid in {CLINICAL_ROLE_UUID, NURSE_ROLE_UUID, EMERGENCY_ROLE_UUID}:
            missing_rest = clinical_rest_privileges - effective
            if missing_rest:
                errors.append(
                    f"{role['_path']}: {role.get('Role name')!r} lacks REST privileges "
                    f"required by encounter/observation writes: {', '.join(sorted(missing_rest))}"
                )

    if admission is not None:
        admission_effective = effective_privileges(admission)
        # Queue 3.0.0 indirectly needs Get Encounters while VisitValidator saves
        # the ticket number, but admission must retain no clinical write/view access.
        admission_clinical_rest = {
            "Add Encounters",
            "Add Observations",
            "Delete Encounters",
            "Delete Notes",
            "Delete Observations",
            "Edit Encounters",
            "Edit Notes",
            "Edit Observations",
            "Get Diagnoses",
            "Get Notes",
            "Get Observations",
            "View Encounters",
            "View Observations",
        } & admission_effective
        admission_clinical_ui = {
            privilege
            for privilege in admission_effective
            if privilege == "app:hoja.clinica"
            or privilege.startswith("app:hoja.clinica.")
        }
        admission_clinical_access = (
            admission_clinical_rest | admission_clinical_ui
        )
        if admission_clinical_access:
            errors.append(
                f"{admission['_path']}: Admision must not access clinical "
                "chart, encounter, note, diagnosis, or observation capabilities: "
                f"{', '.join(sorted(admission_clinical_access))}"
            )
        location_management = {
            "Manage Locations",
            "Manage Location Tags",
        } & admission_effective
        if location_management:
            errors.append(
                f"{admission['_path']}: Admision must not manage locations: "
                f"{', '.join(sorted(location_management))}"
            )

    for role in [clinical, nurse, emergency, admission]:
        if role is None:
            continue
        if "Application: Enters Vitals" in inherited_role_names(role):
            errors.append(
                f"{role['_path']}: {role.get('Role name')} must not inherit "
                "Application: Enters Vitals directly or transitively "
                "(Privilege Level: High)"
            )


def validate_location_contract(errors):
    identifier_types = read_csv(PATIENT_IDENTIFIER_TYPES_PATH)
    active_identifier_types = [
        row for row in identifier_types if not is_retired(row.get("Void/Retire"))
    ]
    if not active_identifier_types:
        errors.append(f"{PATIENT_IDENTIFIER_TYPES_PATH}: no active identifier types")
    for identifier_type in active_identifier_types:
        if identifier_type.get("Location behavior") != "NOT_USED":
            errors.append(
                f"{PATIENT_IDENTIFIER_TYPES_PATH}: {identifier_type.get('Name')!r} "
                "must use Location behavior NOT_USED; registration omits location"
            )

    tags = read_csv(LOCATION_TAGS_PATH)
    visit_tag = find_one(tags, VISIT_LOCATION_TAG_UUID, LOCATION_TAGS_PATH, errors)
    if visit_tag is not None and visit_tag.get("Name") != "Visit Location":
        errors.append(f"{LOCATION_TAGS_PATH}: Visit Location tag changed unexpectedly")

    locations = read_csv(LOCATIONS_PATH)
    emergency = find_one(locations, EMERGENCY_LOCATION_UUID, LOCATIONS_PATH, errors)
    if emergency is not None:
        expected = {
            "Name": "UPSS - EMERGENCIA",
            "Parent": "Hospital Santa Clotilde",
            "Tag|Login Location": "FALSE",
            "Tag|Visit Location": "TRUE",
        }
        assert_fields(LOCATIONS_PATH, emergency, expected, errors)
        if is_retired(emergency.get("Void/Retire")):
            errors.append(f"{LOCATIONS_PATH}: emergency location must be active")

    for support_name in [
        "UPSS - CENTRAL DE ESTERILIZACIÓN",
        "UPSS - SERVICIOS ADMINISTRATIVOS",
    ]:
        matches = [row for row in locations if row.get("Name") == support_name]
        if len(matches) != 1:
            errors.append(f"{LOCATIONS_PATH}: expected one {support_name!r} row")
        elif matches[0].get("Tag|Visit Location") != "FALSE":
            errors.append(
                f"{LOCATIONS_PATH}: support location {support_name!r} must not be a Visit Location"
            )

    visit_types = read_csv(VISIT_TYPES_PATH)
    emergency_visit = find_one(
        visit_types, EMERGENCY_VISIT_TYPE_UUID, VISIT_TYPES_PATH, errors
    )
    if emergency_visit is not None:
        if emergency_visit.get("Name") != "Emergencia":
            errors.append(f"{VISIT_TYPES_PATH}: emergency visit type name changed")
        description = emergency_visit.get("Description", "")
        if "NT N° 042-MINSA/DGSP-V.01" not in description or "NTS N° 021" in description:
            errors.append(
                f"{VISIT_TYPES_PATH}: emergency visit type must cite NT 042, not NTS 021"
            )


def validate_ocl_chart_contract(errors):
    concepts = read_single_ocl_export(
        "*_SIHSALUS_sihsalus_concepts_*.zip", "concepts", errors
    )
    mappings = read_single_ocl_export(
        "*_SIHSALUS_sihsalus_mappings_*.zip", "mappings", errors
    )
    if not concepts or not mappings:
        return

    concepts_by_identifier = {}
    concepts_by_url = {}
    for concept in concepts:
        concepts_by_url[concept.get("url")] = concept
        for identifier in [concept.get("external_id"), concept.get("uuid")]:
            if identifier:
                concepts_by_identifier.setdefault(identifier, concept)

    chart_numeric = set(CHART_NUMERIC_OBSERVATION_CONCEPT_UUIDS)
    chart_context = set(CHART_CONTEXT_OBSERVATION_CONCEPT_UUIDS)
    if chart_numeric & chart_context:
        errors.append("chart numeric and context observation allowlists must not overlap")
    if (chart_numeric | chart_context) & FORBIDDEN_CHART_CONCEPT_UUIDS:
        errors.append("chart observation allowlists must exclude Karnofsky and Glasgow")

    for concept_uuid in CHART_NUMERIC_OBSERVATION_CONCEPT_UUIDS:
        concept = concepts_by_identifier.get(concept_uuid)
        if concept is None:
            errors.append(f"OCL: missing chart numeric concept {concept_uuid}")
        elif concept.get("datatype") != "Numeric":
            errors.append(
                f"OCL: chart numeric concept {concept_uuid} must be Numeric, got "
                f"{concept.get('datatype')!r}"
            )

    for concept_uuid in CHART_CONTEXT_OBSERVATION_CONCEPT_UUIDS:
        concept = concepts_by_identifier.get(concept_uuid)
        if concept is None:
            errors.append(f"OCL: missing chart context concept {concept_uuid}")
        elif concept.get("datatype") != "Text":
            errors.append(
                f"OCL: chart context concept {concept_uuid} must be Text, got "
                f"{concept.get('datatype')!r}"
            )

    vital_signs_set = concepts_by_identifier.get(VITAL_SIGNS_SET_UUID)
    if vital_signs_set is None:
        errors.append(f"OCL: missing Signos Vitales set {VITAL_SIGNS_SET_UUID}")
        return

    set_url = vital_signs_set.get("url")
    actual_members = set()
    unresolved_member_urls = []
    for mapping in mappings:
        if (
            mapping.get("map_type") != "CONCEPT-SET"
            or mapping.get("from_concept_url") != set_url
            or mapping.get("retired") is True
        ):
            continue
        member_url = mapping.get("to_concept_url")
        member = concepts_by_url.get(member_url)
        if member is None or not member.get("external_id"):
            unresolved_member_urls.append(member_url)
        else:
            actual_members.add(member["external_id"])

    if unresolved_member_urls:
        errors.append(
            "OCL: unresolved Signos Vitales member URLs: "
            + ", ".join(sorted(unresolved_member_urls))
        )
    if actual_members != EXPECTED_VITAL_SIGNS_SET_MEMBERS:
        missing = EXPECTED_VITAL_SIGNS_SET_MEMBERS - actual_members
        extra = actual_members - EXPECTED_VITAL_SIGNS_SET_MEMBERS
        errors.append(
            "OCL: Signos Vitales active membership must match the chart contract; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )


def validate_no_form_or_filter_coupling(errors):
    forbidden_tokens = {
        CHART_VITALS_ENCOUNTER_TYPE_UUID,
        EMERGENCY_TRIAGE_ENCOUNTER_TYPE_UUID,
        "Registro de signos vitales y antropometría",
        "Triaje de Emergencia",
    }
    for form_path in sorted(FORMS_PATH.rglob("*.json")):
        text = form_path.read_text(encoding="utf-8")
        found = sorted(token for token in forbidden_tokens if token in text)
        if found:
            errors.append(
                f"{form_path}: new embedded encounter contract must not be coupled "
                f"to a JSON form; found {', '.join(found)}"
            )

    for data_filter_path in sorted(DATA_FILTERS_PATH.rglob("*")):
        if not data_filter_path.is_file():
            continue
        data_filter_text = data_filter_path.read_text(encoding="utf-8")
        for uuid in [
            CHART_VITALS_ENCOUNTER_TYPE_UUID,
            EMERGENCY_TRIAGE_ENCOUNTER_TYPE_UUID,
        ]:
            if uuid in data_filter_text:
                errors.append(
                    f"{data_filter_path}: do not add speculative location filters for {uuid}"
                )

    for liquibase_path in sorted(LIQUIBASE_PATH.rglob("*")):
        if not liquibase_path.is_file():
            continue
        liquibase_text = liquibase_path.read_text(encoding="utf-8")
        for uuid in [
            LEGACY_ENCOUNTER_TYPE_UUID,
            CHART_VITALS_ENCOUNTER_TYPE_UUID,
            EMERGENCY_TRIAGE_ENCOUNTER_TYPE_UUID,
        ]:
            if uuid in liquibase_text:
                errors.append(
                    f"{liquibase_path}: encounter reclassification must not run "
                    f"automatically through Liquibase: {uuid}"
                )

    handoff_text = HANDOFF_PATH.read_text(encoding="utf-8")
    json_blocks = re.findall(r"```json\s*\n(.*?)\n```", handoff_text, flags=re.DOTALL)
    handoff_contracts = []
    for json_block in json_blocks:
        try:
            candidate = json.loads(json_block)
        except json.JSONDecodeError as error:
            errors.append(f"{HANDOFF_PATH}: invalid JSON handoff block: {error}")
            continue
        if "chartVitalsEncounterTypeUuid" in candidate:
            handoff_contracts.append(candidate)

    if len(handoff_contracts) != 1:
        errors.append(
            f"{HANDOFF_PATH}: expected exactly one JSON chart allowlist contract, "
            f"found {len(handoff_contracts)}"
        )
    else:
        handoff = handoff_contracts[0]
        expected_keys = set(EXPECTED_HANDOFF_SCALARS) | {
            "chartNumericObservationConceptUuids",
            "chartContextObservationConceptUuids",
        }
        if set(handoff) != expected_keys:
            errors.append(
                f"{HANDOFF_PATH}: handoff keys must match the exact contract; "
                f"missing={sorted(expected_keys - set(handoff))}, "
                f"extra={sorted(set(handoff) - expected_keys)}"
            )

        for key, expected_value in EXPECTED_HANDOFF_SCALARS.items():
            if handoff.get(key) != expected_value:
                errors.append(
                    f"{HANDOFF_PATH}: {key} must be {expected_value!r}, got "
                    f"{handoff.get(key)!r}"
                )

        expected_allowlists = {
            "chartNumericObservationConceptUuids": set(
                CHART_NUMERIC_OBSERVATION_CONCEPT_UUIDS
            ),
            "chartContextObservationConceptUuids": set(
                CHART_CONTEXT_OBSERVATION_CONCEPT_UUIDS
            ),
        }
        for key, expected_allowlist in expected_allowlists.items():
            actual_allowlist = handoff.get(key)
            if not isinstance(actual_allowlist, list):
                errors.append(f"{HANDOFF_PATH}: {key} must be a JSON array")
                continue
            if len(actual_allowlist) != len(set(actual_allowlist)):
                errors.append(f"{HANDOFF_PATH}: {key} contains duplicates")
            if set(actual_allowlist) != expected_allowlist:
                errors.append(
                    f"{HANDOFF_PATH}: {key} must match its explicit allowlist"
                )

    range_concept_sequence = [
        row.get("Concept Numeric uuid", "").strip()
        for row in read_csv(REFERENCE_RANGES_PATH)
        if row.get("Concept Numeric uuid", "").strip()
    ]
    actual_group_counts = Counter(range_concept_sequence)
    if actual_group_counts != Counter(REFERENCE_RANGE_GROUP_COUNTS):
        errors.append(
            f"{REFERENCE_RANGES_PATH}: range group counts must match the exact contract; "
            f"expected={REFERENCE_RANGE_GROUP_COUNTS}, actual={dict(actual_group_counts)}"
        )
    if set(actual_group_counts) != set(REFERENCE_RANGE_CONCEPT_UUIDS):
        errors.append(
            f"{REFERENCE_RANGES_PATH}: numeric range concepts changed without "
            "updating the independent range contract"
        )

    seen_groups = set()
    previous_concept = None
    for concept_uuid in range_concept_sequence:
        if concept_uuid == previous_concept:
            continue
        if concept_uuid in seen_groups:
            errors.append(
                f"{REFERENCE_RANGES_PATH}: concept range group {concept_uuid} is non-contiguous"
            )
        seen_groups.add(concept_uuid)
        previous_concept = concept_uuid


def main():
    errors = []
    validate_encounter_metadata(errors)
    validate_rbac(errors)
    validate_location_contract(errors)
    validate_ocl_chart_contract(errors)
    validate_no_form_or_filter_coupling(errors)

    if errors:
        print("Chart-vitals encounter contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "Validated chart-vitals/emergency encounter separation, RBAC, identifier/"
        "encounter location invariants, explicit observation allowlists, curated OCL "
        "set membership, and zero JSON-form coupling."
    )


if __name__ == "__main__":
    main()
