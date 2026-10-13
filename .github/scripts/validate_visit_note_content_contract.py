#!/usr/bin/env python3
"""Validate the content contract consumed by the O3 Visit Notes workspace."""

import argparse
import csv
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path


CONTRACT_PATH = Path("docs/contracts/visit-note-content-contract.json")
ENCOUNTER_TYPES_PATH = Path(
    "configuration/encountertypes/encountertypes.csv"
)
METADATA_MAPPINGS_PATH = Path(
    "configuration/metadatatermmappings/"
    "metadatatermmappings-core-sihsalus.csv"
)
EXPECTED_FORM = {
    "uuid": "c75f120a-04ec-11e3-8780-2b40bef9a44b",
    "name": "Visit Note",
    "version": "1.0",
    "published": False,
    "retired": False,
    "encounterTypeUuid": "d7151f82-c1f3-4152-a605-2f9ea7414a79",
}
EXPECTED_ENCOUNTER_TYPE = {
    "uuid": "d7151f82-c1f3-4152-a605-2f9ea7414a79",
    "name": "Notas de Atención",
    "description": "Registro de observaciones clínicas y evolución del paciente en cada consulta.",
    "retired": False,
}


def read_json(path, errors):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{path}: cannot read JSON: {error}")
        return {}


def validate_contract_shape(contract):
    errors = []
    if contract.get("_version") != 1:
        errors.append(f"{CONTRACT_PATH}: _version must be 1")
    if contract.get("form") != EXPECTED_FORM:
        errors.append(f"{CONTRACT_PATH}: canonical Visit Note form metadata changed")
    if contract.get("encounterType") != EXPECTED_ENCOUNTER_TYPE:
        errors.append(f"{CONTRACT_PATH}: canonical Visit Note encounter type metadata changed")
    concepts = contract.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        errors.append(f"{CONTRACT_PATH}: concepts must be a non-empty list")
        return errors

    config_keys = [item.get("configKey") for item in concepts if isinstance(item, dict)]
    if len(config_keys) != len(concepts) or any(not key for key in config_keys):
        errors.append(f"{CONTRACT_PATH}: every concept needs a configKey")
    if len(set(config_keys)) != len(config_keys):
        errors.append(f"{CONTRACT_PATH}: concept configKey values must be unique")
    for item in concepts:
        if not isinstance(item, dict) or not re.fullmatch(
            r"[0-9a-fA-F-]{36}|[0-9A-Za-z]{36}", str(item.get("uuid", ""))
        ):
            errors.append(f"{CONTRACT_PATH}: invalid concept entry: {item!r}")
    return errors


def load_concept_catalog(root, errors):
    """Return uuid -> datatype -> sources from active package concept definitions."""
    catalog = defaultdict(lambda: defaultdict(list))
    concept_dir = root / "configuration/concepts"
    for csv_path in sorted(concept_dir.glob("*.csv")):
        try:
            with csv_path.open(newline="") as stream:
                for row in csv.DictReader(stream):
                    if str(row.get("Void/Retire", "")).strip().lower() in {"true", "1", "yes"}:
                        continue
                    concept_uuid = str(row.get("Uuid", "")).strip()
                    datatype = str(row.get("Data type", "")).strip()
                    if concept_uuid and datatype:
                        catalog[concept_uuid][datatype].append(str(csv_path.relative_to(root)))
        except (OSError, csv.Error) as error:
            errors.append(f"{csv_path}: cannot read concept CSV: {error}")

    ocl_dir = root / "configuration/ocl"
    for zip_path in sorted(ocl_dir.glob("*concepts*.zip")):
        try:
            with zipfile.ZipFile(zip_path) as archive:
                export = json.loads(archive.read("export.json"))
        except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as error:
            errors.append(f"{zip_path}: cannot read OCL export: {error}")
            continue
        for concept in export.get("concepts", []):
            if concept.get("retired"):
                continue
            concept_uuid = concept.get("external_id")
            datatype = concept.get("datatype")
            if concept_uuid and datatype:
                catalog[concept_uuid][datatype].append(str(zip_path.relative_to(root)))
    return catalog


def validate_concepts(contract, catalog):
    errors = []
    for item in contract.get("concepts", []):
        concept_uuid = item.get("uuid")
        expected = item.get("datatype")
        actual = catalog.get(concept_uuid, {})
        if not actual:
            errors.append(
                f"{CONTRACT_PATH}: {item.get('configKey')} concept {concept_uuid} is not "
                "provided by an active package concept definition"
            )
        elif set(actual) != {expected}:
            rendered = ", ".join(
                f"{datatype} ({', '.join(sources)})" for datatype, sources in actual.items()
            )
            errors.append(
                f"{CONTRACT_PATH}: {item.get('configKey')} concept {concept_uuid} must be "
                f"{expected}, found {rendered}"
            )
    return errors


def active_csv_rows(path, uuid_value):
    with path.open(newline="") as stream:
        return [
            row
            for row in csv.DictReader(stream)
            if row.get("Uuid") == uuid_value
            and str(row.get("Void/Retire", "")).strip().lower() not in {"true", "1", "yes"}
        ]


def validate_encounter_metadata(root, contract):
    errors = []
    encounter_uuid = contract["form"]["encounterTypeUuid"]
    encounter_path = root / ENCOUNTER_TYPES_PATH
    mapping_path = root / METADATA_MAPPINGS_PATH
    try:
        rows = active_csv_rows(encounter_path, encounter_uuid)
        if len(rows) != 1:
            errors.append(f"{encounter_path}: expected one active {encounter_uuid} row, found {len(rows)}")
        elif (
            rows[0].get("Name") != contract["encounterType"]["name"]
            or rows[0].get("Description") != contract["encounterType"]["description"]
        ):
            errors.append(f"{encounter_path}: canonical Visit Note encounter metadata changed")
    except (OSError, csv.Error) as error:
        errors.append(f"{encounter_path}: cannot read encounter types: {error}")
    try:
        with mapping_path.open(newline="") as stream:
            mappings = [
                row
                for row in csv.DictReader(stream)
                if row.get("Mapping code") == "emr.visitNoteEncounterType"
                and str(row.get("Void/Retire", "")).strip().lower()
                not in {"true", "1", "yes"}
            ]
        if len(mappings) != 1 or mappings[0].get("Metadata Uuid") != encounter_uuid:
            errors.append(
                f"{mapping_path}: emr.visitNoteEncounterType must map exactly once to {encounter_uuid}"
            )
    except (OSError, csv.Error) as error:
        errors.append(f"{mapping_path}: cannot read metadata mappings: {error}")
    return errors


def validate(root):
    errors = []
    contract = read_json(root / CONTRACT_PATH, errors)
    errors.extend(validate_contract_shape(contract))
    if not contract.get("form") or not isinstance(contract.get("concepts"), list):
        return errors
    catalog = load_concept_catalog(root, errors)
    errors.extend(validate_concepts(contract, catalog))
    errors.extend(validate_encounter_metadata(root, contract))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    errors = validate(args.repo_root)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    print("Validated Visit Note form, encounter, concept datatypes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
