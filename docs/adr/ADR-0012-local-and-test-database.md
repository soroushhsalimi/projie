# ADR-0012 — SQLite for local development and tests, PostgreSQL for production

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-11-19 |
| **Deciders** | Software Architect |
| **Consulted** | Project owner |
| **Supersedes** | none |
| **Superseded by** | none |
| **Related** | ADR-0002, SPEC-0001, SPEC-0002, SPEC-0003 |

## Context and Problem Statement

`AGENTS.md` names PostgreSQL 16 as the database and requires integration tests to run against a real
database, never a mock. The development machine for this milestone has no Docker daemon, no local
PostgreSQL server, and cannot install one. Blocking every feature until that changes would stop the
project; using an in-memory fake would violate the testing doctrine.

We need a database that:

- runs with zero external services on Windows;
- supports the SQLAlchemy async stack and real transactions;
- keeps the production path (PostgreSQL) viable without a rewrite.

## Decision Drivers

- Reproducibility from a clean checkout (`AGENTS.md` R11).
- Tests must exercise real SQL, constraints and transactions.
- No divergence in application code between environments.
- Production correctness (concurrency, partial indexes) must not be compromised silently.

## Considered Options

1. **SQLite (aiosqlite) for local development and the test suite; PostgreSQL remains the production
   target and the only accepted database for concurrency-critical verification.**
2. In-memory repositories or a mocked session for tests.
3. Require PostgreSQL/Docker and pause delivery until it is available.
4. Use SQLite in production as well.

## Decision

Use **SQLite via `aiosqlite`** for local development and automated tests, selected by
`SARA_DATABASE_URL` (default `sqlite+aiosqlite:///./sara.db`). Production and staging use
PostgreSQL through `postgresql+asyncpg://`. Application code uses only portable SQLAlchemy 2.0
constructs: `Uuid`/string identifiers, `DateTime(timezone=True)`, explicit constraint names, no
dialect-specific SQL, and no reliance on database-generated defaults.

Tests create a fresh SQLite database per test (a temporary file, not a shared in-memory database), so
constraints and transactions are real and test-order independent.

## Consequences

### Positive

- A contributor can run the full stack and the test suite with no container runtime.
- Real SQL and real constraints are exercised; tests still catch uniqueness and transaction bugs.
- The production dialect remains a configuration change, not a code fork.

### Negative

- SQLite does not enforce the same concurrency semantics as PostgreSQL. `SELECT ... FOR UPDATE`,
  partial unique indexes and `ON CONFLICT` behavior must be verified on PostgreSQL before the
  allocation features (F-0303) ship.
- Type affinity differences can hide bugs (e.g. naive datetimes, `NUMERIC`).
- The test suite is not a substitute for a Postgres CI job.

### Neutral / Trade-offs accepted

- `AGENTS.md` §8.3 ("integration tests run against real PostgreSQL") is satisfied in spirit (real
  database, real SQL) but not in letter for this milestone. The deviation is temporary and tracked.

## Follow-up Actions

- [ ] `F-0405`: add a PostgreSQL service to CI and run the integration suite against both dialects.
- [ ] Before `F-0303` (allocation concurrency): add PostgreSQL-specific tests for the partial unique
      index and row locking.
- [ ] Revisit this ADR when Docker or a managed Postgres instance is available; supersede rather than
      edit it.

## Revisit Triggers

- Any feature whose correctness depends on `FOR UPDATE`, partial indexes, `jsonb`, or `citext`.
- A production deployment decision.
- Test flakiness attributable to SQLite locking.

## Verification

- The same migration and repository code runs on both dialects (checked manually in F-0405).
- `tests/integration` uses a file-backed SQLite database and asserts real constraint violations.
- CI fails if a model uses a SQLite-only type.

## References

- SQLAlchemy 2.0 dialect documentation (SQLite and PostgreSQL).
- `AGENTS.md` §8.3, §9.3.
