# User Flow 05 — The Comms Wedge End-to-End: the Instrumented Lighthouse

> User-flow output for the agentic-work-platform analysis (`/analyze`, Phase 01 → 03).
> Walks the **existing, deployed** Sequor comms experience as a **platform flow** — one
> concrete, SHIPPED instance that proves several platform primitives in one vertical
> (**Decision A**, `briefs/01-vision.md` §4: "comms is a wedge, not the product").
>
> **What this document is.** A step-by-step walk of one customer message moving through the
> comms product, from the user's screen, annotated at every step with the **platform
> primitive** that step exercises. This is not a feature tour — it is the proof that the
> platform's load-bearing claims (a traced provenance ledger, execution-time posture/HITL,
> a knowledge loop, hard tenant isolation) already run against real users and real data.
>
> **Grounds in** (every claim cites one of these or the brief): the comms-wedge mapping
> (`01-analysis/01-research/09-comms-wedge-mapping.md`), the comms-wedge integration plan
> (`02-plans/05-comms-wedge-integration-plan.md`), and the two domain specs that govern the
> walked path: `specs/response-accuracy.md` (governance + escalation) and
> `specs/rag-pipeline.md` (retrieval + learning). The brief is
> `briefs/01-vision.md`. Where a claim is an inference about the _platform-lens reading_
> rather than the shipped comms behaviour, it is flagged **[PLATFORM-LENS]**. Where a
> behaviour described is shipped-today, it cites the spec section that governs it.
>
> **Plain-language note** (per `rules/communication.md` + `rules/recommendation-quality.md`):
> written for a non-technical founder. Every technical term is translated on first use.
> Outcomes are described as the user sees them on screen, not as code.
>
> **Two readers, two columns.** Each step is told twice: first **what the user sees** (the
> comms product as it ships today), then **what the platform sees** (the primitive that step
> instruments). Comms is the **lighthouse**: a lit, watched proof that the platform's
> navigation system works — not the destination.

---

## 0. The whole flow in one picture

```
  CUSTOMER                 SEQUOR COMMS (today)                  PLATFORM LENS (the primitive)
 ──────────────────────────────────────────────────────────────────────────────────────────
  sends a message    →   1. message arrives (email/WhatsApp)  →  CONNECTOR (data via a tool)
                          │                                       + TENANT ISOLATION (sealed silo)
                          ▼
                         2. AI drafts a reply from the           RAG agent loop (retrieve →
                            knowledge base (RAG)                  answerability → synthesize →
                          │                                       hallucination-check)
                          ▼
                         3. confidence badge + accountability  →  POSTURE / HITL (act/ask/pause)
                            (who-did-what-to-whom recorded)       + PROVENANCE LEDGER (traced)
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼               ▼
        >90% auto    60-90% review    <60% compose      →  L5 / L4 / L3  (the posture ladder)
            │         (human gate)    (human gate)          ESCALATION = the L-GATE
            │             └──────┬───────┘
            ▼                    ▼
        4. sent             human answers  →  customer    →  HITL GATE fires; a human takes over
                                 │
                                 ▼
                         5. the human's answer is LEARNED  →  KNOWLEDGE-CONTRIBUTION transaction
                            (becomes durable knowledge)        + AGENT-COMMS instrumentation
                                 │
                                 ▼
                         6. daily digest (what happened)   →  the watched meters on the lighthouse
```

Six steps. Each one is a vertical specialization of a primitive the **platform** must offer
for _every_ kind of work — not a comms-specific invention (`09-comms-wedge-mapping.md` §2).
The rest of this document walks each step from the user's screen and names the primitive.

---

## 1. Step 1 — A customer message arrives (email or company WhatsApp)

### What the user sees

A customer of the business sends a message. It lands one of two ways
(`09-comms-wedge-mapping.md` §1.1; `specs/response-accuracy.md` §"Escalation Paths"):

- **Email** — the customer emails the business's address (e.g. `hello@acme-clinic.sg`). This
  is the primary, always-on channel — there is no time window, a customer can email at 3am
  and the system handles it (`09-comms-wedge-mapping.md` §1.1).
