# Plan 04 — Trust, Posture & Permissions (M2: the ship-first foundation)

> **What this plan is.** The brief asks for a control where, **before** an agent does a
> piece of work, the user picks how much rein the agent gets — _go ahead_, _ask me once_,
> or _step through with me_ — and the agent then surfaces its plan, waits where it must,
> stays inside a spending and scope budget, and records every move so it can be replayed
> and audited. This is **moat M2** in the strategic spine: governance set _before_
> execution, per objective, not bolted on as after-the-fact observability. The spine's
> instruction is to **ship M2 first** — it is the most-proven of the four moats and the
> foundation the rest stand on. This plan turns the research into a decision-grade build
> plan a non-technical founder can act on.
>
> **Audience & style.** Written for a founder deciding what to build and in what order.
> Plain language throughout; every technical term is translated on first use (per
> `.claude/rules/communication.md`). Effort is in **autonomous execution cycles** — work
> an AI agent system completes in a focused session, not human-days (per
> `.claude/rules/autonomous-execution.md`). Recommendations are single picks with
> symmetric pros and cons (per `.claude/rules/recommendation-quality.md`).
>
> **Grounding.** Synthesised from three files read in full:
> `01-analysis/01-research/04-eatp-trust-posture.md` (the L1–L5 posture machinery,
> HITL/HOTL, BudgetTracker, PostureStore, challenge-nonce), `01-analysis/01-research/03-pact-governance.md`
> (envelopes, the verification gradient, SupervisorOrchestrator / ApprovalBridge /
> EventBridge / EmergencyBypass, the 17 DataFlow models), and
> `01-analysis/07-transparency-intervention-architecture.md` (the four-layer stack, the
> posture-surfacing surface, the traceability-not-accountability boundary). It also draws
> on the brief (`briefs/01-vision.md` §3e–3f) and the strategic spine. Every load-bearing
> claim cites one of these. Genuine uncertainty is flagged, not smoothed over.

---

## 0. The plan in one paragraph

Build the M2 control as a **thin product layer over machinery that already exists**. The
engine that decides "is this agent allowed to do this right now, and if not, who says
yes?" is shipped — it is the PACT governance stack (envelopes + a four-level
auto-approve/flag/hold/block decision + an approval queue surfaced on screen) sitting on
top of the EATP trust plane (a persisted, signed, auto-downgrading L1–L5 posture state
machine + a per-objective spending tracker). The work is **not** to rebuild any of that.
The work is four bounded pieces: (1) **re-key** the posture state machine from "one
posture per code repo" to "one posture per objective"; (2) **surface the agent's plan as
an approvable object before it runs**, gated by the chosen posture; (3) **replace one
keyword-matching classifier with an AI-judged one** (Sequor's own rules forbid keyword
routing in agent decisions); and (4) **render the whole thing in plain language for
non-coders**. Across these, ~80% is reuse, ~15% is integration glue, ~5% is genuinely
new (Research 03 §8.5). The single biggest risk is not the engine — it is making the
control **legible to a non-coder**, and that is a design problem, not an engineering one.

---

## 1. The canonical L1–L5 posture ladder — and the numbering trap

A **posture** is a setting that says how much the agent may do on its own before it has to
stop and ask. There is an industry-standard five-rung ladder for this — it already ships
across the ecosystem as a real, persisted, signed software object (the EATP SDK's
`TrustPosture` enum, Research 04 §1.1). This is the engine's source of truth. The five
rungs, from least to most autonomy:

| Rung (autonomy level) | Engine name (canonical) | What the agent may do | The human's role |
| --- | --- | --- | --- |
| **5** | `AUTONOMOUS` | Acts on its own within the agreed scope | Watches remotely; can abort |
| **4** | `DELEGATING` | Acts on its own; checks in at boundaries | Monitors in real time |
| **3** | `SUPERVISED` | Proposes each action; human approves each one | Approves every action |
| **2** | `TOOL` | Co-plans, then executes the approved plan | Co-plans, approves the plan |
| **1** | `PSEUDO` | Interface only; the human does the reasoning | Does all the reasoning |

Source: `01-research/04-eatp-trust-posture.md` §1.1, grounded in the live SDK source
`kailash-py/.../trust/posture/postures.py`. The engine's default is rung 2 (`TOOL`,
"start supervised") per the CARE spec (Research 04 §1.1, §4.1) — the safe enterprise
default we will inherit (§9 below).

### 1.1 The numbering trap the brief walks into — flag it loudly

There are **three** numbering conventions in the ecosystem and they do **not** line up.
The brief's worked example (`briefs/01-vision.md` §3e) names only three rungs —
**L5 Autonomous**, **L4 Supervised**, **L3 Step-by-step** — and they collide with the
canonical engine labels (Research 04 §1.4, restated in Plan 07 §4.2):

