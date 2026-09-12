#!/usr/bin/env python3
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from urllib.parse import urlsplit


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def canonical_json_bytes(payload):
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def read_export(path):
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        if members != ["export.json"]:
            raise ValueError(f"{path}: expected only export.json; found {members}")
        export = json.loads(archive.read("export.json"))

    if export.get("type") != "Source Version":
        raise ValueError(f"{path}: expected a Source Version export")
    if not isinstance(export.get("concepts"), list) or not isinstance(export.get("mappings"), list):
        raise ValueError(f"{path}: concepts and mappings must be arrays")
    return export


def write_export(path, export):
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = zipfile.ZipInfo("export.json", ZIP_TIMESTAMP)
    entry.compress_type = zipfile.ZIP_DEFLATED
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    entry.extra = b""
    entry.comment = b""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(entry, canonical_json_bytes(export), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def exclude_retired_records(export, manifest):
    """Exclude only reviewed retired identities; preserve every other record."""
    source = manifest["source"]
    expected = {
        "type": "Source Version", "owner": source["owner"], "owner_type": "Organization",
        "short_code": source["id"], "id": manifest["version"],
        "version": manifest["version"], "released": True,
    }
    if any(export.get(key) != value for key, value in expected.items()):
        raise ValueError("exclusions do not match the released source version")
    if any(export.get("source", {}).get(key) != value for key, value in source.items()):
        raise ValueError("exclusions do not match the source identity")

    result = dict(export)
    excluded_urls = set()
    for kind in ("concepts", "mappings"):
        exclusions = manifest[kind]
        excluded_ids = {item["external_id"] for item in exclusions}
        if len(excluded_ids) != len(exclusions):
            raise ValueError(f"duplicate {kind} exclusions")
        for expected_item in exclusions:
            matches = [item for item in export[kind]
                       if item.get("external_id") == expected_item["external_id"]]
            if len(matches) != 1:
                raise ValueError(f"excluded {kind} identity is missing or duplicated")
            item = matches[0]
            if item.get("retired") is not True:
                raise ValueError(f"cannot exclude active {kind}")
            if item.get("id") != expected_item["id"] or hashlib.sha256(
                canonical_json_bytes(item)
            ).hexdigest() != expected_item["sha256"]:
                raise ValueError(f"excluded {kind} record changed; review the manifest")
            if kind == "concepts":
                excluded_urls.add(urlsplit(item["url"]).path)
        result[kind] = [item for item in export[kind] if item.get("external_id") not in excluded_ids]

    for mapping in result["mappings"]:
        if any(urlsplit(mapping.get(key) or "").path in excluded_urls
               for key in ("from_concept_url", "to_concept_url")):
            raise ValueError("a retained mapping references an excluded concept")
    return result


def split_export(input_path, concepts_path, mappings_path, exclusions_path=None):
    export = read_export(input_path)
    if exclusions_path is not None:
        manifest = json.loads(exclusions_path.read_text(encoding="utf-8"))
        export = exclude_retired_records(export, manifest)

    concepts_export = dict(export)
    concepts_export["mappings"] = []
    write_export(concepts_path, concepts_export)

    mappings_export = dict(export)
    mappings_export["concepts"] = []
    write_export(mappings_path, mappings_export)


def main():
    parser = argparse.ArgumentParser(
        description="Split one official OCL Source Version export reproducibly."
    )
    parser.add_argument("input", type=Path, help="Official combined OCL export ZIP")
    parser.add_argument("concepts_output", type=Path, help="Concepts-only output ZIP")
    parser.add_argument("mappings_output", type=Path, help="Mappings-only output ZIP")
    parser.add_argument("--exclusions", type=Path, help="Reviewed retired-record exclusion manifest")
    arguments = parser.parse_args()

    if arguments.concepts_output == arguments.mappings_output:
        parser.error("concepts and mappings outputs must be different paths")
    split_export(arguments.input, arguments.concepts_output, arguments.mappings_output, arguments.exclusions)


if __name__ == "__main__":
    main()
