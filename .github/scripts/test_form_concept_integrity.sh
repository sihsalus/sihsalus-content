#!/usr/bin/env bash
set -euo pipefail

# Verifica que el validador de integridad terminológica distinga las tres
# situaciones que justifica su existencia: una violación bloqueante nueva,
# deuda nueva fuera del baseline, y deuda corregida que deja el baseline obsoleto.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
validator=".github/scripts/validate_form_concept_integrity.py"
form_dir="configuration/ampathforms"

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

cp -R "${repo_root}/.github" "${repo_root}/configuration" "$work_dir/"
cd "$work_dir"

python3 "$validator" >/dev/null || {
  echo "El estado actual del repositorio debe pasar el validador" >&2
  exit 1
}

# Un rendering codificado sobre un concepto Text guardaría el UUID de la
# respuesta como cadena: debe bloquear, no quedar como deuda.
python3 - "$form_dir" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]) / "CE-ANAM-001-ANAMNESIS.json"
form = json.loads(path.read_text())
for page in form["pages"]:
    for section in page.get("sections", []):
        for question in section.get("questions", []):
            if question.get("id") == "apetito":
                question["questionOptions"]["rendering"] = "select"
                question["questionOptions"]["answers"] = [{"concept": "synthetic-answer-uuid", "label": "Respuesta codificada"}]
path.write_text(json.dumps(form, ensure_ascii=False, indent=2))
PY
if python3 "$validator" >/dev/null 2>&1; then
  echo "El validador aceptó un rendering codificado sobre un concepto Text" >&2
  exit 1
fi
cp -R "${repo_root}/${form_dir}/." "$form_dir/"

# Reutilizar un concepto para una pregunta con otro significado es deuda nueva.
python3 - "$form_dir" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]) / "CE-ANAM-001-ANAMNESIS.json"
form = json.loads(path.read_text())
questions = form["pages"][0]["sections"][1]["questions"]
questions.append({
    "type": "obs",
    "id": "conceptoReutilizado",
    "label": "Pregunta con otro significado",
    "questionOptions": {
        "rendering": "textarea",
        "concept": questions[0]["questionOptions"]["concept"],
    },
})
path.write_text(json.dumps(form, ensure_ascii=False, indent=2))
PY
if python3 "$validator" >/dev/null 2>&1; then
  echo "El validador aceptó una colisión de concepto nueva" >&2
  exit 1
fi
cp -R "${repo_root}/${form_dir}/." "$form_dir/"

# Corregir deuda inventariada debe exigir que el baseline encoja.
python3 - "$form_dir" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]) / "CE-001-CONSULTA EXTERNA.json"
form = json.loads(path.read_text())
for page in form["pages"]:
    for section in page.get("sections", []):
        for question in section.get("questions", []):
            if question.get("id") == "procedimientos":
                question["label"] = "Procedimientos realizados"
path.write_text(json.dumps(form, ensure_ascii=False, indent=2))
PY
if python3 "$validator" >/dev/null 2>&1; then
  echo "El validador no exigió retirar una entrada obsoleta del baseline" >&2
  exit 1
fi

echo "[OK] form/concept integrity validator"
