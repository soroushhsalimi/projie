# SPEC-0006 — Accommodation request review (manager queue)

| Field | Value |
|-------|-------|
| **ID** | SPEC-0006 |
| **Feature** | F-0302 — Request review workflow (manager queue) |
| **Owner** | Software Architect |
| **Status** | Approved |
| **Milestone** | M3 — Requests & Allocation |
| **PLAN** | [PLAN-0006](../plans/PLAN-0006-accommodation-review.md) |
| **ADRs** | ADR-0002, ADR-0005, ADR-0012 |

---

## 1. Problem & context

`F-0301` lets a resident submit an accommodation request, but nothing lets the dormitory office see
it: every request stays `submitted` forever. This slice adds the manager side of the workflow: a
queue over all residents, and the status transitions that record the decision.

The slice deliberately mirrors the maintenance-ticket queue (`SPEC-0004`): one filtered, paginated
list, a small and explicit state machine, a stable `409` for illegal moves, and manager/admin-only
access enforced in the transport layer.

## 2. Goals / non-goals

**Goals**

- A manager (or admin) can list every accommodation request, newest first, filtered by status.
- Each row carries the applicant's name, so the queue is usable without a join in the client.
- A manager can move a request to `under_review`, `approved` or `rejected`.
- Illegal transitions are rejected with a stable `409` code, never silently accepted.
- Residents cannot read the queue or change a status (`403`).

**Non-goals**

- Mandatory rejection reason, comment timeline, claim/assignment, SLA (`F-0302` follow-ups).
- Bed allocation and residency (`F-0303`, `F-0304`); approval changes a status only.
- Notifications, dormitory scoping, exports.

## 3. Personas & permissions

| Action | Admin | Manager | User |
|--------|:-----:|:-------:|:----:|
| List the review queue | ✓ | ✓ | — (`403`) |
| Change a request status | ✓ | ✓ | — (`403`) |
| Submit/list/withdraw own requests (`F-0301`) | — | — | ✓ |

Enforced server-side by `require_roles(Role.MANAGER, Role.ADMIN)`; these routes replace the role
dependency with the `F-0104` registry unchanged. Anonymous callers receive `401 invalid_token`.

## 4. User stories

- As a *manager*, I want the newly submitted requests in one queue, so that nothing waits unseen.
- As a *manager*, I want to mark a request "under review", so that the resident knows it is being
  looked at.
- As a *manager*, I want to approve or reject a request, so that the resident sees the decision.
- As a *resident*, I want my request status to reflect the office's decision, so I stop calling.

## 5. Functional requirements

- **FR-1** `GET /api/v1/requests/queue` returns `{ items, meta }` over **all** requests, newest
  first, each item including `applicant_name`; supports `status` filter, `page` (≥ 1) and
  `per_page` (1–100, default 20).
- **FR-2** `meta.total` is the count for the same filter, ignoring pagination.
- **FR-3** `PATCH /api/v1/requests/{id}/status` accepts `under_review`, `approved` or `rejected`
  and returns the updated request with `applicant_name`.
- **FR-4** Legal transitions: `submitted → under_review`, `submitted → approved`,
  `submitted → rejected`, `under_review → approved`, `under_review → rejected`. Every other move
  (including a repeated target and any move from `approved`, `rejected` or `withdrawn`) returns
  `409 request_transition_not_allowed`.
- **FR-5** Only `manager` and `admin` may call the two endpoints; a resident gets `403 forbidden`,
  no token gets `401 invalid_token`.
- **FR-6** An unknown request id returns `404 not_found`; an invalid `status` query or body value
  returns `422 validation_error`.
- **FR-7** A request in `under_review` still occupies the resident's single active slot
  (`SPEC-0005 FR-3`), so a new submission returns `409 request_already_active`.
- **FR-8** A status change emits `request.status.changed` with the request id and new status only.
- **FR-9** The web app exposes `/requests/review` for manager/admin with status tabs, a request
  card per row and the legal actions only; residents are redirected to `/dashboard`.
- **FR-10** After a status change the queue switches to the new status tab, so the change is
  immediately visible (same behaviour as `F-0406`).

## 6. Acceptance criteria

- **AC-1 (FR-1, FR-2)** Given requests from two residents, when a manager opens the queue, then both
  appear newest first with their applicant names and `meta.total` counts both.
- **AC-2 (FR-1)** Given one `submitted` and one `under_review` request, when the manager filters by
  `under_review`, then only that request is returned.
- **AC-3 (FR-3, FR-4)** Given a `submitted` request, moving it to `under_review` and then `approved`
  succeeds; a further move returns `409 request_transition_not_allowed`.
