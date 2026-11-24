# PLAN-0004 — Maintenance & repair ticket management

| Field | Value |
|-------|-------|
| **ID** | PLAN-0004 |
| **Feature ID** | F-0406 |
| **SPEC** | [`SPEC-0004`](../specs/SPEC-0004-maintenance-tickets.md) |
| **Status** | Approved |
| **Owner** | Implementer |
| **Estimate** | S/M — 1 backend module, 1 web view |
| **Created** | 2026-11-24 |

---

## 1. Design summary

A new vertical slice `modules/tickets` (models, repository, service, schemas, router) plus a pure
domain module `domain/tickets.py` that owns the status machine. Role enforcement is a reusable
`require_roles(...)` dependency in `api/deps.py` (the `F-0104` permission registry remains the long-term
home). The web app gains `modules/tickets` (`api.ts`, `format.ts`, `views/TicketsView.vue`) and a
`/tickets` route guarded by role metadata. Demo tickets are added to the existing idempotent seeder so
the manager queue is demonstrable on a fresh database. No existing table changes; one additive Alembic
revision.

## 2. Work breakdown

| # | Task | Failing test first | Files | Verify |
|---|------|--------------------|-------|--------|
| T1 | Domain status machine with a stable error | `tests/unit/test_ticket_transition.py` (all six (state, target) pairs) | `domain/tickets.py`, `core/errors.py` | `pytest -q tests/unit/test_ticket_transition.py` |
| T2 | Persistence: `ticket`, `ticket_message` + repository | `tests/integration/test_ticket_repository.py` | `modules/tickets/models.py`, `repository.py`, migration, `main.py`, `migrations/env.py` | `pytest -q tests/integration/test_ticket_repository.py` |
| T3 | Role dependencies + service | `tests/api/test_tickets.py::test_list_requires_manager_role` | `api/deps.py`, `modules/tickets/service.py`, `schemas.py` | `pytest -q tests/api/test_tickets.py` |
| T4 | HTTP contract: list/detail/reply/status | remaining `test_tickets.py` cases (filters, pagination, 404, 409, 422) | `modules/tickets/router.py`, `main.py` | `pytest -q` |
| T5 | Idempotent demo tickets | manual: run seeder twice | `db/seed.py` | `python -m sara_api.db.seed` |
| T6 | Web api client + typed payloads + status helper | `tests/unit/tickets.spec.ts` (helper + route meta) | `api/types.ts`, `modules/tickets/api.ts`, `format.ts` | `pnpm test:unit` |
| T7 | Manager queue view and route guard | same spec: route resolves, roles metadata present | `modules/tickets/views/TicketsView.vue`, `app/router.ts`, `modules/dashboard/views/DashboardView.vue` | `pnpm typecheck` |
| T8 | Persian + English strings | — | `locales/fa-IR.ts`, `locales/en-US.ts` | `pnpm build` |

## 3. Test plan

| Behaviour | Level | Test |
|-----------|-------|------|
| Legal/illegal transitions exhaustively | unit | `test_ticket_transition.py` |
| Repository ordering, filters, message append | integration | `test_ticket_repository.py` |
| List paging + `meta.total`, status filter | api | `test_tickets.py` |
| Resident → 403, anonymous → 401 | api | `test_tickets.py` |
| Detail 404, reply 201, status 200/409, bad filter 422 | api | `test_tickets.py` |
| Web status label + guarded route metadata | unit (vitest) | `tickets.spec.ts` |

**"One thing that proves this is broken":** a resident can read a ticket, or `resolved → under_review`
returns 200 instead of 409.

## 4. Data/migration plan

Single revision `add_maintenance_tickets` after `397e3882bfd3`: create `ticket` and
`ticket_message` with their indexes and cascading foreign keys. Additive only; `downgrade` drops both
tables. No backfill; seeds insert demo rows only when the table is empty.

## 5. Rollout & rollback

Feature-flag free. Rollback = revert the PR (the migration's `downgrade` drops the two new tables; no
other table references them). The route is additive, so removing it cannot break existing screens.

## 6. Risks & mitigations

| # | Risk | Mitigation |
|---|------|-----------|
| R1 | Role check duplicated by `F-0104` later | Keep it in one dependency; `F-0104` replaces the body, not the call sites |
| R2 | Thread grows unbounded | 2000-char body bound; pagination of messages is a follow-up if needed |
| R3 | Seeder duplicates tickets on every run | Seed only when `ticket` table is empty (idempotent) |

## 7. Definition of Done

- [ ] All FR-1…FR-8 covered by tests that fail when the behaviour is removed.
- [ ] `pytest -q` green; `ruff check` clean on touched files.
- [ ] `pnpm test:unit`, `pnpm typecheck` green.
- [ ] `Task-List.md` row updated, SPEC/PLAN statuses set.
- [ ] No PII or ticket bodies in logs.

## 8. Progress log

| Date | Entry |
|------|-------|
| 2026-11-24 | SPEC and PLAN approved; implementation started on branch `repair`. |
| 2026-11-24 | T1–T8 complete: 72 backend tests, 27 web unit tests, `vue-tsc` and `vite build` green; live check against the seeded database returns 3 tickets for a manager and `403` for a resident. |
