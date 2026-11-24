# SPEC-0004 — Maintenance & repair ticket management

| Field | Value |
|-------|-------|
| **ID** | SPEC-0004 |
| **Feature ID** | F-0406 |
| **Title** | Manager queue for repair tickets: view, reply, change status |
| **Status** | Approved |
| **Owner** | Software Architect |
| **Milestone** | M4 |
| **Plan** | [`PLAN-0004`](../plans/PLAN-0004-maintenance-tickets.md) |
| **ADRs** | [`ADR-0002`](../adr/ADR-0002-backend-modular-monolith.md), [`ADR-0005`](../adr/ADR-0005-authentication-and-authorization.md) |
| **Created** | 2026-11-24 |
| **Last updated** | 2026-11-24 |

---

## 1. Problem & Context

Residents report broken beds, heaters, plumbing and doors by phone or in person. The manager has no
queue, no history of what was answered, and no way to tell a resident whether a repair is being
looked at. SARA digitizes that exchange as **maintenance tickets**: one ticket per problem, a message
thread, and a small, explicit status machine (`open → under_review → resolved`).

This slice is the **manager side** of that exchange. Filing a ticket from the resident UI is a
follow-up (see §12); the endpoints in this SPEC are the ones a manager needs to work a queue.

## 2. Goals & Non-Goals

**Goals**

- G1 — A manager (or admin) can list repair tickets, filtered by status, with pagination.
- G2 — A manager can open one ticket and read its full message thread.
- G3 — A manager can reply to a ticket; the reply is attributed and timestamped.
- G4 — A manager can move a ticket to `under_review` (در حال بررسی) and then to `resolved` (انجام شد).
- G5 — Illegal transitions are rejected with a stable `409` code, never silently accepted.
- G6 — Residents cannot read, reply to, or change the status of any ticket (`403`).

**Non-Goals**

- NG1 — Resident-facing ticket creation and "my tickets" list (follow-up feature).
- NG2 — Attachments/photos, SLA timers, notification fan-out (`F-0307`).
- NG3 — Assignment of a ticket to a specific staff member, priority scoring, dormitory scoping
  (dormitory entities do not exist yet, `F-0201`).
- NG4 — Real-time updates; the queue refreshes on demand.

## 3. Personas & Permissions

| Persona | May do | May not do |
|---------|--------|------------|
| Manager | List/detail tickets, reply, `under_review`, `resolved` | Read tickets outside a future dormitory scope (not yet modelled), manage accounts |
| Admin | Everything a manager may do (oversight) | — |
| User (resident) | — (creation is the follow-up feature) | List, read, reply, or change status (`403`) |
| Visitor | — | Anything (`401`) |

Permissions introduced: `tickets.read`, `tickets.reply`, `tickets.status.write` (manager, admin).
They are enforced by a role dependency in this slice and migrate to the `F-0104` registry unchanged.

## 4. User Stories

- **US-1** — As a *manager*, I want the open repair tickets in one queue, so that nothing is lost.
- **US-2** — As a *manager*, I want to reply in the ticket, so that the resident sees an answer
  instead of calling me.
- **US-3** — As a *manager*, I want to mark a ticket "under review" and later "done", so that the
  queue reflects reality.
- **US-4** — As a *resident*, I want my ticket not to be readable by other residents, so that my room
  problems stay private.

## 5. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|:--------:|
| FR-1 | `GET /api/v1/tickets` returns `{ items, meta }` ordered by newest first; supports `status` filter (`open`, `under_review`, `resolved`), `page` (≥ 1) and `per_page` (1–100, default 20). | M |
| FR-2 | `GET /api/v1/tickets/{id}` returns the ticket, reporter name, description and the message thread in chronological order. | M |
| FR-3 | `POST /api/v1/tickets/{id}/messages` appends a message (2–2000 chars) and returns the updated detail. | M |
| FR-4 | `PATCH /api/v1/tickets/{id}/status` accepts `under_review` or `resolved`; `open → under_review`, `under_review → resolved` and `open → resolved` are legal; everything else returns `409 ticket_transition_not_allowed`. | M |
| FR-5 | Every endpoint requires an authenticated principal with role `manager` or `admin`; a `user` gets `403 forbidden`, no token gets `401 invalid_token`. | M |
| FR-6 | Unknown ticket id returns `404 not_found` with the RFC 9457 body. | M |
| FR-7 | Reply and status change emit structured log events (`ticket.reply.added`, `ticket.status.changed`) carrying ticket id and new status only. | S |
| FR-8 | The web app exposes `/tickets` for manager/admin with filter tabs, detail panel, reply form and status actions; residents are redirected to `/dashboard`. | M |

## 6. Acceptance Criteria

**AC-1 (FR-1)** — *Given* three tickets in different statuses, *when* a manager calls
`GET /tickets?status=open`, *then* only open tickets are returned, `meta.total` equals that count,
and items are ordered by `created_at` descending.

**AC-2 (FR-2, FR-3)** — *Given* a ticket, *when* the manager posts a reply, *then* the response `201`
contains the new message last in `messages`, with the manager's name and role.

**AC-3 (FR-4)** — *Given* an `open` ticket, *when* status `under_review` is set, *then* `200` and
status changes; *when* status is set to `resolved` from `resolved`, *then* `409`.

**AC-4 (FR-5)** — *Given* a resident token, *when* any ticket endpoint is called, *then* `403`
`forbidden`; *given* no token, *then* `401 invalid_token`.

