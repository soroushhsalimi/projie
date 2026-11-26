# SPEC-0008 — Guest management: check-in/check-out with an allowed visit window

| Field | Value |
|-------|-------|
| **ID** | SPEC-0008 |
| **Feature ID** | F-0408 |
| **Title** | Front-desk guest visits: registration, check-in/check-out and allowed-time control |
| **Status** | Approved |
| **Owner** | Software Architect |
| **Milestone** | M4 |
| **Plan** | [`PLAN-0008`](../plans/PLAN-0008-guests.md) |
| **ADRs** | [`ADR-0002`](../adr/ADR-0002-backend-modular-monolith.md), [`ADR-0005`](../adr/ADR-0005-authentication-and-authorization.md) |
| **Created** | 2026-11-26 |
| **Last updated** | 2026-11-26 |

---

## 1. Problem & Context

Guests enter a self-governed dormitory all the time: a resident's family visits, a technician
arrives, a friend stays for the evening. Today the front desk writes the name in a paper notebook if
it writes anything at all. Nobody can answer “who is inside right now?”, “when did this guest
leave?”, or “was that guest even allowed in at this hour?”.

SARA keeps one **guest visit** record per visit: who the guest is, which resident hosts them, the
**allowed window** agreed at the desk, and the actual entry and exit timestamps. The desk registers a
visit, checks the guest in only inside the allowed window, and checks them out — a late exit is
recorded and flagged as overdue rather than rejected.

This slice is the front-desk (manager/admin) side. A resident requesting a guest pass is a follow-up
(§12); the seeder provides demo visits so the screen is never empty.

## 2. Goals & Non-Goals

**Goals**

- G1 — A manager lists guest visits filtered by status, newest first, paginated.
- G2 — A manager registers a visit with a guest name, host resident, purpose and an allowed window.
- G3 — Check-in is accepted only for an `expected` visit and only while the current time is inside
  the allowed window; outside it the API answers `409 guest_check_in_blocked`.
- G4 — Check-out is accepted only for a `checked_in` visit and records the exit timestamp; an exit
  after the allowed window is stored and flagged `overdue`.
- G5 — Illegal moves answer a stable `409` code, the window is validated (`422`), and every endpoint
  is manager/admin only (`403` for residents, `401` anonymously).
- G6 — The web app exposes `/guests` with the queue, a registration form and check-in/check-out.

**Non-Goals**

- NG1 — Visitor pre-registration by residents, QR/badge printing, ID document scanning.
- NG2 — Overnight-stay approval workflow, blacklists, capacity limits per room.
- NG3 — Notifications (`F-0307`), dormitory scoping (`F-0201`), reporting (`F-0401`).
- NG4 — Editing or deleting a recorded visit; the record is append-only in this slice.

## 3. Personas & Permissions

| Persona | May do | May not do |
|---------|--------|------------|
| Manager | Register a visit, list, read, check a guest in and out | Manage accounts, change a recorded exit time |
| Admin | Everything a manager may do (oversight) | Alter a recorded visit after the fact |
| User (resident) | — (requesting a guest pass is the follow-up) | List, register, check in or check out (`403`) |
| Visitor | — | Anything (`401` when unauthenticated) |

Permissions introduced: `guests.read`, `guests.register`, `guests.check_in`, `guests.check_out`
(manager, admin). Enforced by a role dependency in this slice and migrated to `F-0104` unchanged.

## 4. User Stories

- **US-1** — As a *manager*, I want to register a guest at the desk with the hours they may stay, so
  that the entry rule is written down before the door opens.
- **US-2** — As a *manager*, I want check-in to fail outside the allowed window, so that a late guest
  is escalated instead of silently admitted.
- **US-3** — As a *manager*, I want to check a guest out and see who is still inside, so that the
  building can be cleared at night.