- **Company WhatsApp** — the customer messages the business's WhatsApp number. This is a
  **company-owned business number** (not an employee's personal phone), running through an
  approved messaging provider (`09-comms-wedge-mapping.md` §1.1). WhatsApp has a hard rule:
  the business can only send free-form AI replies within **24 hours** of the customer's last
  message; after that, only pre-approved template messages (`09-comms-wedge-mapping.md` §1.1).
  The product is honest about this limit and never promises round-the-clock WhatsApp
  coverage.

From the customer's side, nothing looks unusual — they sent a message to a business and
expect a reply. From the **business operator's** side (the person whose inbox is covered),
nothing happens yet on their screen — the system is working before they ever look.

### What the platform sees

Two platform primitives are exercised the instant the message lands.

**(a) The connector — data reached through a tool.** Email (via standard mail protocols) and
WhatsApp (via the messaging provider) are **adapters**: the agent reaches the data it needs
(the message, the conversation thread) by calling an external system, not by holding the data
itself (`09-comms-wedge-mapping.md` §5.1 "Connectors"; `02-plans/05-comms-wedge-integration-plan.md`
§2.4). In platform terms this is the **integration layer** — the foundation of _agnosticism_
(the platform's promise that it can talk to any system). The brief's whole thesis is that
today a worker is the integration layer, manually crossing ERP → CRM → POS → Excel → portals
(`briefs/01-vision.md` §1); the platform makes the _agent_ the integration layer, reaching
each system through a connector (`briefs/01-vision.md` §2). **The inbox is one data source; an
ERP is another.** Nothing in the comms architecture is hostile to adding more connectors —
they are simply more tools the same agent calls (`09-comms-wedge-mapping.md` §3).

> [PLATFORM-LENS] What comms proves here: the _pattern_ (data-via-tools) generalizes. What it
> does **not** prove: that the agent can sequence across _several_ systems for one objective —
> comms reaches one knowledge base, not an ERP _and_ a CRM _and_ a spreadsheet in sequence
> (`09-comms-wedge-mapping.md` §6.1). See §7 (the boundary).

**(b) Tenant isolation — the message lands in a sealed silo.** The message belongs to exactly
one business (one **tenant**). Each business's data lives in its own dedicated, hermetically
separate database compartment; no business can read another's data _by architecture_, not by
permission setting (`09-comms-wedge-mapping.md` §1.4; `specs/rag-pipeline.md` §"Access
Control": "Cross-tenant document access is impossible by architecture (separate schemas)").
This is the platform's **multi-org boundary** — the privacy floor that makes a multi-customer
platform possible at all (`02-plans/05-comms-wedge-integration-plan.md` §2.3). The boundary is
built to a real regulator's bar (Singapore's data-protection law, with a 72-hour
breach-notification clock — `09-comms-wedge-mapping.md` §4.4), so the platform inherits a
_battle-tested_ isolation pattern rather than an untested one.

> [PLATFORM-LENS] Comms proves the _hard-isolation half_ of the multi-org boundary (keep
> tenants apart). It deliberately does **not** prove the _controlled-permeability half_
> (deliberately sharing an artifact across the boundary) — comms tenants are sealed silos by
> design (`09-comms-wedge-mapping.md` §6.3). Cross-org sharing is the platform's real,
> unbuilt M4 work (the network-effects engine) and depends on a trust model that must be
> _designed first_ (`02-plans/05-comms-wedge-integration-plan.md` §5.3). See §7.3.

---

## 2. Step 2 — The agent drafts a response from the knowledge base (RAG)

### What the user sees

Behind the scenes, the AI reads the customer's message and tries to answer it from the
business's own knowledge — its uploaded documents (price lists, FAQs, policies, rosters) plus
everything the system has _learned_ from past human answers (Step 5). The user (the business
operator) still sees nothing on their screen at this point unless the message needs them — the
agent is doing the work first.

"RAG" means **retrieval-augmented generation**: the AI answers _from_ the business's documents
rather than from its own general memory (`02-plans/05-comms-wedge-integration-plan.md` §2.4).
This matters because the product's founding rule is **"sending wrong information is worse than
sending none"** (`specs/response-accuracy.md` §"Core Design Principle"). An AI that makes
things up is the single biggest risk; the entire pipeline is built to prevent that.

The drafting runs as a careful, multi-stage check (`specs/rag-pipeline.md` §"Retrieval Flow";
`09-comms-wedge-mapping.md` §1.2):

1. **Find candidate answers.** The system searches the business's documents for passages that
   match the customer's question — combining meaning-based search with keyword search
   (`specs/rag-pipeline.md` §"Query Processing": hybrid vector + keyword).
2. **Check each candidate actually answers the question.** The AI is asked, for each passage,
   "does this _actually answer_ the question, yes or no?" A passage that merely _looks_ related
   but doesn't answer is dropped — even if it matched well on similarity
   (`specs/rag-pipeline.md` §"Retrieval Confidence Scoring": "If answerability < 0.3, the
   passage is excluded even if vector similarity is high").
3. **Write the answer, citing sources.** The AI drafts a reply using only the surviving
   passages, and is instructed: "Do not add information not present in the retrieved documents.
   Cite each factual claim with a source. If you are uncertain, say so"
   (`specs/rag-pipeline.md` §"Synthesis").
4. **Double-check for made-up claims.** A _second_ AI pass verifies every factual claim in the
   draft is backed by a cited source. If too many claims are uncited, the draft is rejected and
   sent to a human instead (`specs/rag-pipeline.md` §"Hallucination Detection (Post-Synthesis)":
   ">50% of claims un-cited: response is rejected, routed to backup").
5. **Flag stale sources.** If the answer rests on a document that hasn't been updated in a
   while, the reply carries a warning that the information may be outdated
   (`specs/rag-pipeline.md` §"Index Age Tracking"; `specs/response-accuracy.md` §"Staleness
   Detection").

Some questions never go through this at all. **High-stakes questions** — anything touching
medical, legal, or financial matters — are _never_ auto-answered; they go straight to a human
(`specs/response-accuracy.md` §"High-Stakes Query": "The product MUST NOT attempt RAG
resolution for queries flagged as high-stakes").

### What the platform sees

This is the **agent loop** — the runtime that classifies the message, retrieves relevant data,
synthesizes a response, and decides what to do with it (`09-comms-wedge-mapping.md` §5.1
"Runtime"). In the comms vertical it is a _special-cased_ loop (classify → RAG → respond →
route). The platform's general runtime is the same loop generalized: the agent harness driving
artifacts and tools for _any_ objective, not just "answer a customer" (`briefs/01-vision.md`
§2; `09-comms-wedge-mapping.md` §3). Comms' RAG modules become **one objective-type's skill
set** inside the general runtime.

The hallucination controls (steps 2–4 above) are the comms-specific answer to a question the
platform must answer for _every_ high-stakes objective: **how do we make sure the agent's
output is grounded in real evidence, not invented?** The cite-every-claim discipline and the
post-draft verification pass are the evidence-grounding mechanism, proven against real,
messy SME documents (`specs/rag-pipeline.md` §"Pre-Build Validation: RAG on Real SME
Documents"). That de-risks the platform's grounding primitive.

---

## 3. Step 3 — The confidence badge, the posture decision, and the recorded action

This is the load-bearing step — the one that proves the **two** primitives the platform must
ship first: execution-time **posture/HITL** (M2) and the **provenance ledger** (the substrate
beneath M1 and M4).

### What the user sees

Every AI-drafted reply carries a **confidence badge** — a fixed label that says, in effect,
"I'm X% confident this answer is correct" (`specs/response-accuracy.md` §"Confidence Badge
Specification"). The badge is **not editable by the AI and not configurable by the user** — it
is a fixed governance control, a permanent honesty signal (`specs/response-accuracy.md`
§"Badge Display": "The badge MUST NOT be editable by the AI or configurable by the user — it
is a fixed governance control"; `09-comms-wedge-mapping.md` §1.6).

The badge then drives a three-way decision about **whether to send the reply, ask a human
first, or hand the whole thing to a human** (`specs/response-accuracy.md` §"Option C —
REQUIRED"; `09-comms-wedge-mapping.md` §1.6):

| Confidence     | What happens                                                                                                                                                | What the user sees                                                                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **above ~90%** | the reply is **sent automatically**, badge attached                                                                                                         | nothing in the moment; a line in the daily digest (Step 6) saying it was handled                                                                     |
| **60–90%**     | the reply is **held and escalated to a human** with the AI's draft attached, for the human to **approve, edit, or rewrite** before it sends                 | a structured email: the customer's message + the AI draft + the confidence badge + the cited sources, with "reply to this email to send your answer" |
| **below 60%**  | the reply is escalated to a human **without** sending the draft — the human **composes** the answer (a suggested draft may be included for them to rewrite) | a structured email: the customer's message + classification reasoning + any sources found (even if empty), "compose your answer and reply"           |

The human's entire interface is their **email inbox** — there is no dashboard to log into. An
escalation arrives as a normal, structured email; the human replies to it to resolve it; that
reply goes to the customer (`09-comms-wedge-mapping.md` §1.5; `specs/response-accuracy.md`
§"Audit Trail": "No dashboard login required — everything is in the inbox").

### What the platform sees

**(a) The posture ladder — act / ask / pause.** The three confidence bands are _structurally
the same shape_ as the platform's graduated trust posture — the three plain-language buttons
the brief describes, each mapped onto one engine rung pinned internally and never shown to the
user (engine-internal: "Go ahead" = L5 `AUTONOMOUS`, "Ask me once" = L4 `DELEGATING`, "Step
through" = L3 `SUPERVISED` — `briefs/01-vision.md` §3e; `04-trust-posture…` §1.2;
`09-comms-wedge-mapping.md` §2.1; `02-plans/05-comms-wedge-integration-plan.md` §2.1):

| Comms band (today)                     | Platform posture (button)                         | Plain meaning                                          |
| -------------------------------------- | ------------------------------------------------- | ------------------------------------------------------ |
| above 90% → auto-send                  | **"Go ahead"** — the agent proceeds               | "Let the agent do it; tell me after."                  |
| 60–90% → escalate _with_ a draft       | **"Ask me once"** — the agent prepares, asks once | "The agent prepares it; I approve before it goes out." |
| below 60% → escalate _without_ a draft | **"Step through"** — the human drives             | "The agent pauses; I take over."                       |

This is the platform's **execution-time, posture-graded governance** — moat **M2**, the one the
strategy says to _ship first_ (`02-plans/05-comms-wedge-integration-plan.md` §2.1). The
mapping is structural, not analogical: comms runs a real act/ask/pause decision on every
single message, against a live high-stakes objective (`09-comms-wedge-mapping.md` §2.1).

**The escalation IS the L-gate.** When a reply falls into the 60–90% or below-60% band, the
message stops and waits for a human — that pause-and-wait is exactly what the platform calls a
**human-in-the-loop gate** (HITL). The confidence band _chooses which gate fires_; the
escalation _is_ the gate firing. So comms is not "an email tool that sometimes asks a person"
— it is a **working HITL governance system**, where the question "when does the agent act vs
ask vs pause?" is answered automatically per message and proven against real traffic
(`02-plans/05-comms-wedge-integration-plan.md` §4.1).

> [PLATFORM-LENS] The one difference between comms-today and the full platform vision: comms
> **hard-codes** which band applies (the confidence score picks it). The platform lets the
> _user choose the posture beforehand_, per objective (`briefs/01-vision.md` §3e). The
> integration plan's Refactor 2 closes exactly this gap — replace the hard-coded thresholds
> with a posture the user selects, _defaulting to today's bands so nothing changes for
> customers on day one_ (`02-plans/05-comms-wedge-integration-plan.md` §3.2). The confidence
> _score_ stays (it is the evidence); only _where the thresholds live_ moves from code to a
> chosen posture. Even after that refactor, comms proves posture **as a mechanism**, not the
> brief's full user-facing L3/L4/L5 _choice_ UX — surfacing an explicit ladder risks comms'
> non-technical onboarding promise, so the plan recommends keeping it invisible-by-default
> (`02-plans/05-comms-wedge-integration-plan.md` §3.2, §6.4).

**(b) The provenance ledger — every action is traced.** Alongside the posture decision, _every
state change in the message's life_ is recorded as an append-only, permanent, tamper-resistant
audit row: message received → classified → sources retrieved → response generated → sent (or
escalated) → escalation acknowledged → escalation resolved (`specs/response-accuracy.md`
§"D/T/R Accountability"; `09-comms-wedge-mapping.md` §1.6, §2.3). Each row records three
things — **D**oer (which agent or person did it), **T**ype (what action), **R**ecipient (who
it affected). This vocabulary ("D/T/R", read "who-did-what-to-whom") is the platform's
**accountability grammar** (`specs/response-accuracy.md` §"D/T/R Accountability (PACT
Governance)"; `09-comms-wedge-mapping.md` §2.3).

The audit trail has three hard properties the platform inherits:

- **Append-only and immutable** — actions are recorded forever, never edited or deleted
  (`specs/response-accuracy.md` §"Audit Trail": "Immutable (append-only; no deletion)").
- **Tenant-isolated** — no business can see another's audit log (`specs/response-accuracy.md`
  §"Audit Trail").
- **Free of personal data by design** — so that when a customer exercises their
  right-to-erasure, the audit trail does not need to be touched (`09-comms-wedge-mapping.md`
  §4.3: "AuditEntry is PII-free by design, so erasure does not touch it").

In platform terms this audit log is the **first writer to the provenance ledger** — the shared,
signed, traced record of every action and artifact-change that the rest of the platform will
build on (`02-plans/05-comms-wedge-integration-plan.md` §0, §3.1). That ledger is the substrate
beneath **two** moats: **M1** ("intervene from any step; old outputs versioned" — you can only
go back and intervene if every step was recorded) and **M4** ("trust a stranger's artifact
because its provenance is recorded and recallable"). Comms running on it is the first
real-traffic proof the ledger holds under load _and_ under a real privacy regime
(`02-plans/05-comms-wedge-integration-plan.md` §3.1, §4.1).

> [PLATFORM-LENS] What comms proves about the ledger: it works, it's PDPA-clean, it's
> tenant-scoped, it survives real traffic. What comms does **not** yet prove: the _step-level
> retrace-and-replay_ the ledger ultimately enables — comms records every step but cannot "go
> back to the classification step, change it, and re-cascade the downstream response"
> (`09-comms-wedge-mapping.md` §6.2). Comms' intervention is binary (the human approves /
> edits / composes _one_ reply), not a graph-replay. That replay engine is M1 — the
> platform's real build (§7.2).

---

## 4. Step 4 — Low confidence escalates to a human (the HITL gate fires)

### What the user sees

When confidence is below the auto-send line, the message _stops_ and waits for a person. The
business operator (or their designated backup) gets a structured escalation email
(`specs/response-accuracy.md` §"Semi-Routine Query" / §"Complex Query"). They do exactly what
they'd do anyway — read it, decide the answer, and reply. Their reply goes to the customer.

The system also protects against the human being unavailable. If nobody responds within a set
window (default **4 hours**), the message **auto-escalates** up a chain — account owner →
primary backup → second-tier backup (`09-comms-wedge-mapping.md` §1.5;
`specs/response-accuracy.md` §"Semi-Routine Query": "If no reply within SLA window (default: 4
hours), auto-escalate to backup contact"). If a backup is also out of office, it goes to the
next tier; if there's no one left, it's logged as pending and the primary is alerted on return
(`specs/response-accuracy.md` §"Error States and Fallbacks").

From the operator's seat, the experience is: _the things you needed to handle show up in your
inbox, already triaged, with the AI's best attempt attached when it has one._ The things you
_didn't_ need to handle were handled, and you'll see a summary of those tomorrow (Step 6).

### What the platform sees

This is the **HITL gate firing** — the moment the platform's posture decision routes control
to a human because the agent's confidence didn't clear the bar (`02-plans/05-comms-wedge-integration-plan.md`
§4.2). In platform terms, the escalation is **the L-gate in action**: the agent reached a step
it could not complete to the required confidence, so it _paused and asked_ rather than
_proceeded_ — exactly the L4/L3 behaviour the posture ladder defines (§3 above).

This step is also where the platform's most valuable measurement happens (§6, the lighthouse
reading). Every escalation is a **recorded moment where the agent's communication was judged
insufficient and a human took over** (`02-plans/05-comms-wedge-integration-plan.md` §4.2). The
escalation boundary is the instrument: how often the agent suffices vs needs a human, and
whether that ratio improves over time, is direct evidence for or against the platform's
central bet (that agent-mediated communication can beat human-mediated communication —
`briefs/01-vision.md` §3d). More on that in §6.

The auto-escalation chain (owner → backup → second-tier, on a clock) is the comms instance of
the platform's **coordination** primitive — routing work to the right human when the first one
is unavailable (`09-comms-wedge-mapping.md` §5.1 "Coordination"). The general form of this
lives in the platform-DNA repos as supervisor/approval orchestration, but comms proves the
_simplest useful version_ — a timed hand-off chain — works end-to-end.

---

## 5. Step 5 — The human's answer is learned (the knowledge-contribution transaction)

### What the user sees

This is the quiet magic of the product, and most users never consciously notice it. When a
human resolves an escalation by replying to the escalation email, the system **captures that
answer and remembers it forever** (`specs/rag-pipeline.md` §"Learning from Human Answers";
`09-comms-wedge-mapping.md` §1.3).

Concretely (`specs/rag-pipeline.md` §"How It Works"):

1. The human's reply is captured along with the original customer question.
2. The system creates a new knowledge entry: _this question → this answer_.
3. That entry is indexed alongside the uploaded documents.
4. The next time a similar question comes in, the AI can answer it _from the learned answer_ —
   no human needed.

The human did nothing extra. They just replied to an email, as they would have anyway. But the
business's coverage **compounds with use**: the product's own projection is coverage rising
from 0% on day one (no documents) to 60–70% by month six, _purely through usage_
(`specs/rag-pipeline.md` §"Knowledge Base Composition Over Time";
`09-comms-wedge-mapping.md` §1.3). This is the design's answer to the real-world problem that
most small businesses don't have clean, organized documents to start with
(`specs/rag-pipeline.md` §"Learning from Human Answers" §"Purpose": "The learning loop removes
the document dependency — the product gets smarter through usage, not through upfront document
preparation").

There are honesty controls on what gets learned (`specs/rag-pipeline.md` §"Quality Controls"):
only confirmed resolutions are learned (not half-finished drafts); each learned answer is
attributed to the human who gave it, with a timestamp; if a later answer contradicts an earlier
one, the more recent wins (the older is retained, not destroyed); and the operator can review
learned answers in a weekly digest and flag wrong ones for removal.

### What the platform sees

This is the **knowledge-contribution transaction** — the platform's secondary, faster-cycling
transaction that keeps the platform's knowledge improving without anyone hand-authoring it
(`02-plans/05-comms-wedge-integration-plan.md` §2.2). And it is the **only part of the entire
platform thesis already proven end-to-end against real users** today
(`02-plans/05-comms-wedge-integration-plan.md` §0, §2.2).

The mechanism is **byproduct capture**: a human does their normal job (replies to an email),
and the system harvests the residue as durable knowledge — no separate "training" step
(`02-plans/05-comms-wedge-integration-plan.md` §2.2). In platform terms this is the human↔agent
**feedback loop**: the human corrected/completed what the agent couldn't do, and that
correction became institutional knowledge (`09-comms-wedge-mapping.md` §2.2). It is the same
_shape_ as the platform's broader "human-validated knowledge becomes a reusable artifact" loop
(`09-comms-wedge-mapping.md` §2.2).

**The agent-comms instrumentation angle — the lighthouse's primary reading.** Because every
escalation-then-learning event is a recorded boundary (the agent fell short → a human took
over → the residue was captured), this loop is also the natural _instrument_ for the platform's
central, unproven bet: that agent-mediated communication can beat human-mediated communication
(`briefs/01-vision.md` §3d; `02-plans/05-comms-wedge-integration-plan.md` §2.2, §4.2). Comms
can measure the things that turn that bet from _asserted_ into _measured_ — see §6.

> [PLATFORM-LENS] The honest generalization gap: comms learns **answers** — data-level
> knowledge, a single question→answer pair. The full platform needs to learn **artifacts** —
> process-level knowledge, a procedure or rule that's reusable across objective-types
> (`09-comms-wedge-mapping.md` §2.2; `02-plans/05-comms-wedge-integration-plan.md` §2.2). Comms
> proves the _mechanism_ (human intervention → durable knowledge, cheaply, as work exhaust);
> generalizing the _type_ of knowledge captured is the platform's real build, deliberately
> **not** asked of comms (`02-plans/05-comms-wedge-integration-plan.md` §5.3). See §7.

---

## 6. Step 6 — The daily digest (the watched meters on the lighthouse)

### What the user sees

Once a day, the business operator gets a **digest email** summarizing what happened:
what was auto-handled (and how confident the AI was on each), what was escalated, what's still
pending, and what new knowledge was learned (`09-comms-wedge-mapping.md` §1.7;
`specs/response-accuracy.md` §"Audit Trail": "a summary email of all messages received during
OOO, what was auto-resolved (and the confidence of each), what was escalated, and what is still
pending"). On higher tiers, a weekly recap adds trends (`09-comms-wedge-mapping.md` §1.7).

This is the operator's whole window into the system. No dashboard, no login — the digest is
the report, delivered to the same inbox the operator already lives in. It closes the loop: the
operator stated the intent once (at onboarding — "cover this communication point"), and the
system reports back what it did with that mandate.

### What the platform sees

The digest is the human-facing surface of what makes comms a **lighthouse** rather than just a
working product: it is **lit and watched**. Behind the digest, the same recorded data feeds the
platform's two kinds of continuous reading (`02-plans/05-comms-wedge-integration-plan.md` §4):

**(a) The de-risking readings — do the primitives hold?**
(`02-plans/05-comms-wedge-integration-plan.md` §4.1)

- **Does the provenance ledger hold under load and under the privacy regime?** Measured by:
  every action recorded successfully, zero cross-tenant leakage, and the audit trail never
  needing to be touched during a customer erasure (it's personal-data-free by design).
- **Does posture-graded governance produce _safe_ automation?** Measured by the act/ask/pause
  distribution and — critically — the **wrong-send rate** (how often an auto-sent reply was
  later corrected). The product's founding principle is "wrong info is worse than none"
  (`specs/response-accuracy.md`); the wrong-send rate is the direct measure of whether the
  posture bands are calibrated (`02-plans/05-comms-wedge-integration-plan.md` §4.1).

**(b) The PMF-discovery reading — is the agent-comms bet true?** This is the highest-value
thing comms produces for the platform (`02-plans/05-comms-wedge-integration-plan.md` §4.2). The
escalation boundary (§4) plus the learning loop (§5) yield direct evidence:

- **Sufficiency ratio over time** — what fraction of messages the agent handles without a human
  taking over, and whether it _rises_ as learned answers accumulate. A rising ratio supports
  the bet; a flat ratio argues against it in this vertical
  (`02-plans/05-comms-wedge-integration-plan.md` §4.2; the spec's own 0% → 60-70% projection,
  `specs/rag-pipeline.md` §"Knowledge Base Composition Over Time").
- **Resolution quality at the boundary** — do agent-mediated exchanges resolve faster / more
  completely / with fewer back-and-forths than the human-takeover ones?
- **Knowledge-compounding rate** — how fast the learned-answer base grows.

> [PLATFORM-LENS] These semantic measurements (e.g. "did the agent's reply _actually resolve_
> the customer's question?") MUST be **probe-driven** — a structured query with a defined
> expected answer and a deterministic scoring rule — never a keyword count over the reply text
> (`02-plans/05-comms-wedge-integration-plan.md` §4.2, per `rules/probe-driven-verification.md`).
> Counts, rates, and timings stay deterministic. This keeps the lighthouse's bet-reading
> honest: it measures whether the _behaviour_ happened, not whether a _word_ appeared.

> [PLATFORM-LENS] The honest caution on the bet-reading: comms is a _narrow_ communication
> vertical (customer/stakeholder coverage), and its pipeline is **sequential single-agent
> calls** — there is no agent-to-agent dialogue in it (`09-comms-wedge-mapping.md` §6.4;
> `02-plans/05-comms-wedge-integration-plan.md` §4.2). So comms can measure "agent-mediated
> _human↔customer_ comms vs human-mediated," but it **cannot** measure "agent↔agent vs
> human↔human" — the _sharper_ form of the bet. The lighthouse lights one channel of the
> harbour, not all of them.

---

## 7. The boundary — what this flow does NOT yet exercise

This is the honest center of the document. The flow above is a working, deployed proof of
**five-to-six platform primitives in one vertical** — a connector, hard tenant isolation, the
grounded agent loop, posture/HITL governance, the provenance ledger, and the
knowledge-contribution loop. That is a credible, de-risking demonstration that the _scary
foundational questions_ are solvable and shipped (`09-comms-wedge-mapping.md` §6.5;
`02-plans/05-comms-wedge-integration-plan.md` §6.5).

But comms proves the **spine**, not the whole vision. It exercises the
_trust/feedback/transparency/isolation_ spine; it does **not** exercise the _orchestration_
spine. A founder must not read a green comms lighthouse as "the platform works" — only as "the
platform's _foundation_ works." Three gaps are explicit.

### 7.1 No multi-step cross-system objectives (the M1 engine is unexercised)

Comms is **single-step within one tool-cluster**: a message comes in → the agent classifies →
retrieves → responds or escalates (`09-comms-wedge-mapping.md` §6.1;
`02-plans/05-comms-wedge-integration-plan.md` §6.1). There is no objective that spans systems —
the brief's "I want the 3Q financial report → agent spins up 3 agents → crosses ERP + Excel +
Word" example (`briefs/01-vision.md` §3e) is _not_ tested. Comms' agent calls one knowledge
base, not an ERP _and_ a CRM _and_ a spreadsheet in sequence. The platform's harder claim —
collapsing ERP → CRM → POS → Excel → portals into one interface (`briefs/01-vision.md` §1) — is
**not** exercised by this flow. This is M1 territory (the strongest moat, the hardest build),
and comms does not de-risk it.

### 7.2 No step-level retrace / intervene with versioned cascades (M1, again)

The brief requires: "users can retrace any previous step and intervene from there;
downstream/cascading outputs change accordingly, but old outputs are versioned"
(`briefs/01-vision.md` §3e). Comms has **partial** versioning — its audit trail is immutable
and append-only, and learned answers supersede earlier contradicting ones with the prior
retained (§3, §5). But comms has **no step-level retrace-and-replay**: there is no "go back to
the classification step, change it, and re-cascade the downstream response"
(`09-comms-wedge-mapping.md` §6.2;`02-plans/05-comms-wedge-integration-plan.md` §6.2). Comms'
intervention is **binary** — the human approves, edits, or composes _one_ reply — not a
graph-replay. The retrace-intervene-recascade-with-versioning primitive (moat M1) is **not**
exercised by this flow. It is the platform's real build.

### 7.3 No cross-org artifact sharing (M4's network-effects half is unexercised)

Comms tenants are **sealed silos by design** (§1; `09-comms-wedge-mapping.md` §6.3). The one
cross-tenant flow that exists is an _anonymized routing aggregate_ — and that is _data
aggregation_, not _artifact sharing_; no comms tenant can take another tenant's response policy
and reuse it (`09-comms-wedge-mapping.md` §6.3). The integration plan's Refactor 3 proves the
_intra-org_ publish/consume loop (one account's policy reused by _another account in the same
company_) — but it deliberately does **not** open the _cross-org_ exchange
(`02-plans/05-comms-wedge-integration-plan.md` §2.3, §6.3). Cross-org sharing is moat M4's
network-effects engine and depends on an **untrusted-publisher trust model** that must be
_designed first_ — wiring comms into it before that model exists would be unsafe (a stranger's
policy artifact running against a tenant's real customers)
(`02-plans/05-comms-wedge-integration-plan.md` §5.3). The lighthouse proves the loop _within_
an org; the _across_-org marketplace is unproven by comms.

### 7.4 Secondary gaps

- **Agent↔agent communication** — comms is sequential single-agent; there is no multi-agent
  dialogue in the flow (`09-comms-wedge-mapping.md` §6.4). The _sharpest_ form of the
  agent-comms bet (agent↔agent vs human↔human) stays unmeasured (§6).
- **User-chosen-posture-per-objective** — the flow proves posture _as a mechanism_; the
  brief's explicit L3/L4/L5-chosen-beforehand _UX_ (`briefs/01-vision.md` §3e) is a
  platform-build question, kept invisible-by-default in comms to protect the non-technical
  onboarding promise (`02-plans/05-comms-wedge-integration-plan.md` §3.2, §6.4).
- **Team-oriented interface** (moat M3) — comms is single-operator-per-account; an escalation
  is a _hand-off_, not a _shared human+agent workspace_ (`09-comms-wedge-mapping.md` §6.4;
  `02-plans/05-comms-wedge-integration-plan.md` §6.4). The team substrate is unexercised.

---

## 8. The flow, read as the lighthouse

Stated plainly (mirroring `09-comms-wedge-mapping.md` §6.5 and
`02-plans/05-comms-wedge-integration-plan.md` §6.5):

> This six-step flow, viewed through the platform lens, is the
> **trust/feedback/transparency/isolation spine proven against real users and real data, plus a
> live instrument for the agent-comms bet in one vertical.** Each step the customer's message
> passes through exercises a platform primitive: the message _arrives_ through a connector into
> a sealed tenant silo (integration + isolation); the agent _drafts_ through a grounded RAG
> loop (the runtime); the _confidence badge and three-band decision_ are posture/HITL with the
> escalation as the L-gate (M2); _every action recorded_ is the provenance ledger (the
> substrate beneath M1 and M4); the _escalation_ is the HITL gate firing; the _learned answer_
> is the knowledge-contribution transaction (the secondary M4 loop, the only part of the thesis
> already proven end-to-end); and the _daily digest_ is the watched meter on the lighthouse.
>
> What this flow does **not** exercise — and what the platform's real, harder build is — is the
> **orchestration spine**: multi-step cross-system objectives, step-level retrace/intervene
> with versioned cascades (M1), agent↔agent coordination, and cross-org artifact sharing (the
> network-effects half of M4). Comms does not detour from that build; it de-risks the
> _foundation_ the orchestration spine stands on, and it keeps the company revenue-bearing and
> bet-instrumented while that spine is built.

This is why **Decision A is correct**: subsume comms as the wedge, keep the architecture
horizontal (the 80% spine), light it as the lighthouse — and let the orchestration spine, not
comms, be the platform's real, harder build (`09-comms-wedge-mapping.md` §6.5;
`02-plans/05-comms-wedge-integration-plan.md` §6.5).

---

## 9. Source index (files actually consulted)

- **Brief:** `~/repos/projects/Sequor/workspaces/future-of-work/briefs/01-vision.md` (§1
  disruption thesis, §2 enabling shift, §3d agent-comms bet / §3e posture+retrace / §3f
  transparency / §3g cross-org artifacts, §4 Decision A).
- **Comms-wedge mapping:**
  `~/repos/projects/Sequor/workspaces/future-of-work/01-analysis/01-research/09-comms-wedge-mapping.md`
  (§1 what comms does today, §2 primitive mappings, §3 objective/process/data triple, §4
  de-risking, §5 80/15/5, §6 honest gaps).
- **Comms-wedge integration plan:**
  `~/repos/projects/Sequor/workspaces/future-of-work/02-plans/05-comms-wedge-integration-plan.md`
  (§0 exec summary, §2 feature→primitive mappings, §3 the three re-pointings, §4 the
  instrumented lighthouse / de-risking + PMF readings, §5 scope recommendation, §6 the
  boundary).
- **Specs (the walked path):** `~/repos/projects/Sequor/specs/response-accuracy.md`
  (Option C 3-tier routing, confidence badge, D/T/R accountability, escalation paths,
  high-stakes routing, audit trail, error-state fallbacks); `~/repos/projects/Sequor/specs/rag-pipeline.md`
  (retrieval flow, answerability cross-check, synthesis, hallucination detection, staleness,
  learning from human answers, knowledge-base composition over time, access control).
- **Strategic spine:** carried inline in the analysis invocation (M1–M4 moat, Decisions A+B,
  the agent-comms bet, the comms-as-lighthouse framing).
