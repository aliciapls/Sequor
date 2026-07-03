# M6 — Multi-Human + Multi-Agent Team Substrate (moat M3): FOUNDATIONAL

> **What this milestone proves (plain language).** Several people and several agents can co-work one
> shared piece of knowledge work without stepping on each other: every task is explicitly claimed
> before anyone works it; every handoff between a human and an agent (and between agents) carries the
> whole record — source, caveats, reasoning, version — instead of a lossy sentence; every step says
> who did it and which named human is answerable; the whole thing is one tamper-evident log that turns
> "who did what, when, and was it altered" from a he-said-she-said question into a cryptographic one —
> while a deliberately-ungoverned informal mode preserves the human's right to be vague and
> off-the-record.
>
> **DECISION D applied — this milestone is FOUNDATIONAL, not gated behind a validation spike.** The
> owner has confirmed that agent-mediated communication being richer / less-lossy than human comms is
> a SETTLED founding thesis, not a bet to validate-first. Therefore the team / multi-human+agent layer
> is built as foundational infrastructure. The roadmap's old "C7a agent-comms BET" instrumentation is
> RE-SCOPED to NON-GATING evidence-gathering: build it to corroborate opportunistically, never as a
> prerequisite. No todo in this milestone waits on C7a. The old "gate M3 behind C7a" dependency is
> REMOVED. (Decision D, briefs/01-vision.md §4; journals 0003 / 0005.)
>
> **The CARE guardrails are INVARIANTS, unaffected by Decision D.** Decision D settles the
> richer-comms thesis; it does NOT touch the guardrails. Two guardrails are HELD as load-bearing
> invariants in every relevant todo: (1) a NAMED HUMAN stays on every consequential decision —
> accountability is never delegated to the channel; (2) ambiguity-preservation — the informal,
> "not-an-objective" mode that preserves the human's right to be vague. These are the two halves of
> the design that make the rich channel safe; they are not optional. (roadmap §11.1 invariant;
> coordination-and-teams.md §6.4, §6.3, §12 invariants 4+6.)
>
> **The honest caveat that travels with the rich channel.** The platform does NOT claim agent handoffs
> are error-free. The new failure mode: an agent can misread the human's intent at the human↔agent
> boundary and then propagate that misreading with high-fidelity confidence across the whole network —
> a confident, fast, well-recorded error. Human telephone-game loses information; agent telephone-game
> can amplify a wrong premise. This is exactly WHY the rich channel is safe only BECAUSE every step is
> interveneable (M1 retrace) AND a named human gates every consequential decision (guardrail 1). The
> rich channel and the guardrails are two halves of one design. (coordination-and-teams.md §6.2;
> user-flow 03 §4.3.)

---

## Dependency and sharding posture for this milestone

- **FOUNDATIONAL — no C7a gate.** Per Decision D, the substrate is built as foundational
  infrastructure. C7a handoff instrumentation (M6-9) is NON-GATING evidence-gathering and depends on
  the substrate, not the reverse. Do not sequence any substrate todo behind a validation spike.
- **Consumes M1 governance for the HELD path.** The named-human-on-consequential-decision guardrail
  (guardrail 1) is realized through M1's posture-gated HELD / four-eyes machinery. M6-7 (the
  consequential-decision gate) consumes M2/M1 governance; it does not re-implement it.
- **~80% reused, ~15% re-pointed, ~5% net-new — size honestly.** ~80% already runs today (the signed
  hash-chained coordination log, fold rules, fork detection, the reap ceremony, claims with
  SAME/ADJACENT/INDEPENDENT, the identity triple + roster, onboard/certify, the four-eyes gate). ~15%
  is re-targeting those primitives from file paths to general WORK units. ~5% is genuinely new: the
  agent identity class with two-level attribution, direct agent→log writes, the non-coder UI, and the
  informal mode. (coordination-and-teams.md §11; user-flow 03 §9.)
- **The agent-identity class is the largest net-new piece — greenfield, ~2–3× first-session factor.**
  It binds an agent's own enrolled signing identity to an accountable human at delegation time. The
  agent is NEVER eligible to be the accountable human, to co-sign a quorum, or to be the named human on
  a consequential decision. (coordination-and-teams.md §2, §13 open question 4.)
