# ADR-0006 — Spec → Plan → ADR gates for every feature

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-11-19 |
| **Deciders** | Software Architect, Project owner |
| **Consulted** | — |
| **Supersedes** | none |
| **Superseded by** | none |
| **Related** | ADR-0001, ADR-0004 |

## Context and Problem Statement

The project owner has mandated that **every new capability must have a `SPEC.md` and a `PLAN.md`
before implementation, and every architectural decision an ADR**. This ADR records the mechanism that
makes that mandate enforceable rather than aspirational.

The real risk being managed is **ambiguity debt**. In a long project with changing context, a feature
that starts from a vague verbal description produces: unstated assumptions, missing edge cases,
scope creep, and a PR that cannot be reviewed against anything. Agents make this worse — they will
happily build a plausible interpretation of an under-specified request.

Constraints:

- One developer, so process must cost minutes, not days.
- The project owner acts as product owner and architect; approvals are single-person but **written**.
- Everything must live in the repository and be reviewable in a diff.

## Decision

**Every feature passes through four documentary gates — Intake, SPEC, PLAN, ADR — before the first
line of production code, and the status of each gate is recorded in `Task-List.md`.**

### The gates

| Gate | Artifact | Required content | Exit criterion |
|------|----------|------------------|----------------|
| G0 Intake | Row in `Task-List.md` | ID, persona, MoSCoW, milestone, dependencies, one-paragraph intent | Row accepted, status `Backlog` |
| G1 Spec | `docs/specs/SPEC-XXXX-<slug>.md` | Problem, goals/non-goals, personas, user stories, numbered FRs, Given/When/Then acceptance criteria, data impact, API contract, UI notes, edge cases, NFRs, out-of-scope, open questions | All sections complete; FRs testable; open questions resolved → `Approved` |
| G2 Plan | `docs/plans/PLAN-XXXX-<slug>.md` | Design summary, ordered TDD tasks (each naming its first failing test), test matrix, migration plan, rollout/rollback, risks, DoD checklist, progress log | Every task independently committable and verifiable → `Approved` |
| G3 ADR | `docs/adr/ADR-XXXX-<slug>.md` | Context, drivers, ≥ 2 options, decision, consequences, revisit triggers | `Accepted` before dependent code merges |

The gates are enforced socially and mechanically:

- **Social:** a PR whose feature row lacks SPEC/PLAN links is closed without review.
- **Mechanical:** a CI "docs check" validates that every feature with status `In Progress` or later
  has existing, `Approved` SPEC and PLAN files and that all referenced ADRs exist.

### Document lifecycle

```
Draft ──review──▶ Approved ──implementation──▶ Implemented
  ▲                    │
  └── change log ◀─────┘   (scope change: amend + re-approve, or write a superseding SPEC)
```

- Numbers are global and monotonic; `SPEC-0007` pairs with `PLAN-0007` but they are separate
  sequences in separate folders.
- A scope change amends the SPEC with a dated `## Change Log` entry and a re-approval; a scope
  *reversal* writes a new superseding SPEC.
- Documents are appended to, not rewritten: the progress log and change log are chronological.

### Why separate SPEC and PLAN (instead of one document)

They answer different questions and are written at different times:

- **SPEC** = *what and why* — stable, agreed with the "customer" (the project owner), changes rarely.
- **PLAN** = *how, in what order* — volatile, evolves as tests reveal reality, owned by the implementer.

Merging them causes the "how" to quietly redefine the "what". Separating them lets the PLAN change
daily without reopening requirements, and lets a reviewer check completeness against the SPEC while
checking executability against the PLAN.

### Why the Task-List is the index

Three artifacts per feature means someone must know *which* artifacts exist and *whether* they are
approved. `Task-List.md` is that index, and it is the only place status lives — one file to check, one
file to update. Statuses are defined in the file itself so they cannot drift.

## Consequences

### Positive

- Every implementation has a written, reviewable target; "is this done?" becomes a checklist, not an
  opinion.
- Edge cases and permissions are considered **before** code, when they are cheap to fix.
- AI agents get a bounded, explicit context; ambiguity is surfaced as an open question rather than
  invented behavior.
- Review becomes mechanical: check the diff against FRs and PLAN tasks.
- The document set is a usable onboarding package for a future contributor.

### Negative

- A trivial one-line feature still costs a SPEC and PLAN; the process is deliberately heavier than
  "just do it".
- Documentation can rot if statuses are not updated; mitigated by making the update part of the DoD
  and by the CI docs check.
- Writing a SPEC can feel like premature commitment; mitigated by allowing dated amendments.
- Two documents per feature plus ADRs is a lot of files at a glance; the Task-List index and naming
  convention keep it navigable.

### Neutral / Trade-offs accepted

- We keep one `Task-List.md` instead of a per-milestone board or an issue tracker; GitHub Issues may
  mirror it later, but this file remains authoritative.
- Approvals are single-signature (the owner/architect). With a larger team this would need a second
  approver — noted as a revisit trigger.

### Follow-up actions

- [ ] F-0001: implement the CI docs check (references resolve, statuses valid).
- [ ] Write `SPEC-0001` / `PLAN-0001` as the first exercise of this process.

## Alternatives Considered — Why Rejected

| Option | Why not chosen |
|--------|----------------|
| Single merged design doc per feature | Blurs requirements and implementation; the "how" silently rewrites the "what"; no independence between a frozen spec and an evolving plan. |
| Issue tracker only (GitHub Issues/Linear) | Fine for status, poor for long-lived design; lives outside the diff; no stable IDs to reference from commits and tests. |
| Informal chat-based planning | The status quo this project is explicitly rejecting; produces unrereviewable PRs and unstated assumptions. |
| Full RUP/waterfall documentation set | Radically too heavy for a one-developer incremental project; gates would be skipped entirely within a week. |

## Revisit Triggers

- If more than ~3 features per week flow through the process and documentation becomes the bottleneck →
  simplify the SPEC template for small (`S`-effort) features, keeping full gates for `M`/`L`.
- If the team grows beyond one implementer → require a second approver on `Approved` and add a
  review SLA.

## Verification

- **Automated:** CI docs check (files exist, header statuses valid, links resolve, Task-List references
  match existing files).
- **Review:** PR description must cite feature ID, SPEC link, and PLAN task IDs.
- **Periodic:** audit at each milestone boundary — every `Done` feature has `Implemented` SPEC/PLAN and
  every decision has an ADR.

## References

- ADR-0001 (ADR practice), ADR-0004 (test-first inside the PLAN).
- `AGENTS.md` §6 (gates), §7 (document standards), §15–16 (DoR/DoD).
