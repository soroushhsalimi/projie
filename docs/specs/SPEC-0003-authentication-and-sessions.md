# SPEC-0003 — Authentication and session lifecycle

| Field | Value |
|-------|-------|
| **ID** | SPEC-0003 |
| **Feature ID** | F-0102 |
| **Title** | Login, refresh-token rotation, logout and current principal |
| **Status** | Approved |
| **Owner** | Software Architect |
| **Milestone** | M1 |
| **Plan** | [`PLAN-0003`](../plans/PLAN-0003-authentication-and-sessions.md) |
| **ADRs** | [`ADR-0005`](../adr/ADR-0005-authentication-and-authorization.md) |
| **Created** | 2026-11-19 |
| **Last updated** | 2026-11-19 |

---

## 1. Problem & Context

After registration, a resident needs to return on another day and continue from where they stopped.
Managers and admins need the same, with a session that can be revoked when an account is suspended.
The SPA must survive a page reload without keeping a long-lived credential in `localStorage`, and a
stolen refresh token must have a bounded lifetime and be detectable when replayed.

This SPEC implements the session mechanism defined in `ADR-0005`: a short-lived JWT access token and a
rotating, database-backed, `HttpOnly` refresh cookie.

## 2. Goals & Non-Goals

**Goals**

- G1 — A registered active user can sign in with email and password and receive a session.
- G2 — Access tokens are short-lived (15 min) and verified without a database round-trip.
- G3 — Refresh tokens rotate on every use; replay of an old token revokes the whole family.
- G4 — Logout revokes the family and clears the cookie.
- G5 — `GET /auth/me` returns the authenticated principal's public profile.
- G6 — Invalid, expired and revoked credentials return uniform `401` problem responses.

**Non-goals**

- NG1 — Password reset (`F-0103`), email verification (`F-0108`), MFA.
- NG2 — Instant access-token revocation; the ≤ 15 min window is accepted in ADR-0005.
- NG3 — "Log out other devices" UI (`F-0106`), admin suspension hooks (`F-0105`).
- NG4 — Distributed rate limiting; a follow-up (`F-0109`).

## 3. Personas & Permissions

| Persona | May do | May not do |
|---------|--------|------------|
| Visitor | Call login; receives a uniform `401` on bad credentials | Learn whether an email exists |
| User / Manager / Admin | Log in, refresh, log out, read own profile | Read another user's profile, escalate role via token claims |
| Suspended user | — | Log in (reserved for F-0105; status is checked at login) |

New or changed permissions: `profile.read` (own) is enforced by `GET /auth/me`.

## 4. User Stories

- **US-1** — As a *resident*, I want to sign in and stay signed in across a page reload, so that I do not re-enter my password constantly.
- **US-2** — As a *security reviewer*, I want a replayed refresh token to invalidate the session family, so that theft has a bounded blast radius.
- **US-3** — As a *signed-in user*, I want logout to immediately invalidate my refresh token, so that a shared computer is safe.

## 5. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|:--------:|
| FR-1 | `POST /api/v1/auth/login` accepts `email` and `password`; unknown email and wrong password return the same `401 invalid_credentials`. | M |
| FR-2 | On success, return a JWT access token (≤ 15 min, `sub`, `role`, `iat`, `exp`, `jti`, `typ=access`) and set a rotating refresh cookie (`HttpOnly`, `SameSite=Lax`, `Path=/api/v1/auth`, 30 days). | M |
| FR-3 | `POST /api/v1/auth/refresh` reads the cookie, validates the stored hash, rotates the token (old row revoked with `replaced_by`), and returns a new access token. | M |
| FR-4 | Presenting an already-revoked refresh token returns `401` and revokes every token in its family. | M |
| FR-5 | `POST /api/v1/auth/logout` revokes the family and clears the cookie; it returns `204` even for an unknown token. | M |
| FR-6 | `GET /api/v1/auth/me` requires a valid access token and returns the public profile; a suspended/deactivated account is rejected. | M |
| FR-7 | Access tokens with a bad signature, wrong `typ`, expired `exp`, or missing `sub` return `401`. | M |
| FR-8 | Refresh and logout reject a request whose `Origin` is present and not in the CORS allowlist (`403`). | M |
| FR-9 | A successful login updates `last_login_at` and emits an `auth.login.succeeded` event; failures emit `auth.login.failed` without the password. | S |

## 6. Acceptance Criteria

**AC-1 (FR-1)** — *Given* an active account, *when* login is called with the correct password, *then*
the response is `200` with `access_token`; *when* the email is unknown or the password is wrong, *then*
both return `401` with the same `code` and `title`.

**AC-2 (FR-2, FR-3)** — *Given* a login, *when* refresh is called with the cookie, *then* the response is
`200`, a new refresh cookie is set, the old token row has `revoked_at` and `replaced_by`, and the new
token hash differs.

**AC-3 (FR-4)** — *Given* a rotated token, *when* the old cookie is replayed, *then* the response is
`401`, and the *new* token is also revoked afterwards (family revocation).

**AC-4 (FR-5)** — *Given* a valid session, *when* logout is called, *then* the response is `204`, the
cookie is cleared, and a subsequent refresh with the old cookie returns `401`.

