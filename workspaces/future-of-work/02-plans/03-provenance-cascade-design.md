# Plan 03 — Provenance Ledger + Cascade Engine: The Net-New Core of M1

> **Purpose.** This is the design plan for the single hardest subsystem in the platform — the
> **provenance ledger** (the permanent, inspectable record of everything the system did) and the
> **cascade engine** (the machinery that lets a non-coder rewind to any past step, change it, and have
> only the genuinely-affected downstream work recompute while old results survive as versions). It turns
> moat **M1** (transparent, versioned, intervene-from-any-step work) from architecture prose into a
> buildable, shardable plan a technical founder can authorize.
>
> **Audience.** A technical founder deciding what to build and in what order. Plain language throughout;
> every technical term is translated on first use (per `.claude/rules/communication.md`). Effort is in
> **autonomous execution cycles** — work an AI agent system completes in a focused session — never
> human-days or team-size (per `.claude/rules/autonomous-execution.md`).
>
> **Grounding.** This plan is the design-grade synthesis of three files read in full:
> `01-analysis/07-transparency-intervention-architecture.md` (the architecture decision document),
> `01-research/06-transparency-intervention-versioning.md` (the provenance/cascade/versioning research),
> and `01-research/03-pact-governance.md` (the governance substrate). It also draws on the brief
> (`briefs/01-vision.md` §3e–3f) and the strategic spine. Every load-bearing claim cites one of these.
> Genuine uncertainty is flagged, not smoothed over (per `.claude/rules/spec-accuracy.md`).
>
> **Scope boundary.** This plan covers the provenance ledger (L1) and the cascade engine (L3) — the
> net-new core. The governance/posture layer (L2) and the timeline UI (L4) are designed in their own
> plans; this plan specifies only the L1/L3 contracts those layers consume, and cites where L2/L3 meet.

---

## 0. The thesis in one paragraph

When an AI agent does a piece of knowledge work today, you get the answer and nothing else: you cannot
see why it did what it did, you cannot change one decision it made three steps ago without redoing
everything, and when you redo it the old version is gone. This subsystem makes agentic work a **glass
box with an undo-from-anywhere button**. Two pieces deliver it. The **provenance ledger** is a permanent,
tamper-evident record of every step, every decision, every tool call, and every output — stored so that
each record is identified by a fingerprint of its own content, which makes it impossible to silently
alter and cheap to reuse. The **cascade engine** is the machinery that, when a user rewinds to a past
step and changes it, walks the dependency graph and re-runs *only* the parts that genuinely depend on
that change — while every prior result survives as a named version you can compare against and return to.
The research establishes that ~80% of the substrate already exists across the Kailash/PACT/aegis
ecosystem; the genuinely new engineering is **the cascade engine plus the unifying ledger wiring**
(`01-analysis/07` §6.3). This plan specifies the data model, the transparency boundary, the
re-execution semantics, the determinism handling, the correctness invariants for sharding, and a
deliberately-reduced v1 scope.

---

## 1. The data model — a content-addressed immutable provenance DAG

"Provenance" means the recorded origin and history of every piece of work — what produced it, from what,
and when. A "DAG" (directed acyclic graph) is a network of records connected by one-way arrows that never
loop back on themselves — step B depends on step A, step C depends on B, but nothing ever points back
upstream. The provenance ledger is that DAG, made permanent and queryable.

### 1.1 The three node kinds

The central research finding is that this data model **already exists** as the PACT platform's
work-tracking records — it has simply never been wired to a rewind engine (`01-research/06` §1.1,
`01-analysis/07` §3.1). There are exactly three kinds of node:

| Node kind    | Maps to existing PACT model | Plain meaning                                                          | Load-bearing fields                                                                                                            |
| ------------ | --------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Step**     | `Run`                       | One invocation — one model call, one tool call, one workflow run       | `inputs_hash`, `outputs_hash`, `agent_id`, `posture_at_time`, `prompt_ref`, `tool_calls[]`, `status`, start/end, `cost`. **Immutable.** |
| **Output**   | `AgenticArtifact`           | One produced result                                                    | `content_hash` (fingerprint of the bytes), `version`, `parent_output_id` (the prior version it supersedes), `produced_by_step_id`, `classification`. **Immutable — a new version is a new row, never an overwrite.** |
| **Decision** | `AgenticDecision`           | A surfaced choice — a fan-out plan, a held action, a posture gate      | `status` (pending/approved/rejected), `decided_by`, `decided_at`, `envelope_version`, `decision_type`. **Immutable — resolving it creates a new linked record, never an edit.** |

