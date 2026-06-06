# Research 06 — Transparency, Intervention, and Versioning

> Workspace: `future-of-work` · Phase 01 (analyze) · Research stream
> Brief objectives addressed: **3e** (transparent + interveneable steps, posture-gated, retrace-and-intervene, versioned outputs), **3f** (everything traced; black-box boundary at model reasoning), with supporting decisions **A** (comms wedge) and **B** (capability-first).
> Constraint: described on the platform's own terms (Terrene Foundation / independent). Effort in autonomous execution cycles, not human-days.

---

## 0. What the brief actually demands (the hard problem, stated precisely)

From `briefs/01-vision.md` §3e–3f, three load-bearing requirements:

1. **Total provenance** — "every activity and output is traced and made transparent." Every step a human or agent takes, and every output produced, is recorded and inspectable.
2. **Retrace-and-intervene with cascade** — "Users can retrace any previous step and intervene from there; downstream/cascading outputs change accordingly, but old outputs are versioned." A user rewinds to step N, changes an input or a decision, and _only the affected downstream_ recomputes — while the prior outputs survive as immutable versions.
3. **Decisions surfaced before execution, posture-gated** — the "I want 3Q financial report → agent decides to spin up 3 agents" example: that fan-out decision is "surfaced on screen, recorded," and the user picks a posture beforehand (L5 autonomous / L4 supervised / L3 step-by-step).
4. **Black-box boundary** — "The only thing not transparent is how the model (black box) thinks — but input and output are transparent."

This is the single hardest engineering problem in the vision because it is the intersection of four well-studied-but-rarely-combined disciplines: **event sourcing / provenance ledgers**, **content-addressed immutable versioning**, **dependency-aware incremental recomputation** (the build-system / reactive-notebook problem), and **durable, replayable execution**. The good news from this research: roughly the 80% substrate already exists across kailash / pact / aegis. The genuinely novel 20% is the _composition_ — specifically the reactive-cascade re-execution over a content-addressed provenance DAG with branch/fork semantics, which no single repo in the ecosystem has assembled yet.

---

## 1. The data model: "every activity and output is traced"

### 1.1 The provenance entities already exist in pact

The pact platform's DataFlow model set (`/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/models/__init__.py`) is, almost exactly, the provenance-DAG schema this brief needs. The hierarchy:

| pact model           | Provenance role                           | Key fields for our purpose                                                                                          |
| -------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `AgenticObjective`   | Top-level work unit (the user's goal)     | `id`, `parent_objective_id`, `status`, `metadata`                                                                   |
| `AgenticRequest`     | Decomposed task                           | `objective_id`, **`depends_on: dict` `{"request_ids": [...]}`**, `sequence_order`, `envelope_id`                    |
| `AgenticWorkSession` | Active work period                        | `request_id`, `worker_address`, token/cost tracking, `verification_verdicts`                                        |
| `Run`                | **Single agent/tool/workflow invocation** | `session_id`, `request_id`, `run_type` (llm/tool/workflow), `status`, `duration_ms`, tokens, `cost_usd`, `metadata` |
| `AgenticArtifact`    | **Produced output**                       | `request_id`, `session_id`, **`content_hash` (SHA-256)**, **`version: int`**, **`parent_artifact_id`**              |
| `AgenticDecision`    | **Human judgment point**                  | created on `HELD` verdict; `envelope_version` (TOCTOU defense), multi-approver fields                               |

The critical observation: `AgenticRequest.depends_on` is _already a DAG edge set_, `AgenticArtifact` is _already content-addressed and versioned_ (`content_hash` + `version` + `parent_artifact_id` form an immutable version chain), and `Run` is _already the atomic step record_ with input/output accounting. This is the provenance DAG the brief asks for — it has simply never been wired to a _retrace-and-cascade_ engine.

Source: `models/__init__.py:286-465` (objective→request→session→run), `:329-346` (artifact content-addressing), `:348-373` (decision points).

### 1.2 Sequor's own data model already carries the immutability + content-addressing seeds

`specs/data-model.md` (the comms wedge) independently arrived at the same primitives:

- **`AuditEntry`** (`data-model.md:191-204`) — append-only, **immutable** (`occurred_at` "immutable; not updated on edit"), D/T/R-shaped (`doer_type`, `doer_id`, `action_type`, `recipient_*`). FK constraints enforce `ON DELETE RESTRICT` and the spec states "AuditEntry records are IMMUTABLE — no UPDATE or DELETE allowed at application level" (`:323`).
- **Content addressing** — `Document.file_hash` is "SHA-256 for cache invalidation" (`:152`); `Message.external_message_id` for dedup.
- **Version-on-correction** — the spec already prescribes the versioning discipline: "Corrections to any record create a new audit row (e.g., if a classification is corrected, log it as `classification_corrected` with the reason)" (`:449`). This is exactly the "old outputs are versioned" semantics, applied at the audit layer.
- **Response lineage** — `Response.rag_retrieval_id` → `RAGRetrieval.document_ids` → `Document` is a provenance chain from final output back to source passages.

So both the platform (pact) and the wedge (Sequor) already model immutability + content hashes + lineage. They lack the unifying _provenance-DAG-as-first-class-object_ with cascade re-execution.

### 1.3 Target provenance-graph data model (synthesis)

Combine the two into a single content-addressed provenance ledger. Every node is one of three kinds, every edge is a typed dependency:

```
Step    (= Run)         : one invocation. inputs_hash, outputs_hash, agent_id, posture_at_time,
                          prompt_ref, tool_calls[], status, started/ended, cost. IMMUTABLE.
Output  (= Artifact)    : content_hash (SHA-256 of bytes), version, parent_output_id,
                          produced_by_step_id, classification. IMMUTABLE (new version = new row).
Decision(= AgenticDecision): a surfaced choice (fan-out plan, governance HELD, posture gate).
                          status pending/approved/rejected, decided_by, envelope_version. IMMUTABLE record;
                          resolution is a NEW linked record, never an in-place mutation.

Edges:
  Step  --consumes-->  Output     (input lineage)
  Step  --produces--> Output      (output lineage)
  Step  --depends_on--> Step      (= Request.depends_on, the re-exec DAG)
  Step  --gated_by-->  Decision   (this step waited on a surfaced decision)
  Output --derived_from--> Output (version chain, parent_output_id)
```

The provenance graph IS a Merkle DAG (per the IPFS / Bazel CAS pattern): a Step's identity is `hash(inputs_hash + code_ref + sorted(dependency_step_hashes))`. Two runs with identical inputs and identical upstream produce the _same_ step hash → memoizable, skippable on re-execution (this is precisely Bazel's action-cache + Skyframe model and the basis of incremental recomputation — see §3).

---

## 2. Intervention semantics: retrace to step N, change an input, recompute only downstream

This is the reactive-recomputation problem. The closest established art is **reactive computational notebooks** (ipyflow / nbsafety / "Dataflow Notebooks") layered over a **content-addressed dependency graph** (Bazel / IPFS Merkle-DAG).

### 2.1 The mechanism, grounded in established patterns

From the reactive-notebook research (ipyflow, "Runtime provenance refinement for notebooks", "Fine-Grained Lineage for Safer Notebook Interactions"): when a cell (≈ Step) changes, the kernel computes "the (minimal) set of out-of-sync upstream and downstream cells" and re-executes _only those_, so the notebook ends in the state it would reach on a clean top-to-bottom run. Map that directly:

1. **User retraces to Step N.** The UI reads the provenance DAG and shows Step N's recorded inputs, the prompt that went in, the tool calls, and the output that came out (the transparency surface — §5).
2. **User changes an input/decision at N.** This creates a _new_ Step N′ with a new `inputs_hash`. The old Step N and its Output are **untouched** (immutability — they remain as a prior version, satisfying "old outputs are versioned").
3. **Dirty-marking.** Walk `descendants(N)` in the DAG (the existing `WorkflowDAG.descendants()` — `01-core-sdk/core-workflow-dag.md:33` — gives this in O(1)-amortized via cached topo). Every descendant Step is marked _potentially dirty_.
4. **Content-addressed pruning (the "only affected downstream" guarantee).** Re-execute dirty Steps in topological order. For each, recompute its `inputs_hash` from its (possibly-unchanged) upstream outputs. **If the new `inputs_hash` equals the recorded one, skip and reuse the cached Output** (Bazel action-cache / IPFS "any change alters the identifier and affects all ascendants; unchanged subtrees are reused"). Only steps whose inputs _actually_ changed re-run. A step that depended on N but whose other inputs dominate may produce an identical output and halt the cascade early.
5. **Versioning.** Every re-executed step's output is written as a _new_ `version` with `parent_output_id` pointing at the prior version. Nothing is overwritten.

