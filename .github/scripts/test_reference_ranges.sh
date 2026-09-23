#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
validator=".github/scripts/validate_reference_ranges.sh"
ocl_dir="configuration/ocl"
range_dir="configuration/conceptreferencerange"
hemoglobin_uuid="0ffe780c-a3ee-4c9c-b4dd-bf2e0f79dc7f"
saturation_uuid="5092AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT
cp -R "${repo_root}/.github" "${repo_root}/configuration" "$work_dir/"
cd "$work_dir"
cp -R "$ocl_dir" "$work_dir/original-ocl"
cp -R "$range_dir" "$work_dir/original-ranges"

reset_fixture() {
  cp -R "$work_dir/original-ocl/." "$ocl_dir/"
  cp -R "$work_dir/original-ranges/." "$range_dir/"
}

expect_failure() {
  if bash "$validator" >"$work_dir/result.log" 2>&1; then
    echo "El validador aceptó una fixture inválida: $1" >&2
    exit 1
  fi
  if ! grep -Fq "$1" "$work_dir/result.log"; then
    cat "$work_dir/result.log" >&2
    echo "La fixture falló por una causa distinta de: $1" >&2
    exit 1
  fi
}

# Modifica exclusivamente un concepto de la copia temporal, conservando el ZIP.
mutate_concept() {
  python3 - "$ocl_dir" "$1" "$2" <<'PY'
import json
import pathlib
import sys
import zipfile

changes = json.loads(sys.argv[3])
matches = 0
for path in sorted(pathlib.Path(sys.argv[1]).glob("*.zip")):
    with zipfile.ZipFile(path) as archive:
        entries = [(info, archive.read(info)) for info in archive.infolist()]
    export = json.loads(next(data for info, data in entries if info.filename == "export.json"))
    changed = False
    for concept in export.get("concepts", []):
        if concept.get("external_id") != sys.argv[2] or concept.get("retired"):
            continue
        for key, value in changes.items():
            if key == "extras":
                concept.setdefault("extras", {}).update(value)
            else:
                concept[key] = value
        matches += 1
        changed = True
    if changed:
        with zipfile.ZipFile(path, "w") as archive:
            for info, data in entries:
                archive.writestr(info, json.dumps(export) if info.filename == "export.json" else data)
assert matches == 1, f"Expected one active fixture concept, found {matches}"
PY
}

mutate_range() {
  python3 - "$range_dir/$1" "$2" "$3" "$4" <<'PY'
import csv
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
with path.open(newline="", encoding="utf-8-sig") as handle:
    reader = csv.DictReader(handle)
    fieldnames = reader.fieldnames
    rows = list(reader)
matches = [row for row in rows if row["Label"] == sys.argv[2]]
assert len(matches) == 1, f"Expected one fixture range, found {len(matches)}"
matches[0][sys.argv[3]] = sys.argv[4]
with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
PY
}

bash "$validator"

# El CSV no puede aceptar valores por encima ni por debajo del ConceptNumeric.
mutate_concept "$hemoglobin_uuid" '{"extras":{"hi_absolute":20}}'
expect_failure "Absolute high lies outside the bundled ConceptNumeric absolute bound"
reset_fixture
mutate_concept "$hemoglobin_uuid" '{"extras":{"low_absolute":1}}'
expect_failure "Absolute low lies outside the bundled ConceptNumeric absolute bound"
reset_fixture
mutate_concept "$hemoglobin_uuid" '{"datatype":"Coded"}'
expect_failure "referenced OCL concept is not Numeric"
reset_fixture

# Omitir el absoluto CSV no puede eludir un límite declarado en OCL.
for field in "Absolute low" "Absolute high"; do
  mutate_concept "$hemoglobin_uuid" '{"extras":{"low_absolute":0,"hi_absolute":30}}'
  mutate_range conceptreferencerange_laboratory.csv "Hemoglobina 24 - 59 meses" "$field" ""
  expect_failure "empty required $field"
  reset_fixture
done

# Laboratorio permite límites más estrechos y no inventa límites ausentes en OCL.
mutate_concept "$hemoglobin_uuid" '{"extras":{"low_absolute":-0.5,"hi_absolute":30.5}}'
bash "$validator" >/dev/null
reset_fixture
mutate_concept "$hemoglobin_uuid" '{"extras":{"low_absolute":null,"hi_absolute":null}}'
bash "$validator" >/dev/null
reset_fixture

for value in NaN Infinity -Infinity; do
  mutate_range conceptreferencerange_laboratory.csv "Hemoglobina 24 - 59 meses" "Absolute high" "$value"
  expect_failure "non-finite Absolute high"
  reset_fixture
  mutate_concept "$hemoglobin_uuid" "{\"extras\":{\"hi_absolute\":\"$value\"}}"
  expect_failure "non-finite OCL Absolute high"
  reset_fixture
done

# Signos vitales mantiene igualdad exacta y saturación sin crítico alto.
mutate_concept "$saturation_uuid" '{"extras":{"low_absolute":-1}}'
expect_failure "Absolute low must match the bundled ConceptNumeric absolute bound"
reset_fixture
mutate_range conceptreferencerange_vital_signs.csv "Saturación de oxígeno 0 - <6 wks" "Critical high" 100
expect_failure "Critical high must be empty"
reset_fixture

mutate_range conceptreferencerange_laboratory.csv "Hemoglobina 24 - 59 meses" "Normal low" 11.1
expect_failure "as required by NTS 213-MINSA/DGIESP-2024, tabla 13"

echo "[OK] reference range validator"
