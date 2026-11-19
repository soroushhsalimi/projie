# AGENTS.md — Engineering Handbook for Project SARA

> **Product:** SARA (سرا) — Self-Governed Dormitory Management System
> **Document type:** Living engineering handbook & contributor contract
> **Version:** 1.0.0 · **Status:** Active · **Last updated:** 2026-11-19
> **Owner:** Software Architect · **Applies to:** every human contributor and every AI agent working in this repository

---

## 0. How To Use This Document

This file is the **single source of truth for how we build software in this repository**. It is not
suggestive guidance — it is a contract. If code, tests, or process contradict this file, the process
in this file wins, and the discrepancy must be fixed in the same pull request.

**Mandatory reading order before touching anything** (human or AI):

1. `AGENTS.md` ← you are here
2. `Task-List.md` ← the only authoritative status of features
3. `docs/specs/SPEC-XXXX-*.md` ← *what* we are building (the "what" and "why")
4. `docs/plans/PLAN-XXXX-*.md` ← *how* we are building it (the "how", ordered)
5. `docs/adr/ADR-XXXX-*.md` ← *why* the architecture is the way it is
6. The source code you are about to change

**If any of steps 2–5 is missing for the feature you are asked to implement, you are not allowed to
write production code.** Your first deliverable is the missing document. This is not bureaucracy; it
is the mechanism that keeps a multi-month project coherent.

### 0.1 The five absolute rules (summary only — details follow)

| # | Rule |
|---|------|
| **R1** | No feature without an approved `SPEC`. |
| **R2** | No specification without an approved `PLAN`. |
| **R3** | No production code without a failing test written first. |
| **R4** | No architectural decision without an `ADR`. |
| **R5** | No merge with red CI, failing checks, or an out-of-date `Task-List.md`. |

---

## 1. Product Overview

### 1.1 What we are building

SARA is a web platform for **self-governed dormitories** (خوابگاه خودگردان) — residential facilities
that are run by a community, a cooperative, or a private owner rather than by a university housing
office. These facilities typically manage everything on paper: occupancy ledgers, handwritten
requests, phone-based approvals, and spreadsheet accounting. Result: lost requests, double-booked
beds, no audit trail, and slow administrative work.

SARA digitizes the operational core:

- a **catalog** of dormitories, buildings, rooms, beds, and their live availability;
- a **request workflow** through which residents apply for accommodation and managers decide;
- an **allocation & residency lifecycle** that guarantees a bed is never assigned twice;
- **administration** of accounts, roles, and oversight of system activity.

### 1.2 Personas and scope of authority

| Role | Persian | Responsibilities | Never allowed to |
|------|---------|------------------|------------------|
| **Admin** | ادمین | System-wide administration: user accounts, role assignment, system settings, audit oversight, monitoring. | Read/modify residents' personal residency records for their own benefit; approve their own requests; alter audit logs. |
| **Manager** | مدیر | Operate the dormitory: dormitory/room/bed data, capacities, occupancy, request review, check-in/check-out. Scoped to the dormitories assigned to them. | Manage global users or roles, change system settings, read audit logs. |
| **User** | کاربر | Register, sign in, browse dormitories and rooms, submit and track accommodation requests, manage own profile. | See other residents' data, review requests, mutate catalog data. |

### 1.3 Product goals (V1)

1. **Eliminate paper** for the accommodation request → approval → check-in flow.
2. **Zero double allocation**: a bed can never be actively assigned to two residents.
3. **Full traceability**: every state change on a request, allocation, or account is attributable.
4. **Operational speed**: a manager can review a request queue in seconds; a resident can apply in under 3 minutes.
5. **Trustworthy access control**: role and dormitory-scope enforcement is server-side and tested.

### 1.4 Explicit non-goals for V1 (do not implement without a new SPEC)

- Online payments, invoicing, or accounting integration.
- Native mobile applications (the web app is responsive/mobile-first).
- Real-time chat or ticketing with staff.
- Public self-service booking without an account (no "Cal.com-style" anonymous booking).
- Multi-tenant SaaS billing, white-labeling, or per-tenant custom domains.
- Third-party PMS/ERP integrations.
- SMS gateways beyond a pluggable notification port (see F-0307).

### 1.5 Non-functional requirements (baseline, refined per SPEC)

| Attribute | Target |
|-----------|--------|
| Latency | p95 < 300 ms for catalog/list reads; p95 < 500 ms for writes (local, seeded dataset of 10k beds). |
| Availability | 99.5% monthly for the API; graceful degradation of the web app. |
| Locale | Persian (`fa-IR`) first, fully RTL, Jalali calendar in UI, Gregorian in storage. |
| Accessibility | WCAG 2.1 AA on all primary flows, keyboard-navigable, visible focus states. |
| Security | OWASP ASVS Level 1 as the floor; see §11. |
| Data | All timestamps stored in UTC; PII minimized and access-audited. |
| Browser support | Last 2 versions of Chrome, Edge, Firefox, Safari; ≥ 360 px viewport. |

---

## 2. Golden Rules (Non-Negotiable)

**R1 — Spec-first.** A feature exists only after `docs/specs/SPEC-XXXX-*.md` is written, reviewed, and
marked `Approved`. Implementation of unspecified behavior is a defect, even if the code works.

**R2 — Plan-second.** Every approved SPEC gets a `docs/plans/PLAN-XXXX-*.md` that decomposes it into
ordered, test-first, independently verifiable tasks with risks and rollback. No PLAN, no code.

**R3 — Test-first, always.** Every behavior change starts with a failing automated test. "I'll add
tests after" is not permitted; a PR whose test coverage was written after the implementation is
rejected at review. Exceptions: pure documentation, formatting-only changes, dependency bumps.

**R4 — Every architectural decision is recorded.** Any choice that constrains future work — a
library, a layer boundary, a data model, an API shape, a deployment topology, a cross-cutting
convention — requires an ADR in `docs/adr/` *before* the code that depends on it is merged.

**R5 — The Task-List is the truth.** A feature's status lives in `Task-List.md` and nowhere else. A
stale Task-List is a release blocker.

**R6 — Layering is sacred.** Dependencies point inward only: `api → services → domain ← repositories`.
Routers never touch the ORM directly; services never import FastAPI; domain logic has no I/O.

