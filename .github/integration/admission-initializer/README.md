# Admission Initializer integration

The harness loads the packaged configuration into pinned OpenMRS images and
checks startup, persisted metadata, upgrade history and REST authorization.
It runs only on disposable GitHub-hosted runners with synthetic data.

## Run

[admission-initializer.yml](../../workflows/admission-initializer.yml) runs all
six scenarios. A manual dispatch can select one scenario for diagnosis.

```sh
python3 -B .github/integration/admission-initializer/test_harness.py
```

The pure tests above need no Docker. Native execution requires the workflow's
runner environment, exact candidate checkout and three pinned content baselines.
Do not spoof runner variables to run it on a persistent machine.

| Scenario | Baseline and checks |
| --- | --- |
| `fresh` | Empty database, complete candidate, metadata and native admission RBAC. |
| `upgrade` | Content 1.25.15; historical unchanged-role-CSV migration, current policy, restart, rejection and retry. |
| `operational` | Content 1.25.15 with the recognized 55-permission admission alias and supplement; preserve assignments during reconciliation. |
| `ocl-fresh` | Current pinned runtime with empty database; catalog, numeric metadata, observations and restart. |
| `ocl-upgrade` | Published content 1.25.34 on the current pinned runtime; preserve catalog identities, relationships, ordering, observations and checksums through upgrade/restart. |
| `ocl-latest-upgrade` | Published content 1.25.41 on the same pinned runtime; preserve existing vitamin A and MINSA references, unchanged-file checksums and every catalog row through upgrade/restart. |

All six must pass on the candidate commit. Matrix failures do not cancel the
other scenarios. These checks do not replace clinical acceptance or DEV/QLTY
smoke tests listed in the [follow-up audit](../../../docs/audits/2026-10-19-normative-alignment-followup.md).

## Inputs and packaging

[guards.py](guards.py) holds the immutable image digests, distro revisions,
content baseline commits and module versions. The historical scenarios use the
image containing content 1.25.26; the current-runtime scenarios use the image
containing the published 1.25.34. Both use Initializer `2.13.0-sihsalus.2`.

Before startup the harness verifies image identity, runtime user, embedded
content and assembly layout. It replaces only files whose bytes match the
pinned content source, preserving other image configuration. Current source
files live in `configuration/`; the 1.25.15 source uses the historical nested
layout. Both produce the same package paths.

