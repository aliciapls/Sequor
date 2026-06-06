# Trust, Posture & Governance (M2)

> Status: TARGET-STATE (vision / not yet implemented). This spec describes the intended platform; the comms wedge (shipped) specs are separate (`message-routing.md`, `rag-pipeline.md`, `response-accuracy.md`, `data-model.md`, `channel-coordination.md`, `business-model.md`, `onboarding.md`).

This is the authority on **how the user governs an agent before and during execution** — moat M2 in the strategic spine: execution-time, posture-graded governance set _before_ work runs, per objective, not bolted on as after-the-fact observability. The user states intent and picks how much rein the agent gets; the agent surfaces its plan, waits where it must, stays inside a spending and scope budget, and records every move so it can be replayed and audited.

**Plain-language frame.** Before an agent does a piece of work, the user picks one of three settings — _go ahead_, _ask me once_, or _step through with me_. That choice, plus a spending limit and a scope limit, is the whole control surface. Everything below is the precise machinery behind those three buttons.

**Reuse posture.** ~80% of this machinery already ships across the ecosystem; ~15% is integration glue; ~5% is genuinely new (the non-coder control surface) (Research 03 §8.5; Plan 04 §0). Each domain below states REUSED-vs-NET-NEW explicitly.

---

## 1. The L1–L5 posture ladder (canonical)

A **posture** says how much the agent may do on its own before it must stop and ask. The canonical source of truth is the EATP SDK `TrustPosture` enum — a `str`-backed `Enum` with an `autonomy_level` property; `1` = least autonomy, `5` = most (Research 04 §1.1, grounded in `eatp/.../trust/posture/postures.py`). **REUSED** from eatp (`/Users/esperie/repos/loom/kailash-py`).

| `autonomy_level` | Canonical enum | Wire value | What the agent may do | Human's role |
| --- | --- | --- | --- | --- |
| **5** | `AUTONOMOUS` (alias `DELEGATED`) | `"autonomous"` | Acts on its own within agreed scope | Watches remotely; can abort |
| **4** | `DELEGATING` (alias `CONTINUOUS_INSIGHT`) | `"delegating"` | Acts on its own; checks in at boundaries | Monitors in real time |
| **3** | `SUPERVISED` (alias `SHARED_PLANNING`) | `"supervised"` | Proposes each action; human approves each | Approves every action |
| **2** | `TOOL` (alias `SUPERVISED`-in-spec) | `"tool"` | Co-plans, then executes the approved plan | Co-plans, approves the plan |
| **1** | `PSEUDO` (alias `PSEUDO_AGENT`) | `"pseudo_agent"` | Interface only; the human reasons | Does all the reasoning |

Properties of the enum (Research 04 §1.1):
- Ordering is defined: `TrustPosture.SUPERVISED < TrustPosture.AUTONOMOUS` is `True`.
- `can_upgrade_to(target)` ≡ `target.autonomy_level > self.autonomy_level`; `can_downgrade_to` is the mirror.
- Backward-compat aliases (`DELEGATED→AUTONOMOUS`, `CONTINUOUS_INSIGHT→DELEGATING`, `SHARED_PLANNING→SUPERVISED`, `PSEUDO_AGENT→PSEUDO`) deserialize older records; new code uses canonical names.
- **Default posture is `TOOL` (level 2)** per CARE spec RT-17 — "tool agents start supervised; the agent proposes, a human approves" (Research 04 §1.1, §4.1). For an enterprise end-user platform the safer base is "start supervised"; see §10 safety-floor.

### 1.1 The numbering reconciliation (load-bearing)

Three numbering conventions exist in the ecosystem and they do **not** line up. This reconciliation is a spec section, not folklore — pin it (Research 04 §1.4; Plan 04 §1).

- **aegis L1–L5 ladder** (`/Users/esperie/repos/dev/aegis`) and the COC repo-posture ladder name levels `L1..L5` with `L5` at the _top_, but their `SUPERVISED`/`SHARED_PLANNING` levels re-number relative to the EATP enum. The COC `L3_SHARED_PLANNING` is _higher_ than `L2_SUPERVISED`; the EATP `SUPERVISED` (level 3) is _higher_ than `TOOL` (level 2) (Research 04 §1.2).
- **aegis production transitions** (`aegis/proj-*/anchors/anc-posture-*.json`, read directly) run a `Restricted → Supervised → Autonomous → Full` ladder — a fourth vocabulary. Exact aegis enum semantics are **[UNVERIFIED]**; only transition `record_id`s were read (Research 04 §1.3, §7 item 1).
- **The brief's three rungs** (`briefs/01-vision.md` §3e) — L5 Autonomous, L4 Supervised, L3 Step-by-step — collide head-on with the canonical labels:
  - The brief's **L4 "Supervised"** means "ask for **one** permission." But in the engine "Supervised" is level 3, where the human approves **every** action — the opposite. (Research 04 §1.4.)
  - The brief's **L3 "Step-by-step"** ("pause at each step") behaviourally matches the engine's level-3 `SUPERVISED` (hold-every-action), not a middle planning rung.

**Resolution (binding contract): the canonical EATP five-rung enum is the internal source of truth; the brief's L3/L4/L5 labels MUST NOT be shipped as the enum.** Shipping the brief's labels as enum names confuses every reader who knows the existing system. The collision is contained at the presentation boundary (§2), where it costs nothing.

### 1.2 The end-user mapping — three plain buttons

The user never sees `AUTONOMOUS` or `envelope_version`; they see three choices. **NET-NEW** presentation binding; the underlying enum is **REUSED** (Plan 04 §1.2; Research 04 §1.4).

