# SPEC-0002 — Public registration for residents

| Field | Value |
|-------|-------|
| **ID** | SPEC-0002 |
| **Feature ID** | F-0101 |
| **Title** | Public self-service registration for residents |
| **Status** | Approved |
| **Owner** | Software Architect |
| **Milestone** | M1 |
| **Plan** | [`PLAN-0002`](../plans/PLAN-0002-user-registration.md) |
| **ADRs** | [`ADR-0005`](../adr/ADR-0005-authentication-and-authorization.md), [`ADR-0012`](../adr/ADR-0012-local-and-test-database.md) |
| **Created** | 2026-11-19 |
| **Last updated** | 2026-11-19 |

---

## 1. Problem & Context

A resident who wants a bed currently has to visit the dormitory office, fill a paper form and wait for
a manager to transcribe it. There is no authoritative account, no way to check the status of a request,
and duplicate forms are common. The first step out of that process is a trustworthy account.

Registration must be public (residents are not known to the system in advance), must never let a
visitor choose an elevated role, and must produce a session immediately so the resident can continue
to the request flow without a second round-trip.

## 2. Goals & Non-Goals

**Goals**

- G1 — A visitor can create a resident account with name, email, password and optional phone.
- G2 — Email uniqueness is enforced by the database, not only by a pre-check.
- G3 — Passwords are stored only as Argon2id hashes and never logged.
- G4 — Successful registration returns an authenticated session (access token + refresh cookie).
- G5 — A newly registered account always has role `user` and status `active`.

**Non-goals**

- NG1 — Email verification: there is no mail transport in this slice. Tracked as `F-0108`; accounts are active immediately and the risk is recorded in `ADR-0005`.
- NG2 — Phone/SMS verification, social login, SSO.
- NG3 — Self-service creation of `manager` or `admin` accounts; those are provisioned by an admin (`F-0105`).
- NG4 — Rate limiting and CAPTCHA: follow-up `F-0109`, required before public deployment.

## 3. Personas & Permissions

| Persona | May do | May not do |
|---------|--------|------------|
| Visitor | Register a resident account | Choose a role, register with an existing email, read other accounts |
| User | Register (once), inspect own profile | Register as manager/admin |
| Manager / Admin | Use the same endpoint only as a resident | Elevate the created account |

New or changed permissions: none. Registration is public by design.

## 4. User Stories

- **US-1** — As a *visitor*, I want to create an account with my name, email and password, so that I can apply for accommodation online.
- **US-2** — As a *resident*, I want clear, field-level feedback when my email is already registered, so that I know to sign in instead.
- **US-3** — As a *security reviewer*, I want the role to be fixed server-side, so that a crafted request cannot create an admin.

## 5. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|:--------:|
| FR-1 | `POST /api/v1/auth/register` accepts `full_name`, `email`, `password`, optional `phone`. | M |
| FR-2 | Email is trimmed, lower-cased and validated; uniqueness is case-insensitive. | M |
| FR-3 | Password must be 10–128 characters, must not be a known-common password, and must not contain the email local-part. | M |
| FR-4 | Password is hashed with Argon2id; the plaintext never leaves the request scope and is never logged. | M |
| FR-5 | The created account has role `user` and status `active`; client-supplied role fields are ignored/rejected. | M |
| FR-6 | A duplicate email returns `409` with code `email_already_registered`, without revealing whether the password was valid. | M |
| FR-7 | Success returns `201` with the public profile and an access token, and sets the refresh cookie. | M |
| FR-8 | Validation failures return `422` problem details with field pointers (`full_name`, `email`, `password`, `phone`). | M |
| FR-9 | The public profile never includes the password hash, token hashes or internal session identifiers. | M |

## 6. Acceptance Criteria

**AC-1 (FR-1, FR-7)** — *Given* a valid unused email, *when* a visitor registers, *then* the response is
`201`, the body contains `user.id`, `user.email`, `access_token`, `token_type: "bearer"`, and the
response has an `HttpOnly` refresh cookie.

**AC-2 (FR-2, FR-6)** — *Given* `Ali@Example.com` is registered, *when* a second request uses
`ali@example.com`, *then* the response is `409` with `code = "email_already_registered"`.

**AC-3 (FR-3, FR-8)** — *Given* a 9-character password, *when* registration is attempted, *then* the
response is `422` and the problem body points at the `password` field.

**AC-4 (FR-4, FR-9)** — *Given* a successful registration, *when* the stored row and the response are
inspected, *then* the stored `password_hash` starts with `$argon2id$`, differs from the plaintext, and
appears nowhere in the response.

**AC-5 (FR-5)** — *Given* a request that includes `"role": "admin"`, *when* it is processed, *then* the
response is `422` (unknown field) and no account is created; the role can only be assigned by an
admin provisioner (`F-0105`).