- The brief calls **L4 "Supervised"** and means "ask for **one** permission before
  executing." But in the engine, **"Supervised" is rung 3**, where the human approves
  **every** action — the opposite of "one permission." If we ship the brief's labels as
  the engine's names, every engineer who knows the existing system reads them backwards.
- The brief's **L3 "Step-by-step"** ("pause at each step") behaviourally matches the
  engine's rung 3 (`SUPERVISED`, hold-every-action) — not a middle "shared-planning"
  rung. So the brief's L3 and its L4 sit on the wrong side of the engine's "Supervised."

There is also a separate, **inverted** ladder used for governing the coding agents that
build _this product_ (the COC repo-posture ladder, where `L5` is the _top_ and downgrades
fire on rule violations — Research 04 §1.2). That ladder is real but it is **not** the
end-user control; it governs the codegen, not the customer's work (§8 below).

### 1.2 Recommendation — engine truth internal, three plain buttons external

**Recommendation: adopt the canonical EATP five-rung enum as the internal source of truth,
and present the user three plain-language buttons mapped onto it.** The user never sees
"L5_DELEGATED"; they see three choices. Do **not** ship the brief's L3/L4/L5 labels as the
enum (Research 04 §1.4; Plan 07 §4.2).

| User-facing button | Internal engine posture | Per-step behaviour | Human's relationship |
| --- | --- | --- | --- |
| **"Go ahead"** | `AUTONOMOUS` (5) | Auto-approve inside the scope; anything outside is blocked | On the loop — watches, can abort |
| **"Ask me once"** | `DELEGATING` (4) | Auto-approve inside the scope; **one** approval at the plan→do boundary | On the loop + one checkpoint |
| **"Step through with me"** | `SUPERVISED` (3) | Every consequential action pauses for approval | In the loop — blocks each step |

Rung 1 (`PSEUDO`) and the block-everything floor stay in the engine as the **system's
automatic downgrade target** when something goes wrong — they are not user buttons
(Research 04 §1.4).

**Pros.** The engine stays the shipped, tested, signed primitive — zero re-derivation. The
user sees three honest choices in their own words. The naming collision is contained at the
presentation boundary, where it costs nothing, instead of leaking into the codebase, where
it would confuse every reader forever.

**Cons (real, not glossed).** Three buttons expose fewer states than the engine has, so a
power user cannot reach rung 2 (`TOOL`, "co-plan first") from the UI — acceptable for v1,
but a deliberate narrowing we should record. And the mapping is a **convention we must
document and pin**, or a future contributor re-introduces the collision; the mapping table
above becomes a spec section, not folklore (Research 04 §7 item 8).

**Effort.** The mapping itself is a lookup table — trivial. The cost is the discipline of
writing it down once and grep-pinning it. **< 1 cycle.**

---

## 2. HITL vs HOTL — and why the posture choice _is_ the choice between them

Two terms recur in the brief (§3e). Translated:

- **HITL — "human in the loop":** the human is a **blocking node inside the work path**.
  The agent _cannot proceed_ past a consequential action without the human. This is the
  "Step through with me" posture.
- **HOTL — "human on the loop":** the human is a **monitor outside the work path**. The
  agent proceeds; the human watches and can intervene or abort, but does not gate each
  step. This is the "Go ahead" and "Ask me once" postures.

The crucial finding (Research 04 §3, §5; Plan 07 §4.3): **the posture level _is_ the choice
between HITL and HOTL — it is not a separate control.** Picking "Step through with me" puts
the human _in_ the loop; picking "Go ahead" puts them _on_ it. The selection is mechanical
— the engine's per-action decision rule already encodes it (Research 04 §3, read directly
from PACT's `posture_enforcer.py`):

```
SUPERVISED   (3) : every consequential action → HOLD for approval     → HITL
DELEGATING   (4) : inside scope auto-approve; one boundary → HOLD      → HOTL + one gate
AUTONOMOUS   (5) : inside scope auto-approve; outside scope → BLOCK    → HOTL (remote)
```

So the three buttons sit exactly across the seam between "human approves each step" and
"human watches and can stop it." The user's button choice is, under the hood, a choice over
**which class of gate blocks the agent** (Research 04 §5; Plan 07 §4.3):

- **Structural gates** (approve-the-plan, authorise-a-release, change-the-scope) — these
  stop the agent even at high posture. A human _must_ act here.
- **Execution gates** (the agent doing the analysis, drafting, assembling correctly) —
  these auto-converge at high posture; at low posture they also become blocking.

**Implication for the product.** We do not build "a HITL mode" and "a HOTL mode" as two
features. We build **one posture control**, and HITL-vs-HOTL falls out of it. That halves
the surface area and removes a whole class of "the two modes disagree" bugs.

---

## 3. Operating envelopes — the scope/budget/clearance the posture runs inside

A posture says _how often the human is asked_. An **envelope** says _what the agent is
allowed to touch at all_ — its scope, its spending limit, and what data it may read. The
two are orthogonal and both ship today (Research 03 §3). The envelope is the brief's
"permission envelope."