Initializer's retired-form fix is tracked in
[upstream #334](https://github.com/mekomsolutions/openmrs-module-initializer/pull/334)
and [SIHSalus #336](https://github.com/sihsalus/sihsalus/issues/336), owned by
`@Duvet05`. Updating a pin requires reviewing these contracts against that version.

## Assertions

### Startup and history

Every startup requires `fail_on_error`, checksums enabled, the current attempt's
Initializer completion marker and the expected started module/version from REST.
Each container uses a dedicated log filename; a restored log cannot prove a new
startup. HTTP health alone is insufficient. Authentication, malformed responses,
unexpected loader aborts and CSV error summaries fail the run.

The harness calls the internal `/openmrs/initialsetup` endpoint to trigger
installation if the image's startup request arrived too early. Requests stay
inside the owned container, without redirects. Core's `log.level` sets the
Initializer namespace to INFO so child loggers emit lifecycle records.

The roles CSV must have its actual MD5 checksum. The pinned Liquibase loader
does not write an XML file checksum; the harness requires it to remain absent
and uses the real `liquibasechangelog` for migration evidence. It never deletes
checksums or marks migrations executed.

Journal comparisons preserve checksums and identities. Only execution fields
of the four declared audit-module `runAlways` checks are normalized; their
checksums and all other columns remain compared. See the pinned
[audit changesets](https://github.com/sihsalus/openmrs-module-sihsalus-audit/blob/13712f1f08839047a360e452d988ee361d2181a0/api/src/main/resources/liquibase.xml).

### Admission and clinical metadata

Historical migration must produce the approved 58-privilege admission role
while the roles CSV remains byte-identical. The later complete candidate load
adds the declared logbook privilege. Full RBAC snapshots include unrelated
roles, user assignments, stock references and module-owned EMRAPI roles.

A synthetic admission user must read relationship types, receive 403 when
purging an active relationship, and successfully void it through ordinary
DELETE. The rejection fixture adds `Manage Roles`; loading must abort before
the canary role, preserve prior state, then succeed after removing that fixture
permission. Disposal of Initializer's classloader proves the stopped state
when Core also stops REST.

Fresh, upgrade and restart check versioned form schemas, historical schemas,
reference ranges, the additional medication presentation, neighborhood and
anatomy catalogs, and the vitamin A Numeric/UI concept. UUIDs and persisted
references must survive restart.

### Current-runtime catalog compatibility

The candidate uses the institutional loading namespace and 34 official published
exports from all 18 sources. Six releases `2026-10-22-01` explicitly restore the
2,862 weights absent from the first institutional import. Etnias keeps
`2026-10-21-01` and its 62 explicit weights; anatomy uses the published snapshot
`2026-10-16-1` without clinical changes. See the
[transition audit](../../../docs/audits/2026-10-16-ocl-institutional-transition.md).

All three catalog scenarios verify all 18 sources and their native OCL import items.
The 1.25.41 scenario overlays its exact pinned configuration on the same runtime;
it preserves the existing vitamin A concept and MINSA reference rows without
allowing those insertions again. Initializer's
[`BaseFileLoader`](https://github.com/sihsalus/openmrs-module-initializer/blob/806aec0a11fbb6b582629ecb2c89992e2e46107e/api/src/main/java/org/openmrs/module/initializer/api/loaders/BaseFileLoader.java)
skips byte-identical files. Therefore etnias' unchanged 1.25.41 ZIPs retain their
successful native item URLs under the old host. Expected URLs derive from the
exact baseline files and subscription; a changed file still requires the new
namespace, exact UUID/version and successful state. No checksum reset or forced
reload is used.
Upgrade compares every concept identity, set/answer relationship including
`sort_weight`, reference map, term and source. The only expected new concept is
the native vitamin A dose UUID `9c0b51ef-0d4c-49a3-bdbb-2ee7083fe778`:
it must be a new active Question/Numeric concept with UI, minimum zero and no
decimals. Etnias adds exactly 58 validated MINSA reference maps, 58 terms and one
source, preserving every baseline row and primary key. Both scenarios check all
etnia name identities and native searches by code/synonym, including unknown
codes; restart repeats the checks. No other graph change is accepted. See the
[etnia contract](../../../docs/contracts/etnias-minsa.md).

Birth length changes only `allow_decimal:false` to `true`, preserving its Numeric
UUID, internal identity and `cm` unit. Upgrade first creates a historical 30 cm
observation on the published baseline, then saves 30.1 cm through native REST
after loading the candidate. Fresh installation also saves both observations.
Restart compares the complete catalog, observations, journal and checksums,
including the newly inserted vitamin A concept. A graph, weight, old observation
or historical checksum difference still fails the run.

## Resources and diagnostics

Each job owns one backend (4 GiB, 2 CPUs) and MariaDB 10.11.7 (1 GiB, 1 CPU).
The isolated database uses `innodb_flush_log_at_trx_commit=2` to reduce cold-import
I/O; this fixture does not test crash durability. The first historical baseline
allows 45 minutes, other startups 35 minutes, within an 80-minute total budget.
Cleanup has three minutes; the workflow has a 90-minute timeout.

Containers, volumes and the internal network carry a random prefix and ownership
label. Docker uses the local runner socket and an empty configuration directory.
No host ports are published. Generated credentials stay in private files or stdin.
Cleanup removes only verified owned resources and reports incomplete cleanup.

CI retains JSONL phase results. `WAITING` reports elapsed time and the last
loading domain; neither establishes readiness. On unexpected abort,
`csv_error_summary` and `aborted_domains` identify the failing loader domains.
Catalog and RBAC differences report table/column names and counts, without row
contents. Raw logs, SQL dumps, HTTP bodies and credentials are not artifacts.

The temporary baseline-order export used to diagnose the institutional
transition was removed. Full in-memory ordering comparisons remain mandatory.