- **Tenant-isolation on all coordination state.** Every coordination record, claim, posture record,
  and audit row carries the customer's `tenant_id` (the substrate today is per-repo; in the product it
  is per-tenant). A multi-tenant deployment also needs a durable/distributed event bus — the current
  in-process bus is single-process. (coordination-and-teams.md §3.4; `tenant-isolation.md`.)
- **The informal mode adds a deliberately-ungoverned surface — state this con honestly.** A second
  comms path that is deliberately ungoverned is a place security risks can hide. The mitigation is
  STRUCTURAL, not a guideline: informal mode is talk-never-action — it cannot touch a system of record,
  cannot send anything external, cannot move work; the moment a human promotes informal talk to an
  Objective, full governance re-engages. (coordination-and-teams.md §6.3; user-flow 03 §8.1.)
- **Orphan-detection / facade-manager discipline applies.** Any `*Manager` / `*Store` / `*Service`-
  shaped class (the claim engine, the coordination-log store, the agent-identity registry) MUST land
  with a production call site on the real coordination path + a Tier-2 wiring test in the same change.
  (`orphan-detection.md`, `facade-manager-detection.md`.)
- **BUILD and WIRE are SEPARATE todos throughout.**

---

### M6-1 — BUILD: operator identity triple + roster, extended with the agent identity class

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §2, §2.1, §2.2 (+ plan: 02-plans/01 §5.2; roadmap §11.1)
- **What:** Stand up the participant identity triple — `display_id` (advisory signage),
  `verified_id` (a signing-key fingerprint that authenticates a record), `person_id` (the immutable
  unit of authority) — backed by a roster mapping each `person_id` to one human plus a role and
  enrolled keys. Add the NET-NEW `host_role: agent` class: an agent's own enrolled signing identity,
  analogous to a CI identity but bound to an accountable human via an `accountable_person_id` field.
  Authority decisions test `person_id` inequality, never `display_id`. The agent is NEVER eligible to
  be the accountable human, co-sign a quorum, or be the named human on a consequential decision.
- **Reuses → Builds:** loom identity triple + roster (`operator-id.js`, `operators.roster.json`); the
  `host_role: ci` audit-only shape → the net-new `host_role: agent` class with two-level attribution
  (agent doer + accountable human) and the `accountable_person_id` binding.
- **Invariants:** authority decisions test `person_id`, never `display_id`; `person_id` is immutable,
  keys append-only; agent identities are never eligible for accountable-human / quorum / consequential-
  decision roles; the D/T/R accountability chain uses Department/Team/Role per Decision C (briefs §4),
  NOT Decision/Task/Review; tenant-isolation on the per-tenant roster.
- **Sizing:** ~2–3 cycles (the agent-identity class is greenfield; first-session ~2–3× factor). SHARD:
  (1) the reused triple + roster re-pointed to per-tenant; (2) the net-new agent identity class +
  two-level binding.
- **Depends on:** nothing new (the human-multiplicity half is reused wholesale).
- **Acceptance (confirm / falsify):** **Confirms** — a human and an agent each resolve to a distinct
  identity; an agent's record attributes to both the agent (doer) and its accountable human; an attempt
  to use the agent as a quorum co-signer or accountable human is refused. **Falsifies** — authority is
  decided on `display_id`, OR an agent identity is accepted as an accountable human / quorum co-signer.
  Real-infra Tier-2: resolve both participant classes, assert two-level attribution + agent-ineligible.

---

### M6-2 — BUILD: the append-only signed, hash-chained coordination log (the rendezvous primitive)

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §3, §3.1, §3.3 (+ plan: 02-plans/01 §5.2; roadmap §11.1)
- **What:** Stand up the single rendezvous primitive: one append-only, signed, hash-chained JSONL
  coordination log that every participant reads and writes through. Each record carries the emitter's
  `verified_id` + `person_id`, a monotonic per-emitter `seq`, a `prev_hash` chain, and a detached
  signature over canonical content. Re-target the claim/decision/artifact/handoff record content from
  file paths to general work units (`request_id` + `objective_id` + `accountable_person_id` — a
  field swap, not an architectural change). Enforce the fold rules: signature gate (un-signed records
  are invisible to everyone), per-emitter chain integrity, fork detection (two records at the same
  `(verified_id, seq)` with different content = a cryptographic contradiction that NAMES the
  equivocator), state-mutation scope, liveness as a read-time predicate. Add direct agent→log writes
  (agents append records as themselves — net-new).