- **AC-4 (FR-5)** Given a resident token, both endpoints return `403`; given no token, `401`.
- **AC-5 (FR-6)** Given a random UUID, the status endpoint returns `404`; `status=archived` and
  `status=submitted` in the body return `422`.
- **AC-6 (FR-7)** Given a request moved to `under_review`, a new submission by the same resident
  returns `409`.
- **AC-7 (FR-9, FR-10)** Given a manager signed in, when they approve a request in the `submitted`
  tab, then the `approved` tab becomes active and the request is listed there.

## 7. Data model impact

None. `accommodation_request.status` is a `varchar(24)` holding the domain enum value; the new
values (`under_review`, `approved`, `rejected`) fit the column. No migration is required, and no
existing column, index or constraint changes.

## 8. API contract

```
GET   /api/v1/requests/queue?status=&page=&per_page=  → 200 { items: RequestSummaryRead[], meta }
PATCH /api/v1/requests/{id}/status                    → 200 RequestSummaryRead
```

```json
// GET /api/v1/requests/queue?status=submitted
{
  "items": [
    {
      "id": "6a1c…",
      "applicant_name": "سارا محمدی",
      "dormitory_name": "خوابگاه الزهرا",
      "room_type": "double",
      "desired_move_in": "2027-02-01",
      "duration_months": 6,
      "note": "اتاق نزدیک پنجره",
      "status": "submitted",
      "created_at": "2026-11-25T10:00:00Z",
      "updated_at": "2026-11-25T10:00:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 1 }
}
```

```json
// PATCH /api/v1/requests/{id}/status
{ "status": "under_review" }
```

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `invalid_token` | 401 | Missing or malformed access token |
| `forbidden` | 403 | Authenticated but not manager/admin |
| `not_found` | 404 | Unknown request id |
| `request_transition_not_allowed` | 409 | Illegal or repeated status change |
| `validation_error` | 422 | Unknown filter/body status, bad page size |

## 9. UI/UX notes

- **Route:** `/requests/review`, `meta.requiresAuth: true`, `meta.roles: ['manager', 'admin']`.
- **Queue:** status tabs (همه / ثبت‌شده / در حال بررسی / تأییدشده / ردشده) with `aria-pressed`,
  count on the side, skeleton while loading, retry on error, empty state per filter.
- **Card:** applicant name and status badge, dormitory · room type · duration · move-in date, the
  optional note, submission date, and only the legal action buttons.
- **States:** the active button is disabled while the request is in flight; a successful change
  shows «وضعیت درخواست به … تغییر کرد» and moves the queue to that status tab.
- **Dashboard:** managers and admins get a “review resident requests” card next to the ticket card;
  residents keep their submission card.
- **RTL & i18n:** all strings in `fa-IR` (primary) and `en-US`; dates through `formatDate`.

## 10. Edge cases & failure modes

| # | Scenario | Expected behaviour |
|---|----------|--------------------|
| E1 | Resident calls the queue or the status endpoint | `403 forbidden`, no data leaked |
| E2 | Two managers act on one request | The second call returns `409` (target is terminal or repeated) |
| E3 | `status=archived` filter | `422 validation_error` |
| E4 | `per_page=500` | `422 validation_error` |
| E5 | Request withdrawn by the resident before the review | `409`; the queue reloads |
| E6 | Unknown id | `404`, never `500` |
| E7 | Expired SPA session | existing single-flight refresh retries once, then `401` |

## 11. Non-functional requirements

- **Performance:** p95 < 150 ms on a seeded dataset; one page query plus one count, the applicant
  name joined in SQL (no N+1).
- **Security:** role enforced server-side only; no free-text field is rendered as HTML.
- **Observability:** `request.status.changed` with request id and status; notes are never logged.
- **Accessibility:** WCAG 2.1 AA on `/requests/review` (keyboard tabs, visible focus, contrast).

## 12. Out of scope & follow-ups

- Rejection reason and a comments timeline, claim/assignment and SLA → later `F-0302` extension.
- Allocation of a bed after approval → `F-0303`.
- Notification of the decision → `F-0307`.

## 13. Open questions

| # | Question | Owner | Resolution |
|---|----------|-------|------------|
| Q1 | Should `approved` later become `withdrawn`? | Architect | Deferred; residency lifecycle (`F-0304`) owns that move |

## 14. Change log

| Date | Change |
|------|--------|
| 2026-11-25 | v1.0.0 — manager review queue approved for `F-0302` (status changes only; reason/timeline deferred). |