**R7 — Security is server-side.** Hiding a button is UX, not authorization. Every endpoint enforces
authentication, permission, and dormitory scope on the server, and that enforcement is covered by a
negative test.

**R8 — No silent scope creep.** Touching an unrequested file, refactoring an unrelated module, or
"while I was here" cleanup requires its own task and its own SPEC/PLAN line. Bias: smallest possible
diff that satisfies the SPEC.

**R9 — Deterministic tests.** No dependency on wall-clock time, network, test execution order, or
shared mutable state. Freeze time, seed randomness, isolate the database per test.

**R10 — Migrations are immutable once merged.** You never edit an Alembic revision that exists on
`main`; you add a new one. Forward-only, no `downgrade` assumptions in production.

**R11 — Everything reproducible from a clean checkout.** A new contributor (or CI) must be able to go
from `git clone` to a running, seeded, tested system with the documented commands and no tribal
knowledge.

**R12 — Persian is a first-class language.** Every user-facing string goes through i18n. No hardcoded
Persian or English text in components, no hardcoded date formatting, no LTR-only layouts.

---

## 3. Repository Layout

```
sara/
├── AGENTS.md                     # This handbook (the contract)
├── Task-List.md                  # Feature backlog + status (single source of truth)
├── README.md                     # Quick start for humans
├── Makefile                      # Canonical task entry points (thin wrappers)
├── docker-compose.yml            # Local infrastructure (Postgres, Mailpit, optional MinIO)
├── .editorconfig
├── .gitignore
│
├── apps/
│   ├── api/                      # FastAPI backend (Python 3.12, uv)
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── migrations/           # Alembic revisions (immutable once merged)
│   │   ├── src/sara_api/
│   │   │   ├── main.py           # App factory, lifespan, middleware wiring
│   │   │   ├── core/             # Config, security primitives, errors, logging, pagination
│   │   │   ├── db/               # Engine, session, base models, mixins, seeding
│   │   │   ├── domain/           # Pure domain: entities, value objects, policies, state machines
│   │   │   ├── modules/          # Feature modules (vertical slices)
│   │   │   │   ├── auth/{router,service,repository,schemas,models}.py
│   │   │   │   ├── users/
│   │   │   │   ├── dormitories/
│   │   │   │   ├── rooms/
│   │   │   │   ├── requests/
│   │   │   │   └── allocations/
│   │   │   └── workers/          # Background jobs (ARQ)
│   │   └── tests/
│   │       ├── unit/             # Pure logic, no DB, no HTTP
│   │       ├── integration/      # DB + repositories + services
│   │       ├── api/              # HTTP contract per endpoint
│   │       ├── e2e/              # Multi-module business journeys
│   │       └── fixtures/         # Factories, frozen time, seeded catalogs
│   │
│   └── web/                      # Vue 3 SPA (TypeScript, Vite, pnpm)
│       ├── package.json
│       ├── src/
│       │   ├── main.ts
│       │   ├── app/              # Bootstrap, router, plugins, error boundary
│       │   ├── api/              # Generated OpenAPI types + typed fetch client
│       │   ├── modules/          # Feature slices mirroring backend modules
│       │   │   ├── auth/{views,components,stores,api,types}
│       │   │   └── ...
│       │   ├── shared/           # UI kit, composables, utils, form primitives
│       │   ├── locales/          # fa-IR (default), en-US
│       │   └── assets/
│       └── tests/
│           ├── unit/             # Vitest + Vue Test Utils
│           └── e2e/              # Playwright critical journeys
│
├── docs/
│   ├── adr/                      # Architecture Decision Records (MADR)
│   ├── specs/                    # Feature specifications
│   ├── plans/                    # Implementation plans
│   └── diagrams/                 # C4 / ERD / sequence sources (Mermaid)
│
└── scripts/                      # Cross-platform helpers (PowerShell + Bash)
```

**Naming:** `SPEC-0001-project-foundation.md`, `PLAN-0001-project-foundation.md`,
`ADR-0002-backend-stack.md`. IDs are zero-padded, monotonically increasing, never reused, never
renumbered. A superseded document keeps its ID and gains a `Superseded by` header.

---

## 4. Technology Stack

Versions are pinned in lockfiles; this table states intent, not exact patch numbers.

### 4.1 Backend

| Concern | Choice | Notes |
|---------|--------|-------|
| Language | Python 3.12+ | `from __future__ import annotations` not needed; use modern typing. |
| Framework | FastAPI | Async-first, OpenAPI as a generated artifact. |
| Validation | Pydantic v2 | Separate request/response schemas from ORM models — always. |
| ORM | SQLAlchemy 2.0 (async, `AsyncSession`) | Declarative `Mapped[]` typing; no legacy `Query`. |
| Migrations | Alembic | Autogenerate is a draft, never committed unreviewed. |
| Database | PostgreSQL 16 | `citext` for emails, `uuid` PKs, `timestamptz`. |
| Auth | Argon2id password hashing; JWT access token; opaque rotating refresh token | See ADR-0005. |
| Background jobs | ARQ (Redis) | Only for notifications/exports; never for request-path work. |
| Settings | `pydantic-settings` (12-factor, `.env` locally) | Fail fast on missing/invalid config. |
| Logging | `structlog` (JSON in prod, pretty in dev) | Request ID + actor ID on every record. |
| Testing | `pytest`, `pytest-asyncio`, `httpx.AsyncClient`, `polyfactory` | See §8. |
| Quality | `ruff` (lint + format), `mypy --strict` | Both are merge gates. |
| Packaging | `uv` | `uv.lock` committed. |

### 4.2 Frontend

| Concern | Choice | Notes |
|---------|--------|-------|
| Framework | Vue 3 (Composition API, `<script setup lang="ts">`) | No Options API in new code. |
| Language | TypeScript (strict) | `noUncheckedIndexedAccess`, no `any` in committed code. |
| Build | Vite | `pnpm` workspace. |
| Routing | Vue Router 4 | Lazy-loaded routes, route-level guards. |
| State | Pinia | Stores per feature slice; no global god-store. |
| Server state | TanStack Query (Vue Query) | Caching/retry for API data; Pinia only for client state. |
| HTTP | `openapi-fetch` + types generated by `openapi-typescript` | Contract generated from the FastAPI schema. |
| Forms | `vee-validate` + `zod` | Schemas mirror backend validation rules. |
| Styling | Tailwind CSS + PrimeVue (unstyled/themed) | Design tokens in one place. |
| i18n | `vue-i18n` | Locale files only; `fa-IR` default, RTL. |
| Dates | `date-fns-jalali` + `Intl` | Jalali display, ISO/UTC transport. |
| Unit tests | Vitest + Vue Test Utils + MSW | MSW mocks the HTTP boundary, not modules. |
| E2E | Playwright | Runs against the real stack in CI. |
| Quality | ESLint (flat config) + Prettier + `vue-tsc --noEmit` | All are merge gates. |

