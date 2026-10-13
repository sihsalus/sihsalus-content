# Admission migration real-engine integration harness

Standalone Maven test project that runs the complete candidate content
Liquibase XML against MariaDB **10.11.7** with Liquibase **4.32.0**, MariaDB
JDBC **3.5.4** and Java **21** (the OpenMRS Core 2.8.9 stack). It is not a
content module, is not packaged in the content ZIP and deploys nothing.

The [admission contract](../../../docs/contracts/admission-role-reconciliation.md)
defines the supported transitions; the [development guide](../../../docs/development.md)
locates the other validation layers.

## Running

The reusable `admission-role-reconciliation.yml` workflow starts its own
ephemeral MariaDB service and is called by the main build at the same SHA.
Locally it needs an exclusively owned, disposable MariaDB: the harness accepts
only a numeric loopback port and the literal database
`admission_reconciliation_ci`, refuses a nonempty database and marks the
database per run before resetting its fixture tables.

```sh
ADMISSION_TEST_DATABASE_DISPOSABLE=admission_reconciliation_ci \
ADMISSION_TEST_DB_PORT='REPLACE_WITH_OWNED_NUMERIC_PORT' \
mvn --batch-mode --no-transfer-progress \
  --file .github/integration/admission-role-reconciliation/pom.xml test
```

Do not point it at DEV, QLTY, PROD, an existing OpenMRS schema or a forwarded
port. Missing database configuration fails the suite; it is never skipped or
replaced with an embedded engine. The workflow keeps the Surefire reports for
seven days.

## Coverage

`AdmissionMigrationTest` executes the whole changelog on a small synthetic
schema with real InnoDB foreign keys and asserts:

- the historical 20260722 normalization pending, executed and `MARK_RAN`;
- fresh, canonical, legacy and duplicate admission identities converge to the
  frozen 1.25.15 policy (`admission-role-1.25.15.csv`, 58 privileges) with
  user/tag references transferred and stock scope rows preserved;
- the 55-permission operational alias and the 15-privilege hospital supplement
  (`admission-*-privileges.txt`) are reconciled or retired without touching
  unrelated rows, and a second full run is idempotent;
- altered policies, inheritance, unknown references, missing core constraints
  and the withdrawn 20260903 changesets (`withdrawn-reconciliation.xml`) fail
  closed with RBAC and changelog unchanged;
- an injected trigger failure rolls back the reconciliation DML, leaves the
  changeset unrecorded and allows a successful retry.

## Limits

The schema is a synthetic model, not an installation or the full OpenMRS and
module schemas, and holds no environment data. Initializer CSV loading,
checksums and effective OpenMRS authorization are covered by the
[Initializer harness](../admission-initializer/README.md) (Initializer
`2.13.0-sihsalus.2`), not here. A green run does not prove an Initializer
startup, supply clinical approval or change release gates.
