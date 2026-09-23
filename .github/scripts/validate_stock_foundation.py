#!/usr/bin/env python3
"""Validate the reproducible, zero-balance Stock Management foundation."""

from __future__ import annotations

import csv
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configuration"
CONCEPTS = CONFIG / "concepts" / "stock_foundation_concepts.csv"
CONCEPT_SETS = CONFIG / "conceptsets" / "stock_foundation_concept_sets.csv"
GLOBAL_PROPERTIES = CONFIG / "globalproperties" / "globalproperties-sihsalus.xml"
PRIVILEGES = CONFIG / "privileges" / "privileges_core-demo.csv"
STOCK_ROLES = CONFIG / "roles" / "roles_stockmanagement.csv"
CLINICAL_ROLES = CONFIG / "roles" / "roles-core.csv"

CATALOGS = {
    "packing": "bce2b1af-98b1-48a2-98a2-3e4ffb3c79c2",
    "dispensing": "162402AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "adjustment": "3bbfaa44-d5b8-404d-b4c1-2bf49ad8ce25",
    "stock_take": "47f0825e-8648-47c2-b847-d3197ed6bb72",
    "source": "2e1e8049-9cbe-4a2d-b1e5-8a91e5d7d97d",
    "category": "6d24eb6e-b42f-4706-ab2d-ae4472161f6a",
}

EXPECTED_MEMBER_COUNTS = {
    CATALOGS["packing"]: 8,
    CATALOGS["dispensing"]: 14,
    CATALOGS["adjustment"]: 5,
    CATALOGS["stock_take"]: 4,
    CATALOGS["source"]: 4,
    CATALOGS["category"]: 5,
}

EXPECTED_GLOBAL_PROPERTIES = {
    "stockmanagement.stockSourceCodeConceptId": CATALOGS["source"],
    "stockmanagement.stockAdjustmentReasonCodeConceptId": CATALOGS["adjustment"],
    "stockmanagement.dispensingUnitsConceptId": CATALOGS["dispensing"],
    "stockmanagement.packagingUnitsConceptId": CATALOGS["packing"],
    "stockmanagement.stockItemCategoryConceptId": CATALOGS["category"],
    "stockmanagement.negativeStockBalanceAllowed": "false",
}

ROLE_UUIDS = {
    "Stock Management Base Role": "7d8d214d-2188-11ed-9dff-507b9dea1806",
    "Inventory Manager": "cca4be4b-2188-11ed-9dff-507b9dea1806",
    "Inventory Administrator": "2083fd40-3391-11ed-a667-507b9dea1806",
    "Inventory Clerk": "d210eb66-2188-11ed-9dff-507b9dea1806",
    "Inventory Provider Access": "8ee2f2ac-467f-11ed-8109-00155dcc3fc0",
    "Inventory Dispensing": "84bdd876-4694-11ed-8109-00155dcc3fc0",
    "Inventory Reporting": "a49be648-6b0a-11ed-93a2-806d973f13a9",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split_values(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def main() -> int:
    errors: list[str] = []

    concept_rows = read_csv(CONCEPTS)
    concept_uuids = [row["Uuid"].strip() for row in concept_rows]
    if len(concept_uuids) != len(set(concept_uuids)):
        errors.append("stock_foundation_concepts.csv contains duplicate UUIDs")
    for catalog_name, catalog_uuid in CATALOGS.items():
        if catalog_name != "dispensing" and catalog_uuid not in concept_uuids:
            errors.append(f"missing local {catalog_name} catalog concept {catalog_uuid}")

    set_rows = read_csv(CONCEPT_SETS)
    relationships = [(row["Concept"].strip(), row["Member"].strip()) for row in set_rows]
    if len(relationships) != len(set(relationships)):
        errors.append("stock_foundation_concept_sets.csv contains duplicate memberships")
    for catalog_uuid, expected_count in EXPECTED_MEMBER_COUNTS.items():
        actual_count = sum(parent == catalog_uuid for parent, _member in relationships)
        if actual_count != expected_count:
            errors.append(
                f"catalog {catalog_uuid} has {actual_count} declared members; expected {expected_count}"
            )

    root = ET.parse(GLOBAL_PROPERTIES).getroot()
    global_properties: dict[str, list[str]] = {}
    for node in root.findall(".//globalProperty"):
        name = (node.findtext("property") or "").strip()
        value = (node.findtext("value") or "").strip()
        global_properties.setdefault(name, []).append(value)
    for name, expected_value in EXPECTED_GLOBAL_PROPERTIES.items():
        values = global_properties.get(name, [])
        if values != [expected_value]:
            errors.append(f"global property {name} is {values!r}; expected exactly [{expected_value!r}]")

    privilege_rows = read_csv(PRIVILEGES)
    privilege_names = {row["Privilege name"].strip() for row in privilege_rows}
    if "app:gestionInventario.configuracion.editar" not in privilege_names:
        errors.append("missing app:gestionInventario.configuracion.editar")

    role_rows = read_csv(STOCK_ROLES)
    roles_by_name = {row["Role name"].strip(): row for row in role_rows}
    for role_name, expected_uuid in ROLE_UUIDS.items():
        row = roles_by_name.get(role_name)
        if not row or row["Uuid"].strip() != expected_uuid:
            errors.append(f"role {role_name} is missing or does not use canonical UUID {expected_uuid}")

    provider_role = roles_by_name.get("Inventory Provider Access", {})
    provider_privileges = split_values(provider_role.get("Privileges", ""))
    for required in (
        "App: stockmanagement.stockItems",
        "Task: stockmanagement.stockItems.dispense.qty",
    ):
        if required not in provider_privileges:
            errors.append(f"Inventory Provider Access is missing {required}")

    admin_role = roles_by_name.get("Inventory Administrator", {})
    admin_privileges = split_values(admin_role.get("Privileges", ""))
    if "app:gestionInventario.configuracion.editar" not in admin_privileges:
        errors.append("Inventory Administrator is missing configuration edit UI privilege")

    clinical_rows = read_csv(CLINICAL_ROLES)
    clinical_roles_by_name = {row["Role name"].strip(): row for row in clinical_rows}
    clinical_inheritance = {
        role_name: split_values(row["Inherited roles"])
        for role_name, row in clinical_roles_by_name.items()
    }
    for role_name in ("SIHSALUS Consulta Externa", "Farmacia"):
        if "Inventory Provider Access" not in clinical_inheritance.get(role_name, set()):
            errors.append(f"{role_name} must inherit Inventory Provider Access")

    pharmacy_role = clinical_roles_by_name.get("Farmacia", {})
    pharmacy_privileges = split_values(pharmacy_role.get("Privileges", ""))
    for required in ("Get Concept Sources", "Get Medication Dispense", "Edit Medication Dispense"):
        if required not in pharmacy_privileges:
            errors.append(f"Farmacia is missing medication dispense privilege {required}")

    if errors:
        print("Stock foundation validation FAILED:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "Stock foundation validation passed: 6 catalogs, 7 canonical roles, "
        "read-only clinical availability, negative balances disabled."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