| User-facing button | Internal posture | Per-step behaviour | Human's relationship | HITL/HOTL |
| --- | --- | --- | --- | --- |
| **"Go ahead"** | `AUTONOMOUS` (5) | Auto-approve inside scope; anything outside is **blocked** | On the loop — watches, can abort | HOTL (remote) |
| **"Ask me once"** | `DELEGATING` (4) | Auto-approve inside scope; **one** approval at the plan→do boundary | On the loop + one checkpoint | HOTL + one gate |
| **"Step through with me"** | `SUPERVISED` (3) | Every consequential action pauses for approval | In the loop — blocks each step | HITL |

`PSEUDO` (1) and the block-everything floor remain in the engine as the **system's automatic downgrade target** when something goes wrong — they are never user buttons (Research 04 §1.4).

**Known limitation (recorded, not glossed):** three buttons expose fewer states than the engine has — a power user cannot reach `TOOL` (level 2, "co-plan first") from the UI. This is a deliberate v1 narrowing (Plan 04 §1.2; §13 #5 below).

---

## 2. HITL vs HOTL — the posture choice IS the choice between them

Two terms from the brief (§3e), translated:
- **HITL (human-in-the-loop):** the human is a **blocking node inside the work path** — the agent cannot proceed past a consequential action without the human.
- **HOTL (human-on-the-loop):** the human is a **monitor outside the work path** — the agent proceeds; the human watches and can abort but does not gate each step.

The load-bearing finding (Research 04 §3; Research 03 §4.2; Plan 04 §2): **the posture level _is_ the HITL/HOTL choice — it is not a separate control.** The engine's per-action decision rule already encodes it (read from PACT's `posture_enforcer.py`):

```
SUPERVISED   (3): every consequential action → HOLD for approval     → HITL
DELEGATING   (4): inside scope auto-approve; one boundary → HOLD      → HOTL + one gate
AUTONOMOUS   (5): inside scope auto-approve; outside scope → BLOCK    → HOTL (remote)
PSEUDO       (1): block ALL actions before any LLM call               → HITL (hard)
```

**Implication for the platform contract.** There is **one** posture control; HITL-vs-HOTL falls out of it. The platform MUST NOT build "a HITL mode" and "a HOTL mode" as two features — that halves the surface area and removes a class of "the two modes disagree" bugs.

### 2.1 Structural vs execution gates

The user's button choice is, mechanically, a choice over **which class of gate blocks the agent** (Research 04 §5; `autonomous-execution.md`):
- **Structural gates** (approve-the-plan, authorise-a-release, change-the-scope) — these stop the agent even at high posture. A human _must_ act.
- **Execution gates** (the agent doing analysis, drafting, assembling correctly) — these auto-converge at high posture; at low posture they also become blocking.

At high posture (HOTL) only structural gates stop the agent; at low posture (HITL) execution gates also block. Choosing a posture per objective = choosing which gate class is blocking for that objective.

---

## 3. Operating envelopes — scope / budget / clearance

A posture says _how often the human is asked_. An **envelope** says _what the agent may touch at all_. The two are orthogonal; both **REUSED** from pact (`/Users/esperie/repos/terrene/contrib/pact`) (Research 03 §3). The envelope is the brief's "permission envelope."

### 3.1 Five dimensions + ceilings

A PACT `ConstraintEnvelopeConfig` carries five constraint blocks (Research 03 §3.2):

| Dimension | Constrains (plain language) | Key fields |
| --- | --- | --- |
| **financial** | How much it may spend; the amount above which it must ask first | `max_spend_usd`, `api_cost_budget_usd`, `requires_approval_above_usd` (→ triggers HOLD) |
| **operational** | Which actions are allowed/blocked; rate caps | `allowed_actions`, `blocked_actions`, `max_actions_per_day/hour` |
| **temporal** | When it may run | `active_hours_start/end`, `timezone`, `blackout_periods` |
| **data_access** | Which files/data it may read or write; data types never touched (e.g. PII) | `read_paths`, `write_paths`, `blocked_data_types` |
| **communication** | Internal-only vs external; which channels | `internal_only`, `allowed_channels`, `external_requires_approval` |

