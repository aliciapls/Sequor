# Research 03 — PACT Governance: Foundation for Permission Envelopes and Accountability

> Brief objective **3e** — "Pursue PACT/EATP … to see how HITL, HOTL, trust postures, and permission envelopes are used. Make **all human↔agent and agent↔agent communications/working steps transparent and interveneable.**"
>
> This file maps the PACT governance machinery onto the platform's **permission-envelope + intervention** requirement (the "choose a posture beforehand — L3/L4/L5 — surface decisions on screen, retrace any step and intervene" UX). It grounds every claim in source files actually read.

**Sources consulted (read in full or in depth):**

- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/models/__init__.py` (all 17 DataFlow models)
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/__init__.py`
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/orchestrator.py` (`SupervisorOrchestrator`)
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/approval_bridge.py` (`ApprovalBridge`)
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/event_bridge.py` (`EventBridge`)
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/emergency_bypass.py` (`EmergencyBypass`, full)
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/settings.py` (`EnforcementMode`)
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/seed.py`
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/use/services/multi_approver.py`
- `.claude/skills/29-pact/{SKILL,pact-dtr-addressing,pact-envelopes,pact-access-enforcement,pact-governance-engine,pact-enforcement-modes,pact-conformance-features}.md`
- `.claude/skills/co-reference/{governance-layer-thesis,eatp-spec}.md`
- `.claude/rules/trust-posture.md` (the L1–L5 posture ladder COC runs on)
- `/Users/esperie/repos/dev/aegis/.claude/rules/trust-posture.md` + `proj-*/anchors/anc-posture-*.json` (signed posture transitions)

A note on naming: PACT uses **two posture vocabularies** that must not be conflated. The brief's "L3/L4/L5" is the **COC trust-posture ladder** (a per-repo agent-autonomy state machine in `rules/trust-posture.md`). PACT's own `TrustPostureLevel` (PSEUDO/TOOL/SUPERVISED/DELEGATING/AUTONOMOUS, autonomy 1–5) is a **per-role clearance ceiling**. They rhyme deliberately (both come from EATP's five postures) but are different objects. The synthesis section reconciles them.

---

## 1. What PACT is (in one paragraph)

PACT is the Terrene Foundation's **organizational governance framework** for AI agents. It answers one question structurally: _"is this agent, in this org position, allowed to take this action right now — and if not, who has to say yes?"_ It does this with (a) a positional **address grammar** (D/T/R) that encodes both org containment and the accountability chain; (b) **operating envelopes** that constrain agents across five dimensions; (c) a **verification gradient** that classifies every action as auto-approved / flagged / held / blocked; (d) a **knowledge-clearance** model with a 5-step fail-closed access algorithm; and (e) an **engine + L3 platform** that turns a submitted objective into governed, auditable, approval-gated work. PACT is a layer that sits **above** any execution tool (Governance Layer Thesis, `governance-layer-thesis.md`) — it does not execute work; it decides whether work may proceed and records that it did.

---

## 2. D/T/R Accountability Grammar

**D/T/R = Department / Team / Role.** (Confirmed from source: `pact-dtr-addressing.md:8`, `NodeType.DEPARTMENT="D"`, `NodeType.TEAM="T"`, `NodeType.ROLE="R"`.) The brief's shorthand "Decision/Task/Review" is **incorrect** — D/T/R is the _addressing_ grammar. (Decision and ReviewDecision are _data models_, covered in §6.)

### 2.1 The grammar and its core invariant

Every entity has a globally unique positional address. **Core invariant:** every D or T segment must be immediately followed by exactly one R segment — the R is _the accountable person (head)_ for that unit.

```
D1-R1                  # Dept 1, headed by Role 1
D1-R1-T1-R1            # Team 1 under Dept 1, headed by its own Role
D1-R1-D2-R1-T1-R1      # Team in a sub-department
R1                     # standalone role