Source for the existing models: `01-research/03` §6.1–6.2 (the 17 PACT DataFlow models), `01-research/06`
§1.1. Crucially, `AgenticArtifact` already carries `content_hash` (SHA-256) + `version` +
`parent_artifact_id` — the immutable version chain is already modeled (`01-research/03` §6.1, "the
existing substrate for the brief's 'old outputs are versioned'").

### 1.2 The typed edges

Every connection between nodes is a *typed* relationship (it has a named meaning, not just "related to"):

```
Step   --consumes-->   Output     (input lineage — what this step took in)
Step   --produces-->   Output     (output lineage — what this step made)
Step   --depends_on--> Step       (the dependency that DRIVES recompute — PACT's Request.depends_on)
Step   --gated_by-->   Decision   (this step waited on a surfaced decision)
Output --derived_from->Output     (the version chain — parent_output_id)
```

The `depends_on` edge is the one the cascade engine walks. It already exists as
`AgenticRequest.depends_on` — a `{"request_ids": [...]}` set that is *already a DAG edge-set*
(`01-research/06` §1.1, `01-analysis/07` §6.2). The plan does not invent dependency tracking; it
*consumes* the dependency tracking PACT already records.

### 1.3 Why "content-addressed" is the load-bearing trick

"Content-addressed" means every Step and Output is identified by a **fingerprint of its content** — a
SHA-256 hash, a short string that changes completely if even one byte of the content changes — not by a
sequential ID. This is the same idea behind how Git identifies commits and how IPFS identifies files
(`01-research/06` §1.3, `01-analysis/07` §3.2). It buys three properties that make the whole feature
possible and cheap:

1. **Tamper-evidence / immutability for free.** If a recorded result is altered, its fingerprint no
   longer matches — so it cannot be silently changed. This is the same property aegis already
   demonstrates with its signed posture anchors, where each record carries `record_hash` + a back-pointer
   to its parent (`01-research/06` §2.2, `01-analysis/07` §3.2).
2. **Cheap branching via structural sharing.** When you fork a timeline to explore a "what-if," the new
   branch *reuses the entire unchanged history by reference* — only the changed part is new data. A
   what-if exploration does not cost a full re-run of everything (`01-research/06` §2.2).
3. **The "only recompute what changed" guarantee.** A Step's identity is computed as
   `hash(its inputs + its code/prompt reference + the fingerprints of the steps it depends on)`. Two runs
   with identical inputs and identical upstream produce the *same* identity — so the engine can recognize
   "nothing actually changed here" and skip the re-run, reusing the cached result. This is exactly how
   build systems like Bazel decide what to rebuild, and it is the core of the cascade engine
   (`01-research/06` §1.3, §6.1; `01-analysis/07` §3.2).

### 1.4 Versioned nodes — what "immutable + versioned" means concretely

Nodes are **never updated in place**. The version model is append-only:

- An Output that gets re-derived produces a **new row** with `version = prior.version + 1` and
  `parent_output_id` pointing at the prior version. The original row is untouched
  (`01-research/03` §6.1, `01-research/06` §2.1 step 5).
- A Step that gets re-executed produces a **new Step node** (call it N′) with a new `inputs_hash`; the
  old Step N stays in the ledger as a prior version (`01-analysis/07` §5.1 step 2).
- A Decision that gets resolved produces a **new linked record** carrying the resolution; the original
  pending Decision stays (`01-analysis/07` §3.1).

A "timeline" is then a **named pointer to a head of the DAG** — exactly like a Git branch is a named
pointer to a commit (`01-research/06` §2.2, `01-analysis/07` §5.2). "Compare two timelines" is a
fingerprint-by-fingerprint comparison of their histories.

### 1.5 The ledger is the source of truth; telemetry feeds it

A clean architectural decision (`01-research/06` §8, `01-analysis/07` §3.3): the live event stream
(OpenTelemetry spans — ephemeral telemetry that streams to the screen as work happens) is the *feed*; the
provenance ledger is the *permanent record*. **Spans write into the ledger; the ledger is the source of
truth.** This avoids the "two databases that disagree" problem and gives one clean place to query
history. Persistence reuses the Kailash durable store (`DBCheckpointStore` / `StoreFactory`) that already
ships (`01-research/06` §3, §6; `01-analysis/07` §3.3). The plan needs a clean **ingestion contract** —
the rule for how a live span becomes a permanent ledger node — flagged as an open design point in
§8 (unknown #4).

---

## 2. The transparency contract — drawing the boundary crisply

The single most important thing this subsystem does, after the cascade, is **define exactly what is and
isn't recorded**. A fuzzy boundary is a broken promise: either you over-claim ("we show you everything
the AI does," which is false) or you under-deliver ("we just log the final answer," which is no different
from today) — `01-analysis/07` §2.

### 2.1 RECORDED and SURFACED (the glass box)

For every step a human or agent takes, the ledger records and can display (`01-analysis/07` §2.1,
`01-research/06` §5.1):

| Recorded & shown                          | Plain-language meaning                                                                       |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Inputs**                                | Exactly what went into the step — the data, documents, prior results it consumed             |
| **Decisions, plans, and fan-outs**        | The choices the agent made *before* acting — "I will split this into 3 sub-tasks"            |
| **Tool calls**                            | Every external action requested — which tool, with what arguments ("query the Q3 ledger")    |
| **Tool results**                          | What each tool returned — the rows, the API response, the file it read                       |
| **Outputs**                               | What the step produced — the draft, the number, the message — versioned                      |
| **Metadata**                              | Model used, cost, time, and *which posture was in force when the step ran*                    |

This is exactly the shape the **OpenTelemetry GenAI Semantic Conventions** define — an industry-standard
schema for tracing AI systems that the observability industry has converged on (`01-analysis/07` §2.1,
`01-research/06` §5.1). Kailash's Core SDK already emits this shape today via its tracing levels
(`01-research/06` §5.2). We adopt the standard rather than invent one.

### 2.2 NOT recorded (the black box)

Deliberately not recorded (`01-analysis/07` §2.2, `01-research/06` §5.3):

| NOT recorded (the black box)                                  | Why we cannot / should not record it                                                                  |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| The model's **chain-of-thought** (its internal scratchpad)   | Often not exposed by the model's interface; unstable across model versions; frequently most sensitive |
| The model's **internal activations / weights**               | Billions of opaque numbers; recording them explains nothing a human could act on                      |
| **Token-level logits** (*why* it picked one word over another) | Not human-interpretable; explains nothing in business terms                                          |

**The one subtlety the brief flags (3f), made crisp.** Some model providers now expose a *summarized
reasoning trace* — a short, model-generated explanation of its approach — distinct from raw
chain-of-thought. Where a model voluntarily emits such a summary at its output surface, the ledger records
it (the EATP SDK has an explicit `reasoning-traces` slot for this — `01-research/06` §5.3). The boundary
is therefore stated precisely (`01-analysis/07` §2.2):

> **We record everything the model emits at its input/output surface — including any reasoning summary it
> chooses to surface. We do not record, and do not claim to record, how the model actually computed its
> answer internally.**

### 2.3 The honesty caveat that travels with every trust claim

The system delivers **traceability, not accountability** (`01-analysis/07` §2.3, `01-research/03` §2.3):

- **Traceability** (the machine guarantees this): every AI action traces back to its inputs, its
  decisions, and the human authority that permitted it.
- **Accountability** (no software can guarantee this): that a human actually *understood*, evaluated, and
  bears the consequences of what the agent did.

The transparency surface converts traceability into a *chance* at real accountability — it makes
understanding *possible* — but it cannot force understanding. We promise the glass box; we do not promise
that the human looked through it. Over-claiming here is both dishonest and legally hazardous.

---

## 3. Dependency-aware CASCADE re-execution — the genuinely new core

This is the heart of the subsystem and the only piece that is mostly net-new (`01-research/06` §7,
`01-analysis/07` §5). The brief (3e): *"Users can retrace any previous step and intervene from there;
downstream/cascading outputs change accordingly, but old outputs are versioned."*

The established art borrowed from is **reactive computational notebooks** (tools like ipyflow that, when
you change one cell, automatically re-run only the cells that depend on it) layered over the
content-addressed graph from §1 (`01-research/06` §2.1, `01-analysis/07` §5.1).

### 3.1 The mechanism, step by step

1. **The user retraces to Step N.** The UI reads the provenance DAG (§1) and shows Step N's recorded
   inputs, the prompt that went in, the tool calls it made, and the output it produced — the transparency
   surface from §2 (`01-analysis/07` §5.1 step 1).
2. **The user changes an input or overrides a decision at N.** This creates a *new* Step N′ with a new
   `inputs_hash`. The old Step N and its Output are **untouched** — they remain as a prior version. This
   *is* "old outputs are versioned" (§1.4; `01-analysis/07` §5.1 step 2).
3. **Dirty-marking.** The engine walks *all descendants of N* — every step downstream that could be
   affected — and marks them "potentially dirty" (potentially needing re-run). The graph operation to find
   descendants already exists in the Kailash `WorkflowDAG.descendants()` and is cheap (cached topological
   order) — `01-research/06` §2.1, `01-analysis/07` §5.1 step 3.
4. **Content-hash pruning — the "only affected downstream" guarantee.** The engine re-runs dirty steps in
   dependency order. For each, it recomputes the `inputs_hash` from its (possibly-unchanged) upstream
   outputs. **If the new fingerprint equals the recorded one, it skips the step and reuses the cached
   output.** Only steps whose inputs *actually* changed re-run. A step that depended on N but whose *other*
   inputs dominate may produce an identical result and **halt the cascade early** — the change does not
   propagate further (`01-research/06` §2.1 step 4, `01-analysis/07` §5.1 step 4).
5. **Versioning.** Each re-run step's output is written as a *new version* with a back-pointer to the prior
   version. Nothing is overwritten (`01-research/06` §2.1 step 5).

The combination — *dirty-propagation* (from reactive notebooks) + *fingerprint-skip* (from build systems)
— is precisely what delivers "downstream cascades re-execute, but only the affected ones, and old outputs
survive." The unifying insight (`01-research/06` §6.1, `01-analysis/07` §5.1): this is the *same* skip
operation Kailash already performs in three other places — crash-recovery (`ExecutionTracker` skips
completed nodes), idempotency (`IdempotentExecutor` skips a claimed run), and within-run node-skipping —
**just generalized from "within one run" to "across runs, keyed on content fingerprint."** That is why
this is a 20% novel *composition*, not an 80% greenfield *build*: the hard primitive
(content-addressed memoization) already ships; the new work lifts its scope.

### 3.2 What durable-execution reuse buys, and where the gap is

The research is precise about what Kailash's durable-execution stack already gives versus what the cascade
adds (`01-research/06` §3, `01-analysis/07` §6.2):

| Primitive Kailash already ships          | What it gives                                                          | Reuse vs extend                                                              |
| ---------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `ExecutionTracker`                       | Skip completed nodes within one run, replay cached output             | **REUSE** the skip logic as the within-run case of the broader cascade      |
| `DurableRequest` + `ExecutionJournal`    | Per-request state machine + append-only audit of every state change   | **REUSE** as the event log the ledger ingests                               |
| `Checkpoint` + `DBCheckpointStore`       | Serialized state at boundaries; tiered, dialect-portable persistence  | **REUSE** as the cascade's persistence layer                                |
| `IdempotentExecutor`                     | Exactly-once via atomic claim                                          | **REUSE** the claim primitive to make re-runs idempotent                    |
| `run_id`                                 | Every `runtime.execute()` returns `(results, run_id)`                 | **REUSE** as the spine stamping every Step                                  |

**The four gaps the cascade must close** (`01-research/06` §3):

1. **Resume ≠ retrace.** `DurableRequest.resume()` replays *forward* from the last checkpoint to recover
   from a crash. The brief needs *rewind to an arbitrary past step, mutate it, and re-derive forward*.
   Resume restores to the latest good state; retrace must restore to *any* state and branch.
2. **Checkpoint granularity is coarse.** Checkpoints land at validation/creation/completion boundaries —
   not per-step keyed by content hash. Retrace needs per-step immutable records keyed by content hash —
   that is the provenance ledger (§1), not the checkpoint blob.
3. **No cross-run dependency graph.** `ExecutionTracker` is per-run; the cascade crosses
   runs/sessions/objectives. The cross-run DAG is `Request.depends_on` + the provenance edges.
4. **Determinism constraint.** Replay only works if steps are deterministic given inputs. LLM steps are
   NOT deterministic — see §4.

**Net:** Kailash supplies durable persistence, per-node skip, idempotent claim, and the `run_id` spine.
The cascade engine layers *on top* and is a new framework-level module (§7.3).

---

## 4. The hard problem — non-deterministic LLM steps

This is the part the brief's vision glosses and this plan must not. **Model steps are non-deterministic:
the same prompt can yield a different answer next time.** That breaks the naive assumption behind "rewind
and re-run" — that re-running a step reproduces what was there before (`01-analysis/07` §5.3,
`01-research/06` §3 gap 4, §8).