### 4.3 Platform

Docker Compose for local infra; container images for API and web; PostgreSQL as the only stateful
service in V1. CI runs on every pull request; CD is out of scope until F-0406.

---

## 5. System Architecture

### 5.1 Style: modular monolith, vertical slices

One deployable API, one deployable SPA, one database. Internally the API is a set of **feature
modules** (`auth`, `users`, `dormitories`, `rooms`, `requests`, `allocations`, …). Each module owns
its router, service, repository, schemas, and ORM models. Modules may call another module's **service**
public interface; they may never reach into another module's repository, tables, or models.

This is deliberate: a monolith is the cheapest architecture that satisfies current scale, and the
module boundaries preserve the option to extract a service later. Extraction is allowed only with an
ADR and only when a measured constraint demands it (see ADR-0002).

### 5.2 Backend layering and the dependency rule

```
HTTP → Router (api layer) → Service (application layer) → Domain (pure) 
                                   ↓
                            Repository (persistence) → ORM → PostgreSQL
```

| Layer | May import | Must never import | Contains |
|-------|-----------|-------------------|----------|
| `api` (routers, schemas) | services, core, domain | repositories, ORM models, SQLAlchemy | HTTP concerns: status codes, auth deps, request/response mapping, pagination params |
| `application` (services) | domain, repositories, core, other modules' services | FastAPI, `Request`, `HTTPException`, Starlette | Use-case orchestration, transaction boundaries, authorization checks |
| `domain` | stdlib only (plus typing) | SQLAlchemy, FastAPI, Pydantic, `datetime.now()` | Entities, value objects, invariants, state machines, policy functions |
| `persistence` (repositories) | domain, ORM models, SQLAlchemy | FastAPI, services | Query building, mapping ORM ↔ domain, optimistic locking |
| `db` | SQLAlchemy, core | modules | Engine, session factory, base classes, mixins |

**Enforcement:** `import-linter` contracts in CI plus a review checklist. A layer violation is a
blocking review comment, not a style nit.

**Transaction policy:** the service owns the unit of work. One HTTP request = one transaction, opened
in a dependency, committed on success, rolled back on any exception. Repositories never commit.

### 5.3 Frontend layering

```
views/ (route targets) → components/ (presentational) → composables/ (reusable behavior)
        ↓
   stores (Pinia) + query hooks (TanStack) → api/ (generated client) → HTTP
```

- Views own routing, page state, and composition. They do not contain raw `fetch`.
- Components are presentational and receive props/emit events. No direct store access in leaf
  components; pass data down.
- All HTTP goes through `src/api/`. No component or store calls `fetch`/`axios` directly.
- Generated types are never hand-edited; regeneration is a build step (`pnpm gen:api`).

### 5.4 Runtime topology (local)

| Service | Port | Purpose |
|---------|------|---------|
| `api` | 8000 | FastAPI (uvicorn, `--reload`) |
| `web` | 5173 | Vite dev server, proxies `/api` → 8000 |
| `postgres` | 5432 | Primary datastore |
| `redis` | 6379 | ARQ broker (introduced in F-0307) |
| `mailpit` | 8025 (UI) / 1025 (SMTP) | Email capture in development |

### 5.5 Domain model (V1, conceptual)

```
User 1──* Session(RefreshToken)
User 1──* AccommodationRequest *──1 Dormitory
User 1──* Allocation (Residency) *──1 Bed
Dormitory 1──* Building 1──* Room 1──* Bed
AccommodationRequest 1──0..1 Allocation
Manager *──* Dormitory          (scoping: which dorms a manager operates)
User  1──* AuditLogEntry
```

Key invariants (must be enforced in the domain layer *and* by database constraints where possible):

1. A `Bed` belongs to exactly one `Room`; capacity is derived from active beds, never a free-text number.
2. At most one `Allocation` per `Bed` may be in an active or reserved state at any instant
   (partial unique index + service-level check).
3. A `User` may hold at most one active `Allocation` per dormitory (policy configurable by SPEC).
4. A request may only transition along the defined state machine (§5.6); illegal transitions raise a
   domain error, never a 500.
5. A manager may act only within the dormitories they are scoped to; this is checked in the
   application layer for every state change.

### 5.6 Request lifecycle (authoritative state machine)

```
draft ──submit──▶ submitted ──claim──▶ under_review
                     │                     │
                     │                     ├─request_info──▶ info_requested ──resubmit──▶ submitted
                     │                     ├─approve──────▶ approved ──allocate──▶ allocated
                     │                     └─reject───────▶ rejected
                     ├─withdraw──▶ withdrawn
                     └─expire (SLA)──▶ expired
allocated ──check_in──▶ checked_in ──check_out──▶ completed
allocated ──cancel──▶ cancelled
```

Terminal states: `rejected`, `withdrawn`, `expired`, `completed`, `cancelled`. Transitions are
implemented as a pure function `transition(state, action, actor) -> new_state | DomainError`, unit
tested exhaustively (every (state, action) pair, including the forbidden ones).

---

## 6. Feature Delivery Workflow (the Gates)

A feature advances only through these gates, in order. **Every gate is a PR or a review comment —
gates are never skipped "because it's small".**