D1                     # INVALID — D without R → GrammarError
D1-T1-R1               # INVALID — D followed by T, not R → GrammarError
```

This is the key idea for the platform: **accountability is encoded structurally in the address, not attached as metadata.** You cannot name an org unit without naming who is accountable for it.

### 2.2 How accountability is assigned and traversed

The address yields three derived structures (`pact-dtr-addressing.md:81–142`) that the engine uses for every decision:

| Property                 | Meaning                                | Used for                        |
| ------------------------ | -------------------------------------- | ------------------------------- |
| `parent` / `ancestors()` | structural containment chain           | envelope inheritance            |
| `containment_unit`       | nearest ancestor D or T                | "what unit owns this?"          |
| `accountability_chain`   | **all R segments in order, root→leaf** | the chain of accountable people |

The `accountability_chain` is the load-bearing primitive. For `D1-R1-D2-R1-T1-R1` it is `[D1-R1, D1-R1-D2-R1, D1-R1-D2-R1-T1-R1]` — every person who bears accountability for the leaf role, from the top down. The engine's `_multi_level_verify()` walks this chain and **the most restrictive verdict wins** (`pact-dtr-addressing.md:112`, `pact-governance-engine.md:88`). EmergencyBypass uses the _same_ chain to validate that an approver is structurally senior enough to authorize a bypass (`emergency_bypass.py:621–689` — Tier-1 needs ≥1 level above, Tier-2 ≥2, Tier-3 position 0 or 1).

**Implication for the platform:** when the agent "spins up 3 sub-agents" (the brief's 3Q-report example), each sub-agent can be assigned a D/T/R address whose accountability_chain names the human(s) who must be looped in. Accountability is then _not a UI afterthought_ — it is computable from the address. This is the substrate the brief's "every step is traced to a human" needs.

### 2.3 The traceability/accountability distinction (critical honesty)

EATP (`eatp-spec.md:61–66`) is explicit: **EATP/PACT provide traceability, not accountability.** Traceability = trace any AI action back to a human authority (the machine delivers this). Accountability = a human _understands, evaluates, and bears consequences_ (no protocol delivers this). For the platform this means the governance layer can _guarantee_ every step is attributable to a human; it cannot _guarantee_ that human actually understood it. The intervention UX (surface on screen + pause) is what converts traceability into a _chance_ at real accountability.

---

## 3. Operating Envelopes

### 3.1 The three-layer model

PACT constrains agents with three envelope layers (`pact-envelopes.md:10–17`):

| Layer                  | Type                       | Lifetime                    | Who sets it                       |
| ---------------------- | -------------------------- | --------------------------- | --------------------------------- |
| **Role Envelope**      | `RoleEnvelope`             | standing                    | a supervisor, for a direct report |
| **Task Envelope**      | `TaskEnvelope`             | ephemeral, **auto-expires** | per-task narrowing                |
| **Effective Envelope** | `ConstraintEnvelopeConfig` | computed                    | the engine (intersection)         |

The **Effective Envelope** is computed by walking the accountability_chain root→leaf, intersecting every ancestor's RoleEnvelope, then applying any active (non-expired) TaskEnvelope (`pact-envelopes.md:134–146`, `compute_effective_envelope`). This is the precise mechanism behind "a manager with \$50K can delegate \$10K but not \$75K" (EATP delegation rule, `eatp-spec.md:21`).

### 3.2 What an envelope constrains — five dimensions

A `ConstraintEnvelopeConfig` carries five constraint blocks (`pact-envelopes.md:22–72`, mirrored in `emergency_bypass.py:489–619` and `models/__init__.py:147–149` `ALL_CONSTRAINT_DIMENSIONS`):

| Dimension         | Constrains (examples)                                                                   |
| ----------------- | --------------------------------------------------------------------------------------- |
| **financial**     | `max_spend_usd`, `api_cost_budget_usd`, `requires_approval_above_usd` (← triggers HELD) |
| **operational**   | `allowed_actions`, `blocked_actions`, `max_actions_per_day/hour`                        |
| **temporal**      | `active_hours_start/end`, `timezone`, `blackout_periods`                                |
| **data_access**   | `read_paths`, `write_paths`, `blocked_data_types` (e.g. `pii`)                          |
| **communication** | `internal_only`, `allowed_channels`, `external_requires_approval`                       |

Plus a top-level `confidentiality_clearance` (the clearance ceiling, §4) and `max_delegation_depth` (how many levels of sub-delegation are allowed — directly relevant to "agent spins up 3 agents").

### 3.3 How delegation works (monotonic tightening)

The central invariant: **a child envelope can only be equal to or more restrictive than its parent.** `RoleEnvelope.validate_tightening()` checks all 7 dimensions (`pact-envelopes.md:149–166`); a child that _omits_ a constraint the parent has is treated as **wider** → violation. Numeric NaN/Inf is rejected everywhere because `NaN < X` is always False and would silently pass every budget check (`pact-envelopes.md:206–208`, and `validate_finite` in `models/__init__.py:92`).

Intersection follows **XACML deny-overrides** semantics (`pact-envelopes.md:116–124`): financial = `min()`; operational = intersect allowed, union blocked, blocked wins; data_access = intersect paths, union blocked types; communication = intersect channels, `internal_only = a OR b`.

### 3.4 How an envelope is checked at execution time

`engine.verify_action(role_address, action, context)` is the single decision call (`pact-governance-engine.md:59–93`). Its flow:

1. Compute effective envelope **with a version hash** (SHA-256 of all contributor envelope versions — the **TOCTOU defense**, `pact-envelopes.md:240`).
2. Evaluate the action against envelope dimensions (operational, financial, …).
3. Multi-level verify: walk accountability_chain, most-restrictive wins.
4. If `context["resource"]` is a `KnowledgeItem`, run the 5-step access check (§4).
5. Combine verdicts (most restrictive wins).
6. Emit an audit anchor.

The returned `GovernanceVerdict` carries `level` (the verification gradient), `allowed`, `reason`, `envelope_version` (for stale-snapshot detection), and `access_decision`. **The `envelope_version` is the load-bearing field for the brief's "retrace and intervene" UX** — it lets the system detect that the envelope changed between when a step was planned and when it executes.

Edge cases the engine handles that the platform will inherit: **degenerate envelope** detection (no allowed actions → agent can do nothing; warned, `pact-envelopes.md:230–237`), **pass-through envelope** detection (child adds no constraint → governance adds no value at that level), **gradient dereliction** (auto-approve threshold ≥90% of the financial limit → rubber-stamping warning, `pact-envelopes.md:198–204`), and **degenerate-envelope per-request warnings** wired into the orchestrator (`orchestrator.py:140–142`).

### 3.5 Default envelopes by posture (the autonomy gradient)

`default_envelope_for_posture()` ties the per-role posture to a default envelope (`pact-envelopes.md:220–228`):

| Posture (PACT) | Autonomy | max_spend | Allowed actions            | Internal only |
| -------------- | -------- | --------- | -------------------------- | ------------- |
| PSEUDO         | 1        | \$0       | read                       | yes           |
| TOOL           | 2        | \$50      | read, write                | yes           |
| SUPERVISED     | 3        | \$1,000   | read, write, plan, propose | no            |
| DELEGATING     | 4        | \$10,000  | +execute, deploy           | no            |
| AUTONOMOUS     | 5        | \$100,000 | +approve, delegate         | no            |

This is the closest existing artifact to the brief's "choose a posture beforehand" — _but it is a per-role clearance/budget ceiling, not the per-session step-pause behavior the brief's L3/L4/L5 describes._ See §8 for the reconciliation.

---

## 4. Knowledge Clearance and the Verification Gradient

### 4.1 Knowledge clearance — the 5-step fail-closed algorithm

DEFAULT IS DENY. `engine.check_access(role, knowledge_item, posture)` runs (`pact-access-enforcement.md:12–18`):

```
Step 1  Resolve clearance     → DENY if missing or vetting not ACTIVE
Step 2  Classification check  → DENY if effective_clearance < item.classification
Step 3  Compartment check     → DENY if role lacks item's compartments (SECRET+ only)
Step 4  Containment check     → ALLOW via one of 5 sub-paths (4a–4e)
Step 5  Default deny          → DENY if no path granted access
```

`AccessDecision` returns `allowed`, `reason`, `step_failed` (1–5, or None) and `audit_details` — i.e. **a denial always carries _which step_ failed and why**, which is exactly the legibility the intervention UX needs ("this step was blocked because your clearance is CONFIDENTIAL but the document is SECRET").

**Effective clearance = `min(role.max_clearance, POSTURE_CEILING[posture])`** (`pact-access-enforcement.md:68–90`). A role with TOP_SECRET clearance running at TOOL posture can only read RESTRICTED. The posture is a _ceiling that caps standing clearance_ — the brief's "choose a posture" idea, expressed at the data-access layer.

The five containment sub-paths (4a–4e): same-unit, downward-visibility (ancestor reads descendant), T-inherits-D, **KnowledgeSharePolicy** (unit→unit grant, classification-capped, expirable), and **PactBridge** (role↔role cross-functional link, requires LCA approval first). Clearance has a full FSM: `PENDING → {ACTIVE, REVOKED}`, `ACTIVE → {SUSPENDED, EXPIRED, REVOKED}`, etc. (`pact-governance-engine.md:184`), persisted in the `ClearanceVetting` model (§6).

### 4.2 The verification gradient (the heart of the intervention model)

Every action resolves to one of **four** levels (`eatp-spec.md:30–37`, `VerificationLevel` enum, `pact-enforcement-modes.md:28`):

| Result            | Meaning                    | Action taken                                                |
| ----------------- | -------------------------- | ----------------------------------------------------------- |
| **Auto-approved** | within all constraints     | execute and log                                             |
| **Flagged**       | near a constraint boundary | execute **and highlight for review**                        |
| **Held**          | soft limit exceeded        | **queue for human approval** (creates an `AgenticDecision`) |
| **Blocked**       | hard limit violated        | reject with explanation                                     |

This 4-category gradient is **the structural answer to the brief's intervention requirement.** "Flagged" = surface on screen but proceed (an L5-autonomous step worth noticing). "Held" = pause and ask one permission (L4-supervised). "Blocked" = hard stop. The gradient already encodes the "surface decisions on screen, intervene" spectrum — it just isn't yet wired to a per-step _user-chosen_ posture (§8).

Audit durability is itself gradient-aligned (N4, `pact-conformance-features.md:86–106`): `TieredAuditDispatcher` routes BLOCKED verdicts to the most durable (replicated) storage, auto-approved to memory. More critical verdicts get more durable records.

---

## 5. The Engine — How an Objective Becomes Governed Work

The engine package (`engine/__init__.py`) is the "Dual Plane bridge connecting governance to execution." Four components, plus the underlying `PactEngine`/`GovernanceEngine` from the `pact` library.

### 5.1 SupervisorOrchestrator (`orchestrator.py`)

The **top-level entry point** for executing a request end-to-end. It composes `PactEngine` (enforcement mode + per-node governance + supervisor lifecycle + NaN guards + cost tracking) with three L3 platform features: **Run persistence** (DataFlow), **real-time events** (EventBridge), and **HELD-verdict approval persistence** (ApprovalBridge).

`execute_request(request_id, role_address, objective, context)` flow (`orchestrator.py:253–415`):

```
1. Validate inputs; NaN-guard incoming cost values (cost, daily_total, transaction_amount)
2. Warn if operating under a degenerate envelope
3. Enrich context with platform IDs (request_id, role_address, run_id)
4. PactEngine.submit_sync(objective, role, context)
     → per-node governance fires verify_action per node
     → any HELD verdict invokes _PlatformHeldCallback (below)
