# Reference-range access contract

Supports the [hospital access profiles](../../../docs/contracts/hospital-access-profiles.md)
and complements the [other validation layers](../../../docs/development.md#ensayos-de-integración).

Run from the repository root with Java 17:

```sh
mvn --batch-mode --no-transfer-progress --file .github/integration/reference-range-access/pom.xml test
```

`ReferenceRangeAccessTest` evaluates the shipped maternal temperature criteria
with OpenMRS Core 2.8.9's `ConceptReferenceRangeUtility` and `AuthorizationAdvice`,
granting each of the two laboratory roles exactly the privileges declared in the
roles CSVs: both must evaluate the criteria, and a woman without a maternal
enrollment must not match. `LaboratoryRangePopulationTest` executes the shipped
laboratory criteria against prematurity, week-boundary, postpartum and gestation
cases, including the native fallback for the two disabled urine-creatinine rules.

Limits: data services and session membership are stubbed; no server, container
or database is used. This verifies the access contract and criteria selection,
not clinical validity of the intervals or observation persistence. Dependencies
are test-only; the project is outside the release reactor and CI blocks
publication if it fails.
