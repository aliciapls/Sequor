# Transparency & Provenance

> Status: TARGET-STATE (vision / not yet implemented). This spec describes the intended platform; the comms wedge (shipped) specs are separate.

This file is the domain authority for **what the platform records about its own work, how that record is structured, and how a non-coder sees and trusts it**. It is the spec-side counterpart to moats **M1** (transparent, versioned, intervene-from-any-step work) and **M2** (execution-time, posture-graded governance). It defines the transparency *contract* (the boundary between glass box and black box), the *provenance ledger* data model (the content-addressed, immutable, versioned DAG of work), how every activity and output is traced and attributed, how a planned fan-out is surfaced before it runs, and — for each capability — what is REUSED from ecosystem DNA versus what is NET-NEW.

This spec does NOT cover the cascade re-execution engine's internal algorithm (that is the intervention-and-versioning domain), the posture state machine's transition rules (the governance domain), or the timeline UI's interaction design (the frontend domain). It cites their contract points where they meet provenance.

Grounding: `workspaces/future-of-work/01-analysis/07-transparency-intervention-architecture.md` (architecture decision), `workspaces/future-of-work/02-plans/03-provenance-cascade-design.md` (design plan), `workspaces/future-of-work/01-analysis/01-research/06-transparency-intervention-versioning.md` (research). Every load-bearing claim cites one of these by section.

---

## 1. The transparency CONTRACT — what the platform promises to record

Plain statement: when an agent does a piece of knowledge work — drafts a report, reconciles an invoice, answers a customer — the platform records and can show you *everything the agent saw, decided, did, and produced*. The only thing it does not record is the model's private internal "thinking." This boundary is the single most important thing the contract defines, because a fuzzy boundary is a broken promise: over-claim ("we show you everything the AI does," false) or under-deliver ("we just log the final answer," no different from today). See analysis §2; plan §2.

The boundary is stated precisely so it travels with every trust claim:

> **We record everything the model emits at its input/output surface — including any reasoning summary it chooses to surface. We do not record, and do not claim to record, how the model actually computed its answer internally.**

(analysis §2.2; plan §2.2; research §5.3)

### 1.1 RECORDED and SURFACED — the glass box

For every step a human or agent takes, the ledger records and can display the following. This list is the OpenTelemetry GenAI Semantic Conventions span shape (an industry-standard schema the observability industry has converged on — Datadog, Honeycomb, New Relic; LangChain/CrewAI/AutoGen emit it natively), adopted rather than invented (analysis §2.1; research §5.1).

| Recorded & shown | Plain-language meaning | OTel GenAI attribute |
| --- | --- | --- |
| **Inputs** | Exactly what went into the step — the data, documents, prior results it consumed | `gen_ai.input.messages`, `gen_ai.system_instructions` |
| **Agent decisions, plans, and fan-outs** | The choices the agent made *before* acting — "I will split this into 3 sub-tasks and run them in parallel" — the plan is a first-class, inspectable object | surfaced as a `Decision` node (§2.4) |
| **Tool calls** | Every external action requested: which tool, with what arguments — "send email to X," "query the Q3 sales DB" | `execute_tool` child spans (name, arguments) |
| **Tool results** | What each tool returned — the rows, the API response, the file it read | `execute_tool` span result |
| **Outputs** | What the step produced — the draft, the number, the decision, the message — versioned | `gen_ai.output.messages`, `finish_reasons` |
| **Metadata** | Model id, cost, time taken, and *which posture was in force when the step ran* | `gen_ai.request.model`, `gen_ai.usage.{input,output}_tokens`, plus `posture_at_time` (§2.1) |

The structure is a tree of spans: a top-level *agent-invocation* span, with child *chat* spans (one per model call) and *tool-execution* spans (one per external action) (analysis §2.1; research §5.1–5.2).

### 1.2 The one subtlety — summarized reasoning is IN, chain-of-thought is OUT

Some model providers expose a *summarized reasoning trace* — a short, model-generated explanation of its approach — which is distinct from raw chain-of-thought. Where a model voluntarily emits such a summary at its output surface, the platform records it (the EATP SDK at `/Users/esperie/repos/loom/kailash-py` has an explicit `reasoning-traces` slot for exactly this — research §5.3). Recording the summary the model chose to surface is correct; claiming to reconstruct the hidden computation is not (analysis §2.2; plan §2.2).