| Gate | Artifact | Exit criterion | Who approves |
|------|----------|----------------|--------------|
| **G0 — Intake** | Row in `Task-List.md` | Feature has an ID, persona, priority, milestone, dependencies, and a one-paragraph intent. Status → `Ready`. | Architect |
| **G1 — Specification** | `docs/specs/SPEC-XXXX-*.md` | All required sections complete; acceptance criteria are objectively testable; open questions are resolved or explicitly deferred. Status → `Approved`. | Architect (product owner for scope) |
| **G2 — Plan** | `docs/plans/PLAN-XXXX-*.md` | Ordered task list, each task names its failing test, touched files, and verification command; risks + rollback documented. Status → `Approved`. | Architect / implementing engineer |
| **G3 — Decisions** | `docs/adr/ADR-XXXX-*.md` (only if the feature introduces a decision) | Status `Accepted`; alternatives documented; consequences named. | Architect |
| **G4 — Red** | Failing tests | Tests exist, fail for the right reason (assertion, not import error), and are committed. | Reviewed in the feature PR |
| **G5 — Green** | Implementation | All tests pass; lint, types, and coverage gates pass; SPEC acceptance criteria demonstrably met. | Reviewer (≠ author) |
| **G6 — Close** | PR merged + Task-List updated | Task-List status → `Done` with PR link; SPEC/PLAN status → `Implemented`; follow-ups filed as new Tasks. | Architect |

```
G0 ──▶ G1 ──▶ G2 ──▶ G3 ──▶ G4 ──▶ G5 ──▶ G6
 │                             ▲
 └──────── feedback loop ───────┘   (spec change ⇒ amend SPEC first, then plan)
```

**Changing an approved SPEC:** never edit silently. Either amend in place with a `## Change Log`
entry and re-approval, or (for scope changes) write a new SPEC that supersedes it. Both require an
explicit note in `Task-List.md`.

**Definition of a good feature slice:** it can be demoed end-to-end (UI → API → DB), it is
independently deployable without breaking existing behavior, and it is small enough that its PR is
reviewable in under 45 minutes (target ≤ 400 changed lines excluding tests and generated files).

---

## 7. Documentation Standards

### 7.1 Templates are mandatory

`docs/specs/_TEMPLATE.md` and `docs/plans/_TEMPLATE.md` define required sections. Sections marked
`REQUIRED` may not be deleted; if a section is genuinely inapplicable, keep it and write "N/A —
<reason>". Reviewers reject documents with empty or placeholder sections.

### 7.2 Specification (SPEC) — required content

1. **Metadata** — ID, title, owner, status, links to PLAN/ADRs, milestone.
2. **Problem & context** — who is in pain, what happens today, what breaks.
3. **Goals / non-goals** — explicit.
4. **Personas & permissions** — which roles are affected, what each may do.
5. **User stories** — `As a <role>, I want <capability>, so that <outcome>`.
6. **Functional requirements** — numbered `FR-1`, `FR-2`, … each independently testable.
7. **Acceptance criteria** — Given/When/Then, one per FR (or per behavior group).
8. **Data model impact** — new/changed tables, columns, constraints, migrations.
9. **API contract** — endpoints, methods, payloads, status codes, error codes, permissions.
10. **UI/UX notes** — screens, states (empty/loading/error), RTL/i18n, accessibility.
11. **Edge cases & failure modes** — concurrency, duplicates, partial data, timezone, permissions.
12. **Non-functional requirements** — performance, security, observability specific to this feature.
13. **Out of scope & follow-ups.**
14. **Open questions** — with owner and decision deadline. Unresolved questions block `Approved`.

### 7.3 Plan (PLAN) — required content

1. **Metadata** — ID, SPEC link, owner, status, estimated size.
2. **Design summary** — how the SPEC will be satisfied, at a glance (5–15 lines).
3. **Work breakdown** — ordered tasks, each: `[ ]`, ID (`T1`), description, the *failing test to write
   first*, files to touch, verification command. Tasks must be committable independently.
4. **Test plan** — matrix of behaviors × test levels, plus the "one thing that would prove this is
   broken" list.
5. **Data/migration plan** — expand-migrate-contract steps if schema changes.
6. **Rollout & rollback** — feature flags, deployment order, revert strategy.
7. **Risks & mitigations** — ranked, each with an owner and a trigger signal.
8. **Definition of Done checklist** — the concrete checks for *this* feature.
9. **Progress log** — append-only, dated entries as tasks complete.

### 7.4 Architecture Decision Records (ADR)

Format: MADR (Markdown Any Decision Record), stored as `docs/adr/ADR-XXXX-<slug>.md`.

**When an ADR is required** (non-exhaustive): choosing/adding a dependency of consequence; defining
a module boundary or layer; introducing a pattern (repository, UoW, CQRS-lite); any DB schema
decision with long-term cost (PK type, soft delete, tenancy, partitioning); API versioning or
breaking change strategy; auth/session model; caching strategy; background job infrastructure;
error model; date/time and locale strategy; deployment topology; testing framework choices.

**ADR lifecycle:** `Proposed → Accepted → (Superseded by ADR-YYYY) → Deprecated`. ADRs are
**immutable**: never rewrite an accepted ADR; write a new one that supersedes it and add the pointer
in both files. Every ADR must include *alternatives considered* and *consequences* (positive,
negative, neutral) — an ADR with one option is a rationalization, not a decision.

### 7.5 Traceability

The chain `Task → SPEC (FR-n) → PLAN (Tn) → test → commit → PR` must be walkable in both directions.
Commit messages and PR descriptions reference the feature ID and, where relevant, `FR-n`. A test's
name or docstring identifies the `FR-n` it protects when the mapping is not obvious.

---

## 8. Test-Driven Development Protocol

### 8.1 The cycle (per task, not per feature)

1. **Red** — write the smallest failing test that expresses the next acceptance criterion. Run it.
   Confirm it fails for the expected reason. Never write a test you have not seen fail.
2. **Green** — write the least production code that makes it pass. No speculative generality.
3. **Refactor** — improve names, remove duplication, extract seams; keep tests green after every
   micro-step. Refactoring is *not* a license to broaden scope.
4. **Commit** — a commit is a red→green→refactor unit with a Conventional Commit message.

**Triangulation rule:** do not implement a special case until you have at least two tests that
justify generalizing. Write the second test before the general solution.

### 8.2 Test levels and ownership

