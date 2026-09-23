#!/usr/bin/env python3
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = Path("configuration")
ATTRIBUTE_TYPES_PATH = CONFIG_ROOT / "attributetypes" / "attribute_types.csv"
LOCATIONS_PATH = CONFIG_ROOT / "locations" / "sihsalus-locations.csv"
INSTITUTIONAL_LOCATION_ATTRIBUTES_PATH = (
    CONFIG_ROOT / "locations" / "hospital-institutional-attributes.csv"
)
GLOBAL_PROPERTIES_PATH = (
    CONFIG_ROOT / "globalproperties" / "globalproperties-sihsalus.xml"
)

HOSPITAL_UUID = "35d2234e-129a-4c40-abb2-1ae0b72c1602"
PHONE_ATTRIBUTE_UUID = "07c79e2a-b4e8-4100-9210-6f87bc9b77c9"
IPRESS_ATTRIBUTE_UUID = "5fd2b028-5b40-4c85-9a65-01a7ea2cde2b"
PHONE_ATTRIBUTE_HEADER = f"Attribute|{PHONE_ATTRIBUTE_UUID}"
IPRESS_ATTRIBUTE_HEADER = f"Attribute|{IPRESS_ATTRIBUTE_UUID}"
FREETEXT_DATATYPE = "org.openmrs.customdatatype.datatype.FreeTextDatatype"

EXPECTED_ATTRIBUTE_TYPES = {
    PHONE_ATTRIBUTE_UUID: {
        "Entity name": "Location",
        "Name": "Teléfono institucional",
        "Min occurs": "0",
        "Max occurs": "1",
        "Datatype classname": FREETEXT_DATATYPE,
    },
    IPRESS_ATTRIBUTE_UUID: {
        "Entity name": "Location",
        "Name": "Código Único IPRESS",
        "Min occurs": "0",
        "Max occurs": "1",
        "Datatype classname": FREETEXT_DATATYPE,
    },
}

EXPECTED_HOSPITAL_LOCATION_VALUES = {
    "Name": "Hospital Santa Clotilde",
    "Description": (
        "Establecimiento de salud principal que brinda servicios integrales de atención "
        "en la región Napo de Loreto."
    ),
    "Parent": "",
    "Address 1": "LORETO",
    "Address 2": "",
    "Address 3": "",
    "Address 4": "",
    "Address 5": "",
    "Address 6": "",
    "City/Village": "SANTA CLOTILDE",
    "County/District": "NAPO",
    "State/Province": "MAYNAS",
    "Postal Code": "",
    "Country": "PERU",
}

EXPECTED_INSTITUTIONAL_ATTRIBUTE_VALUES = {
    **EXPECTED_HOSPITAL_LOCATION_VALUES,
    PHONE_ATTRIBUTE_HEADER: "965 336 199",
    IPRESS_ATTRIBUTE_HEADER: "00000066",
}

OUTPATIENT_QUANTITY_PROPERTY = "drugOrder.requireOutpatientQuantity"


def _is_true(value):
    return (value or "").strip().lower() in {"1", "true", "yes"}


def _read_csv(path, errors):
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            return reader.fieldnames or [], list(reader)
    except (OSError, csv.Error) as error:
        errors.append(f"{path}: no se pudo leer el CSV: {error}")
        return [], []


def _value(row, field):
    return (row.get(field) or "").strip()


def _validate_attribute_types(root, errors):
    path = root / ATTRIBUTE_TYPES_PATH
    headers, rows = _read_csv(path, errors)
    required_headers = {
        "Uuid",
        "Void/Retire",
        "Entity name",
        "Name",
        "Min occurs",
        "Max occurs",
        "Datatype classname",
    }
    missing_headers = required_headers - set(headers)
    if missing_headers:
        errors.append(
            f"{path}: faltan columnas requeridas: {', '.join(sorted(missing_headers))}"
        )
        return

    for attribute_uuid, expected in EXPECTED_ATTRIBUTE_TYPES.items():
        matches = [row for row in rows if _value(row, "Uuid") == attribute_uuid]
        if len(matches) != 1:
            errors.append(
                f"{path}: se esperaba exactamente un tipo de atributo con UUID "
                f"{attribute_uuid}; encontrados {len(matches)}"
            )
            continue

        row = matches[0]
        if _is_true(_value(row, "Void/Retire")):
            errors.append(f"{path}: el tipo de atributo {attribute_uuid} no puede retirarse")

        for field, expected_value in expected.items():
            actual = _value(row, field)
            if actual != expected_value:
                errors.append(
                    f"{path}: {attribute_uuid} debe tener {field}={expected_value!r}; "
                    f"se encontró {actual!r}"
                )

        duplicate_names = [
            candidate
            for candidate in rows
            if _value(candidate, "Name") == expected["Name"]
            and _value(candidate, "Uuid") != attribute_uuid
            and not _is_true(_value(candidate, "Void/Retire"))
        ]
        if duplicate_names:
            errors.append(
                f"{path}: el nombre {expected['Name']!r} está asignado a otro UUID activo"
            )


