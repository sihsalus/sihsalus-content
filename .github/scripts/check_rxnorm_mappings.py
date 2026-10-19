#!/usr/bin/env python3
"""Report NLM currency of shipped active RxNorm mappings; never approve or change them."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import urllib.request

from split_ocl_export import read_export


NLM_URL = "https://rxnav.nlm.nih.gov/REST/"
TIMEOUT = 20


def get_json(endpoint):
    request = urllib.request.Request(NLM_URL + endpoint, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.load(response)


def inventory(directory):
    """Discover the source by metadata, retaining every mapping reference per RXCUI."""
    sources, references = [], {}
    for path in sorted(directory.glob("*.zip")):
        export = read_export(path)
        source = export.get("source") or {}
        identities = {export.get("short_code"), source.get("short_code"), source.get("id")} - {None}
        if "medicamentos" not in identities:
            continue
        if identities != {"medicamentos"}:
            raise ValueError("Conflicting medicamentos source identity")
        release = export.get("version")
        if (export.get("owner") != "SIHSALUS" or source.get("owner") != "SIHSALUS"
                or export.get("released") is not True or not isinstance(release, str) or not release.strip()
                or release.casefold() == "head" or export.get("id") != release):
            raise ValueError("Expected an identified, released SIHSALUS medicamentos version")
        if sources and any(item["version"] != release for item in sources):
            raise ValueError("Multiple medicamentos releases cannot be checked as one inventory")
        sources.append({"file": path.name, "source": "medicamentos", "version": release,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        for mapping in export["mappings"]:
            if mapping.get("retired") is True:
                continue
            target = mapping.get("to_source_name")
            target_url = mapping.get("to_source_url")
            if any(value is not None and not isinstance(value, str) for value in (target, target_url)):
                raise ValueError("Mapping target source name and URL must be strings")
            target, target_url = (target or "").strip(), (target_url or "").strip()
            target_id = urlsplit(target_url).path.rstrip("/").split("/")[-1]
            targets = [item.casefold() for item in (target, target_id) if item]
            if not targets:
                raise ValueError("Active mapping target source identity is missing")
            if "rxnorm" not in targets:
                continue
            if any(item != "rxnorm" for item in targets):
                raise ValueError("Conflicting RxNorm target source identity")
            if mapping.get("type") != "Mapping" or mapping.get("retired") is not False:
                raise ValueError("RxNorm mapping type or active state is missing")
            if (mapping.get("source") != "medicamentos" or mapping.get("owner", "SIHSALUS") != "SIHSALUS"
                    or any(not isinstance(mapping.get(key), str) or not mapping[key].strip()
                           for key in ("id", "from_concept_code", "map_type"))):
                raise ValueError("RxNorm mapping identity, relationship or source is missing or inconsistent")
            code = str(mapping.get("to_concept_code", ""))
            references.setdefault(code, []).append({
                "file": path.name, "version": export.get("version"), "mapping_id": mapping.get("id"),
                "map_type": mapping["map_type"], "from_concept_code": mapping.get("from_concept_code"),
                "from_source_url": mapping.get("from_source_url"), "to_source": target or target_id,
                "to_source_url": target_url,
            })
    if not sources or not references:
        raise ValueError("No active RxNorm mappings found in the medicamentos inventory")
    return sources, references


def version(fetch):
    payload = fetch("version.json")
    if not isinstance(payload, dict) or any(
        not isinstance(payload.get(key), str) or not payload[key].strip() for key in ("version", "apiVersion")
    ):
        raise ValueError("Incomplete NLM version response")
    return {key: payload[key] for key in ("version", "apiVersion")}


def history(code, payload):
    record = payload["rxcuiStatusHistory"]
    metadata, attributes = record["metaData"], record["attributes"]
    if attributes["rxcui"] != code:
        raise ValueError("NLM response RXCUI does not match the requested code")
    if not isinstance(metadata["status"], str) or not metadata["status"] or metadata["isCurrent"] not in ("YES", "NO"):
        raise ValueError("Incomplete NLM status response")
    name, tty = attributes.get("name"), attributes.get("tty")
    if any(value is not None and not isinstance(value, str) for value in (name, tty)) or (
        metadata["status"] == "Active" and any(not isinstance(value, str) or not value.strip() for value in (name, tty))
    ):
        raise ValueError("Incomplete NLM attributes response")
    return {
        "result": "CURRENT" if metadata["status"] == "Active" and metadata["isCurrent"] == "YES" else "REVIEW",
        "name": name, "tty": tty,
        "nlm_status": metadata["status"], "is_current": metadata["isCurrent"],
    }


def check(directory, fetch=None):
    fetch = fetch or get_json
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "nlm_url": NLM_URL,
        "scope": "Terminology currency only; active RXCUI does not approve clinical mapping equivalence.",
        "nlm_version": None, "sources": [], "results": [], "errors": [],
    }
    try:
        report["sources"], references = inventory(directory)
        report["nlm_version"] = version(fetch)
        for code, refs in sorted(references.items()):
            result = {"rxcui": code, "references": refs, "result": "ERROR", "name": None, "tty": None,
                      "nlm_status": None, "is_current": None}
            try:
                if not re.fullmatch(r"[0-9]+", code):
                    raise ValueError("RXCUI must contain only ASCII digits")
                result.update(history(code, fetch(f"rxcui/{code}/historystatus.json")))
            except Exception as error:  # Preserve other results while making any failed check non-successful.
                result["error"] = str(error)
            report["results"].append(result)
        report["nlm_version_after"] = version(fetch)
        if report["nlm_version_after"] != report["nlm_version"]:
            raise ValueError("NLM version changed during review; repeat the check")
    except Exception as error:
        report["errors"].append(str(error))
    outcomes = {item["result"] for item in report["results"]}
    code = 2 if report["errors"] or "ERROR" in outcomes else 1 if "REVIEW" in outcomes else 0
    report["result"] = {0: "CURRENT", 1: "REVIEW", 2: "ERROR"}[code]
    return report, code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocl-dir", type=Path, default=Path(__file__).resolve().parents[2] / "configuration/ocl")
    args = parser.parse_args(argv)
    report, code = check(args.ocl_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