| Level | Scope | Speed | Allowed I/O | Examples |
|-------|-------|-------|-------------|----------|
| **Unit** (backend) | Domain entities, policies, state machine, pure functions | < 5 ms | None | `BedAllocator` rejects an occupied bed |
| **Integration** (backend) | Service + repository + real Postgres (transactional, rolled back) | < 200 ms | DB only | Approving a request creates an allocation |
| **API contract** | Router + auth + validation, via `httpx.AsyncClient` | < 100 ms | DB | `POST /requests` returns 201 with location header; 403 for wrong role |
| **E2E** (backend) | Multi-module journey | < 2 s | DB | Register → submit → approve → check-in |
| **Unit** (frontend) | Components, composables, stores, mappers | < 50 ms | None (MSW for HTTP) | Date formatting to Jalali, form validation messages |
| **E2E** (frontend) | Playwright against the running stack | < 60 s | Full stack | Resident applies; manager approves; both see correct status |

**Proportions (target, not dogma):** ~60% unit, ~25% integration/contract, ~15% E2E. Prefer the
cheapest level that genuinely covers the risk. E2E covers *journeys and wiring*, never variants.

### 8.3 Test rules

- **No mocking the database.** Integration tests run against real PostgreSQL (a disposable database or
  a transactional session per test). Mocked repositories prove nothing about SQL, constraints, or
  isolation.
- **Mock only at architectural boundaries** you own: external HTTP, SMTP, object storage, clock.
- **Factories over fixtures files.** `polyfactory` factories with overridable defaults; every test
  builds only the data it cares about.
- **Freeze time.** Inject a `Clock` port; `datetime.now()` and `new Date()` are forbidden in domain
  and business code (lint rule / review gate).
- **Deterministic IDs and ordering.** Explicit `ORDER BY` in every list query; no reliance on
  insertion order.
- **One behavior per test, obvious name.** `test_reject_request_requires_reason` — not `test_requests`.
  Naming: `test_<subject>_<condition>_<expected>`.
- **Assert on contracts, not internals.** API tests assert status + body shape; they do not assert
  that a private method was called.
- **Negative tests are mandatory** for permissions, validation, and illegal state transitions. Every
  endpoint gets at least one "wrong role / wrong scope" test.

### 8.4 Coverage gates (CI-enforced)

| Scope | Minimum |
|-------|---------|
| `domain/` (backend) | **95%** lines + branches |
| `modules/*/service.py` | **90%** |
| Backend overall | **85%** |
| Frontend `modules/*/stores`, `composables`, `utils` | **80%** |
| Frontend components | **70%** (behavioral assertions; snapshot-only tests do not count) |

Coverage is a floor, not a goal. A PR that raises coverage while lowering assertion quality will be
rejected. **New code must not lower any existing scope's coverage.**

### 8.5 Commands (also exposed via `make`)

```bash
# Backend
uv run pytest -q                          # full suite
uv run pytest -q apps/api/tests/unit      # fast loop
uv run pytest -q -k "allocation and not slow"
uv run pytest --cov=sara_api --cov-report=term-missing

# Frontend
pnpm --filter web test:unit
pnpm --filter web test:unit -- --watch
pnpm --filter web test:e2e

# Quality
uv run ruff check . && uv run ruff format --check . && uv run mypy apps/api
pnpm --filter web lint && pnpm --filter web typecheck
```

### 8.6 What "tested" means in the Definition of Done

Every FR in the SPEC has at least one automated test that fails if the FR is removed. Permission
rules have positive and negative tests. Every state-machine transition (legal and illegal) is unit
tested. If you cannot explain which test protects a line of code, that line is untested.

---

## 9. Backend Engineering Standards

### 9.1 API conventions

- Base path `/api/v1`. Breaking changes require a new version + ADR.
- **Contract-first**: the OpenAPI document is a build artifact (`make openapi`); the web client is
  generated from it. Hand-written response shapes are a defect.
- Errors use **RFC 9457 Problem Details** (`application/problem+json`) with a stable machine-readable
  `type`, a human `title`, a `detail`, and a `code` from a single registry in `core/errors.py`.
  Domain errors map to HTTP in one place — never `raise HTTPException` from a service.
- Validation errors: `422` with field pointers. Auth: `401` (unauthenticated), `403`
  (authenticated but forbidden), `404` (not found *or* not visible — do not leak existence).
- Pagination: cursor-based for feeds, `page`/`per_page` (max 100) for admin tables; response envelope
  `{ items, meta: { page, per_page, total } }`.
- Filtering/sorting: explicit whitelisted query parameters; never pass raw SQL.
- Idempotency: state-changing endpoints that could be retried accept `Idempotency-Key` (see SPEC for
  which).
- Every endpoint declares `response_model`, explicit `status_code`, `summary`, `description`, and the
  auth dependency — no implicit defaults.

### 9.2 Code conventions

- Type annotations everywhere; `mypy --strict` clean. No `Any` without a `# rationale:` comment.
- Async all the way in I/O paths; no blocking calls in `async def` (use `run_in_threadpool` where
  unavoidable).
- Dependency injection via FastAPI `Depends` for: DB session, current principal, pagination, clock,
  and services. No globals, no module-level sessions.
- Configuration via a single `Settings` object; **no `os.environ` outside `core/config.py`**.
- One public class/module responsibility per file; files over ~400 lines are a smell.
- Docstrings on public service methods state preconditions and raised domain errors.

### 9.3 Database conventions

- UUIDv7 (or ULID) primary keys, `server_default` never in app code; generated in the service layer
  or DB, consistently per ADR.
- `created_at` / `updated_at` as `timestamptz`, UTC, managed by mixins; `deleted_at` only where soft
  delete is specified — soft delete is a per-entity decision, not a default.
- Snake_case for tables/columns; singular table names (`user`, `accommodation_request`); explicit
  naming convention on `MetaData` so Alembic names constraints deterministically.
- Foreign keys with explicit `ondelete`; indexes justified in the SPEC (every FK is indexed,
  composite indexes named and documented).
- Enums stored as constrained `varchar` + `CHECK` (or native enum only with an ADR) to keep
  migrations painless.
- Money, if ever introduced, is integer minor units + currency code — never floats.
- `SELECT ... FOR UPDATE` (or a unique partial index) is mandatory where the SPEC identifies a race;
  concurrent behavior has a dedicated test.
- Query count discipline: list endpoints must not N+1. Use `selectinload`/`joinedload` deliberately
  and assert query counts in integration tests for hot paths.

### 9.4 Migrations

