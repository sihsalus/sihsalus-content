#!/usr/bin/env python3
"""Protect the segmented physical-examination contract for Consulta Externa."""

import json
import sys
from pathlib import Path


FORM_PATH = Path(
    "configuration/ampathforms/CE-EXF-001-EXAMEN FISICO.json"
)
EXPECTED_NAME = "CE-EXF-001-EXAMEN FISICO"
EXPECTED_VERSION = "1.0.0"
REQUIRED_FIELDS = {"estadoGeneral"}
LEGACY_FORM_PATH = Path("configuration/ampathforms/CE-SOAP-001-NOTA SOAP.json")
SEGMENTED_FIELD_CONCEPTS = {
    "estadoGeneral": "b564fd45-c5e8-4889-ba05-e878b485cdd1",
    "estadoConciencia": "2944f99e-bda8-4acc-8a4e-d5709dd82041",
    "pielAnexos": "23205e1e-fa88-43e0-a421-452516c04f9e",
    "cabezaCuello": "d0640842-e04e-4398-ba6c-a63623d580f8",
    "aparatoRespiratorio": "da3dada5-bde9-48b1-b94c-171355639ab4",
    "aparatoCardiovascular": "24989612-6bbf-4ef8-8af7-adf2b5b95ba3",
    "abdomenDigestivo": "e7daf833-3c73-4151-b581-90646bd93fc5",
    "genitourinario": "57746a04-5f9e-4e42-9233-efeeeb3db0d0",
    "musculoesqueleticoExtremidades": "479e125e-e5be-4538-8c4e-ed6fd9c8d515",
    "neurologico": "d55d40c3-9ba8-4c7f-8728-f28ddb22cbd3",
}
LEGACY_SOAP_FIELDS = {
    "soapSubjetivo": "f0000202-0000-4000-8000-000000000202",
    "soapObjetivo": "160532AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "soapEvaluacion": "160533AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "soapPlan": "f0000201-0000-4000-8000-000000000201",
}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def validate_contract(form):
    errors = []
    if form.get("name") != EXPECTED_NAME:
        errors.append(f"form name must remain {EXPECTED_NAME!r}")
    if form.get("version") != EXPECTED_VERSION:
        errors.append(
            f"form version must remain {EXPECTED_VERSION}; use the dedicated physical-exam identity"
        )

    questions = {
        node.get("id"): node
        for node in walk(form)
        if isinstance(node.get("id"), str) and node.get("type") == "obs"
    }
    missing = SEGMENTED_FIELD_CONCEPTS.keys() - questions.keys()
    if missing:
        errors.append(f"missing segmented physical-exam fields: {sorted(missing)}")

    if form.get("published") is not True or form.get("retired") is not False:
        errors.append("physical-exam form must be published and active")
    for field_id, question in questions.items():
        if (field_id in LEGACY_SOAP_FIELDS or
                question.get("questionOptions", {}).get("concept") in LEGACY_SOAP_FIELDS.values()):
            errors.append(f"{field_id}: SOAP capture does not belong in the physical-exam form")

    for field_id in sorted(SEGMENTED_FIELD_CONCEPTS.keys() & questions.keys()):
        question = questions[field_id]
        options = question.get("questionOptions")
        if not isinstance(options, dict):
            errors.append(f"{field_id}: questionOptions must be an object")
            continue
        expected_concept = SEGMENTED_FIELD_CONCEPTS[field_id]
        if options.get("concept") != expected_concept:
            errors.append(f"{field_id}: must use concept {expected_concept}")
        if options.get("rendering") != "textarea":
            errors.append(f"{field_id}: must remain an open clinical textarea")
        if "default" in options or "answers" in options:
            errors.append(f"{field_id}: must not auto-populate a normal finding")
        expected_required = field_id in REQUIRED_FIELDS
        if (question.get("required") is True) != expected_required:
            errors.append(f"{field_id}: required must be {expected_required}")

    concepts = list(SEGMENTED_FIELD_CONCEPTS.values())
    if len(concepts) != len(set(concepts)):
        errors.append("segmented physical-exam fields must not reuse one concept for different meanings")

    return errors


def validate_legacy_contract(form):
    errors = []
    if form.get("name") != "CE-SOAP-001-NOTA SOAP" or form.get("version") != "1.2.0":
        errors.append("historical form identity must be preserved")
    if form.get("uuid") != "92b9a6f7-0c70-4fb1-9b31-678226d5ce02":
        errors.append("historical schema UUID must be preserved")
    if form.get("published") is not False or form.get("retired") is not True:
        errors.append("historical outpatient SOAP must be unpublished and retired")
    questions = {node.get("id"): node for node in walk(form) if node.get("type") == "obs"}
    for field_id, concept in SEGMENTED_FIELD_CONCEPTS.items():
        if questions.get(field_id, {}).get("questionOptions", {}).get("concept") != concept:
            errors.append(f"{field_id}: preserve historical question and concept")
    return errors


def main():
    try:
        form = json.loads(FORM_PATH.read_text(encoding="utf-8"))
        legacy = json.loads(LEGACY_FORM_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Unable to load the physical-exam contract: {error}", file=sys.stderr)
        return 1

    errors = validate_contract(form) + validate_legacy_contract(legacy)
    if errors:
        print("Consulta Externa physical-exam contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Validated CE-EXF 1.0.0 physical examination and retired outpatient SOAP history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
