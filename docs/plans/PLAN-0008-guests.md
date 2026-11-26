# PLAN-0008 — Guest management (check-in/check-out with an allowed window)

| Field | Value |
|-------|-------|
| **ID** | PLAN-0008 |
| **SPEC** | [SPEC-0008](../specs/SPEC-0008-guests.md) |
| **Owner** | Software Architect |
| **Status** | Approved |
| **Estimated size** | S–M (new slice: domain rules + one table + five endpoints + one web view + tests) |

---

## 1. Design summary

Add a `guests` vertical slice beside `complaints`. `domain/guests.py` holds the three statuses, the
window policy (end after start, at most 24 hours) and the check-in/check-out rules, all pure
functions over explicit timestamps. The module owns `models.py` (`guest_visit`), `repository.py`
(queue and detail join with `user.full_name`), `service.py` (list, detail, register, check in, check
out) and `router.py` (manager/admin router-level dependency).

The current time enters the service through the module-level `utcnow` from `core.security`, so tests
patch exactly that boundary and never depend on the wall clock. Overdue is derived from stored
timestamps plus that clock, never stored as a column.

The web app gains `modules/guests` (`api.ts`, `format.ts`, `views/GuestsView.vue`), a route at
`/guests`, a manager dashboard card and fa-IR/en-US strings.

## 2. Work breakdown

- [x] **T1 — Domain rules (red first).** `tests/unit/test_guest_rules.py` covers the window policy
  (order, 24-hour cap, boundary minutes), the status machine for check-in/check-out and the overdue
  derivation. Touches `domain/guests.py`.
  Verify: `pytest -q tests/unit/test_guest_rules.py`.
- [x] **T2 — Persistence + service + HTTP.** `tests/api/test_guests.py` drives 200/201/401/403/404/
  409/422 for list, create, detail, check-in and check-out, with `utcnow` patched.
  Touches `core/errors.py`, `modules/guests/{models,repository,service,router,schemas}.py`,
  `api/deps.py`, `main.py`.
  Verify: `pytest -q tests/api/test_guests.py`.
- [x] **T3 — Migration.** Additive revision for `guest_visit` with `host_id` and `status` indexes;
  apply to the local database.
  Verify: `alembic upgrade head && alembic current`.
- [x] **T4 — Seed.** Three demo visits (expected, inside, left after the window) built relative to
  the current time so the screen is never empty. Verify: `python -m sara_api.db.seed`.
- [x] **T5 — Web module.** `tests/unit/guests.spec.ts` covers the helpers, the route guard and the
  register → check-in → check-out flow. Touches `modules/guests/*`, `api/types.ts`, `router.ts`.
  Verify: `vitest run tests/unit/guests.spec.ts`.
- [x] **T6 — Dashboard entry + i18n.** Managers/admins get a guests card; `fa-IR` and `en-US` gain
  labels, statuses, actions, form fields and error codes.
- [x] **T7 — Docs.** SPEC-0008/PLAN-0008 and the `Task-List.md` row for `F-0408` (v1.7.0).

## 3. Test plan

| Behaviour | Level | Test |
|-----------|-------|------|
| Window order, 24-hour cap, boundary check-in, status rules, overdue | unit | `test_guest_rules.py` |
| Queue 200, newest first, status filter, pagination, host name | API | `test_guests.py` |
| Create 201, host resolution, unknown host 422, bad window 422, naive time 422 | API | `test_guests.py` |
| Check-in inside the window 200, repeated 409, expired 409 | API | `test_guests.py` |
| Check-out 200, overdue flag, expected visit 409 | API | `test_guests.py` |
| Resident 403, anonymous 401, unknown id 404 | API | `test_guests.py` |
| Filters, legal actions, route roles, register/check-in/check-out flow | frontend unit | `guests.spec.ts` |

“One thing that would prove this broken”: a guest being checked in after the allowed window, or a
resident reading the desk queue.

## 4. Data/migration plan

Expand-only: one new table, no changes to `user` or existing slices. Nothing to backfill; rollback
drops it (demo data only). `checked_in_at` / `checked_out_at` are nullable by design and the status
column is the authoritative state.

## 5. Rollout & rollback

No feature flag. Rollback = revert the commit and downgrade the revision; no other slice reads
`guest_visit`.

## 6. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Wall-clock time makes tests flaky | The service reads time through `utcnow`; API tests patch it to a fixed instant and use relative windows elsewhere |
| Two managers check the same guest in | Status is re-read in the same transaction; the second call sees `checked_in` and answers `409`, covered by an API test |
| A late exit locks a guest inside | Exit is never rejected; it is recorded and flagged `overdue` |
| Guest PII leaks | Router is manager/admin-only; 401/403 tested; logs carry ids only |
| Demo seed floods a real database | The seeder only inserts when the table is empty, as with tickets and complaints |

## 7. Definition of Done

- [x] Every FR has a test that fails when the behaviour is removed.
- [x] Backend `pytest -q`, frontend `vitest run`, `vue-tsc --noEmit`, `vite build` pass.
- [x] Migration applied locally; the queue renders for a manager.
- [x] fa-IR/en-US strings complete; the dashboard links managers to the desk.
- [x] SPEC/PLAN and Task-List updated.

## 8. Progress log

| Date | Entry |
|------|-------|
| 2026-11-26 | PLAN approved; T1–T7 implemented. |
