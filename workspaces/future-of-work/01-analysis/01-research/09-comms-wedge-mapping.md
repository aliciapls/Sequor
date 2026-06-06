# 09 — Comms as the Canonical Wedge: Mapping the Existing Product into the Platform, and the 80/15/5 Reuse Breakdown

> Research output for the agentic-work-platform analysis (`/analyze`, Phase 01).
> Addresses **Decision A** (comms is a wedge, not the product) from `briefs/01-vision.md` §4,
> and derives the product-focus **80/15/5 reuse split** the brief requires (§6).
>
> Grounding: every claim below cites a real file in this repo or in the platform-DNA
> repos named in `briefs/01-vision.md` §5. Where a claim is an inference (not yet built),
> it is flagged **[INFERENCE]**. Where a source could not be confirmed, it is flagged
> **[UNCONFIRMED]**.

---

## 0. Executive Summary

The existing Sequor product — an AI email/WhatsApp communication-coverage layer (RAG
response generation, schema-per-tenant isolation, confidence badges, escalation/SLA,
D/T/R accountability, learning-from-human-answers, daily digest, email-first onboarding) —
is **not a detour from the platform vision. It is a working, deployed proof of several
platform primitives, instantiated in one vertical.**

The thesis of `briefs/01-vision.md` §1 is that all staff work decomposes into three things:
an **objective**, **company-specific processes**, and **data**. The comms product is exactly
this triple, pre-specialized: the objective-type is "cover a communication point";
the company-specific process is the routing/escalation/response policy (per-account config);
the data is the inbox + the knowledge base via channel connectors. The platform's job is to
generalize that triple to _any_ objective-type, _any_ process, _any_ connector.

Five platform primitives already run in production-shaped code inside Sequor:

| Platform primitive (target state)                     | Already instantiated in comms as…                                       | Source of truth                                                                            |
| ----------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Trust posture / HITL graduated autonomy**           | Confidence badges + 3-tier confidence routing (auto / review / compose) | `specs/response-accuracy.md` §"Option C"; `src/sequor/ai/response.py:103-123`              |
| **Human↔agent feedback loop**                         | Learning-from-human-answers (escalation reply → knowledge chunk)        | `specs/rag-pipeline.md` §"Learning from Human Answers"; `src/sequor/ai/learning.py:54-122` |
| **Transparency / accountability (D/T/R)**             | AuditEntry rows on every state transition (Doer/Type/Recipient)         | `specs/response-accuracy.md` §"D/T/R"; `src/sequor/db/audit.py:23-61`                      |
| **Multi-org boundary / tenant isolation**             | Schema-per-tenant PostgreSQL isolation                                  | `specs/data-model.md` §"Multi-Tenancy"; `src/sequor/db/schema_manager.py:77-131`           |
| **Company-specific process as configurable artifact** | Per-account `routing_rules` JSONB + routing templates A/B/C             | `specs/data-model.md` §Account; `specs/onboarding.md` §"Step 5"                            |

The 80/15/5 split (derived in §5) places these primitives squarely in the **80% agnostic
reusable core**, the per-account config in the **15% client-configurable self-service** layer,
and almost nothing in the **5% true custom** layer.

The honest counter-weight (§6): comms does **not yet** exercise the harder half of the vision —
multi-step cross-system objectives, step-level retrace/intervene with versioned outputs, or
cross-org artifact sharing. Comms proves the _trust/feedback/transparency/isolation_ spine; it
does not prove the _orchestration_ spine. That gap is the platform's real build, and comms is
the credible early demonstration that the spine works against real users and real data.

---

## 1. What the comms product does today (precise summary)

This section is the factual baseline. Everything is grounded in `specs/` and `src/sequor/`.

### 1.1 Channels: email + WhatsApp on a company-owned number

- Each **Account** (a "communication point" — an individual like a secretary, or a
  department like HR/Operations) independently configures channels: email only, WhatsApp
  only, or both (`specs/message-routing.md` §"Per-Account Channel Configuration";
  `specs/data-model.md` §Account `channels: enum[]`).
- WhatsApp runs on a **company-owned Business API number** via an approved BSP (Twilio,
  Bird, Infobip), not employees' personal WhatsApp (`specs/message-routing.md` §13, §BSP).
- WhatsApp's **24-hour session window** is a hard constraint: free-form AI replies only
  inside the window; pre-approved template messages after it closes
  (`specs/message-routing.md` §"Session Window"). The product explicitly MUST NOT promise
  multi-day continuous WhatsApp coverage.
- Email is the **primary, unconstrained** async channel; it is also the escalation
  substrate for both channels (`specs/message-routing.md` §"Channel Priority").
- Source modules exist per channel: `src/sequor/email/` (inbound, parser, sender,
  auto_reply, rate_limiter, templates) and `src/sequor/whatsapp/` (inbound, parser,
  sender, auto_reply, rate_limiter, signature).

### 1.2 RAG response generation with hallucination controls

The pipeline (`src/sequor/ai/rag_pipeline.py`) is a real, multi-stage RAG:

