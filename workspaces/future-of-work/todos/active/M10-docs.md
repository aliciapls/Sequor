# M10 — Documentation (cross-cutting)

> **What this milestone builds (plain language).** The words that let real people use, run, and govern
> the platform: a README + user-facing docs for the non-coder surface (state an objective, pick a
> freedom-level, read a trace, rewind a step — with zero code and zero jargon), operator/admin docs for
> the people who set the platform's posture/governance/roster, connector-authoring docs for whoever
> wires a new business system in (under the "tools are dumb endpoints, the LLM reasons" discipline), the
> spec-maintenance discipline that keeps `specs/` describing what the system actually does today, and
> the capability-proven-demo runbook that anyone can follow to reproduce the end-to-end walk.
>
> **Scope boundary (important).** M10 documents the cross-cutting surfaces — the non-coder product, the
> operator/admin posture, the connector-authoring contract, the spec discipline, and the demo runbook.
> Per-feature internal design docs live with their feature milestones. M10 does NOT restate the
> mechanism of a canonical artifact (a command/rule/skill/hook): it references it by path + section per
> `rules/specs-authority.md` Rule 9, so there is one source of truth and no silent drift.
>
> **Two framing rules carried throughout.** (1) Plain language for a non-technical audience: every
> technical term is translated on first use; choices are framed as business impact with a
> recommendation, never a code snippet or unexplained jargon (per `rules/communication.md`,
> `rules/recommendation-quality.md`). (2) Docs describe what SHIPS, not what is planned: a spec/user-doc
> citing a function/endpoint/behavior must resolve against working code; gap-trackers and Phase-1/Phase-2
> split-state framings are BLOCKED in spec content (per `rules/spec-accuracy.md`) — forward plans live in
> todos/issues, not in the truth surface.

---

## Dependency posture for this milestone

- **M10 is cross-cutting and spans the whole build.** The spec-maintenance discipline is needed from the
  first feature milestone (specs stay current at first instance of a change, not batched late); the
  non-coder + operator + connector docs land as their surfaces become usable; the demo runbook can only
  be finalized once the M7 composition exists. So M10's todos land incrementally alongside the feature
  milestones.
- **M10 documents, it does not re-build.** The surfaces, governance, connectors, and demo are owned by
  M0–M9. M10 owns the words: the README + non-coder user docs, the operator/admin docs, the
  connector-authoring docs, the spec-maintenance discipline, and the capability-proven-demo runbook.
- **The demo runbook is load-bearing for testing.** The docs-exact end-to-end regression (M8-6) runs the
  walk EXACTLY as the runbook teaches it — so the runbook and the regression test are two views of one
  contract; drift between them breaks the regression. M10-5 and M8-6 are paired.
- **Out of /todos scope (GTM deferred per Decision B).** The Decision-D "honest carry-forward" — that
  external-facing / GTM material frames agent-mediated comms as a **founding conviction, not an
  established fact** — is a go-to-market messaging obligation, deferred with the rest of GTM per Decision
  B; it is NOT a M10 build todo (M10 documents the shipped product surfaces, not market positioning).

---

### M10-1 — README + user-facing docs for the non-coder surface

- **Type:** DOC
- **Implements:** specs/platform-overview.md §6 (non-coder principle) + §3 (agnostic interface) (+ `rules/communication.md`; `rules/recommendation-quality.md`)
- **What:** Write the README + the user-facing docs a non-technical person reads to use the platform:
  how to state an objective in plain language, how to pick a freedom-level from the three plain buttons
  ("Step through" / "Ask me once" / "Go ahead"), how to read the live trace, and how to rewind a step
  and compare versions — with zero code, zero jargon, and every term translated on first use. Choices
  are framed as business impact with a recommendation.
- **Reuses → Builds:** the comms product's non-technical onboarding docs (a proven plain-language
  pattern) → the platform's non-coder README + user docs.
- **Invariants:** plain language, every technical term translated on first use (no unexplained jargon,
  no code snippets to a non-coder); choices framed as impact with a recommendation + symmetric
  pros/cons; docs describe shipped behavior only (no Phase-1/Phase-2 split-state framing, no
  gap-trackers — per `rules/spec-accuracy.md`); CLI-neutral prose (no CLI-native tool nouns or baseline
  filenames as authority — per `rules/cross-cli-artifact-hygiene.md`).
- **Sizing:** ~1 cycle.
- **Depends on:** M2 (the non-coder surface the docs describe must exist).
- **Acceptance (confirm / falsify):** **Confirm:** a non-coder follows the README to state an objective,
  pick a posture, read a trace, and rewind a step — with no code and no untranslated jargon — and a
  legibility probe (M8-5) over the docs-guided walk passes. **Falsify:** the docs require the reader to
  understand a code snippet or an unexplained term, OR they describe a behavior that does not ship
  (citation fails to resolve against working code).