## 7. Data Model Impact

- **New tables:** `user` (account), plus `refresh_token` introduced here because registration issues a session.
- **Changed tables:** none.
- **Constraints/indexes:** `uq_user_email` on `lower(email)` semantics (email stored normalized; a unique constraint on `email`), index on `user.role` for admin lists.
- **Migration strategy:** single additive migration.
- **Backfill:** none.
- **Retention:** hard delete is not exposed; accounts are deactivated (`F-0105`).

```text
user
  id             uuid  pk
  email          varchar(320) not null unique
  password_hash  varchar(255) not null
  full_name      varchar(120) not null
  phone          varchar(20)  null
  role           varchar(16)  not null default 'user'
  status         varchar(32)  not null default 'active'
  created_at     timestamptz  not null
  updated_at     timestamptz  not null
```

## 8. API Contract

| Method | Path | Permission | Success | Errors |
|--------|------|------------|---------|--------|
| `POST` | `/api/v1/auth/register` | public | `201` | `409`, `422` |

**Request schema**

```json
{
  "full_name": "string, 3–120, trimmed",
  "email": "string, RFC 5322, ≤ 320, normalized",
  "password": "string, 10–128",
  "phone": "string, optional, 7–20 digits/+/-"
}
```

**Response schema**

```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "ali@example.com",
    "full_name": "علی رضایی",
    "phone": "+989121234567",
    "role": "user",
    "status": "active",
    "created_at": "2026-11-19T09:12:00Z"
  }
}
```

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `email_already_registered` | 409 | Normalized email already exists |
| `validation_error` | 422 | Schema or password-policy failure |
| `internal_error` | 500 | Unexpected failure (no details leaked) |

**Idempotency:** none. A retried registration with the same email returns `409`; the client should
switch to login. `Idempotency-Key` is deliberately not supported because the operation creates a
security-sensitive identity.

## 9. UI / UX Notes

- **Screens/routes:** `/register` → `RegisterView` → account creation, with a link to `/login`.
- **States:** idle; submitting (button shows a spinner and is disabled); field errors; form-level error (`409` renders next to the email field with a "sign in instead" link); success (redirect to `/dashboard`).
- **Validation:** client mirrors the server (name ≥ 3, valid email, password ≥ 10, confirm password equal, terms accepted). Server `422` is mapped back to fields by `loc`.
- **RTL & i18n:** all strings in `fa-IR`/`en-US`; labels above inputs; password visibility toggle with an accessible name.
- **Accessibility:** each input has a `<label for>`, `aria-invalid`, `aria-describedby` pointing at the error; the form-level alert uses `role="alert"`; focus moves to the first invalid field on submit.
- **Dates:** none displayed.

## 10. Edge Cases & Failure Modes

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| E1 | Two concurrent registrations for the same email | One succeeds; the other receives `409` from the unique constraint, mapped to the same problem code |
| E2 | Email with surrounding whitespace or mixed case | Normalized before validation and storage |
| E3 | Password consisting only of spaces | Rejected by the length/policy check after trimming is **not** applied to passwords |
| E4 | Client sends `role`/`status` | `422` — the schema forbids unknown fields; role is always `user` |
| E5 | Unicode name | Accepted and stored as-is; length counted in code points |
| E6 | Duplicate phone | Allowed in this slice; phone is not an identifier |

## 11. Non-Functional Requirements

- **Performance:** p95 < 500 ms including Argon2id hashing; one insert plus one refresh-token insert.
- **Security:** generic error text on duplicate; no password in logs; `Cache-Control: no-store` on auth responses; rate limiting deferred to `F-0109`.
- **Observability:** `auth.registration.succeeded` / `auth.registration.rejected` structured events with `user_id` and normalized email hash — never the password or token.
- **Accessibility:** WCAG 2.1 AA on `/register`.
- **Compatibility:** responsive from 360 px; RTL and LTR.

## 12. Out of Scope & Follow-ups

- Out of scope: email verification (`F-0108`), rate limiting/CAPTCHA (`F-0109`), phone verification, terms versioning.
- Follow-ups: emit an audit-log entry when `F-0107` lands; add a welcome notification with `F-0307`.

## 13. Open Questions

| # | Question | Owner | Needed by | Resolution |
|---|----------|-------|-----------|------------|
| Q1 | Do we block registration until email is verified? | Architect | G1 | Deferred: no mail transport; accounts are active and the limitation is recorded in ADR-0005 and Task-List |

## 14. Change Log

| Date | Change | By | Re-approved |
|------|--------|----|-------------|
| 2026-11-19 | Initial approved specification | Architect | — |