**AC-5 (FR-6, FR-7)** — *Given* no `Authorization` header, *when* `/auth/me` is called, *then* `401`;
*given* a token signed with another secret or with `typ=refresh`, *then* `401`; *given* a valid token,
*then* `200` with the profile and no password hash.

**AC-6 (FR-8)** — *Given* `Origin: https://evil.example`, *when* refresh is called, *then* `403` and no
token is rotated.

## 7. Data Model Impact

- **New tables:** `refresh_token` (session family).
- **Changed tables:** `user.last_login_at` (nullable timestamptz) added here.
- **Constraints/indexes:** `uq_refresh_token_hash` (unique), `ix_refresh_token_family` for family revocation, `ix_refresh_token_user` for "active sessions".
- **Migration strategy:** single additive migration.
- **Backfill:** none.
- **Retention:** revoked/expired refresh rows are retained for 30 days for reuse detection, then purgeable by a job (`F-0405`).

```text
refresh_token
  id           uuid  pk
  user_id      uuid  not null  fk → user.id on delete cascade
  token_hash   char(64) not null unique
  family_id    uuid  not null
  issued_at    timestamptz not null
  expires_at   timestamptz not null
  revoked_at   timestamptz null
  replaced_by  uuid null
  user_agent   varchar(300) null
  ip           varchar(64) null
```

## 8. API Contract

| Method | Path | Permission | Success | Errors |
|--------|------|------------|---------|--------|
| `POST` | `/api/v1/auth/login` | public | `200` | `401`, `422`, `429` (future) |
| `POST` | `/api/v1/auth/refresh` | refresh cookie | `200` | `401`, `403` |
| `POST` | `/api/v1/auth/logout` | refresh cookie | `204` | `403` |
| `GET` | `/api/v1/auth/me` | `profile.read` | `200` | `401` |

**Login request**

```json
{ "email": "ali@example.com", "password": "correct horse battery staple" }
```

**Token response** — same envelope as registration (`access_token`, `token_type`, `expires_in`, `user`).

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `invalid_credentials` | 401 | Unknown email or wrong password |
| `invalid_token` | 401 | Missing/malformed/expired access token |
| `invalid_session` | 401 | Missing, expired or revoked refresh token |
| `origin_not_allowed` | 403 | Untrusted `Origin` on a cookie endpoint |
| `validation_error` | 422 | Malformed credentials payload |

**Idempotency:** refresh is deliberately **not** idempotent (rotation is the security property);
clients must serialize refresh calls (single-flight in the SPA).

## 9. UI / UX Notes

- **Screens/routes:** `/login` → `LoginView`; global 401 handling in the API client; `/dashboard` is the post-login landing.
- **States:** idle; submitting; invalid credentials (form-level alert, focus to password); session-expired notice after a failed silent refresh; offline/network error with retry.
- **Validation:** email format and non-empty password client-side; server errors mapped by `code`, not by string matching.
- **RTL & i18n:** "مرا به خاطر بسپار" is a 30-day cookie decision (default on); all strings translated.
- **Accessibility:** `role="alert"` for credential errors, not for field hints; password visibility toggle with `aria-pressed`; Enter submits.
- **Dates:** none displayed.

## 10. Edge Cases & Failure Modes

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| E1 | Two tabs refresh concurrently with the same cookie | One succeeds; the other detects reuse and revokes the family — the SPA serializes refresh across tabs via `BroadcastChannel`/single-flight (documented limitation in this slice: a second tab may be logged out) |
| E2 | Access token expires mid-session | API client refreshes once and retries the original request once |
| E3 | Refresh cookie missing | `401 invalid_session`, no rotation |
| E4 | Tampered JWT | `401 invalid_token`, no DB write |
| E5 | Logout without a cookie | `204` (no information leak) |
| E6 | Account suspended between login and refresh | Refresh fails with `401`; access token expires within 15 min |
| E7 | Clock skew | `exp`/`iat` validated with a small leeway (60 s) |

## 11. Non-Functional Requirements

- **Performance:** login p95 < 500 ms (hash verification); refresh p95 < 150 ms; `/me` p95 < 100 ms.
- **Security:** Argon2id; refresh tokens 256-bit random, stored SHA-256; no tokens in logs or URLs; `Cache-Control: no-store`; cookie `Secure` outside local.
- **Observability:** structured events for login success/failure, refresh, reuse detection, logout; `request_id` on every line; no PII beyond user id.
- **Accessibility:** WCAG 2.1 AA on `/login`.
- **Compatibility:** cookie flow requires same-site deployment or a configured API origin; documented in README.

## 12. Out of Scope & Follow-ups

- Out of scope: password reset (`F-0103`), MFA, device management (`F-0106`), rate limiting (`F-0109`), audit log table (`F-0107`).
- Follow-ups: add a `token_version` claim for instant revocation if the product requires it; multi-tab refresh coordination.

## 13. Open Questions

| # | Question | Owner | Needed by | Resolution |
|---|----------|-------|-----------|------------|
| Q1 | Should refresh tokens be bound to a device fingerprint? | Architect | G3 | Deferred; user-agent and IP are stored for forensics only, not used as a hard binding |

## 14. Change Log

| Date | Change | By | Re-approved |
|------|--------|----|-------------|
| 2026-11-19 | Initial approved specification | Architect | — |
