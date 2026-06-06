# 00 — Executive Summary: The Agentic Work Platform

> The navigable entry-point to the `future-of-work` analysis package. Read this first; every claim
> below is developed in depth in the cited research (`01-research/`), analysis (`02`–`09`), plans
> (`../02-plans/`), user flows (`../03-user-flows/`), and target-state specs (`/specs/platform-*`).
> Status of the package after red team (`10-red-team/00-SUMMARY.md`): **SOUND and HONEST; brief fully
> covered (0 requirements missing, no scope creep); all BLOCKING/HIGH consistency defects fixed.**

## The vision in one paragraph

Today an enterprise worker is the **integration layer**: they swivel between ERP → CRM → POS → Excel →
Word → portals, carrying context in their head, re-keying data, gluing siloed systems together by hand.
The platform inverts this: the **agent becomes the integration layer**, and the human states intent and
governs. Every unit of work decomposes into an **objective** (the user's intent), a **process/procedure**
(company-specific, captured as reusable artifacts), and **data** (reached through connectors). One
agnostic, agentic interface — re-interfaced from the developer CLI harness for **all** knowledge work and
for **non-coders** — lets a worker get everything done without leaving it, with every step transparent,
governed, and reversible. It is also **team-oriented**: humans and agents co-work on one shared,
attributable substrate.

## Strategic verdict

The vision lands in a **crowded macro-category** ("agents do enterprise work") but a **genuinely sparse
intersection**. Almost every individual claim is asserted by someone; very few are delivered well; and
**nobody delivers the full combination in one agnostic, non-coder interface**. That combination is the
moat. Critically, **~80% of the substrate already exists** as shipped Terrene/Kailash ecosystem assets —
which is why this is buildable, not a from-scratch moonshot.

**Recommendation: pursue it — but win on the substrate, not the surface.** Do not compete on "an agent
finishes your deliverable in one interface" (Claude Cowork, GA April 2026, already owns that surface and
ships every ~2 weeks). Compete on the four substrate properties Cowork and the suite vendors have **not**
productized.

## The moat — a conjunction of four properties (M1–M4)

|        | Property                                                                                                                                                                 | Why it's defensible                                                                                         | Status                                                                                            |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **M1** | Transparent, **versioned, intervene-from-any-step** work — retrace any step, change it, only the genuinely-affected downstream re-executes, old outputs kept as versions | Exists only as a _developer_ primitive (durable execution / time-travel). **No non-coder product does it.** | **Lead the story.** Strongest moat **and** hardest build.                                         |
| **M2** | Execution-time, **posture-graded governance** — L3/L4/L5 chosen _beforehand_ per objective; approvals, budgets, clearance, emergency-bypass with audit                   | Native, execution-time governance vs bolt-on observability tools                                            | **Ship first.** Most-proven; reuses PACT/EATP/aegis.                                              |
| **M3** | **Multi-human + multi-agent** shared work substrate — signed coordination log, claims/leases, distinct-person gates                                                      | The _human-multiplicity_ half is rare (agent↔agent is commoditized by A2A)                                  | Rides underneath; reuses loom/aegis multi-operator.                                               |
| **M4** | Governed, versioned, **provenance-tracked cross-org artifact exchange**                                                                                                  | The _trust/provenance_ layer atop the commoditizing skills/MCP marketplace                                  | **Network-effects engine.** Reuses loom splitter; the untrusted-publisher trust model is net-new. |

**Foundation (table-stakes, not the headline):** agnosticism via MCP/A2A + multi-CLI parity (envoy).
Necessary connectivity that _enables_ M1–M4 — but connectivity alone is commodity; only **governed**
connectivity differentiates.

## The strategic decisions (consistent across the corpus)

1. **Lead the story with M1**, but **ship M2 first** as the foundation everything else stands on.
2. **Primary platform transaction = the published/consumed work-artifact (M4)**, fed by a secondary
   knowledge-contribution loop (already running live in the comms wedge).
3. **Lead the wedge's value with Augment** (of the AAA lens — Automate / Augment / Amplify): reducing
   _decision_ cost via posture-graded, provenance-backed judgment is differentiated against Cowork,
   demonstrable now, and load-bearing for correctness in a domain with no compiler to catch errors.
4. **Ignite network effects within-org first, then cross-org** — only after the untrusted-publisher
   trust model is designed.
5. **Comms is a subsumed wedge and instrumented lighthouse** (Decision A), not the product.
6. **Capability-first; GTM/beachhead deferred** (Decision B) — prove the disrupted-work capability before
   choosing where to sell it.

## What's built vs what's net-new (the 80/15/5)

