#!/usr/bin/env python3
"""Real Initializer and narrow RBAC test on exclusively owned GitHub CI containers."""

import base64
import csv
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import sys
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path, PurePosixPath

from guards import (
    BACKEND, DISTRO_SHA, IMAGE_CONTENT_SHA, BASELINE_SHA, DATABASE_IMAGE, DATABASE,
    OWNER_LABEL, CANONICAL_ROLE, LEGACY_ROLE, CANONICAL_UUID, EMRAPI_ROLES, CHANGESET,
    INITIALIZER_VERSION, CONFIG_PREFIX, ROLES_FILE, CURRENT_ADMISSION_ADDITIONS, LIQUIBASE_FILE,
    ROLES_CHECKSUM, LIQUIBASE_CHECKSUM, UUID_PATTERN, STRICT_JAVA, HarnessFailure,
    require, checked, validate_runner, properties, extract_archive,
    single_file_archive, assemble, validate_startup, validate_assembly,
    sql_string, backend_owner, admission_privileges,
)

ROOT = Path(__file__).resolve().parents[3]
COMPLETION = "OpenMRS config loading process completed."
ABORT = "The loading of the 'liquibase' configuration file was aborted:"
FILE_ABORT = re.compile(r"The (?:pre-)?loading of the '[^'\r\n]+' configuration file was aborted:")
INITIALIZER_STOPPED = re.compile(r"Disposing of ModuleClassLoader: \{ModuleClassLoader: uid=-?\d+; initializer\}")
STATE_TABLES = {
    "role": "role", "role_privilege": "role,privilege",
    "role_role": "parent_role,child_role", "user_role": "user_id,role",
    "patientflags_tag_role": "tag_id,role", "stockmgmt_user_role_scope": "user_role_scope_id",
}
CLINICAL_DRUG = {
    "uuid": "07c2b995-5619-4d82-8b55-e4cdf96f94d1",
    "name": "ÁCIDO URSODESOXICÓLICO 250 mg - Tableta",
    "concept": "00d9cb0c-4aef-4614-ab38-a9978e3d62e1",
    "name_es": "ÁCIDO URSODESOXICÓLICO",
    "name_en": "Ursodeoxycholic acid",
    "dosage_form": "bd1e9059-62b4-4967-a804-a63eda4f8657",
    "strength": "250 mg",
}

LOADER_DOMAINS = frozenset("""
liquibase jsonkeyvalues conceptclasses conceptsources metadatasharing visittypes
patientidentifiertypes relationshiptypes locationtags privileges encountertypes
encounterroles proceduretypes roles globalproperties attributetypes providerroles
systemtasks locations locationtagmaps addresshierarchy bahmniforms ocl concepts
conceptsets conceptreferencerange billableservices paymentmodes cashpoints
cashieritemprices flagpriorities flagtags flags programs programworkflows
programworkflowstates personattributetypes idgen autogenerationoptions drugs
orderfrequencies ordertypes appointmentspecialities appointmentservicedefinitions
appointmentservicetypes queues datafiltermappings metadatasets metadatasetmembers
metadatatermmappings cohorttypes cohortattributetypes fhirconceptsources
fhirpatientidentifiersystems ampathforms ampathformstranslations htmlforms dispositions
""".split())


def loader_progress(logs):
    """Report only pinned Initializer domain names and fixed failure categories."""
    loading = re.findall(r"Loading file [^\r\n]*?/configuration/([a-z]+)/", logs)
    completed = re.findall(r"The '([a-z]+)' configuration file has finished loading:", logs)
    categories = {
        "out_of_memory": "java.lang.OutOfMemoryError",
        "connection_timeout": "java.net.SocketTimeoutException",
        "connection_refused": "java.net.ConnectException",
        "dns_failure": "java.net.UnknownHostException",
        "database_deadlock": "Deadlock found when trying to get lock",
        "database_lock_timeout": "Lock wait timeout exceeded",
    }
    return {
        "initializer_last_loading_domain": loading[-1] if loading and loading[-1] in LOADER_DOMAINS else None,
        "initializer_last_completed_domain": completed[-1] if completed and completed[-1] in LOADER_DOMAINS else None,
        "initializer_failure_hints": [name for name, marker in categories.items() if marker in logs],
    }


def emit(stage, status, **safe):
    print(json.dumps({"stage": stage, "status": status, **safe}), flush=True)


