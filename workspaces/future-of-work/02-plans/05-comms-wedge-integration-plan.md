# 05 — Comms-Wedge Integration Plan: Comms as the First Demonstrated Wedge + Instrumented Lighthouse

> Plan output for the agentic-work-platform analysis (`/analyze` → `/todos` handoff, Phase 01 → 02).
> Implements **Decision A** from `briefs/01-vision.md` §4 ("Comms is a wedge, not the product"):
> the existing Sequor comms-coverage product is *subsumed* as the platform's first demonstrated
> wedge AND its instrumented lighthouse — the live system that proves the platform's primitives
> against real users while the harder orchestration spine is built.
>
> **Grounds in** (every claim cites one of these or the brief): the comms-wedge mapping
> (`01-analysis/01-research/09-comms-wedge-mapping.md`), the platform model
> (`01-analysis/04-platform-model.md`), the specs index (`specs/_index.md`), and the strategic
> spine carried in the analysis invocation (M1–M4 moat, Decisions A + B, the agent-comms BET).
> Effort is framed in **autonomous execution cycles (sessions)**, never human-days, per
> `rules/autonomous-execution.md`. Genuine uncertainty is flagged **[UNCERTAIN]**; an inference
> not yet grounded in built code is flagged **[INFERENCE]**.
>
> Plain-language note (per `rules/communication.md` + `rules/recommendation-quality.md`): this
> plan is written for a non-technical founder. Every technical term is translated on first use.
> Where a choice is surfaced, a single recommendation is given with its implications and *both*
> its upsides and downsides — never a bare menu.

---

## 0. Executive summary — read this first

**The recommendation, in one sentence:** keep the comms product running exactly as it is today,
and add a *thin* layer underneath it that re-routes three of its existing behaviours through the
platform's shared machinery — so that comms becomes the live proof that the platform's machinery
works, and the instrument that tells us whether "agents communicating beats humans communicating"
is true. Do **not** rewrite comms; do **not** pause comms; do **not** gold-plate it into a
mini-platform.

The comms product already does five things the broader platform must do for *every* kind of work
(`09-comms-wedge-mapping.md` §2): it decides when the agent acts vs asks vs pauses (confidence
badges + 3-tier routing); it turns a human's correction into durable knowledge (learning from
human answers); it records every action transparently (the D/T/R audit log — "who did what to
whom"); it keeps each customer's data hermetically separate (schema-per-tenant isolation); and it
stores each customer's process as configuration rather than custom code (per-account routing
rules). These are not comms inventions — they are the platform's primitives, instantiated in one
vertical and *deployed against real users on real data* (Vercel + Neon, per `briefs/01-vision.md`
§4).

**What "integration" means here** is narrow and deliberate. It is **not** "fold comms into the
platform codebase." It is three surgical re-pointings, each of which converts a comms-private
mechanism into a *demonstration of a platform primitive*:

1. **Run comms on the provenance ledger** — comms' existing append-only audit log becomes the
   first writer to the platform's shared, signed action-and-artifact record. This proves the
   ledger (the thing that makes M1 "intervene from any step" and M4 "trust a stranger's artifact"
   possible) works against real traffic.
2. **Govern comms via posture** — comms' hard-coded three confidence bands become the first
   *consumer* of the platform's chosen-beforehand posture control (the L3/L4/L5 autonomy ladder).
   This proves M2 (the moat we ship first) on a live high-stakes objective.
3. **Publish comms' response policy as an artifact** — comms' per-account routing/escalation
   config becomes the first *published, versioned work-artifact* on the platform's exchange.
   This proves M4's core transaction (a reusable unit of "how a company does a piece of work")
   exists and can be governed.

**Why this is the right scope and not more or less** (full argument in §5): more (a full rewrite
to make comms "platform-native") burns the one revenue-bearing, de-risking asset the company has,
for a payoff — orchestration of multi-step cross-system work — that comms structurally cannot
demonstrate anyway (`09-comms-wedge-mapping.md` §6). Less (leave comms entirely alone) means the
platform's primitives stay *claimed* rather than *proven*, and the agent-comms BET stays
*asserted* rather than *measured* — the lighthouse goes dark.

**The honest counterweight, carried throughout:** comms proves the platform's
*trust/feedback/transparency/isolation spine*. It does **not** prove the *orchestration spine* —
multi-step cross-system objectives, step-level retrace-and-replay, agent-to-agent coordination,
or cross-org artifact sharing (`09-comms-wedge-mapping.md` §6.1–6.3). This plan is explicit about
that boundary so the founder never mistakes a lit lighthouse for a finished harbour.

---

## 1. The integration thesis in plain language

Picture two layers.

**The top layer** is the comms product as a customer experiences it today: messages arrive by
email or company WhatsApp; the AI drafts a reply from the customer's knowledge base; high-confidence
replies send automatically, medium-confidence replies go to a human with a draft attached,
low-confidence ones go to a human to write from scratch; unanswered items escalate up a chain on a
clock; a daily digest summarises it all; and when a human answers something the AI couldn't, the
system remembers that answer forever (`09-comms-wedge-mapping.md` §1). None of this changes for the
customer.

**The bottom layer** is the platform's shared machinery — the thing the company is actually
building. Today comms has its *own private copy* of three of these mechanisms (its own audit log,
its own confidence-band logic baked into code, its own routing config stored as data inside the
comms database). The integration replaces those three private copies with calls to the *shared*
platform machinery underneath.

**The analogy:** comms today is a house with its own well, its own generator, and its own septic
tank. The integration connects the house to the town's water main, power grid, and sewer — without
the family inside noticing anything except that the utilities now serve the rest of the town too,
and the town can now *see* (on the shared meters) that the utilities actually work under real load.

