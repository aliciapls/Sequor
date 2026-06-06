# 02 — Multi-Operator Coordination & Team-Work Mechanics

> Research output for the agentic-work-platform analysis. Addresses brief objective **3d**
> (team-oriented interface where humans AND agents collaborate transparently) and the
> supporting objectives **3e/3f/3g** (transparent/interveneable steps, full attribution,
> shareable artifacts). Grounds in actual files across loom, aegis, pact, and Sequor's COC
> setup. All paths are absolute or repo-relative-to-cited-root; uncertainty is flagged inline.
>
> **Central synthesis question (from the brief):** the brief hypothesizes that agent↔agent
> communication is _richer and less lossy_ than human↔human. Today this machinery coordinates
> **human operators (and their agents) editing a CODEBASE**. This document maps it onto the
> product requirement: **a team workspace where humans and agents co-work on GENERAL
> knowledge work, where every working step is transparent and attributable.**

---

## 0. Executive summary

The Terrene/Kailash ecosystem already contains a **complete, cryptographically-grounded
multi-operator coordination substrate** — built to let N humans (each running their own
agent CLI session) edit one shared codebase without silent clobbers, impersonation, or
attribution evasion. It is not a coordination _service_; it is a set of **git-native
primitives** (signing keys, an append-only signed log, advisory leases, a single-writer
codify lease, a roster, a per-operator trust posture).

There are **two distinct, complementary implementations** of the same idea:

| Implementation      | Where                       | Coordination primitive                                                                                                                                   | Threat model                                                                                                                                                                              |
| ------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **loom substrate**  | `~/repos/loom/.claude/`     | Append-only **signed JSONL coordination log** (`coordination-log.jsonl`), git-native (commit-signing keys + `gh api`), `refs/coc/**` server-side ruleset | **Bounded-trust**: adversary is a legitimate team member with repo write access (privilege-escalation / impersonation / attribution-evasion / sabotage)                                   |
| **aegis substrate** | `~/repos/dev/aegis/proj-*/` | Per-project **hash-chained signature anchor chain** (`anchors/anc-*.json`), Ed25519 keypair per org (`keys/`), `genesis.json` capability constraints     | Same graduated-trust philosophy, runtime-enforced posture state machine (`L1..L5` ladder via the COC rules; `Restricted/Supervised/Autonomous/Full` named states in the live anchor data) |

