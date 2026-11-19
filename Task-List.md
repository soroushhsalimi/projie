# Task-List.md — SARA Feature Backlog & Delivery Board

> **Project:** SARA (سرا) — Self-Governed Dormitory Management System
> **Document type:** Authoritative feature backlog and status board
> **Version:** 1.0.0 · **Last updated:** 2026-11-19
> **Owner:** Software Architect
> **Companion document:** [`AGENTS.md`](AGENTS.md) (rules, standards, gates)

---

## 1. Purpose and the Control Rule

This file is **the only authoritative status of features**. If a feature is not in this file, it does
not exist. If its status here disagrees with a slide, a chat message, or a commit message, this file
wins and the other source is corrected.

### The hard gate (enforced at review)

> **No implementation starts until the feature's row below has a filled `SPEC` and `PLAN` column,
> both files exist, and both are marked `Approved`.**

The sequence for every new feature is therefore always:

```
1. Add a row to §6 with ID, title, persona, priority, milestone, dependencies → Status: Backlog
2. Write docs/specs/SPEC-XXXX-<slug>.md          → review → Status: Specced   (SPEC Approved)
3. Write docs/plans/PLAN-XXXX-<slug>.md          → review → Status: Planned   (PLAN Approved)
4. Write/accept required ADRs if a decision emerges                        → Status: Ready
5. TDD implementation (Red → Green → Refactor)                              → Status: In Progress
6. PR + review (all CI gates green)                                        → Status: In Review
7. Merge, update this file with PR link, SPEC/PLAN → Implemented            → Status: Done
```

**A row may not skip columns.** A row with `Status: In Progress` and empty `SPEC`/`PLAN` is a process
violation and the PR is closed, not fixed in review.

---

## 2. Status Legend

| Status | Meaning | Who sets it |
|--------|---------|-------------|
| `Backlog` | Identified, not yet specified. Scope may still change. | Architect |
| `Specced` | `SPEC` written and **Approved**. Scope frozen. | Architect |
| `Planned` | `PLAN` written and **Approved**. Tasks, risks, and rollback defined. | Architect / implementer |
| `Ready` | Definition of Ready satisfied (AGENTS.md §15). May be picked up immediately. | Implementer |
| `In Progress` | Red test written; implementation underway. One feature per developer at a time. | Implementer |
| `In Review` | PR open, CI running/green, awaiting reviewer. | Implementer |
| `Blocked` | Cannot proceed; reason and blocker recorded in the Notes column and §8. | Anyone |
| `Done` | Merged to `main`; Definition of Done satisfied; PR link recorded. | Architect |
| `Deferred` | Consciously postponed beyond V1. Needs a new decision to revive. | Architect |
| `Superseded` | Replaced by another feature ID; link kept for history. | Architect |

**Priority (MoSCoW):** `M` = Must (V1 cannot ship), `S` = Should (V1 unless time forces out), `C` =
Could (nice to have), `W` = Won't (recorded to prevent re-litigation).

---

## 3. Milestones

| Milestone | Theme | Exit criteria |
|-----------|-------|---------------|
| **M0 — Foundation** | A running, tested, reproducible skeleton | `make bootstrap && make test` passes on a clean machine; CI green; empty app deployed locally. |
| **M1 — Identity & Access** | Accounts, sessions, roles, admin panel | A user can register, log in, and be assigned a role; every endpoint is permission-tested. |
| **M2 — Dormitory Catalog** | Dorms, buildings, rooms, beds, availability | A manager can model a dormitory; a user can browse it with live availability. |
| **M3 — Requests & Allocation** | The core business value | Resident applies → manager approves → bed allocated → check-in/out, with no double allocation possible. |
| **M4 — Operations & Insight** | Reporting, notifications, hardening, deployment | Manager sees occupancy reports; notifications work; security/a11y review passed; deployable. |

---

## 4. Current Focus

| Field | Value |
|-------|-------|
| **Active milestone** | M0 — Foundation |
| **Next feature to start** | `F-0001` — Repository, tooling & CI foundation |
| **Blocked features** | none |
| **Decisions pending** | `ADR-0005` (authentication model) — status `Proposed`, required before `F-0102` |
| **Working agreements** | TDD mandatory; one feature in `In Progress` at a time; `make check` before every push |

> Update this block at the start of every working session. It must never be stale.

---

## 5. Dependency Graph

