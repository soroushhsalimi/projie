# SPEC-0007 — Complaints management: review and initial response

| Field | Value |
|-------|-------|
| **ID** | SPEC-0007 |
| **Feature ID** | F-0407 |
| **Title** | Manager review of resident complaints with one recorded initial response |
| **Status** | Approved |
| **Owner** | Software Architect |
| **Milestone** | M4 |
| **Plan** | [`PLAN-0007`](../plans/PLAN-0007-complaints.md) |
| **ADRs** | [`ADR-0002`](../adr/ADR-0002-backend-modular-monolith.md), [`ADR-0005`](../adr/ADR-0005-authentication-and-authorization.md) |
| **Created** | 2026-11-26 |
| **Last updated** | 2026-11-26 |

---

## 1. Problem & Context

Residents complain about noise, cleanliness, safety and staff behaviour by phone or in person. Nobody
records what was raised, whether anyone looked at it, or what the first answer was. The dormitory
office therefore cannot prove it responded, and residents repeat the same complaint.

SARA keeps those complaints as **complaints**: one record per issue, a small status machine, and a
single **initial response** written by the dormitory office. This slice is the manager side — the
queue, the record, and the first answer. Filing a complaint from the resident UI is a follow-up
(§12); the seeder provides demo complaints so the queue is never empty.

## 2. Goals & Non-Goals

**Goals**

- G1 — A manager (or admin) lists complaints filtered by status, newest first, paginated.
- G2 — A manager opens one complaint and reads the resident, category, description and its initial
  response (when one exists).
- G3 — A manager marks a complaint «در حال بررسی» (`submitted → in_review`).
- G4 — A manager records one initial response; recording it answers the complaint and stores the
  responder and timestamp.
- G5 — A second response, or an illegal status move, is rejected with a stable `409` code.
- G6 — Residents and visitors cannot list, read or answer complaints (`403` / `401`).

**Non-Goals**

- NG1 — Resident-facing complaint filing and "my complaints" (follow-up feature).
- NG2 — Follow-up conversation threads beyond the first answer, attachments, SLA timers.
- NG3 — Notification fan-out (`F-0307`), dormitory scoping (`F-0201`), assignment to a person.

## 3. Personas & Permissions

| Persona | May do | May not do |
|---------|--------|------------|
| Manager | List/detail, mark in review, record the initial response | Manage accounts, read complaints outside a future dormitory scope |
| Admin | Everything a manager may do (oversight) | Alter the recorded response afterwards |
| User (resident) | — (filing is the follow-up feature) | List, read, review or answer (`403`) |
| Visitor | — | Anything (`401`) |

Permissions introduced: `complaints.read`, `complaints.review`, `complaints.respond` (manager,
admin). Enforced by a role dependency in this slice and migrated to `F-0104` unchanged.

## 4. User Stories

- **US-1** — As a *manager*, I want every open complaint in one queue, so that none is forgotten.
- **US-2** — As a *manager*, I want to mark a complaint as being reviewed, so that the queue shows
  who is working on what.
- **US-3** — As a *manager*, I want to write the first answer once, so that the resident gets a
  trustworthy reply and we keep a record of it.
- **US-4** — As a *resident*, I want my complaint to stay private from other residents.

## 5. Functional Requirements

| ID | Requirement | Priority |
|----|-------------|:--------:|
| FR-1 | `GET /api/v1/complaints` returns `{ items, meta }` newest first; filters by `status` (`submitted`, `in_review`, `answered`); `page` ≥ 1 and `per_page` 1–100 (default 20). | M |
| FR-2 | `GET /api/v1/complaints/{id}` returns the complaint, the resident name, description, category, status and `response` (`null` until answered). | M |
| FR-3 | `POST /api/v1/complaints/{id}/status` accepts only `in_review`; `submitted → in_review` is legal, anything else returns `409 complaint_transition_not_allowed`. | M |
| FR-4 | `POST /api/v1/complaints/{id}/response` validates a 2–2000 character body, stores one response with the responder, sets status to `answered` and returns `201`. | M |
| FR-5 | A complaint that is already answered cannot receive another response (`409 complaint_already_answered`), and the database enforces uniqueness per complaint. | M |
| FR-6 | Every endpoint requires an authenticated principal with role `manager` or `admin`; a resident gets `403 forbidden`, no token gets `401 invalid_token`, an unknown id gets `404 not_found`. | M |
| FR-7 | Response and status change emit structured log events (`complaint.response.recorded`, `complaint.status.changed`) with the complaint id and status only. | S |
| FR-8 | The web app exposes `/complaints` for manager/admin with status filters, a detail panel showing the recorded answer, and the review/answer actions; residents land on `/dashboard`. | M |