- **Reuses → Builds:** loom coordination log (`coordination-log.jsonl`, `coc-append.js`,
  `coordination-log.js`); fold rules + fork detection → the field-swap to work units + direct agent→log
  writes.
- **Invariants:** every record stamped + hash-chained + signed (hand-written appends silently drop on
  fold); fork detection names the equivocator (this IS the "less lossy" guarantee — a handoff record
  cannot be falsified); a record mutates only its own emitter's state; tenant-isolation on the log.
- **Sizing:** ~2 cycles (the log + fold rules are reused; the field-swap + agent-writes are the
  net-new). SHARD: (1) re-pointed log + fold rules; (2) direct agent→log writes.
- **Depends on:** M6-1 (identities the log stamps records with).
- **Acceptance (confirm / falsify):** **Confirms** — a signed record folds into shared state; a
  hand-written append is invisible; two contradictory records at the same chain position are flagged as
  equivocation and name the emitter; an agent appends a record as itself, attributed to its accountable
  human. **Falsifies** — an un-signed record folds, OR a fork goes undetected, OR an agent record
  cannot be attributed. Real-infra Tier-2: append-fold-readback + fork-detection + agent-write
  attribution.

---

### M6-3 — BUILD: claims / leases with SAME/ADJACENT/INDEPENDENT over general WORK units

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §4, §4.1, §4.2 (+ plan: 02-plans/01 §5.2; roadmap §11.1; user-flow 03 §3)
- **What:** Build claims as advisory leases over a work unit (an `AgenticRequest`, not a file path).
  Compute adjacency over the work-item DAG (`Request.depends_on`) instead of the file tree: SAME (two
  participants claim the same Request → `halt-and-report`; no claim record written, preventing the
  race-to-write); ADJACENT (sibling Requests of the same Objective → advisory banner); INDEPENDENT
  (unrelated Objectives → silent auto-claim). The claim-then-work ordering is the structural defense: a
  SAME-class action MUST be preceded by a successful claim — working-then-claiming retroactively is
  BLOCKED, because a retroactive claim cannot prevent the contest it documents.
- **Reuses → Builds:** loom claims + the SAME/ADJACENT/INDEPENDENT adjacency relation (`adjacency.js`,
  `claim.md`) → the adjacency relation re-targeted from the file tree to the work-item DAG.
- **Invariants:** SAME-class action MUST be preceded by a successful claim (retroactive claim BLOCKED);
  SAME-class collision writes no claim record (prevents race-to-write); claims are advisory for a human
  claimant; tenant-isolation on claim records.
- **Sizing:** ~1–2 cycles (the adjacency relation is reused; the DAG re-targeting is the work). No
  shard unless the per-work-item-type SAME=halt-vs-merge tuning (M6-4) is folded in (keep it separate).
- **Depends on:** M6-2 (the log claims are written to). Consumes the work-item ontology (Objective →
  Request → WorkSession → Artifact → Decision).
- **Acceptance (confirm / falsify):** **Confirms** — two agents on sibling Requests get an ADJACENT
  banner; a human claiming a Request already held by another participant is halted with no claim
  written; an edit attempted before a claim on a SAME-class scope is refused. **Falsifies** — a SAME
  collision writes a contested claim, OR a retroactive claim is accepted, OR adjacency is computed over
  the file tree rather than the work DAG. Real-infra Tier-2 + walk: claim → adjacency-class → halt /
  banner / silent per the worked Q3-board-report example.

---