**The reuse story is strong (the brief's "80%").** The unit-of-work hierarchy, the
claim/conflict semantics, the attribution chain, the single-writer lease, the posture
ladder, the onboard/certify lifecycle — all exist and run today. What is **net-new** for the
product is (a) generalizing the "claimable unit" from _file paths_ to _abstract work items_
(objectives/tasks/deliverables), (b) surfacing the machinery in a **non-developer UI**
(today it is CLI prose + JSONL), and (c) wiring the **agent↔agent channel** as a first-class
transport (today agents coordinate _through_ their human operator's signed records).

Crucially, **pact already models the generalized unit of work** (`AgenticObjective →
AgenticRequest → AgenticWorkSession → AgenticArtifact → AgenticDecision/ReviewDecision`),
so the path from "coordinate file edits" to "coordinate general knowledge work" is a
**bridge that already has both banks built** — loom supplies the cryptographic coordination
substrate, pact supplies the work-item ontology.

---

## 1. The unit of work, today and for the product

### 1.1 Today (loom): the claimable unit is a _path or glob_

In loom, the coordination substrate arbitrates concurrent edits to **files**. The claim
record (`/claim` command, `~/repos/loom/.claude/commands/claim.md`) stakes an advisory lease
over a `path`, `glob`, or `workspace`:

```js
// Claim record shape (claim.md § Record shape)
{
  type: "claim",
  verified_id, person_id, display_id,        // WHO (cryptographic + authority + display)
  seq, prev_hash, ts,                        // WHERE in the per-emitter hash chain
  content: {
    claim_id: "claim-<verified_id>-<nowMs>",
    path: "<arg>",        // OR glob: "<arg>"  — the UNIT OF WORK
    granted_relation: "ADJACENT" | "INDEPENDENT",
    granted_at: "<ISO>",
    advisory: true,        // only when ADJACENT
  },
  sig                      // detached signature over canonical(core)
}
```

The unit is therefore **a region of the shared artifact tree**. Claims are _advisory leases_
— they surface conflict; they do not hard-lock (`claim.md` § "What this command does NOT do":
"Does NOT enforce — claims are advisory").

### 1.2 The product unit: pact already generalized it

pact (`~/repos/terrene/contrib/pact/src/pact_platform/models/__init__.py`) defines the
**generalized work-item ontology** the product needs — a hierarchy of claimable, assignable,
attributable work units that are NOT files:

| Model (`@db.model`)                    | Role                                                          | Key coordination fields                                                                                                                                  |
| -------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`AgenticObjective`** (line 268)      | "Top-level **work unit** submitted for execution"             | `status` (draft/active/completed/cancelled), `submitted_by`, `budget_usd`, `priority`, `parent_objective_id`                                             |
| **`AgenticRequest`** (line 286)        | "Decomposed task from an objective"                           | `assigned_to` (pool/agent), `assigned_type`, **`claimed_by`**, `status` (pending→assigned→in_progress→review→completed), `depends_on`, **`envelope_id`** |
| **`AgenticWorkSession`** (line 308)    | "Active work period with cost tracking"                       | `worker_address`, `input_tokens`/`output_tokens`/`cost_usd`, `model_name`, **`verification_verdicts`**                                                   |
| **`AgenticArtifact`** (line 329)       | "Produced deliverable"                                        | `content_hash` (SHA-256), **`version`**, **`parent_artifact_id`**, `created_by`, `status` (draft/submitted/approved/rejected)                            |
| **`AgenticDecision`** (line 348)       | "Human judgment point — created when governance returns HELD" | `status` (pending/approved/rejected/expired), `constraint_dimension`, `required_approvals`/`current_approvals`, `envelope_version` (TOCTOU defense)      |
| **`AgenticReviewDecision`** (line 376) | "Review outcome for an artifact"                              | `reviewer_address`, `verdict`, `findings_count`                                                                                                          |

**This is the missing generalization.** The brief's example — _"user says 'I want 3Q
financial report' → agent decides to spin up 3 agents"_ — maps directly:

- "I want 3Q financial report" → an **`AgenticObjective`** (`status: active`, `submitted_by:
<human>`).
- "spin up 3 agents" → 3 **`AgenticRequest`** rows (`assigned_type: agent`, each
  `claimed_by` a different worker), with `depends_on` capturing the DAG.
- Each agent's run → an **`AgenticWorkSession`** (token/cost tracking + `verification_verdicts`).
- Each agent's output → an **`AgenticArtifact`** (versioned, hashed, `parent_artifact_id`
  for the "old outputs are versioned" requirement in brief 3e).
- "users can choose a posture beforehand / pause at each step" → **`AgenticDecision`** rows
  (`decision_type: governance_hold`, `required_approvals`).

> **Synthesis takeaway #1 — the unit of work generalizes cleanly.** loom's
> _path-claim_ and pact's _Request.claimed_by_ are the **same primitive at two altitudes**.
> The product's claimable unit is `AgenticRequest` (a decomposed task); the coordination
> log's claim record is the cryptographic _envelope_ that proves WHO claimed it, WHEN, and
> in what relation to siblings. Reusing loom's claim shape with `content.request_id`
> substituting for `content.path` is a **field-level change, not an architectural one**.

---

## 2. The coordination log — the rendezvous primitive

### 2.1 One file, append-only, signed, hash-chained

The heart of the loom substrate is **one file**:
`~/repos/loom/.claude/learning/coordination-log.jsonl`
(rule: `Sequor/.claude/rules/multi-operator-coordination.md` §2). It is the _single
rendezvous primitive_ between operators. Properties:

- **Append-only JSONL, ≤2KB per line** so `O_APPEND` is atomic at the OS level.
- Every record carries: emitter's **`verified_id`** (signing-key fingerprint) + **`person_id`**
  (authority unit), **`seq`** (strictly monotonic per-emitter), **`prev_hash`** (per-emitter
  hash-chain), and **`sig`** (detached signature over canonical content).
- A record is appended **only** via the canonical helper (`coc-append.js`) — hand-written
  JSONL is BLOCKED (MUST-1) because it lacks signature + chain and silently drops on every
  sibling's fold.

**Live evidence** — the actual loom log (`head` of `coordination-log.jsonl`) shows real
signed records. The genesis-anchor record (seq 0) carries a full GPG signature and a
`gh_api_owner_capture` proving `esperie-enterprise/loom` is the repo owner; the
genesis-migration record (seq 1) re-anchors the trust root with a fresh org-admin
attestation. These are not fixtures — they are the running trust root of the loom repo.

### 2.2 Record types

The substrate defines a rich record vocabulary (§2):

```
clone-init, collaborator-distinctness-attestation/-revocation,
session-open/-close, heartbeat, claim/release/reap, lease-override,
gate-approval, posture-event, compaction-checkpoint,
genesis-anchor, genesis-migration, generation-rotation,
journal-body-anchor
```

This is the **transcript of all coordination activity** — every session open/close, every
heartbeat (liveness), every claim, every governance approval, every posture change. For the
product, _this log IS the "every working step is traced and transparent" requirement_ (brief
3f), realized as a signed, append-only, tamper-evident event stream.

### 2.3 The 10 fold rules (correctness semantics)

A reader reconstructs shared state by **folding** the log. The 10 fold rules (§2) are the
correctness contract. The load-bearing ones for the product:

1. **Signature gate** — a record folds only if `sig` verifies against a roster public key.
   _(Unsigned/forged records are invisible to everyone.)_
2. **Per-emitter chain integrity** — `seq` exactly +1, `prev_hash` matches.
3. **Fork detection** — two records at the same `(verified_id, seq)` with different content
   hashes = **cryptographic equivocation proof**; `block`-grade; **names the equivocator**.
4. **State-mutation scope** — a record may mutate only its own emitter's state;
   cross-operator release requires a co-signed `reap`.
5. **Liveness as a read-time predicate** — a session is live iff its last heartbeat is within
   `LIVENESS_TTL` (20 min wall-clock) and unclosed.

> **Synthesis takeaway #2 — fork detection IS the "less lossy" guarantee.** The brief's
> hypothesis (agent↔agent is less lossy than human↔human) is _operationalized_ here: in
> human↔human comms, two people can each "remember" a different version of what was agreed,
> and there is no proof. In this substrate, two divergent records at the same chain position
> are a **mathematical contradiction that names the liar**. The coordination log makes
> "who said what, when, and was it tampered with" a cryptographic question, not a
> he-said-she-said one.

### 2.4 Aegis's parallel mechanism: hash-chained anchor chain

aegis implements the same _signed, chained, tamper-evident_ idea with a different on-disk
shape. Instead of one JSONL log, aegis writes **per-record signature anchors** into
`proj-<id>/anchors/anc-*.json`, each linking to a `parent_anchor_id` (a hash chain) and
carrying a `record_hash` + `signature`. Live example
(`~/repos/dev/aegis/proj-ad9690bf/anchors/`):

```
posture-Supervised-to-Restricted   (parent: None)          ← chain root
  → posture-Restricted-to-Supervised  (parent: …9ab71ab)
    → posture-Supervised-to-Autonomous (parent: …1298bf1)
      → posture-Autonomous-to-Full      (parent: …f490b9f)
```

Each `anc-posture-*.json` is a signed, parent-linked record of a **posture transition** —
the aegis analogue of loom's `posture-event` records. The `genesis.json` carries the
Ed25519 `public_key_hex` + a **capability/constraint set** (`allow_network`,
`allow_filesystem`, `allow_code_execution`, `allow_delegation`, `max_context_tokens`,
`allowed_tools`) — i.e., aegis bakes the _permission envelope_ into the genesis record.

> **Reuse note:** loom is the more mature, git-native form (it rides on commit-signing keys
> the team already has + GitHub server-side rulesets). aegis demonstrates the same trust
> chain as an **application-runtime artifact** (Ed25519 keypair, JSON anchors, capability
> envelope in genesis) — which is closer to what a _product backend_ would do for a tenant
> that does not live in git. **The product likely wants aegis's runtime shape backed by
> loom's git-native rigor.**

---

## 3. Claim classes & conflict resolution (SAME / ADJACENT / INDEPENDENT)

### 3.1 The adjacency relation

Conflict semantics are the heart of multi-operator coordination
(`multi-operator-coordination.md` §3, evaluated by `adjacency.js`):

| Class           | Definition                                                                                                               | Lease severity          | Behavior                                                                                                 |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------- | -------------------------------------------------------------------------------------------------------- |
| **SAME**        | exact path/glob match; active claim contains the path; same-commit cohort; phase collision; composed-invariant collision | **`halt-and-report`**   | Session halts; operator adjudicates. Claim record is **NOT** appended (prevents the F2-1 race-to-write). |
| **ADJACENT**    | same dir / workspace / parent-child within 1 level / journal thread                                                      | **`advisory`**          | Banner surfaced; claim written with `granted_relation: "ADJACENT"`; operator MAY proceed.                |
| **INDEPENDENT** | otherwise                                                                                                                | **silent + auto-claim** | Claim written; silent success.                                                                           |

The single `block`-severity exception (filesystem transport only): cross-worktree contention
where `git status --porcelain` shows the exact target file uncommitted-modified on a sibling
worktree.

### 3.2 The claim-then-edit ordering is the structural defense

MUST-2: a SAME-class edit **MUST be preceded by a successful `/claim`**. Editing-then-claiming
retroactively is BLOCKED — "a retroactive claim cannot prevent the contest it documents"
(§3 Why). This is the discipline that converts a silent concurrent-edit (the "F2-1 residual")
into a deterministic pre-edit gate.

### 3.3 Mapping conflict classes onto general knowledge work

For the product, the adjacency classes translate directly to **work-item conflict**:

| Code-edit class                                | General-knowledge-work analogue                                                                                                                                                            |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **SAME** (two operators editing the same file) | Two workers (human or agent) claiming the **same `AgenticRequest`** — e.g., both drafting section 2 of the 3Q report. → **halt-and-report**; second claimant must defer or re-scope.       |
| **ADJACENT** (same dir / workspace)            | Two workers on **sibling tasks of the same objective** — e.g., one drafts section 2, another drafts section 3 of the same report. → **advisory**; surface "alice is on the adjacent task." |
| **INDEPENDENT** (unrelated paths)              | Workers on **unrelated objectives** — e.g., the 3Q report vs. the marketing deck. → silent.                                                                                                |

> **Synthesis takeaway #3 — conflict resolution is already the right shape.** The product
> does NOT need to invent a locking protocol. It needs to (a) define the adjacency relation
> over the _work-item DAG_ (`AgenticRequest.depends_on`) instead of over the file tree, and
> (b) decide whether SAME-class on a knowledge-work item is `halt` (one worker at a time) or
> a _merge surface_ (both contribute, then a `ReviewDecision` reconciles). loom's
> `lease-override` record (gated by `gate-approval`) is the existing primitive for "two
> operators deliberately co-work a SAME-class scope with a recorded override."

### 3.4 Leases, staleness, and the reap ceremony

Claims are **leases** — they can go stale. The stale-lease reap protocol
(`release-claim.md` § Cross-operator reap; `multi-operator-coordination.md` §3.4) handles
"a worker walked away mid-task":

- **Self-release** — operator releases own claim (signed `release` record).
- **Cross-operator reap** (`--reap --cosigner`) — releases a _stale sibling_ claim. Requires:
  (a) a **distinct-`person_id` cosigner** + co-signature, (b) the pinned victim heartbeat
  must be older than `now - LIVENESS_TTL`, and (c) no victim heartbeat with higher `seq`.
  Three bases: `co-signed`, `owner-2-of-N`, `self-reap`.

For the product, this is exactly **"reassign an abandoned task safely"** — but with
cryptographic proof that the original worker was genuinely idle (the pinned-heartbeat
predicate) and that a _second distinct human_ authorized the reassignment (the cosigner). It
prevents the "manager silently reassigns your work and claims you abandoned it" abuse.

---

## 4. Identity, roster & attribution

### 4.1 The identity triple

Operator identity (`multi-operator-coordination.md` §1) is a triple:

- **`display_id`** — advisory, human-readable ("alice"). Collisions are harmless. **Tooling
  MUST attribute via `verified_id`, never `display_id`.**
- **`verified_id`** — fingerprint of a commit-signing key; authenticates a _record_.
- **`person_id`** — **the unit of authority**. One `person_id` → one human → `role` + enrolled
  keys. Immutable; keys are append-only under a `person_id`. Adding a key or `person_id` is a
  **2-of-N quorum roster edit**.

`host_role: ci` identities are **audit-only** — NEVER eligible to co-sign owner-quorum,
distinctness, gate-approval, or genesis/migration records. (This is the structural defense
against a deploy key being used as a "second human" to fake a quorum.)

### 4.2 The roster

`~/repos/loom/.claude/operators.roster.json` (validated by
`operators.roster.schema.json`) is the registry. The live loom roster maps
`pid-esperie-10e7dd16 → {display_id: esperie, role: owner, github_login: esperie,
host_role: human, keys: [{type: gpg, fingerprint: 548F…, pubkey: <armored>}]}`, plus a
`genesis` block pinning `repo_owner`, `root_commit`, `genesis_generation`.

Registration is PR-only (`whoami.md § --register`): `/whoami --register` cuts a
`codify/<display_id>-<date>` branch, schema-validates the proposed roster row, and opens a
PR. **NEVER writes directly to `main`** — branch protection on `operators.roster.json`
enforces the PR + review flow. New operators default `role: contributor`; promotion to
`senior`/`owner` is a separate quorum gate.

### 4.3 The `/whoami` identity surface

`/whoami` (no args, read-only) resolves the active operator via
`operator-id.js::resolveIdentity(cwd)` (signing-key fingerprint → roster lookup → tuple) and
prints `display_id / person_id / verified_id / role / host_role / posture`. Three shapes:
**rostered** (full identity), **un-rostered key** (`(unregistered)` + `next: /whoami
--register`, `posture: L2_SUPERVISED`), **no signing key** (`next: configure signing key`).

> **Synthesis takeaway #4 — attribution is cryptographic, not nominal.** This is the
> backbone of the brief's "every activity and output is traced and made transparent"
> (3f) and "attributable" requirement. Every record — every claim, every artifact anchor,
> every governance approval — is signed by a `verified_id` that resolves to exactly one
> `person_id` (one human). For the product, **agents inherit their operator's identity**
> today (an agent's edits ride on the operator's signed session records). Net-new for the
> product: giving _agents their own enrolled signing identity_ (a `host_role: agent` analogous
> to `host_role: ci`) so an agent's autonomous output is attributable to the **agent** AND
> to the **human accountable for it** — a two-level attribution the brief's
> human↔agent transparency requirement implies.

### 4.4 Team-memory & the decisions log

Two more shared-knowledge surfaces:

- **Team-memory** (`knowledge-convergence.md` MUST-4): shared, signed facts, **one fact per
  file** at `.claude/team-memory/<slug>.md` (an aggregate file is BLOCKED — it would
  re-introduce multi-writer contention). Each file carries frontmatter `promoted_by`,
  `signed`, `body_anchor` stamped by `coc-append.js` at promotion. Live example:
  `~/repos/loom/.claude/team-memory/canonical-build-targets.md` (a signed shared fact about
  build targets). **This is the team's shared, attributable, tamper-evident institutional
  memory** — the product analogue of "what the team knows and has agreed."
- **Decisions log** (the journal `DECISION-` entries): every `/codify` ships journal entries;
  `/onboard` surfaces "recent decisions" (last 5 `DECISION`/`DISCOVERY`/`DEFER` entries).
  Journal slot reservation reads from the _fold_ (not the filesystem) and emits a signed
  `journal-body-anchor` record pinning the body's SHA-256 (`knowledge-convergence.md`
  MUST-2), so tamper is detected at fold-time and **names the anchor's signer**.