```mermaid
graph LR
  F0001[F-0001 Tooling] --> F0002[F-0002 API skeleton]
  F0001 --> F0003[F-0003 Web skeleton]
  F0001 --> F0004[F-0004 Dev env & seed]
  F0002 --> F0005[F-0005 DB conventions]
  F0002 --> F0101[F-0101 Registration]
  F0002 --> F0104[F-0104 RBAC core]
  F0101 --> F0102[F-0102 Login/session]
  F0102 --> F0103[F-0103 Password reset]
  F0102 --> F0105[F-0105 User administration]
  F0104 --> F0105
  F0102 --> F0106[F-0106 Profile & settings]
  F0005 --> F0107[F-0107 Audit log]
  F0005 --> F0201[F-0201 Dormitories]
  F0201 --> F0202[F-0202 Buildings & floors]
  F0202 --> F0203[F-0203 Rooms]
  F0203 --> F0204[F-0204 Beds]
  F0204 --> F0205[F-0205 Public catalog]
  F0205 --> F0301[F-0301 Request submission]
  F0104 --> F0302[F-0302 Review workflow]
  F0301 --> F0302
  F0302 --> F0303[F-0303 Bed allocation]
  F0204 --> F0303
  F0303 --> F0304[F-0304 Residency lifecycle]
  F0303 --> F0305[F-0305 Waitlist & cancellation]
  F0304 --> F0306[F-0306 Occupancy dashboard]
  F0306 --> F0401[F-0401 Reports & exports]
  F0302 --> F0307[F-0307 Notifications]
```

---

## 6. Feature Backlog

### M0 — Foundation

| ID | Feature | Persona | MoSCoW | Status | SPEC | PLAN | ADR | Depends on |
|----|---------|---------|:------:|--------|------|------|-----|------------|
| **F-0001** | Repository, tooling & CI foundation (monorepo layout, uv + pnpm workspaces, ruff/mypy/eslint/prettier, pytest + vitest harness, CI pipeline, pre-commit, Makefile + PowerShell scripts) | Architect | M | **Next** | `—` | `—` | 0001, 0004, 0006 | — |
| **F-0002** | Backend skeleton (app factory, settings, structured logging, request-ID middleware, RFC 9457 error model, `/health/live` + `/health/ready`, OpenAPI export, layer-import contracts) | Architect | M | Backlog | `—` | `—` | 0002 | F-0001 |
| **F-0003** | Frontend skeleton (Vite + Vue 3 + TS strict, router, Pinia, Tailwind + PrimeVue theme, RTL/Jalali shell, `fa-IR` locale, generated API client, MSW test harness, layout/auth-free landing) | Architect | M | Backlog | `—` | `—` | 0003 | F-0001 |
| **F-0004** | Local dev environment & seeding (docker compose: Postgres + Mailpit, `.env.example`, idempotent seeder with demo dormitories and one account per role, `make bootstrap`) | Architect | M | Backlog | `—` | `—` | 0002 | F-0001, F-0002 |
| **F-0005** | Database conventions & migration baseline (naming convention on metadata, UUIDv7 PK mixin, timestamps mixin, Alembic baseline, `alembic check` in CI, enum-as-checked-varchar helper) | Architect | M | Backlog | `—` | `—` | 0002 | F-0002 |

### M1 — Identity & Access

| ID | Feature | Persona | MoSCoW | Status | SPEC | PLAN | ADR | Depends on |
|----|---------|---------|:------:|--------|------|------|-----|------------|
| **F-0101** | User registration (public signup, email/mobile uniqueness, verification token, `pending_verification` state, rate limiting, anti-enumeration responses) | User | M | Backlog | `—` | `—` | 0005 | F-0002, F-0005 |
| **F-0102** | Authentication & sessions (login, logout, JWT access token, rotating opaque refresh token with reuse detection, session revocation, auth dependencies) | All | M | Backlog | `—` | `—` | 0005 | F-0101 |
| **F-0103** | Password reset & recovery (request by email, single-use expiring token, revoke all sessions on reset, rate limit + generic response) | All | S | Backlog | `—` | `—` | 0005 | F-0102 |
| **F-0104** | RBAC core (role/permission registry, `require_permission` dependency, dormitory-scope resolution, 401/403/404 semantics, permission matrix tests for every route) | All | M | Backlog | `—` | `—` | 0005 | F-0002 |
| **F-0105** | User administration (admin list/search/filter/paginate, view account, suspend/reactivate/deactivate, role assignment with self-demotion protection, audit emission) | Admin | M | Backlog | `—` | `—` | 0005, 0007 | F-0102, F-0104 |
| **F-0106** | Profile & account settings (view/edit own profile, change password, active sessions list + revoke others, notification preferences) | All | S | Backlog | `—` | `—` | 0005 | F-0102 |
| **F-0107** | Audit log foundation (append-only table, in-transaction writer, actor/entity/action/before-after schema, admin read-only viewer with filters, no PII in payloads) | Admin | S | Backlog | `—` | `—` | 0007 | F-0005 |

