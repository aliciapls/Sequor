> Status: TARGET-STATE (vision / not yet implemented). This spec describes the intended platform; the comms wedge (shipped) specs are separate (`message-routing.md`, `rag-pipeline.md`, `response-accuracy.md`, `data-model.md`, `channel-coordination.md`, `business-model.md`, `onboarding.md`).

# Coordination & Teams (M3)

This is the domain-truth authority on the **multi-HUMAN + multi-agent shared work substrate** — moat **M3** of the strategic spine: the layer where several people and several agents co-work one shared piece of knowledge work without stepping on each other, where every working step is claimed, attributed, transparent, and interveneable, and where handoffs between humans and agents (and between agents) carry full context losslessly — while a deliberately-ungoverned **informal mode** preserves the human's right to be vague, and a **named human stays accountable for every consequential decision**.

**Plain-language frame.** When a team does work together today, the work lives in five tools and the coordination lives in a sixth (chat) where things get lost — "I thought you were doing that," "which version is current," "who decided this." This subsystem makes the team's coordination **lossless and auditable**: each task is explicitly claimed before anyone works it; every handoff is a recorded transfer of the whole record, not a lossy sentence; every step says who did it and which named human is answerable; and the whole thing is one tamper-evident log that turns "who did what, when, and was it altered" from a he-said-she-said question into a cryptographic one. It does this WITHOUT forcing the deliberately-vague hallway conversation into a permanent record.

**Companion specs (not restated here).** Posture (L1–L5), the plan-approval gate, and the five-dimensional envelope are owned by `trust-posture-and-governance.md` (M2); this spec consumes posture as the gate that decides whether a claim is advisory or enforced and whether a step pauses. Retrace, the cascade engine, versioned artifacts, and the cascade cost-preview are owned by `intervention-and-versioning.md` (M1); this spec consumes the artifact-version chain as the unit a single-writer lease guards, and consumes retrace as the action a teammate performs on another's step (§9). The work-item ontology (Objective → Request → WorkSession → Artifact → Decision) is shared with both M1 and M2; this spec is the authority on the **coordination fields** of those entities (`claimed_by`, `accountable`, adjacency, leases).

**Grounding.** Every load-bearing claim resolves to one of three workspace sources, cited inline by short tag:

- **[R2]** `workspaces/future-of-work/01-analysis/01-research/02-multi-operator-coordination.md` (the coordination substrate research)
- **[F3]** `workspaces/future-of-work/03-user-flows/03-team-collaboration.md` (the worked team-collaboration flow)
- **[K9]** `workspaces/future-of-work/01-analysis/09-risks-failure-points.md` §3 (the agent-comms hypothesis + the guardrail the risks analysis insists on)

**Reuse posture.** ~80% of this machinery already exists and runs today across the ecosystem; ~15% is re-targeting existing primitives from codebase paths to general work units; ~5% is genuinely new (agent identity, direct agent→log writes, the non-coder UI, the informal mode) [R2 §10.3, F3 §9]. Each domain below states REUSED-vs-NET-NEW explicitly, citing the source by path.

---

## 1. What this subsystem is

The ecosystem already contains a **complete, cryptographically-grounded multi-operator coordination substrate**, built to let N humans (each running their own agent CLI session) edit ONE shared codebase without silent clobbers, impersonation, or attribution evasion [R2 §0]. It is a set of **git-native primitives** — signing keys, an append-only signed log, advisory leases, a single-writer lease, a roster, a per-operator posture — not a coordination service.

M3 re-targets that substrate from **file paths** to **general work units**. The claimable thing stops being a file or glob and becomes an **AgenticRequest** (a decomposed task); the conflict relation stops being computed over the file tree and is computed over the work-item DAG; agents stop coordinating only *through* their human operator's identity and (net-new) get their own enrolled identity. The cryptographic core — the signed hash-chained log, the fold rules, fork detection, the reap ceremony, the 4-eyes gate — is reused unchanged.

| Concern | Today (codebase coordination) | Product (general knowledge work) | Reuse verdict [R2 §10.1] |
| --- | --- | --- | --- |
| Unit of work | file / glob / workspace | `Objective → Request → WorkSession → Artifact` | **REUSE** (pact already models it) |
| Who can claim | rostered operator via `verified_id`/`person_id` | rostered human OR enrolled agent (`host_role: agent`) | **EXTEND** (add agent identity class) |
| Conflict resolution | SAME/ADJACENT/INDEPENDENT over file tree | same classes over the work-item DAG | **REUSE** (re-target adjacency relation) |
| Attribution | signed log records + roster | same log; agent + accountable-human two-level | **REUSE + EXTEND** |
| Accountability / audit | append-only signed JSONL + fold rules | same log = the "every step traced" transcript | **REUSE directly** |
| Single-writer on a deliverable | codify lease (branch namespace) | lease over an Artifact under authorship | **REUSE (generalize scope)** |
| Onboarding | `/onboard` deterministic read-path | tenant/workspace snapshot for any participant | **REUSE directly** |
| Knowledge gate | `/certify` brief→probe→gate@100% | domain-bank certification for humans AND agents | **REUSE directly** |

