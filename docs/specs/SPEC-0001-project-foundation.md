# SPEC-0001 — Project Foundation: runnable API, web shell and test harness

| Field | Value |
|-------|-------|
| **ID** | SPEC-0001 |
| **Feature ID** | F-0001, F-0002, F-0003, F-0005 |
| **Title** | Runnable monorepo foundation with a tested API and web shell |
| **Status** | Approved |
| **Owner** | Software Architect |
| **Milestone** | M0 |
| **Plan** | [`PLAN-0001`](../plans/PLAN-0001-project-foundation.md) |
| **ADRs** | [`ADR-0002`](../adr/ADR-0002-backend-modular-monolith.md), [`ADR-0003`](../adr/ADR-0003-frontend-vue-typescript-spa.md), [`ADR-0012`](../adr/ADR-0012-local-and-test-database.md) |
| **Created** | 2026-11-19 |
| **Last updated** | 2026-11-19 |

---

## 1. Problem & Context

The repository currently contains the engineering handbook, the backlog and the decision records, but
no executable code. A contributor cannot clone the project and see anything run. Every later feature
(F-0101 onward) needs a stable place to put a router, a service, a migration, a Vue view, and a test —
and needs those conventions to be enforced before there are ten of them.

This SPEC establishes the smallest foundation that makes the *first vertical slice* possible:

- a FastAPI application with settings, error handling, health checks and a database session;
- a Vue 3 + TypeScript application with routing, state, i18n and a design system;
- test harnesses on both sides that run without a container runtime.

## 2. Goals & Non-Goals

**Goals**

- G1 — A clean checkout can install, configure, migrate, run and test both applications with documented commands.
- G2 — The backend layering (`api → services → domain ← repositories`) exists as real directories and is respected by the first feature.
- G3 — Errors are RFC 9457 Problem Details with stable machine-readable codes.
- G4 — Health endpoints distinguish liveness from readiness (database reachable).
- G5 — The web app boots in Persian, RTL, with a tested router/store foundation and a shared design-token CSS layer.
- G6 — Test commands produce a deterministic result on Windows without Docker.

**Non-goals**

- NG1 — CI pipeline provisioning (GitHub Actions is a follow-up; the local `make`-equivalent commands are delivered here).
- NG2 — Production deployment, containers and observability backends (`F-0405`).
- NG3 — A complete component library; only primitives used by the auth slice are built (`ADR-0013`).
- NG4 — Postgres-specific migrations and `alembic check` wiring; the local strategy is recorded in `ADR-0012`.

## 3. Personas & Permissions

| Persona | May do | May not do |
|---------|--------|------------|
| Contributor | Run, test and extend the foundation | Merge without the gates in `AGENTS.md` |
| All application users | Reach `/health/live`, `/health/ready` and the public auth screens | Access any data endpoint without authentication |

New or changed permissions: none.

## 4. User Stories

- **US-1** — As a *contributor*, I want `git clone` → `install` → `test` to work with the documented commands, so that I can start a feature without tribal knowledge.
- **US-2** — As an *operator*, I want liveness and readiness to be separate, so that a database outage does not cause a restart loop.
- **US-3** — As a *resident*, I want the first page to load in Persian and right-to-left, so that the product feels native.

## 5. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|:--------:|
| FR-1 | `GET /health/live` returns `200` with `{"status":"ok"}` and does not touch the database. | M |
| FR-2 | `GET /health/ready` returns `200` only when a trivial `SELECT 1` succeeds; otherwise `503` with a problem document. | M |
| FR-3 | Every error response uses `application/problem+json` and includes `type`, `title`, `status`, `code`, `detail`, `instance`. | M |
| FR-4 | Unhandled exceptions never leak stack traces or internal identifiers to clients; they are logged with a request id. | M |
| FR-5 | The API exposes `/api/v1` and an OpenAPI document at `/api/openapi.json`. | M |
| FR-6 | The web app boots at `/`, sets `dir="rtl"` and `lang="fa-IR"`, and renders a not-found route without crashing. | M |
| FR-7 | The web build passes `vue-tsc --noEmit` and the unit test command runs at least one meaningful test. | M |
| FR-8 | The backend test harness isolates each test's database and freezes the clock where time matters. | M |

## 6. Acceptance Criteria

