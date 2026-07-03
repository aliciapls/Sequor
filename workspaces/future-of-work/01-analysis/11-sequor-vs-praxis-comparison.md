# 11 — Sequor vs. Praxis: Strategic Comparison

> **What this is.** A side-by-side comparison of the Sequor agentic-work-platform vision (this
> workspace) against the sibling project **Praxis** (`~/repos/dev/praxis`, Integrum /
> praxis.integrum.global). Produced 2026-07-03 from a **user-authorized, read-only** reconnaissance of
> the Praxis repo (`cross-repo-authorized: dev/praxis`; no writes were made to Praxis). Evidence cites
> Praxis file paths for traceability only. This doc informs **Sequor's** positioning; it proposes no
> work in Praxis.
>
> **Headline finding:** Sequor and Praxis are **two expressions of the same vision, by the same
> founder, on the same substrate.** The strategic question is therefore not "how do we build Sequor" but
> "**should Sequor exist separately from Praxis at all?**" — which gates whether `/implement` should
> begin (see workspace `.session-notes` item **F4**).

## 1. What Praxis is (as found)

Praxis is an **all-in-one enterprise work environment that replaces the SaaS suite** — "work,
communicate, build, and a marketplace, in one place" — where a non-coding domain worker puts a
workforce of AI agents on their real production work and turns their expertise into **"mini-programs"**
(named, reusable units of work) (`praxis: workspaces/praxis-strategy/drafts/worker-builds-apps/07-verified-flows-content.md`).

- **Defining paradigm:** "governed free-form codegen" — a Cognitive-Orchestration harness _wrapped
  around_ frontier codegen agents, positioned between raw vibe-coding (fast, unsafe) and 2000s low-code
  (safe but caged). Safety comes from the harness wrap, never from caging the agent.
- **Value thesis:** "governance-as-DNA → production throughput at organizational scale." Regulatory
  liability (EU AI Act, PLD, California AB 316) is the _why-buy-now door, never the value_
  (`praxis: plans/i-want-a-unicorn-ancient-lake.md`). Closing line: "You keep the accountability; we give you the proof."
- **Domain / audience:** regulated EU enterprise knowledge work (banking, insurance, healthcare);
  explicitly **non-coders**; COO/CFO economic buyer, CISO is the gate; ~$60–250K ACV, 6–9 month cycle.
- **Substrate (this is the crucial part):** built entirely on the founder's own **Kailash/Terrene**
  stack — CARE/EATP/PACT/CO specs, **loom** (author-once governed distribution), **Kailash** (Rust+Py
  build engine), **csq** (multi-CLI/multi-provider session engine), **aegis** (governed multi-tenant
  agentic-OS runtime), **envoy** (edge provenance). Per the recon: **aegis, loom, csq, Kailash are
  shipped/running with real paying enterprise customers**; the all-in-one _non-coder surface_ is
  **net-new with zero pilots** (`praxis: ledger/0052-praxis-evolves-master-plan.md`, `ledger/0051-praxis-launch.md`).
- **Stage:** git history is a single initial commit; no product application code yet. Only a static
  marketing/architecture presentation is live. The engines beneath it are shipped.

## 2. Convergence — the two visions are nearly identical

| Sequor pillar                                             | Praxis equivalent                                                                                                           | Match            |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| Non-coders do **all** work in one place                   | "All-in-one environment that replaces the SaaS suite"; non-coder create-experience                                          | Near-identical   |
| Agent-driven work interface                               | csq main agent the worker directs; "AI executes / human judges" law                                                         | Near-identical   |
| Every step **traced / transparent**                       | Signed append-only CareChain audit + verification gradient (`AutoApproved/Flagged/Held/Blocked`) + exportable proof bundles | Strong           |
| **Posture-graded governance**, autonomy chosen beforehand | EATP/PACT declared operating envelopes → "no mid-stream permission prompts"; trust-posture L1–L5                            | Strong           |
| **Multi-human + agent** coordination                      | Multi-operator, org-scale, claims/coordination-log substrate                                                                | Strong           |
| **Versioned** work                                        | loom capability graduation + proof-freshness pins + canon versioning                                                        | Moderate–strong  |
| **Reusable work-recipes**                                 | "mini-programs" (named reusable work units) + marketplace                                                                   | Strong (concept) |
| Model/harness **agnostic**                                | csq cross-model / multi-provider portability                                                                                | Match            |

**The asymmetry that matters:** Praxis is **further along on the substrate** (shipped engines, paying
customers) but at the **same greenfield stage on the actual non-coder surface** (zero pilots). Sequor's
own analysis says "~80% of the substrate already exists" — **that 80% _is_ the Praxis substrate.** So
Sequor and Praxis are competing to build the _same_ net-new surface on the _same_ shared foundation.

## 3. Divergence — where Sequor genuinely differs

These are the only real differentiators, and they are the crux of whether Sequor warrants separate
existence.