## 5. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|:--------:|
| FR-1 | `GET /api/v1/guests` returns `{ items, meta }` newest first; filters by `status` (`expected`, `checked_in`, `checked_out`); `page` ≥ 1 and `per_page` 1–100 (default 20). | M |
| FR-2 | `POST /api/v1/guests` registers a visit from `guest_name` (2–120), `host_email`, optional `purpose` (≤ 200), `allowed_from` and `allowed_until` with an explicit timezone; the host must be an existing `user` account; the response is `201` with status `expected`. | M |
| FR-3 | The allowed window is valid only when `allowed_until > allowed_from` and it is at most 24 hours long; otherwise `422 validation_error`. | M |
| FR-4 | `POST /api/v1/guests/{id}/check-in` is legal only for an `expected` visit at a current time inside `[allowed_from, allowed_until]`; it stores `checked_in_at` and status `checked_in`. Anything else answers `409 guest_check_in_blocked`. | M |
| FR-5 | `POST /api/v1/guests/{id}/check-out` is legal only for a `checked_in` visit; it stores `checked_out_at` and status `checked_out`. Anything else answers `409 guest_check_out_blocked`. | M |
| FR-6 | A visit whose exit timestamp (or, while still inside, the current time) is after `allowed_until` is reported with `overdue: true`; the exit is never rejected for being late. | M |
| FR-7 | Every endpoint requires an authenticated principal with role `manager` or `admin`; a resident gets `403 forbidden`, no token gets `401 invalid_token`, an unknown id gets `404 not_found`. | M |
| FR-8 | Check-in and check-out emit structured log events (`guest.checked_in`, `guest.checked_out`) with the visit id, status and an overdue flag — never the guest name. | S |
| FR-9 | The web app exposes `/guests` for manager/admin with status filters, a registration form, the visit detail and check-in/check-out actions; residents land on `/dashboard`. | M |

## 6. Acceptance Criteria

**AC-1 (FR-1)** — *Given* three visits in different statuses, *when* a manager calls
`GET /guests?status=expected`, *then* only expected visits are returned, `meta.total` matches, and
items are newest first.

**AC-2 (FR-2)** — *Given* a resident host and a one-hour window, *when* the manager registers the
visit, *then* `201`, status `expected`, `host_name` is the resident's full name and the timestamps
echo the requested window in UTC.

**AC-3 (FR-3)** — *Given* `allowed_until` before `allowed_from`, *then* `422`; *given* a 25-hour
window, *then* `422`; nothing is stored.

**AC-4 (FR-4)** — *Given* an expected visit whose window contains the current time, *when* checked
in, *then* `200`, status `checked_in` and `checked_in_at` set; *when* checked in again, *then* `409`.
*Given* an expired window, *then* `409 guest_check_in_blocked`.

**AC-5 (FR-5)** — *Given* a checked-in visit, *when* checked out, *then* `200`, status
`checked_out`; *given* an expected visit, *then* `409 guest_check_out_blocked`.

**AC-6 (FR-6)** — *Given* a visit that exits after `allowed_until`, *then* the response has
`overdue: true` and the exit time is stored.

**AC-7 (FR-7)** — *Given* a resident token, *when* any endpoint is called, *then* `403`; *given* no
token, *then* `401`; *given* a random UUID, *then* `404`.

**AC-8 (FR-9)** — *Given* a manager signed in, *when* they open `/guests`, *then* the queue renders
with loading, empty and error states, the registration form and the check-in/check-out action; a
resident visiting `/guests` lands on `/dashboard`.

## 7. Data Model Impact

New table (additive migration, no backfill):

```text
guest_visit
  id              uuid  pk
  host_id         uuid  not null  fk → user.id on delete cascade  (index)
  guest_name      varchar(120) not null
  purpose         varchar(200) null
  allowed_from    timestamptz not null
  allowed_until   timestamptz not null
  status          varchar(24) not null default 'expected'  (index)
  checked_in_at   timestamptz null
  checked_out_at  timestamptz null
  created_at      timestamptz not null
  updated_at      timestamptz not null
```

`status` is a constrained `varchar` (ADR-0002); the value set lives in the domain state rules and the
API schema. No unique constraint: the same guest may visit twice. Demo visits are added by the
idempotent seeder.

## 8. API Contract

| Method | Path | Permission | Success | Errors |
|--------|------|------------|---------|--------|
| `GET` | `/api/v1/guests` | `guests.read` | `200` | `401`, `403`, `422` |
| `POST` | `/api/v1/guests` | `guests.register` | `201` | `401`, `403`, `422` |
| `GET` | `/api/v1/guests/{id}` | `guests.read` | `200` | `401`, `403`, `404` |
| `POST` | `/api/v1/guests/{id}/check-in` | `guests.check_in` | `200` | `401`, `403`, `404`, `409` |
| `POST` | `/api/v1/guests/{id}/check-out` | `guests.check_out` | `200` | `401`, `403`, `404`, `409` |

```json
// POST /guests
{
  "guest_name": "مریم احمدی",
  "host_email": "resident@sara.ir",
  "purpose": "ملاقات خانوادگی",
  "allowed_from": "2026-11-26T16:00:00Z",
  "allowed_until": "2026-11-26T20:00:00Z"
}
```

