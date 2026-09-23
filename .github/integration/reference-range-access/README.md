# Reference-range access contract

This test supports the [hospital access profiles](../../../docs/contracts/hospital-access-profiles.md)
and complements the [other validation layers](../../../docs/development.md#ensayos-de-integración).

Run from the repository root with Java 17:

```sh
mvn --batch-mode --no-transfer-progress --file .github/integration/reference-range-access/pom.xml test
```

The standalone test project uses OpenMRS Core **2.8.9**, the shipped temperature
criteria and both declared laboratory roles. It executes the native SpEL
`ConceptReferenceRangeUtility`, helper functions, API authorization annotations
and `AuthorizationAdvice`. Session privilege membership comes from the CSV;
clinical data services return synthetic enrollment and gestational-age values.
Patient Flags is not a dependency. No server, container or database is accessed.

Without `Get Patient Programs`, evaluation for a female patient fails with
`APIAuthenticationException` wrapped in `An error occurred while evaluating
criteria`, even when the enrollment query would return no records. The male
control short-circuits before that query. This distinction explains why a test
using only a male patient would miss the access dependency.

Six cases cover both laboratory roles, missing read permission, no maternal
enrollment, the male control, and continued rejection of creating or purging
program enrollments. This verifies the access contract, not clinical range
validity or observation persistence. A synthetic save/read/edit test against the
deployed backend remains required before acceptance.

`LaboratoryRangePopulationTest` additionally executes the shipped laboratory
criteria with Core 2.8.9. Six cases cover recorded/unknown/invalid prematurity,
week boundaries at the sample date, active and ended/voided postpartum states,
gestation continuing at 40 weeks, and native fallback after disabling the two
urine-creatinine rules with incompatible units. These check selection behavior,
not institutional approval of reference intervals. OpenMRS test logging stays
under `target/openmrs`.

All dependencies are test-only. The project is outside the content release
reactor and packaged configuration; CI blocks publication if its tests fail.
