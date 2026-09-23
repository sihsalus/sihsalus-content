#!/usr/bin/env python3
"""Protect the segmented physical-examination contract for Consulta Externa."""

import json
import sys
from pathlib import Path


FORM_PATH = Path(
    "configuration/ampathforms/CE-SOAP-001-NOTA SOAP.json"
)
EXPECTED_NAME = "CE-SOAP-001-NOTA SOAP"
EXPECTED_VERSION = "1.2.0"
REQUIRED_FIELDS = {"estadoGeneral"}
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
LEGACY_SOAP_FIELDS = {"soapSubjetivo", "soapObjetivo", "soapEvaluacion", "soapPlan"}


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
            f"form version must remain {EXPECTED_VERSION}; do not overwrite historical 1.0.0 or 1.1.0"
        )

    questions = {
        node.get("id"): node
        for node in walk(form)
        if isinstance(node.get("id"), str) and node.get("type") == "obs"
    }
    missing = SEGMENTED_FIELD_CONCEPTS.keys() - questions.keys()
    if missing:
        errors.append(f"missing segmented physical-exam fields: {sorted(missing)}")

    duplicated_soap = LEGACY_SOAP_FIELDS & questions.keys()
    if duplicated_soap:
        errors.append(f"physical examination must not duplicate SOAP fields: {sorted(duplicated_soap)}")

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


def main():
    try:
        form = json.loads(FORM_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Unable to load {FORM_PATH}: {error}", file=sys.stderr)
        return 1

    errors = validate_contract(form)
    if errors:
        print("Consulta Externa physical-exam contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "Validated CE-SOAP 1.2.0 segmented general/regional examination without "
        "automatic normal findings."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