### 1.3 NOT recorded — the black box

Deliberately not recorded:

| NOT recorded | Why we cannot / should not record it |
| --- | --- |
| The model's **chain-of-thought** (internal step-by-step scratchpad) | Often not exposed by the model interface; unstable across model versions; frequently the most sensitive content (research §5.3) |
| The model's **internal activations / weights** | Billions of opaque numbers; recording them explains nothing a human could act on |
| **Token-level logits** (*why* it picked one word over another) | Not human-interpretable; explains nothing in business terms |

### 1.4 The honesty caveat — traceability, not accountability

The contract delivers **traceability**, not **accountability**, and product/marketing copy MUST state this (analysis §2.3; research §5.3):

- **Traceability** (the machine guarantees this): every AI action can be traced back to its inputs, its decisions, and the human authority that permitted it.
- **Accountability** (no software can guarantee this): that a human actually *understood*, evaluated, and bears the consequences of what the agent did.

The transparency surface converts traceability into a *chance* at real accountability — it makes understanding *possible* — but it cannot force it. The platform promises the glass box; it does not promise that the human looked through it. Over-claiming here is dishonest and legally hazardous.

**Reuse vs new for §1.** REUSED: the OTel GenAI span shape (industry standard); the Kailash Core SDK already emits it via `TracingLevel.{NONE,BASIC,DETAILED,FULL}` (research §5.2) — `/Users/esperie/repos/loom/kailash-py`; the EATP `reasoning-traces` slot. NET-NEW: the precise boundary statement as a product contract, and the durable projection of the ephemeral spans into the provenance ledger (§2.5).

---

## 2. The PROVENANCE LEDGER — the data model

"Provenance" means the recorded origin and history of every piece of work — what produced it, from what, and when. The ledger is the permanent, queryable record that makes everything in §1 inspectable, every output attributable, and the intervention feature possible.

The central finding: this data model **already exists** as the pact platform's work-tracking records at `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/models/__init__.py` — it has simply never been wired as a unified, retrace-capable provenance DAG (research §1.1; analysis §3; plan §1.1).

### 2.1 The three node kinds

The ledger is a **DAG** (a directed acyclic graph — records connected by one-way arrows that never loop back). It has exactly three node kinds, each mapping to an existing pact model. **This table is the canonical Step/Output/Decision data model for the whole platform — the intervention-and-versioning domain references this section rather than restating it.**