5. NaN-guard the returned budget; record a Run row in DataFlow
6. Bridge a completion event to the EventBus (WebSocket)
7. Return {success, run_id, results, budget_consumed, audit_trail, error}
```

The pivotal piece is `_PlatformHeldCallback` (`orchestrator.py:59–99`): it implements the `HeldActionCallback` protocol. When per-node governance returns HELD, this callback **creates an `AgenticDecision` via the ApprovalBridge and returns `False` to block the action until a human approves.** That single `return False` is how a soft-limit breach becomes a paused, on-screen, human-gated decision — _this is the brief's "agent pauses and asks for one permission" realized in code._

### 5.2 ApprovalBridge (`approval_bridge.py`)

Connects HELD verdicts to the DataFlow-backed approval queue.

- `create_decision(role_address, action, verdict, request_id, session_id)` → persists an `AgenticDecision` (status `pending`), extracting `constraint_dimension`, `constraint_details`, and `envelope_version` (TOCTOU) from the verdict; NaN-guards every numeric constraint detail. Returns `dec-XXXXXXXXXXXX`. (`approval_bridge.py:46–127`)
- `approve(decision_id, decided_by, reason)` / `reject(...)` → update status, record who decided + when + why (audit). (`approval_bridge.py:129–217`)
- `get_pending(limit)` → the approval-queue feed for a dashboard. (`approval_bridge.py:219–228`)

This is the spine of the **approval workflow**: a HELD action becomes a durable, queryable, human-resolvable record.

### 5.3 EventBridge (`event_bridge.py`)

Maps supervisor lifecycle events to platform `PlatformEvent`s for **real-time WebSocket streaming** to a dashboard. Event hooks: `on_plan_event` (plan creation, node scheduling/completion → `VERIFICATION_RESULT`), `on_cost_event` (cost accrual → `AUDIT_ANCHOR`, NaN-guarded), `on_hold_event` (`HELD_ACTION` — _the "a decision needs you" push_), `on_completion_event`. It detects sync-vs-async context and schedules accordingly (`event_bridge.py:183–204`), failing quietly if the bus is absent.

**This is the existing realization of "surface decisions on screen, recorded."** The brief's "these decisions are surfaced on screen" maps almost 1:1 onto EventBridge's event types — the dashboard already receives plan events, hold events, and cost events in real time.

### 5.4 EmergencyBypass (`emergency_bypass.py`)

Time-limited envelope expansion when an emergency needs actions beyond the normal envelope. The most security-hardened component (the file is 1000 lines).

- **Three permitted tiers** (`BypassTier`, PACT spec §9): TIER_1 = 4h (tactical), TIER_2 = 24h (extended), TIER_3 = 72h (crisis). **TIER_4 (>72h) is rejected for creation** — "emergencies over 72 hours must be re-authorized through normal governance every 72 hours" (`emergency_bypass.py:745–751`).
- **Authority gating** (`AuthorityLevel`): SUPERVISOR→Tier1, DEPARTMENT_HEAD→Tier1-2, EXECUTIVE→Tier1-3, COMPLIANCE→any. Enforced by `_authority_sufficient` (`emergency_bypass.py:113–115, 760–767`).
- **Privilege-escalation defense** (H2): `_validate_expanded_envelope` verifies the expanded envelope **does not exceed the approver's own envelope** across all five dimensions (`emergency_bypass.py:489–619`). You cannot grant more than you hold.
- **Structural-authority defense** (H3): `_validate_structural_authority` checks the approver's position in the target's accountability_chain matches the tier (`emergency_bypass.py:621–689`).
- **Rate limiting** (M4): `MAX_BYPASSES_PER_WEEK=3`, `COOLDOWN_HOURS=4`, enforced **atomically** to prevent TOCTOU — `SqliteRateLimitStore` uses `BEGIN IMMEDIATE` for cross-process atomicity across Gunicorn workers (`emergency_bypass.py:321–379`).
- **Fail-closed audit**: if the audit callback fails, bypass creation **aborts** — "governance mutations require an audit trail" (`emergency_bypass.py:826–834`).
- **Mandatory post-incident review**: every bypass schedules `review_due_by` (expiry + 7 days); `check_overdue_reviews()` surfaces ones past deadline (`emergency_bypass.py:976–999`).

### 5.5 EnforcementMode — the rollout-safety toggle (`settings.py`)

Three modes (`pact-enforcement-modes.md:28`): **ENFORCE** (verdicts binding — production default), **SHADOW** (run + log but never block — calibrate envelopes), **DISABLED** (skip governance entirely — requires `PACT_ALLOW_DISABLED_MODE=true`, refuses to instantiate otherwise, `settings.py:63–71`). SHADOW is the safe way to roll governance into an existing product: observe what _would_ be held/blocked before turning on teeth — directly relevant to slotting governance under the existing Sequor comms product without breaking it.

### 5.6 L3 service layer (read for completeness)

Above the engine sit reusable services (`use/services/`): `MultiApproverService` (quorum approvals via per-decision asyncio locks + duplicate-vote prevention, `multi_approver.py:44–131`), `ApprovalQueueService`, `CostTrackingService`, `ExpiryScheduler` (auto-expire task envelopes / bootstrap / bypasses), `NotificationDispatchService`, `RequestRouterService` (pool routing). The `governance.py` API layer sets `required_approvals` on decisions from `ApprovalConfig` (`governance.py:135–172`). The N3 conformance feature **PlanSuspension** (`pact-conformance-features.md:54–84`) is the single most relevant existing primitive to the brief — see §8.

### 5.7 End-to-end control flow

```
user objective
  → AgenticObjective (status active)
  → decomposed into AgenticRequest(s) (sequence_order, depends_on, envelope_id)
  → SupervisorOrchestrator.execute_request(request_id, role_address, objective)
      → PactEngine.submit  (per-node governance: verify_action per step)
          ├─ auto_approved → execute + audit
          ├─ flagged       → execute + highlight (EventBridge)
          ├─ held          → _PlatformHeldCallback → ApprovalBridge.create_decision
          │                     → AgenticDecision(status=pending) → approval queue
          │                     → EventBridge.on_hold_event → dashboard push
          │                     → action BLOCKED until approve()/reject()
          └─ blocked       → reject with reason + audit
      → Run row persisted (cost, tokens, duration, verification_level)
      → EventBridge.on_completion_event → dashboard
  (emergency path: EmergencyBypass.create_bypass → time-limited envelope expansion,
   audit-anchored, rate-limited, post-incident-review scheduled)
