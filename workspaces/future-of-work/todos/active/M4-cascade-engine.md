# M4 — Retrace / Cascade Engine (C5, moat M1): The Headline, Net-New Build #2

> **What this milestone proves (plain language).** A non-technical person can rewind to an earlier
> step of a multi-step job, change something there, and have _only the affected downstream work_
> recompute — while every old result is kept as a version they can compare against and return to.
> This is the strongest thing the platform owns and the hardest thing to build.
>
> **Reduced-v1 scope, stated honestly (do NOT silently widen it).** v1 ships:
> **linear retrace only** (rewind along the single main timeline — no parallel branches);
> **reuse-recorded-output as the default** for every step the user did not touch, with an
> **explicit per-step "regenerate" opt-in** for the step being edited; and a **cost-preview hard
> gate** before any cascade commits. There is **NO user-facing branching in v1**. The reduced form
> still beats the field — no competitor productizes any non-coder versioned cascade — but it is
> _less_ differentiated than the full vision, so it must travel with honest messaging, not the
> strongest-possible claim. (roadmap §8.3; plan 03 §4.2–§4.3, §8.1.)
>
> **The legibility frontier (the thing that can fail even if the engine is perfect).** The engine is
> the tractable part. Whether a non-coder can read the trace, tell "which version is current" in
> seconds, and drive the rewind without it feeling like a developer's version-control graph — that is
> an _unsolved design problem_, and it is where this milestone is most likely to fail. Both of C5's
> falsifiers are checked separately below. (roadmap §8.2, §8.7; plan 03 §8.4 unknowns #1–#2.)
>
> **The three meanings of "rewind" the engine MUST keep separate** (plan 03 §4.1; roadmap §8.4):
> **Re-run** = the user changed an input → re-execute affected downstream; model steps may
> legitimately differ (correct, expected). **Replay** = show exactly what happened last time → reuse
> the recorded answer by fingerprint, no fresh model call (fully deterministic; proven in C1).
> **Branch** = try a different path without losing the original → **DEFERRED to a later form, NOT in
> v1.** Conflating these is the single biggest source of non-coder confusion.

---

## Dependency and sharding posture for this milestone

- **M0-9 (the C1 verdict — stable content-fingerprint + byte-exact single-step replay confirmed)
  gates this engine.** The cascade consumes C1's content-addressed step records + the
  deterministic replay path. If C1's single-step glass-box + replay is not landed, this milestone
  cannot start. (roadmap §8.1, §8.5; plan 03 §3.)
- **C5 is PAIRED with C3** (the non-coder self-service surface). C3's "last 20%" depth-death risk is
  only neutralized by this engine's transparency/rewind making gaps legible and fixable in-flight.
  C3 alone is a wizard; C3+C5 is a wizard whose gaps are visible. (roadmap §6.4.)
- **The engine MUST be sharded — this is mandatory, decided here at /todos time, not deferred to
  implement.** It is the ≥500-LOC load-bearing piece holding **all six ledger invariants** at once
  (immutability, tenant-isolation, determinism-boundary, cascade-minimality, posture-at-time,
  audit-completeness) — over the per-session capacity budget on the invariant axis alone. The four
  engine shards below are each one-invariant-focused. (roadmap §8.6–§8.7; plan 03 §6, §6.1;
  `autonomous-execution.md` § Per-Session Capacity Budget.)
- **The engine BUILD, the WIRE into the comms-wedge flow, and the timeline UI surface are SEPARATE
  todos.** The engine lives as a framework-level module over the data models + descendant-walk, NOT
  inside the Sequor app, so the horizontal capability is reusable and the wedge consumes it. The
  non-coder timeline/rewind/version UI is a separate surface shard (it lives in C3's surface layer,
  consuming this engine). Do NOT combine engine + UI in one shard. (roadmap §8.5, §8.7; plan 03 §7.3.)
- **The M1 content-addressed namespace is a NAMED cross-tenant leak vector — a hard gate.** Tenant
  isolation (every fingerprint, cache key, and graph query carries `tenant_id`) and immutability
  MUST be in EVERY shard's invariant list, not just the first. A later shard that adds a cache key
  without `tenant_id` re-opens the leak. (plan 03 §6 invariant #2, §6.1; `tenant-isolation.md`.)
- **Orphan-detection / facade-manager discipline applies.** The cascade engine is an `*Engine`-shaped
  class and MUST land with a production call site (the comms-wedge hot path) + a Tier-2 wiring test in
  the same change — never a facade with no caller. This is the exact Phase-5.11 failure those rules
  exist to prevent. (plan 03 §6.1; `orphan-detection.md`, `facade-manager-detection.md`.)

---

### M4-1 — Ledger ingestion contract: unify records into one content-addressed graph

- **Type:** BUILD
- **Implements:** specs/transparency-and-provenance.md §provenance-ledger (+ plan: 02-plans/03 §1, §1.5, §3.2; roadmap §8.5)
- **What:** Wire the live event stream + the work-tracking records + the durable store into one
  content-addressed provenance graph, where every Step and Output is identified by a fingerprint of
  its own content. Compute the Step/Output content hashes (a Step's identity = a hash of its inputs +
  its prompt/code reference + the fingerprints of the steps it depends on). The ledger is the source
  of truth; the live event stream writes into it.
- **Reuses → Builds:** existing work-tracking record models (Step / Output / Decision node kinds),
  the durable store, the OpenTelemetry GenAI recording conventions, and content-addressing that
  already ships for crash-recovery/idempotency → the unifying ledger wiring + the span→ledger
  ingestion contract (when a live span becomes a permanent node; how partial/failed spans are
  handled).
- **Invariants:** immutability (a node is never updated in place — a new version is a new row);
  tenant-isolation (every fingerprint and graph query carries `tenant_id` — the content-addressed
  namespace is the named cross-tenant leak vector, hard gate). (Determinism-boundary,
  cascade-minimality, posture-at-time, audit-completeness arrive in the shards that own them, but the
  two above are present in EVERY shard.)
- **Sizing:** ~1 cycle (mostly wiring of existing models; has a live feedback loop — each
  recorded node is testable against a fixture graph). + SHARD: this is the first of four
  invariant-focused engine shards.
- **Depends on:** M0-9 (C1 verdict — stable content-fingerprint + byte-exact single-step replay
  confirmed) — content-addressed step records + replay path must exist first.
- **Acceptance (confirm / falsify):** **Confirm:** identical inputs + identical upstream produce the
  _same_ Step fingerprint; a recorded node round-trips through the durable store; tenant A's
  fingerprints are never resolvable from tenant B's namespace. **Falsify:** the same inputs yield
  different fingerprints (so "only recompute what changed" can never be built — the C5 engine
  falsifier #1 substrate), OR any cache/graph key is constructible without a `tenant_id` dimension.
  Real-infra Tier-2 against a fixture DAG.

### M4-2 — Dirty-propagation over the dependency graph (descendant-walk + dirty-mark)

- **Type:** BUILD
- **Implements:** specs/intervention-and-versioning.md §cascade-engine (+ plan: 02-plans/03 §3.1 steps 2–3; roadmap §8.7 shard 1)
- **What:** When the user rewinds to a step and changes an input, create a new step (the old one
  untouched as a version), then walk _all descendants_ of the changed step over the dependency edge
  and mark each "potentially needs re-run." Produce the ordered dirty set in dependency order.
- **Reuses → Builds:** the descendant-walk that already exists over the dependency graph
  (cached topological order, cheap) + the existing dependency edge-set → the dirty-propagation pass
  (the half of the cascade that decides _what might_ need recompute).
- **Invariants:** cascade-minimality (the marking half — only genuine descendants are marked, in
  dependency order); immutability (the changed step appends a new node, never alters the old);
  tenant-isolation (every graph query carries `tenant_id` — hard gate).
- **Sizing:** ~1 cycle (load-bearing core, first half; live feedback loop against a fixture graph).
  - SHARD: one invariant-focused engine shard.
- **Depends on:** M4-1 (the content-addressed graph + edges must exist).
- **Acceptance (confirm / falsify):** **Confirm:** rewinding to a step marks exactly its descendants
  (no more, no fewer) in correct dependency order; unrelated branches are never marked. **Falsify:**
  the walk over-marks (marks unrelated steps, inflating the cascade) or under-marks (misses a genuine
  descendant, producing a stale downstream). Real-infra Tier-2 over the 4-step comms graph
  (Message → Classification → Retrieval → Response).

### M4-3 — Fingerprint-skip + cascade-minimality (the only-affected-downstream guarantee)

- **Type:** BUILD
- **Implements:** specs/intervention-and-versioning.md §cascade-engine (+ plan: 02-plans/03 §3.1 step 4; roadmap §8.7 shard 2)
- **What:** Re-run the dirty steps in dependency order. For each, recompute its inputs-fingerprint
  from its (possibly-unchanged) upstream outputs. **If the new fingerprint equals the recorded one,
  skip the step and reuse the cached output.** Only steps whose inputs _actually_ changed re-run; a
  step whose other inputs dominate may produce an identical result and **halt the cascade early** —
  the change does not propagate further.
- **Reuses → Builds:** content-addressed memoization (skip-and-reuse-if-fingerprint-matches) that
  already ships for crash-recovery, idempotency, and within-run skipping → generalizing its scope
  from "within one run" to "across runs, keyed on content fingerprint" — the genuinely-new core.
- **Invariants:** cascade-minimality (the skip half — a descendant with unchanged recomputed inputs
  MUST be skipped; this is the "only affected downstream" promise — violating it makes rewind slow
  and expensive); immutability; tenant-isolation (every fingerprint/cache key carries `tenant_id` —
  hard gate).
- **Sizing:** ~1–2 cycles (load-bearing core, second half; live feedback loop — each cascade is
  testable against a fixture graph, so higher per-session budget). + SHARD: one invariant-focused
  engine shard.
- **Depends on:** M4-2 (needs the ordered dirty set).
- **Acceptance (confirm / falsify):** **Confirm:** on the brief's worked example, changing one
  assumption in the _revenue_ branch re-runs the revenue downstream and the final report, while the
  _costs_ and _cash-flow_ branches are skipped because their fingerprints match. **Falsify (C5 engine
  falsifier #1):** the engine can't bound the cascade — steps whose inputs are unchanged still re-run,
  so a change near the root legitimately re-runs everything with no minimality. Real-infra Tier-2 over
  the 4-step comms graph.

### M4-4 — Version-on-rerun + audit-completeness of the intervention

- **Type:** BUILD
- **Implements:** specs/intervention-and-versioning.md §immutable-versioning (+ plan: 02-plans/03 §3.1 step 5, §5; roadmap §8.7 shard 3)
- **What:** Each re-run step's output is written as a _new version_ with a back-pointer to the prior
  version — nothing is overwritten. Revert is repointing to a prior version (lossless, because the
  data was never destroyed); compare-versions is a fingerprint diff that re-runs nothing. The
  intervention itself is recorded as an auditable event: _who_ rewound, _what_ they changed, _when_ —
  a new audit record, never a silent edit.
- **Reuses → Builds:** the existing version chain on outputs (`version` + parent-pointer already
  modeled) + the append-only audit record type → the version-on-rerun write path + the
  intervention-audit record + the revert/compare read paths.
- **Invariants:** immutability (every re-derivation appends; the original survives as a prior
  version); audit-completeness (the intervention is itself an auditable action); tenant-isolation
  (every version row and audit row carries `tenant_id`, indexed — so "show me everything tenant X
  did" is not a full table scan — hard gate).
- **Sizing:** ~1 cycle. + SHARD: one invariant-focused engine shard.
- **Depends on:** M4-3 (a re-run produces the output that gets versioned).
- **Acceptance (confirm / falsify):** **Confirm:** after a rewind, the original output survives as
  v1 and the corrected one is v2 with a back-pointer; revert to v1 restores it without re-running;
  the audit record names who/what/when. **Falsify:** a re-run overwrites the prior version (data
  loss), OR the intervention leaves no audit trail (audit-completeness broken). Real-infra Tier-2
  with read-back verification of every version write.

### M4-5 — Determinism handling: reuse-recorded default + explicit per-step regenerate + posture snapshot

- **Type:** BUILD
- **Implements:** specs/intervention-and-versioning.md §determinism-resolution (+ plan: 02-plans/03 §4.1–§4.2, §6 invariants #3, #5; roadmap §8.4)
- **What:** On a rewind, the engine **reuses the recorded output by fingerprint** for every step the
  user did NOT explicitly change, and only re-generates the steps the user DID change. It never
  assumes a model call replays identically. The per-step choice — _"re-run this with my edit (get a
  fresh answer)"_ vs _"keep the recorded output, only re-run what depended on it"_ — is surfaced as an
  explicit product decision, not a hidden default, because guessing wrong silently is the worst
  outcome. Each Step also snapshots the posture in force when it ran.
- **Reuses → Builds:** the deterministic replay-by-fingerprint path (from C1) + the posture machine
  (read-only) → the reuse-recorded-vs-regenerate policy layer + the per-step explicit-choice surface
  contract + the posture-at-time snapshot on each Step. Keeps the three meanings of rewind separate
  (Re-run / Replay / Branch-deferred).
- **Invariants:** determinism-boundary (LLM steps reuse the recorded output by content hash on
  retrace UNLESS the user explicitly forces regeneration); posture-at-time (every Step records the
  posture in force — so a retrace can show "this ran on its own" vs "a human approved this"); plus
  immutability + tenant-isolation in every shard.
- **Sizing:** ~1 cycle (live feedback loop with a recorded-output fixture). + SHARD: one
  invariant-focused engine shard. This is the determinism _policy_; M4-2/3 are the cascade _core_.
- **Depends on:** M4-1 (records carry the posture snapshot field), M4-3 (skip path is the
  reuse-recorded mechanism).
- **Acceptance (confirm / falsify):** **Confirm:** untouched steps reuse their recorded output with
  no fresh model call; the edited step gets an explicit "regenerate vs keep" choice; a re-run that
  _does_ regenerate a model step shows _what changed and why_ between versions rather than pretending
  the re-run was deterministic; each Step carries its posture snapshot. **Falsify:** the engine
  silently re-generates untouched steps (surprising the user with answers they did not ask for), OR
  the per-step choice is hidden so the user cannot tell whether they got a fresh answer or a recorded
  one. Real-infra Tier-2 with a recorded-output fixture.

### M4-6 — Cost-preview hard acceptance gate

- **Type:** BUILD
- **Implements:** specs/intervention-and-versioning.md §cost-preview (+ plan: 02-plans/03 §8.3, §8.4 unknown #3; roadmap §8.7 shard 4, §8.8)
- **What:** Before any cascade commits, show a plain-language cost-preview — _"this change will
  re-run N steps"_ — estimated from historical cost/latency, and require the user to confirm before a
  wide cascade runs. This is a **hard acceptance gate, not a nice-to-have**: a root-level edit can
  legitimately invalidate everything downstream, and a non-coder will not trust a rewind that can
  silently trigger a large, expensive, surprising re-run.
- **Reuses → Builds:** the historical cost/latency metric source (read for estimation) + the
  dirty-set + fingerprint-skip pass (to estimate which steps will actually re-run vs skip) → the
  cost-estimation + the confirm-before-commit gate in the rewind flow.
- **Invariants:** cascade-minimality (the preview must reflect the _minimal_ set — it counts only
  steps that will genuinely re-run after fingerprint-skip, not all descendants); audit-completeness
  (the user's confirm/cancel of the preview is itself recorded); tenant-isolation.
- **Sizing:** ~1 cycle. + SHARD: the fourth invariant-focused engine shard; gates the rewind flow.
- **Depends on:** M4-3 (the skip pass tells the preview which steps actually re-run), M4-2.
- **Acceptance (confirm / falsify):** **Confirm:** before a cascade, the preview names the number of
  steps that will re-run (post-skip, not all descendants); the cascade does NOT commit until the user
  confirms; cancelling leaves the timeline untouched. **Falsify (C5 engine falsifier #1, second
  half):** there is no comprehensible cost-preview — the count is wrong (counts all descendants, not
  the minimal set) or absent, so a non-coder cannot judge the cost before committing. Real-infra
  Tier-2 over the 4-step comms graph + a non-coder usability check that the preview is _legible_
  (plain count, not a technical estimate).

### M4-7 — Wire the cascade engine into the comms-wedge 4-step flow (production call site)

- **Type:** WIRE
- **Implements:** specs/intervention-and-versioning.md §cascade-engine (+ plan: 02-plans/03 §6.1, §8.1; roadmap §8.5, §8.7)
- **What:** Wire the framework-level cascade engine into the comms-wedge's hot path so that
  correcting a classification on the live 4-step flow (Message → Classification → Retrieval →
  Response) creates a new version and re-derives the downstream response through the engine — using
  the wedge's _existing_ "log a correction as a new audit row" discipline as the natural
  retrace-and-version primitive. This is the production call site that proves the engine is not an
  orphan.
- **Reuses → Builds:** the comms-wedge 4-step flow + its existing classification-correction
  discipline → the hot-path call into the engine (the framework module is consumed, not duplicated in
  the app).
- **Invariants:** orphan-detection (the engine MUST have a real hot-path call site in the same change
  as its Tier-2 wiring test — the M1 content-addressed namespace cross-tenant leak vector is enforced
  here too: the wedge's schema-per-tenant must carry through every engine call). All six ledger
  invariants hold on the wired path.
- **Sizing:** ~1 cycle (part of the ~4–6 cycle end-to-end estimate). Separate from the engine BUILD
  shards and from the UI surface shard.
- **Depends on:** M4-1 through M4-6 (the engine must exist), C4 (≥2-system reach is needed only for
  the full demo; the comms 4-step flow alone suffices for this wire).
- **Acceptance (confirm / falsify):** **Confirm:** a classification correction on the live comms flow
  creates v2 of the response, re-runs only the affected downstream, keeps v1, and is audited — proven
  by a Tier-2 wiring test that imports through the framework facade and asserts the externally
  observable effect (a new version row, a skipped unrelated step, an audit row). **Falsify:** the
  engine ships as a facade with no hot-path caller (the Phase-5.11 orphan pattern), OR the wedge
  re-implements cascade logic locally instead of calling the framework module. Real-infra Tier-2 +
  the orphan-detection protocol (surface scan → hot-path grep → Tier-2 grep).

### M4-8 — Non-coder timeline / rewind / version UI (separate surface shard)

- **Type:** BUILD
- **Implements:** specs/intervention-and-versioning.md §retrace-UX (+ plan: 02-plans/03 §4.3, §8.4 unknowns #1–#2; roadmap §8.2, §8.7)
- **What:** The non-coder-facing surface that lets a non-technical person rewind along the single
  main timeline, see a step's recorded inputs/tool-calls/result/output (the glass box), make the
  per-step regenerate-vs-keep choice, see the cost-preview, and view/compare/revert versions —
  rendered so they can answer "which version is current?" in seconds and read the history _without_
  it looking like a developer's version-control graph. **Linear only — no branch-and-compare surface
  in v1.** This is a SEPARATE surface shard living in C3's surface layer, consuming the engine; it is
  NOT combined with the engine BUILD.
- **Reuses → Builds:** the C3 self-service surface scaffold + the engine's read APIs (versions,
  diff, cost-preview, glass-box record) → the timeline/rewind/version UX. UX work is iterative;
  size by usability-walk milestones, not LOC.
- **Invariants:** non-coder legibility (the load-bearing UX invariant — "which version is current"
  answerable in seconds; history reads as plain, not git-graph); determinism-boundary surfaced
  honestly (the regenerate-vs-keep choice is visible, never hidden); tenant-isolation on every
  rendered record.
- **Sizing:** multiple cycles (open-ended UX frontier — this is the legibility bet). + SHARD:
  separate surface shard; do NOT fold into the engine.
- **Depends on:** M4-1 through M4-6 (engine read APIs), C3 (the surface scaffold it lives in).
- **Acceptance (confirm / falsify):** **Confirm:** in a non-coder usability walk _with receipts_
  (verbatim user actions + what they saw + their disposition), the user rewinds, edits, sees the
  cost-preview, picks regenerate-vs-keep, and tells "which version is current" within seconds.
  **Falsify (C5 falsifier #2 — the legibility bet):** even with a working engine, a non-coder cannot
  answer "which version is current?" in seconds, or the branching/version history reads like a
  developer's git graph. Both C5 falsifiers MUST be checked: this shard owns falsifier #2
  (legibility); M4-3/M4-6 own falsifier #1 (engine can't bound the cascade / no comprehensible
  cost-preview). Non-coder usability walk per `user-flow-validation.md` (receipts mandatory).
  **Honest note for the founder:** if this legibility falsifier fires and cannot be resolved, the
  reduced-form scope (§8.3) and the comms-wedge proving ground exist to surface it _early_, on a
  4-step graph, before it is the headline — but it is a real credibility risk, not a smoothed-over one.

### M4-9 — Version retention / compaction policy (storage grows unbounded — its own todo)

- **Type:** BUILD
- **Implements:** specs/intervention-and-versioning.md §irreversibility-and-retention (+ plan: 02-plans/03 §8.3, §8.4 unknown #5; roadmap §8.8)
- **What:** A retention/compaction policy for the immutable version history. v1 keeps every version
  forever (simplest correct behaviour), but immutable versioning grows storage _without bound_ —
  content-addressing dedupes identical bytes but NOT version _count_. This todo defines and builds
  the operational retention/compaction policy (tiered by plan) before scale, so it is designed in,
  not discovered in production.
- **Reuses → Builds:** content-addressed dedup (identical-byte sharing already free) + tiered
  retention precedents → the version-count retention/compaction policy + the compaction-checkpoint
  mechanism (which versions are kept, which are compacted, on what cadence, per plan tier).
- **Invariants:** immutability (compaction MUST preserve the version chain's integrity and never
  destroy a version still under retention); tenant-isolation (retention is per-tenant; one tenant's
  compaction never touches another's versions); audit-completeness (a compaction event is itself
  recorded).
- **Sizing:** ~1 cycle. Its own todo — explicitly NOT folded into the engine shards (the engine's
  correctness must not depend on a retention policy, and retention must not be an afterthought).
- **Depends on:** M4-4 (the version chain must exist to have something to retain/compact).
- **Acceptance (confirm / falsify):** **Confirm:** with the policy active, version _count_ growth is
  bounded per the plan tier; a compaction preserves the chain (revert and compare still work for
  retained versions); a compaction event is audited and tenant-scoped. **Falsify:** storage grows
  unbounded under the policy (count not actually bounded), OR compaction breaks a revert/compare for
  a version that should still be retained, OR a compaction crosses a tenant boundary. Real-infra
  Tier-2 with a multi-version, multi-tenant fixture.

---

## Milestone-level acceptance (both C5 falsifiers MUST be checked)

The cascade engine is **proven** only when, on the comms-wedge 4-step graph, real-infra Tier-2 tests
AND a non-coder usability walk (with receipts) jointly show:

1. **Engine bounds the cascade with a comprehensible cost-preview** (falsifier #1 NOT triggered —
   M4-3 + M4-6): a revenue-branch edit re-runs only the revenue downstream + final report; costs and
   cash-flow branches skip on fingerprint match; the pre-commit preview names the minimal re-run count.
2. **A non-coder can read the trace and the versions** (falsifier #2 — the legibility bet — NOT
   triggered — M4-8): they tell "which version is current" in seconds and the history does not read
   like a git graph.

If falsifier #1 fires, the engine needs rework. If falsifier #2 fires, the platform leads its story
with a capability it cannot fully ship — a credibility risk the reduced-form (linear, no branching,
reuse-recorded default, cost-preview hard gate) and the small-graph proving ground exist to surface
early. Report both outcomes honestly to the founder; do not paper over the legibility frontier.