### M10-2 — Operator / admin docs (posture, governance, roster)

- **Type:** DOC
- **Implements:** specs/trust-posture-and-governance.md §posture + §governance + specs/coordination-and-teams.md §roster (+ `rules/communication.md`; `rules/recommendation-quality.md`)
- **What:** Write the docs for the people who administer the platform: how to set the trust posture and
  the safety floor, how to configure governance (envelopes, clearance, the plan-approval gate, the
  break-glass override — the now-built `EmergencyBypass` capability from M1-19 (build/wire onto the
  comms hot path) + M1-20 (Tier-2 wiring test), so this doc describes a capability that actually ships
  rather than a referenced-but-unbuilt primitive), how to manage the roster and the distinct-person
  approval gates, and how to run the SHADOW→enforce rollout. Written in business terms with
  recommendations, not implementation prose.
- **Reuses → Builds:** the governance/posture/roster surfaces (M1) + the SHADOW→enforce mechanism
  (M9-6) → the operator/admin docs.
- **Invariants:** plain language + recommendations for every admin decision (impact-framed, not
  jargon-dumped); references canonical artifacts by path + section, does NOT restate their mechanism
  (per `rules/specs-authority.md` Rule 9); describes shipped behavior only (no gap-trackers); no
  secrets/credentials in any example (per `rules/security.md`).
- **Sizing:** ~1 cycle.
- **Depends on:** M1 (governance/posture/roster), **M1-19 + M1-20 (the break-glass `EmergencyBypass` build/wire + Tier-2 wiring test the override docs describe)**, M9-6 (SHADOW→enforce).
- **Acceptance (confirm / falsify):** **Confirm:** an operator follows the docs to set a posture +
  safety floor, configure a governance envelope, manage the roster's distinct-person gates, and run a
  SHADOW→enforce flip — each decision framed as business impact with a recommendation. **Falsify:** the
  docs restate a canonical artifact's mechanism (drift source) instead of referencing it, OR describe an
  admin capability that does not ship, OR leak a credential in an example.

### M10-3 — Connector-authoring docs (the dumb-endpoints discipline)

- **Type:** DOC
- **Implements:** specs/connectors-and-integration.md §MCP-connector-framework + §governed-connectivity (+ architecture §7.2; `rules/agent-reasoning.md`)
- **What:** Write the docs for whoever authors a new connector (wiring a business system in as a tool):
  the "tools are dumb endpoints, the LLM reasons" contract (a tool MUST be `get_order(id) → record`,
  never `handle_order_issue(...)` with business logic buried inside), the OAuth/least-privilege security
  model, and how governance sits between the agent and the connector (a write to a system of record can
  be HELD until a human approves). This is what keeps the transparency contract holdable as new systems
  are added.
- **Reuses → Builds:** the MCP connector protocol + the M3 governed-curation pattern → the
  connector-authoring docs.
- **Invariants:** the dumb-endpoints discipline is stated as the load-bearing contract (no decision
  logic in tool code — per `rules/agent-reasoning.md`); least-privilege per objective documented as the
  default; governed-connectivity (governance between agent and connector) documented; no
  secrets/credentials in any example; describes shipped connector behavior only.
- **Sizing:** ~1 cycle.
- **Depends on:** M3 (the connector framework the docs teach).
- **Acceptance (confirm / falsify):** **Confirm:** a connector author follows the docs to wire a new
  system as a dumb-endpoint tool, scoped least-privilege, with governance between agent and connector —
  and the resulting connector keeps all reasoning in the logged model I/O (no logic in tool code).
  **Falsify:** the docs permit (or fail to forbid) business logic in tool code (breaking the
  transparency contract), OR teach a connector pattern that does not match what ships.

### M10-4 — Spec-maintenance discipline (specs stay current)

- **Type:** DOC
- **Implements:** specs/\_index.md (+ `rules/specs-authority.md` Rules 4/5/5b/6; `rules/spec-accuracy.md`)
- **What:** Establish and document the spec-maintenance discipline so `specs/` stays the single source
  of domain truth: phases read `_index.md` then the relevant spec before acting; a spec is updated at the
  FIRST instance domain truth changes (not batched); a spec edit triggers a full sibling-spec
  re-derivation sweep; specs describe ONLY shipped behavior (no gap-trackers, no Phase-1/Phase-2
  split-state — those go to todos/issues); deviations from spec are explicitly acknowledged. This is the
  discipline that keeps every other doc and every delegation prompt working from current truth.