```

---

## 6. Data Models — Schema and Relationships

17 DataFlow models in `models/__init__.py` (the `@db.model` decorator auto-generates ~187 CRUD/bulk nodes). The brief named 7; the actual set is richer. Field highlights below; every model has `created_at`/`updated_at`.

### 6.1 Work-graph core

| Model                  | Purpose                                   | Key fields                                                                                                                                                                                                 | Relationships                                          |
| ---------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **AgenticObjective**   | top-level work unit                       | `org_address`, `title`, `status` (draft/active/completed/cancelled), `priority`, `budget_usd`, `deadline`, `parent_objective_id`                                                                           | self-referential (sub-objectives); parent of Requests  |
| **AgenticRequest**     | decomposed task                           | `objective_id`, `assigned_to`, `assigned_type` (unassigned/pool/agent), `claimed_by`, `status` (pending→…→completed/failed), `sequence_order`, **`depends_on`** (`{request_ids:[...]}`), **`envelope_id`** | FK→Objective; FK→envelope; produces Sessions/Artifacts |
| **AgenticWorkSession** | active work period **with cost tracking** | `request_id`, `worker_address`, `input/output_tokens`, **`cost_usd`** (NaN-guarded), `provider`, `model_name`, `tool_calls`, `verification_verdicts` (`{verdicts:[...]}`)                                  | FK→Request; parent of Artifacts                        |
| **AgenticArtifact**    | produced deliverable                      | `request_id`, `session_id`, `artifact_type`, `content_ref`, `content_hash` (SHA-256), **`version`**, **`parent_artifact_id`**, `status` (draft/submitted/approved/rejected)                                | FK→Request/Session; **self-referential versioning**    |
| **Run**                | single agent invocation record            | `session_id`, `request_id`, `agent_address`, `run_type` (llm/tool/workflow), `duration_ms`, tokens, `cost_usd`, `verification_level`, `error_message`                                                      | FK→Session/Request; parent of ExecutionMetric          |
| **ExecutionMetric**    | dashboard metrics                         | `run_id`, `metric_type` (latency/cost/tokens/throughput), `agent_address`, `pool_id`, `org_id`, `value`, `unit`, `period_start/end`, `dimensions`                                                          | FK→Run                                                 |

**The `AgenticArtifact.version` + `parent_artifact_id` pair is the existing substrate for the brief's "old outputs are versioned."** When a retraced step re-runs and produces a new output, you create a new Artifact with `version+1` and `parent_artifact_id` pointing at the prior one — the version lineage is already modeled.

### 6.2 Decision / review / governance

| Model                     | Purpose                                                         | Key fields                                                                                                                                                                                                                                                                                                                                                     | Relationships                          |
| ------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| **AgenticDecision**       | **human judgment point — created when governance returns HELD** | `agent_address`, `action`, `decision_type` (governance_hold/budget_hold/manual_review), `status` (pending/approved/rejected/expired), `reason_held`, `constraint_dimension`, `constraint_details`, `urgency`, `decided_by`, `decided_at`, **`envelope_version`** (TOCTOU), **`required_approvals`/`current_approvals`/`approval_record_ids`** (multi-approver) | FK→Request/Session; 1→N ApprovalRecord |
| **AgenticReviewDecision** | review outcome for an artifact                                  | `request_id`, `artifact_id`, `reviewer_address`, `review_type` (quality/security/compliance/peer), `verdict` (pending/approved/revision_required/rejected), `findings_count`                                                                                                                                                                                   | FK→Request/Artifact; 1→N Finding       |
| **AgenticFinding**        | issue found during review                                       | `review_id`, `severity` (info→critical), `category`, `remediation`, `status` (open/acknowledged/resolved/wontfix)                                                                                                                                                                                                                                              | FK→ReviewDecision                      |
| **ApprovalConfig**        | per-operation-type approval policy                              | `operation_type`, `required_approvals`, `timeout_hours` (auto-reject), `eligible_roles` (`{patterns:["D1-R1-*"]}`)                                                                                                                                                                                                                                             | drives Decision.required_approvals     |
| **ApprovalRecord**        | one approver's vote                                             | `decision_id`, `approver_address`, `verdict` (approved/rejected), `reason`                                                                                                                                                                                                                                                                                     | FK→Decision                            |

> Note on the brief's "D/T/R = Decision/Task/Review": there _are_ `AgenticDecision` and `AgenticReviewDecision` models, and Requests are tasks — but the **D/T/R acronym itself is the addressing grammar** (§2). The Decision/Task/Review trio is a coincidental product of the work model, not the meaning of "D/T/R."

### 6.3 Org structure & lifecycle (the rest)

| Model                                       | Purpose                                                                                                                                                                                    |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **AgenticPool** + **AgenticPoolMembership** | agent/human groups for work assignment; `routing_strategy` (round_robin/least_busy/capability_match), `max_concurrent`, per-member `capabilities` (`{skills:[...]}`)                       |
| **KnowledgeRecord**                         | persistent classified item: `classification` (public→top_secret), `owning_unit_address`, `compartments` — the L3 persistence behind the §4 access checks                                   |
| **ClearanceVetting**                        | clearance-grant FSM: `current_status` (pending/active/suspended/revoked/rejected/expired), `requested_level`, `nda_signed`, multi-approver counts, full reject/suspend/revoke audit fields |
| **BootstrapRecord**                         | time-limited permissive envelopes for new orgs (auto-expire); L3-only, never weakens L1 fail-closed                                                                                        |
| **TaskEnvelopeRecord**                      | persists L1 TaskEnvelopes at L3 for restart-survival + auto-expiry scheduling + agent acknowledgment                                                                                       |

### 6.4 Relationship graph (condensed)

```
AgenticObjective ──1:N──> AgenticRequest ──1:N──> AgenticWorkSession ──1:N──> AgenticArtifact
   │ (self: parent_objective_id)          │            │ (cost_usd)            │ (version, parent_artifact_id)
   │                                       │            └──> Run ──1:N──> ExecutionMetric
   │                                       ├──> AgenticDecision ──1:N──> ApprovalRecord   (ApprovalConfig drives policy)
   │                                       └──> AgenticReviewDecision ──1:N──> AgenticFinding
