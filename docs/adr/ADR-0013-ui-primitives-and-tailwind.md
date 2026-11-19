# ADR-0013 — Tailwind plus owned accessible primitives for the V1 UI; PrimeVue deferred

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-11-19 |
| **Deciders** | Software Architect |
| **Consulted** | Project owner |
| **Supersedes** | none |
| **Superseded by** | none |
| **Related** | ADR-0003, SPEC-0001, SPEC-0002, SPEC-0003 |

## Context and Problem Statement

`AGENTS.md` names Tailwind CSS **and** PrimeVue as the frontend styling stack. The first delivered
slice is authentication: two forms, a split marketing panel, an authenticated landing page, and a
404 page. PrimeVue is a full component suite with a theming system; adopting it now means committing
to its design language, its RTL behaviour, and its upgrade cadence before we know which components
the product actually needs.

The UI must be Persian-first, RTL, accessible (WCAG AA), responsive from 360 px, and visually
distinct enough to represent a real product rather than a framework demo.

## Decision Drivers

- RTL and Persian typography must be correct out of the box.
- Accessibility is easier to guarantee with a small number of primitives we fully understand.
- Bundle size and build time matter on a modest student project.
- The design must be coherent across auth, dashboard, and future catalog screens.
- Avoid a dependency whose theme would have to be fought in every screen.

## Considered Options

1. **Tailwind CSS + a small set of owned, accessible primitives (`FormField`, `PasswordField`,
   `AlertBanner`, `BrandMark`, `AuthShell`) and design tokens. PrimeVue is deferred until a screen
   needs a complex widget (data table, date picker, combobox) that justifies it.**
2. PrimeVue for every control, including text inputs and buttons, themed with a custom preset.
3. A different component library (Vuetify, Naive UI, shadcn-vue).
4. No utility framework; hand-written CSS modules only.

## Decision

Use **Tailwind CSS 3** with a single design-token layer in `src/styles/main.css` and a small set of
owned components. PrimeVue is **not** installed in this slice. It may be introduced later through a
new ADR, but only for controls where building an accessible implementation is more expensive than
adopting one (for example a virtualized data table or a Jalali date picker).

The primitives follow these rules:

- every control is labelled with `<label for>` and receives `aria-invalid` / `aria-describedby`;
- errors are rendered next to the field and announced with `aria-live="polite"`;
- focus is never removed, and route changes/errors move focus deliberately;
- all colours come from the token palette; no ad-hoc hex values in components;
- logical CSS properties (`ms-`, `me-`, `ps-`, `pe-`, `start-`, `end-`) are used exclusively.

## Consequences

### Positive

- Full control over RTL spacing, Persian line lengths, and the visual identity.
- No theme override layer, no version lockstep with a component suite.
- The bundle stays small: the production auth build is ~68 kB gzip total JS.
- Accessibility decisions are visible in code and testable with Vue Test Utils.

### Negative

- We own the accessibility and keyboard behavior of every primitive; a future data grid or date
  picker will be expensive to build correctly.
- No ready-made design system documentation for new contributors.
- Tailwind class strings can become long; the design-token layer mitigates but does not eliminate it.

### Neutral / Trade-offs accepted

- `AGENTS.md` remains the target architecture; this ADR records a deliberate, limited deviation for
  V1. When PrimeVue (or another suite) is adopted, this ADR is superseded rather than edited.
- The `AGENTS.md` stack table should be read together with this ADR.

## Follow-up Actions

- [ ] Revisit before building the manager dashboard/table screens (F-0302, F-0306); if a table
      library is needed, write a new ADR covering it.
- [ ] Add an axe-based accessibility check to CI when the Playwright harness lands.
- [ ] Document the primitives in `docs/design-system.md` once a third screen uses them.

## Revisit Triggers

- A screen needs a virtualized table, date range picker, combobox, or file upload with preview.
- An accessibility audit finds a defect that a maintained library would have prevented.
- The team grows beyond one frontend owner and needs a shared component contract.

## Verification

- Unit tests cover field error wiring (`aria-describedby`, `aria-invalid`) and password validation.
- Manual keyboard walkthrough of `/login` and `/register`.
- Production build and `vue-tsc --noEmit` are part of the feature gate.

## References

- `AGENTS.md` §10 (frontend standards).
- WAI-ARIA Authoring Practices (forms, alerts).
