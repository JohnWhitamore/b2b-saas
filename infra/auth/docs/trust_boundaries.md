# Trust Boundaries



### Overview

This document defines the trust boundaries between `SaaSCo` (provider of B2B services) and `ClientCo` (enterprise client). It clarifies which actions `ClientCo` is permitted to perform via the REST API and which operations are retained exclusively by `SaaSCo`.

### Actors

- `SaaSCo`: operates internal modelling and optimisation logic
- `ClientCo`: pushes data and reads results but does not orchestrate or modify `SaaSCo` logic

### Trust Contract

| Scope              | Description                        | Permitted To ClientCo? |
| ------------------ | ---------------------------------- | ---------------------- |
| `ingest:data`      | POST data to `SaaSCo`              | ✅ Yes                  |
| `read:forecast`    | GET forecast results               | ✅ Yes                  |
| `read:inventory`   | GET inventory optimisation results | ✅ Yes                  |
| `execute:modeling` | Run or trigger internal modelling  | ❌ No                   |
| `modify:pipeline`  | Modify orchestration / scheduling  | ❌ No                   |

### Rationale

`ClientCo` interacts with a modular surface:

- They submit data using a scoped `ingest:data` token
- They retrieve computed results using `read:forecast` and `read:inventory`
- They are not permitted to alter, execute or interfere with `SaaSCo`’s modelling or orchestration

These boundaries encode the principle of least privilege and reinforce semantic clarity across the API.

### Notes

- These scopes are implemented in Auth0 and enforced via FastAPI dependencies
- The absence of a scope is itself an enforcement mechanism: unexposed permissions are inaccessible
- This file is versioned and maintained alongside other artifacts in `infra/auth/`