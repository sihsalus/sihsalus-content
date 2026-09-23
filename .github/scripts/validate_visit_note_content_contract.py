#!/usr/bin/env python3
"""Validate the content contract consumed by the O3 Visit Notes workspace."""

import argparse
import csv
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


CONTRACT_PATH = Path("docs/contracts/visit-note-content-contract.json")
LIQUIBASE_PATH = Path("configuration/liquibase/liquibase.xml")
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
CHANGE_SET_IDS = {
    "ensure-canonical-visit-note-encounter-type-20260823",
    "ensure-canonical-visit-note-form-20260823",
    "link-canonical-visit-note-form-encounter-type-20260823",
    "assert-canonical-visit-note-form-contract-20260823",
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


def validate_liquibase_contract(contract, xml_text, path=LIQUIBASE_PATH):
    errors = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        return [f"{path}: invalid XML: {error}"]
    change_sets = {
        node.get("id"): node for node in root if node.tag.rsplit("}", 1)[-1] == "changeSet"
    }
    for change_set_id in sorted(CHANGE_SET_IDS):
        change_set = change_sets.get(change_set_id)
        if change_set is None:
            errors.append(f"{path}: missing changeSet {change_set_id}")
        elif change_set.get("runAlways") is not None:
            errors.append(
                f"{path}: {change_set_id} must not rely on runAlways because BaseFileLoader "
                "can skip the whole Liquibase file by checksum"
            )

    form_uuid = contract["form"]["uuid"]
    encounter_uuid = contract["form"]["encounterTypeUuid"]
    bootstrap = change_sets.get("ensure-canonical-visit-note-encounter-type-20260823")
    ensure = change_sets.get("ensure-canonical-visit-note-form-20260823")
    link = change_sets.get("link-canonical-visit-note-form-encounter-type-20260823")
    assertion = change_sets.get("assert-canonical-visit-note-form-contract-20260823")
    bootstrap_sql = " ".join("".join(bootstrap.itertext()).split()) if bootstrap is not None else ""
    ensure_sql = " ".join("".join(ensure.itertext()).split()) if ensure is not None else ""
    link_sql = " ".join("".join(link.itertext()).split()) if link is not None else ""
    if (
        encounter_uuid not in bootstrap_sql
        or f"'{contract['encounterType']['name']}'" not in bootstrap_sql
        or f"'{contract['encounterType']['description']}'" not in bootstrap_sql
        or "WHERE NOT EXISTS" not in bootstrap_sql
    ):
        errors.append(f"{path}: encounter type must be bootstrapped idempotently before Visit Note")
    if form_uuid not in ensure_sql or encounter_uuid not in ensure_sql or "WHERE NOT EXISTS" not in ensure_sql:
        errors.append(f"{path}: Visit Note insert must be UUID-idempotent and resolve the encounter type")
    if "'Visit Note'" not in ensure_sql or "'1.0'" not in ensure_sql:
        errors.append(f"{path}: Visit Note insert is missing canonical name/version")
    if form_uuid not in link_sql or encounter_uuid not in link_sql or "encounter_type IS NULL" not in link_sql:
        errors.append(f"{path}: Visit Note link must only complete a missing encounter_type")
    if assertion is not None:
        preconditions = next(
            (node for node in assertion if node.tag.rsplit("}", 1)[-1] == "preConditions"),
            None,
        )
        if preconditions is None or preconditions.get("onFail") != "HALT" or preconditions.get("onError") != "HALT":
            errors.append(f"{path}: Visit Note assertion must HALT on failure and error")
    return errors


def expected_frontend_defaults(contract):
    defaults = {item["configKey"]: item["uuid"] for item in contract.get("concepts", [])}
    defaults["encounterTypeUuid"] = contract["form"]["encounterTypeUuid"]
    defaults["formConceptUuid"] = contract["form"]["uuid"]
    return defaults


def parse_frontend_defaults(schema_text):
    constants_match = re.search(
        r"defaultVisitNoteClinicalConceptUuids\s*=\s*\{(.*?)\}\s*as const",
        schema_text,
        re.DOTALL,
    )
    constants = {}
    if constants_match:
        constants = dict(
            (key, value)
            for key, _quote, value in re.findall(
                r"(\w+)\s*:\s*(['\"])([^'\"]+)\2", constants_match.group(1)
            )
        )
    defaults = {}
    for key, body in re.findall(r"^\s{2}(\w+):\s*\{(.*?)^\s{2}\},", schema_text, re.MULTILINE | re.DOTALL):
        direct = re.search(r"_default:\s*(['\"])([^'\"]+)\1", body)
        indirect = re.search(r"_default:\s*defaultVisitNoteClinicalConceptUuids\.(\w+)", body)
        if direct:
            defaults[key] = direct.group(2)
        elif indirect and indirect.group(1) in constants:
            defaults[key] = constants[indirect.group(1)]
    return defaults


def validate_frontend_schema(contract, schema_text, path):
    errors = []
    actual = parse_frontend_defaults(schema_text)
    for key, expected in expected_frontend_defaults(contract).items():
        if actual.get(key) != expected:
            errors.append(f"{path}: {key} must default to {expected}, found {actual.get(key)!r}")
    return errors


def validate(root, frontend_root=None):
    errors = []
    contract = read_json(root / CONTRACT_PATH, errors)
    errors.extend(validate_contract_shape(contract))
    if not contract.get("form") or not isinstance(contract.get("concepts"), list):
        return errors
    catalog = load_concept_catalog(root, errors)
    errors.extend(validate_concepts(contract, catalog))
    errors.extend(validate_encounter_metadata(root, contract))
    try:
        xml_text = (root / LIQUIBASE_PATH).read_text()
        errors.extend(validate_liquibase_contract(contract, xml_text, root / LIQUIBASE_PATH))
    except OSError as error:
        errors.append(f"{root / LIQUIBASE_PATH}: cannot read XML: {error}")
    if frontend_root is not None:
        schema_path = frontend_root / contract["frontendSchemaRelativePath"]
        try:
            errors.extend(validate_frontend_schema(contract, schema_path.read_text(), schema_path))
        except OSError as error:
            errors.append(f"{schema_path}: cannot read frontend schema: {error}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--frontend-root", type=Path)
    args = parser.parse_args()
    errors = validate(args.repo_root, args.frontend_root)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    frontend_note = " and frontend defaults" if args.frontend_root else ""
    print(f"Validated Visit Note form, encounter, concept datatypes{frontend_note}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
