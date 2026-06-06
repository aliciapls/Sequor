# 08 — Product Focus: The 80/15/5 Reuse Split

> Analysis output for the Agentic Work Platform (`/analyze`, Phase 01).
> Addresses `briefs/01-vision.md` §6 (the 80/15/5 reuse breakdown) and the Phase-A
> strategic spine (M1–M4 moat, Decisions A + B).
>
> **Grounding rule.** Every claim below cites a research file in this workspace's
> `01-research/` directory or the brief. Where a claim is an inference or a genuine
> uncertainty, it is flagged inline. Effort is in **autonomous execution cycles/sessions**,
> never human-days (per `rules/autonomous-execution.md`). Competitors are named factually,
> never as a product Sequor is "a version of" (per `rules/independence.md`).

---

## 0. What this document decides (in plain language)

When you build a product for many customers, the most expensive mistake is building the
**same thing twice** because it looked custom each time. The opposite mistake is promising
"one platform fits everyone" and then discovering every customer needs a developer to make
it work — which doesn't scale past a handful of clients.

The 80/15/5 split is the discipline that avoids both. It sorts every piece of the platform
into three buckets:

- **80% — the agnostic core.** Built once. Every customer, every kind of work, gets the
  exact same code. This is the platform's engine.
- **15% — client self-service.** The parts that genuinely differ company-to-company — their
  procedures, their connected systems, their approval rules. These MUST be things a
  non-technical operator configures themselves, with no engineering. If they can't, the
  product doesn't scale.
- **5% — true custom.** The genuinely one-off work: a brand-new connector to an obscure
  system, a regulated industry's bespoke controls. Real, but rare, and kept rare on purpose.

> **CANONICAL 80/15/5 STATEMENT (this document is the authority for the split; cite this
> sentence verbatim).** The platform splits into **80% agnostic reusable core** (built once,
> identical for every client and every kind of work), **15% client self-service**
> (configurable by a non-technical operator with zero engineering), and **5% true custom**
> (genuinely one-off, external, non-generalizable). The three numbers are approximate
> proportions of the platform's surface by reusability, and they always sum to 100.

**The headline finding: roughly 80% of this platform's core already exists — but "exists" means
the building blocks (primitives) exist, NOT that the finished product exists; codegen primitives
are not the same as enterprise-work capability.** The 80% is working, deployed, or specced code
across the Terrene ecosystem (loom, PACT, EATP, aegis, envoy) and inside the existing Sequor
communication product. The platform's job is overwhelmingly **assembly and re-pointing**, not
invention. The genuinely-new build is small, concentrated, and identifiable.

**The single most important caveat, carried throughout:** "80% exists" is true at the level
of _primitives_ (the building blocks); primitives ≠ finished product, and codegen primitives
≠ enterprise-work capability. The hard, scary 5% — the untrusted-publisher trust
model and the step-level retrace engine — is where the real risk lives, and it is exactly
the part the Phase-A spine names as the strongest moat (M1, M4). Existence of primitives is
not the same as a finished product. This document is honest about that seam.

---

## 1. How the buckets are defined (the sorting rule)

The split is by **reusability across clients and kinds of work**, not by build effort
(research 09 §5, framing note). A component lands in a bucket by answering one question:

| Bucket                      | The question that places a component here                                                                                        |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **80% Agnostic core**       | "Is this identical for an invoice-reconciliation job and a quarterly-report job, for client A and client B?" If yes → core.      |
| **15% Client self-service** | "Does this vary company-to-company (the brief's point 1b) BUT require zero code to change?" If yes → self-service.               |
| **5% True custom**          | "Is this genuinely one-off — external policy, a novel system, a regulator's text — that cannot be generalized?" If yes → custom. |

The brief's own decomposition of all work into **(a) an objective, (b) company-specific
processes, (c) data** (`briefs/01-vision.md` §1) maps cleanly onto the buckets: the
_machinery_ that runs any objective is the 80% core; the _company-specific processes_ (point
1b, "these vary from company to company") are the 15% self-service surface; and only the
genuinely external residue is the 5%.

**Why point 1b is the load-bearing self-service surface.** Independent market evidence
(research 07, cited in the spine): MIT's NANDA study found ~95% of enterprise GenAI pilots
fail because generic tools "don't learn from or adapt to workflows," and Gartner projects