REUSED from loom (`~/repos/loom/.claude/`) — the coordination log, claims, roster, leases, hooks, onboard/certify. REUSED from pact (`~/repos/terrene/contrib/pact`) — the work-item ontology. REUSED from aegis (`~/repos/dev/aegis`) — the runtime keypair + capability-genesis trust-anchor shape. NET-NEW — the agent identity class, direct agent→log writes, the non-coder UI, and the informal mode.

---

## 2. Operator identity — the display_id / verified_id / person_id triple

Every participant — human or agent — has a three-part identity [R2 §4.1]. REUSED from loom (`multi-operator-coordination.md` §1, `lib/operator-id.js::resolveIdentity`).

| Field | Role | Authority weight |
| --- | --- | --- |
| **`display_id`** | advisory, human-readable ("Priya", "agent-fin"). Collisions are harmless. | NONE — signage only. Tooling MUST attribute via `verified_id`, never `display_id`. |
| **`verified_id`** | fingerprint of a signing key; authenticates a single *record*. | authenticates the record, not the person |
| **`person_id`** | the unit of authority. One `person_id` → one human → `role` + enrolled keys. Immutable; keys are append-only under it. | the only axis a gate decision tests |

**The invariant.** Authority decisions (gates, quorum, accountability) test `person_id` inequality, never `display_id`. Two participants named "Alex" collide harmlessly on a banner and catastrophically on a gate — so the gate axis is the cryptographic one [R2 §4.1].

**`host_role`** distinguishes the participant class:

- `host_role: human` — a person. Eligible for every gate and quorum role.
- `host_role: ci` — a CI/deploy-key identity. Audit-only; NEVER eligible to co-sign owner-quorum, distinctness, gate-approval, or genesis/migration records. (Structural defense against a deploy key faking a "second human" [R2 §4.1].)
- **`host_role: agent`** — **NET-NEW** [R2 §4.4 takeaway #4, F3 §5.2]. An agent's own enrolled signing identity, analogous to `host_role: ci` but bound to an **accountable human** at delegation time (§6). An agent's autonomous output is attributable to the agent (the doer) AND to the human answerable for it (two-level attribution). The agent is NEVER eligible to be the accountable human, to co-sign a quorum, or to be the named human on a consequential decision — its binding always resolves to a `host_role: human` person.

### 2.1 The roster

`operators.roster.json` is the registry [R2 §4.2]. It maps each `person_id` → `{display_id, role, github_login (or tenant IdP subject), host_role, keys:[...]}`, plus a `genesis` block pinning the trust root. REUSED from loom (`operators.roster.json` + `operators.roster.schema.json`).

Roster shape (one row per participant):

```json
{
  "person_id": "pid-priya-10e7dd16",
  "display_id": "priya",
  "role": "owner",
  "host_role": "human",
  "idp_subject": "priya@acme.example",
  "keys": [{ "type": "ed25519", "fingerprint": "548F…", "pubkey": "<…>" }]
}
```

For an **agent** row, `host_role: "agent"` and an extra field `accountable_person_id` records the human bound to it at enrollment. Adding a key or a `person_id` is a **2-of-N quorum roster edit**; registration is PR/proposal-only (never a direct write), so the roster change is reviewable before it lands [R2 §4.2].

### 2.2 The identity surface (`/whoami`-equivalent)

A read-only identity surface resolves the active participant (signing-key fingerprint → roster lookup → tuple) and surfaces `display_id / person_id / verified_id / role / host_role / posture` [R2 §4.3]. Three shapes: **rostered** (full identity), **un-rostered key** (`(unregistered)` + next-step "register", default posture L2_SUPERVISED), **no signing key** (next-step "configure signing identity"). REUSED from loom (`whoami.md`).

---

## 3. The coordination event log — the rendezvous primitive

The heart of the substrate is ONE file: an **append-only, signed, hash-chained JSONL log** — the single rendezvous primitive every participant reads and writes through [R2 §2.1]. It IS the brief's "every working step is traced and transparent" requirement, realized as a tamper-evident event stream [R2 §2.2, F3 §7]. REUSED from loom (`coordination-log.jsonl`, `coc-append.js`, `lib/coordination-log.js`).

### 3.1 Record shape

Every record carries WHO + WHERE-in-chain + WHAT + signature:

```json
{
  "type": "claim",
  "verified_id": "548F…", "person_id": "pid-priya-…", "display_id": "priya",
  "seq": 14, "prev_hash": "…", "ts": "2026-06-05T09:21:00Z",
  "content": {
    "request_id": "req-q3-section-2",        // ← the UNIT OF WORK (was: path)
    "objective_id": "obj-q3-board-report",
    "granted_relation": "INDEPENDENT",
    "granted_at": "2026-06-05T09:21:00Z",
    "accountable_person_id": "pid-priya-…",  // ← two-level attribution for agent claims
    "advisory": true
  },
  "sig": "<detached signature over canonical(content)>"
}
```

The **only field-level change** from loom's claim record is `content.path → content.request_id` (+ `objective_id`, `accountable_person_id`) — a field swap, not an architectural change [R2 §1.1 takeaway #1, F3 §3].

### 3.2 Record vocabulary

REUSED verbatim from loom [R2 §2.2]: `session-open`/`-close`, `heartbeat`, `claim`/`release`/`reap`, `lease-override`, `gate-approval`, `posture-event`, `decision`, `artifact`, `handoff`, `genesis-anchor`, `genesis-migration`, `generation-rotation`, `compaction-checkpoint`, `collaborator-distinctness-attestation`/`-revocation`. The product adds no new record *type* — it re-targets `claim`/`release`/`reap`/`decision`/`artifact`/`handoff` content from paths to work units.

### 3.3 The fold rules (correctness contract)

A reader reconstructs shared state by **folding** the log. The load-bearing rules for the product [R2 §2.3], REUSED unchanged:

1. **Signature gate** — a record folds only if `sig` verifies against a roster key. Forged/hand-written records are invisible to everyone.
2. **Per-emitter chain integrity** — `seq` exactly +1, `prev_hash` matches.
3. **Fork detection** — two records at the same `(verified_id, seq)` with different content hashes = **cryptographic equivocation proof**; `block`-grade; **names the equivocator**.
4. **State-mutation scope** — a record may mutate only its own emitter's state; cross-participant release requires a co-signed `reap` (§4.4).
5. **Liveness as a read-time predicate** — a session is live iff its last heartbeat is within `LIVENESS_TTL` (20 min wall-clock) and unclosed.

> **Fork detection IS the "less lossy" guarantee** [R2 §2.3, F3 §4.2]. In human↔human comms, two people can each "remember" a different version of what was agreed, with no proof. Here, two divergent records at the same chain position are a **mathematical contradiction that names the liar**. This is the concrete, defensible form of "less lossy" the brief hypothesizes (§8) — not "agents are smarter than people," but "the handoff record is complete and cannot be falsified."

### 3.4 Trust-root substrate

REUSED-PATTERN, RE-SUBSTRATED [R2 §7, §10.3]. loom anchors the trust root in git (a `genesis-anchor` record + a server-side `refs/coc/**` ruleset that *prevents* forged refs at the GitHub boundary). aegis anchors it as a **runtime artifact** (`proj-*/genesis.json` carrying an Ed25519 `public_key_hex` + a capability/constraint envelope; signed `anchors/anc-*.json` with `parent_anchor_id` hash-chaining). The product, serving non-developer tenants who do not live in git, adopts **aegis's runtime shape backed by loom's external-anchoring rigor** — the trust root anchored to the tenant's identity provider instead of GitHub (an IdP that refuses forged records is the prevention-grade equivalent of the `refs/coc/**` ruleset) [R2 §7.2, §11.6]. REUSED from aegis (`~/repos/dev/aegis/proj-*/genesis.json`, `anchors/`) + loom (`refs/coc/**` ruleset pattern).

---

## 4. Claims, leases & the SAME/ADJACENT/INDEPENDENT relation

When a participant (human OR agent) starts on a task, they **claim** it. A claim is an **advisory lease** — it announces "I'm working here" and surfaces conflict; it does not hard-lock [R2 §1.1, F3 §3.1]. REUSED from loom (`claim.md`, `claims.md`, `release-claim.md`, `adjacency.js`).

### 4.1 The adjacency relation

At claim time, the platform computes how the new claim **relates** to every active claim, over the work-item DAG (`Request.depends_on`) instead of the file tree [R2 §3.3]:

| Class | When it fires (work-item form) | Lease severity | Behavior |
| --- | --- | --- | --- |
| **SAME** | two participants claim the **same Request** | **`halt-and-report`** | second claimant is stopped; **no claim record is written** (prevents the race-to-write); participant adjudicates [R2 §3.1] |
| **ADJACENT** | two participants on **sibling Requests of the same Objective** | **`advisory`** | banner surfaced; claim written with `granted_relation: "ADJACENT"`; participant MAY proceed |
| **INDEPENDENT** | participants on **unrelated Objectives** | **silent + auto-claim** | claim written; silent success |

Worked example [F3 §3.2]:

```
agent-fin (Priya's)   claims "section 2 — financials"  → INDEPENDENT (first claim) → silent
agent-narr (Marcus's) claims "section 3 — narrative"   → ADJACENT to section 2 (same objective)
                                                        → banner: "agent-fin is on the adjacent task"
Marcus (human) also claims "section 2"                  → SAME as agent-fin's active claim
                                                        → HALT: "agent-fin (Priya) holds section 2. Defer or re-scope."
```

### 4.2 The claim-then-work ordering is the structural defense

A SAME-class action MUST be preceded by a successful claim. Working-then-claiming retroactively is BLOCKED — "a retroactive claim cannot prevent the contest it documents" [R2 §3.2, F3 §3.2]. This converts a silent concurrent-edit into a deterministic pre-edit gate.

### 4.3 SAME = halt vs SAME = merge-surface (open product decision)

For code, SAME always halts (one writer per file). For a **report section**, two contributors merging may be *desirable* — collaboration, not collision. This is a genuine per-work-item-type product decision [R2 §3.3 takeaway #3, F3 §3.3, K9 §3]:

- **Default SAME → halt** for system-of-record writes and final numbers (where two writers genuinely collide).
- **Default SAME → merge-surface** for drafting prose (where two contributors are a feature).
- Make it a **per-task-type setting**, not a global one.

The existing **`lease-override`** record (gated by a recorded `gate-approval`) is the primitive for "two participants deliberately co-work a SAME-class scope, on the record" when they want it [R2 §3.3]. REUSED from loom. Sized as ongoing per-type design work (~1–2 autonomous cycles per work-item-type family), never one-shot [F3 §3.3].

### 4.4 Leases, staleness & the cross-operator reap ceremony

Claims are leases; they go stale (a participant gets pulled away mid-task). Reassigning an abandoned task is NOT something one manager can do silently [R2 §3.4, F3 §3.4]. REUSED from loom (`release-claim.md` cross-operator reap).

- **Self-release** — a participant releases their own claim (signed `release` record).
- **Cross-operator reap** (`--reap --cosigner`) — releases a *stale sibling* claim. Requires ALL of: (a) a **distinct-`person_id` cosigner** + co-signature, (b) the pinned victim heartbeat is older than `now - LIVENESS_TTL`, and (c) no victim heartbeat with a higher `seq`. Bases: `co-signed`, `owner-2-of-N`, `self-reap`.

This is "reassign an abandoned task safely" — with cryptographic proof the original worker was genuinely idle (the pinned-heartbeat predicate) AND that a *second distinct human* authorized it (the cosigner). It prevents the abuse "the manager silently reassigned your work and claimed you abandoned it" [F3 §3.4].

### 4.5 Advisory vs enforced for autonomous agents (open decision)

loom claims are **advisory** — a human can ignore the banner. For an L5 autonomous agent, advisory may be insufficient: the agent must **honor** the claim structurally [R2 §11.3, F3 §10.3]. Disposition: when the claimant is a human, claims stay advisory (banner); when the claimant is an **agent at L5**, the claim is **enforced** at the hook layer (the agent's edit on a SAME-class claimed Request is `block`ed, not merely warned). The posture (M2) is the switch that decides advisory-vs-enforced.

---

## 5. The single-writer lease on a deliverable

When N participants co-work, every artifact that historically had one writer per session becomes a multi-writer contention surface [R2 §5]. The **single-writer lease** is the primitive [R2 §5.2]. REUSED from loom (`codify-lease.js`), generalized in scope.

In loom the lease races for a *branch namespace* before any artifact edit; on conflict it surfaces the holder + scope + acquired-at verbatim and STOPs. For the product, this generalizes to: **a deliverable (Artifact) under active authorship has a single-writer lease; a second author is told who holds it and on what version**, and the merge happens through review (= an `AgenticReviewDecision`) [R2 §5.2]. The lease file is written atomically (`.tmp` + rename) and fingerprints its scope.

This realizes the brief's "old outputs are versioned" requirement [F3 §6.2]: the version/PR chain + `Artifact.version` + `parent_artifact_id` is the version history; the lease guards which writer owns the head right now. The artifact-version chain itself is owned by `intervention-and-versioning.md` (M1); this spec owns only the *lease* over it.

---

## 6. Handoffs — where the brief's §3d hypothesis goes live (and its guardrail)

This is the section that puts brief §3d in action — and, honestly, the guardrail the risks analysis insists on [F3 §4, K9 §3]. The hypothesis: agent-mediated handoff is *richer and less lossy* than human↔human handoff. The evidence supports this **for handoffs and coordination specifically**, NOT for relationships, judgment, or deliberately-ambiguous talk [K9 §3.1, F3 §0].

### 6.1 The lossy path vs the rich path

**Human → human (lossy)** [F3 §4.1]: "send me the Q3 numbers" → a sentence crosses the wire; the *source* (which ledger version), the *caveats* (provisional vs final), the *adjustments already applied*, and the *reasoning* stay in the sender's head. Communication loss is integration loss wearing a different hat.

**Agent → agent (rich)** [F3 §4.2]: the producing agent emits a **versioned Artifact** carrying full provenance (source = ledger v3 post-adjustment, revenue = FINAL, one-off = excluded per a recorded Decision, every number traceable to the query that produced it), then **hands off by reference** ("artifact v4 is ready; here is the complete record"). The consuming agent reads the *whole record*, not a sentence — losslessly — and it is **auditable in a way human↔human comms can never be**: the handoff is a signed `handoff` record (who handed what to whom, when, which version), and fork detection (§3.3) makes "remembering it differently" a contradiction that names the liar.

```
Q3 board report — coordination log (excerpt, signed records)            [F3 §7.1]

  claim     agent-fin   req-section-2                       Priya
  claim     agent-narr  req-section-3  (ADJACENT banner)     Marcus
  decision  exclude August one-off   approved                Priya
  artifact  section-2 v4                                      agent-fin / Priya
  handoff   section-2 v4 → agent-narr                         agent-fin → agent-narr
  retrace   agent-fin "exclude one-off" step                  Marcus
  decision  add September one-off  requested→approved          Marcus → Priya   ← 2 named humans
  artifact  section-2 v5  (parent: v4)                         agent-fin / Priya
  artifact  final report v1                                    agent-rev / Priya
```

### 6.2 The honest caveat — misconstrual MOVES, it does not vanish

The platform does NOT claim agent handoffs are error-free [K9 §3.1 point 4, F3 §4.3]. The new failure mode: the agent **misreads the human's intent at the human↔agent boundary**, then propagates that misreading **with high-fidelity confidence** across the whole network — a *confident, fast, well-recorded* error. Human telephone-game loses information; agent telephone-game can **amplify a wrong premise**. This is exactly why the rich channel is only safe **because** every step is interveneable (M1 retrace, §9) AND a named human gates every consequential decision (§7) — the rich channel and the guardrail are two halves of one design.

### 6.3 The guardrail #1 — ambiguity-preservation (the informal mode)

NET-NEW [F3 §8, K9 §3.4]. The brief's §3d is a **research BET, not a settled USP** [K9 §3]. Building M3 on the verbatim claim ("agents communicate better than you do") is an internal inconsistency a sharp buyer will find [K9 §3.4]. So the platform ships **the narrowed position** — disrupt the handoff, not the relationship — with **ambiguity-preservation as a first-class, day-one feature**.

Not everything a team says should become a recorded objective. "Let's see how Q3 goes" is *deliberately* unspecified — it preserves optionality, enables negotiation, allows face-saving, and lets people defer commitment [K9 §3.1 point 3]. Forcing it into a complete recorded objective would (a) create a discoverable record where deniability was the point — a legal-discovery and privacy hazard, and (b) strip out the relationship bandwidth the "inefficient" hallway conversation carries.

So the platform ships two explicit modes [F3 §8.1]:

```
[ Objective mode ]   — structured, recorded, agent-actionable, fully traced
[ Informal mode  ]   — NOT structured, NOT a decision, NOT acted on; for talk that
                       should stay vague + off-record
```

**The discipline that bounds the ungoverned path** [F3 §8.1]: informal mode is for **talk, never for action** — it cannot touch a system of record, cannot send anything external, cannot move work. The moment a human **promotes** informal talk into an Objective, the full governance + trace + posture machinery re-engages. The ungoverned path is bounded to deliberation, by construction. (Honest cost: the informal mode adds a second comms path that is deliberately ungoverned — an ungoverned path is a place security risks can hide — which is why the talk-never-action boundary is structural, not a guideline [K9 §3.4 cons].)

### 6.4 The guardrail #2 — a named human on every consequential decision

The rich agent channel does NOT dissolve accountability into "the agents worked it out" — that is precisely the governance failure the platform is built to prevent [K9 §3.1 point 2, F3 §5.2]. **Accountability cannot be delegated to the channel.** Every **consequential decision keeps a named human on it** [K9 §3.4 commitment 2, F3 §6.3]. The platform can always answer "who chose this, and when" — a named, time-stamped, attributable human authorization, not a vendor disclaimer [K9 §4.5]. Two-level attribution (§2) is what keeps a named person answerable for every agent's output. See §7 for the gate mechanics.

## 6.5 Agent↔Agent Transparency & Intervenability — v1 cut

This section is the **single owning authority** for the brief's §3e requirement — "agent↔agent communications and working steps are transparent and interveneable". The brief asks for two things at once, and the v1 cut treats them differently. To stop the two halves drifting across multiple sections, the whole disposition lives here, in one place:

- **Human↔agent: FULL.** Every step an agent takes for a human is transparent (view the input + output, §7.1) and interveneable (retrace from any step, §8) — this half ships in v1 in full.
- **Agent↔agent: PARTIAL, deliberately deferred.** The v1 cut splits the agent↔agent half into HANDOFFS (shipped) vs MESSAGES (deferred), spelled out below.

**The single locatable disposition (v1):**

1. **Agent↔agent HANDOFFS are traced and retraceable in v1.** When one agent hands work to another (§6.1–6.2), the handoff is a signed `handoff` record on the provenance ledger — who handed what to whom, when, which artifact version. A teammate can SEE every handoff (transparent) and can RETRACE the step where a wrong premise entered (interveneable-after-the-fact, §8). This half of §3e ships in v1: the transparency and retraceability promise is real for handoffs because the handoff IS a ledger record, not a sentence.

2. **First-class interveneable agent↔agent MESSAGES are DEFERRED post-v1.** "Intervene mid-conversation between two agents" — pause a live agent↔agent exchange, inspect the in-flight message, edit or redirect it before the receiving agent acts — is NOT in the v1 cut. In v1 the intervention surface is the ledger record (retrace a completed step), not a live message bus between agents. The deferral is deliberate: v1's rich channel is the **versioned-artifact handoff** (§6.1), which carries full provenance as a discrete record; a streaming, mid-conversation agent↔agent message channel with live human interruption is a larger surface that the substrate does not yet model, and shipping it half-built would create exactly the ungoverned-path hazard §6.3 warns against.

3. **The agent-identity enrollment ceremony is net-new and unbuilt.** Both halves above assume agents have their own enrolled signing identity (`host_role: agent`, §2) so their handoff/message records are attributable. That enrollment ceremony — binding an agent identity to an accountable human at delegation time — **does not exist yet** (no detailed spec yet — TARGET-STATE gap; see §13 open question 4). Until it lands, agent↔agent records are attributed through the human operator's identity, not the agent's own.

**Where the two halves live.** The human↔agent FULL half is realized by §7.1 (transparency: view input/output) + §8 (intervenability: cross-participant retrace). The agent↔agent PARTIAL half is realized by §6.1–6.2 (handoffs as signed ledger records) for the shipped part; the deferred MESSAGES part has no detailed spec yet — TARGET-STATE gap.

**Cross-references (companion authorities, not restated here).** Governance — whether an intervention or a consequential agent↔agent step pauses for a named human — is owned by `trust-posture-and-governance.md` (the posture ladder + the consequential-decision gate that §6.4 and §7.2 consume). The ledger itself — the signed, hash-chained record stream that makes handoffs transparent and retraceable — is owned by `transparency-and-provenance.md`. This spec owns only the **coordination semantics** of agent↔agent transparency (which half ships, which defers, and why); the ledger mechanism and the governance gate are the two companion specs above.

---

## 7. Attribution, decisions & the consequential-decision gate

Every step is attributed to a **doer (the agent or human who did it)** under a **named accountable human** [F3 §5]. REUSED from loom (`operator-gate.js`, the 4-eyes matrix); the two-level (agent + accountable human) attribution is NET-NEW.

### 7.1 What a teammate sees, live

```
Q3 board report — live trace                                    posture: L4   [F3 §5.1]

  ✓ agent-fin   pulled ledger v3                    (Priya)    [view I/O]
  ✓ agent-fin   excluded August one-off  ⏸→approved (Priya)   [view decision]
  ✓ agent-fin   drafted section 2 → artifact v4     (Priya)    [view · retrace]
  ⟳ agent-narr  drafting section 3 from §2 v4        (Marcus)   [view · retrace]
  … agent-rev   waiting on §2 + §3                   (Priya)
```

Every line carries **who is accountable** (the named human behind the agent), **what the agent did**, and two affordances: **view** (the actual input and output — transparent) and **retrace** (intervene from this step). The agent's internal reasoning is the black box; its input and output are fully visible (brief §3f) [F3 §5.1].

### 7.2 The four-eyes gate (cannot be faked)

A consequential decision is recorded as a `decision` record requiring a distinct named human [F3 §6.4, R2 §9.1]. The gate resolves the signed approval key → `person_id` and **rejects iff** the approver's `person_id` == the requester's `person_id` OR (for owner/senior gates) the same bound IdP login. A single human with two keys CANNOT self-approve — the gate tests the **person**, not the key. `host_role: ci` and `host_role: agent` are NEVER eligible approvers. This is the existing implementation of "two-person authorization" for high-stakes actions [R2 §9.1].

> **Restated for governance** [F3 §6.4]: in a human team, "did two people really sign off?" is a trust question. On the platform it is a cryptographic one — the gate **names** any attempt to fake a second approver.

### 7.3 Calibrating "consequential" (open tuning)

Gating *which* changes are consequential is an ongoing, never-finished tuning problem — gate too much and the autonomy value erodes into "except every number needs approval" (the HITL-bottleneck); gate too little and a wrong board number reaches the board un-checked [F3 §6.3, K9 §4.2]. The containment answer is **least-privilege + posture per objective** (owned by M2): the gate fires on the genuinely-consequential class (system-of-record writes, external sends, final numbers), not on every keystroke.

---

## 8. The intervention flow — a teammate retraces another's agent's step

The clearest expression of the moat conjunction (M1 retrace + M2 governance + M3 multi-human) [F3 §6]. A teammate (Marcus) notices a wrong premise in another participant's agent's step (agent-fin, accountable: Priya):

1. **Spot** — Marcus uses **view** on the "excluded one-off" step and sees only August was excluded; the September one-off is still in the number, and it has already propagated downstream (§6.2's confident-fast-wrong error) [F3 §6.1].
2. **Retrace** — Marcus clicks **retrace** on the *earliest* step where the error entered (not the final number, not his own draft). He corrects the instruction [F3 §6.2]. (Retrace + cascade preview + version preservation are owned by `intervention-and-versioning.md`; this spec owns the *cross-participant authorization* of that retrace.)
3. **Gate** — the retrace changes a board number = a consequential step. Under the L4 posture Priya set, AND the accountability default, this cannot land on Marcus's say-so alone when **Priya is the accountable human** for that task. A `decision` record fires: `requested_by: Marcus, accountable: Priya`. Priya is asked to confirm [F3 §6.3].
4. **Record** — Priya approves. The correction cascades, new versions are produced, old ones kept (M1), and the `decision` is signed and logged — requested by Marcus, approved by Priya, **both named** [F3 §6.3].

> This is the honest position shown in action: a second named human caught the error, and the accountable human signed the fix. The wrong board number cannot reach the board un-checked [F3 §6.3].

---

## 9. Onboarding & certification — the lifecycle for joining a team

REUSED directly from loom [R2 §6]. Two surfaces govern a participant (human OR agent) joining a workspace.

### 9.1 `/onboard` — deterministic read-path

A **read-only** snapshot (writes ZERO state) surfacing shared state in **fixed order** so two participants opening simultaneously see consistent state [R2 §6.1, F3 §2.1]: **Identity → Team Memory → Workspace → Posture → Active Claims → Single-Writer Lease → Rules/State Changed → Action Items**. It answers "who am I AND what is the whole team doing right now" in one screen instead of five chat scrolls. REUSED from loom (`onboard.md`, skill `41-onboard`).

```
Priya opens the Q3-board-report workspace:                              [F3 §2.1]

  YOU: Priya (Head of Finance) — verified
  TEAM KNOWS: 4 shared facts (Q3 close date, board template, …)
  ACTIVE NOW: Marcus is here (no claims yet)
  POSTURE: this objective runs at L4 (you'll be asked once before consequential steps)
  RECENT DECISIONS: 2 (Q2 report sign-off, FY guidance change)
  NEXT: state the objective, or claim a task
```

### 9.2 `/certify` — brief → probe → gate at 100%

The **knowledge gate** before a participant claims non-trivial work [R2 §6.2]. Three phases: **Brief** (walk the critical surfaces in fixed order), **Probe** (a curated question bank, easy→hard, NOT model-generated, with NO assistance during the gate — enforced structurally by a lockfile + a guard that blocks every retrieval call during the gate), **Gate at 100%** (strict; failed questions loop until all pass; passing writes a signed certification receipt). Until pass, the participant stays L2_SUPERVISED. REUSED from loom (`certify.md`, skill `42-certify`).

A new **agent** joining a workspace can be `/certify`-gated against the team's domain bank exactly like a human — and the agent, by construction, can load the entire brief + team-memory + decisions log losslessly, the very advantage the brief hypothesizes [R2 §6.2]. The certification receipt is the attributable "this participant knows the surface" anchor.

### 9.3 Team-memory & decisions log

Two more shared-knowledge surfaces, REUSED from loom [R2 §4.4]: **Team-memory** (shared, signed facts, one fact per file, each carrying a signed body-anchor — the team's attributable, tamper-evident institutional memory) and the **decisions log** (`DECISION-` journal entries surfaced by `/onboard`, each pinning its body's hash so tamper is detected at read-time and names the signer).

---

## 10. Data shapes — the coordination fields of the work-item ontology

The work-item ontology is shared (pact, `~/repos/terrene/contrib/pact`); this spec is the authority on its **coordination fields** [R2 §1.2].

| Entity | Coordination fields M3 owns | Plain meaning |
| --- | --- | --- |
| **Objective** | `submitted_by`, `status`, `parent_objective_id` | the top-level work unit ("Q3 board report") |
| **Request** | `claimed_by`, `accountable_person_id`, `depends_on`, `granted_relation` | a decomposed task; `depends_on` is the DAG the adjacency relation runs over (§4.1) |
| **WorkSession** | `worker_address` (the agent/human doer), `cost_usd`, `verification_verdicts` | one active work period with cost tracking |
| **Artifact** | `version`, `parent_artifact_id`, `created_by`, single-writer `lease_holder` | a produced deliverable; the version chain + the lease M3 guards (§5) |
| **Decision** | `requested_by`, `accountable_person_id`, `required_approvals`, `status` | the consequential-decision gate row (§7.2) |

Mapping the brief's example [R2 §1.2, F3 §1]: "I want a Q3 board report" → an **Objective** (`submitted_by: Priya`); "spin up 3 agents" → 3 **Request** rows (`claimed_by` a different agent each, `depends_on` the DAG); each agent's run → a **WorkSession**; each output → a versioned **Artifact**; each pause → a **Decision** row.

---

## 11. Reuse-vs-net-new ledger (sized honestly)

Per the 80/15/5 read [R2 §10.3, F3 §9]:

**REUSED directly (~80%) — exists and runs today:**

- the signed, append-only, hash-chained log + fold rules + fork detection — loom (`~/repos/loom/.claude/`)
- claims / SAME/ADJACENT/INDEPENDENT classes + the reap ceremony — loom (`adjacency.js`, `claim.md`, `release-claim.md`)
- identity triple + roster + the deterministic onboarding read-path — loom (`operator-id.js`, `operators.roster.json`, `whoami.md`)
- the L1–L5 posture ladder + the four-eyes gate matrix — pact (`~/repos/terrene/contrib/pact`) + eatp (`~/repos/loom/kailash-py`) + aegis (`~/repos/dev/aegis`) (owned by `trust-posture-and-governance.md`)
- the work-item ontology (Objective → Request → WorkSession → Artifact → Decision) — pact
- versioned artifacts (the "old outputs preserved" chain) — pact + loom anchors (owned by `intervention-and-versioning.md`)
- `/onboard` + `/certify` + team-memory + decisions-log — loom (`41-onboard`, `42-certify`)

**ADAPTATION (~15%) — re-target existing primitives:**

- generalize the claimable unit from **file path** to **Request** (claim-record `content` field swap, §3.1) [R2 §1.1]
- re-target the **adjacency relation** from the file tree to the **work-item DAG** (`Request.depends_on`, §4.1) [R2 §3.3]
- generalize the single-writer lease to a generic "deliverable-under-authorship" lease (§5) [R2 §5.2]
- re-substrate the trust root from GitHub `refs/coc/**` to a multi-tenant backend anchored to the tenant's IdP (aegis runtime shape, §3.4) [R2 §7.2]

**NET-NEW (~5%) — genuinely new:**

- the **agent identity class** (`host_role: agent`) with two-level attribution (agent + accountable human), §2 [R2 §4.4, F3 §5.2]
- **direct agent→log writes** (agents append claim/decision/handoff records as themselves), §6 [R2 §10.2]
- the **non-developer UI** surfacing the log/posture/claims/trace as a screen (today: CLI prose + JSONL), §7.1 [R2 §10.3]
- the **informal / ambiguity-preservation mode** (the guardrail the risks analysis requires), §6.3 [F3 §9, K9 §3.4]

Effort is in **autonomous execution cycles**, never human-days. The reused substrate is configuration + re-targeting, parallelizable across the claim-engine, the work-item model, and the posture layer (independent surfaces). The agent-identity class + two-level binding is the largest net-new piece (greenfield, ~2–3 cycles at the first-session factor). The non-developer UI and the informal mode should ship in a deliberately-reduced first form and grow on usability evidence [F3 §9].

---

## 12. Edge cases & invariants

| Edge case | Behavior | Source |
| --- | --- | --- |
| **SAME-class collision** | second claimant `halt-and-report`; **no claim record written** (prevents race-to-write); participant adjudicates — defer, re-scope, or `lease-override` with a recorded `gate-approval` for deliberate co-work | [R2 §3.1, F3 §3.2] |
| **Stale-lease reap** | cross-operator reap requires (a) distinct-`person_id` cosigner + co-sig, (b) pinned victim heartbeat older than `now - LIVENESS_TTL`, (c) no victim heartbeat with higher `seq`; prevents "manager silently reassigned your work" | [R2 §3.4, F3 §3.4] |
| **A teammate intervening on another's agent's step** | allowed via M1 retrace, BUT if the change is consequential AND the intervener is not the accountable human, a `decision` record fires requiring the **accountable human's** sign-off before the cascade lands (`requested_by` ≠ `accountable_person_id`) | [F3 §6.3] |
| **Agent claims advisory-vs-enforced** | human claimant → advisory banner; agent-at-L5 claimant → enforced (hook `block` on SAME-class) | [R2 §11.3, F3 §10.3, §4.5] |
| **Informal-mode talk that tries to act** | structurally refused — informal mode cannot touch a system of record, send externally, or move work; promotion to an Objective re-engages full governance | [F3 §8.1] |
| **Two participants same `display_id`** | harmless on banners; gates/quorum/accountability test `person_id`, never `display_id` | [R2 §4.1] |
| **Fork / equivocation** | two records at same `(verified_id, seq)` with different content = `block`-grade contradiction that **names the equivocator** | [R2 §2.3] |

**Load-bearing invariants:**

1. Authority decisions test `person_id`, never `display_id` (§2). [R2 §4.1]
2. Every coordination record is stamped + hash-chained + signed; hand-written appends silently drop on fold (§3). [R2 §2.1]
3. SAME-class action MUST be preceded by a successful claim; retroactive claim is BLOCKED (§4.2). [R2 §3.2]
4. Every consequential decision keeps a **named human** on it; accountability is never delegated to the channel (§6.4). [K9 §3.1 point 2]
5. The four-eyes gate tests the **person**, not the key; a single human with two keys cannot self-approve (§7.2). [R2 §9.1]
6. Informal mode is talk-never-action; the ungoverned path is bounded to deliberation (§6.3). [F3 §8.1]

---

## 13. Open questions (flagged, not hidden)

1. **Scale.** The substrate is designed for "~12 operators against one repo" [R2 §11.1]. A product workspace may have hundreds of agents + humans. Does the fold survive 10K+ participants / 1M+ records? Compaction-checkpoints exist but their scaling to product cardinality is unproven. **Open.**
2. **SAME = halt vs merge, per work-item type** (§4.3). Decided per-type; unbuilt and never one-shot [R2 §11.2].
3. **Advisory vs enforced claims for autonomous agents** (§4.5). Disposition leans enforced-at-L5, but the enforcement-vs-friction tuning is open [R2 §11.3].
4. **Agent attribution without a human in the loop.** For an autonomous L5 agent, the accountable-human binding must be established **at delegation time**, not action time; the agent-identity-enrollment ceremony does not exist yet [R2 §11.4, F3 §10.4].
5. **The hypothesis itself.** Whether agent-mediated handoffs measurably beat human handoffs in real team use is the central BET [K9 §3]. M3 is built to **validate it cheaply** — instrument whether teams route real handoffs through the agent channel vs bypass it to chat; whether round-trips drop; whether users ask for an informal mode (which is itself the signal that ambiguity-preservation is needed) [K9 §3.3, F3 §8.2] — not to assume it. The substrate survives as coordination plumbing even if the bold version of the hypothesis is culturally rejected [K9 §3.3, F3 §10.5].

> **If this domain grows.** §6 (handoffs + the two guardrails) and §9 (onboard/certify lifecycle) are the two sub-domains most likely to need their own files if the spec exceeds 300 lines per `specs-authority.md` Rule 8 — split candidates are `coordination-handoffs-and-guardrails.md` and `coordination-onboarding-lifecycle.md`, with this file retained as the substrate + claims + identity authority.