- **Reuses → Builds:** the existing `specs/_index.md` + the specs-authority + spec-accuracy rules → the
  documented, enforced spec-maintenance discipline.
- **Known phantom citation to correct at the first spec-maintenance pass (spec-accuracy Rule 1):** the
  M7-8 todo cites `specs/business-model.md §design-partner`, but `business-model.md` has **no**
  `§design-partner` section (verified: its sections are Pricing, Per-Message Overages, Conversion,
  Economics, Per-Query RAG Pricing, **Channel Partner Model**, Geographic Expansion, Unit Economics,
  Key Assumptions, Cost Baseline — "Channel Partner Model" is resellers, not design partners). The
  design-partner concept is the **lighthouse instrument** (roadmap §11.2 C7b / `specs/platform-overview.md`
  §capability-proof), not a business-model section. Fix: drop the phantom `§design-partner` anchor from
  the M7-8 citation, keeping the real `specs/platform-overview.md §capability-proof` anchor (or describe
  the design-partner lighthouse in plain terms) — no `business-model.md` section is the correct target.
- **Invariants:** specs organized by domain ontology, not process; updated at first instance of change
  (staleness window forbidden); sibling re-derivation on every spec edit; spec content cites only
  working code (citations resolve via grep/ast/find — per `rules/spec-accuracy.md` Rule 1); no
  gap-trackers / split-state framings in spec content; deviations acknowledged, not silent.
- **Sizing:** ~1 cycle.
- **Depends on:** none (foundational discipline; applies from the first feature milestone onward).
- **Acceptance (confirm / falsify):** **Confirm:** the spec-accuracy audit protocol runs clean — zero
  split-state framings, every cited symbol resolves against working code — and a worked example shows a
  spec updated at the first instance of a change with the sibling sweep performed. **Falsify:** a spec
  ships a citation that fails to resolve (phantom citation), OR carries a gap-tracker / Phase-1/Phase-2
  framing, OR a domain-truth change was batched instead of updated at first instance.

### M10-5 — The capability-proven-demo runbook

- **Type:** DOC
- **Implements:** specs/platform-overview.md §3.3 (six-property acceptance test) + §capability-proof (+ roadmap §12; M7 milestone; `rules/user-flow-validation.md`)
- **What:** Write the runbook that lets anyone reproduce the end-to-end capability-proven walk: the
  exact steps (state the objective → pick "Ask me once" → approve the surfaced plan → watch the
  two-system execution traced live → rewind a step, read the cost-preview, choose re-run vs replay →
  compare v1 vs v2), what the user should SEE at each step, and the honest omissions (no user-facing
  branching, no cross-org sharing, no team layer — those are still bets). The runbook is the DOCS-EXACT
  source the end-to-end regression (M8-6) executes — so they are two views of one contract.
- **Reuses → Builds:** the M7 composed demo segments + the four-property walk (roadmap §12.2) → the
  capability-proven-demo runbook.
- **Invariants:** the runbook is DOCS-EXACT with the M8-6 regression (drift between them breaks the
  regression); plain language, every term translated; describes the shipped walk only (the honest
  omissions stated, not staged); receipts (verbatim steps + what the user saw + disposition) per
  `rules/user-flow-validation.md`; CLI-neutral prose.
- **Sizing:** ~1 cycle.
- **Depends on:** M7 (the composed demo), M8-6 (the docs-exact regression it is paired with).
- **Acceptance (confirm / falsify):** **Confirm:** a reader follows the runbook to reproduce the
  end-to-end walk and sees all four properties hold; the M8-6 regression runs the runbook's exact steps
  green on real infrastructure (runbook and regression match). **Falsify:** the runbook drifts from the
  M8-6 regression (the test runs different steps than the docs teach), OR it stages an omitted feature
  (branching/cross-org/team) as if it ships.

---

## Milestone-level acceptance

The documentation layer is **proven** when: a non-coder can use the platform from the README with no
code and no untranslated jargon (legibility probe passes); an operator can set posture/governance/roster
and run a SHADOW→enforce flip from the admin docs; a connector author can wire a new system under the
dumb-endpoints discipline from the connector docs; the spec-maintenance discipline keeps `specs/`
describing only shipped behavior (spec-accuracy audit clean, every citation resolves); and the
capability-proven-demo runbook lets anyone reproduce the end-to-end walk AND is docs-exact with the
M8-6 regression. Every doc references canonical artifacts rather than restating them (no drift), frames
choices as business impact with recommendations, and describes what ships — never what is planned.
