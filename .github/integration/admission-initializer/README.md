# Admission Initializer integration

This is a real Initializer and narrow native-RBAC test for an exclusively owned,
ephemeral GitHub-hosted Linux runner. It does not build Maven modules, publish
images, deploy, contact DEV/QLTY/PROD, or use existing accounts or patients.
The local unit tests are not evidence that the containers or migration passed.

## Invocation and isolation

The caller must check out the exact candidate `GITHUB_SHA` with a clean tracked
worktree and fetch only these immutable source commits:

```sh
git fetch --no-tags --depth=1 origin \
  8000b27f48bf124fe9a553d4ba41c678e9acc231 \
  57690d4e976ef6d97a925c68103d532d10ee15cf
python3 -B .github/integration/admission-initializer/test_harness.py
```

Only inside that disposable GitHub-hosted runner, run:

```sh
ADMISSION_INITIALIZER_DISPOSABLE=github-runner-only \
  ADMISSION_INITIALIZER_SCENARIO=upgrade \
  python3 -B .github/integration/admission-initializer/harness.py
```

Use `ADMISSION_INITIALIZER_SCENARIO=fresh` for the independent fresh-candidate
scenario. CI runs both matrix jobs with `fail-fast: false`; both must pass on
the same candidate SHA before publication.

The runner guard also requires GitHub's `GITHUB_ACTIONS`, `CI`,
`RUNNER_ENVIRONMENT`, `RUNNER_OS`, `GITHUB_REPOSITORY`, `GITHUB_SHA`, and
`RUNNER_TEMP` values. These are refusal checks, not a substitute for a trusted
workflow: do not spoof them to run against a developer or persistent host.

Docker always uses a new empty configuration directory and the runner's local
Unix socket. External Docker hosts and contexts are forbidden. Public images
are pulled before creating an internal-only network. No backend port is
published; REST uses loopback inside the owned backend container, with redirects
and retries disabled. Passwords are generated per run and supplied in private
files or stdin, never command-line arguments or emitted logs. No existing
credential is read. The configuration and snapshot bind mounts are exclusively
within a newly created run directory; database and application data volumes
must match both a random resource prefix and its ownership label.

## Immutable inputs and content ownership

- Backend: `ghcr.io/sihsalus/sihsalus-backend@sha256:d03384f0368052101bfb949c0de24547f6e5aaf7caedce874f1eb7c296711fe2`.
- Distro source label: `492757585d30b9f2b70c3bbff603d16f635e5d28`.
- Database: `mariadb:10.11.7`; the running server must report that exact version.
- Embedded SIH content: 1.25.12, source `57690d4e976ef6d97a925c68103d532d10ee15cf`.
- Applied baseline: 1.25.15, source `8000b27f48bf124fe9a553d4ba41c678e9acc231`.
- Candidate: checked-out SHA and its release version from `pom.xml`, greater
  than 1.25.15. The historical migration still produces the approved 58-entry
  admission policy. The current admission policy adds only
  `app:home.libroAtenciones`, for 59 privileges; any other policy change requires
  a separate review.