1. **Retrieve** — query embedding → hybrid search (vector 0.7 + BM25 0.3) via
   `VectorStore` (`rag_pipeline.py:66-147`; `specs/rag-pipeline.md` §"Retrieval Flow").
2. **Answerability cross-check** — an LLM scores "does this passage actually answer the
   question?" and multiplies it into the passage score; passages below threshold are
   dropped even at high vector similarity (`rag_pipeline.py:149-189`).
3. **Synthesis** — top-5 passages → LLM with a "cite every claim, do not add information
   not in the passages" system prompt (`rag_pipeline.py:231-248`).
4. **Post-synthesis hallucination check** — a second LLM call verifies every factual claim
   is cited; >50% uncited → confidence reduced / rejected (`rag_pipeline.py:307-363`;
   `specs/rag-pipeline.md` §"Hallucination Detection").
5. **Staleness** — documents older than a per-type threshold are flagged in the badge
   (`specs/rag-pipeline.md` §"Staleness Detection").

### 1.3 Learning from human answers (the document-free path)

- Every time a human resolves an escalation by replying to the escalation email, the
  reply + the original client query become a new knowledge chunk
  `{question, answer}`, embedded and indexed alongside uploaded documents
  (`src/sequor/ai/learning.py::capture_human_answer` lines 54-122; `specs/rag-pipeline.md`
  §"Learning from Human Answers").
- Learned answers carry `source_type = human_answer`, are attributed to the human + a
  timestamp, and a later answer supersedes an earlier contradicting one
  (`learning.py:124-162`; `specs/rag-pipeline.md` §"Quality Controls").
