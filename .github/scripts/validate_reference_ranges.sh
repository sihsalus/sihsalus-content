#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python3 - "$repo_root" <<'PY'
import csv
import json
import math
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path


repo_root = Path(sys.argv[1])
range_dir = repo_root / "configuration/conceptreferencerange"
ocl_dir = repo_root / "configuration/ocl"
programs_path = (
    repo_root
    / "configuration/programs/programs-package-peruhce.csv"
)
roles_dir = repo_root / "configuration/roles"

csv_paths = sorted(range_dir.glob("*.csv"))
zip_paths = sorted(ocl_dir.glob("*.zip"))

if not csv_paths:
    raise SystemExit(f"No reference range CSV files found in: {range_dir}")

if not zip_paths:
    raise SystemExit(f"No OCL ZIP exports found in: {ocl_dir}")

concepts_by_identifier = {}
for zip_path in zip_paths:
    with zipfile.ZipFile(zip_path) as archive:
        try:
            export = json.loads(archive.read("export.json"))
        except KeyError as exc:
            raise SystemExit(f"{zip_path}: missing export.json") from exc

    for concept in export.get("concepts", []):
        if concept.get("retired"):
            continue
        concept_uuid = concept.get("uuid")
        if concept_uuid:
            concepts_by_identifier.setdefault(concept_uuid, concept)
        external_id = concept.get("external_id")
        if external_id:
            concepts_by_identifier.setdefault(external_id, concept)

errors = []
checked = 0
range_uuids = []
range_rows_by_label = {}
pregnancy_criteria = []

CURRENTLY_PREGNANT_UUID = "abaf7d91-e9cb-4569-ab65-2b2ab8226a2c"
LEGACY_GESTATIONAL_AGE_UUID = "0f053bc0-1cc4-4114-a08e-f31d18012e0b"
CANONICAL_GESTATIONAL_AGE_UUID = "1e35f0dd-3bbb-4b45-96fd-2fc590c1b385"
MATERNAL_PROGRAM_UUID = "3cb4ffd6-1b67-4c52-8398-4bf9844a415e"
BOOLEAN_OBS_RE = re.compile(
    r'getLatestObs\(\s*["\']([^"\']+)["\']\s*,[^)]*\)\.getValueBoolean\(\)'
)

for integer_concept_uuid in [
    "5085AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5086AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5242AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5087AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
]:
    concept = concepts_by_identifier.get(integer_concept_uuid)
    allow_decimal = (concept.get("extras") or {}).get("allow_decimal") if concept else None
    if allow_decimal not in {False, 0}:
        errors.append(
            f"OCL concept {integer_concept_uuid} must disallow decimals before "
            "encoding strict NT 042 thresholds as adjacent inclusive integers"
        )

numeric_columns = [
    "Absolute low",
    "Critical low",
    "Normal low",
    "Normal high",
    "Critical high",
    "Absolute high",
]


def as_number(csv_path, line_number, label, field, value, required=False):
    if value is None or not str(value).strip():
        if required:
            errors.append(f"{csv_path}:{line_number}: {label}: empty required {field}")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{csv_path}:{line_number}: {label}: non-numeric {field}: {value!r}")
        return None
    if not math.isfinite(number):
        errors.append(f"{csv_path}:{line_number}: {label}: non-finite {field}: {value!r}")
        return None
    return number


def validate_absolute_bounds(csv_path, line_number, label, row, concept):
    if concept.get("datatype") != "Numeric":
        errors.append(
            f"{csv_path}:{line_number}: {label}: referenced OCL concept is not Numeric"
        )
        return

    is_vital_sign = csv_path.name == "conceptreferencerange_vital_signs.csv"
    extras = concept.get("extras") or {}
    expected_by_field = {
        "Absolute low": extras.get("low_absolute"),
        "Absolute high": extras.get("hi_absolute"),
    }
    for field, expected_raw in expected_by_field.items():
        expected = as_number(
            csv_path, line_number, label, f"OCL {field}", expected_raw
        )
        actual = as_number(
            csv_path, line_number, label, field, row.get(field),
            required=not is_vital_sign and expected is not None,
        )
        if is_vital_sign and actual != expected:
            errors.append(
                f"{csv_path}:{line_number}: {label}: {field} must match the bundled "
                f"ConceptNumeric absolute bound; expected {expected!r}, got {actual!r}"
            )
        elif not is_vital_sign and actual is not None and expected is not None:
            if (field == "Absolute low" and actual < expected) or (
                field == "Absolute high" and actual > expected
            ):
                errors.append(
                    f"{csv_path}:{line_number}: {label}: {field} lies outside the bundled "
                    f"ConceptNumeric absolute bound; bound {expected!r}, got {actual!r}"
                )

    if is_vital_sign and concept.get("external_id") == "5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA":
        critical_high = as_number(
            csv_path, line_number, label, "Critical high", row.get("Critical high")
        )
        if critical_high is not None:
            errors.append(
                f"{csv_path}:{line_number}: {label}: Critical high must be empty; "
                "100% oxygen saturation is not critically high"
            )


