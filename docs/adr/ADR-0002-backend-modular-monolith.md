# ADR-0002 — Backend as a modular monolith with layered feature slices

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-11-19 |
| **Deciders** | Software Architect |
| **Consulted** | Project owner |
| **Supersedes** | none |
| **Superseded by** | none |
| **Related** | ADR-0003, ADR-0004, ADR-0005 |

## Context and Problem Statement

The backend must serve a dormitory management domain with three roles, a request workflow, an
allocation/residency lifecycle with strict "never double-book a bed" semantics, and administrative
oversight. Expected V1 scale: a handful of dormitories, hundreds to a few thousand residents,
thousands of beds; peak traffic measured in tens of requests per second, not thousands.

Constraints:

- **One developer** (plus AI agents) must build, deploy, and operate it.
- The domain has real transactional invariants (bed allocation) and an explicit state machine.
- The team has chosen **FastAPI** (Python) and wants a relational database with strong constraints.
- The project must remain changeable: the risk is not traffic, it is *design drift* — business rules
  leaking into HTTP handlers, SQL leaking into controllers, tests becoming impossible to isolate.

The question: what architectural style and internal structure should the API have?

## Decision Drivers

- Operational simplicity for a single maintainer (one deployable, one database).
- Testability: domain rules must be unit-testable without HTTP or SQL.
- Correctness under concurrency for allocation.
- Clear seams so a future extraction (e.g., notifications service) is mechanical rather than a rewrite.
- Mandatory test coverage (ADR-0004) is only feasible if logic is reachable without I/O.

## Considered Options

1. **Modular monolith**: one FastAPI app, feature modules, layered internals, one PostgreSQL database.
2. Microservices per bounded context (auth, catalog, requests, allocations) with HTTP/message contracts.
3. Framework-driven monolith: FastAPI routers holding all logic, SQLAlchemy models as the domain,
   Pydantic schemas doubling as entities.
4. Serverless functions per endpoint with a managed database.

## Decision

**We will build a single FastAPI application structured as a modular monolith of vertical feature
slices, with a strict layered dependency rule inside each slice and a single PostgreSQL 16 database.**

### Module boundaries

`auth`, `users`, `dormitories`, `rooms` (buildings/rooms/beds), `requests`, `allocations`,
`notifications`, `admin` (settings/audit/reports). Each module owns:

```
modules/<name>/
├── router.py      # HTTP mapping only
├── schemas.py     # Pydantic request/response DTOs
├── service.py     # use cases, transaction boundary, authorization
├── repository.py  # queries + ORM↔domain mapping
├── models.py      # SQLAlchemy ORM models
└── events.py      # domain events emitted by this module
```

Cross-module interaction happens **only** through a module's `service.py` public functions or via
domain events. Importing another module's `repository`, `models`, or tables is forbidden.

### Layer dependency rule

```
router → service → domain
             ↓
         repository → models → PostgreSQL
```

- `domain/` is pure Python: entities, value objects, policies, the request state machine. No
  SQLAlchemy, no FastAPI, no `datetime.now()` (a `Clock` port is injected).
- `service.py` may import FastAPI **types** only for dependency-injection annotations it does not
  actually use; it must not raise `HTTPException` or touch `Request`. Domain errors are raised and
  mapped to HTTP once, in the exception-handling middleware.
- `repository.py` never commits; the service owns the unit of work (one request = one transaction).
- `router.py` performs no business logic and no ORM access.

### Persistence and data decisions

- **PostgreSQL 16** as the only stateful component; `citext` for emails; `timestamptz` everywhere;
  UUID primary keys (see follow-up on UUIDv7).
- Business invariants are enforced **twice**: in the domain layer (explicit, tested errors) and by
  database constraints (partial unique index for active allocations, FKs, `CHECK`s). The database is
  the last line of defence, not the first.
- Alembic for migrations; unique partial index plus `SELECT ... FOR UPDATE` where the SPEC identifies a
  race (details in ADR-0008).

### Enforcement

- `import-linter` contracts in CI: layers may only import inward; modules may not import each other's
  repositories/models.
- Review checklist item: "does any business rule live in a router or a repository?"
- A layer violation is a blocking comment, not a style preference.

## Consequences

### Positive

- One artifact to build, deploy, monitor, and debug — proportionate to a single-maintainer project.
- Domain logic (state machine, allocation policy) is testable as pure functions at < 5 ms per test,
  which makes the mandated 95% domain coverage realistic.
- Transactional integrity for allocation comes free from a single database; no distributed saga.
- Module seams make later extraction (notifications, reporting) a refactor of wiring, not a redesign.
- Fewer moving parts means the TDD loop (ADR-0004) stays fast enough to actually be followed.

### Negative

- No independent scaling or deployment of modules; a memory leak in reporting affects login.
- One schema means one migration stream; schema changes must consider all modules.
- Module boundaries are conventions enforced by tooling, not by the network — discipline is required,
  and a determined contributor can still couple modules.
- A single process is a single failure domain; availability depends on process supervision.

### Neutral / Trade-offs accepted

- We accept ~3 extra files per feature (service/repository/schemas) versus a "fat router" approach, in
  exchange for testability and a stable seam.
- We accept some indirection between ORM models and domain entities (explicit mappers) rather than
  using ORM models as domain objects.
- Microservices remain an option, not a plan; extraction requires a new ADR and a measured constraint.

### Follow-up actions

- [ ] F-0002: implement app factory, error model, and `import-linter` contracts.
- [ ] F-0005: establish PK/timestamp/enum conventions and the Alembic baseline.
- [ ] ADR-0008: decide the concurrency mechanism for allocation before F-0303.

## Alternatives Considered — Why Rejected

| Option | Why not chosen |
|--------|----------------|
| Microservices | Distributed transactions for bed allocation, N deployments, N observability setups, and a much slower TDD loop — all for traffic this system will never see. Reversible later via module extraction. |
| Framework-driven monolith (logic in routers, ORM as domain) | Rules become untestable without HTTP+DB, the state machine degrades into scattered `if`s, and coverage targets become unattainable. This is the exact failure mode we are avoiding. |
| Serverless per endpoint | Cold starts hurt the admin UX; local development and end-to-end testing become painful; connection pooling to Postgres is awkward at this scale; no benefit for a low-traffic internal tool. |

## Revisit Triggers

- Sustained p95 read latency > 500 ms for two weeks on catalog endpoints → revisit indexing first, then
  read models/caching (ADR-0009).
- A module needs an independent release cadence or a different scaling profile (e.g. export/PDF
  generation) → consider extraction of that module only, with a new ADR.
- More than one organization requires isolated data → revisit multi-tenancy (deferred F-0505).

## Verification

- **Automated:** `import-linter` contracts (layer + module independence) run in CI on every PR.
- **Automated:** domain tests must run with no database fixtures available (a fixture-usage guard test).
- **Review:** every PR touching `router.py` is checked for business logic; every PR touching
  `repository.py` is checked for commits/transactions.
- **Periodic:** module dependency graph regenerated and reviewed at each milestone boundary.

## References

- ADR-0004 (TDD), ADR-0005 (auth), ADR-0008 (allocation concurrency, planned).
- Martin Fowler, *Patterns of Enterprise Application Architecture* — Separated Domain Layer, Repository.
- *Modular monolith* as described by Simon Brown; vertical slice architecture.
