# ADR-0001 — Record architecture decisions

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-11-19 |
| **Deciders** | Software Architect |
| **Consulted** | Project owner |
| **Supersedes** | none |
| **Superseded by** | none |
| **Related** | ADR-0006, all ADRs |

## Context and Problem Statement

SARA is a multi-milestone project built by a very small team (initially one developer plus AI agents),
over months, with a large surface area: three roles, a state machine, concurrency-sensitive allocation,
authentication, and a Persian/RTL UI. The people making decisions will not be the same people — or the
same model context — that later maintains the code.

In such a project, the failure mode is not "we picked the wrong library". It is **"nobody remembers
why this is the way it is"**, which leads to accidental reversal of deliberate choices, duplicated
mechanisms, and rewrites.

Facts that constrain us:

- No corporate wiki, no dedicated architect after hand-off: decisions must live **in the repository**,
  under version control, next to the code they govern.
- AI agents participate in development and have no persistent memory across sessions; they must be
  able to recover context from files alone.
- Markdown is the only documentation format that survives tool changes, renders in every editor, and
  diffs cleanly.

## Decision Drivers

- Decisions must be discoverable and reviewable by both humans and agents.
- History must be preserved: understanding the *sequence* of decisions matters as much as their content.
- Zero additional tooling: no external service, no proprietary format, no build step.

## Considered Options

1. **ADR files in `docs/adr/` (MADR format), versioned with the code.**
2. A wiki / external knowledge base (Notion, Confluence).
3. Design documentation inside code comments and docstrings.
4. A single growing `ARCHITECTURE.md` document.

## Decision

**We will record every architectural decision as an immutable, numbered ADR in `docs/adr/`, using the
MADR format defined in `docs/adr/_TEMPLATE.md`.**

Conventions that follow from this:

- File name: `ADR-XXXX-<kebab-case-slug>.md`, four-digit zero-padded, monotonically increasing.
- Required sections: Context, Decision Drivers, Considered Options (≥ 2), Decision, Consequences
  (positive/negative/neutral), Alternatives rejected, Revisit triggers, Verification.
- Status values: `Proposed → Accepted → Superseded / Deprecated`.
- An ADR becomes `Accepted` **before** merge of the code that depends on it.
- Accepted ADRs are never edited. A reversal creates a new ADR with `Supersedes: ADR-XXXX`, and the
  old one gains `Superseded by: ADR-YYYY`.
- IDs are never reused or renumbered, even if an ADR is rejected.
- The index in `docs/adr/README.md` is updated in the same PR that adds an ADR.

## Consequences

### Positive

- Every "why" question has a durable, linkable answer that survives team and tool changes.
- Reviewers can challenge a decision at the moment it is made, in writing, instead of re-litigating it
  later in code review.
- AI agents can reconstruct architectural intent from files, which makes their output far more
  consistent.
- Git history provides the timeline for free; no separate tracking system to maintain.

### Negative

- Writing an ADR costs 20–40 minutes, and it is tempting to skip it for "obvious" choices.
- ADRs can rot if nobody reads them; the index and links mitigate but do not eliminate this.
- Immutability means outdated ADRs remain visible; readers must check the `Status` field first.

### Neutral / Trade-offs accepted

- MADR is slightly heavier than the original Nygard one-page template. We accept ~1 extra page per
  decision in exchange for explicit drivers, alternatives, and revisit triggers.
- ADR numbering is global, not per-area — a deliberate simplification that avoids parallel numbering
  schemes.

### Follow-up actions

- [x] Create `docs/adr/_TEMPLATE.md` and `docs/adr/README.md` (done with this ADR set).
- [ ] Each future `SPEC`/`PLAN` links its ADRs; `Task-List.md` has an `ADR` column for the same reason.

## Alternatives Considered — Why Rejected

| Option | Why not chosen |
|--------|----------------|
| Wiki / external knowledge base | Lives outside the repo, drifts from the code, inaccessible to agents, no code review, migration risk. |
| Comments/docstrings only | Cannot express alternatives and rejected options; invisible in a PR; scattered across files; no lifecycle. |
| Single `ARCHITECTURE.md` | Becomes an unmaintainable 2000-line document; merge conflicts on every decision; no stable IDs to link from SPECs. |

## Revisit Triggers

- If ADR count exceeds ~200 and discoverability suffers → introduce a lightweight index by area
  (still Markdown, still in-repo).
- If the team grows beyond ~5 people → consider requiring a second approver on `Accepted` status.

## Verification

- **Automated:** `docs check` in CI verifies every ADR linked from `Task-List.md` / `AGENTS.md` exists
  and has a valid `Status` header.
- **Review:** a PR that introduces a durable choice without an ADR is rejected.
- **Periodic:** re-read the index at each milestone boundary (M0…M4).

## References

- Michael Nygard, *Documenting Architecture Decisions* (2011).
- MADR — Markdown Any Decision Records, <https://adr.github.io/madr/>.
