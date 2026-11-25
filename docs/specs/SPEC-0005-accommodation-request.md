# SPEC-0005 — Accommodation Request Submission (resident slice)

| Field | Value |
|-------|-------|
| **ID** | SPEC-0005 |
| **Feature** | F-0301 — Accommodation request submission (resident slice) |
| **Owner** | Software Architect |
| **Status** | Approved |
| **Milestone** | M3 — Requests & Allocation |
| **PLAN** | [PLAN-0005](../plans/PLAN-0005-accommodation-request.md) |
| **ADRs** | ADR-0002, ADR-0005, ADR-0012 |

---

## 1. Problem & context

The resident dashboard currently ends with a disabled “complete your accommodation request” card
(`dashboard.nextStep*`), so a resident has no way to ask for a bed. Everything is still handled by
the dormitory office. This slice replaces that placeholder with a real request: the resident fills a
short form, the request is stored with a status, and the resident can see and withdraw it.

The dormitory catalog (`F-0201…F-0205`) does not exist yet, so the dormitory is captured as a
**free-text preference** rather than a foreign key to a catalog entity. This is a deliberate,
recorded compromise; the field becomes a FK when `F-0205` lands (see §13).

## 2. Goals / non-goals

**Goals**

- A resident can submit an accommodation request from the web app.
- A resident can see only their own requests, newest first, with status and Jalali dates.
- A resident can withdraw a request that is still `submitted`.
- A resident can hold at most one active (`submitted`) request at a time.

**Non-goals**

- Manager review, approval/rejection, allocation, waitlist (`F-0302`…`F-0305`).
- Draft/resume flow (a single submit is enough for this slice).
- Document upload (`F-0206`).
- Dormitory/room catalog browsing (`F-0205`); the form uses free text + a room-type preference.

## 3. Personas & permissions

| Action | Admin | Manager | User |
|--------|:-----:|:-------:|:----:|
| Submit a request | — | — | ✓ (own) |
| List own requests | — | — | ✓ |
| Withdraw an own `submitted` request | — | — | ✓ |

Enforced server-side by `require_roles(Role.USER)`; a manager or admin token receives `403
forbidden`. A request that belongs to another resident is `404 not_found` (never `403`), so
existence is not leaked.

## 4. User stories

- As a resident, I want to submit a housing request with my dormitory/room preference and desired
  period, so that the office can review it.
- As a resident, I want to see the status of my request, so that I know it was received.
- As a resident, I want to withdraw a request I no longer need, so that the office does not process it.

## 5. Functional requirements

- **FR-1** `POST /api/v1/requests` creates a request owned by the caller with status `submitted`
  and returns `201` with the created resource.
- **FR-2** The payload requires `dormitory_name` (2–120 chars after trim), `room_type` (one of
  `single`, `double`, `triple`, `quad`), `desired_move_in` (ISO date) and `duration_months`
  (1–24). `note` is optional (≤ 1000 chars).
- **FR-3** A resident with an existing `submitted` request receives `409 request_already_active`
  and no second request is stored.
- **FR-4** `GET /api/v1/requests` returns only the caller’s requests, newest first, with
  `{ items, meta }` where `meta.total` is the caller’s request count.
- **FR-5** `POST /api/v1/requests/{id}/withdraw` moves an own `submitted` request to `withdrawn`
  and returns the updated resource.
- **FR-6** Withdrawing a `withdrawn` request returns `409 request_not_withdrawable`.
- **FR-7** Any endpoint rejects anonymous callers with `401 invalid_token` and non-residents with
  `403 forbidden`.
- **FR-8** Requests of another resident are invisible: list excludes them, detail/withdraw return
  `404 not_found`.
- **FR-9** The resident dashboard card links to `/requests`, and `/requests` is reachable only by
  the `user` role.

## 6. Acceptance criteria

- **AC-1 (FR-1, FR-2)** Given a signed-in resident and a valid payload, when the form is submitted,
  then the request appears in the list with status «ثبتشده» and a success message is shown.
