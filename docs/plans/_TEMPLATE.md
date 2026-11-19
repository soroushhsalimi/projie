# PLAN-XXXX — <Feature title>

<!--
Copy this file to docs/plans/PLAN-XXXX-<kebab-slug>.md.
This document answers HOW and IN WHAT ORDER the SPEC will be satisfied. It is expected to change as
tests reveal reality; update the Progress Log rather than rewriting history.
See AGENTS.md §7.3 for the authoritative list of required content.
-->

| Field | Value |
|-------|-------|
| **ID** | PLAN-XXXX |
| **Feature ID** | F-0XXX |
| **Spec** | [`SPEC-XXXX`](../specs/SPEC-XXXX-<slug>.md) |
| **Status** | Draft <!-- Draft | Approved | In Progress | Implemented | Abandoned --> |
| **Owner** | <name> |
| **Estimate** | <S ≤ 1 day | M 2–3 days | L 4–5 days> |
| **Branch** | `feat/F-0XXX-<slug>` |
| **Created** | YYYY-MM-DD |

---

## 1. Design Summary [REQUIRED]

5–15 lines: the approach at a glance. Enough that a reviewer understands the shape of the change
before reading tasks. Name the modules, tables, endpoints, and components that will be created or
modified, and the key design choice (and which ADR covers it).

## 2. Assumptions & Preconditions [REQUIRED]

- [ ] Feature's dependencies are `Done` (list them).
- [ ] Required ADRs are `Accepted`.
- [ ] <environment/tooling availability>

## 3. Work Breakdown [REQUIRED]

Ordered, independently committable tasks. **Every task states the failing test to write first** — a task
without one is not ready. Keep tasks small enough for one reviewable commit.

### T1 — <task title>

- **First failing test:** `<path>::<test name>` — asserts <expected behavior>
- **Command to see it fail:** `uv run pytest <path> -k <expr> -q`
- **Files:** `<paths created/modified>`
- **Covers:** FR-1, AC-1
- **Verify:** `uv run pytest <path> -q && uv run mypy apps/api`
- **Notes:** <edge cases handled here, or "none">

### T2 — <task title>

- **First failing test:** …
- **Files:** …
- **Covers:** …
- **Verify:** …

<!-- Repeat for T3..Tn. Order tasks so that the system is green after each one. -->

## 4. Test Plan [REQUIRED]

| Behavior | Unit | Integration | Contract | E2E | Notes |
|----------|:----:|:-----------:|:--------:|:---:|-------|
| FR-1 <behavior> | ✓ | | ✓ | | |
| FR-2 <behavior> | | ✓ | ✓ | ✓ | |

**"One thing that would prove this is broken" (write a test for each):**

1. <failure scenario that would slip through happy-path tests>
2. …

**Negative cases required:** wrong role, wrong scope, invalid input, illegal state transition,
concurrent modification.

**Frontend:** <component/store tests, MSW handlers, Playwright journey or "none">

## 5. Data & Migration Plan [REQUIRED]

- **Revisions:** `<revision slug>` — <what it does>
- **Expand → migrate → contract:** <steps, or "single non-destructive migration">
- **Rollback of data:** <possible? how?> or "N/A — additive only"
- **Seed data updates:** <what changes in `db/seeding/`>
- **Query-count / index checks:** <queries added, indexes added, `EXPLAIN` evidence>

## 6. Rollout & Rollback [REQUIRED]

- **Flag:** <feature flag name and default state, or "no flag needed because …">
- **Deploy order:** <migration → API → web, etc.>
- **Rollback:** <exact steps and data implications>
- **Monitoring after deploy:** <what to watch for the first hour>

## 7. Risks & Mitigations [REQUIRED]

| # | Risk | Likelihood | Impact | Mitigation | Trigger signal |
|---|------|:----------:|:------:|------------|----------------|
| R1 | <risk> | M | H | <mitigation> | <how we would notice> |

## 8. Definition of Done (feature-specific) [REQUIRED]

- [ ] All ACs verified (manual + automated evidence recorded below).
- [ ] Coverage gates pass for touched scopes.
- [ ] Negative tests present for permissions/scope/transitions.
- [ ] Migration applied on a copy of realistic data; drift check clean.
- [ ] OpenAPI regenerated; web client regenerated; no unintended contract diff.
- [ ] i18n keys added for both locales (or documented fallback); RTL verified.
- [ ] Keyboard/a11y pass on new screens.
- [ ] Task-List updated (status + PR link); SPEC status → `Implemented`.
- [ ] <feature-specific item>

## 9. Progress Log [REQUIRED — append only]

| Date | Task | Status | Evidence / notes |
|------|------|--------|------------------|
| YYYY-MM-DD | T1 | done | `pytest tests/unit/test_x.py -q` → 4 passed |