- This removes the upfront-document dependency: coverage rises from 0% (day 0) to a stated
  60-70% (month 6) purely through usage (`specs/rag-pipeline.md` §"Knowledge Base
  Composition Over Time").

### 1.4 Tenant isolation: schema-per-tenant

- Each tenant gets a dedicated PostgreSQL schema (`tenant_<hex>`), with private copies of
  all tenant-scoped tables; the public schema holds only the tenant registry
  (`src/sequor/db/schema_manager.py:1-5, 63-131`).
- Schema names are deterministic from the UUID and pass `validate_identifier()` before any
  DDL interpolation (`schema_manager.py:71-74, 91-92`) — consistent with this repo's
  `rules/dataflow-identifier-safety.md`.
- Spec is explicit that shared-schema-with-`tenant_id` is **NOT** sufficient for Singapore
  PDPA; schema separation is the compliance boundary (`specs/data-model.md`
  §"Multi-Tenancy Requirement").

### 1.5 Escalation, SLA, and the email-first interface

- 3-tier escalation chain (account owner → primary backup → second-tier) with a default
  4-hour SLA before auto-escalation (`specs/channel-coordination.md` §"Auto-Escalation";
  `src/sequor/escalation/` — service, scheduler, sla, thread_key).
- The **entire human interface is the inbox**: unresolved items arrive as structured
  emails; replying-to-resolve sends the response to the client and captures the answer for
  learning; ignoring triggers auto-escalation (`specs/channel-coordination.md`
  §"Email-First Escalation Interface", §"Reply-to-Resolve").

### 1.6 Confidence badges + D/T/R accountability (already present)

- **Confidence badges** are a fixed governance control (high / moderate / low / uncertain),
  NOT editable by the AI or configurable by the user
  (`specs/response-accuracy.md` §"Badge Display"; `src/sequor/ai/rag_pipeline.py:281-288`).
- **3-tier confidence routing** (`specs/response-accuracy.md` §"Option C — REQUIRED"):
  - > 90% confidence (+ good synthesis, routine, not complex) → **auto-send**
  - 60-90% → **escalate WITH an AI draft** for human review/approval
  - <60% → **escalate WITHOUT a draft** for the human to compose
  - implemented at `src/sequor/ai/response.py:103-123` (the `was_auto_sent` /
    `escalation_has_ai_draft` decision).
- **D/T/R accountability**: every state transition writes an AuditEntry with
  Doer (ai_agent / backup_contact / user / system), action Type, and Recipient
  (`specs/response-accuracy.md` §"D/T/R Accountability (PACT Governance)";
  `src/sequor/db/models.py` AuditEntry; `src/sequor/db/audit.py:23-61`). Audit rows are
  append-only, immutable, tenant-isolated, and PII-free by design
  (`specs/data-model.md` §"Immutability and Audit Integrity", §"Erasure implementation").

### 1.7 Daily digest + email-first onboarding

- **Daily digest** email summarizes auto-handled / pending / escalated / newly-learned
  (`specs/channel-coordination.md` §"Daily Digest Email"; `src/sequor/digest/service.py`);
  weekly recap (Professional+) adds trends.
- **Onboarding** is 5 non-technical steps, no app required, first account active in <10
  minutes, documents optional (`specs/onboarding.md` §"Onboarding Flow (5 Steps)").
  The "Configuration Complexity Budget" forbids requiring the user to understand vectors,
  embeddings, RAG, BSPs, or confidence numbers (`specs/onboarding.md` §"Configuration
  Complexity Budget").

### 1.8 The routing-intelligence flywheel (a sixth primitive in embryo)

- Every routing decision writes a `RoutingOutcome` record; a nightly job aggregates per
  category/industry and updates per-tenant `RoutingThresholdConfig`; new tenants inherit
  cross-tenant (anonymized) defaults (`specs/message-routing.md` §"Routing Intelligence
  Flywheel"; `specs/data-model.md` §RoutingOutcome / RoutingThresholdConfig /
  RoutingOutcomeAggregate). This is an early instance of **institutional knowledge capture**
  — the platform-level "artifacts compound and improve" primitive (§3.6 below).

---

## 2. Comms features are already instances of platform primitives

This is the load-bearing section for Decision A. Each comms feature below is **not a
comms-specific invention** — it is a vertical specialization of a primitive the broader
platform must offer for _every_ objective-type. The platform-DNA repos already implement the
general form of each primitive; comms is the applied form.

### 2.1 Confidence badges + 3-tier routing IS posture/HITL in a vertical

**Comms form** (`specs/response-accuracy.md` §"Option C"; `src/sequor/ai/response.py`):
a per-message decision among auto-send / human-review-with-draft / human-compose, gated by
a confidence score, with a fixed non-editable badge as the transparency control.

**General platform form** — graduated trust posture L1–L5, per `briefs/01-vision.md` §3e:

- **L5 Autonomous** — agent goes ahead → comms "auto-send (>90%)"
- **L4 Supervised** — agent asks one permission before executing → comms "escalate WITH AI
  draft (60-90%): the human approves/edits the draft before it sends"
- **L3 Step-by-step** — agent pauses at each step → comms "escalate WITHOUT draft (<60%):
  the human composes"

The general primitive already exists in the ecosystem and is the _exact same shape_:

- `loom/.claude/rules/trust-posture.md` defines the L1–L5 ladder (L5_DELEGATED …
  L1_PSEUDO_AGENT), automatic downgrade on violation, human-gated upgrade — grounded in
  CARE Principle 7 and EATP "downgrade instantly if conditions change."
- `aegis/.claude/rules/trust-posture.md` + the cryptographic posture anchors at
  `aegis/proj-*/anchors/anc-posture-*.json` are the commercial L1–L5 state-machine
  implementation the brief names as "the closest existing implementation."
- EATP's `PostureStore` / `PostureStateMachine` (`kailash/trust/posture_store.py`,
  surfaced in skill `26-eatp-reference/eatp-posture-stores.md`) is the SDK-level persistence
  contract for posture.

**The mapping is structural, not analogical.** Comms hard-codes a 3-band confidence policy
into Python (`response.py:103-123`); the platform generalizes that to a _per-objective,
user-chosen posture_ selected beforehand (`briefs/01-vision.md` §3e: "users can choose a
posture beforehand"). Comms is posture with N=3 fixed bands and one objective-type. The
platform is posture with L1–L5 chosen per objective across all objective-types. **Same
primitive; comms is the constrained instance.**

> [INFERENCE] To slot comms into the platform, the hard-coded confidence bands in
> `response.py` would be replaced by a posture lookup (the user's pre-selected posture for
> the "comms coverage" objective) — turning a code constant into a configurable artifact.
> The confidence _score_ stays (it is the evidence); the _band thresholds_ become posture.

### 2.2 Learning-from-human-answers IS the human↔agent feedback loop

**Comms form** (`src/sequor/ai/learning.py:54-122`; `specs/rag-pipeline.md` §"Learning from
Human Answers"): a human resolves an escalation; the system captures `{question, answer}`,
embeds + indexes it, and future matching queries are answered from the learned answer
(`src/sequor/ai/response.py:200-253` `_generate_from_learned`).

**General platform form** — `briefs/01-vision.md` §3e: "make all human↔agent and agent↔agent
communications/working steps transparent and interveneable." The comms learning loop is the
_captured residue_ of a human intervention: the human corrected/completed what the agent
could not do, and that correction became durable institutional knowledge.

This is the same shape as the platform's **codify → artifact** loop:

- In COC (`loom/.claude/`), human-validated knowledge is captured at `/codify` into
  artifacts (agents/skills/rules) that improve future runs; `loom/.claude/learning/
observations.jsonl` is the raw observation stream, `codify-lease.json` gates the capture.
- In comms, human-validated answers are captured at escalation-resolution into knowledge
  chunks that improve future answers; the `LearnedAnswer` table is comms' `observations`,
  and the escalation-resolution event is comms' `/codify` trigger.

**The mapping:** comms learns _answers_ (vertical knowledge for one objective-type). The
platform learns _artifacts_ (procedures, rules, skills — reusable across objective-types).
Comms proves the human-in-the-loop-produces-durable-knowledge mechanism end-to-end against
real users. The platform generalizes the _type_ of knowledge captured from "an answer to a
client" to "a procedure the company follows."

> [INFERENCE] Comms' learning loop captures _data-level_ knowledge (Q→A pairs). The
> platform's codify loop captures _process-level_ knowledge (artifacts). Comms does NOT yet
> capture process artifacts from human intervention — that is the generalization the platform
> adds. See §6 gap analysis.

### 2.3 D/T/R AuditEntry IS the transparency/accountability primitive

**Comms form** (`src/sequor/db/audit.py:23-61`; `specs/response-accuracy.md` §"D/T/R";
`specs/data-model.md` §AuditEntry): every action — message_classified, rag_retrieved,
response_auto_sent, escalation_routed, contact.pii_erased — writes an append-only,
immutable, PII-free audit row carrying Doer, action Type, and Recipient.

**General platform form** — `briefs/01-vision.md` §3f: "every activity and output is traced
and made transparent. The only thing not transparent is how the model (black box) thinks —
but input and output are transparent." Comms' AuditEntry is _exactly_ this: it records the
input/output of every agent action without claiming to record the model's internal reasoning
(the `Classification.reasoning` field stores the LLM's stated rationale, but the audit row
records the _fact and effect_ of the action).

This is the same accountability grammar PACT implements at platform scale:

- PACT's **D/T/R addressing** (Doer/Type/Recipient) is the general accountability primitive;
  comms' AuditEntry uses the identical D/T/R vocabulary (`specs/response-accuracy.md`
  literally titles the section "D/T/R Accountability (PACT Governance)").
- PACT's engine (`terrene/contrib/pact/src/pact_platform/engine/`:
  `orchestrator.py`, `approval_bridge.py`, `event_bridge.py`, `emergency_bypass.py`) is the
  platform-scale governance machinery; PACT's `Decision` / `ReviewDecision` records are the
  general form of comms' Response.approved_by_backup + AuditEntry pair.

**The mapping:** comms implements D/T/R as a single append-only table for one objective-type.
PACT implements D/T/R as a full governance engine (envelopes, clearance, supervisor
orchestration, approval bridges) across objective-types. Comms proves D/T/R as a _logging_
discipline; PACT generalizes it to D/T/R as a _control_ discipline (gates, not just records).

### 2.4 Schema-per-tenant IS the multi-org boundary

**Comms form** (`src/sequor/db/schema_manager.py`; `specs/data-model.md`
§"Multi-Tenancy Requirement"): one PostgreSQL schema per tenant; no tenant can read another's
data by architecture; this is the PDPA compliance boundary.

**General platform form** — `briefs/01-vision.md` §3g: "artifacts are easily created,
modified, stored, and **shared across organizations and teams**." The platform needs a
multi-org boundary that is _strong enough to isolate by default_ yet _permeable enough to
share artifacts deliberately_. Comms has built the strong-isolation half: a hard tenant
boundary at the schema level.

This is the same boundary concern the COC artifact-flow system manages:

- `loom`'s variant-overlay + Gate-1/Gate-2 distribution (`.claude/` artifact-flow) is the
  mechanism for sharing artifacts _across_ repos/orgs while preserving per-target isolation.
- The platform's tenant boundary = comms' schema-per-tenant (isolation) + loom's
  variant-overlay distribution (controlled sharing).

**The mapping:** comms proves hard tenant isolation against a real compliance regime (PDPA).
It does **not** yet do cross-org artifact sharing (§6 gap) — comms tenants are sealed silos.
The platform adds the controlled-permeability half (deliberate artifact sharing across the
boundary), which loom already demonstrates for COC artifacts.

### 2.5 Per-account routing config IS company-specific process as artifact

**Comms form** (`specs/data-model.md` §Account `routing_rules: JSONB`,
`confidence_threshold`, `escalation_sla_hours`, `backup_contact_ids`; `specs/onboarding.md`
§"Step 5: Routing Rules" templates A/B/C): each account carries its own process config —
which categories auto-respond vs escalate, who is in the escalation chain, the SLA timing,
the confidence threshold — selected from templates and stored as data, not code.

**General platform form** — `briefs/01-vision.md` §1b: "Processes/procedures to follow —
these vary from company to company." The platform's central claim is that company-specific
process becomes a _configurable artifact_, not bespoke code. Comms has already done this for
one process: routing/escalation/response policy is per-account JSONB + template selection.

This is the same shape as COC's artifact system (`loom/.claude/{agents,skills,rules,hooks,
commands}`): institutional process encoded as data/artifacts that the runtime consumes, not
hard-coded logic.

**The mapping:** comms encodes _one_ company-specific process (comms policy) as
per-account config. The platform generalizes to _any_ company process encoded as artifacts.
Comms' routing templates A/B/C are a primitive "process library"; the platform's artifact
system is the general process library across all objective-types.

### 2.6 The routing flywheel IS knowledge-compounding (a sixth primitive)

**Comms form** (`specs/message-routing.md` §"Routing Intelligence Flywheel";
`specs/data-model.md` §RoutingOutcomeAggregate): routing decisions compound into improved
defaults over time; cross-tenant anonymized aggregates seed new-tenant defaults.

**General platform form** — `briefs/01-vision.md` §6 names "institutional knowledge capture"
and the autonomous-execution rule values "knowledge compounding (zero onboarding)" as a 1.5–2×
multiplier (`rules/autonomous-execution.md` §"10x Throughput Multiplier"). Comms' flywheel is
the data-layer instance of the platform's knowledge-compounding primitive.

---

## 3. Comms as the canonical wedge: the objective/process/data triple

The brief (`briefs/01-vision.md` §1) decomposes all enterprise work into:
**(a) objective, (b) company-specific process, (c) data.** The cleanest way to see comms as a
wedge — not a detour — is to show it is _already_ this triple, pre-specialized:

| Brief's universal triple         | Comms specialization                                                                            | Platform generalization                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **(a) Objective / task**         | "Cover this communication point" — one objective-type: stakeholder/customer comms               | Any objective-type ("produce the 3Q financial report", "reconcile invoices") |
| **(b) Company-specific process** | Routing rules + escalation chain + confidence/response policy (per-account JSONB)               | Any company process, encoded as COC artifacts (skills/rules/commands)        |
| **(c) Data / information**       | The inbox (email/WhatsApp) + the knowledge base (docs + learned answers) via channel connectors | Any system (ERP/CRM/POS/Excel/portals) via MCP connectors                    |

**Why "customer/stakeholder communication" is a clean objective-type.** It is bounded
(messages in, responses out), high-frequency (so the flywheel compounds fast), has an
obvious correctness constraint ("sending wrong information is worse than sending none" —
`specs/response-accuracy.md` §"Core Design Principle"), and a natural human-in-the-loop
fallback (escalation to a backup). These four properties make it the _ideal first
objective-type_ to prove the trust/feedback/transparency spine — which is precisely why it is
the wedge.

**The same platform serves comms as one vertical and generalizes.** Concretely:

- The **runtime** that classifies → retrieves → synthesizes → routes for comms is a
  special-cased agent loop. The platform's runtime is the general agent loop (the CLI harness
  driving artifacts + MCP tools, `briefs/01-vision.md` §2). Comms' classifier/RAG/response
  modules become _one objective-type's skill set_ in the general runtime.
- The **connectors** comms uses (BSP/WhatsApp, IMAP/SMTP email, document parsers) become
  _instances_ of the platform's MCP connector layer. The inbox is one data source; an ERP is
  another. Nothing in the comms architecture is hostile to adding ERP/CRM connectors — they
  are more MCP tools the same agent calls.
- The **trust/transparency/isolation spine** (§2) is already objective-agnostic in shape; it
  is only _applied_ to comms. Re-pointing it at a new objective-type requires no rework of the
  spine, only new skills + connectors for the new objective.

This is the disruption thesis made concrete: today a secretary crosses email + WhatsApp +
the knowledge base + the escalation tooling (4 interfaces). Comms collapses that into one
email-first interface. The platform collapses _all_ of a worker's tools (ERP→CRM→POS→Excel→
portals, `briefs/01-vision.md` §1) into one CLI interface. **Comms is the same collapse,
scoped to the comms-tool-cluster.**

---

## 4. What comms already de-risks for the platform

Because comms is deployed (Vercel + Neon PostgreSQL, per `briefs/01-vision.md` §4) against
real users and real (messy SME) data, it provides evidence the platform would otherwise have
to gather from scratch:

1. **The correctness-vs-automation tension is solvable with posture/HITL.** Comms' whole
   design flows from "wrong info is worse than none" (`specs/response-accuracy.md`). The 3-tier
   confidence routing is a _working_ answer to the question the platform must answer for every
   high-stakes objective: when does the agent act, ask, or pause? This is the posture question.

2. **Human corrections can be captured as durable knowledge cheaply.** The learning loop
   (`learning.py`) shows that intervention residue can be captured at the moment of resolution
   with no separate "training" step — the human just replies, and the system learns. This
   de-risks the platform's feedback-loop primitive.

3. **D/T/R logging is tractable and PDPA-clean.** Comms' AuditEntry shows full action
   traceability _without_ storing PII in the audit trail (`specs/data-model.md`
   §"Erasure implementation": AuditEntry is PII-free by design, so erasure does not touch it).
   This is a non-obvious, hard-won design the platform inherits.

4. **Schema-per-tenant isolation passes a real compliance bar.** PDPA (Singapore) is a real
   regulator with a 72-hour breach-notification clock (`specs/data-model.md` §"Data Breach
   Response"). Comms' isolation boundary is built to that bar, giving the platform a
   battle-tested multi-org isolation pattern.

5. **Non-technical onboarding is achievable.** The <10-minute, no-app, email-first onboarding
   (`specs/onboarding.md`) is direct evidence for `briefs/01-vision.md` §3a ("users don't have
   to be coders").

---

## 5. The product-focus 80/15/5 reuse split

The brief (`briefs/01-vision.md` §6) requires an "80/15/5 reuse breakdown." Per the analyze
method, the split is by **reusability of the component across clients/objective-types**:

- **80% — agnostic reusable core.** Built once, serves every client and every objective-type.
- **15% — client-configurable self-service.** The client assembles/configures this themselves
  (no engineering) — their processes, their connectors, their postures, as artifacts/config.
- **5% — true custom.** Bespoke per-engagement engineering that cannot be generalized.

> **Framing note (per `rules/autonomous-execution.md`).** Effort below is in autonomous
> execution cycles/sessions, not human-days. The 80/15/5 is a _reuse_ ratio (what fraction of
> any given client deployment is reused vs configured vs bespoke), not a build-effort ratio.

### 5.1 The 80% — agnostic reusable core

This is the platform spine. It is objective-agnostic and client-agnostic. The comms wedge's
components that belong here (because they generalize unchanged):

| Core capability                           | Comms component that is an instance of it                                                          | General platform home                                                |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Runtime (agent loop)**                  | classify → RAG → respond → route loop (`src/sequor/ai/*`)                                          | CLI harness + agent loop (`briefs` §2)                               |
| **Artifact system**                       | routing-template engine + RAG skill (the comms "skills")                                           | `loom/.claude/{agents,skills,rules,hooks,commands}`                  |
| **Trust / posture (HITL graduated)**      | confidence badges + 3-tier routing (`response.py:103-123`, `response-accuracy.md`)                 | `trust-posture.md` L1–L5; EATP `PostureStore`; aegis posture anchors |
| **Transparency / accountability (D/T/R)** | AuditEntry append-only log (`db/audit.py`, `data-model.md` §AuditEntry)                            | PACT D/T/R + engine (`pact_platform/engine/`)                        |
| **Feedback loop (human↔agent)**           | learning-from-human-answers (`learning.py`)                                                        | COC codify loop (`loom/.claude/learning/observations.jsonl`)         |
| **Coordination**                          | escalation chain + SLA scheduler (`escalation/*`)                                                  | PACT `SupervisorOrchestrator`, `ApprovalBridge`, `EventBridge`       |
| **Connectors (data via tools)**           | email + WhatsApp/BSP adapters, document parsers (`email/*`, `whatsapp/*`, `ai/document_parser.py`) | MCP connector layer (any system as a tool)                           |
| **Multi-org isolation**                   | schema-per-tenant (`db/schema_manager.py`)                                                         | platform tenant boundary (isolation half)                            |
| **Versioning / audit trail**              | immutable AuditEntry + learned-answer supersession (`learning.py`, `data-model.md`)                | step-level versioned outputs (`briefs` §3e — **partially**; see §6)  |
| **Knowledge compounding**                 | routing flywheel (`message-routing.md` §Flywheel)                                                  | institutional knowledge capture (`autonomous-execution.md`)          |

**Why these are the 80%:** none of them are comms-specific in _concept_. The confidence-band
policy, the D/T/R log, the human-feedback capture, the tenant boundary, the connector pattern —
all are needed identically for an "invoice reconciliation" objective or a "3Q report"
objective. Comms is the _first instantiation_; the spine is reused.

### 5.2 The 15% — client-configurable self-service

This is what a client (or a non-technical operator) configures themselves to make the
platform fit their company — _their processes, their connectors, their postures_, all as
artifacts/config, no engineering. The comms wedge's components that belong here:

| Self-service surface                   | Comms instance                                                                                                                                | Generalizes to                                               |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Their process (as config/artifact)** | per-account `routing_rules` JSONB + escalation chain + SLA + template A/B/C selection (`data-model.md` §Account; `onboarding.md` §Step 5)     | per-objective procedure artifacts (their company's workflow) |
| **Their connectors**                   | which channels (email/WhatsApp), which inbox, which BSP number (`onboarding.md` §Step 2)                                                      | which systems to connect (ERP/CRM/Drive) via MCP             |
| **Their postures**                     | confidence threshold per account + "auto-send below 70% requires explicit ack" (`response-accuracy.md` §"Confidence Threshold Configuration") | per-objective L1–L5 posture chosen beforehand (`briefs` §3e) |
| **Their knowledge**                    | uploaded documents + accumulated learned answers (`onboarding.md` §Step 3; `learning.py`)                                                     | their domain knowledge base per objective                    |
| **Their people / routing targets**     | backup contacts, escalation tiers, owner emails (`data-model.md` §BackupContact)                                                              | their team roster + who-approves-what                        |

**Why these are the 15%:** they vary per client but require _no code_. The onboarding wizard
(`specs/onboarding.md`) is literally the self-service configuration surface for the comms
slice of this layer — it proves the 15% is achievable by non-technical users. The platform
generalizes the wizard to configure _any_ objective-type's process/connectors/postures.

### 5.3 The 5% — true custom

Bespoke, per-engagement, non-generalizable. In the comms wedge this is genuinely small:

| True-custom surface (comms)                                           | Why it resists generalization                                                                                                                                             |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| WhatsApp template message pre-approval per business + BSP onboarding  | Meta policy requires per-business template approval (`message-routing.md` §"Template Message Compliance"); the approval is an external, manual, business-specific process |
| Jurisdiction-specific compliance overlays beyond PDPA                 | `data-model.md` notes extensibility to Malaysia/Indonesia/etc., but each new regime needs bespoke legal mapping                                                           |
| Document cleanup service (optional paid accelerator)                  | `rag-pipeline.md` §"Document Cleanup Service" — a human-in-the-loop one-time service per messy-document client                                                            |
| Bespoke high-stakes keyword/category overrides for a regulated client | High-stakes always-escalate is default; a regulated client may need custom category definitions                                                                           |

**Why this is only 5%:** the comms architecture pushes almost everything into the 80% (spine)
or 15% (self-service). The residue is genuinely external (Meta's approval process, a
regulator's legal text) or genuinely one-off (a specific client's messy documents). This is
the _target_ ratio the platform should preserve across objective-types: keep custom work
external/one-off, push everything reusable into the spine, and everything client-specific into
self-service config.

### 5.4 The split, visualized

```
                    THE PLATFORM (80/15/5)
┌─────────────────────────────────────────────────────────────────┐
│ 80% AGNOSTIC CORE  (built once, every client, every objective)    │
│   runtime · artifacts · trust/posture · D/T/R transparency ·      │
│   human↔agent feedback · coordination · connectors(MCP) ·         │
│   multi-org isolation · versioning · knowledge-compounding         │
│   ── comms proves: badges/routing, AuditEntry, learning loop,      │
│      schema-per-tenant, escalation/SLA, channel adapters ──        │
├─────────────────────────────────────────────────────────────────┤
│ 15% CLIENT SELF-SERVICE  (configured, no engineering)              │
│   their processes (artifacts) · their connectors · their postures ·│
│   their knowledge · their people                                   │
│   ── comms proves: per-account routing JSONB, onboarding wizard,   │
│      confidence thresholds, doc upload, backup chain ──            │
├─────────────────────────────────────────────────────────────────┤
│ 5% TRUE CUSTOM  (bespoke, external, one-off)                       │
│   ── comms: WhatsApp template approval, new-jurisdiction legal,    │
│      doc-cleanup service, regulated-client overrides ──            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. The critical synthesis: comms is a proof of the spine, not the whole vision

This is the honest center of the analysis. Comms is **not a detour** — it is a working proof
of _five-to-six_ platform primitives in one vertical (§2), deployed against real users and
real data (§4). That is a credible, de-risking early demonstration of the platform's
_trust/feedback/transparency/isolation spine_.

But comms is **not the whole vision.** It proves the spine; it does not yet exercise the
_orchestration_ half of `briefs/01-vision.md` §3. Three gaps are explicit:

### 6.1 No multi-step cross-system objectives

Comms is **single-step within one tool-cluster**: a message comes in, the agent classifies →
retrieves → responds or escalates. There is no objective that spans systems
(`briefs/01-vision.md` §3e example: "I want 3Q financial report → agent spins up 3 agents →
crosses ERP + Excel + Word"). Comms' agent calls one knowledge base, not an ERP _and_ a CRM
_and_ a spreadsheet in sequence. The platform's harder claim — collapsing ERP→CRM→POS→Excel→
portals into one interface (`briefs` §1) — is **not exercised** by comms.

> What comms _does_ prove that helps here: the connector pattern (data via tools) and the
> agent loop generalize. What it does _not_ prove: multi-agent fan-out, cross-system
> sequencing, and the dependency-graph reasoning a multi-step objective requires.

### 6.2 No step-level retrace / intervene with versioned cascades

`briefs/01-vision.md` §3e requires: "users can retrace any previous step and intervene from
there; downstream/cascading outputs change accordingly, but old outputs are versioned."

Comms has **partial** versioning: AuditEntry is immutable and append-only
(`data-model.md` §AuditEntry), and learned answers supersede earlier contradicting ones with
the prior retained (`learning.py`; `rag-pipeline.md` §"Quality Controls"). But comms has **no
step-level retrace-and-replay**: there is no notion of "go back to the classification step,
change it, and re-cascade the downstream response." Comms' "intervention" is binary (the
human approves/edits/composes one response), not a graph-replay. The platform's
retrace-intervene-recascade-with-versioning primitive is **not exercised** by comms.

> The platform-DNA repos point at where this lives: PACT's `EventBridge` +
> `SupervisorOrchestrator` (`pact_platform/engine/`) is the orchestration substrate for
> multi-step gated execution; the COC phase system (`/analyze`→`/todos`→`/implement`) is the
> human-gated step model. Neither is wired into comms. This is the platform's real build.

### 6.3 No cross-org artifact sharing

`briefs/01-vision.md` §3g: "artifacts are easily created, modified, stored, and **shared
across organizations and teams**." Comms tenants are **sealed silos** by design
(schema-per-tenant, `data-model.md`). The _one_ cross-tenant flow is the anonymized routing
aggregate (`message-routing.md` §"Cross-Tenant Learning") — and that is _data aggregation_,
not _artifact sharing_. No comms tenant can take another tenant's routing template (artifact)
and reuse it. The platform's controlled-permeability primitive (deliberate artifact sharing
across the org boundary, which `loom`'s variant-overlay + Gate-1/Gate-2 distribution
demonstrates for COC artifacts) is **not exercised** by comms.

### 6.4 Also not yet exercised (secondary gaps)

- **Agent↔agent communication** (`briefs` §3d) — comms has no multi-agent dialogue; the
  classifier and RAG pipeline are sequential single-agent calls.
- **Pre-selected posture per objective** — comms' posture (confidence band) is a _fixed
  policy_, not a _user-chosen-beforehand_ posture per the L5/L4/L3 model (`briefs` §3e). The
  threshold is configurable (`response-accuracy.md`), but the L1–L5 ladder is not surfaced.
- **Team-oriented interface** (`briefs` §3d) — comms is single-operator-per-account
  (escalation is a hand-off, not a shared team workspace).

### 6.5 The synthesis stated plainly

> Comms is the **trust/feedback/transparency/isolation spine, proven in one vertical against
> real users and real data.** It is a credible early demonstration that the hard, scary parts
> of the vision — "when does the agent act vs ask vs pause," "can human corrections become
> durable knowledge," "can every action be traced PDPA-cleanly," "can orgs be isolated to a
> compliance bar" — are _solvable and shipped_.
>
> What remains — and what the platform's real build is — is the **orchestration spine**:
> multi-step cross-system objectives, step-level retrace/intervene with versioned cascades,
> agent↔agent coordination, and cross-org artifact sharing. Comms does not detour from that
> build; it de-risks the foundation the orchestration spine stands on, and it gives the
> platform a revenue-bearing, real-user landing vertical while the orchestration spine is
> built.

This is why **Decision A is correct**: subsume comms as the wedge, keep the architecture
horizontal/agnostic (the 80% spine), and let comms be the proof-and-landing-vertical rather
than the product.

---

## 7. Open questions for downstream analysis

1. **Posture surfacing.** Should the platform replace comms' fixed confidence-band policy
   with a user-selected L1–L5 posture per objective (§2.1, §6.4), and if so, does the comms UX
   (email-first, non-technical) survive surfacing an explicit posture choice? [INFERENCE-heavy]
2. **Connector unification.** Are the comms channel adapters (`email/*`, `whatsapp/*`)
   already shaped like MCP tools, or do they need wrapping to slot into the platform's MCP
   connector layer? (Not inspected at adapter-internals depth in this pass.) [UNCONFIRMED]
3. **Versioning depth.** Comms has immutable audit + answer supersession but no step-replay
   (§6.2). How much of the platform's retrace-recascade primitive can reuse comms' existing
   versioning, vs needing PACT's `EventBridge` orchestration wholesale?
4. **80/15/5 build sequencing.** The split is a _reuse_ ratio; the _build_ sequence (which
   spine primitives to harden first using comms as the test vertical) is a separate plan
   question for `02-plans/`.
5. **Cross-org sharing model.** What is the platform's artifact-sharing boundary policy
   (§6.3) — does it adopt loom's Gate-1/Gate-2 human-classification model, and how does that
   interact with comms' hard PDPA tenant isolation?
6. **Routing flywheel as platform primitive.** Is the cross-tenant anonymized aggregate
   (`message-routing.md` §Flywheel) generalizable to a platform-wide knowledge-compounding
   service, or is it comms-specific? (Privacy/aggregation design question.)

---

## 8. Source index (files actually consulted)

**Sequor specs:**

- `specs/_index.md`, `specs/message-routing.md`, `specs/rag-pipeline.md`,
  `specs/response-accuracy.md`, `specs/data-model.md`, `specs/channel-coordination.md`,
  `specs/onboarding.md`, `specs/business-model.md`

**Sequor source:**

- `src/sequor/auth.py`, `src/sequor/compliance.py`,
  `src/sequor/ai/rag_pipeline.py`, `src/sequor/ai/learning.py`,
  `src/sequor/ai/response.py`, `src/sequor/ai/classifier.py`,
  `src/sequor/db/audit.py`, `src/sequor/db/schema_manager.py`,
  module trees: `src/sequor/{ai,db,email,whatsapp,escalation,digest}/`

**Sequor config:** `CLAUDE.md`, `AGENTS.md` (present, 729 lines), this repo's `.claude/rules/`

**Platform-DNA repos (general-primitive grounding):**

- `briefs/01-vision.md` (authoritative vision)
- loom: `/Users/esperie/repos/loom/.claude/rules/trust-posture.md`,
  `/Users/esperie/repos/loom/.claude/learning/` (observations.jsonl, codify-lease.json,
  coordination-log.jsonl)
- pact: `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/`
  (orchestrator.py, approval_bridge.py, event_bridge.py, emergency_bypass.py),
  `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/models/`
- eatp: `26-eatp-reference/eatp-posture-stores.md` (PostureStore / PostureStateMachine;
  source `kailash/trust/posture_store.py`)
- aegis: `/Users/esperie/repos/dev/aegis/.claude/rules/trust-posture.md`,
  `/Users/esperie/repos/dev/aegis/proj-*/anchors/anc-posture-*.json`,
  `/Users/esperie/repos/dev/aegis/.claude/learning/`

**[UNCONFIRMED] notes:** pact's `AgenticObjective` / `Request` / `WorkSession` / `Decision` /
`ReviewDecision` / `Pool` / `ExecutionMetric` models are defined inside
`pact_platform/models/__init__.py` (a single module, not per-file); they were referenced from
the brief rather than read at field-level depth in this pass. aegis `posture.json` was not
found at the brief's stated path (`.claude/learning/posture.json`); aegis posture state was
instead confirmed via the cryptographic anchors `proj-*/anchors/anc-posture-*.json` and the
`trust-posture.md` rule.
