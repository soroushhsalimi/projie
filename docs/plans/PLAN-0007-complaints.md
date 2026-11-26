# PLAN-0007 — Complaints management (review + initial response)

| Field | Value |
|-------|-------|
| **ID** | PLAN-0007 |
| **SPEC** | [SPEC-0007](../specs/SPEC-0007-complaints.md) |
| **Owner** | Software Architect |
| **Status** | Approved |
| **Estimated size** | S–M (new slice: domain rule + two tables + four endpoints + one web view + tests) |

---

## 1. Design summary

Add a `complaints` vertical slice beside `tickets`. `domain/complaints.py` holds the three statuses,
the review transition and the “answer once” rule. The module owns `models.py` (complaint and its
single response, unique per complaint), `repository.py` (queue joins with `user.full_name`),
`service.py` (list, detail, start review, record response) and `router.py` (manager/admin router-level
dependency). Errors map in `core/errors.py`; the service never imports FastAPI.

The web app gains `modules/complaints` (`api.ts`, `format.ts`, `views/ComplaintsView.vue`), a route at
`/complaints`, a manager dashboard card and fa-IR/en-US strings.

## 2. Work breakdown

- [x] **T1 — Domain rules (red first).** `tests/unit/test_complaint_rules.py` covers the closed
  transition matrix, the terminal `answered` state and the answer-once rule. Touches
  `domain/complaints.py`.
  Verify: `pytest -q tests/unit/test_complaint_rules.py`.
- [x] **T2 — Persistence + service + HTTP.** `tests/api/test_complaints.py` drives 200/201/401/403/
  404/409/422 for list, detail, status and response. Touches `core/errors.py`,
  `modules/complaints/{models,repository,service,router,schemas}.py`, `api/deps.py`, `main.py`.
  Verify: `pytest -q tests/api/test_complaints.py`.
- [x] **T3 — Migration.** Additive revision for `complaint` and `complaint_response` with the unique
  index on `complaint_id`; apply to the local `sara.db`.
  Verify: `alembic upgrade head && alembic current`.
- [x] **T4 — Seed.** Three demo complaints (submitted, in review, answered) so the queue is never
  empty. Verify: `python -m sara_api.db.seed`.
- [x] **T5 — Web module.** `tests/unit/complaints.spec.ts` covers the helpers, the route guard and the
  review → answer flow. Touches `modules/complaints/*`, `api/types.ts`, `router.ts`.
  Verify: `vitest run tests/unit/complaints.spec.ts`.
- [x] **T6 — Dashboard entry + i18n.** Managers/admins get a complaints card; `fa-IR` and `en-US`
  gain labels, statuses, actions and error codes.
- [x] **T7 — Docs.** SPEC-0007/PLAN-0007 and the `Task-List.md` row for `F-0407` (v1.6.0).

## 3. Test plan

| Behaviour | Level | Test |
|-----------|-------|------|
| Status set, review transition, terminal answered, answer-once | unit | `test_complaint_rules.py` |
| Queue 200, newest first, status filter, pagination, resident name | API | `test_complaints.py` |
| Detail with and without a response | API | `test_complaints.py` |
| Review 200 then `409`; unknown status `422` | API | `test_complaints.py` |
| Response `201`, status `answered`, second `409`; blank `422` | API | `test_complaints.py` |
| Resident 403, anonymous 401, unknown id 404 | API | `test_complaints.py` |
| Filter list, legal actions, route roles, review/answer flow | frontend unit | `complaints.spec.ts` |

“One thing that would prove this broken”: a resident reading the queue, or a second response being
accepted after the first.

## 4. Data/migration plan

Expand-only: two new tables, no changes to `user` or `ticket`. Nothing to backfill; rollback drops
them (demo data only). The unique index on `complaint_response.complaint_id` is created with the
table.

## 5. Rollout & rollback

No feature flag. Rollback = revert the commit and downgrade the revision; no other slice reads
`complaint`.

## 6. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Two managers answer at once | The unique index plus the service check reject the second with `409`, covered by an API test |
| A response leaks another resident's text | The router is manager/admin-only; 401/403 tested |
| “Answer once” drifts from the UI | `canAnswer` in `format.ts` mirrors the state machine; the API stays authoritative |
| The demo seed floods a real database | The seeder only inserts when the table is empty, as with tickets |

## 7. Definition of Done

- [x] Every FR has a test that fails when the behaviour is removed.
- [x] Backend `pytest -q`, frontend `vitest run`, `vue-tsc --noEmit`, `vite build` pass.
- [x] Migration applied locally; the queue renders for a manager.
- [x] fa-IR/en-US strings complete; the dashboard links managers to the queue.
- [x] SPEC/PLAN and Task-List updated.

## 8. Progress log

| Date | Entry |
|------|-------|
| 2026-11-26 | PLAN approved; T1–T7 implemented on `feat/F-0407-complaints`. |