Plus a top-level **`confidentiality_clearance`** (the clearance ceiling — how sensitive a document it may read) and **`max_delegation_depth`** (how many layers of sub-agents — directly relevant to the brief's "agent spins up 3 agents").

### 3.2 The load-bearing safety invariant — delegation can only tighten

**A child envelope can only be equal to or more restrictive than its parent** (Research 03 §3.3; EATP delegation rule, Research 04 §2.1). A manager with a $50K limit can hand an agent $10K, never $75K. `RoleEnvelope.validate_tightening()` checks all dimensions; a child that _omits_ a constraint the parent has is treated as **wider** → violation. Intersection follows XACML deny-overrides: financial = `min()`; operational = intersect-allowed/union-blocked, blocked wins; data_access = intersect-paths/union-blocked-types; communication = `internal_only = a OR b`. NaN/Inf is rejected everywhere (`NaN < X` is always `False` → would silently pass every budget check).

The same rule governs posture: **a step inherits ≤ the objective's posture, never above it** (Research 04 §6.2 Gap A). A sub-task cannot promote itself to "Go ahead" if the objective was set to "Step through with me."

### 3.3 Execution-time enforcement — `verify_action` (reused wholesale)

The single decision call is `engine.verify_action(role_address, action, context)` (Research 03 §3.4). Flow:
1. Compute the effective envelope **with a version fingerprint** (SHA-256 of all contributor envelope versions — the TOCTOU defense; this `envelope_version` is the load-bearing field for "retrace and intervene" — it lets the system detect the envelope changed between when a step was planned and when it runs).
2. Evaluate the action against all five dimensions.
3. Multi-level verify: walk the D/T/R accountability chain (§11), **most-restrictive verdict wins**.
4. If the resource is a `KnowledgeRecord`, run the 5-step fail-closed clearance check (§3.4).
5. Combine verdicts (most restrictive wins).
6. Emit an audit anchor.

The returned `GovernanceVerdict` carries `level` (the verification gradient — §4), `allowed`, `reason`, `envelope_version`, and `access_decision`. Edge cases the engine already handles and the platform inherits: degenerate-envelope detection (no allowed actions → warn), pass-through-envelope detection (child adds no constraint), gradient-dereliction (auto-approve threshold ≥90% of the financial limit → rubber-stamping warning).

**Per-objective defaults by posture** ship today (`default_envelope_for_posture()`, Research 03 §3.5): PSEUDO → $0/read-only; TOOL → $50/read+write; SUPERVISED → $1,000/read+write+plan+propose; DELEGATING → $10,000/+execute+deploy; AUTONOMOUS → $100,000/+approve+delegate. The product gives the user a sensible default the moment they pick a button, then lets them narrow it.

### 3.4 Knowledge clearance (the data-access enforcement)

`engine.check_access(role, knowledge_item, posture)` is fail-closed — **default is DENY** (Research 03 §4.1):
```
Step 1  Resolve clearance     → DENY if missing or vetting not ACTIVE
Step 2  Classification check  → DENY if effective_clearance < item.classification
Step 3  Compartment check     → DENY if role lacks item's compartments (SECRET+ only)
Step 4  Containment check     → ALLOW via one of 5 sub-paths (same-unit / downward-visibility / T-inherits-D / KnowledgeSharePolicy / PactBridge)
Step 5  Default deny          → DENY if no path granted
```
**Effective clearance = `min(role.max_clearance, POSTURE_CEILING[posture])`** — posture is a ceiling that caps standing clearance. A denial always carries `step_failed` (1–5) and `reason` — exactly the legibility the intervention UX needs.

**REUSED** wholesale. **NET-NEW:** the per-objective envelope record the per-action checker reads, and the plain-language rendering of the five dimensions ("spend up to $200 without asking", not `requires_approval_above_usd: 200`).

---

## 4. Decision-surfacing + approval — the plan is approvable BEFORE execution

This is the heart of M2 (brief §3e): the agent decides to spin up three agents, and **that decision is shown on screen and recorded, and the user chose a posture beforehand.** The genuinely-new move: the agent's **plan** (the fan-out — 3 sub-tasks, what each does, estimated cost) is captured as an **approvable object and shown to the user _before any of it executes_** (Research 04 §6.1; Plan 04 §4).

### 4.1 The verification gradient (the four-level decision)

Every action resolves to one of four levels (Research 03 §4.2; EATP `Verdict` enum):

| Verdict | Meaning | Action taken |
| --- | --- | --- |
| `AUTO_APPROVED` | within all constraints | execute and log |
| `FLAGGED` | near a constraint boundary | execute **and highlight for review** |
| `HELD` | soft limit exceeded | **queue for human approval** (creates an `AgenticDecision`) |
| `BLOCKED` | hard limit violated | reject with explanation |

The posture chooses _where the pause line falls_: `SUPERVISED` holds every consequential action; `DELEGATING` holds one boundary; `AUTONOMOUS` only blocks out-of-scope. Audit durability is gradient-aligned — `TieredAuditDispatcher` routes BLOCKED to the most durable storage, AUTO_APPROVED to memory.

### 4.2 The shipped surface-and-approve pipeline (reuse, don't rebuild)

The brief's "surface the decision, pause, await the human" loop is **shipped code** in pact (Research 03 §5, read directly). **REUSED** from pact.

- **`SupervisorOrchestrator`** — the top-level entry point that turns a submitted objective into governed work. When per-action checking returns **HOLD**, its `_PlatformHeldCallback` **creates an approval record and returns `False` to block the action until a human approves** (Research 03 §5.1). That single `return False` _is_ "the agent pauses and asks for one permission."
- **`ApprovalBridge`** — turns each HOLD into a durable, queryable, human-resolvable row: `create_decision()` → a pending `AgenticDecision`; `approve()`/`reject()` records who decided, when, and why; `get_pending()` feeds the on-screen approval queue (Research 03 §5.2).
- **`EventBridge`** — streams plan, holds, and costs to the screen in real time over a live connection: `on_plan_event` (per scheduled sub-task), `on_hold_event` ("a decision needs you"), `on_cost_event` (Research 03 §5.3). This is the existing realisation of "decisions surfaced on screen, recorded." **Known constraint:** the event bus is **single-process / in-memory**; a multi-replica deployment needs a durable/distributed bus (§13 #8).

### 4.3 The genuinely-new wiring (small)

1. **A `plan_proposed` decision type.** Today the system surfaces a HOLD when a step is _near a limit_. **NET-NEW:** a decision type that surfaces the **plan itself** — the fan-out — as the approvable object, before execution. The user sees "here is what I'm about to do: 3 sub-tasks, est. $X" as an inspectable card (Research 04 §6; Plan 04 §4.2).
2. **A `USER` pause trigger.** The existing pause mechanism (`PlanSuspension`, Research 03 §5.6 / §8.3) suspends on BUDGET/TEMPORAL/POSTURE/ENVELOPE triggers — there is no user-initiated pause. **NET-NEW:** a `USER` trigger value + one route so a person can say "stop here" mid-flight (Research 03 §8.4 item 1).
3. **A verdict→prose renderer.** Engine holds are legible to engineers (`constraint_dimension=financial, requires_approval_above_usd=200`). **NET-NEW:** a renderer that produces _"This step would spend $240, above your $200 auto-approve limit — approve?"_ with **Approve / Edit / Reject**, per `communication.md` (Research 03 §8.4 item 6).

The posture choice then decides whether the `plan_proposed` card **auto-approves** ("Go ahead"), **needs one approval** ("Ask me once"), or **pauses at every consequential step** ("Step through with me").

**The risk shape.** The platform is not building an approval system; it is putting a non-coder face on one that already pauses, records, and awaits. The risk moves from "can we build the engine?" (no — it ships) to "can a non-coder understand the card?" (§13 #1).

---

## 5. Budget ceilings — cost-per-objective with early warnings

Fully shipped as the EATP `BudgetTracker` (Research 04 §2.3, grounded in `eatp/.../trust/constraints/budget_tracker.py`). **REUSED** from eatp.

- **Integer microdollars** (1 USD = 1,000,000 µ$) — no floating-point drift; threshold checks are exact integer arithmetic.
- **Reserve-then-record, fail-closed** — `reserve(est)` returns `False`/refuses if insufficient; `record(reserved, actual)` after the work. Safe-direction invariant: between the two atomic ops `remaining()` may briefly _over_-report, but **never denies a spend that should have been allowed.**
- **Threshold callbacks at 80% / 95% / exhausted**, each firing at most once — the hooks for "you're approaching your limit" warnings surfaced to the user. `on_record()` fires on every record (the explicit posture-budget integration hook).
- **`BudgetExhaustedError`** (subclass of `ConstraintViolationError`) raised on exhaustion.
- **Crash-safe persistence** via `SQLiteBudgetStore` (WAL mode, per-thread connections, 0600 file perms, parameterised SQL, `tracker_id` validated `^[a-zA-Z0-9_-]+$`, transaction log capped at 10k).

**Contract for the platform.** A per-objective `BudgetTracker(tracker_id="obj-<id>")` gives a spending ceiling per piece of work, with 80/95/exhausted alerts surfaced to the user. "Cost per turn" → `max_cost_per_action`; "objective budget" → `max_cost_per_session` (both exposed by the envelope). The `budget_status` dict (`session_cost / remaining / utilization`) is a ready-made progress widget. Crossing `requires_approval_above_usd` flips the verdict to HELD → spawns a `plan_proposed`/approval card (§4). **NET-NEW:** wiring per-objective trackers + the progress widget.

---

## 6. Emergency bypass with audit — the accountable "break glass"

The most security-hardened component already shipped — `EmergencyBypass` (Research 03 §5.4, ~1,000 lines read in full). **REUSED** from pact wholesale. A senior human can grant a **time-limited expansion** of permissions for a genuine emergency, and the design makes quiet abuse impossible:

- **Tiered, time-bounded** — TIER_1 4h (tactical) / TIER_2 24h (extended) / TIER_3 72h (crisis). **TIER_4 (>72h) is rejected for creation:** "emergencies over 72 hours must be re-authorised through normal governance every 72 hours."
- **Authority gating** — SUPERVISOR→Tier1; DEPARTMENT_HEAD→Tier1-2; EXECUTIVE→Tier1-3; COMPLIANCE→any.
- **Privilege-escalation defense** — `_validate_expanded_envelope` verifies the expanded envelope does not exceed the approver's _own_ envelope across all five dimensions. You cannot grant more than you hold.
- **Structural-authority defense** — `_validate_structural_authority` checks the approver's position in the target's accountability chain matches the tier.
- **Rate-limited atomically** — max 3 per week, 4h cooldown, enforced with `BEGIN IMMEDIATE` cross-process so two workers cannot race past the limit.
- **Fail-closed audit** — if the audit record cannot be written, **bypass creation aborts:** "governance mutations require an audit trail."
- **Mandatory post-incident review** — every bypass schedules `review_due_by` (expiry + 7 days); `check_overdue_reviews()` surfaces ones past deadline. `check_bypass(role)` is fail-closed: errors → `None` = no bypass.

**NET-NEW:** a senior-facing surface to request a bypass + a plain-language rendering of its terms ("expanded permissions for 4 hours; auto-reviewed in 7 days").

---

## 7. Posture lifecycle — a verifiable state machine

The brief wants posture **set/upgraded beforehand** and **recorded as a verifiable state machine**. Both halves ship (Research 04 §2.4, §4).

### 7.1 Set / default / downgrade / upgrade / override

- **Set & default** — the persisted state machine (`PostureStateMachine` + `SQLitePostureStore`, Research 04 §2.4) holds the posture, defaults to "start supervised," and records every transition. Two SQLite tables: `postures(agent_id PK, posture, updated_at)` and `transitions(id, agent_id, from_posture, to_posture, success, timestamp, metadata, transition_type)`. The `transition_type` column preserves `EMERGENCY_DOWNGRADE` distinct from a plain `DOWNGRADE` for forensics. **REUSED** from eatp; the only change is the key (§9 Gap A).
- **Downgrade is automatic and system-gated** — repeated problems instantly drop the agent to the most restrictive posture (`emergency_downgrade()` bypasses all guards and goes straight to `PSEUDO`, Research 04 §2.4, §4.2). The `PostureTransition` enum is `UPGRADE / DOWNGRADE / MAINTAIN / EMERGENCY_DOWNGRADE`. This is the **safety floor** that makes "Go ahead" safe to offer.
- **Upgrade is human-gated** — the governing principle (Mirror Thesis, Research 04 §4.3): **upgrades are human-gated; downgrades fire automatically.** The default `TransitionGuard` requires a `requester_id` on every upgrade — the structural "agent cannot self-promote" enforcement. The full upgrade requirements: ≥7 days at current posture; 0 violations of the triggering rule class; ≥1 demonstrated proactive correction; human approval.
- **Override** — false-positive recovery / bootstrap / emergency-restore: same gate as upgrade but bypasses the time/violation requirements; records `type: OVERRIDE, approved_by: human`.

### 7.2 The challenge-nonce — why upgrade needs a fresh human keystroke

A **nonce** is a one-time random code. The upgrade ceremony works in two steps (Research 04 §4.3): the user requests an upgrade; the system writes a random nonce to a hook-readable file (mode 0600) and prints _"to confirm, paste this code in your next message: `<NONCE>`"_; the user pastes it and re-runs the upgrade with the code. The system verifies the user's _prior turn_ actually contained the literal nonce before recording the upgrade.

**Why the paste-back:** "a human gate alone is forgeable — the agent can invoke the approval command itself." The nonce forces a **fresh human keystroke into the transcript the agent cannot synthesise** — the structural defence against an agent self-promoting.

**End-user contract.** The nonce ceremony was designed for a developer typing slash-commands. For a non-coder picking a button, the equivalent is a deliberate, unspoofable confirmation gesture — a typed confirmation, a re-authentication, or a second-factor tap — that the agent cannot perform on the user's behalf. The _principle_ transfers exactly (the agent must not grant itself more rein); the _mechanism_ is re-skinned from "paste this code" to a UI gesture. This is a design decision (§13 #3). **NET-NEW** (the gesture); the principle and the guard machinery are **REUSED**.

### 7.3 The state-machine operations contract — set / upgrade / override / record

The verifiable state machine exposes four operations the platform binds to per-objective records:

| Operation | Gate | Recorded transition | Anchor emitted |
| --- | --- | --- | --- |
| `set` (initial) | none (default) or user-pick at objective start | `MAINTAIN`/initial | yes |
| `upgrade(challenge-nonce)` | human paste-back gesture; requirements §7.1 | `UPGRADE`, `approved_by: human` | yes |
| `override` | human gesture; bypasses time/violation reqs | `OVERRIDE`, `approved_by: human` | yes |
| `record` (downgrade) | automatic on violation | `DOWNGRADE` / `EMERGENCY_DOWNGRADE` | yes |

Every transition enforces chain-consistency: `transition_history[i].from === transition_history[i-1].to`.

### 7.4 Recorded with signed anchors — two layers, use both

The brief's "recorded as a verifiable state machine with anchors" is satisfied by two existing layers (Research 04 §4.5). **REUSED.**

1. **The posture state file** — an append-only transition history where each entry's "from" must equal the prior entry's "to" (chain-consistency enforced), and **direct edits are blocked** — only the hooks may write it. This is the live, auditable state.
2. **The cryptographic anchors** — the aegis posture-transition anchors (`anc-posture-*.json`, read directly). Each anchor:
```json
{
  "anchor_id": "anc-posture-8838c0a29548",
  "anchor_type": "posture_transition",
  "parent_anchor_id": "anc-posture-f490b9f6a0e6",   // hash-chain back-pointer
  "record_id": "posture-Autonomous-to-Full",
  "record_hash": "8838c0a29548...407a",              // SHA-256 of the record
  "signature": "b3b1e7d1...130b",                    // Ed25519 detached signature
  "created_at": "2026-03-16T16:47:51.536884Z"
}
```
Each anchor names its `parent_anchor_id` (hash-chain back-pointer), carries a SHA-256 `record_hash`, and an Ed25519 `signature`. Modifying any record invalidates the chain forward — tamper-evident, replayable. EATP's signing primitives (`generate_keypair`, `sign`, `verify_signature`) produce these.

Together every posture change is **attributable** (who), **ordered** (the chain), and **tamper-evident** (the signature). **NET-NEW:** wiring anchor emission on the per-objective posture transitions.

### 7.5 The honesty caveat that travels with every trust claim

**The system delivers _traceability_, not _accountability_** (Research 03 §2.3; Research 04 §2.2; brief §3f). Traceability — every action traces back to its inputs, decisions, and the human authority that permitted it — the machine guarantees this. Accountability — that a human actually _understood_ and bears the consequences — no software can guarantee this. The posture + surfacing UX converts traceability into a _chance_ at accountability; it cannot force understanding. Over-claiming here is dishonest and legally hazardous; any user-facing or marketing copy MUST state the boundary.

---

## 8. Per-objective AND per-step posture

The brief wants posture set **per objective** and intervention **per step**. The state machine is already keyed by an ID (`agent_id` today) — the platform **re-keys to `objective_id`** (Research 04 §2.4, §6.2 Gap A). PACT already operates per-action.

The contract:
- **Per-objective posture** — a per-objective default posture record the per-action enforcer reads. Set when the user picks a button at objective start.
- **Per-step posture** — each spawned sub-agent/step inherits-or-tightens via the constraint-tightening delegation rule (§3.2): **a step inherits ≤ the objective's posture, never above it.** When the brief's agent spins up three sub-agents for the 3Q report, each sub-agent gets a _tightened_ slice of the parent's envelope and posture — it can only ever do _less_ than the objective was granted.

**REUSED:** the state machine, persistence, history, and guards. **NET-NEW:** the per-objective keying glue (small) + the inherit-only tightening enforcement on the step path.

---

## 9. The gap — repo-rule-for-coding-agents vs live end-user control

Two _different_ posture systems exist in the ecosystem that look alike and must not be conflated (Research 04 §1.2, §6.2; Research 03 §8.2). This is the precise question the brief poses and the cleanest way to see reuse-vs-new.

- **The COC repo-posture** governs **the coding agents that build _this product_.** One posture per code repo; starts at full trust; auto-downgrades on detected rule violations. The brief borrows its vocabulary ("L3/L4/L5") but not its meaning. This system **stays exactly where it is** — meta-governance of the codegen, not the customer-facing control.
- **The end-user posture** the brief wants is a **per-objective, user-set, step-pausing control** over the agent doing the customer's work. This is the PACT/EATP polarity — the human sets trust over the agent, beforehand, per task; the agent surfaces and waits.

Three sub-gaps, with disposition:

| Gap | Today (coding-agent posture) | Needed (end-user posture) | Reuse vs net-new |
| --- | --- | --- | --- |
| **A — Keying** | One posture per repo | One posture per **objective**; intervention per **step** | The state machine is already keyed by an ID — **re-key** `agent_id` → `objective_id`; steps tighten via inherit-only (§3.2). PACT operates per-action already. Small glue. |
| **B — Audience** | Surfaced to a _developer_ via slash-commands; assumes `L4_CONTINUOUS_INSIGHT` is legible | Surfaced to a _non-coder_: three plain buttons, Approve/Edit/Reject cards, a timeline | Engine unchanged. **Presentation layer is NET-NEW** (PACT's web objectives/approvals screens are the starting scaffold). **The bulk of the work.** |
| **C — Polarity** | Agent governs _itself_ (default full trust, downgrade on self-detected violation) | User governs _the agent_ (default supervised, user opts up) | A **default choice**, not code: adopt PACT/EATP "start supervised"; keep the COC violation-driven downgrade as the **safety floor** (§10). A decision + small wiring. |

### 9.1 Reuse-vs-net-new — the one-line summary

- **REUSED** (eatp / pact / aegis / loom): the posture state machine, the spending tracker, the five-dimension envelope, the four-level decision gradient, the approval queue, the live event stream, the emergency bypass, the signed audit anchors, the D/T/R accountability grammar, the 17 work-tracking DataFlow models, knowledge-clearance, `EnforcementMode.SHADOW`.
- **NET-NEW:** the per-objective keying glue (small), the `plan_proposed` decision type + `USER` pause trigger (small), the AI-judged consequentiality classifier (small — §9.2), and **the non-coder presentation layer (large) — the live end-user control surface.**

This matches the spine's ~80/15/5 reuse/glue/new split (Research 03 §8.5).

### 9.2 Two integration decisions baked into the design

1. **Replace the keyword classifier with an AI-judged one.** PACT decides "is this action consequential?" by **matching keywords** (`write`, `send`, `delete`…). Sequor's own rules **forbid** keyword/regex routing in agent decision paths (`agent-reasoning.md`; CLAUDE.md Directive 6; Research 04 §3; Plan 04 §9.1). The platform keeps PACT's _verdict_ machinery (pause/block/auto-approve) but replaces its _decision path_ with an **AI-judged** consequentiality assessment — the model is the classifier. This carries a real cost/latency tradeoff (an AI call on every action vs an instant keyword match); the mitigation (judge once per step-type, cache the verdict shape, tenant-scoped) is itself unproven at scale (§13 #2). **NET-NEW** (small, well-scoped rewrite).
2. **Roll out in observe-only mode first.** The engine has `EnforcementMode.SHADOW` — it runs full governance and logs what it _would_ have held or blocked but **never actually blocks** (Research 03 §5.5). This is how governance slots under the live Sequor comms product **without breaking it**: observe, calibrate envelopes and thresholds, then turn on the teeth. The three modes: **ENFORCE** (binding — production), **SHADOW** (run + log, never block), **DISABLED** (skip governance; requires `PACT_ALLOW_DISABLED_MODE=true`, refuses to instantiate otherwise). **REUSED.**

---

## 10. The safety floor — `min(user-chosen, system-floor)`

"Go ahead" is **not a blank cheque** — it is a ceiling the system can instantly lower. Two mechanisms compose into the operative posture (Research 04 §6.2 Gap C; Plan 04 §7.1):

**Operative posture = `min(user-chosen-posture, system-floor)`.**

- **`user-chosen-posture`** — the button the user picked for this objective (the upper bound on autonomy).
- **`system-floor`** — the COC violation-driven downgrade applied as a safety floor; on repeated problems `emergency_downgrade()` drops the agent to `PSEUDO` (level 1) instantly.

The user can never set the agent _above_ the floor, and the floor can drop _below_ the user's pick the instant something looks wrong. This is what makes offering "Go ahead" safe by construction: autonomy is bounded above by the user's choice and below by the system's live assessment.

**Tenant default polarity is a per-tenant decision** (§13 #6): COC defaults to full trust (trusted operator); EATP/PACT default to supervised (enterprise). The right default likely varies by tenant trust tier; the safe enterprise base is "start supervised."

---

## 11. D/T/R accountability

**D/T/R = Department / Team / Role** — the positional **addressing** grammar that encodes both org containment and the accountability chain (Research 03 §2; `NodeType.DEPARTMENT="D"`, `TEAM="T"`, `ROLE="R"`). **REUSED** from pact.

> Naming note: the brief's shorthand "D/T/R = Decision/Task/Review" is **incorrect**. D/T/R is the addressing grammar. `AgenticDecision` and `AgenticReviewDecision` are separate _data models_ (§12); the Decision/Task/Review trio is a coincidence of the work model, not the meaning of D/T/R.

**Core invariant:** every D or T segment must be immediately followed by exactly one R segment — the R is _the accountable person (head)_ for that unit. `D1` alone is a `GrammarError`; `D1-T1-R1` is invalid (D must be followed by R). Accountability is encoded **structurally in the address, not attached as metadata** — you cannot name an org unit without naming who is accountable for it.

The address yields the **`accountability_chain`** — all R segments in order, root→leaf. For `D1-R1-D2-R1-T1-R1` it is `[D1-R1, D1-R1-D2-R1, D1-R1-D2-R1-T1-R1]` — every person who bears accountability for the leaf role. The engine's `_multi_level_verify()` walks this chain and **the most restrictive verdict wins**; `EmergencyBypass` uses the same chain to validate an approver is structurally senior enough (§6).

**Platform contract.** When the agent spins up sub-agents, each is assigned a D/T/R address whose `accountability_chain` names the human(s) who must be looped in. Accountability is computable from the address, not a UI afterthought — the substrate the brief's "every step traced to a human" needs.

---

## 12. Work-tracking data models (the records the surface renders)

The governance records are 17 DataFlow models in pact `models/__init__.py` (the `@db.model` decorator auto-generates ~187 CRUD/bulk nodes) (Research 03 §6). **REUSED.** The load-bearing ones for M2:

| Model | Purpose | M2-relevant fields |
| --- | --- | --- |
| **AgenticObjective** | top-level work unit | `status` (draft/active/completed/cancelled), `budget_usd`, `deadline`, `parent_objective_id` |
| **AgenticRequest** | decomposed task | `assigned_to`, `status`, `sequence_order`, `depends_on` (`{request_ids:[...]}`), `envelope_id` |
| **AgenticWorkSession** | active work period w/ cost | `cost_usd` (NaN-guarded), `provider`, `model_name`, `verification_verdicts` |
| **AgenticArtifact** | produced deliverable | `content_hash`, **`version`**, **`parent_artifact_id`** (self-referential versioning), `status` |
| **AgenticDecision** | **human judgment point — created when governance returns HELD** | `decision_type` (governance_hold/budget_hold/manual_review), `status` (pending/approved/rejected/expired), `reason_held`, `constraint_dimension`, `constraint_details`, `envelope_version` (TOCTOU), `required_approvals`/`current_approvals` |
| **ApprovalRecord** | one approver's vote | `approver_address`, `verdict`, `reason` |
| **ApprovalConfig** | per-operation-type approval policy | `required_approvals`, `timeout_hours` (auto-reject), `eligible_roles` |
| **Run** + **ExecutionMetric** | per-invocation record + dashboard metrics | `verification_level`, `cost_usd`, latency/cost/tokens |

`AgenticArtifact.version` + `parent_artifact_id` is the existing substrate for the brief's "old outputs are versioned" — a retraced re-run produces a new artifact with `version+1` pointing at the prior one (the versioning is a consequence of the append-only model; the cascade-recompute that changes downstream outputs is M1's net-new engine, not M2). Multi-party approval for high-stakes ops: `ApprovalConfig.required_approvals > 1` + `MultiApproverService` quorum (per-decision asyncio locks, duplicate-vote prevention).

---

## 13. Edge cases and open unknowns

These MUST be resolved before M2 ships to non-coders. Ranked by how likely they are to sink M2's _usability_ (the engine is the tractable part).

### 13.1 Posture downgrade mid-run

When the safety floor drops mid-objective (a violation accrues while step 4 of 7 is executing), the operative posture recomputes to `min(user-chosen, new-lower-floor)`. The contract:
- Steps **already in flight** complete or are suspended per the new posture's gate class — a step that was auto-approving under `DELEGATING` now lands in HELD if the floor dropped to `SUPERVISED`.
- The downgrade emits an `EMERGENCY_DOWNGRADE` transition + signed anchor (§7.4) so the timeline shows _when_ and _why_ autonomy was reduced.
- The user is notified via `on_hold_event` that the objective's posture changed; subsequent steps inherit the lowered ceiling (inherit-only, §3.2 — a downgrade can only tighten downstream).
- A step **cannot** be retroactively un-approved — already-executed actions are recorded, not reversed (reversal is M1's cascade-recompute concern).

### 13.2 Budget exhaustion mid-objective

When `BudgetTracker` hits `exhausted` mid-objective (§5):
- The 80% and 95% callbacks already fired as warnings; the `exhausted` callback fires once.
- The next `reserve()` returns `False` (fail-closed) → the action is refused, raising `BudgetExhaustedError`.
- This surfaces as a HELD/blocked card: "this objective has used its $X budget — raise the limit to continue, or stop here?" (Approve-with-raised-budget / Stop).
- Raising the budget is an **envelope change** — a structural gate (§2.1) — so it requires a human even at "Go ahead" posture. The safe-direction invariant guarantees the tracker never _denied a spend it should have allowed_; over-reporting is the only tolerated error.

### 13.3 Emergency bypass audit

Every `EmergencyBypass` (§6) leaves a complete, fail-closed audit trail: who approved, which tier, the expanded envelope (validated ≤ approver's own), the rate-limit accounting, and a scheduled 7-day post-incident review. If the audit record cannot be written, **bypass creation aborts** — there is no bypass without an audit row. Overdue reviews are surfaced by `check_overdue_reviews()`. The bypass is time-bounded (≤72h) and rate-limited (≤3/week, 4h cooldown) so even an abused bypass has a bounded blast radius and a forced review.

### 13.4 Highest-risk unknowns (flagged, not resolved)

| # | Unknown | Why it's hard | Where it resolves |
| --- | --- | --- | --- |
| **1** | Non-coder rendering of postures, holds, and envelopes | Turning "Supervised / constraint_dimension=financial / envelope_version" into a control a non-expert acts on is unsolved; the dominant M2 usability risk | UX design + user testing; iterative discovery (§9 Gap B) |
| **2** | AI-classifier latency/cost | An AI call on every consequentiality check is slower/costlier than a keyword match; the per-step-type caching mitigation is unproven | Design decision + caching spike (§9.2) |
| **3** | Challenge-nonce → non-coder confirmation gesture | The paste-back is built for a developer; the unspoofable non-coder gesture (typed confirm / re-auth / 2FA) needs design (§7.2) | Spec + UX decision |
| **4** | Posture composition across multiple humans | When many stakeholders share one objective, how postures compose (loom's `min(operator, floor)` + 4-eyes upgrade) is unspecified; touches moat M3 | Spec decision |
| **5** | Three buttons hide engine states | No `TOOL` co-plan rung in the UI — a deliberate v1 narrowing | Recorded limitation (§1.2) |
| **6** | Default-posture polarity per tenant | COC defaults full trust; EATP/PACT default supervised; the right default varies by tenant trust tier | Business-model-aligned decision (§10) |
| **7** | Facade-orphan discipline on the hot path | PACT's managers are easy to wire-but-never-call; an un-called governance manager is a silent security hole | Enforce `orphan-detection.md` / `facade-manager-detection.md` — real call site + Tier-2 test per manager |
| **8** | The live event bus is single-process | PACT's event bus is in-memory (one process); a multi-replica deployment needs a durable/distributed bus | Infrastructure stream |

The top three decide whether the M2 control is **usable** by its target audience. The engine is tractable; legibility-for-non-coders is the frontier.

---

## 14. Relationship to the other moats

- **M1 (transparent, versioned, intervene-from-any-step)** — M2 is its governance half. M1's provenance ledger records every step; M2 decides which steps pause and who approves. The `plan_proposed` card (§4.3) and the signed posture anchors (§7.4) are shared primitives. M2 ships first; M1's cascade-recompute engine (changing downstream outputs while versioning old ones) is the harder, later build.
- **M3 (multi-human + agent shared substrate)** — posture composition across stakeholders (§13 #4) is where M2 meets M3; the D/T/R accountability grammar (§11) is the substrate both lean on.
- **M4 (governed cross-org artifact exchange)** — the envelope's data_access + communication dimensions (§3.1) and the clearance ceiling are the controls that will later govern what may cross an org boundary; M2 builds the per-objective enforcement M4 reuses.

---

## 15. How M2 plugs into the comms wedge

The comms flow is `Message → Classification → RAG-retrieval → Response → (auto-send | Escalation)` (`message-routing.md`, `response-accuracy.md`). Each is an action the governance engine can check; "auto-send vs escalate" is exactly a posture+envelope decision (auto-send under "Go ahead" within scope; escalate-for-approval under "Ask me once" or when the spend/sensitivity threshold trips). The comms product's existing "escalation when unsure" behaviour (`response-accuracy.md` Option C) is a HOLD by another name. **Wiring M2 to the comms wedge in observe-only (SHADOW) mode is the natural first proof** — it demonstrates posture-graded governance on a real 4-step flow before generalising to arbitrary multi-agent objectives, and cannot break the live product because SHADOW never blocks.

---

## 16. Out of scope

- **Cascade-recompute / rewind-and-re-run** (changing downstream outputs when a prior step is changed) — this is moat M1's net-new engine, built on the anchor chain + `AgenticArtifact` versioning; it is a separate spec (Research 04 §6.3).
- **Multi-human posture composition** — moat M3; the loom multi-operator `min(operator, floor)` + 4-eyes model is the starting point but the per-objective multi-stakeholder semantics are unspecified (§13 #4).
- **Agent↔agent message transparency as first-class interveneable records** — requires a new `AgenticMessage`-style model + EventBridge hook; not part of the M2 posture/governance core (Research 03 §8.4 item 4).
- **The shipped comms wedge** — covered by the seven existing specs listed in the status blockquote.

> Splitting note: if §3 (envelopes) + §4 (decision-surfacing) + §12 (data models) grow as the presentation layer is designed, §4 and §12 would split into `governance-approval-surface.md` and `governance-data-models.md`, leaving this file as the posture-ladder + lifecycle + safety-floor authority.

---

## 17. Source ledger

- **`briefs/01-vision.md`** §3e (posture / HITL / HOTL / permission envelopes / decisions surfaced beforehand), §3f (traceability boundary), §4 Decisions A/B.
- **`workspaces/future-of-work/01-analysis/01-research/04-eatp-trust-posture.md`** — §0 (three realisations + 80% finding), §1 (canonical L1–L5 + numbering trap + 3-button mapping), §2 (TrustPlane, gradient, BudgetTracker, PostureStore), §3 (HITL/HOTL + keyword-classifier caveat), §4 (set/downgrade/upgrade/challenge-nonce/anchors), §5 (structural vs execution gates), §6 (synthesis, three gaps, recommended architecture), §7 (open questions).
- **`workspaces/future-of-work/01-analysis/01-research/03-pact-governance.md`** — §2 (D/T/R accountability + traceability boundary), §3 (envelopes + five dimensions + monotonic tightening + execution-time check), §4 (clearance + verification gradient), §5 (SupervisorOrchestrator / ApprovalBridge / EventBridge / EmergencyBypass / EnforcementMode / PlanSuspension), §6 (17 data models), §8 (synthesis: 80/15/5, two posture vocabularies, facade-heaviness caution).
- **`workspaces/future-of-work/02-plans/04-trust-posture-permissions-plan.md`** — the M2 build plan (3-button mapping, per-objective keying, plan_proposed + USER trigger, AI-judged classifier, SHADOW rollout, safety floor, sharding).
- **Ecosystem DNA:** eatp/`TrustPlane`/`BudgetTracker`/`PostureStore` (`/Users/esperie/repos/loom/kailash-py`); pact D/T/R + envelopes + SupervisorOrchestrator/ApprovalBridge/EventBridge/EmergencyBypass (`/Users/esperie/repos/terrene/contrib/pact`); aegis posture L1–L5 + signed anchors (`/Users/esperie/repos/dev/aegis`); loom artifact lifecycle (`/Users/esperie/repos/loom`).
- **COC rules:** `communication.md` / `recommendation-quality.md` (plain language), `agent-reasoning.md` (no keyword routing in agent decision paths), `orphan-detection.md` / `facade-manager-detection.md` (hot-path call site + test per manager), `spec-accuracy.md` (this is a target-state spec — see status blockquote).