---

## 5. The codify-lease — single-writer discipline

When N operators co-work, every artifact that historically had _one writer per session_
becomes a multi-writer contention surface (`knowledge-convergence.md`). The **codify lease**
(`codify-lease.js`) is the single-writer primitive for the knowledge-convergence path.

### 5.1 Mechanism

`/codify` Step 0 (`knowledge-convergence.md` MUST-3): `acquireCodifyLease({displayId,
scopeFiles})` BEFORE any artifact edit. The lease:

- **Unions `scopeFiles` with `MANDATORY_SCOPE`** automatically (`.claude/.proposals/latest.yaml`
  - `.claude/learning/learning-codified.json`) — callers cannot opt out
    (`codify-lease.js:69`, `MANDATORY_SCOPE`).
- On **conflict** (`{ok: false, reason: "conflict"}`) — surfaces the conflicting `display_id` +
  `acquired_at` + scope overlap verbatim and **STOPs** (`codify-lease.js:261-295`).
- On success — all edits land on `codify/<display_id>-<date>` branch; end-of-session opens a
  PR + admin-merge.
- Release via `releaseCodifyLease({repoDir, displayId})` — the helper derives `leasePath`
  internally (callers cannot misroute, Sec-MED-3).

The lease file is written **atomically** (`_atomicWriteJson`, `.tmp` + `rename`) and
fingerprints its scope (`_scopeFingerprint`, `codify-lease.js:105`). Live example
(`~/repos/loom/.claude/learning/codify-lease.json`): a released lease for `esperie` on branch
`codify/esperie-2026-06-05` covering 3 scope files, with `_released: true` + `released_at`.

