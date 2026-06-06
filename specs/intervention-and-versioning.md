> Status: TARGET-STATE (vision / not yet implemented). This spec describes the intended platform; the comms wedge (shipped) specs are separate.

# Intervention & Versioning (M1 core)

This is the domain-truth authority for **retrace-to-any-step intervention** and **immutable versioning** — moat **M1** of the platform: transparent, versioned, intervene-from-any-step knowledge work for non-coders. It defines what the system IS and DOES across the provenance ledger, the cascade re-execution engine, the determinism resolution for non-deterministic model steps, the timeline/version model, the cascade cost-preview contract, the correctness invariants the cascade engine must hold, and the irreversibility problem for actions that already hit a real external system.

Companion specs (not restated here): the transparency/black-box recording boundary AND the canonical provenance data model + six invariants are owned by `specs/transparency-and-provenance.md`; posture-graded governance (L3/L4/L5, the plan-approval gate, HITL/HOTL) is moat M2 and owned by `specs/trust-posture-and-governance.md`. This spec consumes posture as a recorded snapshot (Invariant 5, owned by transparency-and-provenance.md §2.6) and consumes the recorded I/O envelope as the content of a Step; it does not re-define them.

**Grounding.** Every load-bearing claim here resolves to one of three workspace sources, cited inline by short tag:
- **[P3]** `workspaces/future-of-work/02-plans/03-provenance-cascade-design.md` (the design plan)
- **[A7]** `workspaces/future-of-work/01-analysis/07-transparency-intervention-architecture.md` (the architecture decision)
- **[R6]** `workspaces/future-of-work/01-analysis/01-research/06-transparency-intervention-versioning.md` (the research)

---

## 1. What this subsystem is

Today an AI agent gives you an answer and nothing else: you cannot see why it acted, you cannot change one decision it made three steps ago without redoing everything, and when you redo it the old version is gone. This subsystem makes agentic work a **glass box with an undo-from-anywhere button** [A7 §0, P3 §0]. Two components deliver it:

- **The provenance ledger** — a permanent, content-addressed, append-only record of every step, output, and decision (§2).
- **The cascade engine** — the machinery that, when a user rewinds to a past step and changes it, re-runs *only* the genuinely-affected downstream work, while every prior result survives as a named version (§4).

The platform-level finding is that ~80% of the substrate already exists across the ecosystem; the genuinely net-new engineering is the cascade engine plus the unifying ledger wiring [P3 §0, A7 §6.3, R6 §0]. The reuse-vs-new disposition is stated per capability below.

---

## 2. The provenance ledger — data model (REFERENCED, not restated)

**Owner: `transparency-and-provenance.md`.** The canonical Step/Output/Decision data model — the three node kinds and their load-bearing fields, the typed edges, content-addressing, the versioned-node append-only rules, and the "ledger is the source of truth; telemetry feeds it" architecture — is owned by **`specs/transparency-and-provenance.md` §2** (the canonical Step/Output/Decision model) and the six invariants by **§2.6**. This spec consumes that model; it does NOT restate it. See that file's §2.1 for the node-kind table (including the explicit `step_id` vs `run_id` distinction — a Step carries its OWN content-hash `step_id` AND a `run_id` linking it to the run it belongs to), §2.2 for the typed edges, §2.3 for content-addressing, §2.4 for versioned nodes, and §2.5 for the ledger-as-source-of-truth architecture.

**Disposition: REUSED.** The data model already exists as the PACT platform's work-tracking DataFlow models at `/Users/esperie/repos/terrene/contrib/pact` [R6 §1.1, A7 §3.1, P3 §1.1]; it has simply never been wired to a rewind engine. **NET-NEW:** the wiring of these models into a single content-addressed provenance DAG, plus the `inputs_hash` + `posture_at_time` fields on the Step projection where not already present [P3 §7.2].

### 2.1 What the cascade engine consumes from the model

Two facts from the canonical model (transparency-and-provenance.md §2) are load-bearing for the cascade engine specifically:

- **The `depends_on` edge is the one the cascade engine walks.** It already exists as `AgenticRequest.depends_on`, a `{"request_ids": [...]}` set that is already a DAG edge-set [R6 §1.1, A7 §6.2, P3 §1.2]. The platform consumes this dependency tracking; it does not invent it. (Full edge set: transparency-and-provenance.md §2.2.)
- **A re-executed Step produces a new Step node (N′) with a new `step_id` and `inputs_hash`; the old Step N stays as a prior version.** This append-only versioning rule (transparency-and-provenance.md §2.4) is what makes "old outputs are versioned" true through a cascade re-run (§4).

A **timeline** is a named pointer to a head of the DAG — exactly like a Git branch points to a commit [R6 §2.2, A7 §5.2, P3 §1.4]. "Compare two timelines" is a fingerprint-by-fingerprint comparison of their histories. The timeline model and the v1 boundary on it are this spec's domain — see §5. (The named-pointer-over-a-DAG concept is shared with transparency-and-provenance.md §2.4; the cascade-and-versioning semantics of it are owned here.)

---

## 3. Retrace-to-any-step semantics

"Retrace" means: the user selects any past Step N and the system reconstructs and displays that step's recorded state from the ledger — the inputs it consumed, the prompt that went in, the tool calls it made, the tool results, and the output it produced [A7 §5.1 step 1, P3 §3.1 step 1]. This is a *read* of the provenance DAG and the recorded I/O envelope; it never re-executes anything and is therefore fully deterministic.

Retrace is the precondition for intervention. The user can retrace to inspect (read-only) and stop there, or retrace and then **intervene** — change an input or override a decision at N. Intervention is what triggers the cascade (§4).

**The v1 boundary on retrace (CONTRACT):** v1 supports **linear retrace only**. There is exactly one timeline per objective (the "main" line). Retracing to N and intervening advances that single pointer in place; the prior versions survive as the safety net (§5), but the user does not fork a parallel "what-if" timeline. The branching model is fully designed (§5.3) and cheap to store, but the *non-coder branch-and-compare UX* is the dominant M1 risk, so v1 ships the immutable-version safety net WITHOUT the branch surface [A7 §4.3-equivalent, P3 §4.3, R6 §2.2]. This boundary is a stated contract so downstream consumers do not build against parallel timelines in v1.

---

## 4. Dependency-aware CASCADE re-execution (NET-NEW core)

**Disposition: NET-NEW composition over REUSED primitives.** This is the heart of the subsystem and the only mostly-net-new piece [R6 §7, A7 §5, P3 §3]. It composes *dirty-propagation* (from reactive computational notebooks like ipyflow) with *fingerprint-skip* (from content-addressed build systems like Bazel) over the ledger of §2 [R6 §2.1, A7 §5.1, P3 §3].

The brief's requirement: *"Users can retrace any previous step and intervene from there; downstream/cascading outputs change accordingly, but old outputs are versioned."*

### 4.1 The mechanism, step by step

1. **User retraces to Step N** (§3) — the UI shows N's recorded inputs, prompt, tool calls, and output [A7 §5.1.1, P3 §3.1.1].
2. **User changes an input or overrides a decision at N** — this creates a *new* Step N′ with a new `step_id` and a new `inputs_hash` (per the canonical Step identity rule, transparency-and-provenance.md §2.3–§2.4). The old Step N and its Output are **untouched**; they remain a prior version. This *is* "old outputs are versioned" [A7 §5.1.2, P3 §3.1.2].
3. **Dirty-marking** — the engine walks *all descendants of N* over the `depends_on` edges and marks them "potentially dirty" (potentially needing re-run). The descendant walk is **REUSED** from `WorkflowDAG.descendants()`, which is cheap (cached topological order) [R6 §2.1.3, A7 §5.1.3, P3 §3.1.3].
4. **Content-hash pruning — the "only affected downstream" guarantee** — the engine re-runs dirty steps in dependency order. For each, it recomputes the `inputs_hash` from its (possibly-unchanged) upstream outputs. **If the new fingerprint equals the recorded one, it skips the step and reuses the cached output.** Only steps whose inputs *actually* changed re-run. A step that depended on N but whose *other* inputs dominate may produce an identical result and **halt the cascade early** — the change does not propagate further [R6 §2.1.4, A7 §5.1.4, P3 §3.1.4].
5. **Versioning** — each re-run step's output is written as a *new version* with a back-pointer to the prior version. Nothing is overwritten [R6 §2.1.5, A7 §5.1.5, P3 §3.1.5].