**AC-1 (FR-1, FR-2)** — *Given* the API is running with a reachable database, *when* a client calls
`/health/live` and `/health/ready`, *then* both return `200`; *given* the database is unreachable,
*when* `/health/ready` is called, *then* it returns `503` and `/health/live` still returns `200`.

**AC-2 (FR-3, FR-4)** — *Given* a request that triggers a domain error or an unexpected exception,
*when* the response is inspected, *then* the media type is `application/problem+json`, the body has the
six required members, and no traceback is present.

**AC-3 (FR-5)** — *Given* the app is created, *when* `/api/openapi.json` is fetched, *then* the paths
include `/health/live`, `/health/ready` and the auth endpoints, and `info.title` is `SARA API`.

**AC-4 (FR-6, FR-7)** — *Given* a production build, *when* it is served, *then* the document is RTL and
Persian, unknown routes render the not-found view, and `vue-tsc --noEmit` exits `0`.

**AC-5 (FR-8)** — *Given* two tests that create the same email, *when* the suite runs in any order,
*then* each starts from an empty database.

## 7. Data Model Impact

- **New tables:** none in this feature; the baseline `user` and `refresh_token` tables are introduced by SPEC-0002/0003 using the same conventions.
- **Constraints/indexes:** naming convention applied on `MetaData` so every constraint has a deterministic name.
- **Migration strategy:** baseline revision created after the auth models exist; schema creation in tests uses SQLAlchemy metadata against SQLite.
- **Backfill:** none.
- **Retention:** not applicable yet.

## 8. API Contract

| Method | Path | Permission | Success | Errors |
|--------|------|------------|---------|--------|
| `GET` | `/health/live` | public | `200` | — |
| `GET` | `/health/ready` | public | `200` | `503` |
| `GET` | `/api/openapi.json` | public | `200` | — |

**Readiness schema**

```json
{ "status": "ok", "database": "ok", "version": "0.1.0" }
```

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `internal_error` | 500 | Unhandled exception |
| `not_ready` | 503 | Database probe failed |
| `not_found` | 404 | Unknown route |

## 9. UI / UX Notes

- **Routes:** `/` (landing, redirects to the auth flow when unauthenticated), `/login`, `/register`, `/dashboard`, `/:pathMatch(.*)*` (not found).
- **States:** the shell renders a full-page splash while the session is restored; route-level errors render the not-found or error view.
- **Validation:** not applicable in this feature.
- **RTL & i18n:** `fa-IR` default, `en-US` present as a fallback catalog; logical CSS properties only.
- **Accessibility:** skip link to main content, visible focus ring, `lang` and `dir` set on `<html>`.
- **Dates:** none in this feature.

## 10. Edge Cases & Failure Modes

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| E1 | Database down at boot | Process starts; `/health/live` is `200`; `/health/ready` is `503` |
| E2 | Unknown route | `404` problem document for API; not-found view for the SPA |
| E3 | Missing `SECRET_KEY` in production | Application refuses to start with a clear message |
| E4 | Client sends an unexpected `Accept` | JSON problem document is still returned |

## 11. Non-Functional Requirements

- **Performance:** health endpoints p95 < 50 ms locally; no external calls.
- **Security:** no stack traces in responses; CORS allowlist per environment; security headers set by the app in development.
- **Observability:** request id generated/propagated in `X-Request-ID`; startup logs the environment and database dialect (never the URL with credentials).
- **Accessibility:** WCAG 2.1 AA for the shell; skip link, focus states, semantic landmarks.
- **Compatibility:** Node 24, Python 3.12, last two versions of major browsers.

## 12. Out of Scope & Follow-ups

- Out of scope: Docker Compose/Postgres (`F-0004`, blocked by the absence of a container runtime in the current environment), CI pipeline (`F-0001` follow-up), Prometheus metrics (`F-0405`).
- Follow-ups: add GitHub Actions and `alembic check` when the repository is connected to CI.

## 13. Open Questions

| # | Question | Owner | Needed by | Resolution |
|---|----------|-------|-----------|------------|
| Q1 | Which database runs locally when Docker is unavailable? | Architect | G2 | Resolved by ADR-0012: SQLite for local/test, Postgres remains the production target |

## 14. Change Log

| Date | Change | By | Re-approved |
|------|--------|----|-------------|
| 2026-11-19 | Initial approved specification | Architect | — |
