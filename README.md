# SARA — سامانه مدیریت خوابگاه خودگردان

**Self-Governed Dormitory Management System** — a web platform for managing dormitories that are run
by a community, cooperative, or private owner rather than a university housing office.

> **Project status: pre-foundation (M0).** The engineering process and decision records are in place;
> the application skeleton is the next step (`F-0001`). Commands below describe the intended
> developer experience and will become executable as M0 lands.

---

## What it does

| Role | Capabilities |
|------|--------------|
| **Admin** (ادمین) | Manage accounts and roles, system settings, audit oversight, system-wide monitoring |
| **Manager** (مدیر) | Manage dormitories, buildings, rooms, beds and capacities; review accommodation requests; check residents in and out (scoped to assigned dormitories) |
| **User** (کاربر) | Register and sign in, browse dormitories and rooms, submit and track accommodation requests |

The core value: replace paper ledgers and phone-based approvals with a traceable workflow that
guarantees a bed is never allocated twice, and answer "who changed what, when" for every record.

---

## Engineering docs — read in this order

| Document | Purpose |
|----------|---------|
| [`AGENTS.md`](AGENTS.md) | **The contract.** Rules, architecture, standards, TDD protocol, DoR/DoD, agent instructions |
| [`Task-List.md`](Task-List.md) | Authoritative feature backlog and status |
| [`docs/specs/`](docs/specs/) | What each feature must do (`SPEC-XXXX`) |
| [`docs/plans/`](docs/plans/) | How each feature is built, task by task (`PLAN-XXXX`) |
| [`docs/adr/`](docs/adr/) | Why the architecture is the way it is (`ADR-XXXX`) |

**The rule:** no feature is implemented before its `SPEC` and `PLAN` are approved. Every architectural
decision gets an `ADR`.

---

## Tech stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (async), PostgreSQL 16, Alembic, pytest
- **Frontend:** Vue 3, TypeScript (strict), Vite, Pinia, TanStack Query, Tailwind CSS + PrimeVue, Vitest, Playwright
- **Shared:** OpenAPI as the contract — the frontend client is generated from the backend schema
- **Locales:** Persian (`fa-IR`) first, full RTL, Jalali dates in the UI, UTC in storage

---

## Repository layout

```
apps/api    FastAPI backend (modular monolith, layered feature slices)
apps/web    Vue 3 SPA
docs        adr/ · specs/ · plans/ · diagrams/
scripts     cross-platform dev helpers
```

---

## Quick start (available once M0 is complete)

```bash
docker compose up -d postgres mailpit
uv sync --all-groups
pnpm install
make migrate && make seed
make dev          # API :8000 · Web :5173
```

Windows: use the PowerShell equivalents in `scripts/` if `make` is unavailable.

---

## Quality gates

TDD is mandatory: every behavior change starts with a failing test. CI blocks on lint, type checks,
test suites, coverage floors (domain 95%, backend 85%), migration drift, generated-contract drift, and
security audits. Details in [`AGENTS.md`](AGENTS.md) §8 and §14.

---

## License

TBD by project owner.
