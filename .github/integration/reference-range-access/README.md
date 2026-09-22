# Reference-range access contract

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

All dependencies are test-only. The project is outside the content release
reactor and packaged configuration; CI blocks publication if its tests fail.