The candidate removes only the `Privilege Level: Full` and `Privilege Level: High`
rows from `roles-core.csv`. The pinned
[EMRAPI activator](https://github.com/openmrs/openmrs-module-emrapi/blob/a06a2efd651435609a1c4b39ef35501b3401ff5d/api/src/main/java/org/openmrs/module/emrapi/EmrApiActivator.java#L78)
owns these roles, creates them when absent and maintains their privileges. Its
[constants](https://github.com/openmrs/openmrs-module-emrapi/blob/a06a2efd651435609a1c4b39ef35501b3401ff5d/api/src/main/java/org/openmrs/module/emrapi/EmrApiConstants.java#L79)
retain both historical UUIDs. Other roles can still inherit them by name, and
the privilege catalog remains intact. Initializer no longer rewrites these two
roles when another row changes the CSV checksum.

The backend probe never starts OpenMRS: it overrides the entrypoint with only
`id -u; id -g`, uses no network, a read-only root filesystem and no capabilities.
Its digest, revision label, platform, launch command, actual startup scripts,
embedded content version and numeric runtime UID/GID are checked before
application startup or snapshot restoration. Numeric users need not appear in
`/etc/passwd`; their effective identity must match the image's declared user.
Unverifiable image assumptions fail closed; restore does not assume `1001:0`.

The harness verifies the exact assembly include/exclude contract and every
packaged 1.25.12 file against bytes copied from the image. It removes only these
verified owned files when overlaying baseline or candidate content. Every other
observed image configuration file remains byte-identical, including inherited
reference content. Conflicting writes to unowned files are rejected. This proves
preservation of the observed remainder, not a complete independent manifest of
a particular reference-content release. Unsafe tar paths, links, duplicate
files, and special files are rejected.

## Required runtime evidence

The `upgrade` scenario requires:

1. **Baseline:** bootstrap a fresh synthetic database with complete 1.25.15
   configuration and strict `fail_on_error`, verify real current-attempt
   completion, the actual started Initializer module/version, effective runtime
   properties and system flags, real Liquibase history and roles checksum.
   Restart the same baseline with its existing data and checksums before
   seeding migration fixtures. Require another complete startup, unchanged history
   and checksums, both EMRAPI role UUIDs and the 58-entry admission policy.
   Create two synthetic people and users; no patient is required. Stop the
   backend before capturing owned database and application-data snapshots.
   This captures the baseline after EMRAPI has maintained its roles on restart.
2. **Historical unchanged-CSV upgrade:** restore the baseline snapshots, seed the two
   approved 57-permission identities and synthetic user references, then load
   candidate configuration with only `roles-core.csv` replaced by the exact
   baseline file. This explicit historical fixture is not the current packaged
   configuration. The pre-existing roles CSV checksum must still match unchanged
   bytes while the new changeSet produces exactly the approved 58
   permissions. Compare all RBAC rows, including Full/High, and supported optional
   references against the explicit allowed transformation, preserving unrelated
   multiplicities and Stock identity/audit fields. No role groups are excluded.
   Require real changeSet history and full loader
   completion. Restart with the same data and checksums and require unchanged
   RBAC and complete journal rows, including execution metadata.
3. **Current candidate CSV:** start the reconciled database with the complete,
   unmodified candidate configuration. Require its actual roles checksum, exactly
   59 admission privileges, and only the approved read privilege added to the
   complete RBAC snapshot. Liquibase history must remain unchanged. This checks
   the current role policy independently of the historical migration.
4. **Native RBAC:** a synthetic user assigned only `Admision` reads relationship
   types. Create a new active relationship between the synthetic people. Purging
   that existing active relationship must return 403 without changing the row;
   ordinary deletion must return 204 and persist `voided=1`. An already voided
   or absent relationship is not accepted as a permission test. Run this with
   both the historical and current policies.
5. **Rejection and retry:** restore a separate baseline snapshot and seed one
   identity with the 59th, unapproved `Manage Roles` permission. Add a new,
   separate, empty-privilege canary CSV to the historical-CSV configuration,
   without changing candidate XML or the baseline `roles-core.csv`.
   Require the specific changeSet's current-attempt abort,
   no completion, disposal of Initializer's current classloader, unchanged RBAC
   and journal snapshots, no candidate journal entry, and no canary role or
   checksum. Remove only the synthetic extra permission, then restart with the
   same configuration, data and checksums. Require full completion, 58 approved
   permissions and the newly loaded canary role with its actual checksum.

The independent `fresh` scenario starts the complete candidate configuration
against an empty owned database. It requires full Initializer completion and
the actual module/version, effective strict settings, candidate changeSet
history, the candidate roles checksum, both EMRAPI role UUIDs and exactly 59
admission privileges. It creates its own two synthetic people/users and runs
the same native REST read, 403 purge-denial and 204 persisted-void assertions.
It does not reuse the upgrade scenario's database or snapshots.

The rejection fixture uses `Manage Roles`, which Core creates via `@AddOnStartup`.
Core defines `Purge Relationships` but does not create it on a clean installation;
the harness neither requires nor creates that privilege. Its absence does not
change the separate native REST purge-denial assertion above.

No domains are excluded. The effective startup mode is required in both runtime
properties and JVM flags; setting a global property or merely observing HTTP
health is insufficient. Lifecycle evidence combines each new container's stdout
with its dedicated Initializer log. Each startup configures a different filename
containing the run nonce and phase; the effective runtime property must match.
The reader never opens the default `initializer.log` or another phase's file,
so a restored baseline completion cannot validate a later attempt. A missing
file remains pending; an unreadable or symlinked file fails. Successful startups
also require the actual module/version from REST. A transient unavailable endpoint,
including the installation filter's HTTP 302, is polled within the existing deadline
without following redirects. Only a valid HTTP 200 module response can prove
readiness; persistent redirects time out, and authentication errors, malformed
responses or wrong versions fail.

For the expected rejection, Core's
[Listener](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/web/src/main/java/org/openmrs/web/Listener.java)
stops non-mandatory modules, including REST. The stopped-state evidence is therefore
the current container's exact `Disposing of ModuleClassLoader` message identifying
`initializer`. Core's
[stopModule](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/api/src/main/java/org/openmrs/module/ModuleFactory.java)
removes the module from its started-modules map before disposing the classloader.
Only the `org.openmrs.module.ModuleClassLoader` logger is additionally set to
`DEBUG`. Each phase creates a new container and never restarts modules within it;
the retry uses another container. The marker is not an oracle for a reused
container or for completed filesystem cleanup. An absent REST response alone
never proves rejection, and all abort, checksum, journal and canary checks remain.

The file-abort detector recognizes both loading and pre-loading failures from
any domain using the exact message shape in the pinned
[BaseFileLoader](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api/src/main/java/org/openmrs/module/initializer/api/loaders/BaseFileLoader.java).
It emits only an abort boolean, never a domain or filename. Only the exact
Liquibase loading abort together with the candidate changeSet marker qualifies
as the expected rejection, still requiring no completion and the actual stopped
module. Any other domain abort, pre-loading abort, or CSV error summary fails
immediately, including when it coexists with that expected rejection. This is
not a claim that the detector recognizes every possible startup failure.

Before reading lifecycle logs in each wait iteration, an anonymous GET reaches
the fixed internal `http://127.0.0.1:8080/openmrs/initialsetup` endpoint. This
triggers installation against the disposable synthetic database when the
image's one-shot startup request occurs before the web filter is ready. It is
not a read-only health probe: the endpoint can start the configured installation.
There is no authentication, cookie persistence, query parameter, redirect,
proxy, curl configuration inheritance or automatic request retry; the request
has a five-second deadline and its response body is discarded. The root path
would only redirect, while `/auto_run_openmrs` can invoke a different fallback;
neither is used. An HTTP 200, redirect or error never satisfies the lifecycle
assertions. The existing completion/abort, strict-mode and actual module-state
requirements remain mandatory.

The pinned
[Initializer logger](https://github.com/mekomsolutions/openmrs-module-initializer/blob/3077975fb4f58c91ff3113d7fed1e3df88829476/api-2.4/src/main/java/org/openmrs/module/initializer/api/logging/InitializerLogConfigurator2_4.java)
configures a file appender. Reading Docker stdout alone does not establish that
its completion message will be observed. The dedicated log preserves the same
completion/abort assertions without assuming console propagation or accepting
Core's installer completion as module completion. Raw log contents are never
printed or retained as artifacts. Only a successful container run confirms this
fix against the pinned image; the unit tests exercise the reader and assertions.

Core's `log.level` system property also sets the Initializer namespace to `INFO`.
The pinned module configures its parent logger with `Logger.setLevel`, which does
not update its child loggers under Log4j2. They otherwise inherit Core's `WARN`
level, leaving the dedicated file empty and hiding lifecycle messages. Core's
[configuration factory](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/api/src/main/java/org/openmrs/logging/OpenmrsConfigurationFactory.java)
applies `log.level` to the logger configuration before module startup. This affects
logging only; loader scope and success assertions remain unchanged.

The bootstrap contract follows the pinned Core
[StartupFilter](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/web/src/main/java/org/openmrs/web/filter/StartupFilter.java)
and [InitializationFilter](https://github.com/openmrs/openmrs-core/blob/4dda0f50a60991a5af9a4b36508e69bb3561c8a6/web/src/main/java/org/openmrs/web/filter/initialization/InitializationFilter.java).
Repeated requests do not force a new installation while the filter reports one
already started. This corrects a harness bootstrap gap; it does not establish
that the gap was the sole cause of an earlier startup timeout.

Initializer 2.13.0-sihsalus.1 on the pinned backend writes the roles-file MD5
checksum. Its `LiquibaseLoader2_5` does **not** write XML file checksums, but an
inherited matching XML checksum could still suppress loading. The harness
therefore requires that XML checksum to be absent throughout; it never fabricates
one, deletes checksums, or uses `clearCheckSums`. Real `liquibasechangelog` rows
and their `MD5SUM` provide the XML execution evidence.

## Resources, diagnostics and limits

Each scenario runs on its own runner with only one backend (4 GiB, 2 CPUs) and
one database (1 GiB, 1 CPU) concurrently. Within `upgrade`, baseline snapshots
are reused for the upgrade and rejection branches. Each backend startup allows
at most 35 minutes, sharing an 80-minute total budget per scenario; cleanup has
a separate three-minute global budget and at most 45 seconds per Docker
operation. Each matrix job has a 90-minute timeout.
A cold full baseline can exhaust these budgets; timeout is a failed validation,
not permission to reduce the loader scope or accept partial startup.

Stdout contains only sanitized JSON phase results, public source identifiers,
checksums and fixed diagnostic codes. Preserve only that JSONL in the separate
`admission-initializer-{scenario}-{sha}` CI artifacts,
never raw application logs, Docker inspections, HTTP bodies, SQL dumps or the
private run directory. A failed RBAC snapshot comparison identifies only the
fixed table name, table presence and counts of added/removed whole rows; it never
prints roles, privileges, users or row contents. Repeated rows remain significant.
Cleanup validates resource ownership before removal;
resource creation intents are recorded before Docker calls so client timeouts
cannot silently omit a possibly created resource. Unverifiable absence or
ownership remains a cleanup failure, not a successful cleanup claim.
Failure or exhaustion is reported as failed, with unresolved owned resources
left to the disposable runner's teardown. Cleanup never targets an existing
workspace, broad directory or unlabelled resource.

During lifecycle waits, a sanitized `WAITING` record appears initially and at
most once per minute. It contains only the observed HTTP code (or `null` for
transport unavailability), running state, and boolean completion/abort/candidate
marker/CSV-error signals from the current container. At the same bounded
interval, an anonymous, no-redirect, no-retry GET to the fixed internal
`/openmrs/initialsetup?page=progress.vm.ajaxRequest` reads Core's installer
progress. Strictly boolean `hasErrors` and `initializationComplete` values
are exposed as `installation_has_errors` and `installation_complete`.
Nonnegative integer `actionCounter` and `completedPercentage` values are exposed
as `installation_action_counter` and `installation_completed_percentage`;
booleans, strings, fractions and negative counters become `null`. Missing,
malformed or unavailable values also produce `null`, not a healthy state.
Core's percentage is per task, can reset or exceed 100, and is omitted after
installation completes. It is not an overall progress or readiness assertion.
`initializer_log_present` distinguishes a missing attempt log from an empty
one; `initializer_log_bytes` counts the bytes read from that file, or is `null`
when absent. These observations reuse the existing log read and contain no path.
`hasErrors=true` fails with the static code `installation_reported_errors`.
Neither `hasErrors=false`, `initializationComplete=true`, nor an HTTP code can
replace the Initializer lifecycle assertions. Installer messages, error pages,
log lines, response bodies, credentials and exception text are never emitted.
These diagnostics are not passing test results.

Pure tests exercise safety and assertion contracts without Docker. Only a
successful run on the exact candidate SHA supplies the integration evidence
above. Even that result is a bounded synthetic role/relationship smoke, not
general clinical acceptance, deployed-environment evidence, domain-owner
approval, or authorization to bypass repository merge/release requirements.