def _validate_hospital_location(root, errors):
    path = root / LOCATIONS_PATH
    headers, rows = _read_csv(path, errors)
    unsafe_attribute_headers = {
        PHONE_ATTRIBUTE_HEADER,
        IPRESS_ATTRIBUTE_HEADER,
    } & set(headers)
    if unsafe_attribute_headers:
        errors.append(
            f"{path}: el CSV compartido no debe declarar atributos institucionales; "
            "las celdas vacías anularían valores de otras ubicaciones: "
            f"{', '.join(sorted(unsafe_attribute_headers))}"
        )

    required_headers = {
        "Uuid",
        "Void/Retire",
        *EXPECTED_HOSPITAL_LOCATION_VALUES.keys(),
    }
    missing_headers = required_headers - set(headers)
    if missing_headers:
        errors.append(
            f"{path}: faltan columnas requeridas: {', '.join(sorted(missing_headers))}"
        )
        return

    matches = [row for row in rows if _value(row, "Uuid") == HOSPITAL_UUID]
    if len(matches) != 1:
        errors.append(
            f"{path}: se esperaba exactamente una ubicación con UUID {HOSPITAL_UUID}; "
            f"encontradas {len(matches)}"
        )
        return

    row = matches[0]
    if _is_true(_value(row, "Void/Retire")):
        errors.append(f"{path}: Hospital Santa Clotilde no puede estar retirado")

    for field, expected_value in EXPECTED_HOSPITAL_LOCATION_VALUES.items():
        actual = _value(row, field)
        if actual != expected_value:
            errors.append(
                f"{path}: Hospital Santa Clotilde debe tener {field}={expected_value!r}; "
                f"se encontró {actual!r}"
            )


def _validate_institutional_attributes(root, errors):
    path = root / INSTITUTIONAL_LOCATION_ATTRIBUTES_PATH
    headers, rows = _read_csv(path, errors)
    expected_headers = [
        "Uuid",
        "Void/Retire",
        "Name",
        "Description",
        "Parent",
        "Address 1",
        "Address 2",
        "Address 3",
        "Address 4",
        "Address 5",
        "Address 6",
        "City/Village",
        "County/District",
        "State/Province",
        "Postal Code",
        "Country",
        PHONE_ATTRIBUTE_HEADER,
        IPRESS_ATTRIBUTE_HEADER,
        "_order:1100",
    ]
    if headers != expected_headers:
        errors.append(
            f"{path}: las columnas deben ser exactamente {expected_headers!r}; "
            f"se encontró {headers!r}"
        )
        return

    if len(rows) != 1:
        errors.append(
            f"{path}: debe contener únicamente la fila del Hospital Santa Clotilde; "
            f"se encontraron {len(rows)} filas"
        )
        return

    row = rows[0]
    if _value(row, "Uuid") != HOSPITAL_UUID:
        errors.append(
            f"{path}: la única fila debe usar el UUID del hospital {HOSPITAL_UUID}"
        )
    if _is_true(_value(row, "Void/Retire")):
        errors.append(f"{path}: Hospital Santa Clotilde no puede estar retirado")

    for field, expected_value in EXPECTED_INSTITUTIONAL_ATTRIBUTE_VALUES.items():
        actual = _value(row, field)
        if actual != expected_value:
            errors.append(
                f"{path}: Hospital Santa Clotilde debe tener {field}={expected_value!r}; "
                f"se encontró {actual!r}"
            )


def _validate_global_property(root, errors):
    path = root / GLOBAL_PROPERTIES_PATH
    try:
        document = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        errors.append(f"{path}: no se pudo leer el XML: {error}")
        return

    matches = []
    for element in document.findall("./globalProperties/globalProperty"):
        name = (element.findtext("property") or "").strip()
        if name == OUTPATIENT_QUANTITY_PROPERTY:
            matches.append((element.findtext("value") or "").strip())

    if matches != ["true"]:
        errors.append(
            f"{path}: {OUTPATIENT_QUANTITY_PROPERTY} debe aparecer exactamente una vez "
            f"con valor 'true'; se encontró {matches!r}"
        )


def validate(root=REPOSITORY_ROOT):
    root = Path(root)
    errors = []
    _validate_attribute_types(root, errors)
    _validate_hospital_location(root, errors)
    _validate_institutional_attributes(root, errors)
    _validate_global_property(root, errors)
    return errors


def main():
    errors = validate()
    if errors:
        print("Validación de metadata institucional falló:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "Validada la identidad institucional del Hospital Santa Clotilde, sus atributos "
        "y la obligatoriedad de cantidad ambulatoria."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