- One logical change per revision; descriptive slug (`add_bed_status_check_constraint`).
- `alembic check` runs in CI to detect model/migration drift.
- Destructive changes follow **expand → migrate → contract** across releases; never drop a column in
  the same release that stops writing it.
- Seed data lives in `db/seeding/` and is idempotent; it never runs automatically in production.

### 9.5 Observability hooks

Structured log fields: `request_id`, `actor_id`, `actor_role`, `route`, `status`, `duration_ms`,
`domain_event`. Business-critical transitions emit a domain event log line. No PII (national ID,
phone, address) in logs; redact at the boundary.

---

## 10. Frontend Engineering Standards

### 10.1 Structure and state

- Feature-sliced `modules/<feature>/` mirroring backend modules; cross-feature imports go through
  `shared/` or a public `index.ts` barrel — never deep-import another module's internals.
- **Server state belongs to TanStack Query**, not Pinia. Pinia holds session/auth state, UI
  preferences, and multi-step form drafts.
- Query keys are centralized per module (`queryKeys.requests.list(filters)`); invalidation is explicit
  after mutations.
- Loading, empty, and error states are designed per screen — not an afterthought spinner.

### 10.2 Components and forms

- Props/emits typed; `defineProps<...>()` / `defineEmits<...>()` only. No `any`.
- Presentational components receive data and emit intent; they never call the API.
- Form validation runs client-side with `zod` schemas that mirror the backend contract, and the server
  remains authoritative — always render server field errors (422) next to the field.
- Optimistic updates only where rollback is trivial and specified in the SPEC.

### 10.3 i18n, RTL, and dates

- Every string via `t('module.key')`; `fa-IR` is the default locale; `en-US` may be partial but must
  never crash. No concatenated sentences (use interpolation/named args).
- Layouts use logical CSS properties (`margin-inline-start`, `padding-inline-end`) — never
  `margin-left`. `dir` is set on `<html>` from the active locale.
- Numerals: Persian digits in UI where the locale demands; Latin digits in technical identifiers,
  IDs, and code-like values. One formatting helper, unit tested.
- All API dates are ISO-8601 UTC; conversion and Jalali formatting happen in `shared/datetime.ts`
  only. Timezone of the dormitory is explicit in the domain, not inferred from the browser.

### 10.4 Accessibility and performance

- Semantic HTML, labels bound to inputs, `aria-live` for async status, focus management on dialogs and
  route changes, keyboard-operable menus/tables, contrast AA.
- Route-level code splitting; no component over ~15 kB gzipped; images sized and lazy-loaded; the
  catalog list virtualizes above 200 rows.
- Lighthouse (mobile) targets on primary flows: Performance ≥ 85, Accessibility ≥ 95.

---

## 11. Security, Privacy & Authorization

### 11.1 Authentication (summary — authoritative in ADR-0005)

- Argon2id password hashing; minimum length 10, blocklist of common passwords, no composition rules.
- Access token: short-lived JWT (≤ 15 min), `HS256` with a rotated secret in V1; claims: `sub`,
  `role`, `scope`, `iat`, `exp`, `jti`.
- Refresh token: opaque 256-bit random, stored **hashed** (SHA-256) in `refresh_token` with rotation
  on use and reuse detection (revoke the whole family on reuse).
- Logout revokes the session family. Password change/reset revokes all other sessions.
- No secrets, tokens, or PII in URLs or logs.

### 11.2 Authorization

Three enforcement layers, all server-side:

1. **Authentication** — dependency rejects missing/expired credentials.
2. **Permission** — declarative `require_permission("requests.review")` on every route.
3. **Scope** — dormitory-level filtering for managers, applied in the repository query (not after
   fetching), so an out-of-scope ID yields `404`.

The permission matrix lives in Appendix B and must be updated in the same PR that introduces a new
permission.

### 11.3 Platform hardening

- CORS allowlist per environment (never `*` with credentials).
- Rate limits: login/refresh/password-reset endpoints (per IP + per account), generic write endpoints
  (per principal). 429 with `Retry-After`.
- Security headers at the edge: HSTS, `X-Content-Type-Options`, CSP (no `unsafe-inline` in prod),
  `Referrer-Policy`, frame-ancestors.
- Input validation at the schema boundary; file uploads (if any) validated by content sniffing, size,
  and extension allowlist, stored outside the webroot, served via signed URLs.
- Secrets from environment/secret manager only; `.env` is git-ignored; `.env.example` documents keys
  without values. A secret-scanner runs in CI.
- Dependency audits (`pip-audit`, `pnpm audit`) are CI gates; a critical advisory blocks release.
- PII: collect the minimum, mark sensitive columns, restrict to owner + manager-with-scope + admin
  (admin sees metadata, not content, unless the SPEC says otherwise), and log every read of sensitive
  records in `audit_log`.

### 11.4 Audit

`audit_log` is append-only: `id, actor_id, actor_role, action, entity_type, entity_id, before,
after, request_id, ip, created_at`. Writes happen inside the same transaction as the business change
(outbox-style table, flushed by a listener). No update/delete path exists in application code.

---

## 12. Observability & Operations

- **Health:** `GET /health/live` (process), `GET /health/ready` (DB reachable, migrations current).
- **Metrics:** Prometheus endpoint `/metrics` (request count/latency by route, DB pool, job failures).
- **Logs:** JSON, correlation via `X-Request-ID` (generated if absent, echoed in response).
- **Errors:** domain errors are expected and logged at `info`/`warning` with codes; unexpected
  exceptions are logged with stack traces at `error` and reported to the error tracker.
- **Backups:** nightly `pg_dump` + PITR configuration in production; a documented, *tested* restore
  procedure is part of F-0406.
- **Environments:** `local` (compose), `ci` (ephemeral), `staging`, `production`. Config differs by
  environment variables only.

---

## 13. Local Development & Commands

### 13.1 Bootstrap from a clean checkout

```bash
git clone <repo> && cd sara
cp .env.example .env                 # fill in local values (safe defaults provided)
docker compose up -d postgres mailpit
uv sync --all-groups                 # backend deps (Python 3.12)
pnpm install                         # frontend deps
make migrate                         # alembic upgrade head
make seed                            # idempotent demo data
make openapi && pnpm gen:api         # regenerate typed client
make dev                             # api :8000 + web :5173
```

