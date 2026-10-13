# Admission Initializer integration

`harness.py` starts the pinned SIHSalus backend image and a disposable MariaDB
on a GitHub-hosted runner, loads the candidate content with Initializer in
`fail_on_error` mode and asserts in the database and through REST that the
content loaded. It never contacts DEV/QLTY/PROD, reads no existing credential,
uses no existing account or patient and publishes nothing.

Related: [admission contract](../../../docs/contracts/admission-role-reconciliation.md),
[content guide](../../../docs/content-guide.md) (clinical drug catalog) and
[development guide](../../../docs/development.md).

## Invocation

`admission-initializer.yml` (called from `main.yml`) runs the three scenarios
as a matrix with `fail-fast: false`; all must pass on the same candidate SHA.
The checkout must be the exact `GITHUB_SHA` with a clean tracked worktree, plus
the two pinned source commits:

```sh
git fetch --no-tags --depth=1 origin \
  8000b27f48bf124fe9a553d4ba41c678e9acc231 \
  762920145a806f989fd8876ab2938ef217f57aab
python3 -B .github/integration/admission-initializer/test_harness.py   # no Docker
ADMISSION_INITIALIZER_DISPOSABLE=github-runner-only \
  ADMISSION_INITIALIZER_SCENARIO=upgrade \
  python3 -B .github/integration/admission-initializer/harness.py
```

`validate_runner` (`guards.py`) refuses to run anywhere but a GitHub-hosted
Linux runner: the harness creates and deletes containers, volumes and a network
and must only ever own a disposable host. Do not spoof the runner variables to
run it on a developer machine or a persistent host. Docker uses a fresh empty
config directory and the local socket (`DOCKER_HOST`/`DOCKER_CONTEXT` are
rejected); no port is published and REST is called over loopback inside the
backend container; passwords are generated per run and passed through private
files or stdin.

`test_harness.py` covers the assembly/CSV contracts, the RBAC oracle, history
normalization and the parsing in the `check_*` content checks. It is not
evidence that the containers passed.

## Scenarios

| `ADMISSION_INITIALIZER_SCENARIO` | Phases | Specific assertions |
| --- | --- | --- |
| `fresh` | candidate configuration on an empty database | candidate and operational changesets recorded; candidate roles checksum; 59 admission privileges |
| `upgrade` | 1.25.15 baseline, restart, upgrade with the baseline `roles-core.csv`, idempotence restart, current CSV, rejection, retry | RBAC snapshot equals the oracle after each phase; Liquibase history unchanged by restarts and by the current CSV; historical forms keep identity and schema hash; a seeded unapproved `Manage Roles` grant aborts the reconciliation changeset with RBAC, history and a canary roles CSV untouched, and the retry after removing it completes |
| `operational` | same baseline, then the 55-permission `SIHSALUS Admision` alias plus the 15-privilege hospital supplement | alias references transfer to canonical `Admision` without copying its privileges; the supplement is retired; snapshot, idempotence and current-CSV checks as in `upgrade` |

Every completed startup additionally requires Initializer's completion message
in the current attempt's log, the started module and pinned version from REST,
the roles checksum, both EMRAPI role UUIDs, the arrival-payment visit attribute
(active FreeText, 0..1) and the content checks: the ursodeoxycholic acid
concept and 250 mg tablet (SQL plus the REST drug search), the two OCL refresh
concepts and the ten-member neighborhood set, the 133-member procedure anatomy
set with Spanish preferred names, HL7 `v2-0550` mappings, FHIR source
association and four `q`/`memberOf` searches, and the ten reviewed form
schemas plus eighteen laboratory range criteria. Restarts must leave all of
these identities unchanged. Native RBAC in every scenario: a synthetic user
holding only `Admision` reads relationship types (200), is denied purging an
active relationship (403, row unchanged) and may void it (204, `voided=1`).