### 4.1 Three distinct things "redo" can mean

There are three distinct user intents, with three correct behaviours (`01-analysis/07` §5.3):

| The user's intent                                            | Term        | What the engine does                                                                          | Determinism handling                                                                                       |
| ----------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| "I changed an input three steps back; flow my change forward" | **Re-run**  | Re-execute the affected downstream steps with the changed input                               | Model steps *will* re-run and *may* legitimately differ. This is correct and expected — the input changed.  |
| "Show me exactly what happened last time, don't re-compute"   | **Replay**  | Reconstruct the past state from the recorded outputs by fingerprint — reuse the recorded answer | Fully deterministic, because we read recorded results, not re-generate. Safe default for untouched steps.   |
| "Try a different path without losing the original"            | **Branch**  | Fork a new timeline at Step N (§5)                                                             | The original is preserved by reference; the new branch re-runs its divergent suffix only.                   |

### 4.2 The recommended default — reuse-recorded-output unless changed; explicit regenerate

**The design decision that makes this work** (`01-research/06` §3 gap 4, §7.1 invariant 3;
`01-analysis/07` §5.3): on a rewind, the engine **reuses the recorded output by fingerprint** for every
step the user did *not* explicitly change, and only re-generates the steps the user *did* change (and
their genuinely-affected downstream). It **never assumes a model call replays identically.** This is the
same trick mature durable-execution systems use — recording the result of a non-deterministic operation
and replaying the *recorded value*, not re-executing it.

