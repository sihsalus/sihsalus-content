"""Pure safety/packaging helpers. Importing this module never invokes Docker."""

import csv
import hashlib
import io
import os
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

BACKEND = "ghcr.io/sihsalus/sihsalus-backend@sha256:d03384f0368052101bfb949c0de24547f6e5aaf7caedce874f1eb7c296711fe2"
DISTRO_SHA = "492757585d30b9f2b70c3bbff603d16f635e5d28"
IMAGE_CONTENT_SHA = "57690d4e976ef6d97a925c68103d532d10ee15cf"
BASELINE_SHA = "8000b27f48bf124fe9a553d4ba41c678e9acc231"
DATABASE_IMAGE = "mariadb:10.11.7"
DATABASE = "admission_initializer_ci"
OWNER_LABEL = "org.sihsalus.admission-initializer"
CANONICAL_ROLE = "Admision"
LEGACY_ROLE = "SIHSALUS Admision"
CANONICAL_UUID = "71dcb611-756a-4ad3-a9bb-73b6cfe28066"
CHANGESET = "reconcile-admission-role-20260907"
INITIALIZER_VERSION = "2.13.0-sihsalus.1"
CONFIG_PREFIX = "configuration/backend_configuration"
ROLES_FILE = "roles/roles-core.csv"
CURRENT_ADMISSION_ADDITIONS = frozenset({"app:home.libroAtenciones"})
LIQUIBASE_FILE = "liquibase/liquibase.xml"
ROLES_CHECKSUM = "configuration_checksums/roles/roles-core.checksum"
LIQUIBASE_CHECKSUM = "configuration_checksums/liquibase/liquibase.checksum"
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
ASSEMBLY_EXCLUDES = {
    "**/.DS_Store", "**/.gitkeep", "backend_configuration/ampathforms/Readme",
    "backend_configuration/ampathforms/_deprecated/**",
}
STRICT_JAVA = (
    "-Dfile.encoding=UTF-8 -server -Djava.security.egd=file:/dev/./urandom "
    "-Djava.awt.headless=true -Djava.awt.headlesslib=true "
    "-Dinitializer.startup.load=fail_on_error "
    "-Dinitializer.skip.checksums=false -Dinitializer.row.checksums.enabled=false "
    "-Dinitializer.logging.level=INFO "
    "-Dlog.level=org.openmrs.module.initializer:INFO,org.openmrs.module.ModuleClassLoader:DEBUG"
)


class HarnessFailure(Exception):
    """Only static, non-sensitive reason codes may be reported."""


def require(condition, code):
    if not condition:
        raise HarnessFailure(code)