- **AC-2 (FR-3)** Given an active request, when the resident submits another, then the API returns
  `409` and the UI shows a Persian explanation.
- **AC-3 (FR-4, FR-8)** Given two residents with requests, each list contains only their own.
- **AC-4 (FR-5, FR-6)** Given a `submitted` request, withdrawing twice succeeds once and then
  returns `409`; the badge changes to «لغوشده».
- **AC-5 (FR-7)** Given a manager token, all three endpoints return `403`.

## 7. Data model impact

New table `accommodation_request`:

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid | PK |
| `applicant_id` | uuid | FK `user.id`, `ON DELETE CASCADE`, indexed |
| `dormitory_name` | varchar(120) | free text until F-0205 |
| `room_type` | varchar(16) | one of the domain enum values |
| `desired_move_in` | date | calendar date, no timezone |
| `duration_months` | integer | 1–24 |
| `note` | text | nullable |
| `status` | varchar(24) | `submitted` / `withdrawn`, indexed |
| `created_at`, `updated_at` | timestamptz | mixins |

Migration `b4f1c7d92a10_add_accommodation_requests` (single, forward-only; downgrade drops the table).

## 8. API contract

```
POST   /api/v1/requests                 → 201 AccommodationRequestRead
GET    /api/v1/requests                 → 200 { items: AccommodationRequestRead[], meta: { page, per_page, total } }
POST   /api/v1/requests/{id}/withdraw   → 200 AccommodationRequestRead
```

Errors follow RFC 9457 with `code`:

| Situation | Status | code |
|-----------|--------|------|
| anonymous | 401 | `invalid_token` |
| non-resident role | 403 | `forbidden` |
| unknown / foreign request | 404 | `not_found` |
| invalid payload | 422 | `validation_error` |
| active request exists | 409 | `request_already_active` |
| request not `submitted` | 409 | `request_not_withdrawable` |

## 9. UI/UX notes

- Route `/requests`, resident-only, RTL, Persian by default.
- Form fields: خوابگاه مورد نظر، نوع اتاق، تاریخ ورود، مدت اقامت (ماه)، توضیحات.
- States: loading skeleton, empty (“هنوز درخواستی ثبت نکردهای”), error banner with retry,
  success banner after submit.
- The submit button is disabled while the request is in flight and when no active request can be
  created (existing `submitted` request) with an explanatory note.
- Dates are shown through the shared `formatDate` helper (Jalali); the API transports ISO dates.
- Labels are bound to inputs; the withdraw action is a real `<button>` and errors use `role="alert"`.

## 10. Edge cases & failure modes

- Two tabs submit at nearly the same time: the second request gets `409`; the list is reloaded.
- Withdraw while the list is stale: `409`/`404` are shown and the list reloaded.
- Whitespace-only dormitory name or note is rejected at the schema boundary (422).
- Duration outside 1–24 or a malformed date is a `422` with a field pointer.
- Past `desired_move_in` is accepted in this slice (server clock is not part of the domain); the
  office decides on feasibility during review (F-0302).

## 11. Non-functional requirements

- One request = one transaction; the service never commits (AGENTS.md §5.2).
- All list queries have an explicit `ORDER BY created_at DESC, id DESC`.
- No PII beyond the dormitory preference and free-text note; no logging of note content.
- Persian and English strings for every new label; no hardcoded text in components.

## 12. Out of scope & follow-ups

- Manager review queue and statuses beyond `submitted`/`withdrawn` → `F-0302`.
- Replacing `dormitory_name` with a catalog FK → `F-0205`.
- Draft/resume and document upload → later `F-0301` extension.

## 13. Open questions

None blocking. The free-text dormitory field is recorded above as the accepted interim design and
must be migrated when the catalog lands.

## Change Log

| Date | Change |
|------|--------|
| 2026-11-25 | v1.0.0 — resident submission slice approved (F-0301). |
