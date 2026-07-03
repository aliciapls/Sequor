# Repivot User Flows — Index (Director-Centric)

> The user-flow set for the **repivoted** Sequor (the governed agentic-services control layer). Every
> flow is written from a **director's** screen (a non-technical manager who approves/inspects/steers/
> corrects — never builds). Grounded in `briefs/02-repivot-to-saas-2.0.md` (the 7 value principles),
> `01-analysis/13-pitch.md`, and `01-analysis/12-saas-2.0-thesis.md` (evidence).
>
> **Supersedes** the original flows `03-user-flows/01`–`05` (kept for history), which assumed a
> worker-builds / states-an-objective framing. **Wedge (best-judgment, 2026-07-03):** comms lighthouse →
> mid-market/SMB departmental edge, with enterprise-compliance-grade audit built in from day one.

## The director's journey (flows in sequence)

**Set up** → R1 connect existing systems · R2 set governance/posture (before any work).
**Run** → R3 put an agent to work across ≥2 systems (plan surfaced + approved + traced).
**Oversee** → R4 rewind/change/re-run · R5 approve consequential actions at scale.
**Prove** → R6 export the audit bundle (the compliance SKU).
**Scale** → R8 one control surface across many systems + multiple directors.
**Validate (live now)** → R7 the comms lighthouse — the first live proto-director loop.

## Flow → value principles → features → deliverables

| Flow                                | Value principles                                  | Key features                                                                                                                                                                             | Key deliverables                                                              | Wedge                   |
| ----------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------- |
| **R1** Connect existing systems     | P1 integrate-not-replace, P5 neutrality           | delegated login (no password capture), connector catalog, least-privilege per-objective scoping, tenant isolation                                                                        | cross-vendor connected workspace + connection audit record (sealed tenant)    | all                     |
| **R2** Set governance & posture     | P3 governance-as-product, P4 meaningful oversight | plain-language policy editor, 3 postures (pause-approve / ask-once / supervise-by-exception), budgets, hard clearances, always-approve actions, safety-floor `min(chosen, system-floor)` | versioned, human-attributed governance policy that gates all work             | all                     |
| **R3** Agent work across ≥2 systems | P1, P2 director-not-builder, P7 trace             | intent box, plan-card approval before run, cross-system execution via connectors, governance between agent & each connector, least-privilege envelope, live glass-box trace              | completed cross-system work + full provenance trace (v1)                      | mid-market              |
| **R4** Oversee & intervene          | P4, P7 undo/trace                                 | timeline/trace UI, rewind-to-step, fingerprint-skip cascade, cost-preview before commit, re-run-vs-keep choice, versioning/compare/restore, intervention audit                           | version 2 + intervention audit record (honest v1 limit: linear, no branching) | mid-market              |
| **R5** Approve at scale             | P4 (the anti-rubber-stamp answer)                 | risk-ranked oversight queue, HITL (high-risk) / HOTL (rest), confidence scoring, exception-surfacing, batch-with-sampling, rubber-stamp-velocity meta-watch                              | approval decisions + accountability lineage; meaningful-oversight metrics     | mid-market → enterprise |
| **R6** Prove it (audit export)      | P3 governance-priced-as-compliance                | accountability lineage (action → named approver → posture → data → outcome), tamper-evident signed chain, plain-language + structured exports, EU AI Act Art. 14 mapping                 | exportable audit bundle (compliance-tier SKU)                                 | enterprise              |
| **R7** Comms lighthouse             | P2, P3, P4 + validates the bets                   | shipped comms pipeline mapped to director loop + persona/oversight instrumentation                                                                                                       | first live director loop + persona-validation metrics                         | comms (live)            |
| **R8** Cross-system control surface | P5 cross-vendor neutrality, P3                    | one unified queue/control/audit across Salesforce+ERP+ticketing+mail, accountability-routed + attributed approvals, four-eyes gates, single cross-SoR audit bundle                       | unified cross-SoR control surface + cross-system audit bundle                 | enterprise              |

## Consolidated feature catalog (the product surface)

**Connect:** delegated-login connectors · least-privilege per-objective scoping · tenant isolation · connector catalog.
**Govern (before run):** plain-language policy editor · 3-posture control · budgets · clearances · always-approve rules · safety floor · versioned attributed policy.
**Run:** intent box · plan-card (approve fan-out before execution) · cross-system execution · governance-between-agent-and-connector · least-privilege envelope · live glass-box trace.
**Oversee:** timeline/trace UI · rewind + fingerprint-skip cascade · cost-preview · re-run-vs-keep choice · versioning/compare/restore · risk-ranked approval queue · confidence scoring · exception surfacing · batch-with-sampling · HITL/HOTL tiering.
**Prove:** accountability lineage · tamper-evident signed audit chain · plain-language + structured audit export · EU AI Act Art. 14 mapping.
**Scale:** unified cross-SoR oversight/audit surface · multi-director coordination · attributed/routed approvals · four-eyes gates.

## Deliverables catalog (what the product produces for the director)

Connected workspace · connection audit record · versioned governance policy · provenance trace (versioned) · completed cross-system work · intervention audit record · approval decisions + accountability lineage · **exportable audit bundle (the compliance SKU)** · unified cross-SoR control surface · persona-validation metrics (from the comms lighthouse).

## Reuse → net-new (what the build inherits vs. must create)

- **Reuse (shipped):** PACT (approval/audit/envelopes), EATP (posture/budget), aegis (multi-tenant runtime), loom (governed distribution), csq (session engine), MCP connectors, the comms product.
- **Net-new (the concentrated build):** the **director control/oversight UI** (posture editor, approval queue, timeline/trace, audit export), the **reactive cross-system cascade/undo engine**, the **unified cross-SoR oversight+audit surface**, and the **EU AI Act Art. 14 export mapping**.

## Next → the product

These flows + features + deliverables re-scope the build. The existing capability roadmap
(`02-plans/02-capability-roadmap.md`) and 101-todo plan remain largely valid at the _mechanism_ level (M1
undo, M2 posture, connectors, audit) but must be **re-framed director-first and re-sequenced to the
comms→mid-market→enterprise wedge** before `/implement`. Recommended next step: a re-scoped `/todos` pass
that maps these flows' features/deliverables onto build shards — starting with the R7 comms-lighthouse
instrumentation (cheapest validation of the persona bet) and the R2+R3+R6 core loop (govern → run →
prove).
