#!/usr/bin/env python3
"""Integridad terminológica entre los formularios AMPATH y los exports OCL.

Comprueba que cada formulario use los conceptos de forma inequívoca y con el
datatype correcto. Dos categorías de comprobación:

  * Bloqueantes: hoy no tienen violaciones, así que cualquier aparición es una
    regresión y falla el CI.
  * Con baseline: la deuda existente está inventariada en
    `form_concept_integrity_baseline.json`. Las violaciones nuevas fallan; las
    inventariadas se listan como deuda pendiente. El baseline solo debe
    encoger: si una entrada deja de reproducirse, el validador exige quitarla.

Regenerar el baseline tras corregir deuda:
    python3 .github/scripts/validate_form_concept_integrity.py --update-baseline
"""
import argparse
import json
import re
import sys
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

OCL_DIR = Path("configuration/ocl")
FORM_DIR = Path("configuration/ampathforms")
BASELINE_PATH = Path(".github/scripts/form_concept_integrity_baseline.json")

# El label promete un código pero el concepto guarda texto libre.
CODE_PROMISING = re.compile(r"\bcie[\s\-]?10\b|\bcpms\b|\bc[oó]digo\b", re.IGNORECASE)

# Renderings que persisten el UUID de una respuesta. Sobre un concepto Text el
# motor guardaría ese UUID como cadena, produciendo datos incomputables.
CODED_RENDERINGS = {
    "select",
    "radio",
    "checkbox",
    "content-switcher",
    "toggle",
    "checkbox-searchable",
}


def load_concept_index(errors):
    """external_id -> metadatos, leído de los ZIP de OCL (nunca de texto plano)."""
    index = {}
    if not OCL_DIR.is_dir():
        errors.append(f"{OCL_DIR}: missing OCL export directory")
        return index

    for zip_path in sorted(OCL_DIR.glob("*concepts*.zip")):
        try:
            with zipfile.ZipFile(zip_path) as archive:
                export = json.loads(archive.read("export.json"))
        except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as error:
            errors.append(f"{zip_path}: cannot read OCL export: {error}")
            continue

        source = export.get("source") or {}
        source_id = source.get("id") if isinstance(source, dict) else export.get("short_code")
        for concept in export.get("concepts", []):
            external_id = concept.get("external_id")
            if isinstance(external_id, str) and external_id:
                index[external_id] = {
                    "source": source_id,
                    "datatype": concept.get("datatype"),
                    "concept_class": concept.get("concept_class"),
                    "display_name": concept.get("display_name"),
                }
    return index


def walk_questions(container):
    """Recorre preguntas, descendiendo a las anidadas en obsGroup."""
    for question in container.get("questions") or []:
        yield question
        yield from walk_questions(question)


def form_questions(form):
    for page in form.get("pages") or []:
        for section in page.get("sections") or []:
            yield from walk_questions(section)


def normalize_label(label):
    if not isinstance(label, str):
        return ""
    text = unicodedata.normalize("NFKD", label.lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def collect(errors):
    """Devuelve (bloqueantes, deuda) como dict clave -> mensaje."""
    index = load_concept_index(errors)
    blocking = {}
    debt = {}

    answer_sets = defaultdict(lambda: defaultdict(list))
    label_owners = defaultdict(set)

    for form_path in sorted(FORM_DIR.glob("*.json")):
        try:
            form = json.loads(form_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{form_path}: cannot load form: {error}")
            continue

        name = form_path.name
        uses_by_concept = defaultdict(list)

        for question in form_questions(form):
            options = question.get("questionOptions") or {}
            concept = options.get("concept")
            question_id = question.get("id") or "?"
            label = question.get("label") or ""
            rendering = options.get("rendering")

            for answer in options.get("answers") or []:
                answer_concept = answer.get("concept")
                if isinstance(answer_concept, str) and answer_concept and answer_concept not in index:
                    key = f"unknown-answer|{name}|{question_id}|{answer_concept}"
                    blocking[key] = (
                        f"{name}:{question_id}: answer concept {answer_concept} "
                        f"is not defined in any OCL export"
                    )

            if not isinstance(concept, str) or not concept:
                continue

            metadata = index.get(concept)
            if metadata is None:
                key = f"unknown-concept|{name}|{question_id}|{concept}"
                blocking[key] = (
                    f"{name}:{question_id}: concept {concept} is not defined in any OCL export"
                )
                continue

            datatype = metadata.get("datatype")
            uses_by_concept[concept].append((question_id, label))
            label_owners[normalize_label(label)].add(concept)

            if rendering in CODED_RENDERINGS and datatype == "Text":
                key = f"coded-over-text|{name}|{question_id}"
                blocking[key] = (
                    f"{name}:{question_id}: rendering '{rendering}' stores an answer UUID, "
                    f"but concept {concept} is Text; use a Coded concept instead"
                )

            if CODE_PROMISING.search(label) and datatype == "Text":
                key = f"code-as-text|{name}|{question_id}"
                debt[key] = (
                    f"{name}:{question_id}: label promises a code ('{label}') "
                    f"but concept {concept} is Text"
                )

            answers = options.get("answers") or []
            codes = tuple(sorted(a.get("concept") for a in answers if a.get("concept")))
            if codes:
                answer_sets[concept][codes].append(f"{name}:{question_id}")

        for concept, uses in uses_by_concept.items():
            distinct = {normalize_label(label) for _, label in uses}
            if len(uses) > 1 and len(distinct) > 1:
                key = f"collision|{name}|{concept}"
                rendered = ", ".join(f"{qid} ('{label}')" for qid, label in uses)
                debt[key] = (
                    f"{name}: concept {concept} is reused by {len(uses)} questions with "
                    f"different meanings: {rendered}"
                )

    for concept, variants in answer_sets.items():
        if len(variants) > 1:
            key = f"answer-set|{concept}"
            detail = "; ".join(
                f"{len(codes)} answers in {', '.join(sorted(users))}" for codes, users in variants.items()
            )
            debt[key] = f"concept {concept} has divergent answer sets: {detail}"

    for label, concepts in label_owners.items():
        if label and len(concepts) > 1:
            key = f"duplicate-label|{label}"
            debt[key] = (
                f"label '{label}' is backed by {len(concepts)} different concepts: "
                f"{', '.join(sorted(concepts))}"
            )

    return blocking, debt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()

    errors = []
    blocking, debt = collect(errors)

    if args.update_baseline:
        BASELINE_PATH.write_text(json.dumps(sorted(debt), indent=2, ensure_ascii=False) + "\n")
        print(f"[OK] baseline rewritten with {len(debt)} known issues")
        return 0

    try:
        baseline = set(json.loads(BASELINE_PATH.read_text()))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{BASELINE_PATH}: cannot load baseline: {error}")
        baseline = set()

    for key in sorted(blocking):
        errors.append(blocking[key])

    new_debt = sorted(set(debt) - baseline)
    for key in new_debt:
        errors.append(f"new terminology debt (not in baseline): {debt[key]}")

    stale = sorted(baseline - set(debt))
    for key in stale:
        errors.append(
            f"baseline entry no longer reproduces and must be removed: {key} "
            f"(run --update-baseline)"
        )

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    print(
        f"[OK] form/concept integrity: {len(debt)} known issues pending in the baseline, "
        f"no blocking violations and no regressions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