| Node kind | Maps to pact model | What it is | Load-bearing fields |
| --- | --- | --- | --- |
| **Step** | `Run` | One invocation — one model call, one tool call, one workflow run | `step_id` (content hash — the Step's OWN identity, §2.3), `run_id` (links the Step to the run it belongs to — every `runtime.execute()` returns `(results, run_id)`, §3.1), `inputs_hash`, `outputs_hash`, `agent_id`, `tenant_id`, `posture_at_time`, `prompt_ref`, `tool_calls[]`, `status`, `started_at`/`ended_at`, `cost`. **Immutable.** |
| **Output** | `AgenticArtifact` | One produced result | `content_hash` (SHA-256 of bytes), `version`, `parent_output_id` (prior version superseded), `produced_by_step_id`, `tenant_id`, `classification`. **Immutable — a new version is a new row, never an overwrite.** |
| **Decision** | `AgenticDecision` | A surfaced choice — a fan-out plan, a held action awaiting approval, a posture gate | `decision_id`, `status` (pending/approved/rejected), `decision_type`, `decided_by`, `decided_at`, `envelope_version`, `tenant_id`. **Immutable — resolving it creates a new linked record, never an edit.** |

**`step_id` vs `run_id` (the one field-shape subtlety):** a Step carries BOTH. `step_id` is the Step's own content-addressed identity — a fingerprint of *this single invocation's* content (§2.3), unique per Step. `run_id` is a grouping key that links the Step to the larger run it is part of — one run (one `runtime.execute()`) contains many Steps, all sharing the same `run_id` (§3.1, §6.4). One Step, one `step_id`; many Steps per run, one shared `run_id`. Both are load-bearing and they are not interchangeable.

`AgenticArtifact` already carries `content_hash` + `version` + `parent_artifact_id` — the immutable version chain is already modeled (research §1.1; plan §1.1). `Run` is already the atomic step record with input/output accounting.

### 2.2 The typed edges

Every connection is a *typed* relationship (named meaning, not "related to"):

```
Step   --consumes-->     Output     (input lineage — what this step took in)
Step   --produces-->     Output     (output lineage — what this step made)
Step   --depends_on-->   Step       (the dependency that DRIVES recompute)
Step   --gated_by-->     Decision   (this step waited on a surfaced decision)
Output --derived_from--> Output     (the version chain — parent_output_id)
```

The `depends_on` edge is the one the cascade engine walks. It already exists as `AgenticRequest.depends_on` — a `{"request_ids": [...]}` set that is *already a DAG edge-set* (research §1.1; plan §1.2). The platform does not invent dependency tracking; it *consumes* the dependency tracking pact already records.

### 2.3 Content-addressing — the load-bearing trick

"**Content-addressed**" means every Step and Output is identified by a *fingerprint of its content* — a SHA-256 hash that changes completely if even one byte changes — not by a sequential ID. Same idea as how Git identifies commits and IPFS identifies files (research §1.3; analysis §3.2; plan §1.3). A Step's identity is computed as:

```
step_id = hash(inputs_hash + prompt_ref/code_ref + sorted(dependency_step_hashes))
```

This buys three properties (analysis §3.2; plan §1.3):

1. **Tamper-evidence / immutability for free.** If a recorded result is altered, its fingerprint no longer matches — it cannot be silently changed. Same property as the aegis posture anchors at `/Users/esperie/repos/dev/aegis`, where each record carries `record_hash` + a back-pointer to its parent.
2. **Cheap branching via structural sharing.** Forking a timeline reuses the entire unchanged history *by reference*; only the divergent suffix is new data. A what-if exploration does not cost a full re-run.
3. **The "only recompute what changed" guarantee.** Two runs with identical inputs and identical upstream produce the *same* identity — so the engine recognizes "nothing actually changed here" and skips the re-run, reusing the cached result (the build-system memoization pattern; the seed of the cascade engine).

### 2.4 Versioned nodes — what "immutable + versioned" means concretely

Nodes are **never updated in place**. The version model is append-only (plan §1.4):

- An Output re-derived → a **new row** with `version = prior.version + 1` and `parent_output_id` pointing at the prior version. The original is untouched.
- A Step re-executed → a **new Step node** (N′) with a new `inputs_hash`; the old Step N stays as a prior version.
- A Decision resolved → a **new linked record** carrying the resolution; the original pending Decision stays.

A "timeline" is a **named pointer to a head of the DAG** — exactly like a Git branch is a named pointer to a commit (research §2.2; analysis §5.2; plan §1.4). "Compare two timelines" is a fingerprint-by-fingerprint comparison of their histories. **Note (v1 cut):** v1 ships exactly *one* timeline per objective (the "main" line); branching/forking is deferred post-v1 (plan §4.3, §8.3). This spec's data model supports named heads; the v1 product surfaces only the single head.

### 2.5 The ledger is the source of truth; telemetry feeds it

A clean architectural decision (analysis §3.3; plan §1.5; research §8): the live OTel spans (§1.1) are the *feed* — ephemeral telemetry that streams to the screen as work happens. The provenance ledger is the *permanent record* — durable, queryable, content-addressed. **Spans write into the ledger; the ledger is the source of truth.** This avoids the "two databases that disagree" problem and gives one place to query history. Persistence reuses the Kailash durable store (`DBCheckpointStore` / `StoreFactory`) that already ships (research §3; `/Users/esperie/repos/loom/kailash-py`).

The **ingestion contract** — the rule for when a live span becomes a permanent ledger node, and how partial/failed spans are handled — is specified in §5 (edge cases). It is flagged as an open design point in research §8 / plan §8.4 unknown #4.

### 2.6 The six invariants the ledger MUST always hold

These are the correctness rules the implementation must never violate (research §7.1; analysis §3.4; plan §6). They are the spec's hard contract; downstream implementation shards each carry the relevant subset.

1. **Immutability.** A re-execution NEVER mutates a prior Step/Output/Decision; it appends a new version. Enforced by `ON DELETE RESTRICT` + append-only at the application layer (already specified for `AuditEntry` and `AgenticArtifact`).
2. **Tenant isolation.** Every content-hash, cache key, and DAG query carries `tenant_id`. A shared content-address namespace across tenants is a cross-tenant data leak. The existing comms product already uses schema-per-tenant. **Highest-severity invariant** — a missing `tenant_id` on a cache key is a P0 cross-customer leak (per `.claude/rules/tenant-isolation.md`).
3. **Determinism boundary.** Model steps reuse the recorded output by fingerprint on retrace *unless* the user explicitly forces regeneration; the engine never assumes a model call replays identically (§4).
4. **Cascade minimality.** A downstream step whose recomputed `inputs_hash` is unchanged MUST be skipped. This is the "only affected downstream" promise; violating it makes rewind slow and expensive.
5. **Posture-at-time.** Every Step records the posture in force when it ran, so a retrace can show "this ran on its own (Autonomous)" vs "a human approved this (One-Check)." The cascade reads posture from the EATP posture machine but stores a *snapshot* on the Step.
6. **Audit completeness.** The intervention itself is an auditable action — *who* retraced, *what* they changed, *when*. A new audit record, never a silent edit.

**Reuse vs new for §2.** REUSED: the pact `Run` / `AgenticArtifact` / `AgenticDecision` models (content-hash + version + parent already present); `AgenticRequest.depends_on` (the DAG edge-set); the pact `AuditEntry` immutability discipline (`ON DELETE RESTRICT`); the Kailash `DBCheckpointStore` / `StoreFactory` durable store; the aegis hash-chained signed anchor as the content-addressing precedent. NET-NEW: wiring these into a *unified* content-addressed provenance DAG, the span→ledger ingestion contract (§5), and the cross-tenant content-address namespacing (`tenant_id` on every fingerprint).

---

## 3. How every activity and output is TRACED and ATTRIBUTED

Brief objective 3f: "every activity and output is traced and made transparent." This section defines the tracing-and-attribution contract concretely.

### 3.1 Every activity is a Step; every output is a versioned Output

Every model call, tool call, and workflow run becomes a Step node stamped with `run_id` (every `runtime.execute()` returns `(results, run_id)`; pact stamps every `Run` with `run-{uuid}` — research §3). Every result the work produces becomes an Output node with a content fingerprint and a version. The provenance edges (§2.2) connect them, so any output can be traced *backward* through `produced_by_step_id` → the Step → its `consumes` Outputs → their producing Steps, all the way to the original inputs. Forward tracing follows `depends_on` and `derived_from`.

### 3.2 Attribution — who/what did each thing

Attribution rides on the D/T/R (Doer / Target / Recipient) accountability grammar already in pact at `/Users/esperie/repos/terrene/contrib/pact` and the comms product's `AuditEntry` (`doer_type`, `doer_id`, `action_type`, `recipient_*`). Each Step records `agent_id` (the doer); each Decision records `decided_by` (the human authority, when a human resolved it); each Output records `produced_by_step_id` (the producing activity). Posture-at-time (§2.6 invariant 5) attributes *under what authority* the activity ran. Together these answer "what did the agent see, what did it do, what did it produce, and who permitted it" entirely at the I/O boundary (research §5.3) — which is exactly the traceability (not accountability) the contract promises (§1.4).

### 3.3 The intervention is itself a traced activity

When a user retraces to a past step and changes it, that intervention is a new audit record — *user X changed the exchange-rate assumption at step N at time T* — never a silent edit (invariant 6). The retrace surface reads the provenance DAG to show the user what a step consumed and produced before they change it (analysis §5.1; plan §3.1, §5).

**Reuse vs new for §3.** REUSED: the D/T/R grammar + `AuditEntry` shape (pact / comms product); `run_id` as the activity spine (Kailash). NET-NEW: the backward/forward lineage traversal over the unified DAG, and recording the *intervention* as a first-class traced activity.

---

## 4. The determinism boundary — reuse-recorded vs regenerate

Model steps are non-deterministic: the same prompt can yield a different answer next time. This breaks the naive "rewind and re-run reproduces what was there." The ledger's only obligation here is **invariant 3** (§2.6): on a retrace, the engine reuses the recorded output by fingerprint for every step the user did *not* explicitly change, and only re-generates the steps the user *did* change — it never assumes a model call replays identically (research §3 gap 4).

**The full determinism contract — the Re-run / Replay / Branch user-intent table, the explicit per-step reuse-vs-regenerate user choice, and the legitimate-divergence "what changed and why" UX obligation — is owned by `specs/intervention-and-versioning.md` §6** (the non-deterministic-LLM-step problem and its resolution). That is the intervention-and-versioning domain; this spec records only that the ledger stores the recorded output by fingerprint so the determinism choice has a deterministic thing to reuse (invariant 3). See intervention-and-versioning.md §6.1 for the three-intent table and §6.2 for the resolution contract.

**Reuse vs new for §4.** REUSED: the durable-execution record-and-replay-recorded-value pattern (Kailash `ExecutionTracker` skip + cached-output replay — research §3); the EATP `BudgetTracker` history at `/Users/esperie/repos/loom/kailash-py` as a cost-preview source before a re-run commits. NET-NEW: the per-step reuse-vs-regenerate user choice surfaced as a product decision (owned by intervention-and-versioning.md §6), and the version-diff "what changed and why" rendering.

---

## 5. Surfacing a planned FAN-OUT on screen, before it runs

Brief objective 3e worked example: the user says "I want a 3Q financial report"; the agent *decides* to spin up 3 sub-agents; that decision is **surfaced on screen and recorded**, and the user has **chosen a posture beforehand** (Go-ahead / Ask-once / Step-through). This is where transparency meets governance (M2).

### 5.1 The plan is a Decision node, surfaced and approvable BEFORE execution

When an agent forms a plan, the fan-out (3 sub-tasks, what each does, the estimated cost) is captured as a **Decision** record of a new subtype — `plan_proposed` — and shown to the user as an inspectable object *before any of it executes* (analysis §4.1; research §4.2). On screen this is a small diagram of "here is what I'm about to do." Depending on posture, the user either watches it auto-approve, approves it once, or steps through it. The `gated_by` edge (§2.2) links each downstream Step to the Decision it waited on.

### 5.2 The live stream that carries it

The plan streams to the screen over a live two-way channel (a WebSocket). The pipeline already exists end-to-end (research §4.1; analysis §4.1):

- pact's `EventBridge.on_plan_event` fires per scheduled sub-task and streams it to the browser via `EventBus` (typed emitters: `emit_held_action`, `emit_posture_change`) — `/Users/esperie/repos/terrene/contrib/pact`.
- When something needs approval, pact's `HELD` mechanism pauses the action, writes an `AgenticDecision`, and **blocks until a human approves or rejects** (`ApprovalBridge.get_pending` → approve / reject), surfaced as an approval queue on a dashboard.

The chosen posture (read from the EATP/aegis `PostureStateMachine`/`PostureStore` — `/Users/esperie/repos/loom/kailash-py`, `/Users/esperie/repos/dev/aegis`) decides whether the `plan_proposed` Decision auto-approves, needs one approval, or pauses at each step. The L3/L4/L5 ladder semantics and the 3-button mapping live in the governance domain spec; this spec records only that the posture-at-time is *snapshotted onto every Step* (invariant 5) so a retrace can show under what authority each activity ran.

**Reuse vs new for §5.** REUSED: pact `EventBridge` + `EventBus` (WebSocket fan-out); `SupervisorOrchestrator` + `_PlatformHeldCallback` (block-until-approve) + `ApprovalBridge` (approve/reject queue); the EATP/aegis posture machine — all at `/Users/esperie/repos/terrene/contrib/pact`, `/Users/esperie/repos/loom/kailash-py`, `/Users/esperie/repos/dev/aegis`. NET-NEW: the `plan_proposed` Decision subtype that surfaces the *plan itself* (not just a near-a-limit governance trigger) as the approvable object, and wiring the posture level to gate that specific decision class (~1 cycle of integration — research §4.3, §7 item 3). **Reuse caution:** pact's existing "is this action consequential?" classifier matches keywords (`write`, `send`, `delete`); the platform MUST replace it with an LLM-judged assessment per `.claude/rules/agent-reasoning.md` (CLAUDE.md Directive 6) — keep pact's *verdict* machinery (pause/block/auto-approve), not its keyword decision path (analysis §4.4; research §4.2).

---

## 6. Edge cases

The contract must hold under the messy real conditions, not just the happy path. Each case below names the behavior the ledger MUST exhibit.

### 6.1 Streaming outputs

A model that streams its answer token-by-token produces a span whose output accrues over time. **Contract:** the live stream (§2.5) shows the partial output to the screen as it arrives, but the **ledger node is written once, at span finalization**, with the `content_hash` computed over the *complete* finalized bytes. A partial stream has no stable fingerprint and MUST NOT be content-addressed or memoized. If the stream is interrupted before finalization, the Step is recorded with `status = partial` (§6.4) and no Output node — the partial bytes are telemetry, not a versioned result. (Ingestion contract per §2.5; research §8 ingestion-contract unknown.)

### 6.2 Large artifacts

An Output may be a large file (a generated spreadsheet, a multi-megabyte document). **Contract:** the Output node stores the `content_hash` and a *reference* to the bytes in the durable store (`DBCheckpointStore` tiers memory→disk→DB, gzip >1KB — research §3), never the bytes inline in the node row. Content-addressing dedupes identical bytes across versions automatically (the IPFS property — research §8): two versions that share an unchanged large artifact share one stored blob by hash. This bounds storage growth from byte duplication but NOT from version *count* — a retention/compaction policy is owed before scale (§7 unknown; aegis `compaction-checkpoint` precedent at `/Users/esperie/repos/dev/aegis`).

### 6.3 Tool failures

A tool call that errors (timeout, 4xx/5xx, exception) is a recorded fact, not a hidden one. **Contract:** the tool-execution span records the failure (error type, message) as the tool *result*; the Step that issued it records `status = failed` with the failure captured. This is the glass box working as designed — the user sees *what the agent tried to do in the world and that it failed*, not a silently-swallowed error (per `.claude/rules/zero-tolerance.md` Rule 3 — no silent fallbacks). A downstream Step whose input depended on the failed tool result is marked accordingly; the cascade does not fabricate a success. A failed Step is immutable like any other; a retry is a *new* Step (N′), never an overwrite.

### 6.4 Partial runs

A run that is interrupted — crash, budget exhaustion, user abort — leaves the ledger in a consistent partial state. **Contract:** every Step completed before the interruption is already an immutable ledger node (the ledger is append-only, written per-step, not per-run). The interrupted Step is recorded `status = partial` or `status = running` (resolved to `failed`/`abandoned` on the next fold if no completion arrives). Crash-resume reuses the Kailash `ExecutionTracker` skip logic (skip completed nodes, replay cached output — research §3, §6.1) to continue *forward* from the last good Step; this is distinct from *retrace* (rewind to an arbitrary past step). A partial run never corrupts prior outputs because nothing is ever mutated in place (invariant 1). `run_id` (research §3) ties all Steps of one run together so a partial run is identifiable and resumable.

**Reuse vs new for §6.** REUSED: `DBCheckpointStore` tiered persistence + gzip; content-addressing dedup (IPFS property); `ExecutionTracker` crash-resume skip; `ExecutionJournal` append-only state-transition log (Kailash — `/Users/esperie/repos/loom/kailash-py`). NET-NEW: the streaming finalization rule (write-once-at-finalization), the large-artifact reference-not-inline storage shape, the failed-Step provenance status, and the retention/compaction policy (owed, not yet specified).

---

## 7. Highest-risk unknowns (flagged, not resolved)

Per `.claude/rules/spec-accuracy.md`, genuine uncertainties a spec/redteam phase must resolve are flagged, not smoothed over. These are TARGET-STATE risks (this whole spec is vision); they bound the honest shape of the bet (analysis §8; plan §8.4).

1. **Non-coder versioning/branching UX (dominant risk).** "Rewind, change, see only the affected parts redo, compare versions, revert" for a non-coder is an unsolved design problem; Git-like concepts are hard for experts. v1's linear-no-branching cut (§2.4) is the primary mitigation, but residual UX risk decides whether the feature is *usable* by its target audience. Resolution: UX design + real non-coder user testing, iterative discovery.
2. **Re-run vs replay (the per-step choice).** The "regenerate / keep recorded" decision (§4) may confuse non-coders; guessing the default wrong silently is the worst outcome. v1's reuse-recorded default + explicit-regenerate mitigates. Resolution: product decision + user testing.
3. **Cascade cost explosion.** A change near the root of a wide DAG legitimately invalidates everything downstream. Content-hash skip bounds *unnecessary* re-runs, but a root-prompt edit *correctly* re-runs everything. Resolution: a cost-preview before committing a cascade, estimated from `ExecutionMetric` history (pact — `/Users/esperie/repos/terrene/contrib/pact`).
4. **The span→ledger ingestion contract.** Spans are ephemeral; the ledger is durable. §2.5 sets the direction (ledger is source of truth; spans write into it); §6 sets the partial/streaming rules. The full contract (exact finalization point, idempotent ingestion under retries) needs engine-design closure.
5. **Storage growth / retention policy.** Every re-run is a new version forever. Content-addressing dedupes identical bytes but not version *count*. Resolution: an operational retention/compaction policy (aegis `compaction-checkpoint` precedent; the comms product has tiered retention by plan).
6. **Single-process event bus.** pact's `EventBus` is in-memory (single process). A multi-replica deployment needs a durable/distributed bus (`SQLTaskQueue` with `SKIP LOCKED` or Redis fan-out is the in-ecosystem path). Deferred post-v1; a scaling cliff, not a v1 blocker.
7. **Where the cascade engine lives (framework vs app).** Framework-level placement (over the DataFlow models + `WorkflowDAG`) maximizes reuse and aligns with the capability-first stance, but depends on the not-yet-GA durable-resume integration in the LocalRuntime hot path (research §3 gap 1). Resolution: confirm with framework specialists at design time.

The top two decide whether the feature is *usable*, not whether it can be *built* — the engine is the tractable part; legibility-for-non-coders is the frontier.

---

## 8. Domain split note

This spec is the provenance + transparency authority, and it OWNS the shared provenance data model (§2) and the six invariants (§2.6) — sibling specs reference them here rather than restating them. The domain split per `.claude/rules/specs-authority.md` Rule 8 has already happened; the sibling domains are owned in their own files:

- `transparency-and-provenance.md` (this file) — §1 contract, §2 ledger data model (OWNER), §3 tracing/attribution, §6 edge cases, §2.6 six invariants (OWNER).
- `intervention-and-versioning.md` — §4 determinism semantics + the cascade engine's mechanism (retrace, dirty-mark, fingerprint-skip, version-on-rerun) + branching. References this file for the canonical Step/Output/Decision model and the six invariants.
- `trust-posture-and-governance.md` — fan-out surfacing + the L3/L4/L5 ladder + the LLM-first consequentiality classifier + posture composition across multiple humans (touches moat M3).
- `coordination-and-teams.md` — multi-human coordination and team-level concerns where posture composition and provenance attribution meet.

Those sibling domains are referenced by contract point (posture-at-time snapshot in §2.6 invariant 5; cascade minimality in §2.6 invariant 4; `plan_proposed` Decision subtype in §5.1) and owned in full in their respective files.

---

## Source ledger

- `workspaces/future-of-work/01-analysis/07-transparency-intervention-architecture.md` — §2 (transparency contract), §3 (provenance data model + six invariants), §4 (posture surfacing), §5 (intervention + determinism + worked example), §6 (reuse vs new, layer cake, comms wedge), §7 (recommendation), §8 (nine ranked unknowns).
- `workspaces/future-of-work/02-plans/03-provenance-cascade-design.md` — §1 (data model), §2 (transparency contract), §3 (cascade), §4 (determinism + v1 cut), §5 (versioning/timeline), §6 (invariants + shard map), §7 (reuse vs extend), §8 (v1 scope + unknowns).
- `workspaces/future-of-work/01-analysis/01-research/06-transparency-intervention-versioning.md` — §1 (provenance entities + content-addressing), §2 (intervention + branching), §3 (durable execution + determinism gap), §4 (decision surfacing + posture), §5 (black-box boundary + OTel conventions), §6 (layer-cake + unifying skip insight), §7 (novel parts + invariants), §8 (risks).
- Ecosystem DNA: pact `/Users/esperie/repos/terrene/contrib/pact`; eatp `/Users/esperie/repos/loom/kailash-py`; aegis `/Users/esperie/repos/dev/aegis`; loom `/Users/esperie/repos/loom`; envoy `/Users/esperie/repos/dev/envoy`.
- COC rules: `.claude/rules/tenant-isolation.md`, `.claude/rules/zero-tolerance.md`, `.claude/rules/agent-reasoning.md`, `.claude/rules/spec-accuracy.md`, `.claude/rules/specs-authority.md`, `.claude/rules/communication.md`.