## 6. Acceptance Criteria

**AC-1 (FR-1)** — *Given* three complaints in different statuses, *when* a manager calls
`GET /complaints?status=submitted`, *then* only submitted complaints are returned, `meta.total`
matches, and items are newest first.

**AC-2 (FR-2)** — *Given* an answered complaint, *when* the detail is read, *then* `response.body`
and `response.responder_name` are returned; *given* an unanswered one, *then* `response` is `null`.

**AC-3 (FR-3)** — *Given* a submitted complaint, *when* `in_review` is set, *then* `200` and the
status changes; *when* it is set again, *then* `409 complaint_transition_not_allowed`.

**AC-4 (FR-4, FR-5)** — *Given* a submitted complaint, *when* the manager records an initial
response, *then* `201`, status `answered` and the response is attached; *when* a second response is
posted, *then* `409 complaint_already_answered`.

**AC-5 (FR-6)** — *Given* a resident token, *when* any endpoint is called, *then* `403`; *given* no
token, *then* `401`; *given* a random UUID, *then* `404`.

**AC-6 (FR-8)** — *Given* a manager signed in, *when* they open `/complaints`, *then* the queue
renders with loading, empty and error states and the answer action; a resident visiting `/complaints`
lands on `/dashboard`.

## 7. Data Model Impact

New tables (additive migration, no backfill):

```text
complaint
  id            uuid  pk
  resident_id   uuid  not null  fk → user.id on delete cascade  (index)
  subject       varchar(160) not null
  description   text not null
  category      varchar(32) not null default 'other'
  status        varchar(24) not null default 'submitted'  (index)
  created_at    timestamptz not null
  updated_at    timestamptz not null

complaint_response
  id            uuid  pk
  complaint_id  uuid  not null  fk → complaint.id on delete cascade  (unique index)
  responder_id  uuid  not null  fk → user.id on delete cascade
  body          text not null
  created_at    timestamptz not null
  updated_at    timestamptz not null
```

The unique index on `complaint.complaint_id` is the database half of FR-5. `status` is a constrained
`varchar` (ADR-0002); the value set lives in the domain state machine and the API schema. Demo
complaints are added by the idempotent seeder.

## 8. API Contract

| Method | Path | Permission | Success | Errors |
|--------|------|------------|---------|--------|
| `GET` | `/api/v1/complaints` | `complaints.read` | `200` | `401`, `403`, `422` |
| `GET` | `/api/v1/complaints/{id}` | `complaints.read` | `200` | `401`, `403`, `404` |
| `POST` | `/api/v1/complaints/{id}/status` | `complaints.review` | `200` | `401`, `403`, `404`, `409`, `422` |
| `POST` | `/api/v1/complaints/{id}/response` | `complaints.respond` | `201` | `401`, `403`, `404`, `409`, `422` |

```json
// GET /complaints?status=submitted&page=1&per_page=20
{
  "items": [
    {
      "id": "5d1a…",
      "subject": "سر و صدای شبانه در طبقه سوم",
      "category": "noise",
      "status": "submitted",
      "resident_name": "سارا محمدی",
      "created_at": "2026-11-22T20:10:00Z",
      "updated_at": "2026-11-22T20:10:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 1 }
}
```