Windows note: `make` targets have PowerShell equivalents in `scripts/` (`bootstrap.ps1`, `dev.ps1`,
`test.ps1`). CI uses the same commands, so drift is caught immediately.

### 13.2 Canonical tasks

| Command | Does |
|---------|------|
| `make bootstrap` | Install everything, start infra, migrate, seed |
| `make dev` | Run API + web with reload |
| `make test` | Full backend + frontend unit suites |
| `make test-unit` | Fast loop (no DB) |
| `make e2e` | Playwright against a fresh seeded stack |
| `make lint` / `make fmt` | ruff + eslint / ruff format + prettier |
| `make typecheck` | mypy strict + vue-tsc |
| `make migrate` / `make revision m="..."` | Alembic |
| `make openapi` | Export `openapi.json` |
| `make check` | Everything CI runs, locally — **run before pushing** |

---

## 14. Git, Review & CI

### 14.1 Branching and commits

- Trunk-based: short-lived branches off `main`, merged within ~2 days; feature branches longer than a
  week are a design smell.
- Branch naming: `feat/F-0102-jwt-refresh-rotation`, `fix/F-0203-room-capacity-overflow`,
  `docs/SPEC-0006-...`, `chore/...`.
- **Conventional Commits**, imperative, ≤ 72 chars subject, body explains *why*, footer references
  `Refs: F-0102`, `Closes: #123`.
- One logical change per commit; the repository builds and tests green at every commit on `main`.

### 14.2 Pull requests

- Title = Conventional Commit. Description must contain: feature ID, SPEC link, PLAN task IDs, what
  changed, how it was verified (commands + output), risks, screenshots for UI changes (both RTL and
  LTR if applicable).
- Size target ≤ 400 changed lines (excluding tests/generated). Larger → split by PLAN tasks.
- Minimum one reviewer who did not write the code. The author never merges their own PR.
- **Review checklist:** SPEC traceability, layer boundaries respected, tests genuinely test (not
  tautologies), negative cases covered, error model correct, authorization enforced, indices/migrations
  considered, i18n/a11y for UI, docs updated (Task-List, SPEC/PLAN status, ADR if needed).

### 14.3 CI gates (all blocking)

```
1. Lint + format check          (ruff, eslint, prettier)
2. Type check                   (mypy --strict, vue-tsc)
3. Backend tests + coverage     (pytest, per-scope thresholds)
4. Frontend tests + coverage    (vitest)
5. Migration drift check        (alembic check)
6. OpenAPI diff                 (breaks the build on unannounced contract changes)
7. Security scans               (pip-audit, pnpm audit, secret scan)
8. Build                        (docker images / web bundle)
9. E2E smoke                    (Playwright, seeded stack)
10. Docs check                  (links resolve; Task-List references existing files)
```

A red gate is never bypassed with "merge anyway". If a gate is wrong, fix the gate in its own PR.

---

## 15. Definition of Ready (before implementation starts)

A feature may enter implementation only when **all** are true:

- [ ] Row exists in `Task-List.md` with ID, persona, priority, milestone, dependencies.
- [ ] `SPEC-XXXX` is `Approved` and every FR has acceptance criteria.
- [ ] `PLAN-XXXX` is `Approved` with ordered test-first tasks and verification commands.
- [ ] Required ADRs are `Accepted`.
- [ ] Data model impact and migration strategy are known.
- [ ] Permission/scope matrix for the feature is written.
- [ ] No unresolved blocking open question.
- [ ] Dependencies (features it builds on) are `Done`.

## 16. Definition of Done (a feature is done only when)

- [ ] All acceptance criteria in the SPEC are demonstrably met (manual check + test evidence).
- [ ] Tests written first; all levels present per §8; coverage gates pass.
- [ ] Negative tests: wrong role, wrong scope, invalid input, illegal transition.
- [ ] `make check` passes locally and CI is green.
- [ ] No layer violations; no TODO/FIXME left without a linked Task-List entry.
- [ ] Migrations reviewed, reversible-or-documented, and drift-free; seeds updated.
- [ ] OpenAPI regenerated; web client regenerated; contract diff reviewed.
- [ ] i18n complete for new strings (both locales or explicit fallback decision), RTL verified.
- [ ] Accessibility check on new screens (keyboard + axe).
- [ ] Docs updated: Task-List → `Done` + PR link; SPEC/PLAN status; ADR if a decision emerged;
      `README`/runbook if operationally relevant.
- [ ] Observability: meaningful log lines/events for new state changes; no PII leaks.
- [ ] Reviewer approved; PR merged to `main`.

---

## 17. AI Agent Operating Instructions

This section is addressed to AI coding agents. It refines the rest of the document; where it is
silent, the general rules apply.

### 17.1 Start protocol (every task)

1. Read `AGENTS.md`, then `Task-List.md`. Identify the exact feature ID you are working on.
2. Read that feature's `SPEC`, `PLAN`, and every referenced `ADR`. If any is missing or not
   `Approved`, **stop** and produce the missing document instead of code (unless the user explicitly
   ordered implementation, in which case say what is missing and proceed only on their confirmation).
3. Restate the scope in your own words: what will change, what will **not** change, and how you will
   verify it. Keep it short.
4. Work through the PLAN's tasks in order. For each task: write the failing test, run it, implement,
   run again, then move on.
5. Before reporting completion: run `make check` (or the closest available subset) and paste the
   evidence.

### 17.2 Scope discipline

- Do exactly what the SPEC/PLAN says. Do not add "nice to have" endpoints, columns, abstractions, or
  refactors. If you believe something is missing, **report it** — do not implement it.
- Never reformat or reorganize files you were not asked to touch; it destroys reviewability.
- No new dependency without an ADR (or explicit user approval) — even a "tiny" one.
- No placeholder implementations that silently return fake data; `NotImplementedError` with a clear
  message and a linked task is acceptable, silent stubs are not.
- No `TODO` without a `F-XXXX` reference.

### 17.3 Stop conditions (ask, don't guess)

Ask the user before proceeding when:

- The SPEC is ambiguous or two requirements contradict.
- A required decision has no ADR and the choice is consequential (data model, auth, dependency).
- The task would require touching an unrelated module or a merged migration.
- Tests reveal that the approved design cannot satisfy the SPEC.
- A security or data-loss risk appears (e.g., destructive migration, PII exposure).
- The user's instruction conflicts with this handbook.