The combination — dirty-propagation + fingerprint-skip — is precisely what delivers "downstream cascades re-execute, but only the affected ones, and old outputs survive." Recompute is **genuinely-affected-only**: a descendant whose recomputed `inputs_hash` is unchanged MUST be skipped (Invariant 4, §7).

### 4.2 What is REUSED, and the gaps the cascade closes

The Kailash durable-execution stack supplies the primitives; the cascade generalizes the *skip* operation from "within one run" to "across runs, keyed on content fingerprint" [R6 §6.1, A7 §5.1, P3 §3.1]:

| Primitive (REUSED)                  | What it gives                                       | Role in the cascade                                       |
| ----------------------------------- | -------------------------------------------------- | -------------------------------------------------------- |
| `ExecutionTracker`                  | Skip completed nodes within one run, replay cached | The *within-run* case of the broader cascade skip        |
| `DurableRequest` + `ExecutionJournal` | Per-request state machine + append-only audit     | The event log the ledger ingests                         |
| `Checkpoint` + `DBCheckpointStore`  | Serialized state, tiered dialect-portable persistence | The cascade's persistence layer                       |
| `IdempotentExecutor`                | Exactly-once via atomic claim                       | Makes re-runs idempotent                                 |
| `run_id`                            | Every `runtime.execute()` returns `(results, run_id)` | The spine stamping every Step                         |

**The four gaps the cascade (NET-NEW) closes** [R6 §3, P3 §3.2]:

1. **Resume ≠ retrace.** `DurableRequest.resume()` replays *forward* from the last checkpoint to recover from a crash. Retrace needs *rewind to an arbitrary past step, mutate it, and re-derive forward*.
2. **Checkpoint granularity is coarse.** Checkpoints land at validation/creation/completion boundaries, not per-step keyed by content hash. Retrace needs per-step immutable records keyed by content hash — that is the ledger (§2), not the checkpoint blob.
3. **No cross-run dependency graph.** `ExecutionTracker` is per-run; the cascade crosses runs/sessions/objectives via `Request.depends_on` + provenance edges.
4. **Determinism constraint.** Replay only works if steps are deterministic given inputs. LLM steps are NOT deterministic — see §6.

**Net:** Kailash supplies durable persistence, per-node skip, idempotent claim, and the `run_id` spine; the cascade engine layers on top as a new framework-level module (§9).

### 4.3 The cascade cost-preview contract

