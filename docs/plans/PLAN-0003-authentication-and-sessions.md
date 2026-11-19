# PLAN-0003 — Authentication and session lifecycle

| Field | Value |
|-------|-------|
| **ID** | PLAN-0003 |
| **Feature ID** | F-0102 |
| **Spec** | [`SPEC-0003`](../specs/SPEC-0003-authentication-and-sessions.md) |
| **Status** | Implemented |
| **Owner** | Software Architect |
| **Estimate** | M |
| **Branch** | `feat/F-0102-sessions` |
| **Created** | 2026-11-19 |

---

## 1. Design Summary

`core/security.py` owns two primitives: `AccessTokenIssuer` (PyJWT HS256, 15 min, `typ=access`) and
`RefreshTokenFactory` (256-bit `secrets.token_urlsafe`, SHA-256 at rest). `AuthService` orchestrates
login, refresh rotation, reuse detection and logout; `RefreshTokenRepository` owns the SQL and the
`FOR UPDATE`-equivalent guard for SQLite (serialized writes + unique hash).

The router sets and clears the `sara_refresh` cookie and enforces an `Origin` allowlist on cookie
endpoints. `GET /auth/me` resolves a `Principal` from the bearer token and re-reads the account to
honour suspension. The SPA keeps only the access token in memory and restores the session with a
single-flight `refresh` on boot and on the first `401`.

## 2. Assumptions & Preconditions

- [x] F-0101 registration issues sessions through the same primitives.
- [x] ADR-0005 is `Accepted`.
- [x] Cookie flow is same-origin in development via the Vite `/api` proxy.

## 3. Work Breakdown

### T1 — Access token issuer

- **First failing test:** `tests/unit/test_access_tokens.py::test_round_trip_preserves_claims`, `::test_rejects_wrong_typ`, `::test_rejects_expired`.
- **Files:** `core/security.py`, `core/errors.py`.
- **Covers:** FR-2, FR-7.
- **Verify:** `pytest tests/unit/test_access_tokens.py -q`.

### T2 — Refresh token factory and hashing

- **First failing test:** `tests/unit/test_refresh_tokens.py::test_hash_is_stable_and_not_reversible`.
- **Files:** `core/security.py`.
- **Covers:** FR-3.
- **Verify:** 1000 generated tokens are unique.

### T3 — Login and uniform failure

- **First failing test:** `tests/api/test_auth_login.py::test_login_returns_token_and_cookie`, `::test_wrong_password_and_unknown_email_are_indistinguishable`.
- **Files:** `modules/auth/service.py`, `modules/auth/router.py`.
- **Covers:** FR-1, FR-2, AC-1.
- **Verify:** both failures have identical body `code`/`title`.

### T4 — Rotation and reuse detection

- **First failing test:** `tests/api/test_auth_refresh.py::test_refresh_rotates_cookie_and_revokes_old`, `::test_replay_revokes_family`.
- **Files:** `modules/users/repository.py`, `modules/auth/service.py`.
- **Covers:** FR-3, FR-4, AC-2, AC-3.
- **Verify:** old row has `revoked_at` and `replaced_by`; family is revoked after replay.

### T5 — Logout, `/me` and origin guard

- **First failing test:** `tests/api/test_auth_logout.py::test_logout_clears_cookie_and_revokes`, `tests/api/test_auth_me.py::test_me_requires_bearer`, `::test_me_returns_profile`, `tests/api/test_auth_origin.py::test_refresh_rejects_untrusted_origin`.
- **Files:** `modules/auth/router.py`, `api/deps.py`, `modules/users/schemas.py`.
- **Covers:** FR-5, FR-6, FR-8, AC-4…AC-6.
- **Verify:** `pytest tests/api -q`.

### T6 — Web login, session restore and guard

- **First failing test:** `apps/web/tests/unit/auth-store.spec.ts::test_login_stores_access_token_in_memory_only`, `::test_bootstrap_restores_session_via_refresh`.
- **Files:** `src/api/client.ts`, `src/modules/auth/stores/auth.ts`, `src/modules/auth/views/LoginView.vue`, `src/app/router.ts`.
- **Covers:** UI states in SPEC §9.
- **Verify:** `pnpm test:unit`; manual login → reload → still signed in.

### T7 — Demo accounts and operations check

- **First failing test:** N/A — operational verification.
- **Files:** `scripts/seed.py`, README.
- **Verify:** seed is idempotent; `resident@sara.local` can log in.

## 4. Test Plan

| Behavior | Unit | Integration | Contract | E2E | Notes |
|----------|:----:|:-----------:|:--------:|:---:|-------|
| JWT round-trip / bad signature | ✓ | | ✓ | | |
| Uniform invalid credentials | | | ✓ | | timing-equalized |
| Rotation + replaced_by | | ✓ | ✓ | | |
| Reuse revokes family | | ✓ | ✓ | | the key security test |
| Logout clears cookie | | | ✓ | | |
| `/me` auth + profile | | | ✓ | | negative 401 |
| Origin allowlist | | | ✓ | | |
| In-memory token only | ✓ | | | | store test |

**One thing that would prove this is broken:** replaying a rotated refresh token and still receiving a
new session.

**Negative cases required:** no token, expired token, wrong `typ`, tampered signature, missing cookie,
revoked cookie, evil origin, suspended account.

**Frontend:** Vitest store tests with a fake transport; manual cross-tab limitation documented.

## 5. Data & Migration Plan

- **Revisions:** included in `0001_initial_identity` (`refresh_token`, `user.last_login_at`).
- **Rollback:** truncate `refresh_token`; force re-login. No other data lost.
- **Seed:** one account per role; refresh tokens are never seeded.
- **Indexes:** unique `token_hash`, `family_id`, `user_id`.

## 6. Rollout & Rollback

- **Flag:** none.
- **Deploy order:** migration → API → web.
- **Rollback:** clear cookies; deploy previous API. Access tokens remain valid ≤ 15 min.
- **Monitoring:** spike in `auth.refresh.reuse_detected` means either a bug or token theft; alert in F-0405.

## 7. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation | Trigger signal |
|---|------|:----------:|:------:|------------|----------------|
| R1 | Two tabs race on refresh and trigger false reuse | M | M | single-flight in one tab; cross-tab coordination is a follow-up | support reports of random logout |
| R2 | Cookie blocked by SameSite/Secure misconfiguration | M | H | same-origin proxy in dev; documented deploy constraints | login succeeds but reload logs out |
| R3 | SQLite write contention under refresh | L | L | short transactions; Postgres in production | `database is locked` |

## 8. Definition of Done

- [x] All ACs verified.
- [x] Reuse-detection test fails if rotation is removed.
- [x] Cookie flags asserted in API tests.
- [x] Access token never persisted to `localStorage`.
- [x] Task-List updated.

## 9. Progress Log

| Date | Task | Status | Evidence / notes |
|------|------|--------|------------------|
| 2026-11-19 | T1 | done | claims + typ + expiry tests |
| 2026-11-19 | T2 | done | hash property test |
| 2026-11-19 | T3 | done | uniform 401 |
| 2026-11-19 | T4 | done | rotation + family revocation |
| 2026-11-19 | T5 | done | logout, me, origin |
| 2026-11-19 | T6 | done | store tests + browser reload |
| 2026-11-19 | T7 | done | seed idempotent |