class Harness:
    def __init__(self, env):
        runner_temp = validate_runner(env)
        self.directory = Path(tempfile.mkdtemp(prefix="admission-initializer-", dir=runner_temp))
        self.directory.chmod(0o700)
        self.env = {"PATH": env.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"}
        self.nonce = uuid.uuid4().hex
        self.prefix = "admission-initializer-" + self.nonce[:16]
        self.docker_config = self.directory / "docker-config"
        self.docker_config.mkdir(mode=0o700)
        self.containers, self.volumes = [], []
        self.network = None
        self.deadline = time.monotonic() + 80 * 60
        self.cleanup_deadline = None
        self.candidate_sha = env["GITHUB_SHA"]
        self.password = secrets.token_urlsafe(36) + "Aa1!"
        self.admin_password = secrets.token_urlsafe(36) + "Aa1!"
        self.user_password = secrets.token_urlsafe(36) + "Aa1!"
        self.fixtures = []
        self.lifecycle_files = {}
        self.baseline_data = self.directory / "baseline-data"
        self.baseline_dump = self.directory / "baseline.sql"
        self.mysql_config = self.private("mysql.cnf", "[client]\nuser=root\npassword=" + self.password + "\n")
        self.db_env = self.private("db.env",
            f"MARIADB_DATABASE={DATABASE}\nMARIADB_USER=openmrs\n"
            f"MARIADB_PASSWORD={self.password}\nMARIADB_ROOT_PASSWORD={self.password}\n")
        self.backend_env = self.private("backend.env",
            f"OMRS_DB_HOSTNAME=db\nOMRS_DB_NAME={DATABASE}\nOMRS_DB_USERNAME=openmrs\n"
            f"OMRS_DB_PASSWORD={self.password}\nOMRS_ADMIN_USER_PASSWORD={self.admin_password}\n"
            "OMRS_AUTO_UPDATE_DATABASE=true\nOMRS_CREATE_TABLES=true\n"
            "OMRS_OCL_TOKEN=\nOMRS_MODULE_WEB_ADMIN=false\n"
            "OMRS_EXTRA_INITIALIZER_STARTUP_LOAD=fail_on_error\n"
            "OMRS_EXTRA_INITIALIZER_SKIP_CHECKSUMS=false\n"
            "OMRS_EXTRA_INITIALIZER_ROW_CHECKSUMS_ENABLED=false\n"
            "OMRS_EXTRA_INITIALIZER_LOGGING_LEVEL=INFO\n"
            "OMRS_EXTRA_INITIALIZER_LOGGING_ENABLED=true\n"
            f"OMRS_JAVA_SERVER_OPTS={STRICT_JAVA}\n"
            "OMRS_JAVA_MEMORY_OPTS=-Xms512m -Xmx3g\n")

    def private(self, name, text):
        path = self.directory / name
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text)
        path.chmod(0o600)
        return path

    def remaining(self, maximum=35 * 60):
        remaining = int(self.deadline - time.monotonic())
        require(remaining > 0, "global_time_budget_exhausted")
        return min(maximum, remaining)

    def docker(self, *args, data=None, timeout=60, allow_failure=False):
        if self.cleanup_deadline is not None:
            remaining = int(self.cleanup_deadline - time.monotonic())
            require(remaining > 0, "cleanup_time_budget_exhausted")
            timeout = min(timeout, 45, remaining)
        return checked(
            ["docker", "--config", str(self.docker_config), "--host",
             "unix:///var/run/docker.sock", *args],
            data=data, timeout=timeout, env=self.env, allow_failure=allow_failure,
            operation="docker_" + args[0])

    def inspect(self, kind, name):
        try:
            result = json.loads(self.docker(kind, "inspect", name).stdout)
        except ValueError:
            raise HarnessFailure("invalid_docker_inspection") from None
        require(isinstance(result, list) and len(result) == 1, "invalid_docker_inspection")
        return result[0]

    def owned(self, kind, name):
        require(name.startswith(self.prefix + "-"), "resource_name_not_owned")
        details = self.inspect(kind, name)
        labels = details.get("Labels") if kind in ("volume", "network") else details.get("Config", {}).get("Labels")
        require(labels and labels.get(OWNER_LABEL) == self.nonce, "resource_ownership_mismatch")
        return details

    def volume(self, suffix):
        name = self.prefix + "-" + suffix
        # Journal the intent first: a client timeout does not prove Docker did
        # not create it. Cleanup must inspect its label or report uncertainty.
        self.volumes.append(name)
        self.docker("volume", "create", "--label", OWNER_LABEL + "=" + self.nonce, name)
        self.owned("volume", name)
        return name

    def container(self, suffix, options, image, command=()):
        name = self.prefix + "-" + suffix
        self.containers.append(name)
        self.docker("create", "--name", name, "--label", OWNER_LABEL + "=" + self.nonce, *options, image, *command)
        self.owned("container", name)
        return name

    def remove_container(self, name):
        self.owned("container", name)
        self.docker("rm", "--force", "--volumes", name, timeout=45)
        self.containers.remove(name)

    def copy_tree(self, container, source, destination, prefix):
        self.owned("container", container)
        archive = self.docker("cp", container + ":" + source, "-", timeout=180).stdout
        extract_archive(archive, destination, prefix)

    def copy_file(self, container, source):
        self.owned("container", container)
        archive = self.docker("cp", container + ":" + source, "-").stdout
        return single_file_archive(archive, PurePosixPath(source).name)

    def git_configuration(self, sha, version, destination):
        checked(["git", "cat-file", "-e", sha + "^{commit}"], cwd=ROOT)
        pom = checked(["git", "show", sha + ":pom.xml"], cwd=ROOT).stdout
        node = ET.fromstring(pom).find("{http://maven.apache.org/POM/4.0.0}version")
        require(node is not None and isinstance(node.text, str), "missing_content_version")
        if version is None:
            require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", node.text), "candidate_release_version_required")
            require(tuple(map(int, node.text.split("."))) > (1, 25, 15), "candidate_reuses_baseline_version")
            self.candidate_version = node.text
        else:
            require(node.text == version, "unexpected_content_version")
        validate_assembly(checked(["git", "show", sha + ":assembly.xml"], cwd=ROOT).stdout)
        archive = checked(["git", "archive", sha, CONFIG_PREFIX], cwd=ROOT, timeout=180).stdout
        extract_archive(archive, destination, CONFIG_PREFIX, package=True)

    def prepare(self):
        emit("prepare", "RUNNING")
        require(sys.platform.startswith("linux"), "linux_required")
        require(Path("/var/run/docker.sock").is_socket(), "local_runner_docker_socket_required")
        require(checked(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.decode().strip() == self.candidate_sha, "checkout_sha_mismatch")
        require(not checked(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT).stdout, "clean_tracked_checkout_required")
        self.docker("pull", "--platform", "linux/amd64", BACKEND, timeout=self.remaining(600))
        self.docker("pull", "--platform", "linux/amd64", DATABASE_IMAGE, timeout=self.remaining(300))
        image = self.inspect("image", BACKEND)
        require(image.get("Os") == "linux" and image.get("Architecture") == "amd64", "unexpected_backend_platform")
        require(image.get("Config", {}).get("Labels", {}).get("org.opencontainers.image.revision") == DISTRO_SHA, "backend_revision_label_mismatch")
        require(BACKEND in image.get("RepoDigests", []), "backend_digest_mismatch")
        command = " ".join((image["Config"].get("Entrypoint") or []) + (image["Config"].get("Cmd") or []))
        require("startup.sh" in command, "unverified_image_launch_command")
        runtime_user = image["Config"].get("User", "")
        require(re.fullmatch(r"[1-9][0-9]*(?::[0-9]+)?", runtime_user), "numeric_nonroot_backend_user_required")
        probe = self.container("probe",
            ["--network", "none", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges", "--entrypoint", "/bin/sh"],
            BACKEND, ["-ceu", "id -u; id -g"])
        identity = self.docker("start", "--attach", probe, timeout=30).stdout
        self.backend_owner = backend_owner(runtime_user, identity)
        self.image_config = self.directory / "image-configuration"
        self.copy_tree(probe, "/openmrs/distribution/openmrs_config", self.image_config, "openmrs_config")
        startup_hash = validate_startup(self.copy_file(probe, "/openmrs/startup-init.sh"))
        startup = self.copy_file(probe, "/openmrs/startup.sh").decode()
        require("source /openmrs/startup-init.sh" in startup and "/usr/local/tomcat/bin/catalina.sh run" in startup, "unverified_image_entrypoint")
        distro = properties(self.copy_file(probe, "/openmrs/distribution/openmrs-distro.properties"))
        require(distro.get("content.sihsalus-content") == "1.25.12", "image_content_version_mismatch")
        self.remove_container(probe)
        original, baseline, candidate = [self.directory / name for name in ("source-12", "source-15", "source-candidate")]
        for sha, version, path in ((IMAGE_CONTENT_SHA, "1.25.12", original), (BASELINE_SHA, "1.25.15", baseline), (self.candidate_sha, None, candidate)):
            self.git_configuration(sha, version, path)
        self.privileges = admission_privileges(baseline)
        self.candidate_privileges = admission_privileges(candidate, CURRENT_ADMISSION_ADDITIONS)
        require(self.candidate_privileges == self.privileges | CURRENT_ADMISSION_ADDITIONS, "unreviewed_current_admission_policy")
        self.baseline_config, self.candidate_config = self.directory / "config-baseline", self.directory / "config-candidate"
        assemble(self.image_config, original, baseline, self.baseline_config)
        receipt = assemble(self.image_config, original, candidate, self.candidate_config)
        # Exercise the historical checksum regression independently of later
        # approved role changes, then load the exact candidate CSV separately.
        self.historical_config = self.directory / "config-historical-roles"
        shutil.copytree(self.candidate_config, self.historical_config)
        shutil.copyfile(baseline / ROLES_FILE, self.historical_config / ROLES_FILE)
        self.role_md5 = hashlib.md5((baseline / ROLES_FILE).read_bytes()).hexdigest()
        self.candidate_role_md5 = hashlib.md5((candidate / ROLES_FILE).read_bytes()).hexdigest()
        self.network = self.prefix + "-network"
        self.docker("network", "create", "--internal", "--label", OWNER_LABEL + "=" + self.nonce, self.network)
        require(self.owned("network", self.network).get("Internal") is True, "network_not_internal")
        emit("prepare", "PASSED", source_sha=self.candidate_sha, baseline_sha=BASELINE_SHA,
             candidate_version=self.candidate_version,
             backend_digest=BACKEND.split("@")[1], startup_sha256=startup_hash, **receipt)

    def start_database(self, suffix):
        volume = self.volume(suffix + "-db")
        name = self.container(suffix + "-db",
            ["--network", self.network, "--network-alias", "db", "--memory", "1g", "--cpus", "1",
             "--env-file", str(self.db_env),
             "--mount", "type=volume,src=" + volume + ",dst=/var/lib/mysql",
             "--mount", "type=bind,src=" + str(self.mysql_config) + ",dst=/run/admission-mysql.cnf,readonly"],
            DATABASE_IMAGE, ["mariadbd", "--character-set-server=utf8mb4", "--collation-server=utf8mb4_bin"])
        self.docker("start", name)
        deadline = time.monotonic() + self.remaining(180)
        while time.monotonic() < deadline:
            result = self.docker("exec", name, "mariadb", "--defaults-extra-file=/run/admission-mysql.cnf",
                "--batch", "--skip-column-names", "-e", "SELECT VERSION()", allow_failure=True)
            if result.returncode == 0:
                require(result.stdout.decode().strip().startswith("10.11.7-"), "database_version_mismatch")
                require(self.query(name, "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=" + sql_string(DATABASE)) == ["0"], "database_not_empty")
                return name
            time.sleep(5)
        raise HarnessFailure("database_startup_timeout")

    def query(self, db, sql):
        self.owned("container", db)
        result = self.docker("exec", "-i", db, "mariadb", "--defaults-extra-file=/run/admission-mysql.cnf",
            "--default-character-set=utf8mb4", "--batch", "--skip-column-names", DATABASE,
            data=sql.encode(), timeout=120)
        return result.stdout.decode().splitlines()

    def import_baseline(self, db):
        self.owned("container", db)
        self.docker("exec", "-i", db, "mariadb", "--defaults-extra-file=/run/admission-mysql.cnf",
            DATABASE, data=self.baseline_dump.read_bytes(), timeout=self.remaining(300))

    def start_backend(self, suffix, configuration, data_volume=None, restore=False):
        require(re.fullmatch(r"[a-z][a-z-]*", suffix), "invalid_backend_phase")
        lifecycle_file = "admission-initializer-" + self.nonce + "-" + suffix + ".log"
        require(lifecycle_file not in self.lifecycle_files.values(), "reused_initializer_log")
        volume = data_volume or self.volume(suffix + "-data")
        self.owned("volume", volume)
        if restore:
            require(re.fullmatch(r"[1-9][0-9]*:[0-9]+", self.backend_owner), "backend_restore_owner_unverified")
            helper = self.container(suffix + "-restore",
                ["--network", "none", "--user", "0",
                 "--mount", "type=bind,src=" + str(self.baseline_data) + ",dst=/seed,readonly",
                 "--mount", "type=volume,src=" + volume + ",dst=/openmrs/data", "--entrypoint", "/bin/bash"],
                BACKEND, ["-ceu", "test -d /seed/configuration_checksums; cp -a /seed/. /openmrs/data/; chown -R " + self.backend_owner + " /openmrs/data"])
            self.docker("start", "--attach", helper, timeout=self.remaining(180))
            self.remove_container(helper)
        name = self.container(suffix,
            ["--network", self.network, "--memory", "4g", "--cpus", "2", "--env-file", str(self.backend_env),
             "--env", "OMRS_EXTRA_INITIALIZER_LOGGING_LOCATION=" + lifecycle_file,
             "--mount", "type=bind,src=" + str(configuration) + ",dst=/openmrs/distribution/openmrs_config,readonly",
             "--mount", "type=volume,src=" + volume + ",dst=/openmrs/data"], BACKEND)
        self.lifecycle_files[name] = lifecycle_file
        self.docker("start", name)
        return name, volume

    def request(self, backend, method, resource, body=None, restricted=False):
        self.owned("container", backend)
        require(method in ("GET", "POST", "DELETE"), "unsupported_internal_method")
        require(resource.startswith("/") and not any(char in resource for char in ('\n', '\r', '"', '\\')), "unsafe_internal_resource")
        user = self.fixtures[0]["username"] if restricted else "admin"
        password = self.user_password if restricted else self.admin_password
        auth = base64.b64encode((user + ":" + password).encode()).decode()
        config = (
            "silent\nshow-error\nnoproxy = \"*\"\nconnect-timeout = 5\nmax-time = 20\n"
            "max-redirs = 0\nretry = 0\n"
            f"url = \"http://127.0.0.1:8080/openmrs/ws/rest/v1{resource}\"\nrequest = \"{method}\"\n"
            f"header = \"Authorization: Basic {auth}\"\nheader = \"Content-Type: application/json\"\n"
            "write-out = \"\\n%{http_code}\"\n")
        if body is not None:
            config += "data = " + json.dumps(json.dumps(body, separators=(",", ":"))) + "\n"
        result = self.docker("exec", "-i", backend, "curl", "--config", "-", data=config.encode(), timeout=30, allow_failure=True)
        if result.returncode:
            return None, None
        content, separator, code = result.stdout.rpartition(b"\n")
        require(separator and re.fullmatch(rb"\d{3}", code), "invalid_internal_http_response")
        try:
            parsed = json.loads(content) if content else None
        except ValueError:
            parsed = None
        return int(code), parsed

    def module_status(self, backend):
        code, body = self.request(backend, "GET", "/module/initializer?v=full")
        # The installation filter can still redirect after Initializer finishes.
        # Do not follow it or accept it as readiness; the startup deadline applies.
        require(code not in (None, 302, 502, 503, 504), "module_state_unavailable")
        require(code == 200, "module_state_http_" + str(code))
        require(isinstance(body, dict), "module_state_malformed")
        require(body.get("uuid") == "initializer", "initializer_module_missing")
        require(body.get("version") == INITIALIZER_VERSION, "initializer_version_mismatch")
        require(isinstance(body.get("started"), bool), "initializer_started_state_missing")
        return body["started"]

    def bootstrap(self, backend):
        """Trigger the synthetic installation filter; HTTP is not a success oracle."""
        self.owned("container", backend)
        config = (
            "silent\nshow-error\nproxy = \"\"\nnoproxy = \"*\"\n"
            "connect-timeout = 2\nmax-time = 5\nmax-redirs = 0\nretry = 0\n"
            "url = \"http://127.0.0.1:8080/openmrs/initialsetup\"\nrequest = \"GET\"\n"
            "output = \"/dev/null\"\nwrite-out = \"%{http_code}\"\n")
        # --disable is curl's first option: no inherited curlrc, credentials,
        # cookies, redirects or retry settings. The response body is discarded.
        result = self.docker("exec", "-i", backend, "curl", "--disable", "--config", "-",
            data=config.encode(), timeout=10, allow_failure=True)
        if result.returncode:
            return None
        require(re.fullmatch(rb"[1-5][0-9]{2}", result.stdout), "invalid_bootstrap_http_code")
        return int(result.stdout)

    def installation_progress(self, backend):
        """Read typed flags and counters; never return installer messages or logs."""
        self.owned("container", backend)
        config = (
            "silent\nshow-error\nproxy = \"\"\nnoproxy = \"*\"\n"
            "connect-timeout = 2\nmax-time = 5\nmax-redirs = 0\nretry = 0\n"
            "url = \"http://127.0.0.1:8080/openmrs/initialsetup?page=progress.vm.ajaxRequest\"\n"
            "request = \"GET\"\nwrite-out = \"\\n%{http_code}\"\n")
        result = self.docker("exec", "-i", backend, "curl", "--disable", "--config", "-",
            data=config.encode(), timeout=10, allow_failure=True)
        if result.returncode:
            return None, None, None, None
        content, separator, code = result.stdout.rpartition(b"\n")
        if not separator or code != b"200":
            return None, None, None, None
        try:
            body = json.loads(content)
        except ValueError:
            return None, None, None, None
        if not isinstance(body, dict):
            return None, None, None, None
        has_errors, complete = body.get("hasErrors"), body.get("initializationComplete")
        counters = [body.get(key) for key in ("actionCounter", "completedPercentage")]
        # Core's per-task percentage can reset or exceed 100; it is not readiness.
        counters = [value if type(value) is int and value >= 0 else None for value in counters]
        return (has_errors if isinstance(has_errors, bool) else None,
                complete if isinstance(complete, bool) else None, *counters)

    def effective_strict(self, backend):
        values = properties(self.copy_file(backend, "/openmrs/data/openmrs-runtime.properties"))
        require(values.get("initializer.startup.load") == "fail_on_error", "strict_runtime_property_missing")
        require(values.get("initializer.skip.checksums") == "false", "checksum_tracking_not_enabled")
        require(values.get("initializer.row.checksums.enabled") == "false", "row_checksum_mode_changed")
        require(values.get("initializer.logging.enabled") == "true"
                and values.get("initializer.logging.level") == "INFO"
                and values.get("initializer.logging.location") == self.lifecycle_files[backend],
                "current_attempt_initializer_logging_not_configured")
        require(not values.get("initializer.domains"), "initializer_domain_filter_forbidden")
        require(not any(key.startswith("initializer.exclude") and value for key, value in values.items()), "initializer_exclusions_forbidden")
        actual = self.owned("container", backend)
        env = dict(item.split("=", 1) for item in actual["Config"]["Env"] if "=" in item)
        require(env.get("OMRS_JAVA_SERVER_OPTS") == STRICT_JAVA, "strict_system_flags_changed")

    def lifecycle_logs(self, backend):
        """Read this attempt's dedicated file and container output, never a restored log."""
        self.owned("container", backend)
        filename = self.lifecycle_files[backend]
        require(re.fullmatch(r"admission-initializer-[0-9a-f]{32}-[a-z-]+\.log", filename), "invalid_initializer_log_path")
        output = self.docker("logs", "--tail", "5000", backend)
        log = self.docker("exec", backend, "/bin/sh", "-c",
            'if [ ! -e "$1" ]; then exit 44; fi; test -f "$1" && test ! -L "$1" && cat "$1"',
            "--", "/openmrs/data/" + filename, allow_failure=True)
        require(log.returncode in (0, 44), "initializer_log_unreadable")
        present = log.returncode == 0
        logs = (output.stdout + output.stderr + (log.stdout if present else b"")).decode("utf-8", "replace")
        return logs, present, len(log.stdout) if present else None

    def wait_initializer(self, backend, stage, reject=False):
        started_at = time.monotonic()
        deadline = started_at + self.remaining()
        next_diagnostic = started_at
        observed = None
        while time.monotonic() < deadline:
            require(self.owned("container", backend)["State"].get("Running") is True, "backend_exited_before_validation")
            # The image's one-shot startup request may precede web readiness.
            # Reach the fixed filter directly, without following root redirects.
            bootstrap_code = self.bootstrap(backend)
            logs, log_present, log_bytes = self.lifecycle_logs(backend)
            abort_messages = [match.group(0) for match in FILE_ABORT.finditer(logs)]
            csv_error = "BEGINNING OF CSV FILE ERROR SUMMARY" in logs
            now = time.monotonic()
            if now >= next_diagnostic:
                has_errors, installation_complete, action_counter, percentage = self.installation_progress(backend)
                emit(stage, "WAITING", backend_running=True, bootstrap_http_code=bootstrap_code,
                     completion_seen=COMPLETION in logs, abort_seen=bool(abort_messages),
                     candidate_marker_seen=CHANGESET in logs,
                     csv_error_seen=csv_error, installation_has_errors=has_errors,
                     installation_complete=installation_complete,
                     installation_action_counter=action_counter,
                     installation_completed_percentage=percentage,
                     initializer_log_present=log_present, initializer_log_bytes=log_bytes,
                     **loader_progress(logs))
                next_diagnostic = now + 60
                require(has_errors is not True, "installation_reported_errors")
            # A separate failure cannot be masked by the expected Liquibase
            # rejection. Never emit the matched domain, filename or raw log.
            if any(message != ABORT for message in abort_messages) or csv_error:
                raise HarnessFailure("unexpected_initializer_abort")
            if reject and ABORT in logs and CHANGESET in logs:
                require(COMPLETION not in logs, "initializer_continued_after_rejection")
                observed = False
            elif abort_messages:
                raise HarnessFailure("unexpected_initializer_abort")
            if COMPLETION in logs:
                require(not reject, "expected_rejection_did_not_occur")
                observed = True
            if observed is not None:
                self.effective_strict(backend)
                # Core stops REST too after this startup exception. Its classloader
                # disposal follows removal from the actual started-modules map.
                if reject:
                    if INITIALIZER_STOPPED.search(logs):
                        emit(stage, "PASSED", initializer_started=False)
                        return
                    time.sleep(5)
                    continue
                try:
                    started = self.module_status(backend)
                except HarnessFailure as error:
                    if str(error) != "module_state_unavailable":
                        raise
                    # Lifecycle logs precede web availability. Keep polling;
                    # Unavailable HTTP is never interpreted as false; malformed
                    # successful responses and authentication failures are fatal.
                else:
                    if started == observed:
                        emit(stage, "PASSED", initializer_started=started)
                        return
            time.sleep(5)
        raise HarnessFailure("initializer_lifecycle_not_proven_before_timeout")

    def checksum(self, backend, relative):
        value = self.copy_file(backend, "/openmrs/data/" + relative).decode("ascii")
        require(re.fullmatch(r"[0-9a-f]{32}", value), "invalid_initializer_checksum")
        return value

    def absent_checksum(self, backend, relative):
        result = self.docker("exec", backend, "test", "-e", "/openmrs/data/" + relative, allow_failure=True)
        require(result.returncode == 1, "unexpected_checksum_file")

    def assert_checksums(self, backend, role_md5=None):
        require(self.checksum(backend, ROLES_CHECKSUM) == (role_md5 or self.role_md5), "roles_checksum_mismatch")
        # LiquibaseLoader2_5 explicitly skips checksum WRITES. Never invent one;
        # an inherited checksum could suppress loading, so that state is blocked.
        self.absent_checksum(backend, LIQUIBASE_CHECKSUM)

    def history(self, db):
        return self.query(db, "SELECT * FROM liquibasechangelog ORDER BY ID,AUTHOR,FILENAME")

    def candidate_recorded(self, db):
        records = self.query(db, "SELECT MD5SUM,EXECTYPE FROM liquibasechangelog WHERE ID=" + sql_string(CHANGESET))
        if not records:
            return False
        require(len(records) == 1 and re.fullmatch(r"\d+:[0-9a-f]{32}\tEXECUTED", records[0]), "candidate_history_invalid")
        return True

    def state(self, db):
        existing = set(self.query(db, "SHOW TABLES"))
        return {table: self.query(db, "SELECT * FROM " + table + " ORDER BY " + order)
                for table, order in STATE_TABLES.items() if table in existing}

    def assert_state(self, db, expected, reason):
        actual = self.normalized_state(self.state(db))
        expected = self.normalized_state(expected)
        for table in STATE_TABLES:
            if actual.get(table) != expected.get(table):
                before, after = Counter(expected.get(table, [])), Counter(actual.get(table, []))
                emit("rbac_snapshot", "FAILED", table=table,
                     expected_present=table in expected, actual_present=table in actual,
                     removed_rows=sum((before - after).values()), added_rows=sum((after - before).values()))
        require(actual == expected, reason)

    def expected_upgrade_state(self, db, before):
        """Explicit relational oracle; no execution or translation of candidate SQL."""
        expected = {}
        for table, rows in before.items():
            columns = [row.split("\t", 1)[0] for row in self.query(db, "SHOW COLUMNS FROM " + table)]
            transformed = []
            inserted_legacy_references = set()
            for row in rows:
                values = row.split("\t")
                require(len(values) == len(columns), "snapshot_column_shape_changed")
                data = dict(zip(columns, values))
                if table == "role" and data["role"] == LEGACY_ROLE:
                    continue
                if table == "role_privilege" and data["role"] in (CANONICAL_ROLE, LEGACY_ROLE):
                    continue
                legacy_reference = table in ("user_role", "patientflags_tag_role") and data["role"] == LEGACY_ROLE
                if "role" in data and data["role"] == LEGACY_ROLE:
                    data["role"] = CANONICAL_ROLE
                if table == "role" and data["role"] == CANONICAL_ROLE:
                    data["uuid"] = CANONICAL_UUID
                rewritten = "\t".join(data[column] for column in columns)
                if legacy_reference:
                    # Only the legacy references inserted by this migration are
                    # deduplicated. Existing canonical/unrelated multiplicities
                    # must remain unchanged, including Patient Flags rows.
                    if rewritten not in rows and rewritten not in inserted_legacy_references:
                        transformed.append(rewritten)
                        inserted_legacy_references.add(rewritten)
                else:
                    transformed.append(rewritten)
            if table == "role_privilege":
                for privilege in self.privileges:
                    data = {"role": CANONICAL_ROLE, "privilege": privilege}
                    transformed.append("\t".join(data[column] for column in columns))
            # Stock IDs and every audit column remain part of each whole row.
            expected[table] = sorted(transformed)
        return expected

    @staticmethod
    def normalized_state(state):
        return {table: sorted(rows) for table, rows in state.items()}

    def check_admission(self, db, privileges=None):
        require(self.query(db, "SELECT role,uuid FROM role WHERE role IN ('Admision','SIHSALUS Admision')") == [CANONICAL_ROLE + "\t" + CANONICAL_UUID], "final_admission_identity_mismatch")
        require(set(self.query(db, "SELECT privilege FROM role_privilege WHERE role='Admision'")) == (privileges or self.privileges), "final_admission_privileges_mismatch")
        require(self.query(db, "SELECT COUNT(*) FROM role_role WHERE parent_role IN ('Admision','SIHSALUS Admision') OR child_role IN ('Admision','SIHSALUS Admision')") == ["0"], "final_admission_inheritance_present")
        for fixture in self.fixtures:
            rows = self.query(db, "SELECT r.role FROM user_role r JOIN users u ON u.user_id=r.user_id WHERE u.uuid=" + sql_string(fixture["uuid"]))
            require(rows == [CANONICAL_ROLE], "synthetic_user_assignment_not_preserved")

    def check_emrapi_roles(self, db):
        expected = [role + "\t" + identifier for role, identifier in EMRAPI_ROLES.items()]
        require(self.query(db, "SELECT role,uuid FROM role WHERE role IN ("
                + ",".join(sql_string(role) for role in EMRAPI_ROLES) + ") ORDER BY role") == expected,
                "emrapi_role_identity_mismatch")

    def check_clinical_drug(self, backend, db, phase, previous=None):
        """Verify the catalog entry in storage and the prescribing search response."""
        drug = CLINICAL_DRUG
        names = ",".join(sql_string(drug[key]) for key in ("name_es", "name_en"))
        concepts = self.query(db,
            "SELECT c.concept_id,c.uuid,c.retired,cc.name,dt.name FROM concept c "
            "JOIN concept_class cc ON cc.concept_class_id=c.class_id "
            "JOIN concept_datatype dt ON dt.concept_datatype_id=c.datatype_id "
            "WHERE c.uuid=" + sql_string(drug["concept"]) + " OR EXISTS (SELECT 1 FROM concept_name n "
            "WHERE n.concept_id=c.concept_id AND n.voided=0 AND n.name IN (" + names + ")) "
            "ORDER BY c.concept_id")
        require(len(concepts) == 1, "clinical_drug_concept_missing_or_duplicated")
        concept = concepts[0].split("\t")
        require(len(concept) == 5 and re.fullmatch(r"[1-9][0-9]*", concept[0])
                and concept[1:] == [drug["concept"], "0", "Drug", "N/A"],
                "clinical_drug_concept_invalid")
        require(self.query(db, "SELECT locale,name FROM concept_name WHERE concept_id=" + concept[0]
                + " AND voided=0 AND concept_name_type='FULLY_SPECIFIED' ORDER BY locale,name")
                == ["en\t" + drug["name_en"], "es\t" + drug["name_es"]],
                "clinical_drug_concept_names_invalid")
        presentations = self.query(db,
            "SELECT d.drug_id,d.uuid,d.name,d.retired,d.strength,c.uuid,f.uuid,f.retired,"
            "EXISTS (SELECT 1 FROM concept_name n WHERE n.concept_id=f.concept_id "
            "AND n.voided=0 AND n.locale='es' AND n.name='Tableta') FROM drug d "
            "JOIN concept c ON c.concept_id=d.concept_id "
            "LEFT JOIN concept f ON f.concept_id=d.dosage_form WHERE d.uuid=" + sql_string(drug["uuid"])
            + " OR c.uuid=" + sql_string(drug["concept"]) + " OR d.name=" + sql_string(drug["name"])
            + " ORDER BY d.drug_id")
        require(len(presentations) == 1, "clinical_drug_presentation_missing_or_duplicated")
        presentation = presentations[0].split("\t")
        require(len(presentation) == 9 and re.fullmatch(r"[1-9][0-9]*", presentation[0])
                and presentation[1:] == [drug["uuid"], drug["name"], "0", drug["strength"],
                    drug["concept"], drug["dosage_form"], "0", "1"], "clinical_drug_presentation_invalid")
        code, body = self.request(backend, "GET",
            "/drug?q=URSODESOX&v=custom:(uuid,display,name,strength,dosageForm:(display,uuid),concept:(display,uuid))")
        require(code == 200 and isinstance(body, dict) and isinstance(body.get("results"), list)
                and all(isinstance(item, dict) for item in body["results"]), "clinical_drug_search_invalid")
        matches = [item for item in body["results"] if item.get("uuid") == drug["uuid"]]
        require(len(matches) == 1, "clinical_drug_search_missing_or_duplicated")
        match = matches[0]
        require(match.get("name") == drug["name"] and match.get("strength") == drug["strength"]
                and isinstance(match.get("display"), str) and bool(match["display"].strip())
                and all(isinstance(match.get(key), dict) and match[key].get("uuid") == drug[target]
                    and isinstance(match[key].get("display"), str) and bool(match[key]["display"].strip())
                    for key, target in (("concept", "concept"), ("dosageForm", "dosage_form"))),
                "clinical_drug_search_entry_invalid")
        snapshot = (tuple(concepts), tuple(presentations))
        require(previous is None or snapshot == previous, "clinical_drug_changed_on_restart")
        emit("clinical_drug", "PASSED", phase=phase, concepts=1, presentations=1,
             search_http=200, restart_checked=previous is not None)
        return snapshot

    def check_ocl_refresh(self, db, phase, previous=None):
        """Verify additive OCL concepts and the independently owned neighborhood set."""
        concepts = []
        for identifier, concept_class, name in (
                ("3fb84698-488a-447d-acbc-72e8665cffdc", "Misc", "1:512"),
                ("d14f251d-82a1-4ecf-aa45-f17f57a193db", "Finding", "Cuatro cruces")):
            rows = self.query(db, "SELECT c.concept_id,c.uuid,c.retired,cc.name,dt.name,n.name FROM concept c "
                "JOIN concept_class cc ON cc.concept_class_id=c.class_id "
                "JOIN concept_datatype dt ON dt.concept_datatype_id=c.datatype_id "
                "LEFT JOIN concept_name n ON n.concept_id=c.concept_id AND n.voided=0 "
                "AND n.locale='es' AND n.concept_name_type='FULLY_SPECIFIED' WHERE c.uuid=" + sql_string(identifier))
            require(len(rows) == 1, "ocl_refresh_concept_missing_or_duplicated")
            fields = rows[0].split("\t")
            require(len(fields) == 6 and re.fullmatch(r"[1-9][0-9]*", fields[0])
                    and fields[1:] == [identifier, "0", concept_class, "N/A", name], "ocl_refresh_concept_invalid")
            concepts.append(tuple(rows))
        neighborhood_uuid = "0fd3e744-6d2c-4cb3-9b7e-1f88899635d9"
        root = self.query(db, "SELECT concept_id,uuid,retired,is_set FROM concept WHERE uuid=" + sql_string(neighborhood_uuid))
        require(len(root) == 1, "ocl_refresh_neighborhood_set_missing_or_duplicated")
        fields = root[0].split("\t")
        require(len(fields) == 4 and re.fullmatch(r"[1-9][0-9]*", fields[0])
                and fields[1:] == [neighborhood_uuid, "0", "1"], "ocl_refresh_neighborhood_set_invalid")
        members = self.query(db, "SELECT s.concept_set_id,s.uuid,m.concept_id,m.uuid,m.retired "
            "FROM concept_set s JOIN concept m ON m.concept_id=s.concept_id "
            "WHERE s.concept_set=" + fields[0] + " ORDER BY m.uuid,s.concept_set_id")
        fields = [row.split("\t") for row in members]
        require(len(fields) == 10 and all(len(row) == 5 for row in fields)
                and len({row[3] for row in fields}) == 10
                and all(re.fullmatch(r"[1-9][0-9]*", row[0]) and UUID_PATTERN.fullmatch(row[1])
                    and re.fullmatch(r"[1-9][0-9]*", row[2]) and UUID_PATTERN.fullmatch(row[3])
                    and row[4] == "0" for row in fields), "ocl_refresh_neighborhood_members_invalid")
        snapshot = (tuple(concepts), tuple(root), tuple(members))
        require(previous is None or snapshot == previous, "ocl_refresh_changed_on_restart")
        emit("ocl_refresh", "PASSED", phase=phase, concepts=2, neighborhood_sets=1,
             neighborhood_members=10, restart_checked=previous is not None)
        return snapshot

    def create_fixtures(self, backend):
        for index in range(2):
            code, person = self.request(backend, "POST", "/person", {
                "names": [{"givenName": "Synthetic", "familyName": "Admission CI " + self.nonce[:8]}], "gender": "M"})
            require(code == 201 and isinstance(person, dict) and UUID_PATTERN.fullmatch(person.get("uuid", "")), "synthetic_person_creation_failed")
            username = "admission-ci-" + self.nonce[:12] + "-" + str(index)
            code, user = self.request(backend, "POST", "/user", {
                "username": username, "password": self.user_password, "person": person["uuid"],
                "roles": [CANONICAL_UUID], "userProperties": {}})
            require(code == 201 and isinstance(user, dict) and UUID_PATTERN.fullmatch(user.get("uuid", "")), "synthetic_user_creation_failed")
            self.fixtures.append({"uuid": user["uuid"], "username": username, "person": person["uuid"]})
        code, session = self.request(backend, "GET", "/session?v=full", restricted=True)
        require(code == 200 and isinstance(session, dict) and session.get("authenticated") is True, "synthetic_user_not_authenticated")
        require(str(session.get("user", {}).get("userProperties", {}).get("forcePassword", "false")).lower() != "true", "synthetic_user_requires_password_change")

    def baseline(self):
        emit("baseline", "RUNNING")
        db = self.start_database("baseline")
        backend, volume = self.start_backend("baseline", self.baseline_config)
        self.wait_initializer(backend, "baseline")
        self.assert_checksums(backend)
        require(not self.candidate_recorded(db), "candidate_present_in_baseline")
        history = self.history(db)
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        # The historical CSV overwrote EMRAPI's roles on installation. Restart
        # that same baseline before seeding the migration, retaining all checksums.
        backend, _ = self.start_backend("baseline-restart", self.baseline_config, data_volume=volume)
        self.wait_initializer(backend, "baseline_restart")
        self.assert_checksums(backend)
        require(self.history(db) == history, "baseline_restart_changed_history")
        self.check_emrapi_roles(db)
        self.create_fixtures(backend)
        self.check_admission(db)
        self.baseline_history = self.history(db)
        require(any("normalize-admission-role-name-20260722" in row for row in self.baseline_history), "real_baseline_history_missing")
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.copy_tree(backend, "/openmrs/data", self.baseline_data, "data")
        dump = self.docker("exec", db, "mariadb-dump", "--defaults-extra-file=/run/admission-mysql.cnf",
            "--single-transaction", "--routines", "--triggers", "--skip-dump-date", DATABASE,
            timeout=self.remaining(180)).stdout
        require(dump, "empty_baseline_dump")
        self.baseline_dump.write_bytes(dump)
        self.baseline_dump.chmod(0o600)
        self.remove_container(backend)
        self.remove_container(db)
        emit("baseline_snapshot", "PASSED", synthetic_users=len(self.fixtures),
             real_history_rows=len(self.baseline_history), roles_checksum=self.role_md5)

    def fresh(self):
        emit("fresh_candidate", "RUNNING")
        db = self.start_database("fresh")
        backend, _ = self.start_backend("fresh", self.candidate_config)
        self.wait_initializer(backend, "fresh_candidate")
        self.assert_checksums(backend, self.candidate_role_md5)
        require(self.candidate_recorded(db), "fresh_candidate_history_missing")
        self.check_emrapi_roles(db)
        self.check_clinical_drug(backend, db, "fresh")
        self.check_ocl_refresh(db, "fresh")
        self.create_fixtures(backend)
        self.check_admission(db, self.candidate_privileges)
        self.rbac(backend, db)
        emit("fresh_candidate", "PASSED", privileges=len(self.candidate_privileges),
             emrapi_role_identities_verified=True, roles_checksum=self.candidate_role_md5)

    def seed(self, db, bad=False):
        self.check_admission(db)
        if bad:
            require(self.query(db, "SELECT COUNT(*) FROM privilege WHERE privilege='Manage Roles'") == ["1"], "rejection_fixture_privilege_missing")
        self.query(db,
            "START TRANSACTION;\nUPDATE role SET uuid=" + sql_string(str(uuid.uuid4())) + " WHERE role='Admision';\n"
            "INSERT INTO role(role,description,uuid) VALUES ('SIHSALUS Admision','Synthetic admission fixture'," + sql_string(CANONICAL_UUID) + ");\n"
            "INSERT INTO role_privilege(role,privilege) SELECT 'SIHSALUS Admision',privilege FROM role_privilege WHERE role='Admision';\n"
            + ("INSERT INTO role_privilege(role,privilege) VALUES ('SIHSALUS Admision','Manage Roles');\n" if bad else
               "DELETE FROM role_privilege WHERE role IN ('Admision','SIHSALUS Admision') AND privilege='Delete Relationships';\n")
            + "INSERT INTO user_role(user_id,role) SELECT user_id,'SIHSALUS Admision' FROM users WHERE uuid IN ("
            + ",".join(sql_string(item["uuid"]) for item in self.fixtures) + ");\n"
            "DELETE FROM user_role WHERE role='Admision' AND user_id=(SELECT user_id FROM users WHERE uuid="
            + sql_string(self.fixtures[0]["uuid"]) + ");\nCOMMIT;")

    def rbac(self, backend, db):
        code, readable = self.request(backend, "GET", "/relationshiptype?limit=1", restricted=True)
        require(code == 200 and isinstance(readable, dict) and isinstance(readable.get("results"), list), "admission_read_denied")
        suffix = secrets.token_hex(8)
        code, reltype = self.request(backend, "POST", "/relationshiptype", {
            "aIsToB": "Synthetic CI guardian " + suffix,
            "bIsToA": "Synthetic CI dependent " + suffix, "description": "Owned disposable Initializer test"})
        require(code == 201 and isinstance(reltype, dict) and UUID_PATTERN.fullmatch(reltype.get("uuid", "")), "synthetic_relationship_type_creation_failed")
        code, relationship = self.request(backend, "POST", "/relationship", {
            "personA": self.fixtures[0]["person"], "personB": self.fixtures[1]["person"], "relationshipType": reltype["uuid"]})
        require(code == 201 and isinstance(relationship, dict) and UUID_PATTERN.fullmatch(relationship.get("uuid", "")), "synthetic_relationship_creation_failed")
        identifier = relationship["uuid"]
        before = self.query(db, "SELECT * FROM relationship WHERE uuid=" + sql_string(identifier))
        require(len(before) == 1, "fresh_synthetic_relationship_missing")
        require(self.query(db, "SELECT voided FROM relationship WHERE uuid=" + sql_string(identifier)) == ["0"], "synthetic_relationship_not_active")
        code, _ = self.request(backend, "DELETE", "/relationship/" + identifier + "?purge=true", restricted=True)
        require(code == 403, "admission_purge_not_denied")
        require(self.query(db, "SELECT * FROM relationship WHERE uuid=" + sql_string(identifier)) == before, "denied_purge_changed_relationship")
        code, _ = self.request(backend, "DELETE", "/relationship/" + identifier + "?reason=synthetic-ci", restricted=True)
        require(code == 204, "admission_void_not_allowed")
        require(self.query(db, "SELECT voided FROM relationship WHERE uuid=" + sql_string(identifier)) == ["1"], "allowed_void_not_persisted")
        emit("rbac", "PASSED", authorized_read=200, denied_purge=403, authorized_void=204)

    def upgrade(self):
        emit("upgrade", "RUNNING")
        db = self.start_database("upgrade")
        self.import_baseline(db)
        self.seed(db)
        expected = self.expected_upgrade_state(db, self.state(db))
        backend, volume = self.start_backend("upgrade", self.historical_config, restore=True)
        self.wait_initializer(backend, "upgrade")
        self.assert_checksums(backend)
        require(self.candidate_recorded(db), "candidate_history_missing")
        self.check_admission(db)
        self.assert_state(db, expected, "upgrade_changed_unapproved_rbac_or_references")
        clinical_drug = self.check_clinical_drug(backend, db, "upgrade")
        ocl_refresh = self.check_ocl_refresh(db, "upgrade")
        state, history = self.state(db), self.history(db)
        self.rbac(backend, db)
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        backend, _ = self.start_backend("idempotence", self.historical_config, data_volume=volume)
        self.wait_initializer(backend, "idempotence")
        self.assert_checksums(backend)
        self.assert_state(db, state, "second_start_changed_rbac")
        require(self.history(db) == history, "second_start_changed_history")
        self.check_clinical_drug(backend, db, "idempotence", previous=clinical_drug)
        self.check_ocl_refresh(db, "idempotence", previous=ocl_refresh)
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        backend, _ = self.start_backend("current-policy", self.candidate_config, data_volume=volume)
        self.wait_initializer(backend, "current_policy")
        self.assert_checksums(backend, self.candidate_role_md5)
        self.check_admission(db, self.candidate_privileges)
        state["role_privilege"].extend(CANONICAL_ROLE + "\t" + privilege for privilege in CURRENT_ADMISSION_ADDITIONS)
        self.assert_state(db, state, "current_csv_changed_unapproved_rbac")
        require(self.history(db) == history, "current_csv_changed_migration_history")
        self.rbac(backend, db)
        emit("current_policy", "PASSED", privileges=len(self.candidate_privileges), roles_checksum=self.candidate_role_md5)
        self.remove_container(backend)
        self.remove_container(db)

    def rejection(self):
        emit("reject", "RUNNING")
        configuration = self.directory / "configuration-rejection"
        shutil.copytree(self.historical_config, configuration)
        canary_uuid, canary_role = str(uuid.uuid4()), "Synthetic Initializer canary " + self.nonce[:8]
        with (configuration / ROLES_FILE).open(encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle))
        canary = configuration / "roles/zz-admission-initializer-canary.csv"
        with canary.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerow({"Uuid": canary_uuid, "Role name": canary_role,
                "Description": "Owned disposable failure-order test", "Inherited roles": "", "Privileges": ""})
        canary.chmod(0o644)
        canary_md5 = hashlib.md5(canary.read_bytes()).hexdigest()
        require((configuration / ROLES_FILE).read_bytes() == (self.historical_config / ROLES_FILE).read_bytes(), "canary_changed_roles_csv")
        db = self.start_database("rejection")
        self.import_baseline(db)
        self.seed(db, bad=True)
        before, history = self.state(db), self.history(db)
        backend, volume = self.start_backend("rejection", configuration, restore=True)
        self.wait_initializer(backend, "reject", reject=True)
        self.assert_checksums(backend)
        self.assert_state(db, before, "rejected_migration_changed_rbac")
        require(self.history(db) == history, "rejected_migration_changed_history")
        require(not self.candidate_recorded(db), "rejected_migration_was_recorded")
        require(self.query(db, "SELECT COUNT(*) FROM role WHERE uuid=" + sql_string(canary_uuid)) == ["0"], "later_roles_loader_ran_after_rejection")
        canary_checksum = "configuration_checksums/roles/zz-admission-initializer-canary.checksum"
        self.absent_checksum(backend, canary_checksum)
        self.docker("stop", "--time", "30", backend, timeout=45)
        self.remove_container(backend)
        # Correct only the owned extra fixture. No checksum/history/XML resets.
        self.query(db, "DELETE FROM role_privilege WHERE role='SIHSALUS Admision' AND privilege='Manage Roles'")
        backend, _ = self.start_backend("retry", configuration, data_volume=volume)
        self.wait_initializer(backend, "retry")
        self.assert_checksums(backend)
        self.check_admission(db)
        require(self.candidate_recorded(db), "retry_history_missing")
        require(self.query(db, "SELECT role FROM role WHERE uuid=" + sql_string(canary_uuid)) == [canary_role], "retry_did_not_load_later_roles_canary")
        require(self.checksum(backend, canary_checksum) == canary_md5, "retry_canary_checksum_missing")
        self.remove_container(backend)
        self.remove_container(db)
        emit("reject_retry", "PASSED", later_roles_loader_blocked=True, retry_without_checksum_clear=True)

    def cleanup(self):
        self.cleanup_deadline = time.monotonic() + 180
        failures = 0
        for container in list(reversed(self.containers)):
            try:
                self.remove_container(container)
            except HarnessFailure:
                failures += 1
        for volume in list(reversed(self.volumes)):
            try:
                self.owned("volume", volume)
                self.docker("volume", "rm", volume, timeout=45)
                self.volumes.remove(volume)
            except HarnessFailure:
                failures += 1
        if self.network:
            try:
                self.owned("network", self.network)
                self.docker("network", "rm", self.network, timeout=45)
                self.network = None
            except HarnessFailure:
                failures += 1
        if not failures:
            require(self.directory.name.startswith("admission-initializer-") and self.directory.is_dir()
                    and not self.directory.is_symlink(), "cleanup_directory_not_owned")
            try:
                shutil.rmtree(self.directory)
            except OSError:
                failures += 1
        emit("cleanup", "FAILED" if failures else "PASSED", unresolved_owned_resources=failures)
        return failures == 0


def main(scenario="upgrade"):
    harness, success, cleanup_ok = None, False, True
    def interrupted(signum, frame):
        raise HarnessFailure("interrupted")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        require(scenario in ("upgrade", "fresh"), "invalid_initializer_scenario")
        harness = Harness(os.environ)
        harness.prepare()
        if scenario == "fresh":
            harness.fresh()
        else:
            harness.baseline()
            harness.upgrade()
            harness.rejection()
        success = True
    except HarnessFailure as error:
        emit("harness", "FAILED", reason=str(error))
    except Exception:
        emit("harness", "FAILED", reason="unexpected_harness_error")
    finally:
        if harness is not None:
            try:
                cleanup_ok = harness.cleanup()
            except Exception:
                emit("cleanup", "FAILED", reason="owned_cleanup_incomplete")
                cleanup_ok = False
    emit("harness", "PASSED" if success and cleanup_ok else "FAILED",
         scope="ephemeral synthetic Initializer and native relationship RBAC",
         deployed_environment_validation=False)
    return 0 if success and cleanup_ok else 1


if __name__ == "__main__":
    sys.exit(main(os.environ.get("ADMISSION_INITIALIZER_SCENARIO", "upgrade")))