for csv_path in csv_paths:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if "Concept Numeric uuid" not in (reader.fieldnames or []):
            errors.append(f"{csv_path}: missing 'Concept Numeric uuid' column")
            continue
        for column in ["Uuid", "Label", *numeric_columns, "Criteria"]:
            if column not in (reader.fieldnames or []):
                errors.append(f"{csv_path}: missing '{column}' column")

        for line_number, row in enumerate(reader, start=2):
            checked += 1
            label = (row.get("Label") or "").strip()
            range_uuid = (row.get("Uuid") or "").strip()
            if range_uuid:
                range_uuids.append((range_uuid, csv_path, line_number))
            if label:
                range_rows_by_label[label] = (csv_path, line_number, row)

            concept_uuid = (row.get("Concept Numeric uuid") or "").strip()
            if not concept_uuid:
                errors.append(f"{csv_path}:{line_number}: empty Concept Numeric uuid")
            elif concept_uuid not in concepts_by_identifier:
                errors.append(
                    f"{csv_path}:{line_number}: Concept Numeric uuid not found "
                    f"in bundled OCL exports: {concept_uuid}"
                )
            else:
                validate_absolute_bounds(
                    csv_path,
                    line_number,
                    label,
                    row,
                    concepts_by_identifier[concept_uuid],
                )

            concept = concepts_by_identifier.get(concept_uuid) or {}
            is_oxygen_saturation = (
                concept.get("external_id")
                == "5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            )
            required_numeric_columns = {
                "Critical low",
                "Normal low",
                "Normal high",
            }
            if not is_oxygen_saturation:
                required_numeric_columns.add("Critical high")
            values = [
                as_number(
                    csv_path,
                    line_number,
                    label,
                    column,
                    row.get(column),
                    required=column in required_numeric_columns,
                )
                for column in numeric_columns
            ]
            present_values = [value for value in values if value is not None]
            if present_values != sorted(present_values):
                errors.append(
                    f"{csv_path}:{line_number}: {label}: reference range values "
                    f"must be monotonic when present: {values}"
                )

            criteria = row.get("Criteria") or ""
            if (
                csv_path.name == "conceptreferencerange_vital_signs.csv"
                and "gestante" in label.lower()
            ):
                pregnancy_criteria.append((csv_path, line_number, label, criteria))
                required_fragments = [
                    '$patient.getGender().equals("F")',
                    f'$fn.isEnrolledInProgram("{MATERNAL_PROGRAM_UUID}", $patient, $date)',
                    f'{{$fn.getLatestObs("{CANONICAL_GESTATIONAL_AGE_UUID}", $patient)}}.?[',
                    "#this != null",
                    "#this.getValueNumeric() != null",
                    "].size() == 1",
                ]
                for fragment in required_fragments:
                    if fragment not in criteria:
                        errors.append(
                            f"{csv_path}:{line_number}: {label}: pregnancy criteria "
                            f"must contain {fragment!r}"
                        )
                if criteria.count("getLatestObs(") != 1:
                    errors.append(
                        f"{csv_path}:{line_number}: {label}: pregnancy criteria must "
                        "resolve gestational age exactly once"
                    )
                for obsolete_uuid in [CURRENTLY_PREGNANT_UUID, LEGACY_GESTATIONAL_AGE_UUID]:
                    if obsolete_uuid in criteria:
                        errors.append(
                            f"{csv_path}:{line_number}: {label}: pregnancy criteria "
                            f"must not use obsolete concept {obsolete_uuid}"
                        )

                if "0 - <14 wks" in label:
                    expected_band = (
                        "#this.getValueNumeric() >= 0 && "
                        "#this.getValueNumeric() < 14"
                    )
                elif "14 - <28 wks" in label:
                    expected_band = (
                        "#this.getValueNumeric() >= 14 && "
                        "#this.getValueNumeric() < 28"
                    )
                elif "28 - <40 wks" in label:
                    expected_band = (
                        "#this.getValueNumeric() >= 28 && "
                        "#this.getValueNumeric() < 40"
                    )
                else:
                    expected_band = None
                    errors.append(
                        f"{csv_path}:{line_number}: {label}: unknown pregnancy band"
                    )
                if expected_band and expected_band not in criteria:
                    errors.append(
                        f"{csv_path}:{line_number}: {label}: pregnancy criteria "
                        f"must contain exact band {expected_band!r}"
                    )

            for boolean_concept_uuid in BOOLEAN_OBS_RE.findall(criteria):
                boolean_concept = concepts_by_identifier.get(boolean_concept_uuid)
                datatype = boolean_concept.get("datatype") if boolean_concept else None
                if datatype == "Boolean":
                    continue
                errors.append(
                    f"{csv_path}:{line_number}: {label}: getValueBoolean() references "
                    f"{boolean_concept_uuid} with OCL datatype {datatype!r}, not Boolean"
                )

if len(pregnancy_criteria) != 26:
    errors.append(
        f"Expected exactly 26 operational pregnancy ranges, found {len(pregnancy_criteria)}"
    )

canonical_gestational_age = concepts_by_identifier.get(CANONICAL_GESTATIONAL_AGE_UUID)
if not canonical_gestational_age or canonical_gestational_age.get("datatype") != "Numeric":
    errors.append(
        f"Canonical gestational age {CANONICAL_GESTATIONAL_AGE_UUID} must be an active Numeric concept"
    )

with programs_path.open(newline="", encoding="utf-8-sig") as handle:
    maternal_programs = [
        row
        for row in csv.DictReader(handle)
        if (row.get("Uuid") or "").strip() == MATERNAL_PROGRAM_UUID
        and (row.get("Void/Retire") or "").strip().lower() not in {"true", "1", "yes"}
    ]
if len(maternal_programs) != 1:
    errors.append(
        f"Expected one active Madre Gestante program {MATERNAL_PROGRAM_UUID}, "
        f"found {len(maternal_programs)}"
    )

emergency_roles = []
for roles_path in sorted(roles_dir.glob("*.csv")):
    with roles_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (row.get("Role name") or "").strip() == "Personal de Emergencia":
                emergency_roles.append((roles_path, row))
if len(emergency_roles) != 1:
    errors.append(
        f"Expected one Personal de Emergencia role, found {len(emergency_roles)}"
    )
else:
    roles_path, emergency_role = emergency_roles[0]
    privileges = {
        privilege.strip()
        for privilege in (emergency_role.get("Privileges") or "").split(";")
        if privilege.strip()
    }
    if "Get Patient Programs" not in privileges:
        errors.append(
            f"{roles_path}: Personal de Emergencia requires Get Patient Programs "
            "to evaluate pregnancy episode criteria"
        )

duplicates = [uuid for uuid, count in Counter(uuid for uuid, _, _ in range_uuids).items() if count > 1]
if duplicates:
    for duplicate_uuid in duplicates:
        locations = [
            f"{csv_path}:{line_number}"
            for uuid, csv_path, line_number in range_uuids
            if uuid == duplicate_uuid
        ]
        errors.append(f"Duplicate reference range UUID {duplicate_uuid}: {', '.join(locations)}")


def require_value(label, field, expected, standard="NT 042-MINSA/DGSP-V.01"):
    if label not in range_rows_by_label:
        errors.append(f"Missing reference range row required by {standard}: {label}")
        return
    csv_path, line_number, row = range_rows_by_label[label]
    value = as_number(
        csv_path, line_number, label, field, row.get(field), required=True
    )
    if value is not None and value != expected:
        errors.append(
            f"{csv_path}:{line_number}: {label}: {field} should be {expected:g} "
            f"as required by {standard}, got {value:g}"
        )


def require_at_most(label, field, threshold):
    if label not in range_rows_by_label:
        errors.append(f"Missing reference range row required by NT 042-MINSA/DGSP-V.01: {label}")
        return
    csv_path, line_number, row = range_rows_by_label[label]
    value = as_number(csv_path, line_number, label, field, row.get(field))
    if value is not None and value > threshold:
        errors.append(
            f"{csv_path}:{line_number}: {label}: {field} must be <= {threshold:g} "
            f"to avoid rejecting/underflagging NT 042-MINSA/DGSP-V.01 priority-I values; got {value:g}"
        )


def require_at_least(label, field, threshold):
    if label not in range_rows_by_label:
        errors.append(f"Missing reference range row required by NT 042-MINSA/DGSP-V.01: {label}")
        return
    csv_path, line_number, row = range_rows_by_label[label]
    value = as_number(csv_path, line_number, label, field, row.get(field))
    if value is not None and value < threshold:
        errors.append(
            f"{csv_path}:{line_number}: {label}: {field} must be >= {threshold:g} "
            f"to avoid rejecting/underflagging NT 042-MINSA/DGSP-V.01 priority-I values; got {value:g}"
        )


adult_labels = ["adulto 18 - <60 yrs", "adulto mayor >=60 yrs"]
for suffix in adult_labels:
    require_value(f"Frecuencia cardiaca {suffix}", "Critical low", 49)
    require_value(f"Frecuencia cardiaca {suffix}", "Critical high", 151)
    require_at_most(f"Frecuencia cardiaca {suffix}", "Absolute low", 49)
    require_at_least(f"Frecuencia cardiaca {suffix}", "Absolute high", 151)

    require_value(f"Presion sistolica {suffix}", "Critical low", 89)
    require_value(f"Presion sistolica {suffix}", "Critical high", 221)
    require_at_most(f"Presion sistolica {suffix}", "Absolute low", 89)
    require_at_least(f"Presion sistolica {suffix}", "Absolute high", 221)

    require_value(f"Presion diastolica {suffix}", "Critical high", 111)
    require_at_least(f"Presion diastolica {suffix}", "Absolute high", 111)

    require_value(f"Frecuencia respiratoria {suffix}", "Critical low", 9)
    require_value(f"Frecuencia respiratoria {suffix}", "Critical high", 36)
    require_at_most(f"Frecuencia respiratoria {suffix}", "Absolute low", 9)
    require_at_least(f"Frecuencia respiratoria {suffix}", "Absolute high", 36)

for suffix in ["0 - <14 wks", "14 - <28 wks", "28 - <40 wks"]:
    require_value(f"Presion sistolica gestante {suffix}", "Critical low", 89)
    require_value(f"Presion sistolica gestante {suffix}", "Normal low", 90)

for label in ["0 - <6 wks", "6 - <1 yrs"]:
    require_value(f"Frecuencia cardiaca {label}", "Critical low", 60)
    require_value(f"Frecuencia cardiaca {label}", "Critical high", 200)
    require_value(f"Presion sistolica {label}", "Critical low", 59)
    require_value(f"Saturación de oxígeno {label}", "Critical low", 85)

require_value("Frecuencia respiratoria 0 - <2 mos", "Critical high", 60)
require_value("Frecuencia respiratoria 2 mos - <1 yrs", "Critical high", 50)

for label in ["1 - <2 yrs", "2 - <6 yrs"]:
    require_value(f"Frecuencia cardiaca {label}", "Critical low", 60)
    require_value(f"Frecuencia cardiaca {label}", "Critical high", 180)
    require_value(f"Presion sistolica {label}", "Critical low", 79)
    require_value(f"Frecuencia respiratoria {label}", "Critical high", 41)
    require_value(f"Saturación de oxígeno {label}", "Critical low", 85)

for label, normal_low in [
    ("Hemoglobina 24 - 59 meses", 11),
    ("Hemoglobina gestante 0 - <14 wks", 11),
    ("Hemoglobina gestante 14 - <28 wks", 10.5),
    ("Hemoglobina gestante 28 - <40 wks", 11),
]:
    require_value(label, "Normal low", normal_low, "NTS 213-MINSA/DGIESP-2024, tabla 13")

if errors:
    print("Reference range validation failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(
    f"Validated {checked} reference range rows against "
    f"{len(concepts_by_identifier)} OCL concept identifiers from {len(zip_paths)} ZIP exports."
)
PY