The RBAC oracle (`expected_upgrade_state`, `expected_hospital_role_state`,
`expected_emrapi_refresh`) is an explicit relational transformation of the
seeded snapshot; it never executes or translates the candidate SQL. Whole tables
are compared, including repeated rows: `role`, `role_privilege`, `role_role`,
`user_role`, `patientflags_tag_role` and `stockmgmt_user_role_scope`. History
comparisons normalize only the execution metadata of the audit module's four
`runAlways` changesets (`sihsalusaudit-20260819-07` to `-10`).

## Pinned inputs

| Input | Value |
| --- | --- |
| Backend image | `ghcr.io/sihsalus/sihsalus-backend@sha256:ae9afe41f7632f25268203772ec74266fd0a5495ad7b9ab5e09c9e6a6df6fcd8`, revision label `fb11da724dced859d00974c9ff2928aae135e704` |
| Database | `mariadb:10.11.7`, `utf8mb4_bin`, `innodb_flush_log_at_trx_commit=2` (disposable fixture; no durability claim) |
| Content embedded in the image | 1.25.26, source `762920145a806f989fd8876ab2938ef217f57aab` |
| Applied baseline | 1.25.15, source `8000b27f48bf124fe9a553d4ba41c678e9acc231` (legacy `configuration/backend_configuration/` layout) |
| Initializer | `2.13.0-sihsalus.2`, source `806aec0a11fbb6b582629ecb2c89992e2e46107e`; fork tracked in [SIHSalus #336](https://github.com/sihsalus/sihsalus/issues/336), upstream [Initializer #334](https://github.com/mekomsolutions/openmrs-module-initializer/pull/334) |
| Candidate | the checked-out SHA; its `pom.xml` version must be a release greater than 1.25.15 |

All values live in `guards.py`. The candidate is overlaid on the image's shipped
configuration: only files byte-identical to the pinned 1.25.26 source are
replaced and every other image file is preserved (`assemble`); each source's
`assembly.xml` must match the known contract (`validate_assembly`). Policy
expectations checked in `prepare`: the historical migration yields the
58-privilege admission policy, the current CSV adds only
`app:home.libroAtenciones` (59), `Laboratorio` gains only `Get Patient Programs`
and the hospital CSV declares only `SIHSALUS Laboratorio` and `SIHSALUS Soporte`.
Any other policy change fails before Docker starts and needs its own review.

## Limits

- Budgets: 45 minutes for the first baseline startup, 35 minutes for every
  other startup, 80 minutes per scenario, 3 minutes for cleanup (45 seconds per
  Docker call); the job timeout is 90 minutes. One backend (4 GiB, 2 CPUs) and
  one database (1 GiB, 1 CPU) run at a time.
- Readiness is only Initializer's completion message in the current attempt's
  dedicated log plus a started module over REST; elapsed time, HTTP codes and
  installer progress never count. The anonymous GET to `/openmrs/initialsetup`
  on each poll only kicks Core's installation filter when the image's one-shot
  startup request raced ahead of the web filter.
- The expected rejection is only the Liquibase abort naming the candidate
  changeset followed by Core disposing the `initializer` classloader in the same
  container. Any other domain abort, pre-loading abort or CSV error summary
  fails immediately.
- Initializer writes the roles CSV checksum but not the Liquibase XML checksum;
  the harness requires the XML checksum to stay absent and never clears or
  fabricates checksums.
- Output is JSONL: stage, status, fixed reason codes, public SHAs and counts.
  Raw logs, Docker inspections, HTTP bodies, SQL and row contents are never
  printed; a failed snapshot comparison names only the table and the counts of
  added/removed rows; the periodic `WAITING` line carries elapsed seconds and
  the last loading domain. Only that JSONL is kept as a CI artifact.
- Cleanup removes only resources carrying this run's ownership label; anything
  unresolved is reported as a cleanup failure and left to the runner teardown.
- These are loader and native authorization checks on synthetic data: not
  clinical acceptance, not deployed-environment evidence and not a release gate
  by themselves.
