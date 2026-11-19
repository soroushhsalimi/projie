# ADR-XXXX — <Short imperative title, e.g. "Use PostgreSQL as the primary datastore">

| Field | Value |
|-------|-------|
| **Status** | Proposed <!-- Proposed | Accepted | Superseded by ADR-YYYY | Deprecated --> |
| **Date** | YYYY-MM-DD |
| **Deciders** | <names/roles> |
| **Consulted** | <names/roles, or "none"> |
| **Supersedes** | <ADR-XXXX or "none"> |
| **Superseded by** | <ADR-YYYY or "none"> |
| **Related** | <SPEC-XXXX, PLAN-XXXX, other ADRs> |

## Context and Problem Statement

Describe the forces at play: the constraint, the requirement, the scale, the team, the deadline.
State the problem in **two to five sentences** as a question, e.g. "How do we guarantee that two
managers approving the same bed cannot both succeed?" Include only facts that actually constrain the
decision — no solution talk here.

Include, when relevant:

- Load/scale numbers you are designing for (and where they come from).
- The relevant existing decisions or constraints (link ADRs).
- What happens if we do nothing (the cost of the status quo).

## Decision Drivers

- <driver 1 — e.g. "p95 read latency under 300 ms with 10k beds">
- <driver 2 — e.g. "single maintainer, so operational simplicity outranks throughput">
- <driver 3 — e.g. "team already knows Python">

## Considered Options

1. **<Option A>**
2. **<Option B>**
3. **<Option C>**

*(At least two real options. An ADR with one option is a rationalization, not a decision.)*

## Decision

**We will <do X>.**

State it plainly and unambiguously. Then specify the parts that a future reader would otherwise have
to guess:

- Scope of the decision (what it covers and explicitly what it does not).
- Concrete configuration/conventions that follow from it.
- The rule that implementations must obey (this is what reviewers check).

## Consequences

### Positive

- <what gets better>

### Negative

- <what gets worse — be honest; every decision has a cost>

### Neutral / Trade-offs accepted

- <what changes but is neither good nor bad>

### Follow-up actions

- [ ] <action, owner, feature ID>

## Alternatives Considered — Why Rejected

| Option | Why not chosen |
|--------|----------------|
| <Option B> | <concrete reason, not "less popular"> |
| <Option C> | <concrete reason> |

## Revisit Triggers

Conditions under which this decision should be reconsidered, with the signal that would make us
notice:

- <e.g. "If a single dormitory exceeds 50k beds or p95 read latency exceeds 500 ms for two
  consecutive weeks → revisit partitioning (see ADR-0002).">
- <e.g. "If more than one organization requires isolated data → revisit multi-tenancy (deferred
  F-0505).">

## Verification

How compliance with this decision is checked in practice:

- Automated: <lint rule / CI job / test>
- Review: <what a reviewer must confirm>
- Periodic: <when this ADR is re-read>

## References

- <link>
