# 04 — EATP Trust Plane & the Graduated Trust Posture (L1–L5)

> Research for the Agentic Work Platform analysis (`/analyze`, 2026-06-05).
> Addresses brief objectives **3e** (posture / HITL / HOTL / permission envelopes), **3f** (every step traced + interveneable), and the **CRITICAL SYNTHESIS**: map the EATP + posture machinery onto a per-objective, per-step, user-selectable posture UX.
>
> All claims are grounded in files actually read; paths are cited inline. Where a claim could not be verified, it is flagged **[UNVERIFIED]**.

---

## 0. TL;DR for the platform architect

There are **three independent realizations** of the same L1–L5 graduated-autonomy idea already built across the ecosystem, plus a fourth (Claude Code's own permission modes) that implements ~5–15% of it:

| Realization                                                                                           | What it governs                                                                                                                                                                  | Where it runs                                       | Reusability for the platform                                                                                                                            |
| ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **EATP SDK** (`kailash.trust.posture`)                                                                | A library: `TrustPosture` enum, `PostureStateMachine`, `PostureStore`, `BudgetTracker` — generic, agent-keyed                                                                    | Python runtime, any app                             | **HIGH** — the canonical engine; per-agent/per-objective keyed; SQLite-persisted; signed transitions                                                    |
| **PACT platform** (`pact_platform`)                                                                   | A _product_: posture → action-level verdict (BLOCK / HELD / auto-approve), `ApprovalBridge` → human approval queue, objectives/sessions/decisions DataFlow models, web dashboard | FastAPI + DataFlow + Next.js                        | **VERY HIGH** — this is closest to the brief's "surface decisions, intervene, posture beforehand" UX, already wired end-to-end                          |
| **COC trust-posture** (`rules/trust-posture.md` + `skills/32-trust-posture/` + `commands/posture.md`) | The _coding agent's own_ autonomy in a repo — per-repo posture, violation-driven downgrade, challenge-nonce upgrade                                                              | Claude Code hooks + `.claude/learning/posture.json` | **MEDIUM** — the discipline/UX patterns transfer; but it is repo-scoped and coding-agent-facing, not per-task end-user-facing (this IS the central gap) |
| **Aegis anchors** (`proj-*/anchors/anc-posture-*.json`)                                               | A _verifiable_ posture state machine — hash-chained, signed posture-transition anchors                                                                                           | Filesystem, per-project                             | **HIGH** — the cryptographic "verifiable state machine with anchors" the brief's 3f wants                                                               |

**The single most important finding:** PACT's `posture_enforcer.py` already maps the canonical L1–L5 ladder to per-action runtime verdicts, and `ApprovalBridge` already routes HELD actions into a human approval queue surfaced on a dashboard. That is **80% of the brief's "choose a posture beforehand, see agent decisions surfaced, intervene"** requirement, implemented. The platform's job is to (a) re-key posture from _agent/repo_ to _objective + step_, (b) replace PACT's keyword-based action classifier with an LLM-first classifier (Sequor's `agent-reasoning.md` forbids keyword routing), and (c) build the end-user-facing surfacing UX on top of the existing approval-queue + anchor primitives.

---

## 1. The canonical L1–L5 ladder (define each level precisely)

There are **two numbering conventions** in the ecosystem and they are **inverted relative to each other**. This is a documented, recurring trap (see §1.3). State the platform's chosen convention explicitly and grep-pin it.

### 1.1 EATP SDK canonical (autonomy_level: 1 = least, 5 = most)

Source: `.claude/skills/26-eatp-reference/eatp-trust-posture-canonical.md`, `eatp-posture-stores.md`, and the live source `kailash-py/src/kailash/trust/posture/postures.py`.

| `autonomy_level` | Canonical enum                            | Wire value       | Human role (from `co-reference/eatp-spec.md:40-46`)                                                               |
| ---------------- | ----------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| **5**            | `AUTONOMOUS` (alias `DELEGATED`)          | `"autonomous"`   | Full autonomy; **remote monitoring** only                                                                         |
| **4**            | `DELEGATING` (alias `CONTINUOUS_INSIGHT`) | `"delegating"`   | Agent executes, **human monitors in real-time**                                                                   |
| **3**            | `SUPERVISED` (alias `SHARED_PLANNING`)    | `"supervised"`   | Agent proposes actions, **human approves each one** (note: the SDK's `SUPERVISED` ≈ the spec's "Shared Planning") |
| **2**            | `TOOL` (alias `SUPERVISED` in spec)       | `"tool"`         | Human and agent **co-plan**; agent executes approved plans                                                        |
| **1**            | `PSEUDO` (alias `PSEUDO_AGENT`)           | `"pseudo_agent"` | Agent is **interface only**; human performs all reasoning                                                         |

Key SDK facts (from `eatp-posture-stores.md` + `postures.py:459-605`):

- `TrustPosture` is a `str`-backed `Enum` with an `autonomy_level` **property** (not a separate map). Supports ordering: `TrustPosture.SUPERVISED < TrustPosture.DELEGATED == True`.
- Backward-compat **aliases** exist (`DELEGATED→AUTONOMOUS`, `CONTINUOUS_INSIGHT→DELEGATING`, `SHARED_PLANNING→SUPERVISED`, `PSEUDO_AGENT→PSEUDO`) for deserializing older records. New code uses canonical names.
- `PostureStateMachine` **default is `TrustPosture.TOOL`** (autonomy_level=2) per CARE spec RT-17 — "tool agents start supervised; the agent proposes, a human approves." (`postures.py:483`, `eatp-posture-stores.md:174`.)
- `can_upgrade_to(target)` = `target.autonomy_level > self.autonomy_level`; `can_downgrade_to` is the mirror.

### 1.2 COC repo-posture ladder (L1 = least, L5 = most) — INVERTED LABELS

Source: `.claude/rules/trust-posture.md:25-33` (identical byte-for-byte in `loom`, `aegis`, and `Sequor`). This ladder names the levels `L1..L5` with `L5_DELEGATED` at the top:

| Level  | Name                    | Agent CAN do unilaterally                                                     | Requires human gate                                                          |
| ------ | ----------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **L5** | `L5_DELEGATED`          | Plan + implement + commit + open PR; parallel worktree agents; full `/codify` | Cross-repo writes; release tags; destructive ops                             |
| **L4** | `L4_CONTINUOUS_INSIGHT` | L5 + mandatory journal per shard + `/redteam` Round 1 before merge            | Posture upgrade; multi-shard releases                                        |
| **L3** | `L3_SHARED_PLANNING`    | Edit + run tests; one shard at a time                                         | `/todos` plan approval before `/implement`; PR creation; commits to `feat/*` |
| **L2** | `L2_SUPERVISED`         | Read; propose diffs; run linters                                              | Every Edit/Write; every commit; every Bash beyond read-only                  |
| **L1** | `L1_PSEUDO_AGENT`       | Propose plans + diffs in chat                                                 | Everything that touches the working tree                                     |

**Note the label collision:** the COC `L3_SHARED_PLANNING` is _higher_ than `L2_SUPERVISED`, but the EATP SDK `SUPERVISED` (autonomy 3) is _higher_ than `TOOL` (autonomy 2). The COC ladder borrows the EATP _names_ but re-numbers and re-orders them. The unifying invariant in both: **autonomy increases with the number; downgrades are automatic, upgrades are human-gated.**

### 1.3 The aegis 4-level production naming — a THIRD convention

Source: `aegis/proj-*/anchors/anc-posture-*.json` `record_id` fields (read directly). The aegis commercial implementation's _anchored transitions_ use yet another vocabulary:

```
posture-Supervised-to-Restricted   (downgrade)
posture-Restricted-to-Supervised   (upgrade)
posture-Supervised-to-Autonomous   (upgrade)
posture-Autonomous-to-Full         (upgrade)
```

So aegis runs a `Restricted → Supervised → Autonomous → Full` ladder. This maps onto the canonical 5 approximately as `Restricted≈L2/TOOL`, `Supervised≈L3`, `Autonomous≈L4`, `Full≈L5` — but the platform should NOT assume a clean mapping; aegis is a separate fork (`aegis/.claude/rules/aegis-fork-relationship.md` exists per the brief). **[UNVERIFIED]** the exact aegis level semantics — only the transition record_ids were read, not the aegis enum definition.

### 1.4 Mapping the brief's numbering to the canonical ladder — MISMATCH FLAGGED

The brief (`briefs/01-vision.md:30-32`) names **only three** levels, top-numbered, and they do **not** line up cleanly with either canonical ladder:

| Brief level         | Brief description                                    | Closest canonical match                                                                                                          | Mismatch                                                                                                                                                                                                                                                                                                                      |
| ------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L5 Autonomous**   | "agent goes ahead"                                   | EATP `AUTONOMOUS` (5) / COC `L5_DELEGATED`                                                                                       | ✓ clean                                                                                                                                                                                                                                                                                                                       |
| **L4 Supervised**   | "agent asks for **one** permission before executing" | EATP `DELEGATING` (4) / COC `L4_CONTINUOUS_INSIGHT`                                                                              | **Name clash** — the brief calls L4 "Supervised", but in BOTH canonical ladders "Supervised" is a _lower_ level (autonomy 2–3) where the human approves _every_ action, not "one permission". The brief's L4 ≈ canonical "one approval gate before the run" which is closer to CONTINUOUS_INSIGHT / a single HELD checkpoint. |
| **L3 Step-by-step** | "agent pauses at each step"                          | EATP `SUPERVISED` (3) / COC `L3_SHARED_PLANNING`, behaviourally closer to EATP `TOOL`/PACT `SUPERVISED` ("HELD on every action") | **Behaviour clash** — "pauses at each step" = HELD-on-every-consequential-action, which PACT implements at `SUPERVISED` (its lowest non-blocking level), not at a mid-tier "shared planning" level.                                                                                                                           |

**Recommendation (resolve at spec time):** Adopt the **EATP SDK canonical enum as the source of truth** (it is the shipped, persisted, signed primitive) and present a **plain-language 3-button UX** mapped onto it, accepting that the platform shows fewer buttons than the engine has states:

| Brief button (user-facing)                  | Engine posture (canonical)     | Per-step behaviour                                                      |
| ------------------------------------------- | ------------------------------ | ----------------------------------------------------------------------- |
| **Autonomous** ("go ahead")                 | `AUTONOMOUS` (5)               | auto-approve within envelope; out-of-envelope BLOCKED                   |
| **One check** ("ask once before executing") | `DELEGATING` (4)               | auto-approve within envelope; **one** HELD at the plan→execute boundary |
| **Step-by-step** ("pause at each step")     | `SUPERVISED` (3) or `TOOL` (2) | every consequential action HELD for approval                            |

`PSEUDO` (1) and the BLOCK-everything floor remain available as the **system-imposed downgrade target** when violations accrue (not a user button). The brief's numbering is a _presentation_ concern; the engine keeps all five. **Do not ship the brief's L3/L4/L5 labels as the enum** — they will collide with the canonical "Supervised" semantics and confuse every reader who knows EATP.

---

## 2. The EATP TrustPlane at runtime — what it governs

EATP = **Enterprise Agent Trust Protocol** (`co-reference/eatp-spec.md:8`). Core insight: **trust establishment (human judgment, once) is separate from trust verification (machine speed, continuously).**

### 2.1 The five elements (Trust Lineage Chain)

From `co-reference/eatp-spec.md:12-27`:

1. **Genesis Record** — organizational root of trust; a human executive cryptographically commits accountability. _No AI creates its own genesis._
2. **Delegation Record** — authority transfer with **constraint tightening** (delegations can only _reduce_ authority — "$50K manager → $10K agent, never $75K").
3. **Constraint Envelope** — multi-dimensional operating boundaries: **Financial / Operational / Temporal / Data Access / Communication** (this is the brief's "permission envelope").
4. **Capability Attestation** — signed declaration of authorized capabilities; prevents capability drift.
5. **Audit Anchor** — tamper-evident execution record; each anchor hashes the previous (the hash-chain the aegis anchors implement, §5).

### 2.2 The verification gradient (the runtime decision)

From `eatp-spec.md:30-36` and the SDK `kailash.trust.enforce.Verdict` enum (`eatp-sdk-api-reference.md:262-275`):

| Verdict         | Meaning                    | Action                                                  |
| --------------- | -------------------------- | ------------------------------------------------------- |
| `AUTO_APPROVED` | within all constraints     | execute and log                                         |
| `FLAGGED`       | near a constraint boundary | execute and highlight for review                        |
| `HELD`          | soft limit exceeded        | **queue for human approval** (the intervention surface) |
| `BLOCKED`       | hard limit violated        | reject with explanation                                 |

The four EATP operations (`eatp-spec.md:50-55`): **ESTABLISH** (create identity + initial trust) → **DELEGATE** (transfer authority with constraints) → **VERIFY** (validate chain + permissions, returns a `Verdict`) → **AUDIT** (record + trace). `TrustOperations.verify()` (`eatp-sdk-api-reference.md:110-117`) supports three `VerificationLevel`s — `QUICK` (~1ms hash+expiry), `STANDARD` (~5ms capability+constraints), `FULL` (~50ms signature verification).

**Critical honesty caveat (cite in any user-facing trust claim):** `eatp-spec.md:61-66` — **EATP provides traceability, not accountability.** Traceability = trace any AI action back to human authority (EATP delivers this). Accountability = humans understand and bear consequences (no protocol delivers this). This is exactly the brief's 3f framing: _"the only thing not transparent is how the model thinks — but input and output are transparent."_ The platform can promise traceability; it must NOT over-promise accountability.

### 2.3 BudgetTracker — cost/turn ceilings (the financial envelope at runtime)

Source: `eatp-budget-tracking.md`, `kailash/trust/constraints/budget_tracker.py:289`.

- **Integer microdollars** (1 USD = 1,000,000 µ$) — no floating-point drift; threshold checks are pure integer arithmetic.
- **Two-phase reserve/record**: `reserve(est)` (fail-closed — returns `False` if insufficient) → do work → `record(reserved, actual)`. The "safe direction" invariant: between the two atomic ops, `remaining()` briefly _over_-reports — may briefly allow a reservation that would've been denied, but **never denies one that should be allowed**.
- **Threshold callbacks**: `threshold_80` / `threshold_95` / `exhausted` fire at most once each; `on_record()` fires on every record (for arbitrary % checks — explicitly noted as the "posture-budget integration" hook).
- **`BudgetExhaustedError`** (subclass of `ConstraintViolationError`) raised on exhaustion (`eatp-trust-plane-enterprise.md:48-56`).
- **Crash-safe persistence** via `SQLiteBudgetStore` (WAL mode, per-thread connections, 0o600, parameterized SQL, `tracker_id` validated `^[a-zA-Z0-9_-]+$`, transaction log capped at 10k).

For the platform: a per-objective `BudgetTracker(tracker_id="obj-<id>")` gives **cost-per-objective ceilings** with 80/95/exhausted alerts surfaced to the user. "Cost per turn" maps to `max_cost_per_action`; "session/objective budget" to `max_cost_per_session` (PACT exposes both — `eatp-trust-plane-enterprise.md:14-20`). The `budget_status` dict (`session_cost / remaining / utilization`) is a ready-made progress widget.

### 2.4 PostureStore — persisted posture state

Source: `eatp-posture-stores.md`, `kailash/trust/posture/posture_store.py`, `postures.py:426-456`.

- `PostureStore` is a `@runtime_checkable` **Protocol** with 4 methods: `get_posture(agent_id)` (raises `KeyError` if unregistered → state machine uses default), `set_posture`, `get_history(agent_id, limit)`, `record_transition(result)`.
- `SQLitePostureStore` — two tables: `postures(agent_id PK, posture, updated_at)` and `transitions(id, agent_id, from_posture, to_posture, success, timestamp, metadata, transition_type)`. The `transition_type` column (added RT-06, with auto-migration) **preserves `EMERGENCY_DOWNGRADE`** distinct from a plain `DOWNGRADE` across round-trips — important for forensics.
- `PostureTransition` enum: `UPGRADE / DOWNGRADE / MAINTAIN / EMERGENCY_DOWNGRADE`. `emergency_downgrade()` bypasses all guards and goes directly to `PSEUDO_AGENT` (`eatp-posture-stores.md:271-281`) — the "downgrade instantly if conditions change" mechanism.
- `PostureEvidence` (observation_count, success_rate∈[0,1], time_at_current_posture_hours, anomaly_count) + `PostureEvaluationResult` (decision ∈ {approved, denied, deferred}, rationale, suggested_posture) — the structured evidence + decision shapes for an upgrade evaluator. NaN/Inf rejected (constraint-bypass defense).
- `TransitionGuard` — pluggable checks (`check_fn`, `applies_to=[UPGRADE]`, `reason_on_failure`). The **default guard** requires `requester_id` on every upgrade (`postures.py:510-518`) — the structural "agent cannot self-promote" enforcement.

**This is the per-agent (or per-objective) keyed state machine the platform needs.** `agent_id` is the only key; re-key it to `objective_id` (or `objective_id:step_id`) and the entire persistence + history + guard machinery is reusable as-is.

---

## 3. HITL vs HOTL — precise definitions and how posture selects between them

The brief's 3e asks for HITL and HOTL. The ecosystem defines them as **the two ends of the posture ladder**, not as separate mechanisms:

| Term                         | Definition (grounded)                                                                                                                                                      | Which postures                                                                                                                              | Source                                                                                                              |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **HITL** (human-in-the-loop) | The human is a **blocking node inside the execution path** — the agent cannot proceed past an action without the human.                                                    | `PSEUDO` (1, "agent is interface only, human performs all reasoning"), `TOOL`/`SUPERVISED` (2–3, "agent proposes, human approves each one") | `co-reference/eatp-spec.md:40-44`; PACT `posture_enforcer.py:7-9` ("PSEUDO_AGENT: block ALL; SUPERVISED: HELD ALL") |
| **HOTL** (human-on-the-loop) | The human is a **monitor outside the execution path** — the agent proceeds; the human observes (real-time or remote) and can intervene/abort, but does not gate each step. | `DELEGATING`/`CONTINUOUS_INSIGHT` (4, "agent executes, human monitors in real-time"), `AUTONOMOUS`/`DELEGATED` (5, "remote monitoring")     | `co-reference/eatp-spec.md:45-46`; `rules/autonomous-execution.md` ("Human-on-the-Loop, not in-the-loop")           |

**How posture selects between them — the runtime mechanism is PACT's `posture_enforcer.py` (read directly):**

```
PSEUDO_AGENT       : Block ALL actions before any LLM call           → HITL (hard)
SUPERVISED         : Place ALL actions in HELD queue                 → HITL (every action)
SHARED_PLANNING    : Planning auto-approves; consequential HELD      → HITL for consequential only
CONTINUOUS_INSIGHT : within-envelope auto-approve; boundary HELD     → HOTL + checkpoint
DELEGATED          : within-envelope auto-approve; out-of-envelope BLOCKED (not HELD) → HOTL (full)
```

The selection is **mechanical**: the posture level _is_ the choice of HITL-vs-HOTL. The transition point is between `SHARED_PLANNING` (HITL on consequential actions) and `CONTINUOUS_INSIGHT` (HOTL with a boundary checkpoint). The brief's three buttons sit exactly across this seam:

- "Step-by-step" / "pause at each step" → `SUPERVISED` → **HITL**
- "One check" / "ask once before executing" → `CONTINUOUS_INSIGHT` (the single boundary HELD) → **HOTL + one gate**
- "Autonomous" / "go ahead" → `DELEGATED` → **HOTL (remote)**

The Mirror Thesis (`rules/trust-posture.md:21`) governs the _direction_ of movement: **humans are the structural gate for upgrade (HITL→HOTL); the system is the structural gate for downgrade (HOTL→HITL, instant on violation).**

**⚠ Reuse caveat — PACT's classifier is keyword-based and violates Sequor's `agent-reasoning.md`.** `posture_enforcer.py` decides "consequential vs planning" by matching action strings against `_CONSEQUENTIAL_KEYWORDS` (`write/send/deploy/delete/commit/...`) and `_PLANNING_KEYWORDS` (`analyze/draft/review/...`). Sequor's **Absolute Directive 6 / `agent-reasoning.md`** mandates _LLM-first_ reasoning: "no if-else routing, no keyword matching, no regex classification in agent decision paths." The platform MUST replace this classifier with an LLM-judged consequentiality assessment (the LLM IS the classifier), keeping PACT's _verdict_ machinery (HELD/BLOCK/auto-approve) but not its _keyword_ decision path. This is a small, well-scoped rewrite, not a re-architecture.

---

## 4. How posture is set, upgraded, overridden, and recorded (the verifiable state machine)

### 4.1 Set / default

- EATP SDK default: `TrustPosture.TOOL` (autonomy 2 — supervised) per CARE RT-17 (`postures.py:483`). PACT default: `SUPERVISED` (`eatp-posture-stores.md:91,174`).
- COC repo default: **fresh repo (no `posture.json` + no `.initialized`) → `L5_DELEGATED`** (`rules/trust-posture.md:53`). This is a deliberate inversion of the SDK default: _coding agents_ in a trusted operator's repo start at full trust; _generic agents_ in an enterprise start supervised. The platform must pick a default per context — for an enterprise end-user platform the SDK/PACT "start SUPERVISED" default is the safer base.

### 4.2 Downgrade (automatic, system-gated)

`rules/trust-posture.md:63-84` — **cumulative** (3× same-rule in 30d → drop 1; 5× total in 30d → drop 1) and **emergency** (instant, by 1 posture or to L1 for critical). Emergency triggers include `regression_within_grace`, `time_pressure_procedure_drop`, `streetlight_selection`, `deferral_without_value_anchor`, `self_referential_codify_without_redteam`, `governed_throughput_bypass`, `unbacked_author_claim`, and **critical → L1** (destructive op without confirm, secret leak, cross-repo write outside scope, corrupt-state event). EATP's `emergency_downgrade()` jumps straight to `PSEUDO_AGENT`.

### 4.3 Upgrade (human-gated, challenge-nonce paste-back)

The brief specifically asks about the challenge-nonce. Source: `commands/posture.md:47-77` + `rules/trust-posture.md:86-93`.

**Four upgrade requirements (all required):** ≥7 days at current posture (`time_at_current_posture_hours ≥ 168`); 0 violations of the triggering rule class; ≥1 demonstrated proactive correction (logged positive observation); human approval via `/posture upgrade`.

**The challenge-nonce two-step flow** (`commands/posture.md:62-77`):

1. User runs `/posture upgrade --to L5_DELEGATED`. Command verifies the four requirements, writes a random nonce to `.claude/learning/.posture-upgrade-nonce` (mode 0600, hook-readable only), and prints: _"To confirm upgrade, paste this nonce in your next message: `<NONCE>`."_
2. User **pastes the nonce as the next message** AND runs `/posture upgrade --to ... --ack NONCE`. The command reads the nonce file, validates the user's _prior turn_ contained the nonce literal (verified against the conversation transcript the harness exposes), then appends an `EARNED` transition with `approved_by: human` and clears the nonce.

**Why the paste-back:** `rules/trust-posture.md:93` — "human gate alone is forgeable (agent invokes the slash command itself)." The nonce forces a _fresh human keystroke_ into the transcript that the agent cannot synthesize. In the multi-operator variant (`loom`), upgrade is _additionally_ gated by `operator-gate.js` 4-eyes: a signed `gate-approval` from a **distinct `person_id`** owner/senior whose bound GitHub login differs from the requester's; `host_role: ci` never eligible.

### 4.4 Override (false-positive recovery / bootstrap / emergency restore)

`/posture override --to LEVEL --reason "..."` — same nonce + 4-eyes gate as upgrade, but bypasses the time/violation requirements. Records `type: OVERRIDE, approved_by: human`. Used for wrongful-downgrade recovery, mid-cycle bootstrap (set L4 directly without earning L5), and post-fail-closed restoration (`commands/posture.md:79-92`).

### 4.5 Recorded as a verifiable state machine with anchors

Two layers of recording exist; the platform should use **both**:

**(a) The posture.json state file** (`skills/32-trust-posture/posture-spec.md`): `posture`, `since`, append-only `transition_history[]` (each `{from, to, type, reason, ts, approved_by}` with `transition_history[i].from === transition_history[i-1].to` chain-consistency enforced by `state-io.js`), `pending_verification[]`, `violation_window_30d{}`, `_initialized`. Direct edits BLOCKED by `settings.json::permissions.deny` — hooks are the only legitimate writers (`rules/trust-posture.md:140-142`).

**(b) The aegis cryptographic anchors** (`proj-*/anchors/anc-posture-*.json`, read directly) — this is the brief's "verifiable state machine with anchors":

```json
{
  "anchor_id": "anc-posture-8838c0a29548",
  "anchor_type": "posture_transition",
  "parent_anchor_id": "anc-posture-f490b9f6a0e6",   ← hash-chain back-pointer
  "record_id": "posture-Autonomous-to-Full",
  "record_hash": "8838c0a29548...407a",              ← SHA-256 of the record
  "signature": "b3b1e7d1...130b",                    ← Ed25519 detached signature
  "created_at": "2026-03-16T16:47:51.536884Z"
}
```

Each anchor names its `parent_anchor_id`, hashes the transition record, and signs it. This is EATP element #5 (Audit Anchor — "each anchor hashes the previous; modifying any record invalidates the chain forward", `eatp-spec.md:27`) realized as a per-transition file. The chain is the tamper-evident, replayable history the brief's 3f ("every activity and output is traced") requires. EATP's signing primitives (`generate_keypair`, `sign`, `verify_signature` — Ed25519, `eatp-sdk-api-reference.md:213-240`) produce these.

---

## 5. Relationship to the autonomous-execution model (HOTL, structural vs execution gates)

The brief explicitly ties posture to the autonomous-execution model. Source: `rules/autonomous-execution.md`.

- **The operating-envelope framing:** "Human defines the operating envelope. AI executes within it. **Human-on-the-Loop, not in-the-loop.**" This is the _default_ posture stance of the whole COC system — it assumes `DELEGATED`/`CONTINUOUS_INSIGHT` (HOTL) and treats HITL as the exception triggered by lower postures.
- **Structural vs execution gates** (`autonomous-execution.md` § Structural vs Execution Gates) — the platform's two gate classes:
  - **Structural gates (human required):** plan approval (`/todos`), release authorization (`/release`), envelope changes. These are the points where even a HOTL human _must_ act.
  - **Execution gates (autonomous convergence):** analysis quality (`/analyze`), implementation correctness (`/implement`), validation rigor (`/redteam`), knowledge capture (`/codify`). Human **observes but does NOT block.**
- The mapping to posture: at high posture (HOTL), only **structural gates** stop the agent; **execution gates** auto-converge. At low posture (HITL), execution gates also become blocking. The brief's "choose a posture beforehand per objective" is exactly _choosing which gate class is blocking for this objective._

This gives the platform a clean two-axis model: **posture (per objective)** selects HITL-vs-HOTL → which determines **which gates block**. The user's posture button is, mechanically, a choice over the gate set.

---

## 6. CRITICAL SYNTHESIS — mapping the machinery onto per-objective, per-step, user-selectable posture

The brief's worked example (`briefs/01-vision.md:29-33`): _user says "I want 3Q financial report" → agent decides to spin up 3 agents → these decisions are surfaced on screen, recorded, and the user chose a posture beforehand (L5/L4/L3); the user can retrace any previous step and intervene; downstream outputs change, old outputs are versioned._

### 6.1 What's reusable today (the 80%)

| Brief requirement                                                  | Reusable asset                                                                                                                                                                               | Path                                                                                                                       |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| "choose a posture beforehand"                                      | `PostureStateMachine` + `PostureStore`, re-keyed `agent_id`→`objective_id`                                                                                                                   | `kailash/trust/posture/postures.py`, `posture_store.py`                                                                    |
| "agent asks for one permission / pauses each step"                 | `posture_enforcer.py` → per-action verdict (BLOCK/HELD/auto-approve) per level                                                                                                               | `pact_platform/use/execution/posture_enforcer.py`                                                                          |
| "decisions surfaced on screen, user can intervene"                 | `ApprovalBridge` (HELD verdict → `AgenticDecision` row → approval queue → dashboard `approve()`/`reject()`)                                                                                  | `pact_platform/engine/approval_bridge.py`, `apps/web/app/objectives`, `routers/decisions.py`, `services/approval_queue.py` |
| "every activity recorded / verifiable"                             | Audit Anchor hash-chain (signed posture-transition anchors) + EATP `audit()`                                                                                                                 | `aegis/proj-*/anchors/anc-posture-*.json`, `kailash.trust.audit`                                                           |
| "cost/turn ceilings"                                               | `BudgetTracker` with 80/95/exhausted callbacks, per-objective `tracker_id`                                                                                                                   | `kailash/trust/constraints/budget_tracker.py`                                                                              |
| objectives / sessions / decisions / reviews as first-class records | PACT 11 DataFlow models = 121 auto-nodes (`AgenticObjective`, `AgenticWorkSession`, `AgenticDecision`, `AgenticReviewDecision`, `AgenticArtifact`, `ApprovalRecord`, `ExecutionMetric`, ...) | `pact_platform/models/__init__.py:34-50`                                                                                   |
| posture → audit depth scaling                                      | `/redteam` posture-scaled rounds; emergency-bypass for incidents                                                                                                                             | `skills/32-trust-posture/redteam-integration.md`, `engine/emergency_bypass.py`                                             |
| upgrade ceremony UX (challenge-nonce, history, violations)         | `/posture` command (show/history/violations/upgrade/override)                                                                                                                                | `commands/posture.md`                                                                                                      |

**PACT is the reference implementation of the brief's end-user-facing posture+intervention loop.** It already has: an objectives router, work sessions, an approval queue surfaced on a web dashboard with an `Approvals` screen (`pact/care-03-approvals.png` exists), posture enforcement at action time, an `ApprovalBridge` connecting HELD verdicts to human-resolvable rows, an `EmergencyBypass`, and an `EventBridge`. The platform reuses this stack wholesale.

### 6.2 The gap — "repo-level rule for coding agents" vs "live, per-task, end-user-facing control"

This is the precise gap the synthesis must name. Three sub-gaps:

**Gap A — Keying granularity (repo → objective → step).** The COC posture is **per-repo, single-valued** (`posture.json` holds ONE posture for the whole checkout; `rules/trust-posture.md:37` "Posture Is Per-Repo"). The brief wants posture **per-objective** ("choose a posture beforehand" for _this_ report) and intervention **per-step**. The EATP `PostureStateMachine` is already keyed by `agent_id` — re-key to `objective_id` (objective-level posture) and let each spawned sub-agent/step inherit-or-tighten via EATP's **constraint-tightening delegation** (a step can only _reduce_ the objective's posture, never raise it — `eatp-spec.md:15`). PACT already operates per-action; the missing piece is a per-objective _default posture record_ that the per-action enforcer reads. **Effort: ~1 session** (re-key + a per-objective posture row; the state machine is unchanged).

**Gap B — Audience (coding agent → non-coder end user).** COC posture is surfaced to a _developer_ via slash commands (`/posture`, `[ack: rule]` receipts) and assumes the reader understands `L4_CONTINUOUS_INSIGHT`. The brief's user is a non-coder (`briefs/01-vision.md:24`, and Sequor `rules/communication.md` mandates plain-language). The fix is a **presentation layer**: the three plain-language buttons (§1.4), HELD decisions rendered as "The agent wants to send this email — Approve / Edit / Reject" cards (PACT's approval queue already produces the rows; the rendering is new), and posture history shown as a timeline, not a JSON transition_history. The _engine_ needs no change; the _surface_ is net-new but PACT's Next.js `objectives`/`approvals` screens are the starting scaffold. **Effort: this is the bulk of the net-new UX work — multiple sessions.**

**Gap C — Self-imposed (agent governs itself) → other-imposed (user governs the agent).** COC posture is the agent's _self-governance_ in a trusted operator's repo (default L5, downgrade on self-detected violation). The brief inverts the trust polarity: the **user** sets the posture _over_ the agent, beforehand, per task, and the agent must _surface and wait_. This is exactly PACT/EATP's polarity (human establishes trust, agent verifies against it) — so the gap is "use the PACT/EATP polarity, not the COC polarity." Practically: the platform's default should be the **EATP/PACT default (start SUPERVISED, user opts up)**, NOT the COC default (start DELEGATED). The COC violation-driven _downgrade_ machinery still applies as a safety floor (`min(user_chosen_posture, system_floor)` — the `computeOperativePosture` pattern in `commands/posture.md:18`).

### 6.3 Retrace + intervene + version (the brief's hardest requirement)

The brief: _"users can retrace any previous step and intervene from there; downstream/cascading outputs change accordingly, but old outputs are versioned."_ Grounding for each half:

- **Retrace** — the signed Audit-Anchor hash-chain (§4.5) IS the retraceable step log; each anchor's `parent_anchor_id` lets the UI walk backward. PACT's `AgenticWorkSession` + `AgenticDecision` + `Run` + `ExecutionMetric` models give per-step rows; the `EventBridge` (`engine/event_bridge.py`) streams them to the UI live.
- **Intervene-from-a-prior-step** — this is a **re-execution-from-checkpoint** capability that does NOT exist as a primitive in any of the read sources. EATP/PACT record and gate steps; they do not implement "rewind to step N, change the decision, re-run downstream." **[GAP — net new]** The platform must build this on top of: (a) the anchor chain (to identify step N), (b) the `AgenticDecision`/artifact records (the per-step inputs/outputs to version), and (c) a workflow re-entry mechanism. Kailash Core SDK durable execution + checkpointing (`skills/15-enterprise-infrastructure`) is the likely substrate but was **not read** in this research — flag for the infrastructure research stream.
- **Version old outputs** — `AgenticArtifact` records + the immutable anchor chain give natural versioning (each re-run produces new artifacts; old ones are never mutated, they're superseded). The append-only, hash-chained design means "old outputs versioned" is a _consequence_ of the anchor model, not extra work — but the **branching semantics** ("downstream changes accordingly") are net-new orchestration logic.

### 6.4 Recommended platform posture architecture (synthesis)

1. **Engine:** EATP `PostureStateMachine` + `SQLitePostureStore` (or DataFlow-backed store), keyed by `objective_id`; per-step delegation tightens via constraint-tightening (steps inherit ≤ objective posture).
2. **Per-action enforcement:** PACT `posture_enforcer` verdict model (BLOCK/HELD/auto-approve) — **but** replace the keyword classifier with an LLM-first consequentiality judge per Sequor `agent-reasoning.md`.
3. **Intervention surface:** PACT `ApprovalBridge` → approval-queue rows → plain-language Approve/Edit/Reject cards (Next.js, built on PACT's `objectives`/`approvals` scaffold).
4. **Budget:** per-objective `BudgetTracker` with 80/95/exhausted alerts surfaced as a progress widget.
5. **Audit/retrace:** signed Audit-Anchor hash-chain (aegis anchor format) + PACT session/decision/artifact records, streamed via `EventBridge`.
6. **Posture lifecycle:** EATP/PACT default (start SUPERVISED) + user opt-up via a challenge-nonce-equivalent confirmation; COC violation-driven downgrade as the safety floor (`operative = min(user_chosen, system_floor)`).
7. **Net-new (build):** per-objective keying glue (small), the non-coder presentation layer (large), and rewind-re-execute-with-versioning (large; needs durable-execution research).

---

## 7. Open questions (for downstream research / spec)

1. **Exact aegis posture enum semantics** — only transition `record_id`s were read; the `Restricted/Supervised/Autonomous/Full` level definitions and their mapping to the canonical 5 are **[UNVERIFIED]**.
2. **Durable-execution substrate for rewind-and-re-run** — `skills/15-enterprise-infrastructure` (Core SDK checkpointing) was not read; it is the likely substrate for §6.3 "intervene from a prior step" but must be confirmed by the infrastructure research stream.
3. **PACT objectives router contract** — `routers/objectives.py` and `apps/web/app/objectives` exist but were not read in depth; the exact AgenticObjective→posture binding (is posture a field on the objective?) needs confirmation.
4. **Posture × multi-operator** — the loom multi-operator variant runs `operative = min(operator_posture, repo_floor)` with 4-eyes upgrade gates. For an enterprise platform with many human stakeholders per objective, does posture compose across stakeholders the same way? Needs a spec decision.
5. **LLM-first consequentiality classifier** — replacing PACT's keyword classifier with an LLM judge is required by `agent-reasoning.md`; the latency/cost of an LLM call on _every_ action vs PACT's instant keyword check needs a design decision (likely: LLM-classify once per step-type, cache the verdict shape).
6. **Default-posture polarity per deployment** — COC defaults DELEGATED (trusted operator); EATP/PACT default SUPERVISED (enterprise). The platform's default likely varies by tenant trust tier — needs a business-model-aligned decision.

---

## 8. Sources consulted (paths read)

- `workspaces/future-of-work/briefs/01-vision.md`
- `.claude/rules/trust-posture.md` (Sequor; identical in loom + aegis)
- `.claude/rules/autonomous-execution.md`, `agent-reasoning.md` (via CLAUDE.md Directive 6), `communication.md`
- `.claude/commands/posture.md`
- `.claude/skills/32-trust-posture/{SKILL.md, posture-spec.md, grace-period-mechanics.md, redteam-integration.md, implement-integration.md}`
- `.claude/skills/26-eatp-reference/{eatp-trust-posture-canonical.md, eatp-sdk-api-reference.md, eatp-budget-tracking.md, eatp-posture-stores.md, eatp-trust-plane-enterprise.md, eatp-trust-plane-security.md}`
- `.claude/skills/co-reference/{eatp-spec.md, governance-layer-thesis.md}`
- `kailash-py/src/kailash/trust/posture/postures.py` (PostureStore, PostureStateMachine)
- `kailash-py/src/kailash/trust/plane/config.py` (TrustPlaneConfig)
- `kailash-py/src/kailash/trust/constraints/budget_tracker.py` (class locations)
- `aegis/.claude/rules/trust-posture.md`; `aegis/proj-*/anchors/anc-posture-*.json` (signed transition anchors)
- `pact/src/pact_platform/use/execution/posture_enforcer.py` (posture→verdict mapping)
- `pact/src/pact_platform/engine/approval_bridge.py` (HELD→approval queue)
- `pact/src/pact_platform/models/__init__.py` (11 DataFlow governance models)
- `pact/` tree (objectives router, approvals dashboard, emergency_bypass, event_bridge, orchestrator, posture_assessor, posture_history — located, not all read in depth)