### 5.2 Why this is the right primitive for the product

> **Synthesis takeaway #5 — single-writer-with-lease generalizes to "who owns this
> deliverable right now."** Two concurrent `/codify` sessions writing `latest.yaml` would
> last-writer-wins clobber one operator's entire knowledge-extraction cycle. The lease
> _races for the branch namespace, not the working tree_ — it converts silent loss into a
> loud, named conflict ("esperie holds the codify lease on branch X since T"). For general
> knowledge work, this maps to: **a deliverable (artifact) under active authorship has a
> single-writer lease; a second author is told who holds it and on what branch/version**,
> and the merge happens through PR review (= `AgenticReviewDecision`). The brief's "old
> outputs are versioned" (3e) is exactly the branch/PR + `AgenticArtifact.version` +
> `parent_artifact_id` chain.

---

## 6. Onboard & certify — the lifecycle for joining a team

### 6.1 `/onboard` — deterministic read-path

`/onboard` (`commands/onboard.md` + `skills/41-onboard/SKILL.md`) is a **read-only**
command — writes ZERO state. It surfaces shared state in **fixed order** so two operators
see consistent state: **Operator identity → Team Memory → Workspace → Posture → Active Claims
→ Codify Lease → Rules Changed → Action Items**. Every read goes through an existing helper
(table in `41-onboard/SKILL.md` lines 20-29):

