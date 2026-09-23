#!/usr/bin/env python3
"""Protect the single, native-diagnosis workflow used by Consulta Externa."""

import json
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

from validate_ampath_forms import ampath_persisted_form_uuid


CE001_PATH = Path(
    "configuration/ampathforms/CE-001-CONSULTA EXTERNA.json"
)
LIQUIBASE_PATH = Path("configuration/liquibase/liquibase.xml")
EXPECTED_NAME = "CE-001-CONSULTA EXTERNA"
PREVIOUS_VERSION = "1.0.1"
EXPECTED_VERSION = "1.0.2"
PREVIOUS_PERSISTED_FORM_UUID = "da631d8c-c695-3c4a-9d77-19bbbf0174e3"
EXPECTED_PERSISTED_FORM_UUID = "df1a34b4-0e8f-3564-84d9-55ce9e4284bd"
RETIRE_CHANGE_SET_ID = "retire-legacy-ce001-form-1-0-1-20260825"
ASSERT_CHANGE_SET_ID = "assert-exclusive-canonical-ce001-form-20260825"
LEGACY_DIAGNOSIS_IDS = {
    "diagnosticoPrincipal",
    "certezaDiagnostica",
    "ocurrenciaDiagnostico",
}
LEGACY_DIAGNOSIS_ONLY_CONCEPTS = {
    "2d53d39f-c93f-4128-8f7c-1bb45b498497",
    "f0000207-0000-4000-8000-000000000207",
}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def normalized(value):
    if not isinstance(value, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(
        without_accents.lower().replace("-", " ").split()
    )


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def normalized_sql(element):
    return " ".join("".join(element.itertext()).split()).upper()


def child_with_name(element, name):
    return next((child for child in element if local_name(child.tag) == name), None)


def require_fragments(sql, fragments, errors, context):
    for fragment in fragments:
        if fragment.upper() not in sql:
            errors.append(f"{context}: missing SQL contract fragment {fragment!r}")


def validate_halt_preconditions(change_set, change_set_id, errors, path):
    preconditions = child_with_name(change_set, "preConditions")
    if preconditions is None:
        errors.append(f"{path}: {change_set_id} must have fail-closed preconditions")
        return []
    if preconditions.get("onFail") != "HALT" or preconditions.get("onError") != "HALT":
        errors.append(f"{path}: {change_set_id} preconditions must HALT on failure and error")
    checks = [
        child for child in preconditions if local_name(child.tag) == "sqlCheck"
    ]
    if not checks or any(check.get("expectedResult") != "0" for check in checks):
        errors.append(
            f"{path}: {change_set_id} must use zero-count fail-closed SQL checks"
        )
    return checks


def validate_liquibase_contract(xml_text, path=LIQUIBASE_PATH):
    errors = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        return [f"{path}: invalid XML: {error}"]

    change_sets = {
        change_set.get("id"): change_set
        for change_set in root
        if local_name(change_set.tag) == "changeSet"
    }
    retire = change_sets.get(RETIRE_CHANGE_SET_ID)
    assertion = change_sets.get(ASSERT_CHANGE_SET_ID)
    if retire is None:
        errors.append(f"{path}: missing changeSet {RETIRE_CHANGE_SET_ID}")
    if assertion is None:
        errors.append(f"{path}: missing changeSet {ASSERT_CHANGE_SET_ID}")
    if retire is None or assertion is None:
        return errors

    retire_checks = validate_halt_preconditions(
        retire, RETIRE_CHANGE_SET_ID, errors, path
    )
    retire_check_sql = " ".join(normalized_sql(check) for check in retire_checks)
    require_fragments(
        retire_check_sql,
        (
            PREVIOUS_PERSISTED_FORM_UUID,
            EXPECTED_PERSISTED_FORM_UUID,
            EXPECTED_NAME,
            PREVIOUS_VERSION,
            EXPECTED_VERSION,
        ),
        errors,
        f"{path}: {RETIRE_CHANGE_SET_ID} preconditions",
    )

    retire_sql_element = child_with_name(retire, "sql")
    if retire_sql_element is None:
        errors.append(f"{path}: {RETIRE_CHANGE_SET_ID} must contain the retirement UPDATE")
    else:
        retire_sql = normalized_sql(retire_sql_element)
        require_fragments(
            retire_sql,
            (
                "UPDATE FORM",
                "PUBLISHED = 0",
                "RETIRED = 1",
                "CHANGED_BY = 1",
                "DATE_CHANGED = NOW()",
                "RETIRED_BY = COALESCE(RETIRED_BY, 1)",
                "DATE_RETIRED = COALESCE(DATE_RETIRED, NOW())",
                "RETIRED_REASON = COALESCE(",
                f"WHERE UUID = '{PREVIOUS_PERSISTED_FORM_UUID}'",
                f"AND NAME = '{EXPECTED_NAME}'",
                f"AND VERSION = '{PREVIOUS_VERSION}'",
            ),
            errors,
            f"{path}: {RETIRE_CHANGE_SET_ID}",
        )
        if EXPECTED_PERSISTED_FORM_UUID.upper() in retire_sql:
            errors.append(
                f"{path}: {RETIRE_CHANGE_SET_ID} must not mutate the canonical Form"
            )
        if "RETIRE_REASON" in retire_sql:
            errors.append(
                f"{path}: {RETIRE_CHANGE_SET_ID} uses the nonexistent form.retire_reason column; "
                "OpenMRS 2.8.9 uses form.retired_reason"
            )
        for forbidden in ("DELETE FROM", "UPDATE ENCOUNTER", "UPDATE OBS", "UPDATE FORM_RESOURCE"):
            if forbidden in retire_sql:
                errors.append(
                    f"{path}: {RETIRE_CHANGE_SET_ID} must preserve historical clinical data; "
                    f"found {forbidden!r}"
                )

    assertion_checks = validate_halt_preconditions(
        assertion, ASSERT_CHANGE_SET_ID, errors, path
    )
    assertion_sql = " ".join(normalized_sql(check) for check in assertion_checks)
    require_fragments(
        assertion_sql,
        (
            PREVIOUS_PERSISTED_FORM_UUID,
            EXPECTED_PERSISTED_FORM_UUID,
            EXPECTED_NAME,
            PREVIOUS_VERSION,
            EXPECTED_VERSION,
            "PUBLISHED",
            "RETIRED",
            f"UUID <> '{EXPECTED_PERSISTED_FORM_UUID}'",
        ),
        errors,
        f"{path}: {ASSERT_CHANGE_SET_ID} preconditions",
    )
    assertion_noop = child_with_name(assertion, "sql")
    if assertion_noop is None or normalized_sql(assertion_noop) != "SELECT 1;":
        errors.append(
            f"{path}: {ASSERT_CHANGE_SET_ID} must be an assertion-only changeSet"
        )

    return errors


def validate_contract(data, path=CE001_PATH):
    errors = []

    if data.get("name") != EXPECTED_NAME:
        errors.append(
            f"{path}: name must remain {EXPECTED_NAME!r}; AmpathFormsLoader derives "
            "the persisted Form identity from name plus version"
        )
    if data.get("version") != EXPECTED_VERSION:
        errors.append(
            f"{path}: version must be {EXPECTED_VERSION}; keeping {PREVIOUS_VERSION} "
            "would make AmpathFormsLoader overwrite the historical schema CLOB instead "
            "of retiring it and creating the corrected version"
        )

    previous_uuid = ampath_persisted_form_uuid(EXPECTED_NAME, PREVIOUS_VERSION)
    expected_uuid = ampath_persisted_form_uuid(EXPECTED_NAME, EXPECTED_VERSION)
    if previous_uuid != PREVIOUS_PERSISTED_FORM_UUID:
        errors.append(
            f"{path}: validator has an invalid Initializer identity fixture for "
            f"CE-001 {PREVIOUS_VERSION}: {previous_uuid}"
        )
    if expected_uuid != EXPECTED_PERSISTED_FORM_UUID:
        errors.append(
            f"{path}: CE-001 {EXPECTED_VERSION} must derive to persisted Form UUID "
            f"{EXPECTED_PERSISTED_FORM_UUID}, got {expected_uuid}"
        )
    if previous_uuid == expected_uuid:
        errors.append(
            f"{path}: corrected CE-001 must not reuse the persisted identity of "
            f"historical version {PREVIOUS_VERSION}"
        )

    description = data.get("description")
    description_text = normalized(description)
    if not isinstance(description, str) or not all(
        marker in description_text
        for marker in ("diagnostico cie 10", "visit notes", "diagnostico nativo")
    ):
        errors.append(
            f"{path}: description must direct CIE-10 diagnosis capture to Visit Notes "
            "and its native encounter diagnosis"
        )

    pages = data.get("pages")
    if not isinstance(pages, list):
        errors.append(f"{path}: pages must be a list")
        return errors

    for page in pages:
        if not isinstance(page, dict):
            continue
        if "diagnostico" in normalized(page.get("label")):
            errors.append(
                f"{path}: CE-001 must not expose a diagnosis page; use Visit Notes"
            )
        sections = page.get("sections")
        if not isinstance(sections, list):
            continue
        for section in sections:
            if isinstance(section, dict) and "diagnostico" in normalized(
                section.get("label")
            ):
                errors.append(
                    f"{path}: CE-001 must not expose a diagnosis section; use Visit Notes"
                )

    for node in walk(data):
        node_id = node.get("id")
        node_type = node.get("type")
        if node_id in LEGACY_DIAGNOSIS_IDS:
            errors.append(
                f"{path}: legacy diagnosis field {node_id!r} must not be present in CE-001"
            )
        if node_type == "diagnosis":
            errors.append(
                f"{path}: diagnosis field {node_id!r} duplicates the Visit Notes workflow"
            )
        if node_type != "obs":
            continue

        options = node.get("questionOptions")
        concept = options.get("concept") if isinstance(options, dict) else None
        label = normalized(node.get("label"))
        looks_like_coded_diagnosis = (
            "diagnostico principal" in label
            or "diagnostico clasificado" in label
            or "cie 10" in label
        )
        if concept in LEGACY_DIAGNOSIS_ONLY_CONCEPTS or looks_like_coded_diagnosis:
            errors.append(
                f"{path}: obs field {node_id!r} reintroduces diagnosis-as-observation; "
                "CIE-10 diagnoses must be recorded through Visit Notes"
            )

    return errors


def main():
    try:
        data = json.loads(CE001_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Unable to load {CE001_PATH}: {error}", file=sys.stderr)
        return 1

    errors = validate_contract(data)
    try:
        liquibase_text = LIQUIBASE_PATH.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"{LIQUIBASE_PATH}: cannot read Liquibase contract: {error}")
    else:
        errors.extend(validate_liquibase_contract(liquibase_text))
    if errors:
        print("CE-001 diagnosis contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Validated retirement of CE-001 {PREVIOUS_VERSION} and exclusive canonical "
        f"{EXPECTED_VERSION} Visit Notes diagnosis workflow."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