A change near the root of a wide DAG legitimately invalidates everything downstream. Content-hash skip bounds the *unnecessary* re-runs, but a root-prompt edit *correctly* re-runs everything [R6 §8 #2, A7 §8 #3, P3 §8 #3]. The contract:

- **A cascade that exceeds a preview threshold MUST present a cost-preview before it commits.** v1 deliberately excludes automatic cascade execution without preview [P3 §8.3].
- The preview is **estimated from historical `ExecutionMetric` data** (cost/latency per step-type) — **REUSED** as the estimation source, read before committing the cascade [P3 §7.2, R6 §8, A7 §8 #3].
- The preview states, in plain language: how many steps will re-run, the estimated cost and time, and which downstream sections will change. The user confirms (a yes/no gate) before the cascade runs.
- A cascade that the content-hash skip prunes to zero affected steps requires no preview — it is free (§8 short-circuit).

**Contract shape (data the preview must carry):**

| Field             | Meaning                                                   |
| ----------------- | -------------------------------------------------------- |
| `affected_steps`  | count of dirty steps the engine will actually re-run (post-prune estimate) |
| `estimated_cost`  | sum of `ExecutionMetric`-derived per-step cost           |
| `estimated_time`  | wall-clock estimate                                      |
| `affected_outputs`| the user-visible sections that will produce new versions |
| `irreversible_actions` | any dirty step that would re-trigger an external side-effect (§8.3) — surfaced separately and prominently |

---

## 5. Immutable versioning + the timeline model

**Disposition: REUSED** (version chain) **+ NET-NEW** (timeline pointer over the DAG). The version chain is the existing `Artifact.version` + `parent_artifact_id` [R6 §2.1, P3 §1.4]; the named-pointer-over-the-DAG timeline is the new wiring.

- **A version is a row, not an edit.** Every re-derivation appends. The lineage (`parent_output_id` for Outputs; the new-Step-node for Steps) is a chain the UI renders as "v1 → v2 → v3" with the ability to view any version and revert to it [P3 §5, R6 §2.1].
- **A timeline is a named pointer to a DAG head** [R6 §2.2, A7 §5.2, P3 §5]. In v1 there is exactly **one** timeline per objective (the "main" line); rewinding advances that single pointer. Post-v1, additional named heads = branches.
- **Revert is cheap and lossless.** Because nothing was overwritten, "go back to v1" is repointing to the prior version — the data was never destroyed (Invariant 1).
- **Compare-versions is a fingerprint diff.** Side-by-side "v1 vs v2 of this output" is a content comparison the UI renders; it does *not* re-run anything [R6 §2.2, P3 §5].
- **The intervention is itself a versioned, audited event** — *who* rewound, *what* they changed, *when* is a new audit record, never a silent edit (Invariant 6).

### 5.1 Worked example (the brief's 3Q report) [A7 §5.4, P3 §5]

The user gets a 3Q report, spots a wrong exchange-rate assumption two steps back in the *revenue* section, rewinds to that step, and changes the assumption. The cascade re-runs the revenue downstream and the final report; the *costs* and *cash-flow* sub-agents are **untouched** (their fingerprints match → skipped). The original report survives as v1; the corrected one is v2. The user can compare v1 vs v2 and revert. "User X changed the exchange-rate assumption at step N at time T" is a permanent audit record.

### 5.2 The v1 boundary on versioning (CONTRACT)

v1 keeps **every version forever** (the simplest correct behaviour). Storage grows without bound; content-addressing dedupes identical bytes but not version *count*. A retention/compaction policy is owed before scale and is deferred to post-v1 [P3 §8.3, A7 §8 #5, R6 §8] — flagged §8 #5.

### 5.3 Branching — designed, deferred (CONTRACT)

Branching is the Git-like model: an intervention at Step N forks a new timeline that shares all history ≤ N by reference and diverges after; content-addressing makes the fork cheap to store (structural sharing) [R6 §2.2, A7 §5.2, P3 §4.3]. The engine primitive (branch heads over the DAG) is ~1 cycle of work; the *non-coder UX* is open-ended. **v1 ships linear-retrace only, NO branching** (§3 boundary). This is the single most confusing concept (parallel timelines that diverge and must be compared) removed from the first release. The cost: "explore a what-if side-by-side" is deferred — the user advances the main timeline in place and old versions are the safety net instead of a parallel branch. Branching is the first post-v1 extension once the linear UX validates with real non-coder users.

---

## 6. The non-deterministic-LLM-step problem and its resolution

Model steps are **non-deterministic**: the same prompt can yield a different answer next time. This breaks the naive assumption behind "rewind and re-run" — that re-running a step reproduces what was there before [A7 §5.3, R6 §3 gap 4 §8, P3 §4].

### 6.1 Three distinct things "redo" can mean

| User intent                                                   | Term       | What the engine does                                                          | Determinism handling                                                            |
| ------------------------------------------------------------ | ---------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| "I changed an input three steps back; flow my change forward" | **Re-run** | Re-execute the affected downstream steps with the changed input               | Model steps *will* re-run and *may* legitimately differ — correct and expected  |
| "Show me exactly what happened last time, don't re-compute"   | **Replay** | Reconstruct past state from the recorded outputs by fingerprint — reuse the recorded answer | Fully deterministic — reads recorded results. Safe default for untouched steps |
| "Try a different path without losing the original"            | **Branch** | Fork a new timeline at Step N                                                 | Original preserved by reference; new branch re-runs its divergent suffix. **Deferred post-v1 (§5.3)** |

### 6.2 The resolution (CONTRACT)

> **Default to REUSE-RECORDED for every step the user did NOT touch; require an EXPLICIT per-step regenerate action for the step the user is editing; in v1, support LINEAR RETRACE only — NO branching.**

[A7 §5.3, R6 §3 gap 4 §7.1 invariant 3, P3 §4.2]

Concretely, on a rewind the engine **reuses the recorded output by fingerprint** for every step the user did not explicitly change, and only re-generates the steps the user *did* change (and their genuinely-affected downstream). It **never assumes a model call replays identically** — this is the same trick mature durable-execution systems use (record the result of a non-deterministic operation; replay the *recorded value*, not the operation). This is Invariant 3 (§7).

The user is given an **explicit, per-step choice** when it matters: *"re-run this with my edit (get a fresh answer)"* vs *"keep the recorded output, only re-run what depended on it."* That choice is **surfaced in the UI, not a hidden default** — because either behaviour is sometimes what the user wants and **guessing wrong silently is the worst outcome** [A7 §5.3, R6 §8, P3 §4.2].

**Implications (plain language).** The user's mental model becomes "the system shows me last time's answers unless I ask for a fresh one." Rewinding is predictable and free for untouched steps; editing a step is an explicit act with an explicit consequence the user chose.

**The legitimate-divergence obligation.** When a re-run *does* re-generate a model step, the new answer may differ in ways that are *correct but surprising* to a non-coder ("I only changed the date and the whole tone changed"). The product MUST show *what changed and why* between versions rather than pretend re-runs are deterministic [A7 §5.3, P3 §4.2]. This is a UX obligation and part of why the non-coder UX is the dominant risk (§8 #1).

---

## 7. Correctness INVARIANTS the cascade engine MUST hold

**Owner: `transparency-and-provenance.md` §2.6.** The six invariants the ledger MUST always hold — Immutability, Tenant isolation, Determinism boundary, Cascade minimality, Posture-at-time, Audit completeness — are owned and stated in full in **`specs/transparency-and-provenance.md` §2.6**. They are NOT restated here. The cascade engine MUST hold all six; this section adds only the cascade-specific reading of which invariants land in which implementation shard.

The count is load-bearing for sharding: there are **six** invariants, and per the capacity budget six invariants is the explicit signal that the cascade engine MUST be sharded, not built in one pass [R6 §7.1, A7 §3.4, P3 §6]. The two invariants the cascade engine bears most directly: **Cascade minimality** (transparency-and-provenance.md §2.6 invariant 4 — a descendant whose recomputed `inputs_hash` is unchanged MUST be skipped; this is the "only genuinely-affected downstream" promise §4.1 step 4) and the **Determinism boundary** (invariant 3 — LLM steps reuse the recorded output by content hash on retrace unless the user explicitly forces regeneration, §6.2). **Tenant isolation** (invariant 2) is the highest-severity and MUST appear in every shard (§7.1).

### 7.1 Sharding note (for /todos)

The cascade engine exceeds a single shard's capacity budget; it MUST be sharded [P3 §6.1]. The recommended decomposition: **S1** ledger ingestion + content-hash computation (holds Invariants 1, 2); **S2** descendant-walk + dirty-marking (holds 4-marking-half); **S3** content-hash skip + version-on-rerun + halt-early (holds 1, 4-skip-half, 6); **S4** determinism handling + posture-at-time snapshot (holds 3, 5). **Invariants 1 and 2 MUST appear in EVERY shard's invariant list** — a later shard that adds a cache key without `tenant_id` re-opens the leak. The cascade engine is an `*Engine`-shaped class and MUST land with a production call site (the comms-wedge hot path) + a Tier-2 wiring test in the same change — never a facade with no caller.

---

## 8. Edge cases

### 8.1 A changed step whose output is identical → short-circuit

A user edits Step N, but the edit produces an output whose `content_hash` equals the recorded one (e.g. a cosmetic change the model normalizes away, or a re-typed identical value). The engine recomputes N′'s `inputs_hash`; if downstream steps' recomputed `inputs_hash` matches their recorded values, **the cascade halts immediately** — zero downstream steps re-run, zero new versions are created beyond N′ itself, and the cost-preview reports `affected_steps: 0` [R6 §2.1.4, A7 §5.1.4, P3 §3.1.4, Invariant 4]. This is the fingerprint-skip guarantee at its limit: an identical-output change does not propagate. The short-circuit is what makes "rewind to inspect, change, decide it didn't matter" free.

### 8.2 Cycles

The provenance ledger is a **DAG** — a directed *acyclic* graph; the `depends_on` edges never loop back upstream [R6 §1, §2.1, A7 §3]. Because every Step's identity (`step_id`) includes the fingerprints of the steps it depends on (the content-addressing rule owned by transparency-and-provenance.md §2.3), a cycle is structurally impossible to form: a step cannot incorporate its own not-yet-computed fingerprint into its own identity. The descendant-walk (`WorkflowDAG.descendants()`) operates over a guaranteed-acyclic graph with a cached topological order. The engine MUST reject any attempted edge that would introduce a cycle (a Step declaring `depends_on` a descendant of itself) with a typed error at ingestion time, rather than entering an unbounded dirty-propagation loop. (The acyclicity is a structural property of content-addressing, not an additional check that can drift; the typed rejection is the defense for a malformed ingestion attempt.)

### 8.3 External side-effects already committed to a real system — the irreversibility problem

This is the hardest edge case and the one the versioning model **cannot** make lossless on its own. The ledger is perfectly reversible *for the recorded representation of work*: outputs, decisions, and steps are immutable rows you can revert to. But when a step's tool call **already committed an action to a real external system** — posted a journal entry to the ERP, sent an email, charged a card, filed a record — reverting the ledger to v1 does **not** un-send the email or un-post the ERP entry. The external world has no `parent_output_id`.

How versioning handles this:

- **The action is recorded, not undone.** The original tool call and its result are immutable ledger records (Invariant 1). Reverting the timeline to a prior version restores the *ledger's* view but does NOT issue a compensating external action automatically. The platform never silently fabricates a "rollback" of an irreversible external effect.
- **Cascade re-execution surfaces irreversible re-triggers in the cost-preview.** When a cascade would re-run a dirty step whose tool call has an external side-effect, that step is surfaced in the preview's `irreversible_actions` field (§4.3) **separately and prominently** — the user is told "re-running this step will post a SECOND entry to the ERP" before the cascade commits. A re-run that would re-fire an irreversible action MUST NOT proceed on the silent reuse-recorded/regenerate default; it requires an explicit user acknowledgment of the external consequence.
- **Idempotency bounds accidental double-firing.** Where the external system and the tool support an idempotency key, the **REUSED** `IdempotentExecutor` claim primitive prevents the same logical action from firing twice on a re-run (the second attempt reuses the recorded result rather than re-issuing). This is the structural defense against "the cascade charged the card twice."
- **The honest boundary (CONTRACT).** The platform delivers reversibility of the *work record* and traceability of *what hit the world and when* — it does NOT and cannot promise reversibility of effects already committed to systems it does not control. Compensating actions (issue a refund, post a reversing entry, send a correction email) are themselves new governed steps the user or agent must take; they are recorded as new Steps with their own provenance, never as a silent "undo." This is the versioning-side expression of the platform's traceability-not-accountability honesty boundary.

This edge case is also why the governance posture (M2) and the cost-preview gate matter most for side-effecting steps: the cheapest place to prevent an irreversible mistake is *before* the action fires, not in the versioning afterward.

---

## 9. Where the cascade engine lives (REUSE vs NEW disposition)

**Recommendation:** the cascade engine lives as a **framework-level module** operating over the DataFlow models + `WorkflowDAG`, *not* inside the comms-wedge app code [R6 §8, A7 §7.2, P3 §7.3]. This is consistent with the capability-first strategic stance (build the horizontal capability; the wedge consumes it).

- **REUSED:** the durable store, the descendant walk, the idempotent claim, the `run_id` spine, the PACT node models, the `ExecutionMetric` cost source, the `EventBridge`/`EventBus` live stream that writes into the ledger.
- **NET-NEW:** the cascade engine itself (dirty-propagation + fingerprint-skip + version-on-rerun), the unifying content-addressed ledger wiring, the `inputs_hash` + `posture_at_time` Step fields, the cost-preview contract, the linear-retrace timeline pointer, and the per-step regenerate-vs-reuse UI surface.
- **Implication / con:** a framework-level module has a higher integration bar (it must not assume the comms product's schema-per-tenant specifics) and depends on the durable-execution resume integration into the LocalRuntime hot path, which the research notes is "not yet GA" — a real external dependency that could gate the timeline [R6 §3 gap 1, A7 §7.2, P3 §7.3]. Placement MUST be confirmed with the framework specialists at design time (the runtime-ownership decision that determines whether M1 is buildable).

---

## 10. Open design points (flagged, not resolved)

Per spec-accuracy discipline these are genuine uncertainties a design/redteam phase must resolve; they are recorded here because they bound what this spec can promise [A7 §8, R6 §8, P3 §8.4]. The top two decide whether the feature is *usable*, not whether it can be *built*.

1. **Non-coder versioning UX (dominant risk).** "Rewind, change, see only the affected parts redo, compare versions, revert" is an unsolved design problem for non-coders. v1's linear-no-branching cut (§5.3) is the primary mitigation; residual UX risk is real. Resolution: UX design + real non-coder user testing.
2. **Re-run vs replay as a user-facing choice.** The per-step "regenerate / keep recorded" decision (§6.2) may confuse non-coders; guessing the default wrong silently is the worst outcome. Resolution: product decision + user testing.
3. **Cascade cost explosion.** Bounded by content-hash skip and the cost-preview (§4.3) but a root edit correctly re-runs everything. Resolution: the preview, estimated from `ExecutionMetric` history.
4. **The span→ledger ingestion contract.** When a span becomes a permanent node; how partial/failed spans are handled (the ledger-as-source-of-truth architecture is owned by transparency-and-provenance.md §2.5). Resolution: engine design.
5. **Storage growth / retention policy.** Every re-run is a new version forever (§5.2). Resolution: an operational retention/compaction policy.
6. **Single-process event bus.** The live decision stream's `EventBus` is in-memory; multi-replica needs a durable/distributed bus. Resolution: infrastructure, deferred.
7. **Framework vs app placement of the engine** (§9). Resolution: confirm with framework specialists — the runtime-ownership decision.

---

## 11. Source ledger

- **[P3]** `workspaces/future-of-work/02-plans/03-provenance-cascade-design.md` — §0 thesis, §1 data model, §3 cascade mechanism + reuse table + gaps, §4 determinism, §5 timeline, §6 invariants + shard map, §7 reuse-vs-extend, §8 v1 scope + cost-preview + risks.
- **[A7]** `workspaces/future-of-work/01-analysis/07-transparency-intervention-architecture.md` — §3 ledger + six invariants, §5 intervention + cascade + determinism + worked example, §6 layer cake + reuse inventory, §7 recommendation + placement, §8 ranked unknowns.
- **[R6]** `workspaces/future-of-work/01-analysis/01-research/06-transparency-intervention-versioning.md` — §1 provenance entities + content-addressing, §2 intervention semantics + branching, §3 durable-execution reuse + determinism gap, §6 unifying skip insight + comms wedge, §7 novel parts + invariants + cycle estimate, §8 risks.

> Note on splitting: if the cascade engine's implementation contract (the S1–S4 shard internals, the ingestion contract, the descendant-walk algorithm) grows beyond a skim-readable section, §4 + §7 split into a sibling `specs/cascade-engine.md` and this file retains the semantics, the timeline model, the determinism resolution, and the edge cases.
