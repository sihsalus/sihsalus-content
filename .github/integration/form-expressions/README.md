# Clinical form expression checks

The two neonatal cases for issues #389 and #390 evaluate the expressions from the
shipped birth form with the real OpenMRS expression evaluator. Its logical
operators evaluate both operands, whereas JavaScript short-circuits them. A
`node:vm` test alone therefore missed the original missing-patient error.

CI checks out frontend SHA `0420291580c1a5d8ee3c39712afa8b62174eceea` and uses that
repository's existing Yarn version, lockfile and evaluator build. This is the same
evaluator used by frontend PR #1229 at `a46a8653c0fb4fa1d499b232459cef0f16fbca89`.
The focused installation builds only `@openmrs/esm-expression-evaluator`; it does
not build the frontend applications. No backend, server or browser is required.
Updating this pin requires verifying the evaluator used by the frontend candidate.

Use an existing frontend checkout with its own dependencies installed. Build the
evaluator there if its `dist/index.js` is absent:

```sh
corepack yarn workspace @openmrs/esm-expression-evaluator build
```

Then run from the content repository, replacing the path with that checkout:

```sh
export SIHSALUS_EXPRESSION_EVALUATOR=/absolute/path/to/frontend/packages/libs/esm-expression-evaluator/dist/index.js
npm ci --prefix .github/integration/form-expressions --ignore-scripts
npm test --prefix .github/integration/form-expressions
TZ=America/Lima npm test --prefix .github/integration/form-expressions
TZ=America/New_York npm test --prefix .github/integration/form-expressions
```

A missing environment variable or module fails the tests; there is no fallback to
JavaScript. The birth-form cases cover missing/invalid demographics, an optional
discharge date, the birth-day boundary, Yes/No/unanswered hospitalization, and
retained duration including zero. The dependency extractor also checks that both
hospitalization fields can trigger each other's reevaluation.

The seven other existing cases still use `node:vm` and the form engine's date
library. Neither kind of expression check proves browser behavior or successful
encounter persistence; clinical validation in an authorized environment remains
separate.
