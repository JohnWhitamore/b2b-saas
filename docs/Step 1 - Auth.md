# Auth

_John Whitamore_

_July 2025_

### Intro

This note discusses and implements authentication (AuthN) and authorization (AuthZ) using Auth0 within the AWS environment created in `Step 0 - AWS set up.md`. 

Authentication and authorization are primary concerns in an environment with a) several users, including programmatic users and b) people using coding assistants. Even before thinking about questions of effective cyber-security, those two points combine into the rhetorical question "do you want to vibe code an automated pipeline that will somehow manage to drop your production database?".

The first part of the note steps down through high-, medium- and low-level concepts to provide clarity before we commence implementation. The second part of the note is all about implementation and uses (as a running example) `SaaSCo` to represent the B2B SaaS company and `ClientCo` to represent one of their enterprise clients.

---

### High-level: concepts

Authentication is the act of verifying identity: confirming that a user, machine or service is who it claims to be. It’s the gatekeeper before any access is granted.

_Core concepts_

- Identity: a unique representation of a user or system (e.g. email, username, device ID).
- Authentication (AuthN): proving identity via credentials such as passwords, tokens or biometrics.
- Authorization (AuthZ): granting access based on identity and permissions.
- Identity Provider (IdP): a service that manages identities and issues credentials (e.g. Auth0, Google, Azure AD).
- Tokens: encoded proofs of identity (e.g. JSON Web Tokens - JWTs) used to access resources.
- Protocols: standards like OAuth 2.0, OpenID Connect, and SAML define how authentication flows work.

_Some common flows_

| Flow                      | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| **Password-based**        | Traditional login with username / password                   |
| **OAuth 2.0**             | Delegated access using tokens                                |
| **OpenID Connect (OIDC)** | Identity layer on top of OAuth 2.0                           |
| **MFA**                   | Multi-factor authentication - adds a second layer (e.g. SMS, biometrics) |
| **SSO**                   | Single sign-on - authenticate once, access many services     |

### Medium-level: how AWS implements authentication

AWS treats authentication as a foundational layer of identity and access management (IAM). It supports both human and machine identities.

_Key AWS Mechanisms_

- IAM users and roles: long-term identities with credentials or temporary roles assumed via STS.
- Federated Access: external IdPs (e.g. Auth0, Google) can federate into AWS via SAML (Security Assertion Markup Language) or OIDC (OpenID Connect).
- AWS IAM Identity Centre: centralised workforce identity management with SSO and MFA.
- Temporary credentials: issued via STS for short-lived access. Used heavily in role assumption.
- MFA: strongly recommended for root and IAM users. Supports virtual apps, hardware keys and passkeys.

_Authentication flow in AWS_

1. User signs in via console, CLI or API.
2. IAM matches credentials to a principal (user, role, federated identity).
3. IAM evaluates policies to determine authorisation.
4. Access is granted or denied based on permissions and context.

_Encouraged practices_

- Use temporary credentials via role assumption.
- Enable MFA for all users.
- Use IAM Identity Centre for centralised access.
- Prefer Attribute-Based Access Control (ABAC) for fine-grained permissions.

### Low-level: details of Auth0

Auth0 is a cloud-based identity provider that handles authentication, authorization and user management. It’s built on OAuth 2.0 and OpenID Connect.

_Core components_

- Universal login: hosted login page supporting social, enterprise and passwordless connections.
- Connections: define how users authenticate. e.g. database, social (Google, Facebook), enterprise (SAML, AD).
- Rules and actions: server-side hooks to customise login flows. e.g. assign roles, call Stripe.
- User profiles: rich metadata including `user_metadata`, `app_metadata` and linked identities.
- Tokens: Auth0 issues JWTs for identity (`id_token`) and access (`access_token`).

_Authentication API_

- RESTful endpoints for login, signup, logout, token exchange and user info.
- Supports multiple auth methods: OAuth2, client credentials, mTLS (Mutual Transport Layer Security) and JWT assertions.

_Protocols and flows_