The user is given an **explicit, per-step choice** when it matters (`01-research/06` §8): *"re-run this
with my edit (get a fresh answer)"* vs *"keep the recorded output, only re-run what depended on it."* That
choice is surfaced in the UI, not a hidden default — because either behaviour is sometimes what the user
wants, and **guessing wrong silently is the worst outcome** (`01-analysis/07` §5.3).

**The recommendation (single, with implications and symmetric pros/cons per
`.claude/rules/recommendation-quality.md`):**

> **Default to REUSE-RECORDED for every step the user did not touch; require an EXPLICIT regenerate action
> for the step the user is editing; in v1, support LINEAR RETRACE only — NO branching.**

*Implications.* The user's mental model becomes "the system shows me last time's answers unless I ask for a
fresh one." Rewinding is predictable and free for untouched steps. Editing a step is an explicit act with
an explicit consequence the user chose. Dropping branching from v1 removes the single most confusing
concept (timelines that diverge and must be compared) from the first release; the cost is that "explore a
what-if without losing the original" is deferred — the user advances the main timeline in place, and old
versions survive as the safety net instead of a parallel branch.

*Pros (real):* (a) Predictable — reuse-by-default means a rewind never surprises the user with a different
answer they did not ask for. (b) Cheap — untouched steps cost nothing to re-display. (c) Honest about
non-determinism — the explicit regenerate action names the fact that re-running an LLM step may differ.
(d) Linear-only removes the hardest UX concept (branching/merging) from v1, directly de-risking the
dominant unknown (§8 #1).

*Cons (real, not glossed):* (a) The per-step "regenerate vs keep" choice is a genuine conceptual burden we
are partly *pushing onto the user*; if users find it confusing, the feature feels unpredictable
(`01-analysis/07` §7.3 cons). (b) Without branching, a user who wants to compare two genuinely different
approaches must do it sequentially (advance, inspect, revert, advance again) rather than side-by-side —
clunkier, but legible. (c) When a re-run *does* re-generate a model step, the new answer may differ in
ways that are *correct but surprising* to a non-coder ("I only changed the date and the whole tone
changed") — the product must show *what changed and why* between versions rather than pretend re-runs are
deterministic. This is a UX obligation and part of why the non-coder UX is the dominant risk
(`01-analysis/07` §5.3 legitimate-divergence caveat).

### 4.3 Why linear-retrace-no-branching is the right v1 cut

Branching is the Git-like model (`01-research/06` §2.2, `01-analysis/07` §5.2): an intervention at Step N
can fork a new timeline that shares all history ≤ N by reference and diverges after. The content-addressed
store makes the fork *cheap to store* (structural sharing). But "rewind, fork, compare timelines, revert"
for a non-coder is the **single biggest risk in M1** (`01-analysis/07` §8 unknown #1 — "Git is hard for
experts"). The engine primitive (branch heads over the DAG) is ~1 cycle of work (`01-research/06` §7 item
2); the *UX* is open-ended. v1 ships the immutable-version safety net (you can always revert to a prior
version) without the branch-and-compare surface — capturing the value (nothing is lost) without the
confusing concept (parallel timelines). Branching is the first post-v1 extension once the linear UX is
validated with real non-coder users.

---

## 5. The immutable versioning + timeline model

This section makes §1.4 concrete as a timeline the user experiences.

- **A version is a row, not an edit.** Every re-derivation appends. The version lineage
  (`parent_output_id` for Outputs, the new-Step-node for Steps) is a chain the UI renders as "v1 → v2 →
  v3" with the ability to view any version and revert to it (`01-research/03` §6.1, `01-research/06`
  §2.1).
- **A timeline is a named pointer to a DAG head** (`01-research/06` §2.2, `01-analysis/07` §5.2). In v1
  there is exactly **one** timeline per objective (the "main" line); rewinding advances that single
  pointer. Post-v1, additional named heads = branches.
- **Revert is cheap and lossless.** Because nothing was overwritten, "go back to v1" is repointing to the
  prior version — the data was never destroyed (the immutability invariant, §6 #1).
- **Compare-versions is a fingerprint diff.** Side-by-side "v1 vs v2 of this output" is a content
  comparison the UI renders; it does *not* require re-running anything (`01-research/06` §2.2).
- **The intervention is itself a versioned, audited event** — *who* rewound, *what* they changed, *when*
  is a new audit record, never a silent edit (§6 #6; `01-analysis/07` §3.4 invariant 6).

The brief's worked example, traced end-to-end through this model (`01-analysis/07` §5.4): the user gets a
3Q report, spots a wrong exchange-rate assumption two steps back in the *revenue* section, rewinds to that
step, changes the assumption; the cascade re-runs the revenue downstream and the final report; the *costs*
and *cash-flow* sub-agents are **untouched** (their fingerprints match → skipped); the original report
survives as v1, the corrected one is v2; the user can compare and revert; and "user X changed the
exchange-rate assumption at step N at time T" is a permanent record.

---

## 6. Correctness invariants the cascade engine MUST hold (for /todos sharding)

These are the rules the implementation must never violate. They are listed here so they can be enforced
*and* so the work can be split correctly when it is planned. There are **six** of them — at the upper edge
of the ≤5–10-invariant capacity budget per `.claude/rules/autonomous-execution.md` § Per-Session Capacity
Budget, which is the explicit signal that the cascade engine MUST be sharded, not built in one pass
(`01-research/06` §7.1, `01-analysis/07` §3.4).

1. **Immutability.** A re-execution NEVER mutates a prior Step/Output/Decision; it appends a new version.
   Enforced by `ON DELETE RESTRICT` + append-only at the application layer (already specified for
   `AuditEntry` and `AgenticArtifact` — `01-research/06` §1.2, §7.1).
2. **Tenant isolation.** Every content-hash, cache key, and DAG query carries `tenant_id`. A shared
   content-address namespace across tenants is a cross-tenant data leak. Per
   `.claude/rules/tenant-isolation.md`; the existing Sequor comms product already uses schema-per-tenant
   (`01-research/06` §7.1, `01-analysis/07` §3.4 #2). **This is the highest-severity invariant** — a
   missing `tenant_id` on a cache key is a P0 cross-customer leak.
3. **Determinism boundary.** LLM steps reuse the recorded output by content hash on retrace UNLESS the
   user explicitly forces regeneration; the engine never assumes an LLM call replays identically (§4.2;
   `01-research/06` §7.1 invariant 3, `01-analysis/07` §3.4 #3).
4. **Cascade minimality.** A descendant whose recomputed `inputs_hash` is unchanged MUST be skipped. This
   is the "only affected downstream" promise; violating it makes rewind slow and expensive
   (`01-research/06` §7.1, §2.1 step 4; `01-analysis/07` §3.4 #4).
5. **Posture-at-time.** Every Step records the posture in force when it ran, so a retrace can show "this
   ran on its own (Autonomous)" vs "a human approved this (One-Check)" (`01-research/06` §7.1,
   `01-analysis/07` §3.4 #5). This is the L2/L3 contract point — the cascade reads posture from the EATP
   posture machine but stores a *snapshot* on the Step.
6. **Audit completeness.** The intervention itself is an auditable action — *who* retraced, *what* they
   changed, *when*. A new audit record, never a silent edit (`01-research/06` §7.1, `01-analysis/07`
   §3.4 #6).

### 6.1 Recommended shard map for /todos (each ≤500 LOC load-bearing, ≤5 invariants)

The cascade engine exceeds a single shard's capacity budget. The recommended decomposition — each shard
carries its own value-anchor (deliver retrace-and-intervene on the comms wedge per the brief's M1
objective) and a live feedback loop where noted (per `.claude/rules/autonomous-execution.md` § Feedback
Loops Multiply Capacity):

| Shard | Scope (describable in ≤3 sentences)                                                                                                | Invariants held                          | Feedback loop                          |
| ----- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | -------------------------------------- |
| **S1** | Ledger ingestion contract — wire OTel spans + PACT models + durable store into one content-addressed graph; compute Step/Output content hashes. | #1 Immutability, #2 Tenant isolation     | Unit + Tier-2 against a fixture DAG     |
| **S2** | Descendant-walk + dirty-marking over `depends_on` (reuse `WorkflowDAG.descendants()`); produce the ordered dirty set.              | #4 Cascade minimality (marking half)     | Unit against a fixture graph            |
| **S3** | Content-hash skip + version-on-rerun — recompute `inputs_hash`, skip-or-rerun, append new version, halt-early on match.            | #1, #4 (skip half), #6 Audit completeness | Tier-2: cascade vs fixture DAG, live    |
| **S4** | Determinism handling — reuse-recorded default + the explicit per-step regenerate path; snapshot posture-at-time on each Step.      | #3 Determinism boundary, #5 Posture-at-time | Tier-2 with a recorded-output fixture   |

S2+S3 are the load-bearing core (the actual cascade); S1 is mostly wiring of existing models; S4 is the
determinism policy. S3 carries a live feedback loop (each cascade is testable against a fixture graph —
`01-research/06` §7 item 1, `01-analysis/07` §6.3 item 1), so it MAY run at higher budget. **Tenant
isolation (#2) and immutability (#1) must be in EVERY shard's invariant list**, not just S1 — a later
shard that adds a cache key without `tenant_id` re-opens the leak (per `tenant-isolation.md` audit
protocol). The orphan-detection / facade-manager rules apply: the cascade engine is a `*Engine`-shaped
class and MUST land with a production call site (the comms-wedge hot path) + a Tier-2 wiring test in the
same change — never a facade with no caller (per `.claude/rules/orphan-detection.md`,
`facade-manager-detection.md`; this is the exact Phase-5.11 failure those rules exist to prevent,
flagged for PACT's facade-heaviness at `01-analysis/07` §7.3 cons).

---

## 7. How existing ecosystem assets are reused vs extended

The build-vs-reuse picture, grounded in the reuse ratios from `01-research/06` §6 and `01-research/03`
§8.5.

### 7.1 Kailash durable-execution / run_id / checkpoints — REUSE wholesale

Covered in §3.2. Summary: `ExecutionTracker` (within-run skip → the cascade's within-run case),
`DurableRequest`/`ExecutionJournal` (the event log the ledger ingests), `Checkpoint`/`DBCheckpointStore`
(persistence), `IdempotentExecutor` (idempotent re-runs), `run_id` (the Step spine). The cascade
**generalizes** the skip logic from intra-run to cross-run, keyed on content hash — it does not rebuild
any of these (`01-research/06` §3, §6.1; `01-analysis/07` §6.2).

### 7.2 PACT models, EventBridge, Decision, ExecutionMetric — REUSE + narrow extend

| PACT asset                            | Disposition | What changes                                                                                                       |
| ------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------- |
| `Run` / `AgenticArtifact` / `AgenticDecision` | **REUSE** as Step / Output / Decision node kinds (§1.1). `Artifact.version` + `parent_artifact_id` already give versioning. | Add `inputs_hash` + `posture_at_time` to the Step projection if not already present (the ledger projection over `Run`). |
| `AgenticRequest.depends_on`           | **REUSE** as the cascade DAG edge-set (§1.2).                                                                       | None — consumed as-is.                                                                                             |
| `EventBridge` + `EventBus`            | **REUSE** as the live decision/plan stream that *writes into* the ledger (§1.5).                                    | Define the ingestion contract (span → ledger node). The in-memory `EventBus` is single-process — a multi-replica scaling gap flagged in §8 #6 (`01-research/06` §8). |
| `AgenticDecision` (Decision node)     | **REUSE** as the `gated_by` decision record.                                                                        | L2 adds a `plan_proposed` subtype (surface a fan-out plan pre-execution) — that extension is L2's plan, not this one; this plan only consumes the Decision node. |
| `ExecutionMetric`                     | **REUSE** as the historical cost/latency source for the **cascade cost-preview** (§8 #3 mitigation).               | None — read for estimation before committing a cascade.                                                            |

Source: `01-research/03` §6.1–6.2 (models), §5.3 (EventBridge), §8.3 (the 80% reuse table);
`01-research/06` §1.1, §4.1.

### 7.3 Where the cascade engine lives — a framework-level module, not Sequor-app code

**Recommendation:** the cascade engine lives as a **framework-level module** operating over the DataFlow
models + `WorkflowDAG`, *not* inside the Sequor app (`01-research/06` §8 last bullet, `01-analysis/07`
§7.2). This is consistent with the strategic spine's capability-first stance and Decision B (build the
horizontal capability; the wedge consumes it). *Implication:* the engine is reusable by any vertical, not
just comms — but placement must be confirmed with the framework specialists at design time (the runtime-
ownership SPIKE the spine flags as determining whether M1 is buildable at all). *Pro:* maximum reuse,
moat-aligned. *Con:* a framework-level module has a higher integration bar (it must not assume Sequor's
schema-per-tenant specifics) and depends on the durable-execution resume integration, which the research
notes is "not yet GA" in the LocalRuntime hot path (`01-research/06` §3 gap 1) — a real external
dependency that could gate the timeline.

---

## 8. Recommended v1 scope (deliberately reduced) + highest-risk unknowns

### 8.1 The recommendation

> **Build the provenance ledger (L1) + the cascade engine (L3) and prove them end-to-end on the comms
> wedge's 4-step flow (`Message → Classification → RAG-retrieval → Response`), with: reuse-recorded-output
> as the default; explicit per-step regenerate; LINEAR retrace only (no branching); immutable versioning
> with revert + compare; and the full transparency boundary. Run governance in SHADOW mode under the live
> comms product during rollout. Defer branching, cross-vertical generalization, and the multi-replica
> event bus to post-v1.**

*Why the comms wedge first* (`01-research/06` §6.2, `01-analysis/07` §6.4): it is a *small, concrete
instance* of the general DAG. Each of its 4 steps is a Step; `Response.content` is a versioned Output; the
classification reasoning and retrieved passages are recorded I/O. The wedge's *existing*
`classification_corrected` discipline (log a correction as a new audit row) is literally the
retrace-and-version primitive **already specified in prose** — a user correcting a classification should
create a new version and re-derive the downstream response. Proving retrace-and-intervene on a 4-step flow
before generalizing is the natural first vertical, and `EnforcementMode.SHADOW` (observe, never block) is
how governance slots under the live product without breaking it (`01-research/03` §5.5).

### 8.2 Effort estimate (autonomous execution cycles)

An end-to-end working retrace-and-intervene over the comms-wedge 4-step flow is estimated at **~4–6
autonomous execution cycles**, because the substrate (L1 models, L2 governance, the event stream, the
posture machine, the durable store) is reused rather than rebuilt (`01-research/06` §7,
`01-analysis/07` §6.3). The split: ledger wiring (S1) ~1 cycle; cascade core (S2+S3) ~1–2 cycles (higher
budget via the live feedback loop); determinism policy (S4) ~1 cycle; integration + the comms-wedge hot-path
call site + Tier-2 wiring tests ~1 cycle. Generalizing beyond the wedge to arbitrary multi-agent
objectives is *incremental* once L3 exists. This estimate excludes the L4 non-coder UI, which is the open-
ended frontier (its own plan).

### 8.3 What v1 deliberately excludes — implications + symmetric pros/cons

| Excluded from v1                                   | Pro of excluding                                                                              | Con of excluding (real)                                                                                          |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Branching / fork-and-compare timelines**         | Removes the single hardest non-coder UX concept (Git-like divergence) from v1 (§4.3)         | "Explore a what-if side-by-side" is deferred; users compare sequentially via revert. Immutable versions are the safety net, not branches. |
| **Cross-vertical generalization**                  | Lets the team prove the engine on a 4-step flow before betting on arbitrary multi-agent DAGs  | The horizontal moat (the engine reusable by any vertical) is *built* (framework-level, §7.3) but only *exercised* on comms in v1. |
| **Multi-replica distributed event bus**            | The in-memory `EventBus` is correct for single-process; avoids premature infra              | A multi-replica deployment needs a durable/distributed bus (`SQLTaskQueue` with `SKIP LOCKED` or Redis fan-out is the in-ecosystem path — §8 #6). A scaling cliff, not a v1 blocker. |
| **Automatic cascade execution without preview**    | Avoids a single root-edit triggering a large, surprising, expensive re-run                   | The user must confirm a cost-preview before a wide cascade commits (§8 #3); adds one gate to the rewind flow.    |
| **Version retention / compaction policy**          | v1 keeps every version forever (simplest correct behaviour)                                  | Storage grows without bound; content-addressing dedupes identical bytes but not version *count*. A retention policy is owed before scale (§8 #5). |

### 8.4 The highest-risk unknowns (flagged, not resolved — ranked by likelihood of sinking the feature)

Per `.claude/rules/spec-accuracy.md` and the analyst discipline, these are genuine uncertainties a spec /
redteam phase must resolve. The top two decide whether the feature is *usable*, not whether it can be
*built* — the engine is the tractable part; legibility-for-non-coders is the frontier
(`01-analysis/07` §8).

1. **Non-coder versioning UX (the dominant risk).** "Rewind, change, see only the affected parts redo,
   compare versions, revert" is an unsolved design problem for non-coders; Git-like concepts are hard even
   for experts. v1's linear-no-branching cut (§4.3) is the primary mitigation, but the residual UX risk is
   real and is where the product is most likely to fail. **Resolution path:** UX design + real non-coder
   user testing; treat as iterative discovery, not a one-shot build (`01-analysis/07` §8 #1). *This is the
   spine's named dominant M1 unknown.*
2. **Re-run vs replay vs branch as a user-facing choice.** The per-step "regenerate / keep recorded"
   decision (§4.2) may confuse non-coders; guessing the default wrong silently is the worst outcome. v1's
   reuse-recorded default + explicit-regenerate mitigates, but the choice itself is a conceptual burden.
   **Resolution path:** product decision + user testing (`01-research/06` §8, `01-analysis/07` §8 #2).
3. **Cascade cost explosion.** A change near the root of a wide DAG legitimately invalidates everything
   downstream. Content-hash skip bounds the *unnecessary* re-runs, but a root-prompt edit *correctly* re-runs
   everything. **Resolution path:** a cost-preview before committing a cascade, estimated from
   `ExecutionMetric` history (§7.2; `01-research/06` §8, `01-analysis/07` §8 #3).
4. **The span→ledger ingestion contract.** Spans are ephemeral; the ledger is durable. The recommendation
   is "ledger is source of truth, spans write into it" (§1.5) — but the clean ingestion contract (when a
   span becomes a permanent node, how partial/failed spans are handled) is unspecified.
   **Resolution path:** engine design (`01-research/06` §8).
5. **Storage growth / retention policy.** Every re-run is a new version forever. Content-addressing dedupes
   identical bytes but not version *count*. **Resolution path:** an operational retention/compaction policy
   (aegis's `compaction-checkpoint` is a precedent; Sequor has tiered retention by plan —
   `01-research/06` §8, `01-analysis/07` §8 #5).
6. **The live event bus is single-process.** PACT's `EventBus` is in-memory; multi-replica needs a
   durable/distributed bus. **Resolution path:** infrastructure, deferred per §8.3 (the `SQLTaskQueue` or
   Redis fan-out is the in-ecosystem path — `01-research/06` §8, `01-analysis/07` §8 #6).
7. **Where the cascade engine lives (framework vs app).** Framework-level placement (§7.3) affects reuse
   and the M-series moats and depends on the not-yet-GA durable-resume integration. **Resolution path:**
   confirm with framework specialists at design time — the runtime-ownership SPIKE the spine flags as
   determining whether M1 is buildable (`01-research/06` §3 gap 1, §8; `01-analysis/07` §8 #9).

### 8.5 The alternative considered and rejected

The alternative is to **build a bespoke provenance/versioning system from scratch** rather than reuse the
PACT/Kailash/aegis substrate. Rejected (`01-analysis/07` §7.4): it discards ~80% of working, tested code;
it would re-derive the content-addressing, the durable store, the version chain, and the dependency
edge-set that already ship; and it conflicts with Decision B (capability-first reuse of ecosystem DNA).
The only argument for it — "a clean-room design avoids PACT's facade-heaviness" — is better addressed by
enforcing the orphan-detection rules on the reused code (§6.1) than by rewriting it.

---

## 9. Source ledger

All claims above resolve to one of:

- **`briefs/01-vision.md`** §3e (posture, retrace-and-intervene, versioning), §3f (black-box boundary),
  §4 Decisions A/B.
- **`01-analysis/07-transparency-intervention-architecture.md`** — §2 (transparency contract), §3
  (provenance ledger data model + the six invariants), §5 (intervention + cascade + determinism), §6
  (reuse vs new, layer cake, comms wedge), §7 (recommendation + symmetric pros/cons + rejected
  alternative), §8 (the nine ranked unknowns).
- **`01-analysis/01-research/06-transparency-intervention-versioning.md`** — §0 (80/20 framing), §1
  (provenance entities + content-addressing), §2 (intervention semantics + branching), §3 (durable
  execution reuse + the determinism gap), §4 (decision surfacing), §5 (black-box boundary + OTel
  conventions), §6 (layer-cake synthesis + unifying skip insight), §7 (novel parts + the six invariants +
  the cycle estimate), §8 (risks).
- **`01-analysis/01-research/03-pact-governance.md`** — §5 (SupervisorOrchestrator / EventBridge /
  EnforcementMode SHADOW), §6 (the 17 DataFlow models — Run / Artifact / Decision / ExecutionMetric /
  Request.depends_on), §8 (the 80/15/5 reuse ratio, the facade-heaviness caution).
- **The strategic spine** — moats M1–M4, the runtime-ownership SPIKE, the "transparency makes depth
  legible" point, Decisions A and B, the Cowork threat (compete on substrate, not surface).
- **COC rules** — `recommendation-quality.md` (symmetric pros/cons), `communication.md` (plain language),
  `autonomous-execution.md` (effort in cycles + capacity-budget sharding), `tenant-isolation.md`,
  `orphan-detection.md` / `facade-manager-detection.md`, `spec-accuracy.md` (flag uncertainty).
