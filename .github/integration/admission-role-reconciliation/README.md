# Admission migration real-engine integration harness

This standalone test project runs the complete candidate content Liquibase XML
against MariaDB **10.11.7**, using Liquibase **4.32.0**, MariaDB JDBC **3.5.4**,
and Java **21**. The Java dependencies match OpenMRS Core **2.8.9**; the database
version and `utf8mb4_bin` collation match the distro test Compose configuration.
It is not a content module, is not packaged in the content ZIP, and does not
publish or deploy anything.

## Isolation and execution

The reusable `admission-role-reconciliation.yml` workflow creates its own
ephemeral MariaDB service. The normal build calls it at the same checkout SHA
and depends on its success before publication; it also supports manual runs.
It has no independent push/PR trigger or competing concurrency group.
Credentials are fixed synthetic fixture values, not
repository secrets. The harness accepts only a numeric loopback port and the
literal database `admission_reconciliation_ci`; it does not accept a backend URL
or arbitrary database credentials. It refuses a nonempty database before any
DDL, claims the empty database with a per-run ownership marker, and checks that
marker before resetting only its enumerated fixture tables. Foreign keys stay
enabled throughout the migration. The runner disposes of the service afterward.

Do not point this harness at DEV, QLTY, PROD, an existing OpenMRS schema, a shared
database, or a forwarded database port. Do not substitute runtime credentials.
Running locally requires separately approved, exclusively owned disposable
MariaDB infrastructure; this command does not create or download containers:

```sh
ADMISSION_TEST_DATABASE_DISPOSABLE=admission_reconciliation_ci \
ADMISSION_TEST_DB_PORT='REPLACE_WITH_OWNED_NUMERIC_PORT' \
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/admission-role-reconciliation/pom.xml test
```

Compilation and guard/policy checks do not need MariaDB or Docker:

```sh
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/admission-role-reconciliation/pom.xml \
  -Dtest=HarnessGuardTest test
```

Missing database configuration fails the integration suite; it is not silently
skipped or replaced with SQLite/H2. Surefire XML reports are retained by the
workflow for seven days, tied to its tested SHA. A locally compiled test is not
evidence that its MariaDB assertions passed.

## What this proves when the integration job passes

- Real Liquibase parsing, MariaDB syntax, preconditions, changelog checksums,
  and the complete candidate XML sequence, including the historical 20260722
  normalization pending, genuinely executed, and genuinely `MARK_RAN`.
- Fresh/canonical/legacy/duplicate identities; optional tables absent or
  present; deduplicated user/tag references (Patient Flags has no artificial
  uniqueness constraint), and preserved stock scope IDs/UUIDs, audit fields,
  and dependent child rows.
- Privileges compared with the frozen 1.25.15 policy, with the sole permitted
  input omission of `Delete Relationships` under the previous 57-privilege
  contract. Existing identities explicitly converge to that 58-privilege output
  in SQL, adding only that permission already published in #222. The later
  `app:home.libroAtenciones` grant from #224 belongs to the current 59-privilege
  CSV loaded afterward by Initializer; it is not an input to this migration.
  A missing native privilege or a later CSV grant applied before reconciliation
  causes a closed failure without changing RBAC.
- Closed failures for an unrelated UUID owner, extra/missing privileges,
  inheritance in either direction, an unknown role foreign key, and a
  nontransactional optional table, additional copied columns, or a trailing-space
  identity/reference alias, with RBAC snapshots unchanged. Missing core primary
  keys, role UUID uniqueness, core role foreign keys, and the privilege foreign
  key are rejected independently. Each rejection also evaluates
  its specific candidate SQL guard against the fixture to establish its cause.
- An injected trigger failure at legacy-role deletion rolls back the preceding
  reconciliation DML, including the new 57-to-58 privilege grant, leaves the
  changeset unrecorded, and permits a successful 58-privilege retry after removal
  of that owned synthetic trigger. This is transaction
  rollback evidence, **not** evidence of an explicit Liquibase rollback script.
- A second complete run is idempotent in RBAC rows and changelog records.

`src/test/resources/admission-role-1.25.15.csv` preserves the header and canonical
Admisión row from source `8000b27f48bf124fe9a553d4ba41c678e9acc231`. Java fixtures
and SQL assertions use this historical policy. Python checks it against an
independent 58-entry allowlist and verifies that the current CSV and validator
add exactly the approved logbook read permission. The guard test also compares
the two CSV policies. Current CSV changes therefore cannot rewrite the historical
fixtures or silently expand the SQL allowlist.

The historical changelog fixture is the full candidate XML minus the new reconciliation
changeset, executed first at the same logical path. It does not fabricate a
successful historical changeset by inserting a made-up checksum.
Additional tests execute the six withdrawn 20260903 changesets, preserved from
`9855170d45d922756e0719725fe06a36a3bbd960` in `withdrawn-reconciliation.xml`,
and verify that the candidate refuses those histories under either the actual
Initializer table `liquibasechangelog` or the default `DATABASECHANGELOG` name.

## Explicit limits and remaining gates

The schema is an intentionally small synthetic model with real foreign keys and
InnoDB tables, not a copy of an installation or the full OpenMRS/module schemas.
The tests contain no patients, accounts from an environment, clinical records,
or credentials from an environment. They cannot inventory arbitrary installed
modules or validate a database upgrade against an operational backup.

**NOT RUN by this harness:** Initializer **2.13.0-sihsalus.1**, from source
`3077975fb4f58c91ff3113d7fed1e3df88829476`, loading `roles-core.csv` through
OpenMRS **2.8.9**, file/row checksums, and effective allowed/denied authorization
for synthetic users. The source archive is pinned by the distro to SHA256
`a750faaa6485b7f5716db8dcd94552102710cd9af0a80b067982133b02365e69`.

That additional phase distinguishes unchanged and changed CSV checksums:
Initializer's role processor replaces privileges and inherited roles when a row
is loaded, while its checksum mechanism can skip loading. The SQL test therefore
asserts 57-to-58 convergence without calling or simulating a CSV reload; it does
not leave #222's grant contingent on a changed checksum. The Initializer harness
separately exercises the unchanged historical CSV and the current CSV carrying
#224's read permission. A CSV policy oracle in these tests is **not** a substitute
for invoking that loader. The upstream
Initializer Validator is also not a drop-in exact-stack test: that source pins
Core 2.3.6 and starts MySQL 5.7.31, despite its README's MariaDB description.

No green result here authorizes environment access, proves an Initializer
startup, supplies clinical approval, or changes release/deployment gates.
