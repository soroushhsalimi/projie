# PLAN-0002 — Public registration for residents

| Field | Value |
|-------|-------|
| **ID** | PLAN-0002 |
| **Feature ID** | F-0101 |
| **Spec** | [`SPEC-0002`](../specs/SPEC-0002-user-registration.md) |
| **Status** | Implemented |
| **Owner** | Software Architect |
| **Estimate** | M |
| **Branch** | `feat/F-0101-registration` |
| **Created** | 2026-11-19 |

---

## 1. Design Summary

Registration is a vertical slice: a pure password/email policy in `domain/accounts.py`, an Argon2id
hasher and token issuer in `core/security.py`, a `UserRepository` and `RefreshTokenRepository` in
`modules/users/repository.py`, an `AuthService.register` use case, and
`POST /api/v1/auth/register` in `modules/auth/router.py`.

The service owns the transaction and issues a session through the shared `SessionIssuer`, so
registration and login cannot drift. The API schema forbids unknown fields, which makes a
client-supplied `role` a validation error rather than a silent privilege decision.

## 2. Assumptions & Preconditions

- [x] F-0002 (API skeleton) and F-0005 (database baseline) are Done.
- [x] ADR-0005 is `Accepted`; refresh cookie contract is fixed.
- [x] No mail transport exists → email verification is explicitly deferred (`F-0108`).

## 3. Work Breakdown

### T1 — Domain email and password policy

- **First failing test:** `tests/unit/test_password_policy.py::test_rejects_short_password`, `::test_rejects_email_local_part`, `::test_accepts_long_passphrase`.
- **Files:** `src/sara_api/domain/accounts.py`, `src/sara_api/domain/errors.py`.
- **Covers:** FR-2, FR-3.
- **Verify:** `pytest tests/unit/test_password_policy.py -q`.

### T2 — User model, repository and unique email

- **First failing test:** `tests/integration/test_user_repository.py::test_duplicate_email_raises_conflict`.
- **Files:** `modules/users/models.py`, `modules/users/repository.py`.
- **Covers:** FR-2, FR-6, E1.
- **Verify:** integration test passes against SQLite.

### T3 — Registration use case

- **First failing test:** `tests/integration/test_auth_service_register.py::test_register_hashes_password_and_issues_session`.
- **Files:** `modules/auth/service.py`, `core/security.py`.
- **Covers:** FR-4, FR-5, FR-7.
- **Verify:** hash starts with `$argon2id$`; refresh row exists.

### T4 — HTTP contract

- **First failing test:** `tests/api/test_auth_register.py::test_register_returns_201_and_cookie`, `::test_duplicate_email_returns_409_problem`, `::test_short_password_returns_422`.
- **Files:** `modules/auth/schemas.py`, `modules/auth/router.py`, `main.py`.
- **Covers:** FR-1, FR-6, FR-7, FR-8, AC-1…AC-5.
- **Verify:** `pytest tests/api/test_auth_register.py -q`.

### T5 — Web registration screen

- **First failing test:** `apps/web/tests/unit/register-validation.spec.ts::test_password_confirmation_must_match`.
- **Files:** `src/modules/auth/views/RegisterView.vue`, `src/modules/auth/components/*`, `src/modules/auth/stores/auth.ts`, `src/modules/auth/api.ts`.
- **Covers:** UI states in SPEC §9.
- **Verify:** `pnpm test:unit` and manual browser check at 360 px and desktop.

### T6 — Seeded demo account and manual journey

- **First failing test:** N/A — operational verification.
- **Files:** `scripts/seed.py`, README.
- **Verify:** register in the browser, refresh the page, session survives; duplicate email shows the inline error.

## 4. Test Plan

| Behavior | Unit | Integration | Contract | E2E | Notes |
|----------|:----:|:-----------:|:--------:|:---:|-------|
| Password policy | ✓ | | ✓ | | table-driven |
| Email normalization | ✓ | | ✓ | | case/space |
| Unique email | | ✓ | ✓ | | DB constraint |
| Hash never returned | | ✓ | ✓ | | response body scan |
| Cookie set | | | ✓ | | `HttpOnly`, `Path` |
| Client role rejected | | | ✓ | | extra field |

**One thing that would prove this is broken:** a response that contains `password_hash`, or two users
with `Ali@x.com` and `ali@x.com`.

**Negative cases required:** duplicate email, short password, password containing the email local part,
missing name, 129-character password, concurrent duplicate insert.

**Frontend:** password confirmation, strength meter, server 409 mapping; no Playwright in this slice.

## 5. Data & Migration Plan

- **Revisions:** `0001_initial_identity` — creates `user` and `refresh_token`.
- **Rollback:** drop the two tables (no production data in this slice).
- **Seed:** `resident@sara.local` / `Resident12345!` (documented demo credentials, never in production).
- **Indexes:** `uq_user_email`, `ix_refresh_token_family`, `ix_refresh_token_user`.

## 6. Rollout & Rollback

- **Flag:** none.
- **Deploy order:** migration → API → web.
- **Rollback:** disable the `/register` route at the edge; existing sessions remain valid.
- **Monitoring:** `auth.registration.rejected` rate by `code`.

## 7. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation | Trigger signal |
|---|------|:----------:|:------:|------------|----------------|
| R1 | Account enumeration through `409` | H | M | accepted for registration UX; login stays uniform; rate limit in F-0109 | scraping pattern |
| R2 | Argon2 parameters too heavy for the host | M | M | benchmark; parameters configurable | p95 > 1 s |
| R3 | Unicode normalization mismatch in emails | L | L | lower-case + trim only; document | duplicate lookalike accounts |

## 8. Definition of Done

- [x] All ACs verified.
- [x] Negative tests present.
- [x] i18n keys in `fa-IR` and `en-US`; RTL verified.
- [x] Password hash never serialized.
- [x] Task-List updated.

## 9. Progress Log

| Date | Task | Status | Evidence / notes |
|------|------|--------|------------------|
| 2026-11-19 | T1 | done | 8 policy tests pass |
| 2026-11-19 | T2 | done | duplicate insert mapped to 409 |
| 2026-11-19 | T3 | done | Argon2id hash asserted |
| 2026-11-19 | T4 | done | 201 + cookie + problem codes |
| 2026-11-19 | T5 | done | register form renders and validates |
| 2026-11-19 | T6 | done | browser journey verified |
| 2026-11-25 | T7 | done | SPEC-0002 v1.1.0: required national ID, mobile and address. Domain normalizers unit-tested; contract covers missing/invalid/duplicate fields; migration `d5c8a1e93f42` is additive and nullable for legacy rows |