```json
// 201 / GET /guests/{id}
{
  "id": "0b7e…",
  "guest_name": "مریم احمدی",
  "host_name": "سارا محمدی",
  "purpose": "ملاقات خانوادگی",
  "status": "checked_in",
  "allowed_from": "2026-11-26T16:00:00Z",
  "allowed_until": "2026-11-26T20:00:00Z",
  "checked_in_at": "2026-11-26T16:10:00Z",
  "checked_out_at": null,
  "overdue": false,
  "created_at": "2026-11-26T15:40:00Z",
  "updated_at": "2026-11-26T16:10:00Z"
}
```

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `invalid_token` | 401 | Missing/malformed access token |
| `forbidden` | 403 | Authenticated but not manager/admin |
| `not_found` | 404 | Unknown visit id |
| `guest_check_in_blocked` | 409 | Wrong status, too early, or the allowed window has passed |
| `guest_check_out_blocked` | 409 | The guest was never checked in |
| `validation_error` | 422 | Bad status filter, page size, window, unknown host, blank name |

## 9. UI / UX Notes

- **Route:** `/guests`, `meta.requiresAuth: true`, `meta.roles: ['manager', 'admin']`.
- **Screens:** queue with status tabs (همه / در انتظار ورود / داخل خوابگاه / خارج‌شده), total counter,
  skeleton, empty state and retry.
- **Registration form:** guest name, host email, purpose, allowed-from and allowed-until
  (`datetime-local`), client-side check that the end is after the start; server errors are shown.
- **Detail:** guest, host, purpose, allowed window, entry/exit times, «ثبت ورود» while expected,
  «ثبت خروج» while inside, and an «مهلت گذشته» badge when overdue.
- **Dashboard:** managers and admins get a «مدیریت مهمان» card linking to `/guests`.
- **RTL & i18n:** all strings in `fa-IR` (primary) and `en-US`; window times through one formatter.
- **Accessibility:** status tabs are buttons with `aria-pressed`, the panel is a `<section>` with a
  heading, every input has a label, actions are disabled while submitting.

## 10. Edge Cases & Failure Modes

| # | Scenario | Expected behaviour |
|---|----------|--------------------|
| E1 | Resident calls a desk endpoint | `403 forbidden`, no guest data leaked |
| E2 | Classified status filter (`status=cancelled`) | `422 validation_error` |
| E3 | Guest arrives 5 minutes before the window | `409 guest_check_in_blocked` |
| E4 | Guest arrives after the window | `409 guest_check_in_blocked` |
| E5 | Guest leaves after the window | Accepted; `overdue: true` |
| E6 | Two managers check in at once | Second call returns `409 guest_check_in_blocked` |
| E7 | Host email belongs to a manager or is unknown | `422 validation_error`, nothing stored |
| E8 | Naive timestamp without a timezone | `422 validation_error` |
| E9 | 25-hour window | `422 validation_error` |
| E10 | Expired session in the SPA | existing single-flight refresh retries once, then `401` |

## 11. Non-Functional Requirements

- **Performance:** queue p95 < 150 ms on a seeded dataset; one query for the page plus one count.
- **Security:** role enforced server-side; guest names and purposes rendered through `{{ }}`;
  no guest name in logs (AGENTS.md §9.5).
- **Observability:** `guest.checked_in` / `guest.checked_out` log lines with the visit id, status and
  an overdue flag only.
- **Accessibility:** WCAG 2.1 AA on `/guests` (keyboard tabs, labelled inputs, visible focus).

## 12. Out of Scope & Follow-ups

- Out of scope: resident guest-pass requests, ID verification, blacklists, badges, edits/deletes,
  notifications, dormitory scoping, capacity rules.
- Follow-ups: a resident «درخواست ورود مهمان» slice; move the role check into `F-0104`; alert the
  manager when a guest passes `allowed_until` once `F-0307` lands.

## 13. Open Questions

| # | Question | Owner | Needed by | Resolution |
|---|----------|-------|-----------|------------|
| Q1 | Is a late exit rejected or only flagged? | Architect | F-0408 | Resolved — flagged `overdue`; a guest must always be able to leave |
| Q2 | Is overnight stay inside this window rule? | Architect | F-0408 | Deferred — a 24-hour cap is V1 policy; overnight approval is its own SPEC |

## 14. Change Log

| Date | Change | By | Re-approved |
|------|--------|----|-------------|
| 2026-11-26 | Initial specification, `F-0408` intake | Architect | — |
