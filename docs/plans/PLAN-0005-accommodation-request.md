# PLAN-0005 — Accommodation Request Submission (resident slice)

| Field | Value |
|-------|-------|
| **ID** | PLAN-0005 |
| **SPEC** | [SPEC-0005](../specs/SPEC-0005-accommodation-request.md) |
| **Owner** | Software Architect |
| **Status** | Approved |
| **Estimated size** | M (backend module + migration + web module + tests) |

---

## 1. Design summary

A new backend module `requests` follows the same vertical slice as `tickets`: a pure domain module
(`domain/requests.py`) owns statuses, room types and the withdrawal rule; a repository holds the SQL;
a service owns the unit of work, ownership checks and the “one active request” invariant; a router
maps HTTP and enforces `Role.USER`. One Alembic revision adds `accommodation_request`. The web app
gains a `requests` module (`api.ts`, `format.ts`, `views/RequestsView.vue`) and a `/requests` route
limited to residents; the dashboard’s placeholder card becomes the entry point.

## 2. Work breakdown

- [x] **T1 — Domain rules (red first).** `tests/unit/test_request_rules.py` covers the status enum,
  the room-type enum and `ensure_withdrawable`. Touches `domain/requests.py`.
  Verify: `pytest -q apps/api/tests/unit/test_request_rules.py`.
- [x] **T2 — Persistence.** `tests/integration/test_request_repository.py` proves newest-first
  ordering, ownership filtering and the active-request count. Touches `modules/requests/models.py`,
  `repository.py`, the migration, `migrations/env.py`.
  Verify: `pytest -q apps/api/tests/integration/test_request_repository.py`.
- [x] **T3 — Service + errors.** `tests/api/test_requests.py` (contract) drives create/list/withdraw,
  the duplicate-active conflict and the ownership 404. Touches `core/errors.py`, `service.py`,
  `api/deps.py`.
  Verify: `pytest -q apps/api/tests/api/test_requests.py`.
- [x] **T4 — HTTP layer.** Router, schemas, `main.py` wiring; the same contract test verifies 201,
  401, 403, 409 and 422 codes.
- [x] **T5 — Web module.** `apps/web/tests/unit/requests.spec.ts` covers formatting helpers, the
  route guard and the submit/withdraw flow with a mocked API. Touches `modules/requests/*`,
  `api/types.ts`, `router.ts`, `tests/unit/requests.spec.ts`.
  Verify: `vitest run tests/unit/requests.spec.ts`.
- [x] **T6 — Dashboard entry point + i18n.** The next-step card links residents to `/requests`;
  `fa-IR` and `en-US` gain the new strings.
- [x] **T7 — Docs.** SPEC-0005/PLAN-0005 and the `Task-List.md` row for `F-0301`.

## 3. Test plan

| Behaviour | Level | Test |
|-----------|-------|------|
| Withdrawal rules per status | unit | `test_request_rules.py` |
| Newest-first list, ownership filter, active count | integration | `test_request_repository.py` |
| Create 201 + payload echo | API | `test_requests.py` |
| Duplicate active request → 409 | API | `test_requests.py` |
| Invalid duration / blank dormitory → 422 | API | `test_requests.py` |
| Manager/admin rejected → 403 | API | `test_requests.py` |
| Foreign request hidden → 404 | API | `test_requests.py` |
| Route role guard, helpers, submit flow | frontend unit | `requests.spec.ts` |

“One thing that would prove this broken”: a resident seeing another resident’s request, or a second
active request being stored.

## 4. Data/migration plan

Expand-only: add `accommodation_request` in one revision (`b4f1c7d92a10`); no existing column
changes. Downgrade drops the table. SQLite locally per ADR-0012; the same revision is portable to
PostgreSQL.

## 5. Rollout & rollback

No feature flag. Rollback = revert the commit and `alembic downgrade -1`; the dashboard card returns
to its placeholder and no data is lost for other features.

## 6. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Free-text dormitory drifts from the future catalog | Documented in SPEC-0005 §1/§13; migrate when F-0205 lands |
| Two concurrent submissions create two active requests | Service-level active check plus the 409 contract test; a partial unique index is deferred until Postgres is available (F-0004) |
| Ownership leak through list/detail | Repository filters by `applicant_id`; API test with two residents |

## 7. Definition of Done

- [x] All FRs have tests that fail when the behaviour is removed.
- [x] `pytest -q`, `vue-tsc --noEmit`, `vitest run` and `ruff check` pass.
- [x] Migration applies and the app boots against the migrated SQLite database.
- [x] fa-IR/en-US strings complete; dashboard links residents to the form.
- [x] SPEC/PLAN and Task-List updated.

## 8. Progress log

| Date | Entry |
|------|-------|
| 2026-11-25 | PLAN approved; T1–T7 implemented on `feat/F-0301-accommodation-request`. |