| Flow                          | Description                                                  |
| ----------------------------- | ------------------------------------------------------------ |
| **Authorization Code + PKCE** | Recommended for SPAs and mobile apps                         |
| **Client Credentials**        | For machine-to-machine auth                                  |
| **Implicit Flow**             | Deprecated for SPAs (Single Page Applications). Use PKCE instead |
| **Passwordless**              | Via email or SMS                                             |
| **Social Login**              | OAuth-based login via Google, Facebook, etc.                 |

[PKCE: Proof Key for Code Exchange]

_Customization_

- Branding: custom login UI, email templates and domains.
- Actions: JavaScript snippets triggered during login/signup.
- Fine-Grained Authorization (FGA): relationship-based access control inspired by Google Zanzibar.

---

We now commence implementation.

### Create a sensible folder structure

Within the root `b2b-saas/` project folder, create folders called `infra/` and `fastapi_app/` so that we can keep our infrastructure (including auth) separate from the the app that we will later build and expose via FastAPI.

Inside the `infra/` folder, create this structure. We'll create the files that it mentions as we go along.

```bash
auth/
├── config/
│   └── auth_scopes.yaml       # Formalised permission contract
│
├── fastapi/
│   ├── middleware.py          # Token verification logic (JWT decoding, scope checks)
│   └── dependencies.py        # Re-usable FastAPI auth dependencies
│
├── tests/
│   └── test_auth_flow.py      # End-to-end: token, scopes, endpoint access
│
├── docs/
│   └── trust_boundaries.md    # Narrative articulation of access boundaries
│
└── clientco/
    ├── credentials.json       # ClientCo credentials (saved securely)
    └── sample_requests.http   # Example ingest and result retrieval calls using token
```

### Permission matrix

Define a minimal permission matrix that establishes a clear access model for how `ClientCo` interacts with `SaaSCo`. We do this by creating `auth_scopes.yaml` as below and saving it under `auth/config/` as in the folder structure chart above.

```yaml
permissions:
  - ingest:data        	# POST data to SaaSCo
  - read:forecast      	# GET forecast results
  - read:inventory     	# GET inventory results
restrictions:
  - no:execute_modeling # Modeling logic cannot be triggered manually
  - no:modify_pipeline  # Pipeline orchestration is internal only
```

This gives us a semantic contract ready to enforce at the authentication layer. We use it to constrain the API surface as follows: 

| Endpoint          | Method | Scope Required   | Description                       |
| ----------------- | ------ | ---------------- | --------------------------------- |
| `/ingest`         | POST   | `ingest:data`    | `ClientCo` pushes data            |
| `/forecast`       | GET    | `read:forecast`  | Retrieve demand forecast          |
| `/inventory`      | GET    | `read:inventory` | Retrieve inventory optimization   |
| *(internal only)* | —      | *restricted*     | Modelling orchestration and logic |

By the way, note that we have to use American spellings for operations and definitions, such as "modeling" with one "l". It's going to be ok :)

_Documentation_

It is useful to document what we have done in human-readable form. I have created `trust_boundaries.md` and saved it in the `auth/docs/` folder.

Note that there is the potential for two conflicting sources of truth: `trust_boundaries.md` and `auth_scopes.yaml` which are documenting the same thing, one for human readers and one for machines. It is therefore useful to put a short note within each file referring to the other file.

### Token verification and scope enforcement

We now translate the semantic contract that we have defined into executable logic. We'll create two Python files, both of which should be saved in the `auth/fastapi/` folder.

`middleware.py`: performs early validation of incoming requests by:

- decoding JWTs from headers or cookies
- verifying token signature and expiry
- extracting scopes and caching claims in request state

Note that you will need to enter 

`dependencies.py`: defines re-usable `Depends()` functions using a `require_scope()` function so that, later in the API router, we'll be able to write something like:

```python
@app.get("/forecast")
async def get_forecast(scope=require_scope("read:forecast")):
    ...
```

### Configure Auth0 M2M application