```json
// GET /complaints/{id} — response is null until answered
{
  "id": "5d1a…",
  "subject": "سر و صدای شبانه در طبقه سوم",
  "category": "noise",
  "status": "answered",
  "resident_name": "سارا محمدی",
  "description": "هر شب بعد از ساعت ۱۲ صدای بلند…",
  "created_at": "2026-11-22T20:10:00Z",
  "updated_at": "2026-11-23T08:00:00Z",
  "response": {
    "id": "9f02…",
    "body": "با ساکنان طبقه سوم صحبت شد.",
    "responder_name": "رضا کریمی",
    "created_at": "2026-11-23T08:00:00Z"
  }
}

// POST /complaints/{id}/status
{ "status": "in_review" }

// POST /complaints/{id}/response
{ "body": "با ساکنان طبقه سوم صحبت شد." }
```

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `invalid_token` | 401 | Missing/malformed access token |
| `forbidden` | 403 | Authenticated but not manager/admin |
| `not_found` | 404 | Unknown complaint id |
| `complaint_transition_not_allowed` | 409 | Illegal or repeated status move |
| `complaint_already_answered` | 409 | A second initial response |
| `validation_error` | 422 | Bad filter, page size, status value or response body |

## 9. UI / UX Notes

- **Route:** `/complaints`, `meta.requiresAuth: true`, `meta.roles: ['manager', 'admin']`.
- **Screens:** queue with status tabs (همه / ثبت‌شده / در حال بررسی / پاسخ داده‌شده), total counter,
  skeleton, empty state («شکایتی در این وضعیت نیست»), retry on error.
- **Detail:** side panel with resident, category, description, the recorded answer (when present),
  «شروع بررسی» while submitted, and a response textarea with 2–2000 character validation. Once
  answered, the form is replaced by the recorded answer.
- **Dashboard:** managers and admins get a «مدیریت شکایات» card linking to `/complaints`.
- **RTL & i18n:** all strings in `fa-IR` (primary) and `en-US`; dates through `formatDate`.
- **Accessibility:** status tabs are buttons with `aria-pressed`, the panel is a `<section>` with a
  heading, the textarea has a label, actions are disabled while submitting.

## 10. Edge Cases & Failure Modes

| # | Scenario | Expected behaviour |
|---|----------|--------------------|
| E1 | Resident calls a manager endpoint | `403 forbidden`, no data leaked |
| E2 | `status=closed` filter | `422 validation_error` |
| E3 | `per_page=500` | `422 validation_error` |
| E4 | Two managers answer the same complaint | Second call returns `409 complaint_already_answered` |
| E5 | Whitespace-only response | `422`, nothing stored |
| E6 | Unknown complaint id | `404`, never `500` |
| E7 | Answering a complaint that was never marked in review | Legal: the response answers it directly |
| E8 | Expired session in the SPA | existing single-flight refresh retries once, then `401` |

## 11. Non-Functional Requirements

- **Performance:** queue p95 < 150 ms on a seeded dataset; one query for the page plus one count.
- **Security:** role enforced server-side; body length bounded; response bodies rendered through
  `{{ }}` interpolation, never as HTML.
- **Observability:** `complaint.status.changed` and `complaint.response.recorded` log lines with the
  complaint id and status; no complaint text in logs (AGENTS.md §9.5).
- **Accessibility:** WCAG 2.1 AA on `/complaints` (keyboard tabs, visible focus, contrast).

## 12. Out of Scope & Follow-ups

- Out of scope: resident complaint filing, further conversation, attachments, notifications, SLA,
  dormitory scoping, reopening an answered complaint.
- Follow-ups: a resident «ثبت شکایت» slice; move the role check into `F-0104`; notification on
  answer once `F-0307` lands.

## 13. Open Questions

| # | Question | Owner | Needed by | Resolution |
|---|----------|-------|-----------|------------|
| Q1 | May a complaint be reopened after it is answered? | Architect | F-0407 | Deferred — reopening needs its own decision and SPEC line |
| Q2 | Does the resident see the initial response in V1? | Architect | F-0407 | Deferred to the resident-facing follow-up |

## 14. Change Log

| Date | Change | By | Re-approved |
|------|--------|----|-------------|
| 2026-11-26 | Initial specification, `F-0407` intake | Architect | — |