### 3.1 What an envelope constrains — five dimensions

A PACT envelope (`ConstraintEnvelopeConfig`, Research 03 §3.2) carries five blocks:

| Dimension | Constrains (plain language) |
| --- | --- |
| **financial** | How much it may spend; the amount above which it must ask first |
| **operational** | Which actions are allowed / blocked; how many actions per hour/day |
| **temporal** | When it may run (working hours, blackout periods) |
| **data_access** | Which files/data it may read or write; data types it may never touch (e.g. PII) |
| **communication** | Internal-only vs external; which channels; external-needs-approval |

Plus a **clearance ceiling** (how sensitive a document it may read) and a
**max-delegation-depth** (how many layers of sub-agents it may spin up — directly relevant
to the brief's "agent spins up 3 agents").

### 3.2 The load-bearing safety property — delegation can only tighten

The central invariant (Research 03 §3.3; EATP delegation rule, Research 04 §2.1): **a
child envelope can only be equal to or more restrictive than its parent.** A manager with
a \$50K limit can hand an agent \$10K, never \$75K. When the brief's agent spins up three
sub-agents for the 3Q report, each sub-agent inherits a _tightened_ slice of the parent's
envelope — it can only ever do _less_ than the objective was granted, never more. This is
checked structurally, not by trust. The same rule governs posture: a step **inherits ≤ the
objective's posture**, never above it (Research 04 §6.2 Gap A) — a sub-task cannot promote
itself to "Go ahead" if the objective was set to "Step through with me."

### 3.3 How the envelope is checked at execution time — reuse, don't rebuild

The single decision call is `engine.verify_action(role, action, context)` (Research 03
§3.4), which already: computes the effective envelope **with a version fingerprint** (so
the system can tell the envelope changed between when a step was planned and when it runs —
the load-bearing field for "retrace and intervene"), evaluates the action against all five
dimensions, walks the accountability chain (most-restrictive verdict wins), and emits an
audit anchor. This call is the spine of execution-time checking and is reused wholesale.

**Per-objective envelope-by-posture defaults already exist** (Research 03 §3.5): the engine
ships a `default_envelope_for_posture()` mapping (PSEUDO → \$0/read-only; SUPERVISED →
\$1,000/read-write-plan; DELEGATING → \$10,000/+execute; AUTONOMOUS → \$100,000/+approve).
The product gives the user a sensible default the moment they pick a button, then lets them
narrow it.

**Effort.** Envelope machinery is fully reused; the new work is wiring a **per-objective
envelope record** the per-action checker reads, and rendering the five dimensions in plain
language ("spend up to \$200 without asking", not `requires_approval_above_usd: 200`).
**~1 cycle** for the wiring; the plain-language rendering folds into the §7 UX work.

---

## 4. The decision-surfacing + approval UX — surface the plan _before_ it runs

This is the heart of M2 and the part the brief is most specific about (§3e): the agent
decides to spin up three agents, and **that decision is shown on screen and recorded, and
the user has chosen a posture beforehand.** The key move — and the one genuinely-new piece
of wiring here — is that the agent's **plan** (the fan-out: 3 sub-tasks, what each does,
the estimated cost) is captured as an **approvable object and shown to the user _before any
of it executes_** (Research 04 §6.1; Plan 07 §4.1).

### 4.1 The pipeline already exists end-to-end — wire it, don't build it

The brief's "surface the decision, pause, await the human" loop is **shipped code**
(Research 03 §5, read directly):

- **`SupervisorOrchestrator`** is the top-level entry point that turns a submitted
  objective into governed work. When per-action checking returns **HOLD** (a soft limit
  was crossed, or the posture demands approval), its `_PlatformHeldCallback` **creates an
  approval record and returns `False` to block the action until a human approves** (Research
  03 §5.1). That single `return False` _is_ "the agent pauses and asks for one permission,"
  realised in code.
- **`ApprovalBridge`** turns each HOLD into a durable, queryable, human-resolvable row:
  `create_decision()` → a pending decision; `approve()` / `reject()` records who decided,
  when, and why; `get_pending()` feeds the on-screen approval queue (Research 03 §5.2).