### M6-4 — BUILD: leases, the cross-operator reap ceremony, and the per-work-type SAME tuning

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §4.3, §4.4, §4.5, §5 (+ plan: 02-plans/01 §5.2; roadmap §11.1; user-flow 03 §3.4)
- **What:** Build the lease lifecycle: claims go stale; reassigning an abandoned task is the
  cross-operator reap ceremony — a `reap` requires (a) a distinct-`person_id` cosigner + co-signature,
  (b) the pinned victim heartbeat older than `now - LIVENESS_TTL`, and (c) no victim heartbeat with a
  higher `seq`. Build the single-writer lease over a deliverable-under-authorship (generalizing loom's
  branch-namespace lease). Build the per-work-item-type SAME tuning: default SAME→halt for
  system-of-record writes and final numbers, default SAME→merge-surface for drafting prose; the
  `lease-override` (gated by a recorded `gate-approval`) is the primitive for deliberate co-work on the
  record. Add the advisory-vs-enforced switch: a human claimant → advisory banner; an agent claimant at
  the most-autonomous posture → enforced (hook-layer block on a SAME-class scope).
- **Reuses → Builds:** loom cross-operator reap (`release-claim.md`); single-writer lease
  (`codify-lease.js`); the `lease-override` record → the deliverable-scope generalization + the
  per-work-type SAME tuning + the agent advisory-vs-enforced switch (posture is the switch).
- **Invariants:** cross-operator reap requires a distinct-person cosigner + the pinned-idle predicate
  (prevents "the manager silently reassigned your work"); the single-writer lease guards the version
  head; agent-at-most-autonomous claims are enforced, not merely advisory; tenant-isolation on leases.
- **Sizing:** ~1–2 cycles per work-item-type family for the SAME tuning (never one-shot — this is
  ongoing per-type design work); ~1 cycle for the reap + lease generalization. SHARD: (1) reap + lease;
  (2) per-work-type SAME tuning + the advisory-vs-enforced switch.
- **Depends on:** M6-1, M6-2, M6-3. Consumes M2 posture (the advisory-vs-enforced switch).
- **Acceptance (confirm / falsify):** **Confirms** — an abandoned claim is reaped only with a distinct
  cosigner + proof the worker was idle; a prose Request allows deliberate co-work via `lease-override`
  while a final-number Request halts; an agent at the most-autonomous posture is blocked (not just
  warned) on a SAME-class claimed scope. **Falsifies** — a reap succeeds without a cosigner or without
  the idle proof, OR an agent ignores a SAME-class claim. Real-infra Tier-2: reap-ceremony +
  per-type-SAME + agent-enforced-claim.

---

### M6-5 — BUILD: agent↔agent + human↔agent handoffs as first-class surfaced records (context/memory-carrying)

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §6, §6.1, §6.2, §6.5 (+ plan: 02-plans/01 §5.2; roadmap §11.1; user-flow 03 §4)
- **What:** Build the handoff as a signed `handoff` record on the coordination log — who handed what to
  whom, when, which artifact version. A producing agent emits a versioned Artifact carrying full
  provenance (source, caveats, adjustments-already-applied, reasoning, every number traceable to its
  query) and hands off BY REFERENCE ("artifact v4 is ready; here is the complete record"); the
  consuming agent reads the whole record, not a sentence — losslessly. Human↔agent handoffs carry the
  same full context/memory. Per the v1 cut: agent↔agent HANDOFFS are traced and retraceable (shipped);
  first-class interveneable agent↔agent MESSAGES (pause a live exchange, edit an in-flight message
  before the receiver acts) are DEFERRED post-v1 — in v1 the intervention surface is the ledger record
  (retrace a completed step), not a live message bus. Do NOT silently widen v1 to live messages.
- **Reuses → Builds:** the signed coordination log + the versioned-Artifact provenance chain → the
  first-class `handoff` record surfaced as an inspectable record + the human↔agent context-carrying
  handoff. The agent↔agent message bus is explicitly out of v1 scope.
- **Invariants:** the handoff is a signed ledger record (who/what/when/which-version), not a sentence;
  fork detection makes "remembering it differently" a contradiction that names the liar;
  accountability is never delegated to the channel (the rich channel carries a named accountable human
  on every record); tenant-isolation on handoff records.
- **Sizing:** ~1–2 cycles (the handoff record is a thin layer over the reused log + artifact chain).
  No shard. Keep the deferred message bus OUT.