1. **Cross-org recipe sharing (Sequor's M4) — direct conflict.** Sequor's network-effects engine is
   _governed cross-organization_ sharing of work-recipes. **Praxis deliberately KILLED this** on legal
   grounds: cross-employer capability transfer was judged "legally fragile," the marketplace was cut to
   **intra-enterprise only** (employer-as-publisher), and the "sovereign two-sided clearing network" is
   dead and stays dead (`praxis: ledger/0052`). **Implication:** Sequor's M4 revives a bet the same
   founder already examined and rejected — it needs hard re-scrutiny before any build.
2. **Integrate the silos (Sequor) vs. replace the suite (Praxis).** Sequor frames the agent as the
   _integration layer over existing_ ERP/CRM/portals. Praxis frames itself as _replacing_ the SaaS
   suite ("instead of adding another tab to it"). Genuinely different architecture and go-to-market bet
   — and arguably the strongest candidate for a _distinct_ Sequor identity (serving firms that will not
   rip-and-replace their systems).
3. **First-class rewind / re-run (Sequor's M1 signature).** Sequor's headline is step-level
   _interveneable_ work: rewind to any step, change it, re-cascade only what's affected, keep versions.
   Praxis achieves human control via **gate-approval + compulsory re-eval + never-inherit-unproven** —
   the same _goal_ (human correction) but **no first-class time-travel/rewind primitive** was found.
   This is Sequor's cleanest original idea.
4. **Framing: governance-first (Sequor) vs. value/throughput-first (Praxis).** Same machinery, inverted
   emphasis — Praxis leads with production throughput and treats governance as the by-product; Sequor
   foregrounds transparency/trace/governance as the headline.
5. **Stack depth / scope.** Praxis is a heavy, vertically-integrated stack (own Rust SDK, runtime,
   published specs, foundry, certification bench) aimed narrowly at regulated EU enterprises. Sequor as
   specified reads as a lighter, broader interface/coordination layer.

## 4. Recommendation (single rec + symmetric pros/cons)

**Consolidate to one thesis — do not run two overlapping products.** They compete for the same net-new
surface on the same substrate, and one founder cannot fund/focus both.

- **Recommended — Sequor as a positioning/pivot exploration _inside_ the Praxis program.** Keep
  Sequor's three genuine differentiators (integrate-over-silos, first-class rewind, and a _reconsidered_
  cross-org story) and fold them into the Praxis substrate that already ships.
  - _Pros:_ inherits real engines + paying customers instead of rebuilding; ends the duplication;
    concentrates one founder's focus; Sequor's rewind primitive and integrate-over-silos angle become
    genuine upgrades to Praxis rather than a parallel effort.
  - _Cons:_ Sequor loses independent identity/brand; you must resolve the **replace-vs-integrate**
    tension explicitly (they are contradictory theses); the Sequor 101-todo plan would be re-scoped, not
    executed as-is.
- **Alternative — keep Sequor separate ONLY with a named wedge Praxis structurally cannot serve.** The
  most defensible such wedge: _integrate-existing-silos_ for organizations that refuse to replace their
  suite (Praxis's replace-the-suite thesis structurally excludes them).
  - _Pros:_ a distinct market and a clean story; avoids re-litigating Praxis's internal decisions.
  - _Cons:_ duplicated build and split focus for one founder; shares a substrate, so the "separation" is
    largely marketing; still must resolve M4's legal question independently.
- **Regardless of choice — re-examine M4.** Praxis's own legal conclusion is direct evidence that
  cross-org sharing is the riskiest of Sequor's four pillars; treat it as a research/legal question to
  settle before it is designed, not a settled moat.

**This is the founder's strategic call.** This doc surfaces it with evidence; it does not decide it.

## 5. What this gates

The reconciliation decision (F4 in `.session-notes`) **precedes** `/implement`. Building Sequor's M0
spikes before deciding the Praxis relationship risks re-building a surface on a substrate the founder
already owns — the exact duplication this comparison surfaces. Sequor's own `08-product-focus-80-15-5`
"80% already exists" finding is the tell: that 80% has a name, and it is Praxis's engines.

## 6. Sources

- **Sequor (this workspace):** `00-EXECUTIVE-SUMMARY.md`, `03-unique-selling-points.md`,
  `08-product-focus-80-15-5.md`, `02-plans/02-capability-roadmap.md`, `briefs/01-vision.md`.
- **Praxis (read-only, user-authorized 2026-07-03):** `README.md`;
  `workspaces/praxis-strategy/CLAUDE.md`;
  `workspaces/praxis-strategy/drafts/worker-builds-apps/07-verified-flows-content.md` (product model);
  `.../06-technical-architecture-grounding.md` (stack); `.../08-praxis-strategy.md` (deep strategy);
  `.../plans/i-want-a-unicorn-ancient-lake.md` (master plan); `.../ledger/0052-praxis-evolves-master-plan.md`
  (current strategic state — incl. the cross-org kill decision); `.../ledger/0051-praxis-launch.md`
  (what is actually live).
