#!/usr/bin/env python3
"""Temporary metrics on the existing harness's owned synthetic GitHub runner."""
import json
import os
import re
import signal
import time
from harness import Harness, emit
from guards import HarnessFailure

STACK_CATEGORIES = {
    "hibernate_dirty_check": ("org.hibernate.event.internal.DefaultFlushEntityEventListener",),
    "hibernate_flush": ("org.hibernate.event.internal.AbstractFlushingEventListener",),
    "hibernate_search": ("org.hibernate.search.", "org.apache.lucene."),
    "location_validation": ("org.openmrs.validator.LocationValidator",),
    "metadata_save_handlers": ("org.openmrs.aop.RequiredDataAdvice", "org.openmrs.api.handler."),
    "jdbc_query": ("org.mariadb.jdbc.", "com.mysql.cj.", "com.mysql.jdbc."),
    "jdbc_pool_wait": ("com.mchange.v2.resourcepool.BasicResourcePool",),
    "socket_read": ("sun.nio.ch.SocketDispatcher.read", "sun.nio.ch.NioSocketImpl.implRead", "java.net.SocketInputStream"),
    "monitor_wait": ("java.lang.Object.wait", "java.util.concurrent.locks.LockSupport.park"),
    "file_read": ("java.io.FileInputStream.read", "sun.nio.ch.FileDispatcherImpl.read"),
    "class_loading": ("java.lang.ClassLoader.loadClass", "org.openmrs.module.ModuleClassLoader"),
    "xml_parse": ("org.apache.xerces.", "com.sun.org.apache.xerces."),
    "initializer_locations": ("org.openmrs.module.initializer.api.loc.",),
    "initializer_concepts": ("org.openmrs.module.initializer.api.c.", "org.openmrs.module.initializer.api.ocl."),
}
DB_COUNTERS = ("Innodb_buffer_pool_reads", "Innodb_buffer_pool_read_requests", "Innodb_data_reads",
               "Innodb_data_writes", "Innodb_row_lock_current_waits", "Innodb_row_lock_time", "Threads_running")


def container_metrics(data):
    try:
        value = json.loads(data)
    except (ValueError, TypeError):
        return {}
    if not isinstance(value, dict):
        return {}
    result = {}
    for key, output, maximum in (("CPUPerc", "cpu_percent", 100000), ("MemPerc", "memory_percent", 100)):
        match = re.fullmatch(r"([0-9]{1,6}(?:\.[0-9]{1,3})?)%", str(value.get(key, "")))
        if match and float(match[1]) <= maximum:
            result[output] = float(match[1])
    if re.fullmatch(r"[0-9]{1,6}", str(value.get("PIDs", ""))):
        result["processes_and_threads"] = int(value["PIDs"])
    return result


def thread_metrics(text):
    result = []
    for block in re.split(r'\n(?=")', text):
        frames = [line for line in block.splitlines() if re.match(r"\s+at ", line)]
        if not any("org.openmrs.module.initializer." in frame or
                   "org.openmrs.web.filter.initialization." in frame for frame in frames):
            continue
        state = re.search(r"java.lang.Thread.State: (RUNNABLE|BLOCKED|WAITING|TIMED_WAITING|NEW|TERMINATED)\b", block)
        matches = []
        for frame in frames:
            for category, markers in STACK_CATEGORIES.items():
                if any(marker in frame for marker in markers) and category not in matches:
                    matches.append(category)
        result.append({"state": state[1] if state else None, "stack_categories": matches})
        if len(result) == 8:
            break
    return result


class StartupProfile(Harness):
    def __init__(self, env):
        super().__init__(env)
        self.deadline = min(self.deadline, time.monotonic() + 20 * 60)
        self.next_snapshot = time.monotonic() + 5 * 60
        self.snapshot_count = 0

    def snapshot(self, backend):
        data = {"runner_cpus": os.cpu_count(), "startup_threads": [], "database_counters": {}}
        databases = [name for name in self.containers if name.endswith("-db")]
        targets = {"backend": backend}
        if len(databases) == 1:
            targets["database"] = databases[0]
        for component, name in targets.items():
            self.owned("container", name)
            stats = self.docker("container", "stats", "--no-stream", "--format", "{{json .}}", name,
                                timeout=10, allow_failure=True)
            data[component] = container_metrics(stats.stdout) if stats.returncode == 0 else {}
        emit("startup_resources", "DIAGNOSTIC_ONLY", **data)
        if "cpu_percent" in data["backend"]:
            self.snapshot_count += 1
        processes = self.docker("exec", backend, "jcmd", "-l", timeout=10, allow_failure=True)
        pids = []
        if processes.returncode == 0:
            for line in processes.stdout.decode("utf-8", "replace").splitlines():
                match = re.match(r"^([1-9][0-9]*)\s+", line)
                if match and "sun.tools.jcmd.JCmd" not in line:
                    pids.append(match[1])
        data["jvm_probe_available"] = len(pids) == 1
        if len(pids) == 1:
            threads = self.docker("exec", backend, "jcmd", pids[0], "Thread.print", timeout=15, allow_failure=True)
            if threads.returncode == 0:
                data["startup_threads"] = thread_metrics(threads.stdout.decode("utf-8", "replace"))
            heap = self.docker("exec", backend, "jcmd", pids[0], "GC.heap_info", timeout=15, allow_failure=True)
            match = re.search(rb"garbage-first heap\s+total ([0-9]+)K, used ([0-9]+)K", heap.stdout)
            if heap.returncode == 0 and match:
                data["heap_total_kib"], data["heap_used_kib"] = int(match[1]), int(match[2])
        if len(databases) == 1:
            sql = "SHOW GLOBAL STATUS WHERE Variable_name IN (" + ",".join("'" + key + "'" for key in DB_COUNTERS) + ")"
            for row in self.query(databases[0], sql):
                fields = row.split("\t")
                if len(fields) == 2 and fields[0] in DB_COUNTERS and re.fullmatch(r"[0-9]{1,20}", fields[1]):
                    data["database_counters"][fields[0]] = int(fields[1])
        emit("startup_resources", "DIAGNOSTIC_ONLY", **data)

    def installation_progress(self, backend):
        progress = super().installation_progress(backend)
        if time.monotonic() >= self.next_snapshot:
            self.snapshot(backend)
            self.next_snapshot = time.monotonic() + 5 * 60
        return progress


def main():
    def interrupted(signum, frame):
        raise HarnessFailure("interrupted")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    runtime = None
    cleanup_ok = True
    try:
        runtime = StartupProfile(os.environ)
        runtime.prepare()
        runtime.baseline()
        emit("startup_profile", "BASELINE_COMPLETED", full_upgrade_validation=False)
    except HarnessFailure as error:
        emit("startup_profile", "STOPPED", reason=str(error), full_upgrade_validation=False)
    except Exception:
        emit("startup_profile", "STOPPED", reason="unexpected_profile_error", full_upgrade_validation=False)
    finally:
        if runtime is not None:
            try:
                cleanup_ok = runtime.cleanup()
            except Exception:
                cleanup_ok = False
                emit("cleanup", "FAILED", reason="owned_cleanup_incomplete")
    emit("startup_profile", "DIAGNOSTIC_ONLY", full_upgrade_validation=False, cleanup_complete=cleanup_ok)
    return 0 if cleanup_ok and runtime is not None and runtime.snapshot_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