def validate_runner(env):
    require(
        env.get("GITHUB_ACTIONS") == "true" and env.get("CI") == "true"
        and env.get("RUNNER_ENVIRONMENT") == "github-hosted"
        and env.get("RUNNER_OS") == "Linux"
        and env.get("GITHUB_REPOSITORY") == "sihsalus/sihsalus-content"
        and env.get("ADMISSION_INITIALIZER_DISPOSABLE") == "github-runner-only",
        "github_hosted_disposable_runner_required",
    )
    require(not env.get("DOCKER_HOST"), "external_docker_host_forbidden")
    require(not env.get("DOCKER_CONTEXT"), "external_docker_context_forbidden")
    require(re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", "")), "invalid_candidate_sha")
    directory = Path(env.get("RUNNER_TEMP", ""))
    require(directory.is_absolute() and directory.is_dir(), "runner_temp_required")
    require(directory.resolve() == directory and directory != Path("/"), "unsafe_runner_temp")
    return directory


def checked(args, *, data=None, timeout=60, cwd=None, env=None, allow_failure=False, operation="git"):
    require(re.fullmatch(r"(?:git|docker_(?:pull|image|container|volume|network|create|rm|cp|start|exec|logs|stop))", operation), "unsafe_diagnostic_operation")
    try:
        result = subprocess.run(
            args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, cwd=cwd, env=env, check=False,
        )
    except subprocess.TimeoutExpired:
        raise HarnessFailure(operation + "_timeout") from None
    except OSError:
        raise HarnessFailure(operation + "_unavailable") from None
    if result.returncode and not allow_failure:
        # Never print argv, raw stderr, HTTP bodies, SQL dumps, or environment.
        raise HarnessFailure(operation + "_exit_" + str(result.returncode))
    return result


def properties(data):
    result = {}
    for line in data.decode("utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "!")) and "=" in line:
            key, value = line.split("=", 1)
            require(key.strip() not in result, "duplicate_runtime_property")
            result[key.strip()] = value.strip()
    return result


def packaged_path(relative):
    path = PurePosixPath(relative)
    return (
        path.name not in (".gitkeep", ".DS_Store")
        and relative != "ampathforms/Readme"
        and not relative.startswith("ampathforms/_deprecated/")
    )


def validate_assembly(data):
    root = ET.fromstring(data)
    ns = {"a": "http://maven.apache.org/plugins/maven-assembly-plugin/assembly/1.1.3"}
    require(
        {node.text for node in root.findall(".//a:exclude", ns)} == ASSEMBLY_EXCLUDES,
        "unreviewed_assembly_excludes",
    )
    includes = [node.text for node in root.findall(".//a:include", ns)]
    require(includes == ["content.properties", "backend_configuration/**/*"], "unreviewed_assembly_includes")


def extract_archive(data, destination, prefix, package=False):
    """Only regular files below a required prefix; no tar links or traversal."""
    destination.mkdir(parents=True, exist_ok=False)
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        for item in archive:
            raw = item.name.rstrip("/")
            path = PurePosixPath(raw)
            require(
                not path.is_absolute() and ".." not in path.parts
                and raw == str(path) and "\\" not in raw,
                "unsafe_archive_path",
            )
            if item.isdir():
                # git archive also emits the ancestors of the selected subtree.
                require(
                    raw == prefix or raw.startswith(prefix + "/")
                    or prefix.startswith(raw + "/"), "archive_outside_prefix",
                )
                continue
            require(item.isfile(), "archive_links_or_special_files_forbidden")
            require(raw.startswith(prefix + "/"), "archive_outside_prefix")
            relative = raw[len(prefix) + 1:]
            require(relative and relative not in seen, "duplicate_archive_path")
            seen.add(relative)
            if package and not packaged_path(relative):
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = archive.extractfile(item)
            require(stream is not None, "archive_file_unreadable")
            with target.open("xb") as output:
                shutil.copyfileobj(stream, output)
            target.chmod(0o644)
    require(seen, "empty_configuration_archive")
    for directory in [destination, *destination.rglob("*")]:
        if directory.is_dir():
            directory.chmod(0o755)


def single_file_archive(data, basename):
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        members = archive.getmembers()
        require(
            len(members) == 1 and members[0].isfile()
            and members[0].name == basename,
            "unexpected_single_file_archive",
        )
        return archive.extractfile(members[0]).read()


def manifest(directory):
    result = {}
    for path in sorted(directory.rglob("*")):
        require(not path.is_symlink(), "configuration_symlink_forbidden")
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    require(result, "empty_configuration")
    return result


def assemble(image, image_content, replacement, destination):
    """Remove only byte-verified owned old files; preserve all other image files."""
    image_files, old_files, new_files = map(manifest, (image, image_content, replacement))
    require(
        all(image_files.get(path) == digest for path, digest in old_files.items()),
        "image_content_manifest_does_not_match_pinned_source",
    )
    preserved = {path: digest for path, digest in image_files.items() if path not in old_files}
    require(
        all(path not in preserved or preserved[path] == digest for path, digest in new_files.items()),
        "replacement_collides_with_unowned_image_content",
    )
    shutil.copytree(image, destination)
    for path in old_files:
        (destination / path).unlink()
    for path in new_files:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(replacement / path, target)
        target.chmod(0o644)
    actual = manifest(destination)
    require(actual == {**preserved, **new_files}, "assembled_configuration_manifest_mismatch")
    return {"preserved_files": len(preserved), "candidate_files": len(new_files)}


def validate_startup(data):
    text = data.decode("utf-8")
    for code, needle in {
        "distribution_path": 'OMRS_DISTRO_CONFIG="$OMRS_DISTRO_DIR/openmrs_config"',
        "configuration_path": 'OMRS_CONFIG_DIR="$OMRS_DATA_DIR/configuration"',
        "configuration_copy": 'cp -R "$OMRS_DISTRO_CONFIG/." "$OMRS_CONFIG_DIR"',
        "configuration_cleanup": 'rm -fR "' + "$" + '{OMRS_CONFIG_DIR:?}"/*',
        "extra_properties": "OMRS_EXTRA_",
        "runtime_properties": "OMRS_RUNTIME_PROPERTIES_FILE",
        "ocl_hook": "/usr/local/bin/configure-ocl-token.sh",
    }.items():
        require(needle in text, "unverified_startup_" + code)
    return hashlib.sha256(data).hexdigest()


def sql_string(value):
    return "CONVERT(0x" + value.encode("utf-8").hex() + " USING utf8mb4)"


def backend_owner(runtime_user, identity):
    require(re.fullmatch(r"[1-9][0-9]*(?::[0-9]+)?", runtime_user), "numeric_nonroot_backend_user_required")
    # Docker supports numeric users absent from /etc/passwd. Verify the actual
    # effective identity in an isolated id-only probe, never assume its GID.
    parts = identity.decode("ascii").splitlines()
    require(len(parts) == 2 and all(re.fullmatch(r"[0-9]+", part) for part in parts), "backend_effective_identity_unverified")
    declared = runtime_user.split(":")
    require(parts[0] == declared[0] and (len(declared) == 1 or parts[1] == declared[1]), "backend_effective_identity_mismatch")
    return parts[0] + ":" + parts[1]


def admission_privileges(configuration, additions=frozenset()):
    with (configuration / ROLES_FILE).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row["Uuid"] == CANONICAL_UUID or row["Role name"] == CANONICAL_ROLE]
    require(len(selected) == 1, "canonical_csv_identity_missing")
    row = selected[0]
    require(
        row["Uuid"] == CANONICAL_UUID and row["Role name"] == CANONICAL_ROLE
        and not row["Inherited roles"], "canonical_csv_identity_changed",
    )
    privileges = set(row["Privileges"].split(";"))
    require(
        len(privileges) == 58 + len(additions) and additions <= privileges
        and "Delete Relationships" in privileges
        and "Purge Relationships" not in privileges, "unexpected_admission_policy",
    )
    return privileges