- **Depends on:** M6-1, M6-2. Consumes the versioned-Artifact chain (owned by M1 /
  intervention-and-versioning).
- **Acceptance (confirm / falsify):** **Confirms** — a producing agent hands off a versioned artifact
  by reference; the consuming agent reads the whole provenance-carrying record (source + caveats +
  reasoning), not a paste; the handoff is a signed record a teammate can SEE; a human↔agent handoff
  carries the same full context. **Falsifies** — a handoff loses provenance (degrades to a sentence),
  OR the handoff is not a surfaced signed record, OR v1 silently ships a live agent↔agent message bus.
  Real-infra Tier-2 + walk: produce → handoff-by-reference → consumer-reads-whole-record, with receipts.

---

### M6-6 — BUILD: the ambiguity-preservation / informal "not-an-objective" mode (HELD guardrail 2)

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §6.3, §12 invariant 6 (+ plan: 02-plans/01 §5.2; roadmap §11.1; user-flow 03 §8)
- **What:** Build two explicit modes: Objective mode (structured, recorded, agent-actionable, fully
  traced) and Informal mode (NOT structured, NOT a decision, NOT acted on — for deliberately-vague,
  off-the-record talk). The discipline that bounds the ungoverned path is STRUCTURAL: informal mode is
  talk-never-action — it cannot touch a system of record, cannot send anything external, cannot move
  work. The moment a human promotes informal talk into an Objective, the full governance + trace +
  posture machinery re-engages. This guardrail is a CARE invariant, HELD per Decision D — it preserves
  the human's right to be vague, which is a feature, not a defect (forcing ambiguity into a permanent
  record is a legal-discovery and relationship hazard).
- **Reuses → Builds:** the Objective-mode work-item machinery (reused) → the net-new informal mode +
  the structural talk-never-action boundary + the promote-to-Objective transition.
- **Invariants:** informal mode is talk-never-action (the ungoverned path is bounded to deliberation by
  construction); promotion to an Objective re-engages full governance; the boundary is structural, not
  a guideline. **Symmetric con stated honestly:** the informal mode is a second, deliberately-
  ungoverned comms path — a place security risks can hide — which is exactly why the talk-never-action
  boundary is enforced structurally.
- **Sizing:** ~1–2 cycles (net-new; ship in a deliberately-reduced first form, grow on usability
  evidence). No shard.
- **Depends on:** M6-2 (the log; informal talk is NOT written as governed records). Consumes M2
  governance (re-engaged on promotion).
- **Acceptance (confirm / falsify):** **Confirms** — informal-mode talk preserves ambiguity, is not
  recorded as a decision, and is not acted on; an attempt to act from informal mode (touch a system of
  record, send externally, move work) is structurally refused; promoting informal talk to an Objective
  re-engages full governance + trace. **Falsifies** — informal talk leaks into an action, OR ambiguity
  is forced into a recorded objective, OR the boundary is a guideline rather than a structural refusal.
  Real-infra Tier-2 + walk: informal-talk → attempt-action-refused → promote → governance-re-engages.

---

### M6-7 — BUILD + WIRE: the named-human-on-consequential-decision gate (HELD guardrail 1)

- **Type:** WIRE
- **Implements:** specs/coordination-and-teams.md §6.4, §7, §7.2, §8 (+ plan: 02-plans/01 §5.2; roadmap §11.1; user-flow 03 §6)
- **What:** Wire the consequential-decision gate: a consequential step (a system-of-record write, an
  external send, a final number) is recorded as a `decision` record requiring a distinct NAMED HUMAN.
  When a teammate retraces another participant's agent's step (M1 retrace) and the change is
  consequential AND the intervener is not the accountable human, a `decision` fires with
  `requested_by` ≠ `accountable_person_id`, and the accountable human must confirm before the cascade
  lands. The four-eyes gate resolves the signed approval key → `person_id` and rejects iff approver
  `person_id` == requester (or, for owner/senior gates, the same bound IdP login); a single human with
  two keys cannot self-approve; agent identities are never eligible approvers. This guardrail is a CARE
  invariant, HELD per Decision D — accountability is never delegated to the channel.
