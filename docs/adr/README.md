# Architecture Decision Records (ADR)

Every architectural decision in SARA is recorded here **before** the code that depends on it is
merged. This folder is the institutional memory of the project: it answers *why* the system looks the
way it does, in a form that survives team changes.

## Rules

1. **One decision per file**, named `ADR-XXXX-<kebab-case-slug>.md`, IDs zero-padded and never
   reused.
2. **Immutable once `Accepted`.** You never rewrite an accepted ADR. To change your mind, write a new
   ADR that supersedes it, and update the `Superseded by` / `Supersedes` fields in both files.
3. **At least two real options** must be considered, with the rejected ones justified.
4. **Consequences are mandatory** — positive *and* negative. An ADR with no downside is marketing.
5. **Format:** MADR, using [`_TEMPLATE.md`](_TEMPLATE.md).
6. Link the ADR from the affected `SPEC`/`PLAN` and from the feature row in `Task-List.md`.

## When an ADR is required

Any decision that constrains future work:

- adding a dependency of consequence (framework, library, service, SaaS);
- defining or changing a module boundary, layer, or the dependency direction between them;
- a durable data-model decision (primary keys, soft delete, enums, tenancy, partitioning, indexing strategy);
- API shape decisions: versioning, error model, pagination, idempotency, breaking changes;
- authentication/authorization/session model;
- caching, background jobs, event delivery, or consistency strategy;
- date/time, locale, and i18n architecture;
- testing strategy and tooling;
- deployment topology, environments, observability.

If you are unsure whether something needs an ADR: **write a short one**. The cost of a page is far
lower than the cost of an unexplained decision six months from now.

## Lifecycle

```
Proposed ──▶ Accepted ──▶ Superseded by ADR-YYYY
    │                └──▶ Deprecated
    └──▶ Rejected
```

`Proposed` means "written, not yet signed off" — no code may depend on it. The Architect moves it to
`Accepted` (or `Rejected`) after review, usually in the PR that introduces the decision.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](ADR-0001-record-architecture-decisions.md) | Record architecture decisions | Accepted | 2026-11-19 |
| [0002](ADR-0002-backend-modular-monolith.md) | Backend as a modular monolith with layered feature slices | Accepted | 2026-11-19 |
| [0003](ADR-0003-frontend-vue-typescript-spa.md) | Frontend as a Vue 3 + TypeScript SPA with a generated API client | Accepted | 2026-11-19 |
| [0004](ADR-0004-test-driven-development.md) | Test-Driven Development as the default development method | Accepted | 2026-11-19 |
| [0005](ADR-0005-authentication-and-authorization.md) | Authentication and authorization model | Accepted | 2026-11-19 |
| [0006](ADR-0006-spec-plan-adr-workflow.md) | Spec → Plan → ADR gates for every feature | Accepted | 2026-11-19 |
| [0012](ADR-0012-local-and-test-database.md) | SQLite for local development and tests, PostgreSQL for production | Accepted | 2026-11-19 |
| [0013](ADR-0013-ui-primitives-and-tailwind.md) | Tailwind plus owned accessible primitives; PrimeVue deferred | Accepted | 2026-11-19 |

### Reserved IDs (not yet written)

Decision IDs 0007+ are pre-allocated so that references from `Task-List.md` remain stable. The ADR
must be written and `Accepted` **before** the feature that depends on it is implemented.

| ADR | Planned decision | Needed by |
|-----|------------------|-----------|
| 0007 | Audit logging & system settings model | F-0107, F-0402 |
| 0008 | Concurrency control for bed allocation (locking strategy, state machine ownership) | F-0302, F-0303, F-0304 |
| 0009 | Aggregation & caching strategy for dashboards and reports | F-0306, F-0401 |
| 0010 | Notification delivery & background job infrastructure | F-0307 |
| 0011 | Deployment topology & environment promotion | F-0405 |

`0012` and `0013` were written for the first delivered slice because the environment and the UI
foundation forced decisions earlier than planned. They are recorded in the index above; the reserved
IDs `0007–0011` remain stable.