- **`EventBridge`** streams the agent's plan, holds, and costs to the screen in real time
  over a live connection: `on_plan_event` (per scheduled sub-task), `on_hold_event` ("a
  decision needs you"), `on_cost_event` (Research 03 §5.3). This is the existing realisation
  of "decisions surfaced on screen, recorded."

So "show the plan, pause, record, await the human" maps almost 1:1 onto shipped primitives.

### 4.2 What is genuinely new here — and it is small

Two small additions (Research 04 §6; Plan 07 §4.1; Research 03 §8.4):

1. **A `plan_proposed` decision type.** Today the system surfaces a HOLD when a step is
   _near a limit_. We add a decision type that surfaces the **plan itself** — the fan-out —
   as the approvable object, before execution. The user sees "here is what I'm about to do:
   3 sub-tasks, est. \$X" as an inspectable card. _~1 cycle of integration._
2. **A `USER` pause trigger.** The existing pause mechanism (`PlanSuspension`, Research 03
   §8.3) suspends on budget/time/posture/envelope triggers but has **no user-initiated
   pause** — the trigger list is governance-only. We add a `USER` trigger so a person can
   say "stop here" mid-flight. _Small — one new trigger value + one route._

The posture choice then decides whether the `plan_proposed` card **auto-approves** ("Go
ahead"), **needs one approval** ("Ask me once"), or **pauses at every consequential step**
("Step through with me").

### 4.3 The plain-language rendering of holds — net-new, but bounded

The engine's holds are legible to engineers (`constraint_dimension=financial,
requires_approval_above_usd=200`). The brief's user is a non-coder. We add a **verdict →
prose renderer** (Research 03 §8.4 item 6) that turns that into: _"This step would spend
\$240, above your \$200 auto-approve limit — approve?"_ with **Approve / Edit / Reject**.
The rows already exist; the rendering is new and aligns with `rules/communication.md`.
_Small._

**Why this is the right shape.** We are not building an approval system. We are putting a
non-coder face on an approval system that already pauses, records, and awaits. The risk
moves from "can we build the engine?" (no — it ships) to "can a non-coder understand the
card?" (the real question, §10).

---

## 5. Budget ceilings — cost-per-objective with early warnings

The brief lists budget ceilings as part of the control. This is fully shipped as the EATP
`BudgetTracker` (Research 04 §2.3, grounded in
`kailash-py/.../trust/constraints/budget_tracker.py`):

- **Integer microdollars** (1 USD = 1,000,000 µ\$) — no floating-point drift; threshold
  checks are exact integer arithmetic.
- **Reserve-then-record, fail-closed** — it reserves an estimated cost before doing work
  (returns `False`/refuses if insufficient) and records the actual cost after. The safe
  direction is guaranteed: it may briefly _over_-report remaining budget, but **never
  denies a spend that should have been allowed.**
- **Threshold callbacks at 80% / 95% / exhausted**, each firing at most once — the hooks
  for "you're approaching your limit" warnings surfaced to the user.
- **Crash-safe persistence** (write-ahead logging, per-thread connections, 0600 file
  perms, parameterised SQL, validated tracker IDs) — survives restarts.

**For the product.** A per-objective `BudgetTracker(tracker_id="obj-<id>")` gives **a
spending ceiling per piece of work**, with 80/95/exhausted alerts surfaced to the user, and
its `budget_status` dict (`session_cost / remaining / utilization`) is a ready-made
progress widget. "Cost per turn" maps to a per-action cap; "objective budget" to a
per-session cap — both exposed by the envelope (Research 04 §2.3). Crossing the
"ask-first-above" amount flips the verdict to HOLD, which spawns an approval card (§4).
**Effort: reuse the tracker; ~1 cycle to wire per-objective trackers + the progress
widget.**

---

## 6. Emergency bypass with audit — the accountable "break glass"

The brief asks for an emergency-bypass with audit. This is the most security-hardened
component already shipped — `EmergencyBypass` (Research 03 §5.4, the file is ~1,000 lines,
read in full). A senior human can grant a **time-limited expansion** of the agent's
permissions for a genuine emergency, and the design makes it impossible to abuse quietly:

- **Tiered and time-bounded** — 4h (tactical) / 24h (extended) / 72h (crisis). Anything
  over 72h is **refused**: "emergencies over 72 hours must be re-authorised through normal
  governance every 72 hours."
- **Cannot grant more than the approver holds** — the expanded envelope is validated against
  the approver's _own_ envelope across all five dimensions (no privilege escalation).
- **Cannot be granted by someone structurally junior** — the approver's position in the
  accountability chain must match the tier.
- **Rate-limited atomically** — max 3 per week, 4h cooldown, enforced across processes so
  two workers cannot race past the limit.
- **Fail-closed audit** — if the audit record cannot be written, **bypass creation aborts**:
  "governance mutations require an audit trail."
- **Mandatory post-incident review** — every bypass schedules a review 7 days out; overdue
  reviews are surfaced.

**For the product.** This is the "break glass" path that stays accountable. We **reuse it
wholesale**; the only product work is a senior-facing surface to request a bypass and a
plain-language rendering of its terms ("expanded permissions for 4 hours; auto-reviewed in
7 days"). **Effort: reuse; <1 cycle for the surface.**

---

## 7. How posture is set, upgraded, and recorded — a verifiable state machine

The brief wants posture **set/upgraded beforehand** and **recorded as a verifiable state
machine**. Both halves ship.

### 7.1 Set / default / downgrade (automatic) / upgrade (human-gated)

- **Set & default** — the persisted posture state machine (`PostureStateMachine` +
  `SQLitePostureStore`, Research 04 §2.4) holds the posture, defaults to the safe
  enterprise base (start supervised), and records every transition. It is keyed by an
  `agent_id` today — we re-key to `objective_id` (§8 Gap A).
- **Downgrade is automatic and system-gated** — repeated problems instantly drop the agent
  to the most restrictive posture (`emergency_downgrade()` jumps straight to rung 1,
  Research 04 §2.4, §4.2). This is the **safety floor** that makes "Go ahead" safe to offer:
  it is not a blank cheque, it is a ceiling the system can lower the instant something looks
  wrong.
- **Upgrade is human-gated** — the governing principle (the "Mirror Thesis," Research 04
  §1.2, §4.3): **upgrades are human-gated; downgrades fire automatically.** The human is the
  structural gate for _more_ autonomy; the system is the structural gate for _less_.

### 7.2 The challenge-nonce — why upgrade needs a fresh human keystroke

The brief specifically asks about the **challenge-nonce**. A "nonce" is a one-time random
code. The COC upgrade ceremony (Research 04 §4.3, from `commands/posture.md`) works in two
steps: the user requests an upgrade; the system writes a random nonce to a hook-readable
file and prints _"to confirm, paste this code in your next message: `<NONCE>`"_; the user
pastes it and re-runs the upgrade with the code. The system verifies the user's _prior
turn_ actually contained the literal nonce before recording the upgrade.

**Why the paste-back exists** (Research 04 §4.3): "a human gate alone is forgeable — the
agent can invoke the approval command itself." The nonce forces a **fresh human keystroke
into the transcript that the agent cannot synthesise.** It is the structural defence against
an agent self-promoting.

**Implication for the end-user product.** The nonce ceremony is designed for a _developer_
typing slash-commands. For a non-coder picking a button, the equivalent is a deliberate,
unspoofable confirmation gesture — a typed confirmation, a re-authentication, or a
second-factor tap — that the agent cannot perform on the user's behalf (Research 04 §6.2;
Plan 07 §4.2). The _principle_ transfers exactly (the agent must not be able to grant itself
more rein); the _mechanism_ is re-skinned from "paste this code" to a UI gesture. **This is
a design decision to record, not a hard build.**

### 7.3 Recorded as a verifiable state machine — two layers, use both

The brief's "recorded as a verifiable state machine with anchors" is satisfied by two
existing layers (Research 04 §4.5; Plan 07 §3.2):

1. **The posture state file** — an append-only transition history where each entry's "from"
   must equal the previous entry's "to" (chain-consistency enforced), and **direct edits are
   blocked** — only the hooks may write it. This is the live, auditable state.
2. **The cryptographic anchors** — the aegis posture-transition anchors
   (`anc-posture-*.json`, read directly): each anchor names its `parent_anchor_id`
   (a hash-chain back-pointer), carries a SHA-256 `record_hash` of the transition, and an
   Ed25519 `signature`. Modifying any record invalidates the chain forward — this is the
   tamper-evident, replayable history the brief's §3f wants. EATP's own signing primitives
   produce these.

Together: every posture change is **attributable** (who), **ordered** (the chain), and
**tamper-evident** (the signature). **Effort: reuse the state file + anchor format;
~1 cycle to wire the anchor emission on the per-objective posture transitions.**

### 7.4 The honesty caveat that must travel with every trust claim

Both Research 03 (§2.3) and Research 04 (§2.2) surface the same line, and it must appear in
any product or marketing copy: **the system delivers _traceability_, not _accountability_.**
Traceability — every action traces back to its inputs, decisions, and the human authority
that permitted it — the machine guarantees this. Accountability — that a human actually
_understood_ and bears the consequences — no software can guarantee this. The posture +
surfacing UX converts traceability into a _chance_ at accountability; it cannot force
understanding. Over-claiming here is dishonest and legally hazardous.

---

## 8. The gap — "posture as a repo rule for coding agents" vs "posture as a live end-user control"

This is the precise question the brief poses, and the cleanest way to see what is reused vs
net-new. There are two _different_ posture systems in the ecosystem that look alike and must
not be conflated (Research 04 §1.2, §6.2; Research 03 §8.2):

- **The COC repo-posture** governs **the coding agents that build _this product_.** It is
  one posture per code repo, it _starts at full trust_ (a trusted operator's repo), and it
  _auto-downgrades on detected rule violations_. The brief borrows its **vocabulary**
  ("L3/L4/L5") but not its meaning. This system **stays exactly where it is** — it is the
  meta-governance of the codegen, not the customer-facing control (Research 04 §6.2 Gap C).
- **The end-user posture** the brief actually wants is a **per-objective, user-set,
  step-pausing control** over the agent doing the customer's work. This is the PACT/EATP
  polarity — _the human sets trust over the agent, beforehand, per task; the agent surfaces
  and waits._

The three sub-gaps between them (Research 04 §6.2), with effort:

| Gap | Today (coding-agent posture) | Needed (end-user posture) | Reuse vs net-new | Effort |
| --- | --- | --- | --- | --- |
| **A — Keying** | One posture per repo | One posture per **objective**; intervention per **step** | The state machine is already keyed by an ID — **re-key** `agent_id` → `objective_id`; steps tighten via the inherit-only rule (§3.2). PACT already operates per-action. | **~1 cycle** |
| **B — Audience** | Surfaced to a _developer_ via slash-commands; assumes the reader understands `L4_CONTINUOUS_INSIGHT` | Surfaced to a _non-coder_: three plain buttons, Approve/Edit/Reject cards, a timeline | Engine unchanged. **Presentation layer is net-new** (PACT's web objectives/approvals screens are the starting scaffold). | **The bulk of the work — multiple cycles** |
| **C — Polarity** | Agent governs _itself_ (default full trust, downgrade on self-detected violation) | User governs _the agent_ (default supervised, user opts up) | A **default choice**, not code: adopt the PACT/EATP "start supervised" default; keep the COC violation-driven downgrade as the **safety floor** — operative posture = `min(user-chosen, system-floor)`. | **A decision + small wiring** |

**The one-line summary of reuse vs net-new.** Reused: the posture state machine, the
spending tracker, the five-dimension envelope, the four-level decision gradient, the
approval queue, the live event stream, the emergency bypass, the signed audit anchors, the
17 work-tracking data models. Net-new: the per-objective keying glue (small), the
`plan_proposed` decision type + `USER` pause trigger (small), the AI-judged classifier
(small, §9.1), and the **non-coder presentation layer (large)**. This matches the spine's
~80/15/5 reuse/glue/new split (Research 03 §8.5).

---

## 9. The recommended v1 posture model

**Recommendation.** Ship M2 as: **the canonical EATP five-rung engine, internal; three
plain-language buttons, external; per-objective keying; PACT's surface-and-approve pipeline
with a `plan_proposed` card and a `USER` pause; per-objective budget ceilings with 80/95/
exhausted alerts; emergency-bypass reused as-is; signed posture anchors for the verifiable
history; default to "supervised," user opts up via an unspoofable confirmation gesture;
and operative posture = `min(user-chosen, system-floor)` as the safety floor.** Roll it
under the existing comms wedge in **observe-only mode first** (below).

### 9.1 The two integration decisions baked into the recommendation

1. **Replace the keyword classifier with an AI-judged one.** PACT decides "is this action
   consequential?" by **matching keywords** (`write`, `send`, `delete`…) — and Sequor's own
   rules **forbid** keyword/regex routing in agent decision paths (`agent-reasoning.md`,
   CLAUDE.md Directive 6; Research 04 §3; Plan 07 §4.4). We keep PACT's _verdict_ machinery
   (pause/block/auto-approve) but replace its _decision path_ with an **AI-judged**
   consequentiality assessment — the model judges whether an action is consequential, the
   model is the classifier. Research 04 calls this "a small, well-scoped rewrite, not a
   re-architecture." It carries a real cost/latency tradeoff (an AI call on _every_ action
   vs an instant keyword match) — the mitigation (judge once per step-type, cache the
   verdict shape) is itself unproven at scale and is flagged in §10.
2. **Roll out in observe-only mode first.** The engine has an `EnforcementMode.SHADOW`
   setting — it runs the full governance and logs what it _would_ have held or blocked, but
   **never actually blocks** (Research 03 §5.5). This is how governance slots under the live
   Sequor comms product **without breaking it**: observe what would be held/blocked,
   calibrate the envelopes and thresholds, _then_ turn on the teeth. Strongly recommended
   for the wedge rollout.

### 9.2 Effort headline

Because ~80% is reuse, the M2 control over the **comms-wedge flow** (the existing 4-step
message → classify → retrieve → respond path) is achievable in a **small number of
autonomous cycles**: the engine, posture machine, budget tracker, approval pipeline, and
event stream are wired, not rebuilt. The per-objective keying, `plan_proposed` card, `USER`
trigger, AI-judged classifier, and budget widget are each ≤1 cycle and several have a live
feedback loop (testable against fixtures), so they can run at higher budget per
`autonomous-execution.md`. The **non-coder presentation layer is the open-ended part** —
estimate a first version in a few cycles, but treat it as iterative discovery, not a
one-shot build (§10).

### 9.3 Sharding note (per `autonomous-execution.md` § capacity budget)

The load-bearing pieces are small and separable — shard them so each stays within the
~500-LOC / ≤5–10-invariant ceiling:

- **Shard 1 — per-objective keying** (invariants: posture inherit-only tightening; operative
  = `min(user, floor)`; per-objective default record). Has a live test loop.
- **Shard 2 — `plan_proposed` card + `USER` pause trigger** (invariants: plan surfaced
  before any execution; posture decides auto/once/each-step; user pause halts the path).
- **Shard 3 — AI-judged consequentiality classifier** (invariants: no keyword path remains;
  verdict shape unchanged; cache key is per-step-type and tenant-scoped).
- **Shard 4 — budget ceilings + plain-language verdict renderer** (invariants: fail-closed
  reserve; 80/95/exhausted fire once; renderer leaks no jargon).

Each shard carries a value-anchor citing the brief §3e (per `value-prioritization.md`). The
presentation layer (Gap B) is its own multi-cycle iterative track, not a single shard.

### 9.4 Pros and cons of the recommended model (symmetric)

**Pros.**

- **Highest reuse, lowest reinvention** — the governance engine, posture machine, approval
  queue, budget tracker, and emergency bypass all ship; the new work is keying glue + one
  classifier + a UI (Research 03 §8.5; Plan 07 §7.3).
- **The posture choice unifies HITL/HOTL** — one control, not two modes, halving the surface
  and removing the "two modes disagree" bug class (§2).
- **Safe by construction** — "Go ahead" is a ceiling the system can instantly lower, not a
  blank cheque (the `min(user, floor)` safety floor + auto-downgrade, §7.1).
- **Honest by construction** — the traceability-not-accountability boundary is stated
  crisply, protecting against over-claiming (§7.4).
- **Safe rollout** — observe-only (SHADOW) mode lets governance run under the live comms
  product without blocking anything until calibrated (§9.1).
- **It is the most-proven moat** — the spine's reason to ship M2 first; PACT is the closest
  existing implementation of the brief's exact loop (Research 04 §0).

**Cons (real, not glossed).**

- **The non-coder presentation layer is the dominant unknown** — translating "Supervised,
  envelope_version=…, constraint_dimension=financial" into something a non-coder acts on is
  a design problem no research file resolves. This is where v1 is most likely to underwhelm
  (§10 #1).
- **AI-on-every-action is slower and costlier than a keyword match** — the classifier rewrite
  is required by our own rules, but its caching mitigation is unproven at scale; a step-heavy
  objective could feel sluggish or expensive (§10 #2).
- **PACT is a facade-heavy codebase** — full of managers/bridges/stores. We must enforce
  `orphan-detection.md` / `facade-manager-detection.md`: every governance manager we wire in
  needs a **real call site on the hot path + an integration test**, or it becomes a security
  promise that silently never executes (the exact Phase-5.11 failure those rules exist to
  prevent — Research 03 §8.5). The intervention UX must _actually call_ the pause/hold
  machinery on the live path, not just expose it.
- **Posture composition across multiple humans is unspecified** — the brief is
  team-oriented (§3d); when many stakeholders share one objective, how postures compose is
  an open spec decision (§10 #4), and it touches the multi-human moat M3.
- **Three buttons hide engine states** — a deliberate narrowing (no `TOOL` co-plan rung in
  the UI); acceptable for v1 but recorded as a known limitation (§1.2).

### 9.5 The alternative considered and rejected

**Build a bespoke posture/governance/approval system from scratch.** Rejected: it discards
~80% of working, tested, signed code (the posture state machine, budget tracker, approval
queue, envelope intersection, emergency bypass); it would re-derive the cryptographic
anchoring and the four-level verdict logic; and it conflicts with the spine's
capability-first reuse stance. The only argument for it — "a clean room avoids PACT's
facade-heaviness" — is better met by **enforcing the orphan-detection rules on the reused
code** than by rewriting it (Plan 07 §7.4).

---

## 10. The highest-risk unknowns (flagged, not resolved)

Per the analyst discipline and `spec-accuracy.md`, these are genuine uncertainties a
spec/redteam phase must resolve. Ranked by how likely they are to sink M2's _usability_
(not its buildability — the engine is the tractable part).

| # | Unknown | Why it's hard | Where it resolves |
| --- | --- | --- | --- |
| **1** | **Non-coder rendering of postures, holds, and envelopes** | Turning "Supervised / constraint_dimension=financial / envelope_version" into a control a non-expert acts on is an unsolved design problem; it is the dominant M2 usability risk | UX design + user testing; treat as iterative discovery (§9.2) |
| **2** | **AI-classifier latency/cost** | An AI call on every consequentiality check is slower and costlier than a keyword match; the caching mitigation is unproven (Research 04 §7 item 5; Plan 07 §10 #4) | Design decision + a spike on per-step-type caching |
| **3** | **The challenge-nonce → non-coder confirmation gesture** | The paste-back is built for a developer; the unspoofable, agent-can't-fake confirmation for a non-coder (typed confirm / re-auth / 2FA tap) needs design (§7.2) | Spec + UX decision |
| **4** | **Posture composition across multiple humans** | The brief is team-oriented; when many stakeholders share one objective, how postures compose (the loom model is `min(operator, floor)` + 4-eyes upgrade) is unspecified (Research 04 §7 item 4) | Spec decision; touches moat M3 |
| **5** | **Posture naming/label unification** | Three colliding ladders; shipping the brief's labels as the engine enum confuses every reader (§1.1) | Spec decision — adopt canonical enum internally, three buttons externally (Research 04 §1.4) |
| **6** | **Default-posture polarity per tenant** | COC defaults to full trust (trusted operator); EATP/PACT default to supervised (enterprise). The right default likely varies by tenant trust tier (Research 04 §7 item 6) | Business-model-aligned decision |
| **7** | **Facade-orphan discipline on the hot path** | PACT's managers are easy to wire-but-never-call; an un-called governance manager is a silent security hole (Research 03 §8.5) | Enforce `orphan-detection.md` — real call site + Tier-2 test per manager |
| **8** | **The live event bus is single-process** | PACT's event bus is in-memory (one process); a multi-replica deployment needs a durable/distributed bus (Plan 07 §8 #6) | Infrastructure stream |

The top three decide whether the M2 control is **usable** by its target audience. The engine
is the tractable part; legibility-for-non-coders is the frontier. That is the honest shape
of the bet.

---

## 11. How M2 plugs into the comms wedge (Decision A)

The strategic spine folds the existing Sequor comms product in as the first vertical. M2
lands there cleanly (Research 03 §5.5; Plan 07 §6.4): the comms flow is `Message →
Classification → RAG-retrieval → Response → (auto-send | Escalation)`. Each is an action
the governance engine can check; "auto-send vs escalate" is exactly a posture+envelope
decision (auto-send under "Go ahead" within scope; escalate-for-approval under "Ask me
once" or when the spend/sensitivity threshold trips). The comms product's existing
"escalation when unsure" behaviour is a HOLD by another name. **Wiring M2 to the comms
wedge in observe-only (SHADOW) mode is the natural first proof** — it demonstrates
posture-graded governance on a real 4-step flow before generalising to arbitrary
multi-agent objectives, and it cannot break the live product because SHADOW never blocks.

---

## 12. Relationship to the other moats

- **M1 (transparent, versioned, intervene-from-any-step work)** — M2 is its governance
  half. M1's provenance ledger records every step; M2 decides which steps pause and who
  approves. The `plan_proposed` card (§4.2) and the signed posture anchors (§7.3) are shared
  primitives. M2 ships first (this plan); M1's cascade-recompute engine is the harder,
  later build (Plan 07).
- **M3 (multi-human + agent shared substrate)** — the open question of posture composition
  across stakeholders (§10 #4) is where M2 meets M3; the D/T/R accountability grammar
  (Research 03 §2) is the substrate both lean on.
- **M4 (governed cross-org artifact exchange)** — the envelope's data-access + communication
  dimensions (§3.1) and the clearance ceiling are the controls that will later govern what
  may cross an org boundary; M2 builds the per-objective enforcement M4 will reuse.

---

## 13. Source ledger

All claims resolve to one of:

- **`briefs/01-vision.md`** §3e (posture / HITL / HOTL / permission envelopes / decisions
  surfaced beforehand), §3f (traceability boundary), §4 Decisions A/B.
- **`01-analysis/01-research/04-eatp-trust-posture.md`** — §0 (three realisations + the 80%
  finding), §1 (canonical L1–L5 + the numbering trap + 3-button mapping), §2 (TrustPlane,
  verification gradient, BudgetTracker, PostureStore), §3 (HITL/HOTL + keyword-classifier
  caveat), §4 (set/downgrade/upgrade/challenge-nonce/anchors), §5 (structural vs execution
  gates), §6 (the synthesis, three gaps, recommended architecture), §7 (open questions).
- **`01-analysis/01-research/03-pact-governance.md`** — §2 (D/T/R accountability), §3
  (envelopes + five dimensions + monotonic tightening + execution-time check), §4
  (verification gradient + clearance), §5 (SupervisorOrchestrator / ApprovalBridge /
  EventBridge / EmergencyBypass / EnforcementMode), §6 (17 data models), §8 (synthesis:
  80/15/5, the two posture vocabularies, PlanSuspension, facade-heaviness caution).
- **`01-analysis/07-transparency-intervention-architecture.md`** — §4 (posture surfacing,
  plan-before-execution, the 3-button mapping, HITL/HOTL, safety floor + emergency path),
  §6 (reuse inventory + the genuinely-new list), §7 (recommendation + symmetric pros/cons),
  §8 (risk register).
- **The strategic spine** — moats M1–M4, "ship M2 first," ~80% reuse, the Cowork threat,
  Decisions A and B.
- **COC rules** — `communication.md` (plain language), `autonomous-execution.md` (cycles,
  not human-days; capacity sharding), `recommendation-quality.md` (symmetric pros/cons),
  `agent-reasoning.md` (AI-first, no keyword routing), `orphan-detection.md` /
  `facade-manager-detection.md` (hot-path call site + test per manager),
  `value-prioritization.md` (value-anchored shards), `spec-accuracy.md` (flag uncertainty,
  don't paper over it).
