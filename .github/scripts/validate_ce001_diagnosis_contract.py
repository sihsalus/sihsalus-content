#!/usr/bin/env python3
"""Protect the single, native-diagnosis workflow used by Consulta Externa."""

import json
import sys
import unicodedata
from pathlib import Path


CE001_PATH = Path(
    "configuration/ampathforms/CE-001-CONSULTA EXTERNA.json"
)
EXPECTED_NAME = "CE-001-CONSULTA EXTERNA"
PREVIOUS_VERSION = "1.0.1"
EXPECTED_VERSION = "1.0.3"
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
    if errors:
        print("CE-001 diagnosis contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated CE-001 {EXPECTED_VERSION} Visit Notes diagnosis workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
