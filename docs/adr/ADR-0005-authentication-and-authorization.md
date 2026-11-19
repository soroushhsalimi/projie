# ADR-0005 — Authentication and authorization model

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-11-19 |
| **Deciders** | Software Architect |
| **Consulted** | Project owner |
| **Supersedes** | none |
| **Superseded by** | none |
| **Related** | ADR-0002, F-0102, F-0103, F-0104 |

## Context and Problem Statement

SARA has three roles with materially different powers, and managers are further **scoped** to specific
dormitories. A single wrong authorization check means one resident can read another's residency
records, or one manager can approve requests for a dormitory they do not operate.

Requirements to satisfy:

- Public registration for residents; admin/manager accounts are provisioned by an admin.
- Session revocation must be possible (password change, admin suspension, "log out other devices").
- The SPA runs in a browser; tokens must not be readable by injected scripts where avoidable.
- Authorization must express both **role/permission** ("may review requests") and **scope** ("only for
  dormitory X").
- No external identity provider in V1; no social login; no SSO.

The question: what authentication mechanism, and how do we model authorization so it is simple to
apply, hard to forget, and cheap to test?

## Decision Drivers

- Security: credential theft and token replay must have bounded blast radius.
- Simplicity: one maintainer must operate it; no auth server to run.
- Testability: every endpoint's authorization must be provable with positive and negative tests.
- UX: sessions should survive a page reload and a browser restart within a reasonable window.
- Zero lock-in to a vendor.

## Considered Options

1. **Short-lived JWT access token + rotating opaque refresh token (DB-backed sessions) + RBAC with
   permissions and dormitory scope.**
2. Server-side sessions with an opaque cookie only (no JWT), stored in Redis/Postgres.
3. Third-party identity provider (Auth0/Keycloak/Clerk) with OIDC.
4. Long-lived JWT only, no refresh mechanism.

## Decision

**Access is granted by a short-lived JWT access token (≤ 15 min). Sessions are represented by an
opaque, rotating refresh token stored hashed in the database, delivered as an `HttpOnly`, `Secure`,
`SameSite=Lax` cookie. Authorization is permission-based, with an explicit dormitory scope.**

### Authentication

| Aspect | Decision |
|--------|----------|
| Password storage | Argon2id (`argon2-cffi`/`pwdlib`), m=64 MiB, t=3, p=4 (tuned on deploy hardware and benchmarked). |
| Password policy | Minimum 10 characters, maximum 128, blocklist of common/compromised passwords, no forced composition rules, no periodic rotation. |
| Access token | JWT, `HS256` in V1 with a 32-byte secret from the environment; claims `sub`, `role`, `permissions_hash`, `iat`, `exp`, `jti`, `typ=access`. Delivered in the `Authorization: Bearer` header by the SPA (kept in memory, not `localStorage`). |
| Refresh token | 256-bit random, base64url; stored as SHA-256 hash with `family_id`, `issued_at`, `expires_at` (30 days), `revoked_at`, `replaced_by`; delivered as `HttpOnly` cookie scoped to `/api/v1/auth`. |
| Rotation | Every refresh issues a new token and revokes the old one within the same family. Presenting an already-rotated token ⇒ **reuse detected** ⇒ revoke the entire family and force re-login. |
| Revocation | Logout revokes the family; password change/reset revokes all other families; admin suspension revokes all families immediately. Access tokens are short-lived, so revocation latency ≤ 15 min is accepted (documented, not accidental). |
| Verification | Email verification token (single-use, 24 h) moves `pending_verification → active`. |
| Throttling | Login and password-reset are rate-limited per IP **and** per account, with exponential backoff; responses are uniform to prevent account enumeration. |
| CSRF | Refresh/logout are cookie-based ⇒ require a `SameSite=Lax` cookie plus an `Origin`/`X-Requested-With` check; no cross-site POST is accepted. |

### Authorization

Three layers, all server-side, all mandatory:

1. **Authentication** — `get_current_principal()` rejects missing/invalid/expired tokens with `401`.
2. **Permission** — routes declare `require_permission("requests.review")`. A central registry maps
   permission strings → roles; the registry is the single place roles are expanded.
3. **Scope** — `Principal.scope_dormitory_ids` is applied **inside repository queries** (`WHERE
   dormitory_id = ANY(...)`), so an out-of-scope identifier yields `404`, never `403` (no existence
   leakage) and never an unfiltered list.

Authorization is denied by default: a route without an explicit auth dependency fails a CI test that
enumerates every route in the OpenAPI schema and asserts both an auth requirement and a declared
permission.

### Frontend implications

- Access token lives in memory (Pinia) and is refreshed on 401 via a single-flight interceptor.
- Route guards use permissions from the principal endpoint; the UI hides what cannot be done, but the
  server remains authoritative (ADR-0002, R7).
- Guarded routes are still tested server-side; UI guards are UX only.

## Consequences

### Positive

- Revocation is real (DB-backed refresh tokens) while request-path cost stays low (JWT, no DB hit).
- Rotating refresh tokens with reuse detection contains the damage of a stolen token.
- Permission strings decouple routes from role names; adding a role does not require touching routes.
- Scope filtering in SQL prevents accidental "fetch then filter" data leaks and keeps pagination correct.
- No external provider: no vendor cost, no outage dependency, full control of the login UX.

### Negative

- We implement security-critical code (hashing, rotation, reuse detection) ourselves — mitigated by
  well-reviewed libraries, focused tests, and an explicit threat model in F-0404.
- A DB write per login/refresh/logout; acceptable at this scale but not free.
- Access tokens cannot be revoked instantly; a ≤ 15 min window exists (accepted and documented).
- Two token mechanisms (JWT + opaque) is more moving parts than a pure session cookie.

### Neutral / Trade-offs accepted

- `HS256` rather than `RS256`: single issuer, single verifier — asymmetric keys add key management
  with no benefit until a second service verifies tokens. Documented in `Revisit Triggers`.
- Roles are coarse (3) but permissions are fine-grained; we accept the small mapping table.

### Follow-up actions

- [x] Review and mark `Accepted` before F-0102 starts.
- [x] F-0102: implement rotation + reuse detection with tests for the replay scenario.
- [ ] F-0404: threat model and ASVS L1 checklist covering this ADR.
- [ ] F-0108: email verification and the `pending_verification → active` transition (deferred; no mail transport in this slice).

## Alternatives Considered — Why Rejected

| Option | Why not chosen |
|--------|----------------|
| Opaque cookie sessions only | Every request needs a session lookup (DB/Redis); simpler in some ways, but the JWT + refresh split gives cheaper reads and a cleaner mobile/API future. Kept as fallback if we ever need instant revocation. |
| OIDC provider (Auth0/Keycloak) | Adds a network dependency, cost/complexity, and a second system to operate for three roles and ~thousands of users; SSO is not required in V1. |
| Long-lived JWT, no refresh | No revocation path at all; a stolen token stays valid for its full lifetime; unacceptable for an admin-capable system. |

## Revisit Triggers

- A second service must verify tokens → migrate to `RS256`/`EdDSA` with a JWKS endpoint (new ADR).
- Requirement for instant global revocation → add a token version/jti denylist or move to opaque
  sessions.
- Federation/SSO requirement (e.g. university identity) → OIDC integration, new ADR.

## Verification

- **Automated:** a test enumerates all routes and asserts auth + permission declarations; rotation,
  reuse-detection, and revocation scenarios each have dedicated tests; wrong-role and wrong-scope tests
  per endpoint (ADR-0004).
- **Review:** any new permission updates `AGENTS.md` Appendix B and the registry in the same PR.
- **Periodic:** secret rotation runbook exercised in F-0405.

## References

- OWASP ASVS v4 (V2 Authentication, V3 Session Management, V4 Access Control).
- OWASP *JSON Web Token Cheat Sheet*; *Session Management Cheat Sheet*.
- RFC 6749 §10.4 (refresh token rotation), RFC 9700 (OAuth 2.0 Security BCP).