> 40% of agentic projects cancelled by 2027. The common failure is the same: the tool can't
> absorb _this company's_ way of working without an engineer. If point 1b (company-specific
> process) is custom engineering, the platform inherits the 95%-failure mode. If point 1b is
> **self-service configuration captured as artifacts and memory**, the platform escapes it.
> This is why the 15% MUST be self-service — it is not a convenience, it is the survival
> condition.

---

## 2. The 80% — the agnostic reusable core

This is the platform spine: built once, serves every client and every kind of work. The
table below is the **concrete inventory** — each core capability, the existing ecosystem
asset that already implements it, and the research file proving it exists.

| #   | Core capability (plain language)                                                                                          | Existing asset (the evidence it's ~built)                                                                                                              | Maturity                                                            | Source                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- | ---------------------------------------------- |
| 1   | **The work engine** — the loop that reasons, acts, checks, repeats, for any task                                          | The agent CLI harness loop (`reason→act→verify`); domain-neutral by construction                                                                       | Shipped (commercial harnesses) / specced (Kaizen native)            | 05 §1.1, §2                                    |
| 2   | **The artifact system** — agents/skills/rules/hooks/commands as the unit of reusable know-how                             | loom's five-layer system: **39 agents, 36 skills (405 skill files), 70 rules, 30 hooks, 41 commands, 499 variant files**                               | Shipped, runs in production for codegen                             | 01 §1, §1a–1e                                  |
| 3   | **Trust & posture (graduated autonomy)** — choose how much the agent does alone, per job, beforehand                      | EATP `PostureStateMachine` + `PostureStore`; PACT `posture_enforcer`→verdict; aegis L1–L5 signed anchors                                               | Shipped (3 independent implementations)                             | 04 §0, §1, §2.4                                |
| 4   | **Governance (permission envelopes + approval gates)** — budgets, clearance, "pause and ask," emergency-bypass-with-audit | PACT engine: `SupervisorOrchestrator`→HELD callback→`ApprovalBridge`→`EventBridge`; 17 DataFlow models; `EmergencyBypass`                              | Shipped end-to-end with web dashboard                               | 03 §5, §6, §7                                  |
| 5   | **Transparency / accountability (D/T/R)** — every action traced to a person                                               | PACT D/T/R address grammar (`accountability_chain`); comms `AuditEntry` append-only log                                                                | Shipped (both general + vertical forms)                             | 03 §2; 09 §2.3                                 |
| 6   | **Provenance & versioning** — old outputs kept, every step has a signed record                                            | EATP signed Audit-Anchor hash-chain (aegis `anc-posture-*.json`); PACT `AgenticArtifact.version` + `parent_artifact_id`; envoy two-phase signed ledger | Shipped (anchors, version model, ledger spec)                       | 04 §4.5; 03 §6.1; 05 §3.3                      |
| 7   | **Human↔agent feedback loop** — corrections become durable knowledge                                                      | COC `/codify`→artifact loop; comms learning-from-human-answers (`learning.py`)                                                                         | Shipped (both forms)                                                | 01 §3; 09 §2.2                                 |
| 8   | **Multi-human + multi-agent coordination** — many people and agents share one work substrate safely                       | loom multi-operator-coordination: signed coordination log, claims/leases, distinct-person gates; PACT pools/routing                                    | Shipped (the human-multiplicity half)                               | 05 §6.1; multi-operator-coordination substrate |
| 9   | **MCP connector framework** — any business system reached as a tool, with governance in between                           | MCP (OAuth 2.1, >1,000 connectors); "tools are dumb endpoints" discipline; PACT approval-between-agent-and-connector                                   | Standard protocol shipped; discipline specced                       | 05 §1.4, §5                                    |
| 10  | **Cross-org artifact registry** — create/modify/store/share artifacts across companies, with recall                       | loom splitter: two-gate `/sync`, variant overlays, proposal lifecycle, obsoletion/recall, disclosure-scrub                                             | Shipped for one org's 30+ consumers; cross-_org_ is the adapt layer | 01 §2, §7                                      |
| 11  | **Multi-CLI parity** — the same artifact runs on any harness (table-stakes, not headline)                                 | envoy + loom cross-CLI emission: neutral-body byte-identical, examples may diverge, bijection enforcement                                              | Shipped (CC/Codex/Gemini)                                           | 01 §6; 05 §4.1                                 |

