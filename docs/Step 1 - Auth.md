# Auth

_John Whitamore_

_July 2025_

### Intro

This note discusses and implements authentication (AuthN) and authorization (AuthZ) using Auth0 within the AWS environment created in `Step 0 - AWS set up.md`. 

Authentication and authorization are primary concerns in an environment with a) several users, including programmatic users and b) people using coding assistants. Even before thinking about questions of effective cyber-security, those two points combine into the rhetorical question "do you want to vibe code an automated pipeline that will somehow manage to drop your production database?".

The first part of the note steps down through high-, medium- and low-level concepts to provide clarity before we commence implementation. The second part of the note is all implementation.

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