AgenticPool ──1:N──> AgenticPoolMembership          ClearanceVetting / KnowledgeRecord / TaskEnvelopeRecord / BootstrapRecord
```

---

## 7. How Approval + Cost Tracking + Emergency Bypass Actually Function

**Approval workflow:** governance returns HELD → `_PlatformHeldCallback` → `ApprovalBridge.create_decision` writes an `AgenticDecision(status=pending)` → `EventBridge.on_hold_event` pushes to the dashboard → action is **blocked** (`return False`) until a human calls `approve()`/`reject()`. For high-stakes ops, `ApprovalConfig` sets `required_approvals>1`; `MultiApproverService.record_approval` records each distinct `ApprovalRecord`, prevents duplicate votes via a per-decision asyncio lock, and reports `quorum_met`. `ApprovalConfig.timeout_hours` auto-rejects stale decisions; `expires_at` on the Decision encodes the deadline.

**Cost tracking:** budget is a first-class envelope dimension (`financial.max_spend_usd`, `requires_approval_above_usd`). Costs accrue on `AgenticWorkSession.cost_usd` and `Run.cost_usd`, are NaN-guarded at every boundary (`validate_finite`, `safe_sum_finite` for read-back), streamed via `EventBridge.on_cost_event`, aggregated into `ExecutionMetric`, and surfaced in the orchestrator return as `budget_consumed`. Crossing `requires_approval_above_usd` flips the verdict to HELD → spawns an approval decision. There is a dedicated `CostTrackingService`.

**Emergency bypass:** an authorized senior creates a tier-bounded, time-limited envelope expansion (§5.4) — validated against the approver's own envelope (no escalation), against the accountability chain (structural authority), rate-limited atomically, audit-anchored fail-closed, and saddled with a mandatory 7-day post-incident review. `check_bypass(role)` returns the active bypass (fail-closed: errors → None = no bypass). This is the "break glass" path that stays auditable.

---

## 8. CRITICAL SYNTHESIS — Is PACT the Right Substrate for the Platform's Posture + Intervention UX?

The brief's requirement, restated precisely:

1. The user **chooses a posture beforehand** — L5 Autonomous (agent goes ahead), L4 Supervised (agent asks once before executing), L3 Step-by-step (agent pauses at each step).
2. Agent decisions (e.g. "spin up 3 agents") are **surfaced on screen and recorded.**
3. The user can **retrace any previous step and intervene from there**; downstream outputs change accordingly, but **old outputs are versioned.**
4. Every activity and output is **traced and transparent** (input/output transparent; model internals are the only black box).

### 8.1 Verdict: PACT is the right _governance_ substrate — but it is the envelope/approval/accountability engine, NOT the interactive step-replay UX.

PACT is the correct foundation for the **permission-envelope + accountability + approval-gate** half of the requirement. It is _not_, as-shipped, the **interactive, step-level, retrace-and-intervene** half. The platform needs PACT **plus** a thin session/timeline layer built on primitives PACT already exposes. This is a "wire two existing things together + build one new thing" shape, not a "build from scratch" shape.

### 8.2 The two posture vocabularies must be unified (a real design decision)

There are **two** L1–L5 ladders in the ecosystem and the platform must pick a relationship:

- **PACT `TrustPostureLevel`** (PSEUDO/TOOL/SUPERVISED/DELEGATING/AUTONOMOUS): a **per-role clearance + budget + allowed-actions ceiling** (§3.5, §4.1). Static per role.
- **COC trust-posture** (L1_PSEUDO_AGENT → L5_DELEGATED, `rules/trust-posture.md`): a **per-repo agent-autonomy state machine** — auto-downgrades on violations, human-gated upgrades, signed transitions (aegis `anc-posture-*.json` cryptographic anchors). This is the one whose vocabulary the brief borrows ("L3/L4/L5").

The brief's "choose a posture beforehand (L3/L4/L5)" is **neither exactly** — it's a _per-objective, user-selected, step-pause behavior_. The recommended reconciliation:

- Keep PACT `TrustPostureLevel` as the **clearance/budget ceiling** (what an agent is _allowed_ to reach).
- Adopt the brief's L3/L4/L5 as a **per-objective interaction mode** (how often the human is _asked_), implemented by **mapping each level to a verification-gradient threshold**: L5 = only BLOCKED stops; L4 = HELD+BLOCKED stop (ask once on soft-limit); L3 = every step emits a Flagged/Held checkpoint the user must clear. The gradient already exists (§4.2); the platform sets _where the "pause" line falls_ per objective.
- Keep COC trust-posture as the **meta-governance of the agent platform's own development** (it governs how the codegen builds the product), not the end-user-facing control.

This unification is the single most important governance decision this research surfaces. It is a **Decision A/B-class** item for the analysis (which posture model is user-facing, and how the three relate).

### 8.3 What PACT already gives us (the 80%)

| Brief requirement                                     | PACT primitive that satisfies it                                                                                                    | Source                                                   |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Choose a posture (clearance/budget ceiling)           | `TrustPostureLevel` + `default_envelope_for_posture` + `POSTURE_CEILING`                                                            | `pact-envelopes.md:220`, `pact-access-enforcement.md:68` |
| "Agent asks for one permission before executing" (L4) | HELD verdict → `_PlatformHeldCallback` → `ApprovalBridge` → blocks until approve                                                    | `orchestrator.py:59–99`, `approval_bridge.py`            |
| "Pauses at each step" (L3)                            | **PlanSuspension (N3)**: `suspend_plan` blocks `verify_action` for a `plan_id` until resume conditions met; `resume_plan` continues | `pact-conformance-features.md:54–84`                     |
| Decisions surfaced on screen, recorded                | `EventBridge` (WebSocket: plan/hold/cost events) + `AgenticDecision` rows                                                           | `event_bridge.py`, `models:348`                          |
| Every activity traced & transparent                   | Audit anchors (hash-chained), `Run`/`AgenticWorkSession` rows, `ObservationSink` (N5), tamper-evident `AuditChain`                  | `eatp-spec.md:27`, `pact-conformance-features.md:108`    |
| Old outputs versioned                                 | `AgenticArtifact.version` + `parent_artifact_id`                                                                                    | `models:330–345`                                         |
| Permission envelope (5-dimension)                     | `ConstraintEnvelopeConfig` + intersection + monotonic tightening                                                                    | `pact-envelopes.md`                                      |
| Accountability of each step traced to a human         | D/T/R `accountability_chain` + EATP traceability chain                                                                              | §2, `eatp-spec.md:13–27`                                 |
| Multi-party approval for high-stakes                  | `ApprovalConfig` + `MultiApproverService` quorum                                                                                    | `multi_approver.py`                                      |
| Safe rollout into the existing Sequor product         | `EnforcementMode.SHADOW` (observe, never block)                                                                                     | `settings.py`                                            |
| Cost surfaced + budget-gated                          | financial envelope + `cost_usd` + `requires_approval_above_usd`→HELD                                                                | §7                                                       |
| "Black box is only the model's thinking"              | EATP's input/output-transparent, internals-opaque stance                                                                            | `eatp-spec.md:61–66`                                     |

**PlanSuspension (N3) is the closest existing primitive to the entire intervention UX** and deserves emphasis. It already: suspends a running plan on BUDGET/TEMPORAL/POSTURE/ENVELOPE triggers, _blocks every subsequent `verify_action` carrying that `plan_id`_, exposes `update_resume_condition` + `resume_plan`, and stores a `snapshot` of plan state at suspension. That is 70% of "pause at this step, let the human intervene, then continue."

### 8.4 What's missing for an interactive, step-level, retrace-and-intervene UX (the 15–20%)

1. **User-initiated, mid-flight intervention.** PACT suspends on _governance_ triggers (budget/temporal/posture/envelope). It has **no user-initiated `suspend_plan(reason=user_intervention)` trigger** — the `SuspensionTrigger` enum is BUDGET/TEMPORAL/POSTURE/ENVELOPE only (`pact-conformance-features.md:84`). Add a `USER` trigger. _Effort: small — one enum value + one API route._

2. **The per-objective L3/L4/L5 selector → gradient-threshold mapping.** No code maps "user picked L3" to "pause at every step." This is the new control surface. _Effort: a thin policy layer over the existing gradient + PlanSuspension. ~1 session._

3. **Step-level checkpointing + retrace.** PACT records `Run`s and `Artifact` versions but has **no "rewind to step N, fork from there" operation.** The DAG exists (`AgenticRequest.depends_on`, `sequence_order`, Artifact `parent_artifact_id`) but nothing computes "which downstream steps to invalidate and re-run when step N is changed." This **cascade-recompute + version-fork engine is the genuinely new component.** _Effort: moderate — a DAG-walk over the request/artifact graph; ~2–3 sessions; this is the only ≥500-LOC load-bearing piece._

4. **An agent↔agent transparency layer.** The brief wants _agent↔agent_ communications surfaced too. EventBridge surfaces _supervisor→platform_ events but there is no model of inter-agent messages as first-class, interveneable records. The Pool/Membership models route work but don't capture the _conversation_. _Effort: new model (`AgenticMessage`?) + EventBridge hook; ~1 session._

5. **Posture model unification (§8.2).** A design decision, not just code: which of the three posture ladders is user-facing.

6. **Non-coder-facing rendering of verdicts.** PACT verdicts are legible to engineers (`step_failed=2`, `reason_held`, `constraint_dimension`). The brief's "users don't have to be coders" needs a plain-language layer translating `constraint_dimension=financial, requires_approval_above_usd=200` into "This step would spend \$240, above your \$200 auto-approve limit — approve?" _Effort: small — a verdict→prose renderer; aligns with `rules/communication.md`._

### 8.5 Reuse ratio and integration posture

The 80/15/5 lens: **~80% reuse** (envelopes, gradient, approval bridge, event bridge, emergency bypass, audit, cost tracking, multi-approver, PlanSuspension, the 17 models, D/T/R accountability), **~15% integration/glue** (posture-selector→gradient mapping, USER suspension trigger, verdict-prose renderer, agent↔agent message model, EnforcementMode wiring under the existing product), **~5% genuinely new** (the step-retrace cascade-recompute + version-fork engine). PACT's `DataFlow`-backed models and `kailash-pact` library are direct dependencies; nothing here argues for re-implementing governance.

One caution grounded in the COC rule corpus: PACT is itself a **facade-heavy** codebase (managers, bridges, stores). The platform must hold the line on `orphan-detection.md` / `facade-manager-detection.md` — every governance manager wired into the product hot path needs a real call site + Tier-2 test, or it becomes a security promise that never executes (the exact Phase-5.11 failure those rules exist to prevent). The intervention UX must _actually call_ PlanSuspension on the hot path, not just expose it.

---

## 9. Bottom line for the platform design

- **D/T/R** gives accountability _for free, structurally_ — adopt the address grammar so every agent (including spun-up sub-agents) carries a computable accountability chain.
- **Envelopes + the 4-level verification gradient** are the permission-envelope spine — adopt wholesale; map the brief's L3/L4/L5 onto gradient thresholds rather than inventing a parallel mechanism.
- **The engine (SupervisorOrchestrator → HELD callback → ApprovalBridge → EventBridge)** already implements "pause, surface on screen, record, await human" — wire it, don't rebuild it.
- **PlanSuspension (N3)** is the seed of step-level intervention; the platform adds a USER trigger and a retrace/cascade-recompute engine on top.
- **Artifact versioning** already exists; the new work is the _cascade_ (invalidate + re-run downstream), not the _versioning_.
- **EnforcementMode.SHADOW** is how governance slots under the live Sequor comms wedge without breaking it.
- The **one real design decision** is unifying the three posture ladders (PACT clearance-ceiling vs COC agent-autonomy vs the brief's per-objective interaction mode).