Otherwise, make the smallest reasonable decision, **record it where the process requires it** (ADR,
SPEC change log, PLAN progress log), and continue. Never ask permission for routine choices the
handbook already settles (naming, test structure, layer placement).

### 17.4 Communication contract

- Report in the user's language; keep repository artifacts (code, docs, commits) in English.
- Structure reports as: **what changed → why → evidence (commands/results) → what's next / open
  questions**. Link files, don't paste entire files.
- Never claim a test passed without running it. Never claim a UI works without verifying it.
- If you could not verify something, say so explicitly and say why.

### 17.5 Forbidden actions

- Writing production code before a failing test exists (R3).
- Editing an Alembic revision that is already on `main` (R10).
- Adding dependencies, changing the auth model, or altering module boundaries without an ADR.
- `git push --force`, rewriting published history, or committing secrets/`.env` files.
- Disabling, skipping (`@pytest.mark.skip`, `.skip`), or weakening a test to make CI green.
- Broad `ruff: noqa`, `# type: ignore` without a specific code and rationale, or `any` in committed TS.
- Touching files outside the stated scope "because they were already broken" — file a task instead.

### 17.6 Self-review before declaring done

- Does every FR in the SPEC have a test that would fail if the FR were removed?
- Do wrong-role, wrong-scope, and illegal-transition paths return the correct codes?
- Is any business logic in a router or a component? (Move it.)
- Are all new strings translated and all new dates formatted through the shared helper?
- Did I update `Task-List.md` and the SPEC/PLAN status?
- Would a reviewer be able to understand the diff without asking me questions?

---

## 18. Governance of This Document

- This handbook is versioned with the code. Significant changes require an ADR
  (`ADR-0001` establishes this practice).
- Any contributor may propose an amendment via PR modifying this file; approval by the Architect.
- When practice and handbook diverge, **fix the handbook in the same PR** — an outdated handbook is
  worse than none.
- Review this document at each milestone boundary (M0…M4) and after any incident.

---

## Appendix A — Domain Glossary

| Term | Definition |
|------|------------|
| **Dormitory** (خوابگاه) | A self-governed residential facility, the top-level unit of scope. |
| **Building** (ساختمان) | A physical block within a dormitory. |
| **Room** (اتاق) | A rentable unit inside a building, with a gender policy and amenities. |
| **Bed** (تخت) | The atomic allocatable resource. Capacity is the count of active beds. |
| **Accommodation Request** (درخواست اسکان) | A resident's application for a bed, with preferences and documents. |
| **Allocation / Residency** (اسکان) | The binding of a user to a bed for a period; the record of occupancy. |
| **Check-in / Check-out** | Physical start/end of an allocation, recorded with timestamps and actor. |
| **Waitlist** | Ordered queue of approved requests awaiting a bed. |
| **Scope** (دامنه دسترسی) | The set of dormitories a manager may operate. Enforced server-side. |
| **Principal** | The authenticated actor (user + role + scope) derived from the access token. |
| **Domain Error** | An expected business-rule violation with a stable code, mapped to an HTTP status once. |

## Appendix B — Role × Permission Matrix (V1)

| Permission | Admin | Manager | User |
|------------|:-----:|:-------:|:----:|
| `profile.read` / `profile.write` (own) | ✓ | ✓ | ✓ |
| `users.read` / `users.write` (all accounts) | ✓ | — | — |
| `roles.assign` | ✓ | — | — |
| `system.settings.read` / `write` | ✓ | — | — |
| `audit.read` | ✓ | — | — |
| `dormitories.read` | ✓ | ✓ (scoped) | ✓ (public/active only) |
| `dormitories.write` | — | ✓ (scoped) | — |
| `rooms.read` | ✓ | ✓ (scoped) | ✓ (active only) |
| `rooms.write` / `beds.write` | — | ✓ (scoped) | — |
| `requests.create` | — | — | ✓ |
| `requests.read.own` | ✓ | ✓ | ✓ |
| `requests.read.all` | ✓ (oversight, read-only) | ✓ (scoped) | — |
| `requests.review` (approve/reject) | — | ✓ (scoped) | — |
| `allocations.write` (allocate/check-in/out) | — | ✓ (scoped) | — |
| `reports.read` | ✓ | ✓ (scoped) | — |
| `dashboard.view` | ✓ (system-wide) | ✓ (scoped) | ✓ (personal) |

Any new permission must be added here **and** to the backend permission registry in the same PR.

## Appendix C — Status Enums (V1)

```text
UserStatus        : pending_verification | active | suspended | deactivated
DormitoryStatus   : draft | active | inactive | archived
RoomStatus        : active | out_of_service | archived
BedStatus         : available | reserved | occupied | blocked | maintenance
RequestStatus     : draft | submitted | under_review | info_requested | approved
                  | rejected | withdrawn | expired | allocated | checked_in | completed | cancelled
AllocationStatus  : reserved | active | checked_out | cancelled
```

Enum values are part of the API contract: adding one is a SPEC-level change; renaming/removing one is
a breaking change requiring an ADR and a migration plan.

## Appendix D — Decision Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](docs/adr/ADR-0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](docs/adr/ADR-0002-backend-modular-monolith.md) | Backend as a modular monolith with layered slices | Accepted |
| [0003](docs/adr/ADR-0003-frontend-vue-typescript-spa.md) | Frontend as a Vue 3 + TypeScript SPA with generated API client | Accepted |
| [0004](docs/adr/ADR-0004-test-driven-development.md) | Test-Driven Development as the default method | Accepted |
| [0005](docs/adr/ADR-0005-authentication-and-authorization.md) | Authentication and authorization model | Proposed |
| [0006](docs/adr/ADR-0006-spec-plan-adr-workflow.md) | Spec → Plan → ADR gates for every feature | Accepted |

**Reserved, not yet written** (pre-allocated so `Task-List.md` references stay stable; each must reach
`Accepted` before its dependent feature is implemented): `0007` audit logging & system settings,
`0008` allocation concurrency control, `0009` dashboard/report aggregation, `0010` notifications &
background jobs, `0011` deployment topology. See [`docs/adr/README.md`](docs/adr/README.md).