That visibility is the entire point of calling comms a **lighthouse**: a lighthouse is not the
destination, it is the proof that the harbour's navigation system works, lit and watched. Comms
running on the shared ledger, governed by shared posture, publishing a shared artifact is the lit,
watched proof that the platform's three load-bearing claims are real — *before* the company has
written a single line of the much harder orchestration engine.

---

## 2. Mapping each comms feature to the general primitive it foreshadows

This section is the load-bearing detail behind Decision A. Each comms feature is shown as a
*constrained instance* of a general platform primitive, with the specific platform moat (M1–M4) it
foreshadows named. The mappings are taken from `09-comms-wedge-mapping.md` §2 and re-expressed
against the moat structure and the platform transaction model (`04-platform-model.md` §2).

### 2.1 Response-accuracy D/T/R → M2 posture + HITL

**Comms feature today.** Every reply runs through a fixed three-band decision
(`specs/response-accuracy.md` "Option C"; `src/sequor/ai/response.py:103-123`): above ~90%
confidence the AI sends automatically; 60–90% it escalates *with* a draft for a human to
approve/edit; below 60% it escalates *without* a draft for the human to compose. A fixed,
non-editable confidence badge (high/moderate/low/uncertain) is the transparency control
(`09-comms-wedge-mapping.md` §1.6). Every state change writes a "who-did-what-to-whom" audit row —
D/T/R = **D**oer / action **T**ype / **R**ecipient (`specs/response-accuracy.md` §"D/T/R";
`src/sequor/db/audit.py:23-61`).

**General platform primitive it foreshadows: M2 — execution-time posture-graded governance + HITL**
(human-in-the-loop). The brief's L5-Autonomous / L4-Supervised / L3-Step-by-step ladder
(`briefs/01-vision.md` §3e) is *the same shape* as comms' three bands, mapped structurally
(`09-comms-wedge-mapping.md` §2.1):

| Comms band (fixed in code)            | Platform posture (chosen beforehand) | What it means for the user                          |
| ------------------------------------- | ------------------------------------ | --------------------------------------------------- |
| >90% → auto-send                      | **L5 Autonomous** — agent proceeds   | "Let the agent do it; tell me after."               |
| 60–90% → escalate *with* a draft      | **L4 Supervised** — agent asks once  | "Agent prepares it; I approve before it goes out."  |
| <60% → escalate *without* a draft     | **L3 Step-by-step** — human composes | "Agent pauses; I drive."                            |

**The difference that integration closes:** comms *hard-codes* which band applies (the confidence
score picks the band). The platform lets the *user choose the posture beforehand* per objective
(`briefs/01-vision.md` §3e). After integration, the confidence *score* stays (it is the evidence),
but the band *thresholds* become a posture artifact the user selects — turning a code constant into
a configurable control (`09-comms-wedge-mapping.md` §2.1 [INFERENCE]). The general posture machinery
already exists in the ecosystem: the L1–L5 ladder in `pact`/`aegis` posture state machines, and
EATP's `PostureStore` (the place a chosen posture is persisted; skill `26-eatp-reference`). M2 is
the moat the strategic spine says to **ship first** — comms is the live objective that proves it.

### 2.2 Learning-from-human-answers → the knowledge-contribution transaction (D) + agent-comms instrumentation

**Comms feature today.** When a human resolves an escalation by replying to the escalation email,
the system captures the `{question, answer}` pair, embeds and indexes it, and answers future
matching queries from that learned answer (`src/sequor/ai/learning.py:54-122`;
`specs/rag-pipeline.md` §"Learning from Human Answers"). This is *byproduct capture*: the human
just does their job (replies to an email) and the system learns, with no separate "training" step
(`09-comms-wedge-mapping.md` §4.2).

**General platform primitive it foreshadows: the knowledge-contribution transaction (transaction D),
the *feeder* of the M4 marketplace** (`04-platform-model.md` §2.2). The platform model names the
*published/consumed work-artifact* (transaction B) as the primary marketplace good, and the
*knowledge contribution* (transaction D) as the secondary, faster-cycling transaction that keeps
the goods improving without anyone hand-authoring them. **Comms runs transaction D end-to-end in
production today** — it is the *only* part of the entire platform thesis already proven against
real users (`04-platform-model.md` §0, §2.2). The integration's job is not to build D; it is to
*instrument* D so the company can measure it.