**AC-5 (FR-6)** — *Given* a random UUID, *when* the detail/reply/status endpoint is called, *then*
`404 not_found`.

**AC-6 (FR-8)** — *Given* a manager signed in, *when* they open `/tickets`, *then* the queue renders
with loading, empty and error states; a resident visiting `/tickets` lands on `/dashboard`.

## 7. Data Model Impact

New tables (additive migration, no backfill):

```text
ticket
  id            uuid  pk
  reporter_id   uuid  not null  fk → user.id on delete cascade  (index)
  subject       varchar(160) not null
  description   text not null
  category      varchar(32) not null default 'general'
  status        varchar(24) not null default 'open'  (index)
  created_at    timestamptz not null
  updated_at    timestamptz not null

ticket_message
  id            uuid  pk
  ticket_id     uuid  not null  fk → ticket.id on delete cascade  (index)
  author_id     uuid  not null  fk → user.id on delete cascade
  body          text not null
  created_at    timestamptz not null
  updated_at    timestamptz not null
```

`status` is a constrained `varchar` (ADR-0002 §enums); no database `CHECK` yet because the value set
is enforced by the domain state machine and the API schema. Demo tickets are added by the idempotent
seeder so the queue is never empty on a fresh checkout.

## 8. API Contract

| Method | Path | Permission | Success | Errors |
|--------|------|------------|---------|--------|
| `GET` | `/api/v1/tickets` | `tickets.read` | `200` | `401`, `403`, `422` |
| `GET` | `/api/v1/tickets/{id}` | `tickets.read` | `200` | `401`, `403`, `404` |
| `POST` | `/api/v1/tickets/{id}/messages` | `tickets.reply` | `201` | `401`, `403`, `404`, `422` |
| `PATCH` | `/api/v1/tickets/{id}/status` | `tickets.status.write` | `200` | `401`, `403`, `404`, `409`, `422` |

```json
// GET /tickets?status=open&page=1&per_page=20
{
  "items": [
    {
      "id": "0b0e…",
      "subject": "نشتی شیر آب حمام طبقه دوم",
      "category": "plumbing",
      "status": "open",
      "reporter_name": "سارا محمدی",
      "created_at": "2026-11-24T08:12:00Z",
      "updated_at": "2026-11-24T08:12:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 1 }
}
```

```json
// POST /tickets/{id}/messages
{ "body": "لوله‌کش فردا ساعت ۱۰ مراجعه می‌کند." }

// PATCH /tickets/{id}/status
{ "status": "under_review" }
```

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `invalid_token` | 401 | Missing/malformed access token |
| `forbidden` | 403 | Authenticated but not manager/admin |
| `not_found` | 404 | Unknown ticket id |
| `ticket_transition_not_allowed` | 409 | Illegal or repeated status change |
| `validation_error` | 422 | Bad filter, page size, message body or status value |

## 9. UI / UX Notes

- **Route:** `/tickets`, `meta.requiresAuth: true`, `meta.roles: ['manager', 'admin']`.
- **Screens:** queue list with status tabs (همه / باز / در حال بررسی / انجام شد), empty state
  ("تیکتی در این وضعیت نیست"), skeleton while loading, retry on error.
- **Detail:** side panel with reporter, category, description, message thread (own replies marked
  "مدیر"), reply textarea with client-side length validation, and the legal status action only.
- **RTL & i18n:** all strings in `fa-IR` (primary) and `en-US`; statuses labelled «باز»، «در حال
  بررسی»، «انجام شد»; dates through `formatDate`.
- **Accessibility:** each status tab is a button with `aria-pressed`, the panel is a `<section>` with
  a heading, the reply form has a labelled textarea, actions disabled while submitting.

## 10. Edge Cases & Failure Modes

| # | Scenario | Expected behaviour |
|---|----------|--------------------|
| E1 | Resident calls a manager endpoint | `403 forbidden`, no data leaked |
| E2 | `status=archived` filter | `422 validation_error` |
| E3 | `per_page=500` | `422 validation_error` |
| E4 | Two managers resolve the same ticket | Second call returns `409` (resolved is terminal) |
| E5 | Empty reply body / whitespace only | `422`, no message stored |
| E6 | Ticket id that does not exist | `404`, never `500` |
| E7 | Expired session in the SPA | existing single-flight refresh retries once, then `401` |

## 11. Non-Functional Requirements

- **Performance:** list p95 < 150 ms on a seeded dataset; one query for the page plus one count (no
  N+1 for reporter names).
- **Security:** role enforced server-side only; message body length bounded; no HTML rendering of
  bodies in the client (`{{ }}` interpolation).
- **Observability:** `ticket.reply.added` and `ticket.status.changed` log lines with `ticket_id` and
  `status`; no ticket body in logs.
- **Accessibility:** WCAG 2.1 AA on `/tickets` (keyboard tabs, visible focus, contrast).

## 12. Out of Scope & Follow-ups

- Out of scope: resident ticket creation, attachments, notifications, SLA, dormitory scoping.
- Follow-ups: `F-0104` (move the role check to the permission registry), a resident "file a ticket"
  slice, and a notification trigger once `F-0307` lands.

## 13. Open Questions

| # | Question | Owner | Needed by | Resolution |
|---|----------|-------|-----------|------------|
| Q1 | Should `resolved` be reopenable? | Architect | F-0406 | Deferred — reopen is a separate action with its own SPEC if requested |

## 14. Change Log

| Date | Change | By | Re-approved |
|------|--------|----|-------------|
| 2026-11-24 | Initial specification, promoted from deferred `F-0502` | Architect | — |