### M2 — Dormitory Catalog

| ID | Feature | Persona | MoSCoW | Status | SPEC | PLAN | ADR | Depends on |
|----|---------|---------|:------:|--------|------|------|-----|------------|
| **F-0201** | Dormitory registry (manager-scoped CRUD, address/contact, gender policy, status draft→active→inactive→archived, manager assignment, archive instead of delete) | Manager | M | Backlog | `—` | `—` | 0002 | F-0005, F-0104 |
| **F-0202** | Buildings & floors (CRUD within a dormitory, floor numbering, per-building rules, ordering, cascade rules on archive) | Manager | M | Backlog | `—` | `—` | 0002 | F-0201 |
| **F-0203** | Rooms (room number unique per building, room type, capacity policy, gender policy, amenities, `out_of_service` state, image-free V1) | Manager | M | Backlog | `—` | `—` | 0002 | F-0202 |
| **F-0204** | Beds & availability computation (bed lifecycle, `available/reserved/occupied/blocked/maintenance`, derived capacity, availability query + `EXPLAIN`-verified indexes, partial unique index on active allocation) | Manager | M | Backlog | `—` | `—` | 0002 | F-0203 |
| **F-0205** | Public catalog browsing (user-facing list + detail of active dormitories/rooms, filters by gender/price-range/amenities, live free-bed count, empty/loading/error states, Jalali dates, RTL) | User | M | Backlog | `—` | `—` | 0003 | F-0204 |
| **F-0206** | Media & documents (dorm/room images, house-rules PDF, signed-URL delivery, upload validation) | Manager | C | Backlog | `—` | `—` | 0002 | F-0201 |

### M3 — Requests & Allocation

| ID | Feature | Persona | MoSCoW | Status | SPEC | PLAN | ADR | Depends on |
|----|---------|---------|:------:|--------|------|------|-----|------------|
| **F-0301** | Accommodation request submission (draft save/resume, dormitory + room-type preference, desired period, applicant details, document upload, submit transition, one active request per dormitory rule) | User | M | Backlog | `—` | `—` | 0002 | F-0205 |
| **F-0302** | Request review workflow (manager queue with filters/SLA, claim → `under_review`, approve / reject with mandatory reason / request more info, comments timeline, state-machine enforcement, concurrency-safe transitions) | Manager | M | Backlog | `—` | `—` | 0008 | F-0301 |
| **F-0303** | Bed allocation (suggested beds by policy, manual assignment, occupancy lock/`FOR UPDATE`, partial unique index, rollback on conflict, allocation event + audit, notification trigger) | Manager | M | Backlog | `—` | `—` | 0008 | F-0302, F-0204 |
| **F-0304** | Residency lifecycle (check-in, extension, room transfer, check-out, early departure, occupancy status sync, resident self-service view) | Manager / User | M | Backlog | `—` | `—` | 0008 | F-0303 |
| **F-0305** | Waitlist & cancellation (ordered waitlist on full capacity, auto-offer on vacancy, cancellation by resident and by manager, withdrawal rules, expiry job) | User / Manager | S | Backlog | `—` | `—` | 0008 | F-0303 |
| **F-0306** | Occupancy dashboard (manager: beds/rooms/occupancy %, pending queue, SLA breaches; personal summary for residents; cached aggregates with explicit invalidation) | Manager / Admin | S | Backlog | `—` | `—` | 0009 | F-0304 |
| **F-0307** | Notifications (in-app inbox + email via pluggable port, templated messages in `fa-IR`, delivery retries via ARQ, read/unread state, preference-aware dedupe) | All | S | Backlog | `—` | `—` | 0010 | F-0302 |

### M4 — Operations & Insight

| ID | Feature | Persona | MoSCoW | Status | SPEC | PLAN | ADR | Depends on |
|----|---------|---------|:------:|--------|------|------|-----|------------|
| **F-0401** | Reports & exports (occupancy over time, request funnel, rejection reasons, per-dormitory utilization; CSV export with streaming; PDF optional) | Manager / Admin | S | Backlog | `—` | `—` | 0009 | F-0306 |
| **F-0402** | System settings & feature flags (admin-editable settings with typed schema, audit on change, safe rollout of new behavior) | Admin | S | Backlog | `—` | `—` | 0007 | F-0105 |
| **F-0403** | Accessibility & performance hardening (axe audits on all primary flows, keyboard-only journey tests, Lighthouse budgets in CI, bundle-size budgets) | All | M | Backlog | `—` | `—` | 0003 | F-0307, F-0401 |
| **F-0404** | Security review & hardening (threat model, ASVS L1 checklist, dependency audit triage, rate-limit tuning, secrets rotation, penetration-test fixes) | All | M | Backlog | `—` | `—` | 0005 | F-0402 |
| **F-0405** | Production deployment & observability (container images, migrations in deploy pipeline, `/metrics`, error tracking, backups + tested restore, runbook, smoke tests) | Architect | M | Backlog | `—` | `—` | 0011 | F-0403, F-0404 |