- **~80% agnostic core already exists** as shipped ecosystem assets: loom (artifact splitter, variant
  overlays, proposal lifecycle, recall), PACT (D/T/R governance, envelopes, approval engine), EATP
  (TrustPlane/BudgetTracker/PostureStore), aegis (L1–L5 posture state machines, multi-operator
  coordination), envoy (multi-CLI parity), 400+ artifacts, **plus the deployed comms wedge**.
  _Honest caveat: primitives ≠ a finished product, and codegen primitives ≠ enterprise-work capability —
  the 80% is a head start, not a shortcut._
- **~15% client-configurable self-service** — each company's processes/procedures captured as artifacts,
  their connectors, postures, memory, roster. This is the **survival condition** against the ~95%-pilot-
  failure mode (generic tools that don't adapt to a company's workflow).
- **~5% true custom** + the genuinely net-new core builds, which concentrate the risk:
  **(a)** the non-coder self-service surface, **(b)** the M1 retrace/cascade engine, and **(c)** the
  design-first untrusted-publisher trust model.

## The honest bets and hard unknowns (do not gloss these)

- **The agent-comms hypothesis is unproven** (brief 3d: agent-mediated communication beats lossy
  human↔human). True for the _handoff_ layer; dangerous/false for the _relational/judgment_ layer. Treat
  as a **research bet to validate cheaply** (instrument the comms lighthouse), never sell it as fact.
- **M1 versioned cascade is the best moat _and_ the highest execution risk** — non-deterministic LLM
  steps make "re-run from step N" semantically tricky; the non-coder versioning UX is unsolved. v1 is
  deliberately reduced (linear retrace, reuse-recorded-output by default, no branching).
- **Non-coder depth is where no-code historically dies at "the last 20%"** — survivable only if
  transparency (M1) makes depth legible; this is the riskiest claim and must be proven, not asserted.
- **The agent-as-integration-layer concentrates blast radius** (one agent touching ERP+CRM+bank) and the
  "tools are dumb; the LLM reasons" principle that _enables_ transparency _also_ removes any deterministic
  layer between a prompt injection and an irreversible action — defense is **containment** (posture +
  envelopes + least-privilege per objective), not prevention.

## The "capability proven" demo (Decision B's falsifiable target)

A **non-coder** states an objective → the agent surfaces its plan on screen → the user picks a posture
beforehand → the agent executes across **≥2 formerly-siloed systems** → the output is delivered **traced,
interveneable, and versioned**, with the user able to retrace a step, change it, and watch only the
affected downstream re-run. Sequenced cheapest-decisive-falsifiers-first: the runtime-ownership spike and
single-step glass-box/replay come before the heavy builds.

## Brief coverage (red-team traceability)

**24 atomic brief requirements: 22 FULL, 1 PARTIAL, 0 MISSING; no scope creep.** The single PARTIAL —
agent↔agent transparency/intervenability (brief 3e) — is honestly deferred by design: v1 traces agent↔agent
_handoffs_ as ledger records; first-class interveneable agent↔agent _messages_ are post-v1 (see
`/specs/coordination-and-teams.md §6.5`).

**One brief correction to confirm:** the brief reads "D/T/R = Decision/Task/Review"; in the PACT
governance grammar **D/T/R = Department / Team / Role** (the addressing/accountability grammar). The specs
use the correct expansion — please confirm this matches your intent.

## The deliverable corpus (where to read more)

- `01-research/01–09` — grounded research (COC artifacts, multi-operator coordination, PACT, EATP/posture, CLI-harness thesis, transparency/versioning, competitive landscape, work-disruption thesis, comms-wedge mapping).
- `02-value-propositions` · `03-unique-selling-points` · `04-platform-model` · `05-aaa-framework` · `06-network-effects` · `07-transparency-intervention-architecture` · `08-product-focus-80-15-5` · `09-risks-failure-points`.
- `../02-plans/01-architecture` · `02-capability-roadmap` · `03-provenance-cascade-design` · `04-trust-posture-permissions-plan` · `05-comms-wedge-integration-plan`.
- `../03-user-flows/01-objective-to-output` · `02-intervention-retrace-cascade` · `03-team-collaboration` · `04-artifact-authoring-sharing` · `05-comms-wedge-flow`.
- `/specs/platform-*` (7 target-state specs) + `/specs/_index.md` (two-section: platform vision + shipped comms wedge).
- `10-red-team/00-SUMMARY` — the full findings ledger + dispositions.

## Recommended next step

Proceed to **`/todos`** to shard the capability roadmap into an execution plan. The red team's
**FIX-AT-TODOS** items (design-grade specs for the L7 work-interface and L2 runtime layers; the C4 cross-
system-reach and C6 untrusted-publisher design depth; retention/storage policies; the consequentiality-
classifier gating spike) are the natural first inputs to that phase. **Human approval gate**: does this
package cover everything you intended, and is anything here you did _not_ ask for?