**The evidence for "80% already exists" is this table — but it is evidence the _primitives_
exist, not that the finished product exists; codegen primitives ≠ enterprise-work capability.**
Eight of eleven rows are shipped,
running code; the remaining three (cross-org registry, native work-engine, connector
discipline) are specced with shipped foundations. None of the eleven is conceptually
comms-specific or codegen-specific — each is needed identically for a "reconcile invoices"
job and a "produce the 3Q report" job (research 09 §5.1, "why these are the 80%").

### 2.1 Where the comms wedge's components land in the 80%

Decision A (`briefs/01-vision.md` §4) subsumes the existing Sequor communication product as a
wedge. Its working, deployed components are **already instances** of the core primitives
above (research 09 §2) — which is the proof the spine works against real users and real data:

| Comms component (deployed, Vercel + Neon)                  | The core capability it instantiates                                                           |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Confidence badges + 3-tier routing (`response.py:103-123`) | Trust & posture (#3) — N=3 fixed bands; the platform generalizes to user-chosen L1–L5 per job |
| `AuditEntry` append-only log (`db/audit.py`)               | Transparency / D/T/R (#5) — already PDPA-clean, PII-free by design                            |
| Learning-from-human-answers (`learning.py`)                | Human↔agent feedback (#7) — captures the residue of human correction                          |
| Schema-per-tenant isolation (`schema_manager.py`)          | The isolation half of multi-org boundary (part of #10) — passes Singapore PDPA                |
| Escalation chain + SLA scheduler (`escalation/*`)          | Coordination (#8) — the hand-off precursor to a shared team substrate                         |
| Email/WhatsApp/BSP adapters, document parsers              | Connectors (#9) — the inbox is one data source; an ERP is another                             |
| Routing flywheel (cross-tenant anonymized aggregates)      | Knowledge compounding (part of #7)                                                            |

**Recommendation (comms → core placement): REUSE the comms spine as-is; do not rebuild it as
part of the platform.** The comms primitives are the platform's de-risking evidence; ripping
them out to "do it properly" discards working proof. The cons are stated symmetrically in §6.

---

## 3. The 15% — client-configurable self-service

This is the **"processes vary company-to-company" surface** (brief 1b). It MUST be
self-service — configurable by a non-technical operator with zero engineering — or the
platform inherits the 95%-pilot-failure mode (§1). The good news: the comms onboarding wizard
already proves a non-technical person can configure this layer in under 10 minutes with no app
(research 09 §1.7, §5.2).

| Self-service surface (plain language)                | Comms proves it (deployed)                                     | Generalizes to                            | Captured as                                |
| ---------------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------ |
| **Their processes** — how this company does the work | Per-account routing rules + escalation chain + template A/B/C  | Any company procedure for any objective   | Artifacts (skills/rules/commands) + memory |
| **Their connectors** — which systems to plug in      | Which channels (email/WhatsApp), which inbox, which BSP number | Which systems (ERP/CRM/Drive/calendar)    | MCP server selections                      |
| **Their postures** — how much autonomy, per job      | Confidence threshold per account                               | Per-objective L1–L5 chosen beforehand     | Posture records (re-keyed to objective)    |
| **Their memory/knowledge** — what the company knows  | Uploaded docs + accumulated learned answers                    | Their domain knowledge base per objective | Knowledge store + learned artifacts        |
| **Their roster/governance** — who approves what      | Backup contacts, escalation tiers, owner emails                | Team roster + who-approves-what (D/T/R)   | Roster + approval config                   |

**Why self-service is achievable, not aspirational.** Every row above is already _data or
configuration_ in the comms product — none is code (research 09 §5.2). The onboarding wizard
is literally the self-service surface for the comms slice; the platform's job is to generalize
the wizard from "configure comms coverage" to "configure any objective's
process/connectors/postures/memory/roster."

### 3.1 The seam that makes self-service real: posture must surface in plain language

There is a genuine design decision here, and it is the riskiest part of the 15% (research 04
§6.2, Gap B). The existing posture engine speaks engineer (`L4_CONTINUOUS_INSIGHT`,
`constraint_dimension=financial`). The brief's user is a non-coder. The fix is a
**presentation layer**: three plain-language buttons mapped onto the shipped engine —

| User-facing button | Engine posture   | What happens per step                                      |
| ------------------ | ---------------- | ---------------------------------------------------------- |
| **"Go ahead"**     | `AUTONOMOUS` (5) | Auto-approve within the envelope; out-of-bounds is blocked |
| **"Ask me once"**  | `DELEGATING` (4) | One approval at the plan→execute boundary                  |
| **"Step by step"** | `SUPERVISED` (3) | Every consequential action pauses for approval             |

(Research 04 §1.4 — the engine keeps all five states; the user sees three. The brief's
L3/L4/L5 _labels_ should NOT ship as the engine enum, because "Supervised" means a _lower_
level in both canonical ladders and would confuse anyone who knows EATP.)

**Recommendation (the 15% surface): BUILD the self-service configuration layer as the primary
net-new product surface, REUSING the comms onboarding wizard as the scaffold.** This is where
the bulk of net-new UX work lives (research 04 §6.2, Gap B: "multiple sessions"). It is worth
the investment because it is the difference between scaling to a thousand customers and
needing an engineer per customer.

- **Pros:** directly attacks the 95%-failure root cause; the engine underneath is shipped, so
  this is a _surface_ build not an _engine_ build; the comms wizard de-risks the UX pattern.
- **Cons (real):** non-coder configuration depth is exactly where no-code tools historically
  die — at "the last 20%" of any company's process (spine caution). A wizard that handles
  90% of a process but needs an engineer for the final 10% is a wizard customers stop
  trusting. Mitigation is to pair this surface _tightly_ with M1 transparency (below): when the
  configured process runs, the user can see every step and intervene, which makes the
  un-configured 10% legible and fixable in-flight rather than silently wrong.

---

## 4. The 5% — true custom

Bespoke, per-engagement, non-generalizable. The discipline is to keep this bucket _small_ by
pushing everything reusable into the 80% and everything client-specific into the 15%. The
comms wedge already demonstrates a genuinely-small 5% (research 09 §5.3).

| True-custom surface                                                                       | Why it resists generalization                                                                                           | Source           |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------- |
| **Novel connectors** — a system with no existing MCP server                               | Each new system's API/auth/data-shape is one-off until a server exists; thereafter it joins the 80% connector framework | 05 §5.1; 09 §5.3 |
| **Regulated-industry controls** — bespoke compliance overlays beyond a shipped regime     | Each new jurisdiction/regulator needs bespoke legal mapping (comms: PDPA shipped, Malaysia/Indonesia bespoke)           | 09 §5.3          |
| **External-policy onboarding** — e.g. per-business approval processes outside our control | Meta's WhatsApp template pre-approval is an external manual process per business                                        | 09 §5.3          |
| **One-off data cleanup** — a specific client's messy source data                          | Human-in-the-loop, per-client, non-repeatable                                                                           | 09 §5.3          |

### 4.1 The critical clarification: the untrusted-publisher trust model is NOT per-client custom

The Phase-A spine names the **untrusted-publisher trust model** (M4) as the "genuinely-new"
part of the cross-org registry — and research 01 §7c confirms it: loom's existing trust model
is _bounded-trust_ ("the adversary is a legitimate team member with repo write access"), but a
cross-company marketplace faces _untrusted publishers_ whose artifacts must be signed,
provenance-tracked, and recallable without trusting the publisher.

**This is a one-time core build, not per-client custom work.** It belongs conceptually in the
80% (it is built once and serves every client's cross-org sharing), but it is _genuinely new_
rather than _already-existing_, so it sits at the boundary. The reason to call it out under the
5% heading is to prevent a specific, costly misclassification: treating "trust for external
publishers" as something re-solved for each engagement. It is the opposite — it is a single
hard architecture decision that, once made, every client inherits for free.

- **The existing foundation (reuse):** loom already ships commit-signing keys, a hash-chained
  coordination log, 2-of-N quorum, `refs/coc/**` server-side rulesets, disclosure-scrub on
  intake, and the `obsoleted:`-list recall primitive (research 01 §2d, §7c). aegis's
  fork-relationship asymmetry (upstream-generic-only, no client leakage) is the right
  governance shape, already a baseline rule.
- **The genuinely-new piece (build):** signed-artifact provenance from an _external_ publisher
  (vs an enrolled operator), plus marketplace-grade licensing/attribution.

**Recommendation (untrusted-publisher model): DESIGN-FIRST, then BUILD — and design it before
the registry surface, because it constrains the registry.** Research 01 §7d sizes it as a
_novel-architecture decision_ (greenfield, first-session ~2–3× factor per
`autonomous-execution.md`), distinct from the mechanical registry surface.

---

## 5. Placing the comms wedge components into the buckets (research 09)

Pulling the wedge mapping into the 80/15/5 frame, component by component, so the wedge's slot
in the platform is unambiguous:

```
                    THE PLATFORM (80/15/5) — comms components placed
┌──────────────────────────────────────────────────────────────────────────┐
│ 80% AGNOSTIC CORE  (built once · every client · every objective)           │
│   work engine · artifact system · trust/posture · governance (PACT) ·      │
│   D/T/R transparency · provenance/versioning · human↔agent feedback ·      │
│   multi-human+agent coordination · MCP connectors · cross-org registry ·   │
│   multi-CLI parity                                                          │
│   ── COMMS PROVES: confidence badges/routing (→posture), AuditEntry        │
│      (→D/T/R), learning loop (→feedback), schema-per-tenant (→isolation),  │
│      escalation/SLA (→coordination), channel adapters (→connectors) ──     │
├──────────────────────────────────────────────────────────────────────────┤
│ 15% CLIENT SELF-SERVICE  (configured by a non-coder · no engineering)      │
│   their processes (artifacts+memory) · their connectors · their postures · │
│   their knowledge · their roster/governance                                │
│   ── COMMS PROVES: per-account routing config, onboarding wizard (<10 min, │
│      no app), confidence thresholds, doc upload, backup/escalation chain ──│
├──────────────────────────────────────────────────────────────────────────┤
│ 5% TRUE CUSTOM  (bespoke · external · one-off)                             │
│   novel connectors · regulated-industry controls                          │
│   [boundary] untrusted-publisher trust model = ONE-TIME CORE build, NOT    │
│              per-client (see §4.1)                                          │
│   ── COMMS: WhatsApp template approval, new-jurisdiction legal,            │
│      doc-cleanup service, regulated-client overrides ──                    │
└──────────────────────────────────────────────────────────────────────────┘
```

**What comms does NOT yet prove (the honest seam, research 09 §6):** comms exercises the
_trust/feedback/transparency/isolation spine_ but **not the orchestration spine** —
multi-step cross-system objectives, step-level retrace/intervene with versioned cascades,
agent↔agent coordination, or cross-org artifact sharing. These are the platform's real build
and map directly to the M1 and M4 moats. Comms de-risks the foundation; it does not deliver
the headline.

---

## 6. The BUILD vs REUSE vs DEFER recommendation

This is the operative recommendation, per `rules/recommendation-quality.md` (a single pick,
implications, symmetric pros and cons, plain language). Each item carries an
autonomous-execution sizing (research 01 §7d, research 04 §6, research 05 §6.3 — sessions, not
human-days).

### 6.1 The recommendation, in one table

| Capability                               | Disposition                                                 | Why                                                                               | Sizing (autonomous cycles)                                                    |
| ---------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Work engine (loop)                       | **REUSE** (own a runtime abstraction for the governed core) | Owning the loop is what makes M1 transparency native, not bolted-on               | Engine reuse; runtime-ownership decision is the pivot (see §6.3)              |
| Artifact system                          | **REUSE + adapt**                                           | loom is shipped; generalize "codegen" tiers → work-domain tiers                   | ~1 session (mechanical manifest/overlay) — 01 §7d                             |
| Trust/posture engine                     | **REUSE**                                                   | 3 shipped implementations; re-key agent→objective                                 | ~1 session re-key (engine unchanged) — 04 §6.2 Gap A                          |
| Governance (PACT)                        | **REUSE**                                                   | Shipped end-to-end with dashboard; wire into hot path                             | Integration glue; replace keyword classifier with LLM-first                   |
| D/T/R transparency                       | **REUSE**                                                   | Address grammar + AuditEntry both shipped                                         | Adopt grammar; minimal                                                        |
| Provenance/versioning                    | **REUSE the records; BUILD the cascade**                    | Versioning exists; _retrace-and-re-cascade_ does not                              | ~2–3 sessions (the one ≥500-LOC load-bearing piece) — 03 §8.4                 |
| Human↔agent feedback                     | **REUSE**                                                   | `/codify` + comms learning both shipped                                           | Generalize knowledge type captured                                            |
| Multi-human+agent coordination           | **REUSE the human-multiplicity half**                       | loom substrate shipped; differentiate on humans (A2A commoditizes agent-to-agent) | Integration; new agent↔agent message model ~1 session — 03 §8.4               |
| MCP connector framework                  | **REUSE protocol; BUILD the governed curation**             | MCP is standard; governed-connectivity is the differentiator                      | Connector porting is boilerplate-heavy (~5× scale) — 05 §6.3                  |
| Cross-org registry                       | **BUILD on the loom control plane**                         | Splitter exists; cross-_org_ publish/subscribe + discovery do not                 | ~3–5 sessions (after the trust model is designed) — 01 §7d                    |
| Untrusted-publisher trust model          | **DESIGN-FIRST then BUILD**                                 | The genuinely-new M4 piece; constrains the registry                               | Novel-architecture decision; greenfield ~2–3× factor — 01 §7d                 |
| Non-coder self-service surface (the 15%) | **BUILD (primary net-new UX)**                              | The 95%-failure escape; reuse comms wizard scaffold                               | Multiple sessions (the bulk of net-new UX) — 04 §6.2 Gap B                    |
| Step-level retrace/intervene UX (M1)     | **BUILD (the headline moat)**                               | Strongest moat AND highest execution risk                                         | ≥500-LOC load-bearing; needs durable-execution spike first — 04 §6.3, 05 §6.2 |

### 6.2 The single overarching recommendation

**Recommend: treat the platform as a ~3–5-shard parallel assembly of shipped primitives,
with two concentrated net-new builds (the non-coder self-service surface and the
retrace/intervene engine) and one design-first decision (the untrusted-publisher trust model)
gating the registry.**

The reusable 80% is assembly across many parallel sessions (research 05 §6.3); the hard work
is a small number of high-invariant sessions that gate the rest. The shards are independent —
artifact layer, posture layer, governance layer, connector layer, surface layer can each come
up in parallel worktrees — so the throughput multiplier applies (research 05 §6.3).

**Implications (what this means for the business):**

- **Time-to-first-capability is short** because most of the engine is shipped. The platform
  is not a from-scratch build; it is a re-pointing of proven machinery at a new audience.
- **The risk is concentrated, not diffuse.** Two builds (retrace engine, self-service surface)
  and one design (trust model) carry almost all the execution risk. They can be spiked early
  to convert uncertainty into evidence before committing the assembly work.
- **The moat is in the net-new 5%, not the reused 80%.** Anyone can call an agent loop; almost
  no one ships transparent step-level intervention, per-objective posture, and governed
  cross-org artifact exchange (research 05 §7.2). The reused 80% is necessary but not
  defensible; the built 5% is where M1–M4 live.

**Pros (of this assembly-first, risk-concentrated approach):**

- Maximizes reuse of shipped, real-user-tested code — lowest invention cost.
- Isolates risk into spike-able units, so a failed spike costs one session, not a program.
- Keeps the architecture horizontal/agnostic per Decision B (capability-first, GTM deferred) —
  no beachhead is prematurely locked.
- The comms wedge provides a revenue-bearing, real-user landing vertical _while_ the
  orchestration spine is built (research 09 §6.5).

**Cons (real, not glossed):**

- **The reuse story can lull.** "80% exists" is true of primitives; a primitive is not a
  product. The integration glue between shipped components (re-key posture, replace keyword
  classifier with LLM-first per `agent-reasoning.md`, wire PACT into the hot path) is real
  work that the "80% exists" headline can hide. Mitigation: the §6.1 sizing column counts the
  glue explicitly.
- **The two net-new builds are the hardest things in the plan AND the most load-bearing.** M1
  (retrace/intervene) is the strongest moat and the highest execution risk — non-deterministic
  LLM steps and non-coder versioning UX are both unsolved (spine). If M1 fails, the platform
  degrades to "an agent does your work in one interface" — which is exactly the surface
  Claude Cowork (GA Apr 2026) already embodies (spine, biggest threat). Competing on that
  surface is the failure case.
- **Orphan risk is structural.** PACT is facade-heavy (managers, bridges, stores). Reusing it
  risks shipping governance that never executes on the hot path — the exact Phase-5.11 failure
  the `orphan-detection.md` / `facade-manager-detection.md` rules exist to prevent (research 03
  §8.5). The intervention UX MUST _actually call_ the governance primitives on the data path,
  with a Tier-2 test proving it, or the security promise is a no-op.

### 6.3 The one decision everything hinges on (flagged as genuine uncertainty)

Research 05 §4.4 is explicit: the pivotal unknown is **"can the brief's transparency +
intervention + versioned-replay requirement be satisfied without owning the agent loop?"**

- If harness introspection is enough → the platform can sit _on_ existing harnesses (lower
  build cost, but `rules/independence.md` forbids _depending_ on a proprietary SDK, and you
  don't control the loop).
- If not → the transparency/intervention/replay requirement is a _runtime_ capability, which
  implies owning a runtime abstraction (the envoy precedent — research 05 §4.2).

**Recommendation: resolve this with a spike before committing the assembly, because it
determines whether M1 is buildable at all.** This is the highest-leverage early experiment.
The evidence tilts toward "own the governed core's runtime" (envoy chose exactly this for
exactly this reason), but the brief defers the recommendation to plans (Decision B), so this
document surfaces the criterion and recommends the spike rather than pre-deciding.

---

## 7. Honest cautions carried into the split (symmetric)

Per the spine's instruction to carry symmetric pros/cons everywhere:

1. **"80% exists" — pro:** the inventory in §2 is real, cited, mostly-shipped code; this is
   genuinely a re-pointing, not a from-scratch build. **Con:** existence of primitives ≠
   finished product; the glue and the net-new 5% carry the real cost and the real moat.

2. **Self-service 15% — pro:** it is the escape from the 95%-pilot-failure mode and the comms
   wizard proves non-coders can do it. **Con:** no-code depth dies at "the last 20%"; the
   mitigation (pair tightly with M1 transparency) is itself one of the two hardest builds.

3. **The untrusted-publisher model — pro:** it is a one-time core build every client inherits,
   and loom's crypto substrate is a strong starting point. **Con:** it is genuinely-new
   greenfield architecture (~2–3× first-session factor) and it gates the entire registry, so a
   wrong call here is expensive to unwind.

4. **Connectivity — pro:** MCP makes any system a tool, and >1,000 connectors exist. **Con:**
   connectivity is a commodity; only _governed_ connectivity differentiates (spine), which
   means the connector work is only valuable when the governance-between-agent-and-connector
   (research 05 §5.3) ships with it.

5. **The comms wedge as proof — pro:** it de-risks the trust/feedback/transparency/isolation
   spine against real users and real data. **Con:** it proves the spine, not the orchestration
   half (M1, M3-team, M4); the headline moat is still unbuilt and unproven.

6. **The "agent-comms beat human-comms" hypothesis (brief 3d) — pro:** the multi-operator
   substrate gives a real substrate to _test_ it. **Con:** it is an UNPROVEN, contrarian
   research bet, NOT a USP — the platform must not stake its value proposition on it (spine).

---

## 8. Bottom line

- **~80% of the platform core already exists — as primitives, not as a finished product
  (codegen primitives ≠ enterprise-work capability)** — shipped or specced ecosystem assets (loom
  artifact system, PACT governance, EATP/aegis posture, envoy parity, 400+ artifacts) plus the
  deployed comms wedge — the §2 inventory is the evidence.
- **~15% is the company-specific-process surface (brief 1b)** that MUST be non-coder
  self-service (their processes/connectors/postures/memory/roster as artifacts and config) —
  the comms onboarding wizard proves it is achievable; building it out is the primary net-new
  UX work.
- **~5% is true custom** (novel connectors, regulated-industry controls) — kept small on
  purpose; the untrusted-publisher trust model sits at the boundary as a **one-time core build,
  not per-client custom**.
- **The recommendation is assembly-first, risk-concentrated:** reuse the shipped 80%, build the
  two hard net-new pieces (non-coder self-service surface + retrace/intervene engine), design
  the trust model first, and spike the runtime-ownership question early because it determines
  whether the strongest moat (M1) is buildable at all.
- **The moat is in the built 5%, not the reused 80%** — which is why the honest cautions
  (§6.2, §7) matter more than the encouraging inventory.

---

## 9. Sources

- `briefs/01-vision.md` (authoritative vision; §1 triple, §4 Decisions, §6 80/15/5)
- `01-research/01-coc-artifact-system.md` (loom five-layer system, splitter, registry §7)
- `01-research/03-pact-governance.md` (PACT engine, D/T/R, envelopes, intervention §8)
- `01-research/04-eatp-trust-posture.md` (EATP/posture ladders, retrace/version §6)
- `01-research/05-cli-harness-universal-interface.md` (harness as runtime, MCP, runtime-ownership §4)
- `01-research/09-comms-wedge-mapping.md` (comms→platform mapping, the 80/15/5 derivation §5)
- Phase-A strategic spine (M1–M4 moat, Decisions A+B, market evidence from research 07)