The combination — dirty-propagation from reactive notebooks + content-hash skip from Bazel/IPFS — is what delivers "downstream cascades re-execute, but only the affected ones, and old outputs survive."

### 2.2 Branching / forking an execution timeline

"Retrace and intervene" implies the user may _not_ want to destroy the original timeline — they may want to explore an alternative. The natural model is **git-like branching over the provenance DAG**:

- An intervention at Step N can either **advance the main timeline** (N′ supersedes N; descendants recompute in place as new versions) or **fork a branch** (N′ starts a new branch sharing all ancestors ≤ N by reference, diverging after).
- Because every Step and Output is content-addressed and immutable, a fork is _cheap_: it shares the entire unchanged ancestor subtree by hash reference (structural sharing, exactly the IPFS/Merkle-DAG property). Only the divergent suffix is new.
- aegis already demonstrates the hash-linked immutable chain primitive: its posture anchors (`proj-*/anchors/anc-posture-*.json`) form a signed chain — each anchor carries `parent_anchor_id`, `record_hash`, and `signature`. That is a single-parent content-addressed ledger; generalizing `parent` to support divergence yields a branchable provenance DAG.

A "timeline" is then a named pointer to a DAG head (git's branch ref). "Compare two timelines" = diff two heads' transitive closures by content hash.

### 2.3 What this requires that doesn't yet exist

The DAG primitive (`WorkflowDAG`), the immutable content-addressed records (`Artifact`, `AuditEntry`, aegis anchors), and the dependency edges (`Request.depends_on`) all exist. **The reactive cascade engine — dirty-propagation + content-hash skip + version-on-rerun + branch heads — does not.** It is the central novel component (see §7).

---

## 3. Durable execution & checkpointing: how far kailash gets us, and the gap

kailash's durable-execution stack (`15-enterprise-infrastructure/durability-patterns.md`) provides the _replayability_ half of the problem:

| Primitive                                                | What it gives                                                                                                                       | Source                                                                           |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `ExecutionTracker`                                       | Per-node completion state; on restore, runtime SKIPS completed nodes and replays cached outputs                                     | `runtime/execution_tracker.py`                                                   |
| `DurableRequest` + `ExecutionJournal`                    | Per-request state machine (`INITIALIZED→…→CHECKPOINTED→COMPLETED/RESUMING`) + **append-only audit trail of every state transition** | `middleware/gateway/durable_request.py`                                          |
| `Checkpoint` + `CheckpointManager` + `DBCheckpointStore` | Serialized state at boundaries; tiered (memory→disk→DB), gzip>1KB, dialect-portable SQL                                             | `middleware/gateway/checkpoint_manager.py`, `infrastructure/checkpoint_store.py` |
| `IdempotentExecutor` (claim-execute-store)               | Exactly-once via atomic `try_claim` (INSERT IGNORE + fingerprint), release-on-failure, TTL                                          | `15-enterprise-infrastructure/idempotency-patterns.md`                           |
| `run_id`                                                 | Every `runtime.execute()` returns `(results, run_id)`; pact stamps every `Run` with `run-{uuid}`                                    | `01-core-sdk` execution contract; `orchestrator.py:299`                          |

**What this already does well:** `ExecutionTracker`'s "skip already-completed nodes, replay cached output" is _node-level memoization within a single run_ — structurally the same operation as our content-hash skip (§2.1 step 4), just scoped to crash-resume rather than user-intervention. And the external durable-execution literature (Temporal-style event history) confirms the model: "a durable log of events … replay reconstructs in-memory state and resumes." The `ExecutionJournal` is exactly that event log.

**The gap to full retrace-and-intervene:**

1. **Resume ≠ retrace.** `DurableRequest.resume()` replays _forward_ from the last checkpoint to recover from a crash. The brief needs _rewind to an arbitrary past step, mutate it, and re-derive forward_. Resume restores to the latest good state; retrace must restore to _any_ state and branch. The durability skill explicitly flags this: "In-flight integration work tying `DurableRequest` resume into the LocalRuntime hot path is tracked at the SDK's open LocalRuntime-resume integration issue" (`durability-patterns.md:76`). Even forward-resume into LocalRuntime is not yet GA.
2. **Checkpoint granularity is coarse.** Checkpoints land "at validation, workflow-creation, and workflow-completion boundaries" — not per-step with content hashes. Retrace needs per-step immutable records keyed by content hash, which is the provenance ledger (§1), not the checkpoint blob.
3. **No cross-run dependency graph.** `ExecutionTracker` is per-run; the brief's cascade crosses runs/sessions/objectives. The cross-run DAG is `Request.depends_on` + provenance edges, which the durable layer doesn't consult.
4. **Determinism constraint.** Replay only works if steps are deterministic given inputs. LLM steps are NOT deterministic. This is why the transparency boundary (§5) matters: we record the _output_ of each LLM step as an immutable artifact, and on retrace we _reuse the recorded output by content hash_ unless the user explicitly forces re-generation. We never assume an LLM call replays identically. (External durable-execution practice handles this by recording non-deterministic results in the event history and replaying the _recorded_ value — Temporal's activity-result recording. Same trick.)

**Net:** kailash supplies durable persistence, per-node skip, idempotent claim, and the `run_id` spine. The retrace engine layers _on top_ and reuses `DBCheckpointStore`/`StoreFactory` for persistence and `ExecutionTracker`'s skip logic as the within-run case of the broader content-hash-skip cascade.

---

## 4. Surfacing decisions "on screen, recorded": the live event stream

The brief's worked example — "agent decides to spin up 3 agents → surfaced on screen, recorded → user picks posture beforehand." pact already ships the entire pipeline for this.

### 4.1 The event stream from agent → UI exists end to end

`engine/event_bridge.py` + `use/api/events.py` are a complete agent→WebSocket→UI event bus:

- **`EventBus`** (`events.py:81-277`) — in-memory pub/sub, per-subscriber `asyncio.Queue`, WebSocket fan-out, bounded subscribers, with typed convenience emitters: `emit_audit_anchor`, `emit_held_action`, `emit_posture_change`.
- **`EventType`** enum (`events.py:29-37`): `AUDIT_ANCHOR`, `HELD_ACTION`, `POSTURE_CHANGE`, `BRIDGE_STATUS`, `VERIFICATION_RESULT`, `WORKSPACE_TRANSITION`. These are exactly the event classes the transparency UI needs.
- **`EventBridge`** (`event_bridge.py:33-204`) — translates supervisor lifecycle events into `PlatformEvent`s: `on_plan_event` (plan creation, **node scheduling**, node completion, plan finalization → `VERIFICATION_RESULT`), `on_cost_event` (`AUDIT_ANCHOR`), `on_hold_event` (`HELD_ACTION`), `on_completion_event`.

So when an agent forms a plan ("spin up 3 agents"), `on_plan_event` already fires per scheduled node, and the dashboard already receives it via WebSocket. The "decisions surfaced on screen" requirement is _substantially built_.

### 4.2 The "approve the plan BEFORE execution" gate

The HELD pattern is the approval gate. `SupervisorOrchestrator` wires `_PlatformHeldCallback` (`orchestrator.py:59-99`): when governance returns `HELD`, the callback (a) persists an `AgenticDecision` via `ApprovalBridge.create_decision`, (b) **returns `False` to block the action until a human approves** (`orchestrator.py:99`). `ApprovalBridge` (`approval_bridge.py`) then exposes `get_pending()` (the approval queue the dashboard renders), `approve()`, and `reject()`. Multi-approver is modeled (`AgenticDecision.required_approvals` / `current_approvals` / `approval_record_ids`; `ApprovalConfig` per operation type).

**The gap for the brief's fan-out example:** Today the HELD gate fires on _governance_ triggers (action near a constraint limit). The brief wants the _plan itself_ — the decision to fan out to 3 agents — surfaced as an inspectable, approvable object _before_ execution, gated by the user's chosen posture. That means:

- A new `Decision` subtype: **`plan_proposed`** (alongside the existing `governance_hold`/`budget_hold`/`manual_review` in `AgenticDecision.decision_type`, `models/__init__.py:357`). The proposed plan (the fan-out DAG: 3 child Steps, their objectives, estimated cost) is recorded as a Decision record and emitted as `HELD_ACTION`.
- Posture decides whether that Decision _auto-approves_ (L5), _requires one approval_ (L4), or _pauses at every step_ (L3). The posture comes from the EATP `PostureStateMachine` (§4.3).

### 4.3 Posture (L5/L4/L3) is the EATP/aegis state machine — already built

The brief's L5/L4/L3 ladder maps 1:1 onto the EATP `TrustPosture` enum and the `.claude/rules/trust-posture.md` ladder:

| Brief posture   | EATP `TrustPosture` (`eatp-posture-stores.md:244-250`) | COC ladder (`trust-posture.md`) | Behavior                                 |
| --------------- | ------------------------------------------------------ | ------------------------------- | ---------------------------------------- |
| L5 Autonomous   | `DELEGATED` (5)                                        | `L5_DELEGATED`                  | Agent proceeds; plan auto-approves       |
| L4 Supervised   | `CONTINUOUS_INSIGHT` (4)                               | `L4_CONTINUOUS_INSIGHT`         | One permission before executing the plan |
| L3 Step-by-step | `SHARED_PLANNING` (3)                                  | `L3_SHARED_PLANNING`            | Pause at each step                       |

The persistence + transition machinery is production-grade: `SQLitePostureStore` (thread-safe, WAL, parameterized, agent-ID-validated, schema-migrated), `PostureStateMachine` with guards, `record_transition`, `get_history`, and **`EMERGENCY_DOWNGRADE`** (instant drop to `PSEUDO_AGENT`). Per CARE Principle 7 / EATP Mirror Thesis: "upgrades are human-gated; downgrades fire on detection." aegis demonstrates the _signed, hash-chained_ posture-transition ledger in production (`anc-posture-*.json`: `parent_anchor_id` + `record_hash` + `signature`), and the `POSTURE_CHANGE` event already streams to the UI.

**Net for §4:** the live decision stream, the approve-before-execute gate, the posture ladder, and the posture-transition ledger are all built. The novel work is (a) the `plan_proposed` Decision subtype that surfaces a fan-out plan as an inspectable DAG before execution, and (b) wiring the posture level to gate that specific decision class. ~1 cycle of integration, not greenfield.

---

## 5. The black-box boundary: precisely what is and isn't transparent

Brief 3f: "The only thing not transparent is how the model (black box) thinks — but input and output are transparent." This boundary is exactly the one the OpenTelemetry GenAI Semantic Conventions draw, which gives us an off-the-shelf, industry-standard schema.

### 5.1 The transparency boundary, defined

For every LLM/agent step, **record the I/O envelope, never the latent reasoning**:

| RECORDED (transparent)                                                                     | NOT recorded (the black box)                               |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Prompt in — system + user messages (`gen_ai.input.messages`, `gen_ai.system_instructions`) | The model's internal activations / weights                 |
| Tool calls requested (name, arguments) — `execute_tool` spans                              | The model's chain-of-thought / hidden scratchpad reasoning |
| Tool results returned                                                                      | Why the model "chose" those tokens (token-level logits)    |
| Output out — final messages (`gen_ai.output.messages`), `finish_reasons`                   |                                                            |
| Metadata — model id, token counts, cost, duration, posture-at-time                         |                                                            |

This is precisely the OTel GenAI span shape: a top-level `invoke_agent` span with child `chat` spans (one per LLM call) and `execute_tool` spans (one per tool invocation), capturing `gen_ai.request.model`, `gen_ai.usage.{input,output}_tokens`, `gen_ai.input.messages`, `gen_ai.output.messages` — and _not_ chain-of-thought. The industry has converged on this (Datadog, Honeycomb, New Relic; LangChain/CrewAI/AutoGen emit it natively). We adopt the convention rather than invent one.

### 5.2 kailash already emits this shape

`01-core-sdk/otel-tracing.md` shows kailash's progressive tracing: `TracingLevel.{NONE,BASIC,DETAILED,FULL}`. BASIC = workflow spans (`workflow_id`, `run_id`); DETAILED = node spans (`node.id`, `node.type`, `node.duration_ms`, `node.input_size`, `node.output_size`); FULL = DB + DataFlow ops. The `NodeInstrumentor` already wraps each node in a child span with input/output sizes. For LLM nodes this is the input/output envelope. The provenance ledger (§1) is the _durable, queryable, content-addressed_ projection of these spans (spans are ephemeral telemetry; the ledger is the permanent record).

### 5.3 Why this boundary is the right one (and a caveat)

- **Right:** Recording chain-of-thought is (a) often not exposed by the model API, (b) unstable across model versions, (c) frequently the most sensitive content. Recording the I/O envelope is sufficient for accountability ("what did the agent see, what did it do, what did it produce") without claiming to explain the unexplainable. The D/T/R accountability grammar (`AuditEntry.doer_type/action_type`, pact's `agent_address`) operates entirely at the I/O boundary.
- **Caveat to flag:** some providers now expose a _summarized_ reasoning trace (distinct from raw chain-of-thought). The EATP SDK has a `reasoning-traces` reference (`26-eatp-reference/eatp-sdk-reasoning-traces.md`) — there is an explicit place to record a model-provided reasoning _summary_ if one is returned, while still treating the true latent computation as opaque. The boundary is "we record what the model emits at its I/O surface (including any reasoning it chooses to surface); we do not claim to record how it actually computed."

---

## 6. The coherent target architecture (synthesis)

Four layers, bottom to top. The 80% that exists is marked; the novel 20% is isolated.

```
┌─────────────────────────────────────────────────────────────────────────┐
│ L4  TRANSPARENCY + INTERVENTION UI                                        │
│     - timeline view (provenance DAG rendered)                            │
│     - "retrace to step N" + edit input/decision                          │
│     - live decision stream (WebSocket) + approve/reject queue            │
│     - posture selector (L5/L4/L3) per objective                          │
│     [EXISTS: WebSocket EventBus + approval queue API. NEW: timeline +    │
│      retrace UI + plan-approval surface]                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ L3  REACTIVE CASCADE ENGINE  ◄── THE NOVEL CORE (20%)                     │
│     - dirty-propagation over descendants(N)  [WorkflowDAG.descendants ✓] │
│     - content-hash skip (reuse unchanged outputs)  [Bazel/IPFS pattern]  │
│     - version-on-rerun (new Output version, parent_output_id)            │
│     - branch/fork heads over the provenance DAG  [aegis anchor-chain ✓]  │
├─────────────────────────────────────────────────────────────────────────┤
│ L2  GOVERNED EXECUTION + DECISION GATING                                  │
│     - SupervisorOrchestrator → PactEngine.submit  [EXISTS ✓]            │
│     - HELD → AgenticDecision → ApprovalBridge (approve/reject) [EXISTS ✓]│
│     - posture gate (L5 auto / L4 one-approve / L3 step) [EATP SM EXISTS ✓]│
│     - NEW Decision subtype: plan_proposed (fan-out surfaced pre-exec)    │
├─────────────────────────────────────────────────────────────────────────┤
│ L1  PROVENANCE LEDGER (content-addressed, immutable)                      │
│     - Step(=Run) / Output(=Artifact, content_hash+version+parent) /      │
│       Decision(=AgenticDecision)  [pact models EXIST ✓]                  │
│     - depends_on edges [Request.depends_on EXISTS ✓]                     │
│     - append-only, ON DELETE RESTRICT, immutable [AuditEntry EXISTS ✓]   │
│     - durable persistence [DBCheckpointStore/StoreFactory EXISTS ✓]      │
│     - I/O-envelope recording, no chain-of-thought [OTel GenAI conv. ✓]   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.1 The unifying insight

The provenance ledger (L1) _is_ a Merkle DAG of immutable steps and content-addressed outputs. Three different operations are all the same content-hash-skip primitive at different scopes:

- **Crash resume** (`ExecutionTracker`): skip completed nodes within one run.
- **Idempotency** (`IdempotentExecutor`): skip a run whose idempotency key was claimed.
- **Retrace cascade** (novel): skip downstream steps whose recomputed `inputs_hash` is unchanged.

Building L3 is therefore _generalizing the skip logic kailash already has_ from intra-run to cross-run, keyed on content hash rather than node-id-completion. That is why this is a 20% novel composition, not an 80% greenfield: the hard primitive (content-addressed memoization) ships in kailash; we lift its scope.

### 6.2 How the comms wedge slots in (Decision A)

Sequor's flow is a _small, concrete instance_ of the general DAG: `Message → Classification → RAGRetrieval → Response → (auto-send | Escalation)`. Each is a Step; `Response.content` is an Output with a hash; `Classification.reasoning` + `RAGRetrieval.passages` are recorded I/O. The wedge's existing `classification_corrected` discipline (`data-model.md:449`) is the retrace-and-version primitive _already specified in prose_ — a user correcting a classification creates a new version and (should) re-derive the downstream Response. Wiring the comms wedge to the cascade engine is the natural first vertical: it proves retrace-and-intervene on a 4-step DAG before generalizing to arbitrary multi-agent objectives.

---

## 7. The genuinely novel parts (the 20%)

Everything in §1, §4, §5 exists or is industry-standard. The novel engineering is concentrated in **L3 — the reactive cascade engine** and two integration points:

1. **Content-hash-skip cascade over a cross-run provenance DAG.** Generalize `ExecutionTracker`'s intra-run skip to a cross-run, content-addressed dirty-propagation + memoized-reuse engine. This is the heart. (~1–2 cycles; has a live feedback loop — each cascade is testable against a fixture DAG — so per `autonomous-execution.md` the shard can run at higher budget.)
2. **Branch/fork heads over the provenance DAG.** git-like timeline pointers with structural sharing of unchanged ancestor subtrees. aegis's single-parent anchor chain is the precedent; generalizing `parent_anchor_id` to support divergence + named heads is the new work. (~1 cycle.)
3. **`plan_proposed` Decision subtype + posture-gated plan approval.** Surface a fan-out plan as an inspectable DAG object _before_ execution and gate it on the EATP posture level. Extends the existing HELD/ApprovalBridge path. (~1 cycle of integration.)
4. **Timeline + retrace UI.** Render the provenance DAG, let the user pick step N, edit, and trigger the cascade; show the live decision stream. (Frontend; ~1–2 cycles.)

Estimated total for a working end-to-end retrace-and-intervene over the comms wedge DAG: **~4–6 autonomous execution cycles**, because the substrate (L1, L2, EventBus, posture SM, durable store) is reused rather than rebuilt. Generalizing beyond the wedge to arbitrary objectives is incremental once L3 exists.

### 7.1 Hard correctness invariants the cascade engine must hold (for /todos sharding)

These are the ≤5–10 invariants per `autonomous-execution.md` capacity budget — flagging them now so the cascade engine is sharded correctly later:

- **Immutability:** a re-execution NEVER mutates a prior Step/Output; it appends a new version. (Enforced by `ON DELETE RESTRICT` + append-only at app layer, already specified.)
- **Tenant isolation:** every content-hash, cache key, and DAG query carries `tenant_id` (per `tenant-isolation.md`; Sequor mandates schema-per-tenant). A shared content-address namespace across tenants is a cross-tenant leak.
- **Determinism boundary:** LLM steps reuse recorded output by content hash on retrace UNLESS the user explicitly forces regeneration; the engine never assumes an LLM call replays identically.
- **Cascade minimality:** a descendant whose recomputed `inputs_hash` is unchanged MUST be skipped (else "only affected downstream" is violated and cost/latency explode).
- **Posture-at-time:** every Step records the posture in force when it ran (so retrace shows "this ran autonomously under L5" vs "this was human-approved under L4").
- **Audit completeness:** the intervention itself is an auditable action (who retraced, what they changed, when) — a new `AuditEntry`/Decision, not a silent edit.

---

## 8. Risks and open questions

- **Determinism of LLM steps** breaks naive replay. Mitigated by content-hash reuse of recorded outputs (§3 gap 4, §7.1). But: _should_ a retrace re-run the LLM (fresh answer) or reuse the recorded one? This is a product decision — likely user-selectable per step ("re-run with my edit" vs "keep the recorded output, only re-run what consumed it").
- **Cascade cost explosion.** A change near the root of a wide DAG could re-run everything. Content-hash skip bounds this, but a pathological edit (changing a root prompt) legitimately invalidates everything downstream. Need cost-preview before committing a cascade (estimate via `ExecutionMetric` history).
- **Storage growth from immutable versioning.** Every rerun is a new version forever. Need a retention/compaction policy for old versions (aegis has `compaction-checkpoint` in its coordination log as a precedent; Sequor has tiered retention by plan). Content-addressing dedupes identical bytes across versions (IPFS property), which helps.
- **Provenance ledger vs OTel spans — two stores or one?** Spans are ephemeral telemetry; the ledger is the durable record. Recommendation: ledger is source of truth (DataFlow models), OTel spans are the live-view feed that _write into_ the ledger. Needs a clean ingestion contract.
- **pact's `EventBus` is in-memory** (`events.py:81` — single process, bounded subscribers). For a multi-replica deployment the decision stream needs a durable/distributed bus (the `SQLTaskQueue` with `SKIP LOCKED` or a Redis fan-out is the in-ecosystem path). Flagged: the current EventBus is correct for single-process, a known scaling gap for multi-replica.
- **Where does the cascade engine live?** It's framework-level (operates over DataFlow models + WorkflowDAG). Likely a new kailash/pact-adjacent module, not Sequor-app code — consistent with Decision B (build the horizontal capability, wedge consumes it). Confirm with the framework specialists at design time.

---

## 9. Sources consulted

### Repo files (read directly)

- `/Users/esperie/repos/projects/Sequor/workspaces/future-of-work/briefs/01-vision.md` — authoritative brief (§3e/3f)
- `/Users/esperie/repos/projects/Sequor/specs/data-model.md` — AuditEntry immutability, content hashes, version-on-correction
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/models/__init__.py` — Objective/Request/Session/Run/Artifact/Decision provenance models
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/event_bridge.py` — supervisor→event translation
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/orchestrator.py` — SupervisorOrchestrator, \_PlatformHeldCallback (block-until-approve)
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/approval_bridge.py` — create/approve/reject/get_pending decision queue
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/use/api/events.py` — EventBus, EventType, PlatformEvent, WebSocket fan-out
- `/Users/esperie/repos/dev/aegis/proj-ad9690bf/anchors/anc-posture-*.json` — hash-linked signed posture-transition ledger
- `/Users/esperie/repos/dev/aegis/.claude/learning/violations.jsonl` — violation event stream shape
- `/Users/esperie/repos/dev/aegis/.claude/rules/aegis-fork-relationship.md` — Quartet/fork governance context
- `.claude/skills/15-enterprise-infrastructure/{durability,idempotency,task-queue}-patterns.md` — ExecutionTracker, DurableRequest, Checkpoint, IdempotentExecutor, SQLTaskQueue
- `.claude/skills/01-core-sdk/{core-workflow-dag,otel-tracing}.md` — WorkflowDAG (descendants/topo), TracingLevel
- `.claude/skills/26-eatp-reference/eatp-posture-stores.md` — TrustPosture enum, PostureStateMachine, SQLitePostureStore, EMERGENCY_DOWNGRADE

### External (web search, June 2026)

- OpenTelemetry GenAI Observability + Semantic Conventions — opentelemetry.io/blog/2026/genai-observability, mlflow.org GenAI semconv, greptime.com OTel GenAI — the input/output-envelope (not chain-of-thought) tracing standard
- Temporal / LangGraph durable execution — temporal.io, docs.langchain.com/oss/python/langgraph/durable-execution, docs.temporal.io/workflow-execution/event — event-history replay, determinism, time-travel debugging
- IPFS Merkle-DAG + Bazel CAS/Skyframe — docs.ipfs.tech/concepts/merkle-dag, gocodeo.com Bazel dependency graphs, cacm.acm.org Bazel remote cache — content-addressed immutable versioning + incremental recomputation
- Reactive notebooks — github.com/ipyflow/ipyflow, arxiv.org/pdf/2012.06981 (Fine-Grained Lineage), dl.acm.org/doi/10.1145/3530800.3534535 (Runtime provenance refinement) — minimal-set dirty-propagation, downstream re-execution, lineage
- Event sourcing / CQRS — confluent.io event-sourcing-cqrs, microservices.io/patterns/data/event-sourcing — audit log as data provenance, rewind-and-reprocess
