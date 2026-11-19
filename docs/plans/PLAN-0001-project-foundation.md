# PLAN-0001 — Project foundation

| Field | Value |
|-------|-------|
| **ID** | PLAN-0001 |
| **Feature ID** | F-0001, F-0002, F-0003, F-0005 |
| **Spec** | [`SPEC-0001`](../specs/SPEC-0001-project-foundation.md) |
| **Status** | Implemented |
| **Owner** | Software Architect |
| **Estimate** | M |
| **Branch** | `feat/F-0001-project-foundation` |
| **Created** | 2026-11-19 |

---

## 1. Design Summary

Create a two-application monorepo: `apps/api` (FastAPI, SQLAlchemy async, Pydantic v2) and `apps/web`
(Vue 3, TypeScript, Vite, Pinia, Vue Router, vue-i18n, Tailwind). The API is assembled by an app
factory that owns settings, the engine, the session factory and exception handlers, so tests can
build an isolated instance. Errors are RFC 9457 Problem Details produced by one module. The web shell
owns routing, i18n, a design-token CSS layer and a typed HTTP client.

SQLite (aiosqlite) is the local/test engine per `ADR-0012`; the code path is dialect-neutral and the
production target remains PostgreSQL. Tailwind plus owned primitives replace PrimeVue for this slice
per `ADR-0013`.

## 2. Assumptions & Preconditions

- [x] The handbook, templates and ADRs 0001–0006 exist.
- [x] Python 3.12 and Node 24 are available.
- [x] ADR-0012 (local/test database) is `Accepted`.
- [ ] Docker is **not** available in the current environment; Postgres verification is deferred to `F-0405`.

## 3. Work Breakdown

### T1 — Monorepo skeleton and installable packages

- **First failing test:** `apps/api/tests/unit/test_package_imports.py::test_package_exposes_version` — fails with `ModuleNotFoundError`.
- **Command:** `\.venv\Scripts\python -m pytest apps/api/tests/unit/test_package_imports.py -q`
- **Files:** `apps/api/pyproject.toml`, `apps/api/src/sara_api/__init__.py`, `apps/web/package.json`, `apps/web/index.html`.
- **Covers:** FR-5, FR-7.
- **Verify:** import succeeds; `pnpm --dir apps/web typecheck` runs.

### T2 — Settings, app factory and health endpoints

- **First failing test:** `tests/api/test_health.py::test_liveness_is_200` and `::test_readiness_checks_database`.
- **Files:** `core/config.py`, `main.py`, `modules/health/router.py`.
- **Covers:** FR-1, FR-2, AC-1.
- **Verify:** both tests pass; `/health/live` does not open a DB session.

### T3 — Problem Details error model

- **First failing test:** `tests/api/test_errors.py::test_unknown_route_returns_problem_json`, `::test_unhandled_exception_hides_traceback`.
- **Files:** `core/errors.py`, handler registration in `main.py`.
- **Covers:** FR-3, FR-4, AC-2.
- **Verify:** media type is `application/problem+json`; body has six members.

### T4 — Database session, base model and naming convention

- **First failing test:** `tests/integration/test_database.py::test_session_executes_select_one`.
- **Files:** `db/base.py`, `db/session.py`, `tests/conftest.py`.
- **Covers:** FR-8, AC-5.
- **Verify:** two tests can each create the same row without interference.

### T5 — Vue shell: router, i18n, RTL, design tokens

- **First failing test:** `apps/web/tests/unit/router.spec.ts::test_unknown_route_resolves_to_not_found`.
- **Files:** `src/main.ts`, `src/App.vue`, `src/app/router.ts`, `src/app/i18n.ts`, `src/styles/main.css`, `src/shared/views/NotFoundView.vue`.
- **Covers:** FR-6, FR-7, AC-4.
- **Verify:** `pnpm test:unit` and `pnpm typecheck`.

### T6 — Reproducible commands and documentation

- **First failing test:** N/A — documentation-only task, exempt per `AGENTS.md` R3.
- **Files:** `Makefile`, `scripts/*.ps1`, `README.md`, `.env.example`.
- **Covers:** G1.
- **Verify:** commands in README executed on this machine.

## 4. Test Plan

| Behavior | Unit | Integration | Contract | E2E | Notes |
|----------|:----:|:-----------:|:--------:|:---:|-------|
| Liveness independent of DB | | | ✓ | | |
| Readiness fails when DB down | | ✓ | ✓ | | |
| Problem Details on 404/500 | ✓ | | ✓ | | |
| Test DB isolation | | ✓ | | | |
| RTL shell + not-found route | ✓ | | | | Vitest + happy-dom |

**One thing that would prove this is broken:** readiness returning `200` with an unreachable database.

**Negative cases required:** malformed URL, unknown route, exception in a route, DB failure.

**Frontend:** router and i18n unit tests; no Playwright in this slice (no browser binary budget).

## 5. Data & Migration Plan

- **Revisions:** baseline created after the auth tables (T1 of PLAN-0002/0003) so one revision covers the initial schema.
- **Rollback of data:** N/A — additive only.
- **Seed data:** `scripts/seed.py` creates one account per role; idempotent by email.
- **Index checks:** health probe is `SELECT 1`; list queries are covered in later plans.

## 6. Rollout & Rollback

- **Flag:** none; this is the initial skeleton.
- **Deploy order:** migrate → API → web.
- **Rollback:** revert the commit; no data exists yet beyond the seed.
- **Monitoring:** startup log line with environment and dialect; `/health/ready` in the smoke test.

## 7. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation | Trigger signal |
|---|------|:----------:|:------:|------------|----------------|
| R1 | SQLite accepts SQL that Postgres rejects | M | M | portable types, no SQLite-only SQL, CI Postgres job in F-0405 | migration/dialect errors at deploy |
| R2 | Layer boundaries erode as modules are added | M | H | directories enforce the shape; review checklist; import-linter in F-0405 | router importing ORM in review |
| R3 | Dev-only secret reaches production | L | H | startup validation refuses default secret when `ENV=production` | boot failure in staging |

## 8. Definition of Done

- [x] All ACs verified.
- [x] `pytest` and `vitest` green.
- [x] `vue-tsc --noEmit` clean.
- [x] RTL and Persian verified in the browser.
- [x] README commands executed.
- [x] Task-List updated.

## 9. Progress Log

| Date | Task | Status | Evidence / notes |
|------|------|--------|------------------|
| 2026-11-19 | T1 | done | packages import; `sara_api.__version__ == "0.1.0"` |
| 2026-11-19 | T2 | done | health tests pass |
| 2026-11-19 | T3 | done | problem+json asserted |
| 2026-11-19 | T4 | done | isolated SQLite per test |
| 2026-11-19 | T5 | done | Vitest router/i18n pass |
| 2026-11-19 | T6 | done | commands documented in README |