- Identity → `operator-id.js::resolveIdentity()` (un-rostered → stop + `/whoami --register`)
- Team-memory → readdir + per-file `integrity-guard.js` validation (integrity-fail = treated
  as absent, never displayed as authoritative)
- Posture → `state-io.js::readPosture()` (fail-closed L1 surfaced verbatim)
- Claims → `coordination-log.js::foldLog()` active-claim slice
- Codify lease → `codify-lease.js::readActiveLease()` (names holder + branch + acquired_at)

`/onboard` is the answer to **"who am I AND what is the whole team doing right now"** — a
single deterministic snapshot. The brief's team-oriented interface needs exactly this: a
new participant (human or agent) gets the complete shared-state surface before acting.

### 6.2 `/certify` — brief → probe → gate at 100%

`/certify` (`commands/certify.md` + `skills/42-certify/SKILL.md`) is the **knowledge gate**
before a new dev/consultant claims non-trivial work. Three phases:

- **Brief** — walk the critical surfaces (specs index, baseline rules, posture, team-memory,
  recent decisions) in fixed order; write scrubbed read-receipts.
- **Probe** — present a **curated question bank** (`specs/_certification.yaml`, NOT
  LLM-generated) easy→hard. **NO Claude-assistance during the gate** — enforced
  _structurally_ by a lockfile (`.certify-in-probe-<verified_id>.lock`) that activates a
  `probe-phase-guard.js` PreToolUse hook emitting `severity: block` on every retrieval call.
- **Gate at 100%** — strict; failed questions loop (re-read cited section → retry) until all
  pass. Pass writes a **signed journal `DECISION` receipt** via the canonical
  slot-reservation + body-anchor helpers (hand-writing is BLOCKED). Until pass, the operator
  stays `L2_SUPERVISED`.

> **Synthesis takeaway #6 — onboarding/certification is the "richer agent context"
> hypothesis made concrete.** The brief argues agents talk to agents with more context than
> humans give humans. `/certify` is the _inverse-direction proof of the same principle_:
> before a participant acts, the system **verifies they hold the load-bearing context** —
> and records cryptographic proof they passed. For the product, a new **agent** joining a
> team workspace can be `/certify`-gated against the team's domain bank exactly like a human
> — and the agent, by construction, can load the entire brief + team-memory + decisions log
> losslessly (the very advantage the brief hypothesizes). The certification receipt is the
> attributable "this participant knows the surface" anchor.

---

## 7. Cryptographic trust anchors (aegis + loom)

The brief calls out aegis as "the closest existing implementation of the posture +
interveneable steps idea." The trust-anchor stack:

### 7.1 loom: git-native, server-enforced

- **Genesis anchor** (fold rule 9): first signed `genesis-anchor` record is the trust root;
  carries `gh_api_owner_capture` (proves repo ownership via live `gh api`) + signed root
  commit. Live in the loom log (seq 0).