The motivation of this step is to construct a semantic and operational boundary between `ClientCo` and the FastAPI surface. The boundary will be expressive, enforceable and auditable. Note: M2M means "machine to machine".

Specific objectives of this step are:

- Designate an actor (`ClientCo`) and authorise it to perform specific rules, such as pass data to the API, read demand forecasts and inventory levels from the API.
- Enable secure, token-based communication via OAuth 2.0 Client Credentials Grant. This means no user prompts or logins, just clean service-to-service messaging.
- Embed intentional access patterns through scopes and audiences so that each call reflects a narrative of permission and purpose.
- Prepare the token infrastructure that let's us later verify claims and protect routes in Fast API.

_Auth0 account_

Go to [Auth0](https://autho.com) and sign up or log in.

_Application set up_

1. Left-hand menu: Applications/Applications
2. Top-right: Create Application
3. Click `[...]` and then:
   1. Settings
      1. Name: `clientco-m2m-access` (modify as appropriate)
      2. Application Type: select Machine to Machine
      3. Copy the Client ID and Client Secret to a safe place.
      4. Click Save.

_Client API registration_

Still in the Auth0 dashboard:

1. Left-hand menu: Applications/APIs
2. Click the Create API button
3. Name: `clientco-fastapi-service`. Note, use a different name to the one you entered in Settings (above).
4. Identifier: a URL such as `https://clientco/api`. This needs to look like a URL but it doesn't need to be hosted or to resolve to anything. It is used as the `aud` (audience) claim in access tokens.
5. Leave the other two fields at their default values, JWT and RS256.
6. Click Create (or Save)

_Scope definition_

Scopes define what the token holder is allowed to do. Auth0 will embed them in the `scope` field of access tokens.

Still in the Auth0 dashboard:

1. Left-hand menu: Applications/APIs
2. Click on the newly-created API `clientco-fastapi-service`
3. Click on the Permissions tab
4. Add two permissions:
   1. Permission:`read:data`; Description `ClientCo` enabled to read data
   2. Permission:`write:data`; Description `ClientCo` enabled to write data

Further permissions can be added later in the same way.

_Implement token verification in FastAPi_

We now create the runtime logic to:

- Accept tokens from `ClientCo`
- Verify that they are signed correctly using RS256 via Auth0's public key
- Confirm that the token was issued for the API by checking the `aud` claim that we set earlier
- Extract scopes for endpoint-level access control

I modified the `dependencies.py` file to incorporate two new functions: `get_public_key()` and `verify_token_and_scope()`. 

At this stage it is also necessary to replace two placeholder values in `dependencies.py` as follows:

1. `AUTH0_DOMAIN`: replace `your_tenant` with your tenant ID which can be found in Settings (bottom left of dashboard)
2. Ensure that `API_IDENTIFIER` is the same as the `aud` value set earlier e.g. `https://clientco/api`

_Granting access_



_Token flow testing_







| Sub-Step                                        | Description                                                  | Purpose                                                 |
| ----------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------- |
| **1.1 Define Trust Boundaries**                 | Clarify what ClientCo is *allowed* to do                     | Ingest, access results, not manipulate modeling logic   |
| **1.2 Choose Auth0 Flow Type**                  | Likely OAuth 2.0 with machine-to-machine (M2M) client credentials | Fits for server-to-server API access, no user UI needed |
| **1.3 Configure Auth0 Application**             | Create a M2M app with proper scopes                          | Lightweight, no need for Universal Login                |
| **1.4 Define API Audience & Scopes**            | Example scopes: `ingest:data`, `read:forecast`, `read:inventory` | Enables role-based endpoint access                      |
| **1.5 Implement Token Verification in FastAPI** | Middleware or dependency-based JWT decoding                  | Secures the API surface cleanly                         |
| **1.6 Protect Routes Based on Scope or Claim**  | Endpoint-level protection using scopes or custom claims      | Operational clarity and least privilege enforcement     |
| **1.7 Test with Sample ClientCo Credentials**   | Create test client, obtain token, exercise full workflow     | Validates auth from ingest to output                    |






