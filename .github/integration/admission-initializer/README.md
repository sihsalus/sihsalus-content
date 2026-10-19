# Admission Initializer integration

`harness.py` starts the pinned SIHSalus backend image and a disposable MariaDB
on a GitHub-hosted runner, loads the candidate content with Initializer in
`fail_on_error` mode and asserts in the database and through REST that the
content loaded. It never contacts DEV/QLTY/PROD, reads no existing credential,
uses no existing account or patient and publishes nothing.

Related: [admission contract](../../../docs/contracts/admission-role-reconciliation.md),
[content guide](../../../docs/content-guide.md#presentaciones-adicionales-de-medicamentos) (clinical drug catalog) and
[development guide](../../../docs/development.md).

## Invocation

`admission-initializer.yml` (called from `main.yml`) runs the five scenarios
as a matrix with `fail-fast: false`; all must pass on the same candidate SHA.
The checkout must be the exact `GITHUB_SHA` with a clean tracked worktree, plus
the three pinned source commits:

```sh
git fetch --no-tags --depth=1 origin \
  8000b27f48bf124fe9a553d4ba41c678e9acc231 \
  762920145a806f989fd8876ab2938ef217f57aab \
  b9e93638fd7ed9c8dffe8b48f2be868f3d9b1a10
python3 -B .github/integration/admission-initializer/test_harness.py   # no Docker
ADMISSION_INITIALIZER_DISPOSABLE=github-runner-only \
  ADMISSION_INITIALIZER_SCENARIO=upgrade \
  python3 -B .github/integration/admission-initializer/harness.py
```

Use `ADMISSION_INITIALIZER_SCENARIO=fresh` for the independent fresh-candidate
scenario, or `ADMISSION_INITIALIZER_SCENARIO=operational` for the additional
55-permission legacy alias upgrade from a real 1.25.15 baseline. CI runs all
five jobs with `fail-fast: false`; all must pass on the same candidate SHA.
The operational case uses synthetic accounts and a random alias UUID, transfers
references to the existing canonical role, and checks the full RBAC snapshot,
unchanged/current CSV loading, idempotence, and native allowed/denied access.
It never copies the alias privileges into the canonical policy. Each successful
upgrade/fresh installation also requires the arrival-payment visit attribute
with its active FreeText 0..1 contract.

The preparatory changeset is a recorded no-op outside the 55-permission input.
When the original reconciliation rejects another policy, prior history and all
RBAC rows must remain unchanged; only that preceding no-op record is allowed.

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

The following inputs remain unchanged for `upgrade`, `fresh` and `operational`.
The additional OCL scenarios use the separately pinned current runtime below.

- Backend: `ghcr.io/sihsalus/sihsalus-backend@sha256:ae9afe41f7632f25268203772ec74266fd0a5495ad7b9ab5e09c9e6a6df6fcd8`.
- Distro source label: `fb11da724dced859d00974c9ff2928aae135e704`.
- Database: `mariadb:10.11.7`; the running server must report that exact version.
- Embedded SIH content: 1.25.26, source `762920145a806f989fd8876ab2938ef217f57aab`.
- Applied baseline: 1.25.15, source `8000b27f48bf124fe9a553d4ba41c678e9acc231`.
- Initializer: `2.13.0-sihsalus.2`, source
  `806aec0a11fbb6b582629ecb2c89992e2e46107e`. This fixes native creation of a
  retired AMPATH form by supplying the same retirement reason used for updates.
  The content remains declarative; no SQL loader or historical schema rewrite
  is introduced. Upstream contribution:
  [Initializer #334](https://github.com/mekomsolutions/openmrs-module-initializer/pull/334).
  Temporary fork tracking and replacement condition:
  [SIHSalus #336](https://github.com/sihsalus/sihsalus/issues/336), owner `@Duvet05`.
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
packaged 1.25.26 file against bytes copied from the image. It removes only these
verified owned files when overlaying baseline or candidate content. Every other
observed image configuration file remains byte-identical, including inherited
reference content. Conflicting writes to unowned files are rejected. This proves
preservation of the observed remainder, not a complete independent manifest of
a particular reference-content release. Unsafe tar paths, links, duplicate
files, and special files are rejected.

Current sources and the embedded image content live directly under
`configuration/`. The pinned 1.25.15 baseline retains
`configuration/backend_configuration/`; only that commit uses the legacy
assembly contract. Both layouts produce the same runtime paths
(`roles/`, `liquibase/`, etc.) and the distributed ZIP still uses
`configuration/backend_configuration/`. The guard checks source and output
directories and each file set's includes/excludes, so a source-tree cleanup
cannot silently change the overlay.

## Required runtime evidence

### Institutional OCL transition on the current runtime

`ocl-fresh` and `ocl-upgrade` reuse the same runner guards, native Initializer,
owned container/volume lifecycle, configuration assembly and strict startup
checks. They do not build or modify a backend image and do not contact OCL or
any deployed environment. Their immutable inputs are:

- Backend: `ghcr.io/sihsalus/sihsalus-backend@sha256:72c0c4cedfd5ba4b3eb1a3fabd8d1f4e9222548ce49ba06dd7ac2c3a00282414`.
- Distro source label: `bdfa1bb78095e59fc24eb655bb39aa352fdf5681`;
  [successful build](https://github.com/sihsalus/sihsalus/actions/runs/38807577878).
- Core: `2.8.10-sihsalus.4`; OCL: `4.0.0`; Initializer: `2.13.0-sihsalus.2`.
  Image properties must match; REST must report the expected started OCL and
  Initializer modules. The digest, revision label and platform remain mandatory.
- Embedded and upgrade baseline content: published `1.25.34`, commit
  `b9e93638fd7ed9c8dffe8b48f2be868f3d9b1a10`. Every owned configuration file must
  match the image before overlay. The Maven Central ZIP has SHA-256
  `6f1fdcf430d6d0cac6e5f71ff9e337c8af8f5c81384cfc0f20e6e62231093b45`.
  Later commit `78178494` kept version `1.25.34` but changed two roles/privileges
  CSV files; it is not byte-equivalent to this published release.

The fresh scenario loads the full candidate into an empty owned database.
The upgrade scenario first loads the complete published baseline, records all
Initializer checksum files and Liquibase history, and creates one synthetic
person and an integer birth-length observation through native REST. It then
loads the candidate using the same database and application-data volumes.
No checksum is removed or reset: unchanged and retired-file checksum records
must survive byte-identically, changed files must receive their actual new
checksum, and all 34 candidate OCL ZIP checksums must be present.

After verifying baseline startup, checksums and integer-only birth-length
metadata, `ocl-upgrade` also saves `ocl-baseline-order-{sha}.json` as a separate
seven-day CI artifact. This happens **before creating synthetic people or
observations and before loading the candidate**. Neither `ocl-fresh` nor the
historical scenarios produce it. The artifact records the pinned baseline
version/source SHA and backend digest, plus only the 17,404 active OCL catalog
relationships declared by the published baseline exports: 3,270 `Q-AND-A` and
14,134 `CONCEPT-SET` mappings. Each entry contains its type, mapping UUID,
parent/target concept UUIDs, `drug_uuid: null`, and the actual numeric sort weight
(or JSON `null` for SQL NULL). The OCL edges point to concepts; an unexpected
drug reference fails validation. No database IDs, concept names, accounts,
clinical records, SQL dumps or raw responses are included.

The database edges must match the allowlisted UUIDs and endpoints exactly;
missing, duplicate or mismatched entries fail. Canonical UUIDs and the published
36-character CIEL identifiers (digits followed by `A`) are validated, and
malformed/non-finite weights are rejected. CSV-owned relationships outside the
OCL allowlist are omitted. The complete projection is validated before the
artifact becomes visible; an existing destination or symlink is not overwritten.
The JSON is **review evidence, not a migration or OCL update payload**. Its
presence proves only that baseline metadata was captured: the candidate may
still fail the unchanged complete graph/weight, checksum and restart assertions.
It does not establish the ordering of an existing DEV/QLTY/production database.

Both scenarios require the exact birth-length UUID
`bf82beb1-d3b8-400e-8160-90869cad8136`, the existing numeric concept ID, unit `cm`,
and `allow_decimal=true` in SQL and REST. A native REST submission of `30.1`
must persist exactly; it must not be rounded. The baseline observation remains
byte-identical. All concept identities, set/answer edges, reference-map
identities/types and reference-term source/codes are compared across upgrade;
native metadata audit timestamps are not mistaken for identifier changes.

For every one of the 32,551 concepts and 20,552 mappings in the candidate ZIPs,
the latest native OCL item must carry its unchanged external identifier, the
institutional namespace `https://api.gidis-terminology.duckdns.org`, its expected
concept version URL and a successful native state. All 18 sources are required,
including `anatomia-procedimientos`; a source skipped because its ZIP checksum
did not change fails this assertion. Older OCL Cloud import history may remain.
The file importer records a local startup path as `import.subscription_url`;
that field is not used as proof of the HTTP namespace.

Finally, both scenarios restart the candidate with the same volumes. Every
checksum, normalized Liquibase history row, catalog identity/reference and
synthetic observation must remain unchanged; the decimal metadata and complete
institutional namespace are verified again. The existing 80-minute harness
budget and 90-minute job timeout remain bounded. Local pure tests do not prove
these runtime assertions; both CI jobs must pass before runtime compatibility
is claimed. No DEV, QLTY or production operation is part of these tests.

### Historical admission scenarios

History snapshots retain every column and row. The pinned audit module at
[`13712f1`](https://github.com/sihsalus/openmrs-module-sihsalus-audit/blob/13712f1f08839047a360e452d988ee361d2181a0/api/src/main/resources/liquibase.xml)
declares four native `runAlways` checks (07 through 10). Only their
`DATEEXECUTED`, `ORDEREXECUTED`, `EXECTYPE` and `DEPLOYMENT_ID` are normalized
for comparisons: Liquibase updates these on each startup. Their exact
ID/author/file identities, checksums and all other fields remain compared.
Failed/skipped execution states are rejected; `MARK_RAN` is permitted only
for the two trigger-creation checks whose preconditions declare it. All content
changesets and other module rows preserve execution metadata too. This is a
comparison rule for the pinned image, not a database mutation, skipped migration
or checksum reset. Keep it limited to the verified native declarations when
updating the image. Owner and tracking: `@Duvet05`, SIHSalus #336.

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
   completion. Restart with the same data and checksums and require RBAC
   unchanged except the sanctioned EMRAPI grant of the declared
   hospital-reference names and `CURRENT_EMRAPI_ADDITIONS` to Full/High, plus
   complete journal rows, with only the native `runAlways` execution metadata
   exception described above.
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

Both scenarios also verify the additional ursodeoxycholic acid concept and
250 mg tablet presentation after loading. SQL checks their active state,
identities and references; REST checks the medication search representation
consumed by the frontend. The upgrade restart must preserve those records
without duplicates. See the [catalog contract](../../../docs/content-guide.md#presentaciones-adicionales-de-medicamentos).

The OCL refresh has a separate read-only SQL check in fresh, upgrade and the
upgrade restart: both added UUIDs must exist once, stay active, retain their
Spanish fully specified names and classes, and import as datatype `N/A`.
OCL 3.2.0 normalizes the export's literal `None` to `N/A`; the check verifies
the resulting database values. The neighborhood set must remain active with
ten active members. Concept IDs and the catalog snapshot must survive the
restart unchanged. Logs expose only fixed counts and the phase result.

The rejection fixture uses `Manage Roles`, which Core creates via `@AddOnStartup`.
Core defines `Purge Relationships` but does not create it on a clean installation;
the harness neither requires nor creates that privilege. Its absence does not
change the separate native REST purge-denial assertion above.

## Startup and checksum evidence

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
Before an unexpected abort it reports the CSV-summary boolean and deduplicated
domains present in both the public source and the candidate configuration, as
described under bounded progress diagnostics. Only the exact
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

Initializer 2.13.0-sihsalus.2 on the pinned backend writes the roles-file MD5
checksum. Its `LiquibaseLoader2_5` does **not** write XML file checksums, but an
inherited matching XML checksum could still suppress loading. The harness
therefore requires that XML checksum to be absent throughout; it never fabricates
one, deletes checksums, or uses `clearCheckSums`. Real `liquibasechangelog` rows
and their `MD5SUM` provide the XML execution evidence.

## Resources, diagnostics and limits

Each scenario runs on its own runner with only one backend (4 GiB, 2 CPUs) and
one database (1 GiB, 1 CPU) concurrently. Within `upgrade`, baseline snapshots
are reused for the upgrade and rejection branches. The first historical baseline
startup allows at most 45 minutes; every other startup allows at most 35 minutes.
All startups share an 80-minute total budget per scenario; cleanup has a separate
three-minute global budget and at most 45 seconds per Docker operation. Each
matrix job has a 90-minute timeout.

The exclusively disposable database uses MariaDB 10.11's native
[`innodb_flush_log_at_trx_commit=2`](https://mariadb.com/docs/server/server-usage/storage-engines/innodb/innodb-system-variables#innodb_flush_log_at_trx_commit):
commits write the redo log while disk flushes occur periodically, avoiding a
forced flush for every metadata transaction. The effective setting is checked
before loading any content. SQL transactions, rollback, checksums and all
assertions remain enabled. This fixture does **not** test durability under an
operating-system crash or power loss. No deployed database configuration changes.
The change addresses the write-heavy cold import after the operational baseline
again exhausted 45 minutes in
[main CI 35936258926](https://github.com/sihsalus/sihsalus-content/actions/runs/35936258926).
That timeout did not identify its root cause; a successful candidate run must
still prove the complete load. Raising the deadline again, changing historical
metadata or skipping domains is not part of this change. CI owner: `@Duvet05`,
tracking [SIHSalus #336](https://github.com/sihsalus/sihsalus/issues/336).
Reassess this fixture setting if CI adds crash-recovery coverage or changes its
storage; such coverage requires the normal durable database configuration.

The baseline allowance addresses the cold-start timeout observed in
[main CI 35932198274](https://github.com/sihsalus/sihsalus-content/actions/runs/35932198274):
both update scenarios were still producing Initializer log output when the
35-minute limit expired, with no abort or CSV error marker. The identical source
passed all scenarios in
[PR CI 35929593687](https://github.com/sihsalus/sihsalus-content/actions/runs/35929593687).
This increases only the first baseline startup allowance; it does not identify
the cause of the runtime variation. No elapsed time, progress counter or log
activity proves readiness: completion and the real started module are still
required. Exhausting either budget remains a failed validation.

Stdout contains only sanitized JSON phase results, public source identifiers,
checksums and fixed diagnostic codes. Preserve that JSONL in the separate
`admission-initializer-{scenario}-{sha}` CI artifacts,
never raw application logs, Docker inspections, HTTP bodies, SQL dumps or the
private run directory. The OCL baseline ordering artifact described above is
the only additional metadata projection; it is not copied from raw diagnostics.
A failed RBAC snapshot comparison identifies only the
fixed table name, table presence and counts of added/removed whole rows; it never
prints roles, privileges, users or row contents. Repeated rows remain significant.
Cleanup validates resource ownership before removal;
resource creation intents are recorded before Docker calls so client timeouts
cannot silently omit a possibly created resource. Unverifiable absence or
ownership remains a cleanup failure, not a successful cleanup claim.
Failure or exhaustion is reported as failed, with unresolved owned resources
left to the disposable runner's teardown. Cleanup never targets an existing
workspace, broad directory or unlabelled resource.

### Bounded progress diagnostics

During lifecycle waits, a `WAITING` record appears initially and at most once
per minute with `elapsed_seconds`, `completion_seen` and `last_loading_domain`.
The last observed loading domain does not establish which domain failed.
Core's installer `hasErrors=true` still fails with `installation_reported_errors`;
its absence or a false value cannot replace the Initializer lifecycle assertions.

Immediately before `unexpected_initializer_abort`, a `FAILED` record reports
`csv_error_summary` and a sorted, deduplicated `aborted_domains` list. A domain
is emitted only if its directory exists both in the public checked-out
`configuration/` and in the assembled candidate configuration. Unknown or absent
domains are omitted. No filenames, paths, URLs, raw log lines, SQL, credentials
or exception text are copied. These observations do not identify the underlying
exception or prove a root cause; an empty domain list does not imply success.
The abort remains a failure, including a CSV error summary without an abort
marker or a separate loader failure during the expected Liquibase rejection.
An expected Liquibase rejection alone keeps its existing acceptance checks.
No resource hints, installer progress counters or thread dumps are produced.
These diagnostics do not change startup deadlines or establish readiness.

Pure tests exercise safety and assertion contracts without Docker. Only a
successful run on the exact candidate SHA supplies the integration evidence
above. Even that result is a bounded synthetic role/relationship smoke, not
general clinical acceptance, deployed-environment evidence, domain-owner
approval, or authorization to bypass repository merge/release requirements.

## Canonical admission and Laboratory update

The operational scenario also seeds the recognized admission supplement and
verifies its retirement without losing canonical user assignments. Both the
historical CSV restart and the final candidate load must leave it absent.
The historical roles CSV retains its exact baseline checksum; the subsequent
current-policy phase expects only the approved admission logbook grant and
`Get Patient Programs` on canonical `Laboratorio`. The separately loaded native
hospital CSV contains only operational Laboratory and Support roles. Whole-table
comparisons still include unrelated identities, assignments and module scopes.
