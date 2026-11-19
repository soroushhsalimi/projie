# SPEC-XXXX — <Feature title, outcome-oriented>

<!--
Copy this file to docs/specs/SPEC-XXXX-<kebab-slug>.md.
Sections marked [REQUIRED] may not be deleted. If a section does not apply, keep the heading and
write "N/A — <reason>". Placeholders must be replaced before the status becomes Approved.
See AGENTS.md §7.2 for the authoritative list of required content.
-->

| Field | Value |
|-------|-------|
| **ID** | SPEC-XXXX |
| **Feature ID** | F-0XXX |
| **Title** | <short title> |
| **Status** | Draft <!-- Draft | In Review | Approved | Implemented | Superseded by SPEC-YYYY --> |
| **Owner** | <name> |
| **Milestone** | M0 <!-- M0 | M1 | M2 | M3 | M4 --> |
| **Plan** | [`PLAN-XXXX`](../plans/PLAN-XXXX-<slug>.md) |
| **ADRs** | [`ADR-XXXX`](../adr/ADR-XXXX-<slug>.md) <!-- or "none" --> |
| **Created** | YYYY-MM-DD |
| **Last updated** | YYYY-MM-DD |

---

## 1. Problem & Context [REQUIRED]

Who is in pain, what do they do today, and what breaks? Describe the current process concretely — not
"users need a better experience", but "a manager keeps a paper ledger and calls residents to check bed
availability; two managers have double-booked a bed twice this term".

Include the triggering event/evidence for this feature and link related SPECs.

## 2. Goals & Non-Goals [REQUIRED]

**Goals**

- G1 — <outcome that this feature must achieve>
- G2 — …

**Non-goals (explicitly out of scope)**

- NG1 — <what we are deliberately not doing, and why>
- NG2 — …

## 3. Personas & Permissions [REQUIRED]

| Persona | May do | May not do |
|---------|--------|------------|
| User | <specific actions> | <specific denials> |
| Manager | … | … |
| Admin | … | … |

New or changed permissions (must be added to `AGENTS.md` Appendix B in the same PR):

- `permission.name` — <who gets it, what it gates>

## 4. User Stories [REQUIRED]

- **US-1** — As a *<role>*, I want *<capability>*, so that *<outcome>*.
- **US-2** — …

## 5. Functional Requirements [REQUIRED]

Each FR must be independently testable and observable from outside the system.

| ID | Requirement | Priority |
|----|-------------|:--------:|
| FR-1 | <The system shall …> | M |
| FR-2 | … | S |

## 6. Acceptance Criteria [REQUIRED]

Given/When/Then, one block per FR (or per behavior group). These become test names.

**AC-1 (covers FR-1)**

- *Given* <precondition and state>
- *When* <action by a specific persona>
- *Then* <observable outcome, including status code / UI state / persisted change>

**AC-2 (covers FR-2)** …

## 7. Data Model Impact [REQUIRED]

- **New tables:** <name: purpose> — or "none"
- **Changed tables:** <table.column: change, nullability, default>
- **Constraints/indexes:** <name, purpose, the query it serves>
- **Migration strategy:** <single migration | expand-migrate-contract>
- **Backfill needed:** <yes/no, approach, volume>
- **Retention/soft delete:** <policy, or "hard delete">

```text
<table_name>
  id            uuid  pk
  <column>      <type> <nullability> <default>
  created_at    timestamptz not null
```

## 8. API Contract [REQUIRED]

Base path `/api/v1`. Errors follow RFC 9457 (see `AGENTS.md` §9.1).

| Method | Path | Permission | Success | Errors |
|--------|------|------------|---------|--------|
| `POST` | `/requests` | `requests.create` | `201` | `401`, `403`, `409`, `422` |

**Request schema**

```json
{ "field": "type — constraints and meaning" }
```

**Response schema**

```json
{ "id": "uuid", "status": "draft" }
```

**Error catalogue**

| Code | HTTP | When |
|------|------|------|
| `request.duplicate_active` | 409 | <condition> |

**Idempotency:** <which endpoints accept `Idempotency-Key`, or "none">

## 9. UI / UX Notes [REQUIRED]

- **Screens/routes:** <route path → view name → purpose>
- **States:** empty / loading / error / partial — describe each explicitly.
- **Validation:** client-side rules, and how server `422` field errors are surfaced.
- **RTL & i18n:** new translation keys, numeral handling, direction-sensitive layout.
- **Accessibility:** keyboard flow, focus management, labels, `aria-live` usage.
- **Dates:** which values are Jalali in the UI, which timezone applies.

## 10. Edge Cases & Failure Modes [REQUIRED]

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| E1 | Two managers act on the same record simultaneously | <lock/constraint/conflict behavior> |
| E2 | Duplicate submission (double click, retry) | <idempotency/guard> |
| E3 | Out-of-scope identifier supplied | `404`, no existence leak |
| E4 | Expired/invalid token | `401` + client refresh flow |
| E5 | <timezone boundary / leap year / partial data> | … |

## 11. Non-Functional Requirements [REQUIRED]

- **Performance:** <p95 target for the new endpoints; expected row counts; index implications>
- **Security:** <specific risks, PII touched, rate limits, audit events emitted>
- **Observability:** <log events, metrics, what a failure looks like in logs>
- **Accessibility:** <WCAG criteria affected>
- **Compatibility:** <browser/viewport/API-version constraints>

## 12. Out of Scope & Follow-ups [REQUIRED]

- Out of scope: <item → why → candidate feature ID if known>
- Follow-ups: <new feature IDs to file in Task-List>

## 13. Open Questions [REQUIRED]

| # | Question | Owner | Needed by | Resolution |
|---|----------|-------|-----------|------------|
| Q1 | <question> | <name> | <date or gate> | Open |

**All questions must be resolved or explicitly deferred before status → `Approved`.**

## 14. Change Log

| Date | Change | By | Re-approved |
|------|--------|----|-------------|
| YYYY-MM-DD | Initial draft | <name> | — |