- **Reuses → Builds:** loom four-eyes gate (`operator-gate.js`, the 4-eyes-on-`person_id` matrix); the
  M2 posture-gated HELD path; the M1 retrace action → the two-level (agent + accountable human)
  attribution wired onto the consequential-decision gate.
- **Invariants:** every consequential decision keeps a NAMED HUMAN on it (accountability never
  delegated to the channel); the four-eyes gate tests the PERSON, not the key (a single human with two
  keys cannot self-approve); agent identities are never eligible approvers; the D/T/R accountability
  chain uses Department/Team/Role per Decision C (briefs §4), NOT Decision/Task/Review; tenant-isolation
  on decision records. **Symmetric con stated honestly:** gating consequential writes is the
  HITL-bottleneck risk — gate too much and the autonomy value erodes into "except every number needs
  approval"; calibrating WHICH changes are consequential is ongoing, never-finished tuning. The
  containment answer is least-privilege + posture per objective, so the gate fires on the genuinely-
  consequential class, not every keystroke.
- **Sizing:** ~1–2 cycles (the gate is reused; the wiring onto retrace + two-level attribution is the
  work). No shard.
- **Depends on:** M6-1, M6-2. Consumes M1 retrace + M2 governance for the HELD path.
- **Acceptance (confirm / falsify):** **Confirms** — a teammate retraces another's agent's step; the
  change is consequential so a `decision` fires naming requester + accountable human; the accountable
  human signs before the cascade lands; an attempt to self-approve with a second key is refused, the
  gate naming the attempt. **Falsifies** — a consequential change lands on one person's say-so when
  another is the accountable human, OR a single human self-approves via two keys, OR an agent is
  accepted as an approver. Real-infra Tier-2 + walk: retrace → consequential-decision-fires →
  named-human-signs, with receipts (the worked Marcus-retraces-Priya's-step flow).

---

### M6-8 — BUILD + WIRE: onboarding, certification, and the non-coder team UI surface

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §7.1, §9, §9.1, §9.2 (+ plan: 02-plans/01 §5.2; roadmap §11.1; user-flow 03 §2, §5, §7)
- **What:** Wire the deterministic `/onboard` read-path (a read-only, fixed-order snapshot: Identity →
  Team Memory → Workspace → Posture → Active Claims → Single-Writer Lease → Rules/State Changed →
  Action Items) so two participants opening simultaneously see consistent state; wire `/certify`
  (brief → probe → gate-at-100%, no assistance during the gate) so a participant — human OR agent — is
  knowledge-gated before claiming non-trivial work. Build the non-coder UI surface that renders the
  coordination log / posture / claims / live trace as a screen (today this is CLI prose + JSONL): each
  trace line carries who-is-accountable, what-the-agent-did, and two affordances — VIEW (the actual
  input/output; the model's internal reasoning is the black box) and RETRACE (intervene from this
  step). Surface team-memory (shared signed facts) and the decisions log.
- **Reuses → Builds:** loom `/onboard` + `/certify` + team-memory + decisions-log (`41-onboard`,
  `42-certify`) → the non-coder UI surface over the reused read-paths (the net-new surface; today CLI +
  JSONL).
- **Invariants:** `/onboard` writes ZERO state (deterministic read-path, fixed order); `/certify` gate
  runs at 100% with no assistance; VIEW shows input/output but never claims to show the model's
  internal reasoning (the black-box boundary); tenant-isolation on all surfaced state.
- **Sizing:** ~2–3 cycles (the read-paths are reused; the non-coder UI surface is the net-new bulk,
  shipped in a deliberately-reduced first form). SHARD: (1) onboard/certify wiring; (2) the non-coder
  live-trace UI surface.
- **Depends on:** M6-1, M6-2, M6-3, M6-7 (the surface renders claims + decisions + trace).
- **Acceptance (confirm / falsify):** **Confirms** — two participants open the workspace and see the
  same fixed-order snapshot; an agent is `/certify`-gated against the team's domain bank before
  claiming; a teammate watches the live trace with per-step VIEW + RETRACE affordances and a named
  accountable human on each line. **Falsifies** — `/onboard` writes state or shows inconsistent order,
  OR a participant claims non-trivial work un-certified, OR the trace claims to show the model's
  internal reasoning. User-facing walk with receipts (the worked Priya-opens-the-workspace flow).

---

### M6-9 — BUILD: C7a handoff instrumentation (NON-GATING corroborating evidence, per Decision D)

- **Type:** BUILD
- **Implements:** specs/coordination-and-teams.md §13 open-question 5 (+ plan: 02-plans/02 §11.1; roadmap §11.1 — re-scoped non-gating)
- **What:** Instrument the handoff path — from the audit trail the platform records anyway — to gather
  CORROBORATING evidence that agent-mediated handoffs reduce round-trips, "I thought you were doing
  that" failures, and re-keying. Measure: whether teams route real handoffs through the agent channel
  versus bypassing to chat/email; whether round-trips drop; whether users ask for an informal /
  off-the-record mode (itself a signal the ambiguity-preservation need is real and met). **Per Decision
  D this is NON-GATING:** it corroborates the settled richer-comms thesis opportunistically; it is
  NEVER a prerequisite for any other M6 todo, and no substrate todo waits on it. (The old roadmap "gate
  M3 behind C7a" dependency is REMOVED.)
- **Reuses → Builds:** the coordination log / audit trail the platform records anyway (near-zero
  incremental build) → the handoff-metrics instrumentation surfaced as opportunistic evidence.
- **Invariants:** non-gating (this todo blocks nothing); the named-human-on-decision and
  accountability-not-in-channel invariants are unaffected (instrumentation observes, it does not relax
  any guardrail); tenant-isolation on metric labels, with bounded label cardinality (no unbounded
  `tenant_id` Prometheus labels — top-N or aggregation tier per `tenant-isolation.md`).
- **Sizing:** ~1 cycle (instrumentation over an existing trail). No shard.
- **Depends on:** M6-2, M6-5 (the log + handoff records it measures). **Depends on NOTHING that depends
  on it** — and per Decision D, nothing else depends on it.
- **Acceptance (confirm / falsify):** **Confirms** — the instrumentation reports round-trip counts,
  channel-routing (agent channel vs chat/email bypass), and informal-mode requests from the existing
  audit trail, with bounded metric cardinality. The substrate ships and is usable whether or not this
  evidence is yet collected. **Falsifies** — the instrumentation gates or blocks any substrate todo
  (a Decision-D violation), OR it requires a new data path beyond the existing audit trail, OR its
  metric labels are unbounded by `tenant_id`. Real-infra Tier-2: metrics-from-existing-trail with
  bounded cardinality, and a confirmation that no substrate todo lists this as a dependency.

---

### M6-10 — BUILD (DEFERRED post-v1): the live agent↔agent interveneable message bus

- **Type:** BUILD (DEFERRED post-v1)
- **Implements:** specs/coordination-and-teams.md §6, §6.2 (+ plan: 02-plans/01 §10.4 — the named NET-NEW "agent↔agent message model" component; brief §3e)
- **Value-anchor:** brief §3e — "agent↔agent communications/working steps transparent and interveneable."
  The brief asks for live agent↔agent exchanges that a human can SEE in flight and STEP INTO before the
  receiver acts (pause a live exchange, edit an in-flight message). Plan 01 §10.4 named this as a
  NET-NEW component ("agent↔agent message model, ~1 cycle"); it is surfaced here so it is not silently
  dropped.
- **What:** Build a first-class live agent↔agent MESSAGE bus where an in-flight message between two
  agents is itself a surfaced, pausable, editable object — a human can intervene on the LIVE exchange
  (pause it, edit the message, redirect it) BEFORE the receiving agent acts on it. This is distinct from
  the v1 handoff (M6-5), which records a COMPLETED step as a traced, retraceable ledger record. The bus
  adds the live-intervention surface on top of the ledger.
- **Disposition (explicit, out of v1):** Per the reduced-scope discipline, v1 ships agent↔agent
  HANDOFFS as traced, retraceable ledger records (M6-5) — NOT live interveneable messages. The v1
  intervention surface is the ledger record (retrace a completed step via M1 retrace), not a live
  message bus. M6-5 already defers the live interveneable messages post-v1 with no gate; this todo
  converts that silent deferral into a surfaced, anchored one. Do NOT silently widen v1 to include this.
- **Founder-gated:** This deferral is founder-gated — the founder decides if/when the live agent↔agent
  message bus enters scope. It is NOT auto-promoted by any downstream session; re-pickup MUST
  re-validate the value-anchor against the brief before resuming.
- **Reuses → Builds:** the signed coordination log + the M6-5 handoff record + M1 retrace/intervention
  surface → the net-new live-message-bus intervention layer (pause / edit-in-flight / redirect a LIVE
  agent↔agent exchange before the receiver acts).
- **Invariants (when built):** a named accountable human remains on every consequential decision the bus
  carries (accountability never delegated to the channel); intervention on a live message is a signed,
  attributed action; tenant-isolation on bus records.
- **Sizing:** ~1 cycle (per plan 01 §10.4), counted ONLY if/when the founder promotes it into v1+ scope.
- **Depends on:** M6-2, M6-5 (the log + the handoff records the live bus extends). DEFERRED — blocks
  nothing in v1.
- **Acceptance (confirm / falsify):** **Confirms** — a human pauses a live agent↔agent exchange, edits
  an in-flight message, and the receiving agent acts on the edited message, not the original; the
  intervention is a signed, attributed record. **Falsifies** — a live agent↔agent message cannot be
  paused/edited before the receiver acts, OR the intervention is not attributed. (Out of v1 — acceptance
  applies only if/when founder-promoted.)

---

### M6-11 — DESIGN: multi-stakeholder posture composition on a shared enterprise objective

- **Type:** DESIGN
- **Implements:** specs/coordination-and-teams.md §5.3, §12 #10 (+ plan: 02-plans/01 §5.2; roadmap §11.1)
- **What:** Produce a written, reviewed design (NOT code) for how N humans' postures COMPOSE on ONE
  shared enterprise objective. loom today computes operative posture as `min(operator_posture, floor)` —
  one operator against one repo floor. The product needs the GENERALIZATION: when several stakeholders
  (e.g. an analyst, a reviewer, and an owner) each hold a posture and all act on the SAME objective,
  what is the operative posture for an action under that objective? The design MUST specify, with worked
  examples: (a) the composition function — is it `min` across all participating stakeholders' postures
  (most-cautious wins), a role-weighted rule (the accountable human's posture dominates), or a hybrid;
  (b) how the objective-level floor interacts with each stakeholder's per-objective posture; (c) what
  happens when a stakeholder JOINS or LEAVES a live objective mid-flight (does the operative posture
  recompute); (d) the interaction with the M6-7 consequential-decision gate (a more-cautious
  stakeholder's posture must not be silently overridden by a more-autonomous one). The design MUST state
  symmetric cons (a strict `min` across many stakeholders can grind a multi-stakeholder objective to the
  most-cautious participant's pace — the HITL-bottleneck risk at the team scale).
- **Reuses → Builds:** loom `min(operator_posture, repo_floor)` single-operator composition (M2 posture
  model) → the multi-stakeholder generalization on a shared objective (net-new design).
- **Invariants (the design MUST hold):** a more-cautious stakeholder's posture is never silently
  overridden by a more-autonomous one on a shared objective; a named accountable human stays on every
  consequential decision regardless of how postures compose; tenant-isolation on per-objective posture
  records.
- **Sizing:** ~1–2 cycles (design, not code; greenfield generalization — first-session ~2–3× factor).
  No shard unless the join/leave-mid-flight recompute diverges enough to need a separate review pass.
- **Depends on:** consumes M2 posture model + M6-1 (the identity layer the stakeholders resolve to) as
  inputs. This design informs M6-7 (the consequential-decision gate consumes the composed posture).
- **Acceptance (confirm / falsify):** **Confirms** — a reviewer can read the design and, for a worked
  3-stakeholder objective, state the operative posture for an action plus what happens on join/leave
  mid-flight; the design shows a more-cautious stakeholder is never overridden by a more-autonomous one.
  **Falsifies** — the composition function is left as "min, generalized" without a worked multi-party
  example, OR a more-autonomous stakeholder can silently override a more-cautious one, OR join/leave
  mid-flight is unspecified. Human review gate.
