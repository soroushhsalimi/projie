# ADR-0004 — Test-Driven Development as the default development method

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-11-19 |
| **Deciders** | Software Architect, Project owner |
| **Consulted** | — |
| **Supersedes** | none |
| **Superseded by** | none |
| **Related** | ADR-0002, ADR-0003, ADR-0006 |

## Context and Problem Statement

The project owner has mandated TDD. This ADR records **how** TDD is practised here, because "we do
TDD" is otherwise ambiguous: it can mean anything from "tests exist somewhere" to a disciplined
red-green-refactor loop that shapes the design.

The domain makes this decision consequential. The accommodation request lifecycle is a state machine;
bed allocation has a real concurrency invariant ("a bed is never actively assigned twice"); permissions
are security-relevant. These are exactly the areas where "write it, then test it" produces passing
tests that encode the implementation's bugs.

Constraints:

- A very small team (one developer + AI agents) — no dedicated QA.
- Development will be incremental over months, with long gaps between sessions; tests are the only
  reliable regression net and the primary way an agent recovers intended behavior.
- CI must be fast enough that the loop is actually followed when the suite grows.

## Decision Drivers

- Design quality: writing the test first forces interfaces to be usable from the outside.
- Regression safety for a system that must never double-allocate a bed.
- Executable specification: tests document behavior for future contributors and agents.
- Reviewability: a failing test plus its fix is easy to review; a large untested diff is not.

## Considered Options

1. **Strict TDD (red → green → refactor) per acceptance criterion, with a test pyramid and CI gates.**
2. Test-after development with a coverage threshold.
3. Manual/exploratory testing only for V1, automation later.
4. Behaviour-Driven Development with Cucumber-style Gherkin as the primary specification.

## Decision

**TDD is mandatory for all production code. Every behavior change begins with a failing automated
test that the author has personally observed failing for the expected reason.**

### The loop

1. **Red** — write the smallest test for the next acceptance criterion; run it; confirm it fails on the
   assertion (not on an import/collection error).
2. **Green** — write the minimum production code to pass; no speculative abstraction.
3. **Refactor** — improve names/structure with tests green after each micro-step.
4. **Commit** — one red→green→refactor unit per commit (Conventional Commit).

**Triangulation:** a general solution requires at least two tests that motivate it. A single test
justifies only the special case.

### Test levels and allocation

| Level | Tech | Backing services | Target share |
|-------|------|------------------|--------------|
| Domain unit | pytest, pure functions | none | ~45% |
| Service integration | pytest + real PostgreSQL (transactional) | DB | ~20% |
| API contract | `httpx.AsyncClient` against the app | DB | ~20% |
| Backend E2E journey | pytest, full modules | DB | ~5% |
| Frontend unit | Vitest + Vue Test Utils + MSW | none (MSW) | ~7% |
| Browser E2E | Playwright | full stack | ~3% |

Targets are guidance for effort allocation, not quotas to game. The rule: **use the cheapest level
that genuinely exercises the risk.**

### Non-negotiable test rules

- **No mocked database.** Integration tests use real PostgreSQL. A mocked repository proves nothing
  about SQL, constraints, or transaction behavior.
- **Mock only owned boundaries:** clock, email sender, object storage, third-party HTTP.
- **Deterministic:** injected `Clock`, seeded factories, explicit ordering, database isolation per test.
- **Negative cases mandatory:** every endpoint has wrong-role, wrong-scope, and invalid-input tests;
  every state transition has illegal-transition tests.
- **One behavior per test**, named `test_<subject>_<condition>_<expected>`.
- **No skipped tests.** A `.skip` / `@pytest.mark.skip` in committed code is a CI failure unless it
  references an open feature ID and an expiry note.

### Gates

- Coverage floors (CI-enforced): domain 95%, services 90%, backend overall 85%, frontend
  stores/composables/utils 80%, components 70%.
- New code may not reduce an existing scope's coverage.
- CI runs: lint → typecheck → unit → integration → contract → migration drift → e2e smoke.

### Test-first artifacts in the process

`PLAN.md` tasks must name **the failing test to write first** and the command that proves it. A task
without a named first test is not ready to start.

## Consequences

### Positive

- The state machine and allocation policy get designed from the caller's perspective, which is exactly
  where their complexity lives.
- Regressions in security and allocation are caught immediately — the two areas with the highest
  real-world cost.
- Tests double as executable documentation of the SPEC's `FR-n` items.
- Reviewers can reject "test-shaped" code (tautologies, implementation-coupled assertions) early.

### Negative

- Noticeably slower to deliver the first version of a trivial feature; the payoff is later.
- Poorly written tests become a maintenance burden and can lock in bad design — mitigated by
  contract-level assertions and review.
- Requires real PostgreSQL in CI and locally (Docker), raising setup cost.
- AI agents and humans can "cheat" by writing the test after the code; enforcement is cultural plus
  PR review, not mechanical.

### Neutral / Trade-offs accepted

- We accept a slow-ish integration layer (< 200 ms/test) in exchange for realistic SQL coverage;
  the fast unit layer keeps the inner loop tight.
- We accept some duplication between frontend `zod` schemas and backend Pydantic schemas; the contract
  test plus OpenAPI generation keeps them aligned without code sharing across languages.

### Follow-up actions

- [ ] F-0001: test harnesses (pytest + Vitest + Playwright), CI jobs, coverage gates in configuration.
- [ ] F-0001: `make test-unit` fast path documented and enforced under 30 s.
- [ ] F-0303: a dedicated concurrency test (two parallel allocations of the same bed) as a release gate.

## Alternatives Considered — Why Rejected

| Option | Why not chosen |
|--------|----------------|
| Test-after + coverage threshold | Coverage measures execution, not correctness; tests written afterwards tend to mirror the implementation, including its bugs — unacceptable for allocation and authorization. |
| Manual testing for V1 | No regression net across months of incremental work; impossible to verify permission matrices consistently; directly contradicts the owner's mandate. |
| Gherkin/Cucumber as primary spec | Heavy tooling and step-definition maintenance for a single-developer project; the SPEC + pytest naming already provide traceability without a second language. |

## Revisit Triggers

- Test suite wall-clock time exceeds ~5 minutes for the fast path → split suites, optimize fixtures,
  or introduce test impact analysis (keep the gate, change the mechanics).
- Mutation testing becomes affordable → add it for `domain/` to validate assertion strength.

## Verification

- **Automated:** CI enforces coverage floors, no-skip rule, and the full test job matrix.
- **Automated:** domain tests run in an environment without DB fixtures (guard test).
- **Review:** each PR's PLAN task must reference the first failing test; reviewers check that tests
  assert behavior, not internals.
- **Periodic:** suite duration and flakiness reviewed monthly; flaky test = defect.

## References

- Kent Beck, *Test-Driven Development: By Example*.
- Martin Fowler, *The Practical Test Pyramid*.
- ADR-0002 (layering makes domain tests cheap), ADR-0003 (frontend harness).