### Deferred / Not in V1

| ID | Feature | Why deferred | Revisit when |
|----|---------|--------------|--------------|
| F-0501 | Online payments & invoicing | Out of V1 scope (§1.4) | A financial process is confirmed |
| F-0502 | Maintenance & incident tickets | Adjacent domain, not core to allocation | Post-M4 feedback |
| F-0503 | Native mobile apps | Responsive web covers V1 | Real usage data demands it |
| F-0504 | SMS notifications | Depends on a provider contract | Provider + budget available |
| F-0505 | Multi-tenant SaaS mode | Premature; single-operator V1 | Multiple operators onboard |
| F-0506 | Anonymous public booking (Cal.com-style) | Contradicts residency model | Product decision reversal |

---

## 7. Feature Intake Template

Copy this block to §6 when adding a feature. Every field is mandatory at `Backlog` time; `SPEC` and
`PLAN` may be `—` until the gates are passed.

```markdown
| **F-0XXX** | <feature name — outcome-oriented, not "user module"> | <Admin/Manager/User/All> | <M/S/C/W> | Backlog | `—` | `—` | <ADR ids> | <F-ids> |
```

**Intake checklist (before the row is accepted):**

- [ ] The feature is a **vertical slice** with observable user value, not a technical layer.
- [ ] It is small enough that SPEC + PLAN fit on two pages each.
- [ ] Its dependencies are listed and are already `Done` or scheduled before it.
- [ ] A rough effort estimate (`S` ≤ 1 day, `M` 2–3 days, `L` 4–5 days) is recorded in the Notes.
- [ ] Any architectural decision it forces is listed in the `ADR` column, even if not yet written.

---

## 8. Blocked & At-Risk Register

| Feature | Blocker | Owner | Since | Next action |
|---------|---------|-------|-------|-------------|
| `F-0102` | `ADR-0005` (auth model) is `Proposed`, not `Accepted` | Architect | 2026-11-19 | Review and accept ADR-0005 before M1 starts |

Update this table whenever a feature enters or leaves `Blocked`. An empty table should say "none".

---

## 9. Done Log (reverse chronological)

| Date | Feature | PR | Notes |
|------|---------|----|-------|
| 2026-11-19 | *Project bootstrap (documents only)* | — | `AGENTS.md`, `Task-List.md`, ADR 0001–0006, SPEC/PLAN templates created. No code yet. |

---

## 10. Milestone Progress

| Milestone | Features | Done | Progress |
|-----------|:--------:|:----:|----------|
| M0 — Foundation | 5 | 0 | 0% |
| M1 — Identity & Access | 7 | 0 | 0% |
| M2 — Dormitory Catalog | 6 | 0 | 0% |
| M3 — Requests & Allocation | 7 | 0 | 0% |
| M4 — Operations & Insight | 5 | 0 | 0% |
| **Total** | **30** | **0** | **0%** |

> Update this table in the same PR that changes a feature's status to `Done`. It is a derived view —
> when it disagrees with §6, §6 is correct and this table must be recomputed.

---

## 11. Change Log of This Document

| Date | Change | By |
|------|--------|----|
| 2026-11-19 | v1.0.0 — initial backlog: 30 features across 5 milestones, gates and templates. | Architect |

---

## 12. Immediate Next Step

**Start `F-0001`** (Repository, tooling & CI foundation):

1. Write `docs/specs/SPEC-0001-project-foundation.md` (structure, tooling versions, commands, CI
   jobs, acceptance criteria).
2. Write `docs/plans/PLAN-0001-project-foundation.md` (ordered TDD tasks: e.g. T1 monorepo skeleton,
   T2 backend test harness bringing a trivial green test, T3 lint/type gates, T4 frontend harness,
   T5 CI pipeline, T6 `make`/PowerShell parity).
3. Only then create the actual files.

No feature beyond `F-0001` may be started before `F-0002`/`F-0003`/`F-0005` exist, because every
other feature depends on them.