**The agent-comms instrumentation angle (this is the lighthouse's primary reading).** The strategic
spine carries an unproven research BET: *agent-to-agent communication beats human-to-human
communication* because agents carry more context and memory into an exchange (`briefs/01-vision.md`
§3d). Comms is the natural instrument for this BET because it is *already a communication system
with a human-in-the-loop fallback*. Concretely, every escalation is a moment where the agent's
communication was judged insufficient and a human took over — and the learned answer is the captured
residue. By instrumenting that boundary (§4.2 below), comms can measure: how often the agent's
communication suffices vs needs human takeover, whether that ratio improves as learned answers
accumulate, and whether agent-mediated exchanges resolve faster/more-completely than the
human-takeover ones. That is direct, real-data evidence for or against the agent-comms BET — the
single most valuable thing comms can produce for the platform.

> **The generalization gap (honest):** comms learns *answers* (data-level knowledge, a `{Q,A}`
> pair). The platform needs to learn *artifacts* (process-level knowledge — a procedure, a rule, a
> skill) (`09-comms-wedge-mapping.md` §2.2 [INFERENCE]; `04-platform-model.md` §9 uncertainty #3).
> This plan does **not** ask comms to make that leap — that is the platform's real build. Comms
> proves the *mechanism* (human intervention → durable knowledge, cheaply, as work exhaust);
> generalizing the *type* of knowledge captured is out of scope here (§5.3).

### 2.3 Tenant isolation → the multi-org boundary (M3 + M4 isolation half)

**Comms feature today.** Each customer gets a dedicated database schema (`tenant_<hex>`); no
customer can read another's data by architecture; this is the hard compliance boundary that meets
Singapore PDPA (`src/sequor/db/schema_manager.py`; `specs/data-model.md` §"Multi-Tenancy
Requirement"; `09-comms-wedge-mapping.md` §1.4). Schema names are validated before any SQL is
constructed (`schema_manager.py:71-74`), consistent with this repo's
`rules/dataflow-identifier-safety.md`.

**General platform primitive it foreshadows: the multi-org boundary** that both *isolates by
default* (the M3 team/org substrate's privacy floor) and is *deliberately permeable for artifact
sharing* (the M4 cross-org exchange) (`briefs/01-vision.md` §3g; `09-comms-wedge-mapping.md` §2.4).
Comms has built — and battle-tested against a real regulator — the *hard-isolation half*. The
platform adds the *controlled-permeability half* (deliberate sharing across the boundary), for
which `loom`'s variant-overlay + Gate-1/Gate-2 distribution is the candidate mechanism
(`04-platform-model.md` §9 uncertainty #5).

**The difference that integration closes — and deliberately does NOT close.** Integration makes
comms' tenant boundary the *reference implementation* of the platform's isolation floor (the ledger
and posture machinery below comms must respect the same per-tenant boundary). It does **not** make
comms tenants permeable — comms tenants stay sealed silos by design (`09-comms-wedge-mapping.md`
§6.3). Cross-org artifact sharing depends on the *untrusted-publisher trust model*, which is the
platform's genuinely-new, unbuilt, must-design-first 5% (`04-platform-model.md` §7.3 cons, §9
uncertainty #1) — wiring comms into it before it is designed would be premature and unsafe (§5.3).

### 2.4 RAG / connectors → the integration layer (the agnosticism foundation)

**Comms feature today.** Comms reaches its data through adapters: email (IMAP/SMTP), company
WhatsApp (a Business API number via an approved provider), and document parsers feeding the RAG
pipeline — RAG = "retrieval-augmented generation," i.e. the AI answers *from* the customer's
documents rather than from its own memory (`src/sequor/email/*`, `src/sequor/whatsapp/*`,
`src/sequor/ai/rag_pipeline.py`; `09-comms-wedge-mapping.md` §1.2, §5.1 "Connectors").

**General platform primitive it foreshadows: the MCP connector layer** — the platform's foundation
of *agnosticism* (MCP = "Model Context Protocol," the open standard that lets an agent call any
system as a tool) (`briefs/01-vision.md` §2; `04-platform-model.md` §5.1). The inbox is one data
source; an ERP, a CRM, a spreadsheet is another (`09-comms-wedge-mapping.md` §3). Nothing in comms'
architecture is hostile to adding more connectors — they are more tools the same agent calls.

**The difference that integration closes — and deliberately does NOT close.** Integration confirms
comms' adapters are *shaped like* platform connectors (and wraps them as such if they are not —
this is an open question, `09-comms-wedge-mapping.md` §7 q2 [UNCONFIRMED]). It does **not** add new
connectors (ERP/CRM) to comms — comms stays a single-tool-cluster vertical. The strategic spine is
explicit that *connectivity is commodity; only governed connectivity differentiates*
(`04-platform-model.md` §5.2). So the integration touches connectors only enough to prove the
*pattern* generalizes (data-via-tools), not to expand comms' surface (§5.3).

### 2.5 The mapping, drawn together

```
   COMMS FEATURE (live today)            PLATFORM PRIMITIVE             MOAT      INTEGRATION ACTION
 ─────────────────────────────────────────────────────────────────────────────────────────────────
   3-band confidence routing       →   posture / HITL (L3/L4/L5)        M2    →  govern via posture
   + D/T/R audit rows
   learning-from-human-answers      →   knowledge-contribution (D)       M4    →  instrument the loop
                                        + agent-comms BET instrument            (the lighthouse reading)
   schema-per-tenant isolation      →   multi-org boundary (isolation)   M3/M4 →  ledger respects the
                                                                                  same tenant floor
   per-account routing config       →   published work-artifact (B)      M4    →  publish as artifact
   RAG + email/WhatsApp adapters    →   MCP connector layer (agnostic)   FND   →  confirm connector shape
   (immutable audit + supersession  →   provenance ledger / versioning   M1    →  run on the ledger
    of learned answers)                  (foreshadows step-replay)              (partial — see §6)
```

(FND = foundation / table-stakes. The M1 row is *partial*: comms has immutable audit + answer
supersession but no step-level retrace-and-replay; see §6.1.)

---

## 3. What to REFACTOR — the three surgical re-pointings

This is the concrete integration work. Each item is a *re-pointing* of an existing comms mechanism
onto a shared platform substrate, not a rewrite. Each is scoped to fit the per-session capacity
budget (`rules/autonomous-execution.md` § Per-Session Capacity Budget: ≤500 lines of load-bearing
logic, ≤5–10 invariants, ≤3–4 call-graph hops per shard). Where an item exceeds that, it is sharded
explicitly. Specialist delegation (per `rules/agents.md`) is named CLI-neutrally
("delegate to dataflow-specialist", "delegate to pact-specialist").

### 3.1 Refactor 1 — Run comms on the provenance ledger

**What exists.** Comms writes append-only, immutable, PII-free audit rows on every state transition
(`src/sequor/db/audit.py:23-61`; `specs/data-model.md` §AuditEntry). Learned answers supersede
earlier contradicting ones with the prior retained (`src/sequor/ai/learning.py`). This is *already*
a provenance discipline — it records inputs and outputs of every agent action without claiming to
record the model's internal reasoning (`09-comms-wedge-mapping.md` §2.3).

**What to change.** Introduce a thin platform **provenance-ledger interface** — a single shared
contract for "append a signed, attributable, tenant-scoped record of an action or an
artifact-change" — and make comms' audit writer the *first writer* to it. Comms' AuditEntry table
becomes one *backing store* behind that interface; the interface is what the rest of the platform
will share. The ecosystem already has the shape: the multi-operator coordination log
(`rules/multi-operator-coordination.md` §2 — stamped + chained + signed append-only records) is the
signed-ledger pattern; PACT's D/T/R engine is the governance-record pattern
(`04-platform-model.md` §7.2). The refactor adapts comms' writer to that shape; it does **not**
re-implement the ledger.

**Invariants this refactor must hold** (≤5, within budget): (1) every record is tenant-scoped — the
tenant boundary of §2.3 must survive the ledger move (`rules/tenant-isolation.md` §5: audit rows
persist `tenant_id`, indexed); (2) records stay append-only/immutable (no UPDATE/DELETE path);
(3) records stay PII-free so PDPA erasure never touches the ledger (`specs/data-model.md`
§"Erasure implementation"); (4) every record is attributable to a doer (the platform's two-level
attribution — *both* the agent AND the accountable human, `04-platform-model.md` §3.3); (5) the
existing comms audit behaviour is unchanged from the customer's view (the daily digest still reads
the same data).

**Why this proves a platform claim.** The provenance ledger is the substrate beneath M1
("intervene from any step; old outputs versioned") *and* M4 ("trust a stranger's artifact because
its provenance is recorded and recallable"). Comms running on it is the first real-traffic proof
the ledger holds under load and under a real compliance regime.

**Sharding & effort.** One shard, ~1 session — comms' audit writer is bounded, the ledger interface
is an adapter, and there is a live feedback loop (the existing comms test suite + a read-back
assertion per `rules/testing.md` § State Persistence Verification). Delegate to **dataflow-specialist**
(the writer touches the database) with the relevant `specs/data-model.md` §AuditEntry content
inlined per `rules/specs-authority.md` Rule 7.

### 3.2 Refactor 2 — Govern comms via posture

**What exists.** The three confidence bands are hard-coded constants in `src/sequor/ai/response.py:103-123`
(`09-comms-wedge-mapping.md` §2.1).

**What to change.** Replace the hard-coded band thresholds with a **posture lookup** — comms reads
the user's pre-selected posture for the "comms coverage" objective from the platform's PostureStore
(EATP `PostureStore` / `PostureStateMachine`, skill `26-eatp-reference`) and derives the act/ask/pause
decision from it. The confidence *score* stays exactly as-is (it remains the evidence); only the
*thresholds* move from code constants to a posture artifact (`09-comms-wedge-mapping.md` §2.1
[INFERENCE]). Default the posture to comms' current bands so behaviour is identical on day one —
the change is *where the thresholds live*, not *what they are*.

**Invariants this refactor must hold** (≤5, within budget): (1) the default posture exactly
reproduces today's behaviour (no customer sees a change unless they opt to change posture);
(2) posture is per-tenant and per-objective (respects the isolation floor); (3) an automatic
downgrade on violation is honoured (posture machines downgrade instantly when conditions change —
EATP discipline; `09-comms-wedge-mapping.md` §2.1); (4) the confidence badge stays a fixed,
non-editable transparency control (`specs/response-accuracy.md` §"Badge Display") — posture governs
the *action*, the badge governs the *disclosure*, and they stay separate; (5) the posture choice is
written to the ledger (Refactor 1) so it is auditable.

**The honest UX risk this surfaces.** Comms' onboarding forbids making the user understand vectors,
RAG, or confidence numbers (`specs/onboarding.md` §"Configuration Complexity Budget"). Surfacing an
explicit L3/L4/L5 posture choice *could* violate that budget (`09-comms-wedge-mapping.md` §7 q1
[INFERENCE-heavy]). **Recommendation:** keep the posture *invisible by default* (the default band
behaviour is the default posture) and surface the posture choice only as an *optional* control for
customers who ask for more or less automation — phrased in plain language ("send routine replies
automatically? yes / only with my approval / never"), never as "L3/L4/L5." **Pro:** preserves the
non-technical onboarding promise while still proving M2 against a live objective. **Con:** the
fully-explicit posture ladder (the brief's §3e vision) is *not* exercised by comms even after this
refactor — comms proves posture-as-mechanism, not posture-as-user-facing-choice. That gap is
acceptable here because the user-facing posture UX is a platform-build question, not a comms one
(§6.4).

**Sharding & effort.** One shard, ~1 session — the change is localized to the response decision and
has a live feedback loop (the existing 3-band tests, re-pointed to assert default-posture
equivalence). Delegate to **pact-specialist** (posture/governance) with `specs/response-accuracy.md`
§"Option C" inlined.

### 3.3 Refactor 3 — Publish comms' response-policy as an artifact

**What exists.** Each account carries its process config as data: routing rules (which categories
auto-respond vs escalate), the escalation chain, the SLA timing, the confidence threshold — selected
from templates A/B/C and stored as JSONB (a flexible data field), not code (`specs/data-model.md`
§Account; `specs/onboarding.md` §"Step 5"; `09-comms-wedge-mapping.md` §2.5).

**What to change.** Define a **work-artifact wrapper** for this config — a versioned, signed,
provenance-tracked package that says "here is how this account does comms coverage" — and publish it
to the platform's artifact registry. This makes comms' response-policy the *first published
work-artifact* (transaction B, the M4 primary transaction; `04-platform-model.md` §2.2). The COC
artifact machinery already does exactly this for one organization's code artifacts
(`04-platform-model.md` §0, §6.1: the splitter + variant-overlay + recall primitive run in
production); the refactor wraps comms' config in that artifact shape.

**Scope discipline — intra-org first, no cross-org.** The published artifact is consumable *within
the same organization* (one account's policy reused by another account in the same company), exactly
the intra-org-first cold-start sequence the platform model recommends (`04-platform-model.md` §6.3:
"supply = demand = same customer, no chicken-and-egg"). It is **not** published cross-org — that
needs the untrusted-publisher trust model that must be designed first (§5.3). So this refactor proves
transaction B *within a tenant boundary*, not across it.

**Invariants this refactor must hold** (≤5, within budget): (1) the artifact is versioned (a new
policy version supersedes the old, the old retained — same supersession discipline comms already
uses for learned answers); (2) the artifact is attributable (who authored this policy version);
(3) the artifact is tenant-scoped (an account's policy is publishable only within its own org);
(4) the artifact carries a recall hook (a bad policy version can be withdrawn — the recall primitive,
`04-platform-model.md` §4.2); (5) consuming the artifact (another account adopting it) is governed
at install (provenance checked) and at run (posture chosen) — the two consumer gates
(`04-platform-model.md` §4.2).

**Sharding & effort.** This is the largest of the three — it touches config modelling, the artifact
wrapper, versioning, and the registry. **Shard into two** (each within budget): **Shard 3a** —
wrap an account's existing routing config as a versioned, signed, tenant-scoped artifact and write
it to the registry (publish side); **Shard 3b** — let a second account in the same org *install and
run* that artifact, governed at install (provenance check) and at run (posture) (consume side).
~2 sessions total. Delegate to the COC-artifact machinery owners (the `loom` splitter pattern) with
`specs/data-model.md` §Account + `specs/onboarding.md` §"Step 5" inlined.

### 3.4 The three refactors as a dependency-ordered sequence

```
   Refactor 1 (ledger)  ──┐
   ~1 session             ├──→  Refactor 3a (publish artifact)  ──→  Refactor 3b (consume artifact)
   Refactor 2 (posture) ──┘     ~1 session                           ~1 session
   ~1 session
   ── 1 + 2 are independent (parallelizable) ──   ── 3a/3b depend on 1 (ledger) + 2 (posture) ──
```

Refactors 1 and 2 are independent and can run as a parallel wave (per `rules/agents.md` § Parallel
Execution; worktree-isolated if they touch overlapping files). Refactor 3 depends on both (an
artifact must be ledger-recorded and posture-governed). Total: **~4 autonomous execution sessions**,
not human-weeks. This is small precisely *because* the work is re-pointing existing, deployed
mechanisms onto shared substrate — not greenfield construction.

---

## 4. Comms as the instrumented lighthouse

The refactors of §3 connect comms to the platform's machinery. *Instrumentation* is what makes
comms a **lighthouse** — a lit, watched proof. Two things must be measurable: (a) that the platform
primitives work under real load (the de-risking reading), and (b) whether the agent-comms BET is
true (the PMF-discovery reading). PMF = product-market fit, "is this a thing people actually want."

### 4.1 The de-risking readings (do the primitives hold?)

Once comms runs on the ledger, is governed by posture, and publishes an artifact, the company gets
continuous, real-traffic evidence on the questions the platform must otherwise answer from scratch
(`09-comms-wedge-mapping.md` §4):

- **Does the ledger hold under load and under PDPA?** Measured by: ledger write success rate, zero
  cross-tenant leakage (a tenant-isolation probe per `rules/tenant-isolation.md` § Audit Protocol),
  and that PDPA erasure never has to touch the ledger (audit rows stay PII-free).
- **Does posture-graded governance produce safe automation?** Measured by: the act/ask/pause
  distribution per posture, and — critically — the *wrong-send rate* (how often an auto-sent reply
  was later corrected). Comms' founding principle is "wrong info is worse than none"
  (`specs/response-accuracy.md`); the wrong-send rate is the direct measure of whether posture is
  calibrated.
- **Does the published artifact get consumed safely?** Measured by: intra-org install rate of the
  published policy artifact, and whether a recalled policy version actually stops being used.

### 4.2 The PMF-discovery reading (is the agent-comms BET true?) — the lighthouse's primary value

This is the highest-value thing comms produces for the platform, and the reason it is *the* natural
instrument for the agent-comms BET (`briefs/01-vision.md` §3d; strategic spine). The BET — *agents
communicating beats humans communicating* — is **unproven research** (strategic spine caution).
Comms can move it from asserted to measured because comms is *already* a communication system with a
human takeover boundary.

**The instrument is the escalation boundary + the learning loop.** Every escalation is a recorded
moment where the agent's communication was judged insufficient and a human took over; every learned
answer is the captured residue (§2.2). Instrumenting this boundary yields direct BET evidence:

- **Sufficiency ratio over time** — what fraction of communications the agent handles without human
  takeover, and whether it rises as learned answers accumulate (comms' own spec projects coverage
  rising 0% → 60-70% over six months purely through usage, `specs/rag-pipeline.md` §"Knowledge Base
  Composition Over Time"). A rising ratio is evidence the agent-mediated channel *improves*; a flat
  ratio is evidence against the BET in this vertical.
- **Resolution quality at the boundary** — do agent-mediated exchanges resolve faster / more
  completely / with fewer back-and-forths than the human-takeover ones? Comms already records the
  data to compute this (message threads, escalation timing, resolution events).
- **Knowledge-compounding rate** — how fast the routing flywheel (`specs/message-routing.md`
  §"Routing Intelligence Flywheel"; `09-comms-wedge-mapping.md` §2.6) and the learned-answer base
  grow, which is the data-layer instance of the platform's knowledge-compounding primitive.

**How the readings are produced — probe-driven, not keyword-counted.** Per
`rules/probe-driven-verification.md`, any *semantic* measurement (e.g. "did the agent's reply
actually resolve the customer's question?") MUST be a probe — a structured query with a defined
expected-answer schema and a deterministic scoring rule — never a regex or keyword count over the
reply text. Structural measurements (counts, rates, timings) stay deterministic. This keeps the
lighthouse's BET reading honest: it measures *whether the behaviour happened*, not *whether a word
appeared*.

**The honest caution on the BET reading.** Comms is a *narrow* communication vertical
(customer/stakeholder coverage). A positive agent-comms reading *in comms* is evidence for the BET
*in that vertical*, not a proof for all knowledge work — and comms does **not** exercise
agent-to-agent dialogue at all (its pipeline is sequential single-agent calls,
`09-comms-wedge-mapping.md` §6.4). So comms can measure "agent-mediated *human↔customer* comms vs
human-mediated" but *cannot* directly measure "agent↔agent vs human↔human," which is the sharper
form of the BET. The lighthouse lights one channel of the harbour, not all of them (§6).

### 4.3 What the lighthouse does NOT measure

To keep the founder from over-reading a lit lighthouse (the comms gaps, `09-comms-wedge-mapping.md`
§6): comms cannot test multi-step cross-system objectives, step-level retrace-and-replay with
versioned cascades, agent-to-agent coordination, or cross-org artifact sharing. Those are the
orchestration spine — the platform's real, harder build. A green comms lighthouse de-risks the
*foundation* the orchestration spine stands on; it does not de-risk the orchestration spine itself.

---

## 5. The integration scope recommendation (single rec + implications + symmetric pros/cons)

Per `rules/recommendation-quality.md`: one recommendation, its implications, and *both* its upsides
and downsides — not a menu.

### 5.1 The recommendation

**Adopt the "thin lighthouse" scope: the three surgical re-pointings of §3 (ledger, posture,
intra-org artifact) plus the instrumentation of §4 — and nothing more. Keep the comms product
running and shipping to customers throughout; do not rewrite it; do not pause it; do not expand its
surface (no new connectors, no cross-org publishing, no orchestration).**

In plain terms: connect comms' three private mechanisms to the shared platform machinery, put meters
on the result, and stop there. Comms keeps earning revenue and serving real users while becoming the
live proof that the platform's load-bearing claims are real.

### 5.2 Implications (what this means for the founder, concretely)

- **Effort: ~4 autonomous execution sessions** (Refactors 1+2 in parallel ≈ 1 session of wall-clock,
  Refactor 3 ≈ 2 sessions, instrumentation ≈ 1 session), not weeks (`rules/autonomous-execution.md`).
  Small because it is re-pointing, not building.
- **Customer-facing change: none by default.** Defaults reproduce today's behaviour exactly
  (Refactor 2 invariant 1, Refactor 1 invariant 5). Customers notice nothing unless they opt into a
  posture change.
- **Revenue: uninterrupted.** Comms keeps running and selling throughout — it is the company's one
  revenue-bearing, real-user asset (`04-platform-model.md` §6.2), and this scope never takes it
  offline.
- **What the company gains: proof + instrument.** Three platform primitives move from *claimed* to
  *proven against real traffic and a real regulator*; the agent-comms BET moves from *asserted* to
  *measured*; the M4 primary transaction (published work-artifact) gets its first live instance
  (intra-org).
- **What is deliberately deferred: the orchestration spine** (multi-step, retrace-replay,
  agent↔agent, cross-org) — out of scope here by design, because comms cannot demonstrate it and
  forcing it would corrupt the asset for no proof (§6, §5.3).
- **Reversibility: high.** Each re-pointing is an adapter behind comms' existing behaviour; defaults
  preserve current behaviour; backing out is reverting an adapter, not unwinding a rewrite.

### 5.3 What NOT to over-engineer (explicit non-goals)

These are the gold-plating temptations to refuse — each would burn effort for no proof comms can
actually deliver:

- **Do NOT rewrite comms to be "platform-native."** Comms' value is that it is *deployed and
  working*; a rewrite trades a proven asset for an unproven one. Re-point, don't rebuild.
- **Do NOT generalize the learning loop from answers to artifacts inside comms.** That leap
  (data-level → process-level knowledge capture) is the platform's real build, not comms' job
  (§2.2; `09-comms-wedge-mapping.md` §6.1). Comms proves the *mechanism*; the platform generalizes
  the *type*.
- **Do NOT wire comms into cross-org artifact sharing.** That requires the untrusted-publisher trust
  model — the genuinely-new, unbuilt, load-bearing 5% that must be designed *first* because it
  constrains the cross-org surface (`04-platform-model.md` §7.3 cons, §9 uncertainty #1). Wiring
  comms in before it exists is unsafe (a stranger's policy artifact running against a tenant's real
  customers).
- **Do NOT surface an explicit L3/L4/L5 posture ladder in comms onboarding.** It risks violating
  comms' non-technical onboarding budget (`specs/onboarding.md`; §3.2). Keep posture invisible by
  default; surface only a plain-language optional control.
- **Do NOT add ERP/CRM connectors to comms.** Comms stays a single-tool-cluster vertical; expanding
  its connector surface tests nothing the connector *pattern* doesn't already prove, and
  connectivity is commodity (`04-platform-model.md` §5.2).
- **Do NOT build step-level retrace-and-replay into comms.** Comms is single-step within one
  tool-cluster; retrace-replay needs multi-step cross-system objectives comms doesn't have
  (`09-comms-wedge-mapping.md` §6.2). It is the M1 engine — the platform's real build (§6.1).

### 5.4 Symmetric pros and cons of the recommended scope

**Pros (real):**

- **Proves three load-bearing claims cheaply and against real data.** The ledger, posture, and the
  published-artifact transaction get live, real-traffic, real-regulator validation for ~4 sessions
  of work — far cheaper than proving them on a greenfield vertical (`09-comms-wedge-mapping.md` §4).
- **Lights the agent-comms BET instrument.** Comms is the *only* asset that can move the BET from
  asserted to measured today (§4.2), using a human-takeover boundary it already records.
- **Zero revenue interruption, zero customer disruption.** Defaults preserve behaviour; comms keeps
  earning (§5.2).
- **Maps onto machinery that already runs.** The ledger pattern, the posture machinery, and the
  artifact splitter all exist in the ecosystem (`04-platform-model.md` §7.3 pros) — the work is
  adaptation, not invention.
- **Establishes the intra-org-first cold-start sequence in practice.** Refactor 3 (intra-org publish
  + consume) is the recommended cold-start path made concrete (`04-platform-model.md` §6.3).

**Cons (real, not glossed):**

- **It proves the spine, not the orchestration.** Even fully done, comms demonstrates
  trust/feedback/transparency/isolation — *not* multi-step cross-system work, retrace-replay,
  agent↔agent, or cross-org sharing (`09-comms-wedge-mapping.md` §6.5). A founder must not read a
  green comms lighthouse as "the platform works" — only "the platform's foundation works."
- **The agent-comms BET reading is vertical-bounded.** A positive reading in comms is evidence for
  the BET in *customer-comms*, and comms can't test agent↔agent at all (§4.2 caution). The sharpest
  form of the BET stays unmeasured here.
- **The posture-as-user-choice vision stays unexercised.** Integration proves posture-as-mechanism;
  the brief's user-chosen-L3/L4/L5-per-objective UX (§3e) is deferred to the platform build (§6.4),
  because forcing it into comms risks the onboarding budget.
- **Instrumentation effort competes with platform-build effort.** The ~1 session on
  instrumentation is ~1 session not spent on the orchestration spine. Mitigation: the BET reading
  is high-leverage PMF evidence (it could redirect the whole platform thesis), so it is worth the
  session — but it *is* a real opportunity cost, named honestly.
- **An [UNCONFIRMED] dependency exists.** Whether comms' email/WhatsApp adapters are already
  connector-shaped or need wrapping is unverified (`09-comms-wedge-mapping.md` §7 q2). If they need
  significant wrapping, Refactor 1's effort could grow. **[UNCERTAIN]** — flag to resolve by
  inspecting the adapters at `/todos` time before committing the estimate.

### 5.5 The single alternative considered, and why it loses

The one serious alternative is **"leave comms entirely alone; build the platform greenfield and
prove the primitives there."** **Why it loses:** it throws away the only deployed, real-user,
real-data proof the company has, forcing the platform to gather from scratch evidence comms already
provides (`09-comms-wedge-mapping.md` §4), *and* it leaves the agent-comms BET unmeasured until a
greenfield vertical ships (much later). The recommended scope gets the same proof for ~4 sessions
against live traffic. The alternative's *only* advantage — keeping comms untouched — is preserved
anyway by the recommendation's "defaults preserve behaviour, no rewrite" discipline. So the
alternative pays comms' full opportunity cost for none of its de-risking upside.

---

## 6. The boundary: what comms proves vs what remains the platform's real build

This section is the honest center (mirroring `09-comms-wedge-mapping.md` §6) so the founder reads
the lighthouse correctly. Comms is a proof of the *spine*, not the whole vision.

### 6.1 No multi-step cross-system objectives (the M1 engine is unexercised)

Comms is single-step within one tool-cluster: message in → classify → retrieve → respond/escalate
(`09-comms-wedge-mapping.md` §6.1). It never crosses ERP + Excel + Word for one objective (the
brief's "3Q financial report" example, §3e). The platform's harder claim — collapsing
ERP→CRM→POS→Excel→portals into one interface (`briefs/01-vision.md` §1) — is **not** tested by
comms. This is M1 territory (versioned, intervene-from-any-step work), the strongest moat and the
hardest build, and the strategic spine's named net-new work — comms does not de-risk it.

### 6.2 No step-level retrace / intervene with versioned cascades (M1, again)

The brief requires retrace-any-step-and-recascade with old outputs versioned (§3e). Comms has
*partial* versioning (immutable audit + learned-answer supersession) but **no** step-replay
(`09-comms-wedge-mapping.md` §6.2). Comms' "intervention" is binary (approve/edit/compose one
reply), not a graph-replay. The platform-DNA points at where this lives — PACT's `EventBridge` +
`SupervisorOrchestrator` for multi-step gated execution — but neither is wired into comms
(`09-comms-wedge-mapping.md` §6.2). **This is the platform's real build; comms does not touch it.**

### 6.3 No cross-org artifact sharing (M4's network-effects half is unexercised)

Comms tenants are sealed silos by design (`09-comms-wedge-mapping.md` §6.3). Refactor 3 proves the
*intra-org* publish/consume loop (transaction B within a tenant boundary) — it does **not** open the
cross-org exchange, which is the M4 network-effects engine and depends on the untrusted-publisher
trust model that must be designed first (§5.3; `04-platform-model.md` §9 uncertainty #1). The
lighthouse proves the loop *within* an org; the *across*-org marketplace is unproven by comms.

### 6.4 Secondary gaps (agent↔agent, user-chosen posture, team workspace)

- **Agent↔agent communication** — comms is sequential single-agent; no multi-agent dialogue
  (`09-comms-wedge-mapping.md` §6.4). The sharpest form of the agent-comms BET stays unmeasured
  (§4.2 caution).
- **User-chosen-posture-per-objective** — Refactor 2 proves posture-as-mechanism; the brief's
  explicit L3/L4/L5-chosen-beforehand UX (§3e) stays a platform-build question (§3.2, §5.4 con).
- **Team-oriented interface** (M3) — comms is single-operator-per-account; escalation is a hand-off,
  not a shared human+agent workspace (`09-comms-wedge-mapping.md` §6.4). The team substrate (moat
  M3) is unexercised.

### 6.5 The boundary stated plainly

> Comms, fully integrated and instrumented, is the **trust/feedback/transparency/isolation spine
> proven against real users and real data, plus a live instrument for the agent-comms BET in one
> vertical.** It is a credible, cheap demonstration that the scary foundational questions — when
> does the agent act vs ask vs pause, can human corrections become durable knowledge cheaply, can
> every action be traced PDPA-cleanly, can orgs be isolated to a compliance bar, can a way-of-working
> be published as a governed artifact intra-org — are *solvable and shipped*. What remains, and what
> the platform's real build is, is the **orchestration spine**: M1 (multi-step versioned
> retrace-from-any-step) and the cross-org half of M4. Comms does not detour from that build; it
> de-risks the foundation the orchestration spine stands on, and it keeps the company
> revenue-bearing and BET-instrumented while that spine is built.

This is why **Decision A is correct**: subsume comms as the wedge, keep the architecture horizontal
(the 80% spine), light it as the lighthouse, and let the orchestration spine — not comms — be the
platform's real, harder build.

---

## 7. Handoff to `/todos`

The four shards below are the concrete `/todos` candidates. Each carries a value-anchor (per
`rules/value-prioritization.md` MUST-2) citing a user-anchored source, and is sized within the
per-session capacity budget.

| Shard | What | Value-anchor (user-anchored source) | Size |
| ----- | ---- | ----------------------------------- | ---- |
| **S1** | Run comms audit writer on the shared provenance-ledger interface (Refactor 1) | Proves the M1/M4 ledger substrate against real traffic + PDPA — `briefs/01-vision.md` §3f ("every activity and output is traced and made transparent") | ~1 session, ≤5 invariants |
| **S2** | Replace comms' hard-coded confidence bands with a posture lookup, default-equivalent (Refactor 2) | Proves M2 (the ship-first moat) on a live high-stakes objective — `briefs/01-vision.md` §3e (posture chosen beforehand: L5/L4/L3) | ~1 session, ≤5 invariants |
| **S3a/3b** | Publish an account's routing config as a versioned signed artifact; let a second same-org account install + run it (Refactor 3) | Proves M4's primary transaction (published work-artifact) intra-org — `briefs/01-vision.md` §3g ("artifacts created, modified, stored, and shared across organizations and teams") | ~2 sessions, ≤5 invariants each |
| **S4** | Instrument the escalation boundary + learning loop for the de-risking + agent-comms-BET readings (probe-driven) | Measures the agent-comms BET — `briefs/01-vision.md` §3d (hypothesis: human↔human comms is incomplete vs agent comms) | ~1 session |

**Open items to resolve at `/todos` time before committing estimates** (flagged [UNCERTAIN] /
[UNCONFIRMED] above): (1) are comms' email/WhatsApp adapters already connector-shaped, or do they
need wrapping? — inspect at adapter-internals depth (`09-comms-wedge-mapping.md` §7 q2); (2) how
much of the platform's retrace-recascade primitive can reuse comms' existing versioning vs needing
PACT's `EventBridge` wholesale? (`09-comms-wedge-mapping.md` §7 q3) — this is a *platform-build*
question surfaced by comms, not a comms shard; (3) the posture-surfacing UX decision (invisible
default vs optional plain-language control) needs the founder's call at the `/todos` gate (§3.2).

**Approval-gate questions for the founder** (per `rules/communication.md` § Approval Gates): Does
this cover what Decision A intended — comms subsumed as the proven wedge + lighthouse? Is anything
here you did *not* want (e.g. is the ~1-session instrumentation worth deferring the orchestration
spine by that much)? Is anything missing you expected — in particular, do you want comms to surface
the explicit posture choice to customers now, or keep it invisible-by-default as recommended?

---

## 8. Source index (files actually consulted)

- **Brief:** `~/repos/projects/Sequor/workspaces/future-of-work/briefs/01-vision.md` (§1 disruption
  thesis, §2 enabling shift, §3 target state incl. §3d agent-comms BET / §3e posture+retrace / §3f
  transparency / §3g cross-org artifacts, §4 Decisions A+B, §5 ecosystem-DNA reference table).
- **Comms-wedge mapping:** `01-analysis/01-research/09-comms-wedge-mapping.md` (§0 exec summary, §1
  what comms does today, §2 primitive mappings, §3 objective/process/data triple, §4 de-risking,
  §5 80/15/5, §6 honest gaps, §7 open questions).
- **Platform model:** `01-analysis/04-platform-model.md` (§0 exec summary, §2 core transaction B+D,
  §3 producers, §4 consumers + governed install/run, §5 partners, §6 cold-start incl. §6.3
  intra-org-first, §7 recommended shape + pros/cons + non-goals, §9 uncertainty flags).
- **Specs index:** `~/repos/projects/Sequor/specs/_index.md` (and the cited domain specs:
  `response-accuracy.md`, `rag-pipeline.md`, `data-model.md`, `message-routing.md`,
  `channel-coordination.md`, `onboarding.md`).
- **Strategic spine:** carried inline in the analysis invocation (M1–M4 moat, Decisions A+B, the
  agent-comms BET, the Claude Cowork threat, the symmetric-cautions discipline).
- **Comms source references (via the mapping doc, not re-read at depth here):**
  `src/sequor/ai/response.py`, `src/sequor/ai/learning.py`, `src/sequor/ai/rag_pipeline.py`,
  `src/sequor/db/audit.py`, `src/sequor/db/schema_manager.py`.