- **`refs/coc/**`GitHub ruleset** (MUST-5): a server-side ruleset with FOUR rule types —`creation`+`deletion`+`non_fast_forward`+`required_signatures` — so the coordination
  log's git refs cannot be created/deleted/force-pushed/unsigned by anyone outside the
  bypass-allowlisted operator identities. **This is the prevention layer**: the GitHub server
  itself refuses a forged ref. (Confirmed-prevention verdict, journal/0125.)
- **Generation rotation + genesis-migration** (MUST-4/MUST-7): relocating the trust root
  requires 2-of-N owner co-signatures + a fresh external `gh api` owner check + a monotonic
  `genesis_generation` increment. Under single-owner N=1, org-owned repos may substitute a
  fresh **gh-api-bound org-admin attestation** (the live loom genesis-migration record at
  seq 1 demonstrates exactly this).

### 7.2 aegis: runtime keypair + capability genesis

- **Ed25519 keypair per org** (`proj-*/keys/{private,public}.key`) + `genesis.json` carrying
  `public_key_hex` and a **capability/constraint envelope** (`allow_network`,
  `allow_code_execution`, `allow_delegation`, `max_context_tokens`, `allowed_tools`).
- **Signed anchor chain** (`anchors/anc-*.json`) with `parent_anchor_id` linking + per-record
  `signature` + `record_hash`.
- **`manifest.json`** tracks `anchor_count`, `last_anchor_id`, `trust_posture` (the live one
  reads `"Full"`).

