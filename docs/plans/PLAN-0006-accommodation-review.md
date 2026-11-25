# PLAN-0006 — Accommodation request review (manager queue)

| Field | Value |
|-------|-------|
| **ID** | PLAN-0006 |
| **SPEC** | [SPEC-0006](../specs/SPEC-0006-accommodation-review.md) |
| **Owner** | Software Architect |
| **Status** | Approved |
| **Estimated size** | S–M (domain rule + repository reads + two endpoints + one web view + tests) |

---

## 1. Design summary

Extend the existing `requests` vertical slice instead of adding a module. `domain/requests.py` gains
three statuses, `ACTIVE_STATUSES` and `ensure_review_transition`; the repository gains queue-wide
reads joined with `user.full_name`; the service gains `list_queue` and `review`; the router gains
`GET /requests/queue` and `PATCH /requests/{id}/status` guarded by
`require_roles(MANAGER, ADMIN)`. No migration: status stays a bounded `varchar(24)`.

The web app reuses `modules/requests`: the API client gains `listQueue`/`updateStatus`, `format.ts`
gains the filter list and the legal-action map, and a new `RequestQueueView.vue` renders the queue at
`/requests/review`. The manager dashboard gains an entry card.

## 2. Work breakdown

- [x] **T1 — Domain rules (red first).** `tests/unit/test_request_rules.py` covers the status set,
  `ACTIVE_STATUSES`, the five legal transitions and the illegal ones. Touches
  `domain/requests.py`.
  Verify: `pytest -q tests/unit/test_request_rules.py`.
- [x] **T2 — Persistence.** `tests/integration/test_request_repository.py` proves the queue is
  global and newest first, the status filter and count, the applicant-name join, and that
  `under_review` counts as active. Touches `repository.py`.
  Verify: `pytest -q tests/integration/test_request_repository.py`.
- [x] **T3 — Service + error.** `tests/api/test_request_review.py` drives list/review; the service
  maps a domain violation onto `RequestTransitionBlocked`. Touches `core/errors.py`,
  `service.py`.
- [x] **T4 — HTTP layer.** Router routes, `RequestSummaryRead`, `RequestQueuePageRead`,
  `RequestStatusUpdate`; the same contract test verifies 200, 401, 403, 404, 409 and 422.
- [x] **T5 — Web module.** `apps/web/tests/unit/request-review.spec.ts` covers the helpers, the
  route guard and the approve flow (including the conflict banner). Touches
  `modules/requests/{api,format}.ts`, `views/RequestQueueView.vue`, `api/types.ts`, `router.ts`.
  Verify: `vitest run tests/unit/request-review.spec.ts`.
- [x] **T6 — Dashboard entry point + i18n.** Managers/admins get a review card; `fa-IR` and `en-US`
  gain the new strings and the new status labels.
- [x] **T7 — Docs.** SPEC-0006/PLAN-0006 and the `Task-List.md` row for `F-0302`.

## 3. Test plan

| Behaviour | Level | Test |
|-----------|-------|------|
| Status set, active statuses, legal/illegal transitions | unit | `test_request_rules.py` |
| Global newest-first queue, filter, count, applicant join | integration | `test_request_repository.py` |
| Queue 200 + applicant names + filter + pagination | API | `test_request_review.py` |
| Review 200 and `409` on a repeated/terminal move | API | `test_request_review.py` |
| Resident 403, anonymous 401, unknown id 404, bad status 422 | API | `test_request_review.py` |
| `under_review` still blocks a second submission | API | `test_request_review.py` |
| Filter list, legal actions, route roles, approve flow | frontend unit | `request-review.spec.ts` |

“One thing that would prove this broken”: a resident reading the queue, or an `approved` request
being moved again without a `409`.

## 4. Data/migration plan

No schema change; `status` already accepts the new values. Nothing to migrate or roll back in the
database.

## 5. Rollout & rollback

No feature flag. Rollback = revert the commit; the resident slice keeps working because the extra
statuses are additive and `withdrawn`/`submitted` behaviour is unchanged.

## 6. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| A second active request appears once review starts | `ACTIVE_STATUSES` includes `under_review`, covered by an API test |
| Two managers race on the same request | The state machine rejects the repeated move with `409`; SQLite has no row lock, Postgres gets one with `F-0303` |
| Queue leaks another resident's data | The endpoint is manager/admin-only and covered by 401/403 tests |
| Approving implies a bed that does not exist | Documented: approval changes status only; allocation is `F-0303` |

## 7. Definition of Done

- [x] All FRs have tests that fail when the behaviour is removed.
- [x] `pytest -q`, `ruff check`, `vue-tsc --noEmit` and `vitest run` pass.
- [x] The app boots and the queue renders for a manager against the existing database.
- [x] fa-IR/en-US strings complete; the dashboard links managers to the queue.
- [x] SPEC/PLAN and Task-List updated.

## 8. Progress log

| Date | Entry |
|------|-------|
| 2026-11-25 | PLAN approved; T1–T7 implemented on `feat/F-0302-request-review`. |