> **Synthesis takeaway #7 — the product needs both forms.** loom's server-enforced ruleset
> is the right model when the team's substrate lives in git (developer-shaped). aegis's
> runtime keypair + capability-genesis is the right model when the substrate is a **product
> backend serving non-developer tenants** (the product's actual target). The reusable
> insight is identical across both: **a signed, chained, externally-anchored trust root, and
> a posture/capability envelope bound into it.** Net-new is choosing/blending the storage
> substrate for a multi-tenant SaaS (likely: aegis-shape runtime records, with loom-shape
> external anchoring against the tenant's identity provider instead of GitHub).

---

## 8. Posture, permission envelopes & the interveneable-step model

### 8.1 The L1–L5 ladder

Both repos ship the same posture ladder (`trust-posture.md`, identical in
`Sequor/.claude/rules/` and `aegis/.claude/rules/`):

| Posture                   | Agent CAN do unilaterally                                          | Requires human gate                              |
| ------------------------- | ------------------------------------------------------------------ | ------------------------------------------------ |
| **L5_DELEGATED**          | plan + implement + commit + open PR; parallel agents; full /codify | cross-repo writes; release tags; destructive ops |
| **L4_CONTINUOUS_INSIGHT** | L5 + mandatory journal per shard + redteam Round 1 before merge    | posture upgrade; multi-shard releases            |
| **L3_SHARED_PLANNING**    | edit + run tests; one shard at a time                              | plan approval before implement; PR creation      |
| **L2_SUPERVISED**         | read; propose diffs; run linters                                   | every Edit/Write; every commit                   |
| **L1_PSEUDO_AGENT**       | propose plans + diffs in chat                                      | everything that touches the working tree         |

aegis's live anchor data uses a parallel named ladder (`Restricted → Supervised → Autonomous
→ Full`) in its `posture-*-to-*` transition anchors — the same graduated-autonomy concept,
runtime-named.

### 8.2 The brief's posture example maps 1:1

The brief's posture choices map directly onto this ladder:

| Brief posture                                 | Ladder posture                 | Behavior                                                                    |
| --------------------------------------------- | ------------------------------ | --------------------------------------------------------------------------- |
| **L5 Autonomous** ("agent goes ahead")        | **L5_DELEGATED**               | agent plans + executes the 3-agent fan-out unilaterally                     |
| **L4 Supervised** ("asks for one permission") | **L4_CONTINUOUS_INSIGHT / L3** | one approval gate before executing (an `AgenticDecision` `governance_hold`) |
| **L3 Step-by-step** ("pauses at each step")   | **L3_SHARED_PLANNING / L2**    | pauses at each request boundary; each step is a `Decision`                  |

### 8.3 Upgrade is human-gated; downgrade is automatic

The asymmetry (`trust-posture.md` MUST-3): **downgrades fire on detection** (no human),
**upgrades require human approval** (challenge-nonce paste-back; the agent CANNOT
self-promote). Downgrade triggers (MUST-4) are cumulative (3× same-rule / 5× total in 30d)

- emergency (instant, e.g. destructive-op-without-confirm → drop to L1). Upgrade requires
  all four: ≥7 days at posture + 0 violations of the triggering class + a demonstrated
  proactive correction + human challenge-nonce.

> **Synthesis takeaway #8 — the interveneable-step model already exists as posture +
> AgenticDecision.** Brief 3e ("surface decisions on screen, recorded; choose a posture
> beforehand; retrace any step and intervene") is the _union_ of three existing primitives:
> (1) the **posture ladder** sets how much the agent does before pausing; (2) every pause is
> an **`AgenticDecision`** row (recorded, with `required_approvals`, `constraint_dimension`);
> (3) **versioned artifacts** (`AgenticArtifact.version` + `parent_artifact_id`) realize
> "retrace any previous step and intervene; downstream outputs change accordingly but old
> outputs are versioned." The coordination log is the recorded transcript binding them.

---

## 9. Multi-operator lifecycle hooks (the runtime enforcement layer)

The substrate is enforced by **hooks** at lifecycle boundaries
(`multi-operator-coordination.md` §5 + §2; aegis `~/repos/dev/aegis/.claude/hooks/`):

| Hook                             | Lifecycle moment                           | Role                                                                                                                                                                  |
| -------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `multi-operator-sessionstart.js` | session-start (advisory, zero-network)     | surfaces identity, sibling sessions + claims + override counts, operative posture, rules-changed, team-memory index, ref-regression check, revocation-contest surface |
| `multi-operator-sessionend.js`   | session-end (never blocks)                 | releases own claims; appends `compaction-checkpoint` if triggered; regenerates `.session-notes` atomically                                                            |
| `integrity-guard.js`             | pre-tool-use (Edit/Write on watched paths) | blocks writes off a `codify/<id>-<date>` branch                                                                                                                       |
| `adjacency-leasecheck.js`        | pre-tool-use                               | enforces MUST-2 (SAME-class claim discipline); emits the §4.2 filesystem-exception `block`                                                                            |
| `operator-gate.js`               | pre-tool-use (gated invocations)           | enforces 4-eyes: rejects `gate-approval` where approver `person_id` == requester OR same GitHub-login (MUST-3); `host_role: ci` never eligible                        |
| `genesis-anchor-guard.js`        | pre-tool-use                               | trust-root enforcement (fresh-consumer vs enrolled-then-deleted discrimination)                                                                                       |
| `signing-mutation-guard.js`      | pre-tool-use                               | degraded-mode read-only via working-tree-mutation predicate                                                                                                           |
| `journal-write-guard.js`         | pre-tool-use                               | blocks journal writes when file already on disk / slot unreserved                                                                                                     |
| `probe-phase-guard.js`           | pre-tool-use (during /certify probe)       | `block` on every retrieval call while the certify lockfile exists                                                                                                     |

aegis ships a parallel runtime hook set: `posture-gate.js`, `session-start.js`,
`session-end.js`, `detect-violations.js`, `pre-commit-branch-scope.js`,
`validate-bash-command.js` (the last one fired a false-positive `block` on a read during this
very research session — evidence the enforcement teeth are live).

### 9.1 The gate matrix (4-eyes on person_id)

The owner-gate (MUST-3) is the **two-distinct-humans approval** primitive:
`operator-gate.js` resolves the signed `gate-approval` key → `person_id` and **rejects iff
approver `person_id` == requester OR (owner/senior gates) same bound GitHub-collaborator
login.** A second `verified_id` under the same `person_id` is the same human → blocked. This
is the existing implementation of "two-person authorization" for high-stakes actions.

> **Synthesis takeaway #9 — the hooks are the "transparent AND interveneable" enforcement.**
> The brief wants every human↔agent and agent↔agent step transparent and interveneable.
> The hook layer is _where intervention is structurally possible_: a pre-tool-use guard can
> `halt-and-report` (surface for human decision) or `block` (structural refusal) at exactly
> the moments the brief cares about — before an agent edits a claimed scope, before a
> gated action proceeds, before the trust root is touched. The product re-uses this layer
> by re-targeting the watched surfaces from _file paths_ to _work-item operations_.

---

## 10. The central synthesis — mapping codebase-coordination onto general knowledge work

### 10.1 The mapping table

| Coordination concern                     | Today (codebase)                                     | Product (general knowledge work)                                                | Reuse verdict                            |
| ---------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------- |
| **Unit of work**                         | file / glob / workspace (loom `claim.path`)          | `AgenticObjective → Request → WorkSession → Artifact` (pact)                    | **Reuse** (pact already models it)       |
| **Who can claim**                        | rostered operator via `verified_id`/`person_id`      | rostered human OR enrolled agent (`host_role: agent`)                           | **Extend** (add agent identity class)    |
| **Conflict resolution**                  | SAME/ADJACENT/INDEPENDENT over file tree             | same classes over the work-item DAG (`Request.depends_on`)                      | **Reuse** (re-target adjacency relation) |
| **Attribution**                          | signed coordination-log records + roster             | same log, `content.request_id` ⟶ work item; agent + accountable-human two-level | **Reuse + extend**                       |
| **Accountability / audit**               | append-only signed JSONL + fold rules + body-anchors | same log = the "every step traced" transcript                                   | **Reuse directly**                       |
| **Single-writer on a deliverable**       | codify lease (branch namespace)                      | lease over an `Artifact` under authorship; merge via `ReviewDecision`           | **Reuse (generalize scope)**             |
| **Posture / interveneability**           | L1–L5 ladder + hooks                                 | same ladder; pauses = `AgenticDecision` rows                                    | **Reuse directly**                       |
| **Trust root**                           | git genesis-anchor + `refs/coc/**` ruleset           | aegis-shape runtime keypair anchored to tenant IdP                              | **Reuse pattern; re-substrate**          |
| **Onboarding**                           | `/onboard` deterministic read-path                   | tenant/workspace state snapshot for any participant                             | **Reuse directly**                       |
| **Knowledge gate**                       | `/certify` brief→probe→gate@100%                     | domain-bank certification for humans AND agents                                 | **Reuse directly**                       |
| **Versioning ("old outputs preserved")** | branch/PR + journal body-anchors                     | `Artifact.version` + `parent_artifact_id` + signed anchor                       | **Reuse (pact + loom anchors)**          |

### 10.2 Is agent↔agent communication actually richer/less lossy? What the machinery says

The brief _hypothesizes_ it; the substrate _supports the hypothesis structurally but does
not yet realize the channel_:

- **Supports it:** the coordination log is a **lossless, signed, totally-ordered (per-emitter)
  transcript**. Fork detection makes equivocation a cryptographic contradiction. An agent
  reading the fold has the _complete_ shared-state context (every claim, every decision,
  every artifact version) — far more than a human reading a Slack thread. The team-memory +
  decisions log + specs are loadable in full. This is the "wealth of info and memory agents
  can use" the brief describes.
- **Does NOT yet realize it as a channel:** today, agents do not write coordination records
  _as themselves_ — they ride on their human operator's signed session. Agent↔agent
  coordination today is _mediated through the human's identity_. The net-new work to realize
  the brief's hypothesis: **give agents enrolled identities + let them append claim/decision/
  artifact records directly**, with the accountable human bound as a co-attribution. Then
  agent A claiming a `Request`, agent B reading the fold and respecting the claim, and both
  surfacing their `WorkSession` cost/verdicts to the human IS the richer-than-human channel
  the brief predicts — and it is _auditable in a way human↔human comms can never be_.

### 10.3 What's reusable vs net-new (the 80/15/5 read)

**Reusable (~80% — the substrate exists and runs):**

- coordination log + 10 fold rules + signing + chaining + fork detection (`coc-append.js`,
  `coordination-log.js`, `multi-operator-coordination.md`)
- claim / claims / release-claim / reap commands + adjacency relation (`adjacency.js`,
  `claim.md`, `release-claim.md`)
- roster + identity triple + `/whoami` register ceremony (`operator-id.js`,
  `operators.roster.json`, `whoami.md`)
- codify lease single-writer discipline (`codify-lease.js`)
- posture ladder + downgrade/upgrade asymmetry + gate matrix (`trust-posture.md`,
  `operator-gate.js`)
- lifecycle hooks (session-start/end, integrity-guard, adjacency-leasecheck, operator-gate,
  genesis-anchor-guard)
- `/onboard` + `/certify` lifecycle (`41-onboard`, `42-certify`)
- team-memory + decisions-log + body-anchor versioning (`knowledge-convergence.md`)
- pact work-item ontology (`AgenticObjective/Request/WorkSession/Artifact/Decision/ReviewDecision`)
- aegis cryptographic trust anchors + capability-genesis (`proj-*/genesis.json`, `anchors/`)

**Adaptation (~15% — re-target existing primitives):**

- generalize the _claimable scope_ from file path to `request_id` (claim record `content`
  field swap)
- re-target the _adjacency relation_ from the file tree to the work-item DAG
- re-substrate the trust root from GitHub-`refs/coc/**` to a multi-tenant backend anchored
  to the tenant's IdP (aegis runtime shape)
- generalize the _codify lease_ to a generic "deliverable-under-authorship" lease

**Net-new (~5% — genuinely new):**

- **agent identity class** (`host_role: agent`) with two-level attribution (agent +
  accountable human)
- **direct agent→log writes** (agents append claim/decision/artifact records as themselves)
- **non-developer UI** surfacing the log/posture/claims as a screen (today: CLI prose + JSONL)
- the **agent↔agent channel** as a first-class transport (today: mediated through the human)

---

## 11. Risks & open questions

1. **Cardinality at scale.** The substrate is designed for "~12 operators" against one repo
   (`knowledge-convergence.md` Rule 2 rationalization). A product team workspace may have
   hundreds of agents + humans. The fold cost is O(log length); compaction-checkpoints exist
   but their scaling to product cardinality is unproven. **Open: does the fold survive
   10K+ participants / 1M+ records?**
2. **SAME-class on knowledge work: halt vs merge.** For code, SAME-class halts (one writer).
   For a report section, two contributors merging may be _desirable_. The product must decide
   per-work-item-type whether SAME is halt or merge-surface. `lease-override` is the existing
   override primitive but it is heavyweight (gate-approval).
3. **Advisory vs enforced.** loom claims are _advisory_ (the human can ignore the banner).
   For autonomous agents, advisory may be insufficient — an agent must _honor_ the claim
   structurally. **Open: are claims enforced (block) or advisory (banner) when the claimant
   is an agent at L5?**
4. **Agent attribution without a human in the loop.** If an L5 agent acts autonomously, the
   "accountable human" binding must be established _at delegation time_, not at action time.
   pact's `envelope_id` + `AgenticDecision.envelope_version` (TOCTOU defense) is the likely
   anchor, but the agent-identity-enrollment ceremony does not exist yet.
5. **aegis vs loom substrate choice.** The two implementations have diverged (loom is
   git-native + actively developed; aegis's coordination-log is empty — it uses the
   anchor-chain + posture-state-machine form). **Open: which substrate is the product's
   backbone, or is it a synthesis?** The brief names aegis as "closest," but loom's
   coordination-log machinery is the more complete coordination implementation.
6. **GHES / non-GitHub anchoring.** loom's prevention layer (`refs/coc/**` ruleset) is
   GitHub-specific. A product backend not on GitHub needs an equivalent server-side
   prevention anchor (the aegis runtime keypair is detection-grade, not server-prevention-grade
   unless backed by an IdP that refuses forged records).
