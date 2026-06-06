# User Flow 03 — Team Collaboration: Multi-Human + Multi-Agent on One Shared Objective

> **What this flow shows.** Two humans and several agents co-working on a single shared
> objective, on the platform, end to end. It walks: how work is **claimed** (claims/leases,
> SAME/ADJACENT/INDEPENDENT); how **handoffs** carry full context/memory (human↔agent and
> agent↔agent — the rich path — versus the lossy human↔human path); how each working step is
> **attributed and transparent and interveneable**; how one teammate **retraces and intervenes**
> on another teammate's agent's step under governance; and how the **coordination log** makes
> the whole thing auditable.
>
> **Which moat this is.** This is **M3 — the multi-human + multi-agent shared substrate** —
> and it is the flow that puts the brief's hypothesis (brief §3d: _agent-mediated communication
> is richer and less lossy than human-to-human_) **in action**. It also shows, honestly, the
> **guardrail** the risks analysis insists on: ambiguity-preservation (an off-the-record mode)
> and a **named human on every consequential decision**. The hypothesis is a research BET, not a
> settled fact — this flow markets it only as far as the evidence reaches.
>
> **Grounding.** Brief: `briefs/01-vision.md` §3d/§3e/§3f. Analysis:
> `01-analysis/01-research/02-multi-operator-coordination.md` (the coordination substrate),
> `01-analysis/09-risks-failure-points.md` §3 (the unproven agent-comms hypothesis + the
> guardrail), `01-analysis/06-network-effects.md` §6 (COLLABORATION as a true network effect).
> Ecosystem DNA cited by path. Uncertainty is flagged inline. Effort is in **autonomous
> execution cycles**, never human-days.

---

## 0. Read this first (plain language)

Today, a team doing a piece of work together lives in **five tools at once and a sixth where
they argue about it**: the doc, the spreadsheet, the chat thread, the email chain, the project
tracker, and the meeting. The work is in the tools; the **coordination** is in the chat and the
meeting — and the chat and the meeting are exactly where things get lost. "I thought you were
doing that." "Which version is current?" "Who decided this?" "Wait, did we agree on X or Y?"
Those are not edge cases; they are the daily texture of team knowledge work.

The platform's claim is narrow and specific, and it is worth stating precisely because the
risks analysis (`09` §3) warns against over-claiming it:

- **For HANDOFFS and COORDINATION** — "you take section 2, I'll take section 3," "pull the Q3
  numbers and give them to the report agent," "this draft is ready for your review" — the
  platform makes the transfer **lossless and recorded** instead of a lossy sentence. This is the
  half of the brief's hypothesis the evidence supports (`09` §3.1, `02` §4.1).
- **For RELATIONSHIPS, JUDGMENT, and DELIBERATELY-AMBIGUOUS talk** — "let's see how Q3 goes,"
  the hallway conversation where trust gets built, the thing you say off the record — the
  platform does **not** force these into a complete recorded objective. It ships an explicit
  **informal mode** for exactly this (`09` §3.4). Forcing ambiguity into a permanent record is a
  legal-discovery hazard and a relationship hazard, and the platform refuses to do it
  (`09` §3.1 point 3).

So the one-sentence version: **the platform makes the team's coordination lossless and
auditable, while deliberately preserving the human's ability to be vague, informal, and
off-the-record — and it keeps a named human accountable for every consequential decision.**

Everything below is one worked scenario showing both halves.

---

## 1. The scenario — "The Q3 board report"

Two humans, several agents, one objective.

| Participant    | Who/what                 | Role in this scenario                                        |
| -------------- | ------------------------ | ------------------------------------------------------------ |
| **Priya**      | Human, Head of Finance   | Owns the objective; sets posture; makes consequential calls  |
| **Marcus**     | Human, FP&A analyst      | Co-works section 2; later intervenes on Priya's agent's step |
| **agent-fin**  | Agent, claimed by Priya  | Pulls ledger data, drafts the financials (section 2)         |
| **agent-narr** | Agent, claimed by Marcus | Drafts the narrative/commentary (section 3)                  |
| **agent-rev**  | Agent, claimed by Priya  | Reviews + assembles the final report                         |

The objective: **"Produce the Q3 board report."** In the platform's work-item model (which
pact already supplies, `02` §1.2), this is a single **Objective** that decomposes into
**Requests** (decomposed tasks), each worked in a **WorkSession** (with cost/token tracking),
each producing a **versioned Artifact**, with **Decision** rows wherever a human gate fires.
The mapping is exact and is reused, not invented (`02` §1.2, §10.1).

```
Objective: "Q3 board report"  (submitted_by: Priya, status: active)
  ├─ Request: "section 2 — financials"   (claimed_by: agent-fin,  accountable: Priya)
  ├─ Request: "section 3 — narrative"    (claimed_by: agent-narr, accountable: Marcus)
  └─ Request: "assemble + review"        (claimed_by: agent-rev,  accountable: Priya)
        depends_on: [section 2, section 3]
```

> **Why this matters for the reader.** You do not have to learn a new project-management model.
> You state an objective in one place. The agent proposes the decomposition into tasks **on
> screen, before doing anything** (brief §3e). You approve, adjust, or take over. The structure
> is the agent's first draft, and you supervise it — you don't build it.

---

## 2. Setting up the room — onboarding and posture (before anyone touches the work)

### 2.1 Each participant gets one deterministic snapshot of "what's going on"

Before Priya or Marcus does anything, each opens the shared workspace and gets the **same**
fixed-order snapshot of team state: who they are, what the team already knows, what's claimed
right now, what posture is in force, what's changed (`02` §6.1, the `/onboard` read-path). It is
read-only — it writes nothing — so two people opening it at the same moment see consistent
state. This is the platform's answer to **"who am I AND what is the whole team doing right
now"** in one screen instead of five Slack scrolls.

```
Priya opens the Q3-board-report workspace:

  YOU: Priya (Head of Finance) — verified
  TEAM KNOWS: 4 shared facts (Q3 close date, board template, …)
  ACTIVE NOW: Marcus is here (no claims yet)
  POSTURE: this objective runs on "Ask me once" (you approve the plan once, then it runs)
  RECENT DECISIONS: 2 (Q2 report sign-off, FY guidance change)
  NEXT: state the objective, or claim a task
```

> **Plain-language note.** "Verified" means the platform knows this is really Priya, by a
> cryptographic key tied to one person — not a display name anyone could copy (`02` §4.1). This
> is load-bearing later: when Marcus intervenes on Priya's agent's step, the record of who did
> what cannot be faked or mis-attributed (`02` §4, "attribution is cryptographic, not nominal").

### 2.2 Posture is chosen beforehand, per objective — the interveneable-step model

Priya sets the **posture** for this objective before work begins (brief §3e; `02` §8.2). Posture
is "how much the agents do on their own before they pause for a human." The user sees **three
plain-language buttons**; each maps onto one rung of the engine's internal ladder (the L-number
is engine-internal and pinned at `04-trust-posture…` §1.2 — the user never types it):

| Button (what the user sees) | What the agents do                                                   | Plain-language meaning           | Engine rung (internal) |
| --------------------------- | -------------------------------------------------------------------- | -------------------------------- | ---------------------- |
| **"Go ahead"**              | Plan + execute the whole fan-out on their own, inside scope          | "Go; show me the result"         | `AUTONOMOUS` (L5)      |
| **"Ask me once"**           | Auto-run inside scope after **one** approval at the plan→do boundary | "Show me the plan, then run it"  | `DELEGATING` (L4)      |
| **"Step through"**          | Pause for approval at **every** consequential step                   | "Ask me before each real action" | `SUPERVISED` (L3)      |

Priya chooses **"Ask me once"** for the Q3 report: she approves the plan once at the start, and
the agents then draft and execute freely inside the agreed scope and budget. The only thing that
re-interrupts her is a step trying to go **outside** scope — past the spend cap, or into a data
type the envelope forbids — which flips to a hold. This is not a setting she has to re-confirm
mid-flight; it is the operating envelope she sets once, and the agents execute inside it.
**Human-on-the-loop, not in-the-loop.** (Had she wanted a pause at _every_ consequential step —
each system-of-record write, each external send, each board number committed — that is the
**"Step through"** button, the most hands-on posture for high-stakes work.)

> **Recommendation (carried from the risks analysis, stated as the platform's default).** New
> teams should **start every objective on "Step through" or "Ask me once" and earn "Go ahead"
> per-task-class on evidence** (engine-internal: start at L3/L4, earn L5), not
> start autonomous (`09` §6.1). The trace itself is the trust-building instrument: you watch the
> agents prove themselves on the low-stakes steps, then grant autonomy where the record shows
> they're reliable.
>
> **Pro:** the buyer never has to trust the agent on day one — they trust the **trace**, which
> matches how they already trust a new human employee (`09` §6.1).
> **Con (real, not glossed):** a team that starts fully-supervised takes **longer to feel the
> "wow"** of end-to-end autonomy, which lengthens the path to obvious ROI (`09` §6.1). The
> mitigation is that legibility makes the supervised phase fast — but legibility is itself the
> hard bet (`09` §2), so this default leans on M1's transparency actually being readable.

---

## 3. Claiming the work — claims, leases, and the three conflict classes

This is the heart of "multiple people + agents on one substrate without stepping on each other."
The platform reuses, almost unchanged, the coordination substrate that already runs today
(`02` §0, §3). The unit being claimed generalizes from "a file" to "a **task** (Request)" —
which the analysis flags as a **field-level change, not an architectural one** (`02` §1.1
synthesis takeaway #1).

### 3.1 A claim is a lease, not a lock

When a participant (human **or** agent) starts on a task, they **claim** it. A claim is an
**advisory lease** — it announces "I'm working here" and surfaces conflict; it does not hard-lock
the work (`02` §1.1). The claim is written as a **signed record** in the coordination log, so it
is attributable and tamper-evident (`02` §3.1).

### 3.2 The three conflict classes (this is the whole mechanism)

When someone claims a task, the platform computes how that claim **relates** to everyone else's
active claims, and behaves accordingly (`02` §3.1, §3.3):

| Class           | When it fires                                          | What happens                                                          | Plain-language                                                 |
| --------------- | ------------------------------------------------------ | --------------------------------------------------------------------- | -------------------------------------------------------------- |
| **SAME**        | Two workers claim the **same task**                    | **Halt-and-report** — second claimant is stopped; no claim is written | "You're both trying to write section 2. Stop and sort it out." |
| **ADJACENT**    | Two workers on **sibling tasks of the same objective** | **Advisory banner** — claim is written; you may proceed               | "Marcus is on section 3 next door — heads up."                 |
| **INDEPENDENT** | Workers on **unrelated objectives**                    | **Silent** — claim auto-written                                       | "Totally different work; carry on, no noise."                  |

Walking it in the scenario:

```
agent-fin (Priya's)  claims "section 2 — financials"   → INDEPENDENT at first → silent claim
agent-narr (Marcus's) claims "section 3 — narrative"   → ADJACENT to section 2 (same objective)
                                                        → banner: "agent-fin is on the adjacent
                                                          task (section 2). Proceeding advisory."
Marcus (human) also tries to claim "section 2"          → SAME as agent-fin's active claim
                                                        → HALT: "agent-fin (Priya) holds section 2.
                                                          Defer, or re-scope your work."
```

The SAME-class halt is the structural defense against the classic team failure — two people
silently editing the same thing and one of them losing their work at merge time. The claim-then-
work ordering is the discipline: **you claim before you edit, never after** — "a retroactive
claim cannot prevent the contest it documents" (`02` §3.2).

### 3.3 The honest open question: SAME = halt, or SAME = merge-surface?

For **code**, SAME-class always halts (one writer per file). For a **report section**, two people
contributing to the same section may be **desirable** — that's collaboration, not collision. The
analysis names this as a genuine product decision the platform must make **per work-item type**
(`02` §3.3 takeaway #3; `09`/`06` §6.3 echo it):

> **Recommendation.** Default **SAME → halt** for system-of-record writes and final numbers
> (where two writers genuinely collide), and default **SAME → merge-surface** for drafting prose
> (where two contributors are a feature). Make it a per-task-type setting, not a global one.
> The existing **lease-override** primitive (gated by a recorded approval) is exactly "two people
> deliberately co-work a SAME-class scope, on the record" when they want it (`02` §3.3).
>
> **Pro:** matches the work — collision where collision is real, collaboration where it isn't.
> **Con (real):** per-type tuning is **never finished** — every new work-item type needs a
> halt-vs-merge call, and a wrong call is either lost work (halt too rarely) or constant friction
> (halt too often). This is unbuilt, per-type design work (`02` §11.2), sized at **~1–2 autonomous
> cycles per work-item-type family**, not a one-shot.

### 3.4 If someone walks away mid-task — the safe reassignment ceremony

Claims are leases, so they can go stale (someone gets pulled into a meeting and abandons a task).
Reassigning an abandoned task is **not** something one manager can do silently. The platform's
reap ceremony (`02` §3.4) requires:

- proof the original worker is **genuinely idle** (their last "I'm alive" signal is older than the
  liveness window — a cryptographic predicate, not a guess), AND
- a **second distinct human** to co-authorize the reassignment.

> **Plain-language meaning.** This prevents the abuse "the manager silently reassigned your work
> and claimed you abandoned it." Reassignment is possible, but it leaves a two-person,
> tamper-evident record (`02` §3.4). It is the difference between "your work was taken" and "your
> work was reassigned, by two named people, with proof you were away."

---

## 4. The handoff — where the brief's hypothesis goes live

This is the section that puts **brief §3d in action**: the claim that agent-mediated handoff is
richer and less lossy than human-to-human handoff. The analysis is precise about where this is
true and where it isn't (`02` §10.2, `09` §3) — so this flow shows **both** the rich path and the
lossy path, side by side, and then the guardrail.

### 4.1 The LOSSY path (human → human) — what teams do today

Marcus needs the closing balances from Priya to write the section-3 narrative. The human-to-human
handoff:

```
Marcus → Priya (chat):  "hey can you send me the Q3 closing numbers when you get a sec"
Priya → Marcus (later): "here you go [pastes a few numbers]"
Marcus:                 (re-keys them into his draft, doesn't know which ledger version,
                         doesn't know if revenue is final or provisional, doesn't know
                         Priya already adjusted for the one-off in August)
```

What got lost: the **source** (which ledger, which version), the **caveats** (provisional vs
final), the **adjustments already applied**, the **reasoning**. A sentence crossed the wire; the
executable context stayed in Priya's head (`09` §3.1, the steelman). This is the disease the brief
names: communication loss is integration loss wearing a different hat.

### 4.2 The RICH path (agent → agent) — what the platform does

The same handoff, agent-mediated:

```
agent-fin finishes section 2:
  → produces a versioned Artifact (the financials) with its full provenance:
      source = ledger v3 (post-August-adjustment), revenue = FINAL, opex = FINAL,
      one-off = excluded (per Priya's L4 approval at step 6), every number traceable
      to the ledger query that produced it.
  → hands off to agent-narr by REFERENCE, not by paste:
      "section 2 artifact v4 is ready; here is the complete record."

agent-narr (Marcus's) reads the WHOLE record, not a sentence:
  → it has the numbers AND the source AND the caveats AND the adjustments AND the
    reasoning — losslessly — and drafts section 3 against the real, final, caveated data.
```

The transfer is the **whole record, not a lossy summary** (`02` §4.1, `09` §3.1). And it is
**auditable in a way human-to-human comms can never be** (`02` §10.2): the handoff is a signed
record in the coordination log — who handed what to whom, when, which artifact version. Nobody can
later "remember it differently," because two divergent records at the same point in the chain are a
**mathematical contradiction that names the liar** (`02` §2.3, the fork-detection guarantee).

> **Synthesis takeaway, in the platform's voice (`02` §2.3, §10.2).** In a human team, "who said
> what, when, and was it tampered with" is a he-said-she-said question. On the platform it is a
> **cryptographic** question. That is the concrete, defensible form of "less lossy" — not "agents
> are smarter than people," but "the handoff record is complete and cannot be falsified."

### 4.3 The honest caveat — misconstrual MOVES, it does not vanish

The platform does not claim agent handoffs are error-free. The risks analysis names the specific
new failure mode (`09` §3.1 point 4): the agent can **misread the human's intent at the
human↔agent boundary**, then propagate that misreading **with high-fidelity confidence** across
the whole network — a _confident, fast, well-recorded_ error. Human telephone-game loses
information; agent telephone-game can **amplify a wrong premise**.

```
Risk in this scenario:
  Priya says "exclude the one-off."  agent-fin interprets "one-off" as the August item only,
  but Priya also meant a smaller September item.  agent-fin propagates the SECTION-2 numbers
  to agent-narr and agent-rev with full confidence — the September one-off is silently in the
  board number, and every downstream step inherits the wrong premise, cleanly and quickly.
```

This is **why the next two sections exist.** The defense against confident-fast-wrong is not
"prevent the misread" (impossible) — it is **transparency + retrace** (M1) so a human can **see**
the premise and **fix it from the step where it entered**, and **a named human on the consequential
decision** so the wrong number cannot reach the board un-checked. The brief's hypothesis and the
brief's transparency requirement are two halves of one design: the rich channel is only safe
**because** every step is interveneable.

---

## 5. Every step is attributed, transparent, and interveneable

The brief's §3f: _every activity and output is traced and made transparent; the only thing not
transparent is how the model thinks (the black box) — but input and output are._ The platform
realizes this as the **coordination log + versioned artifacts** (`02` §2.2, §8.3; `06` §3.1).

### 5.1 What a teammate sees, live

As the agents work, the screen shows each step **as it happens and before consequential steps
execute** (brief §3e: "surfaced on screen, recorded"):

```
Q3 board report — live trace                          posture: "Ask me once"

  ✓ agent-fin   pulled ledger v3                    (Priya)    [view I/O]
  ✓ agent-fin   excluded August one-off  ⏸→approved (Priya)   [view decision]
  ✓ agent-fin   drafted section 2 → artifact v4     (Priya)    [view · retrace]
  ⟳ agent-narr  drafting section 3 from §2 v4        (Marcus)   [view · retrace]
  … agent-rev   waiting on §2 + §3                   (Priya)
```

Every line carries **who is accountable** (the named human behind the agent), **what the agent
did**, and two affordances: **view** (the actual input and output — transparent) and **retrace**
(intervene from this step). The agent's internal reasoning is the black box; its **input and
output are fully visible** (brief §3f).

### 5.2 Two-level attribution — the genuinely net-new piece

Today, an agent's work rides on its human operator's identity — agents coordinate _through_ the
human (`02` §4.4, §10.2). For the product, the analysis names the net-new work (`02` §4.4
takeaway #4, §10.3): give agents **their own enrolled identity** so an agent's autonomous output
is attributable to **the agent AND the human accountable for it** — two-level attribution.

> **In the scenario:** the section-2 draft is attributed to **agent-fin (the doer) under Priya
> (the accountable human)**. If something is wrong with section 2, the record says exactly which
> agent produced it and which human is answerable — not a vague "the system did it."
>
> **Plain-language why this matters (and the risks-analysis caution, `09` §3.1 point 2).**
> Accountability **cannot be delegated to the channel.** "The agents worked it out" is precisely
> the governance failure the platform is built to prevent. Two-level attribution keeps a **named
> person answerable** for every agent's output — the channel is rich, but the accountability is
> human. This is **net-new (~5%)** work: the agent-identity enrollment ceremony does not exist
> yet (`02` §10.3, §11.4), sized as a greenfield design (~2–3 autonomous cycles for the identity
> class + the two-level binding).

---

## 6. The intervention — Marcus retraces and fixes Priya's agent's step, under governance

This is the scenario's climax and the clearest expression of the moat conjunction: M1 (retrace),
M2 (posture-gated governance), M3 (multi-human). It walks the **confident-fast-wrong** error from
§4.3 to its fix.

### 6.1 Marcus spots the wrong premise

Marcus, drafting section 3, notices the operating margin looks too high. He uses **view** on
agent-fin's "excluded August one-off" step and sees the input/output: only the August item was
excluded; the September one-off is still in the number. The premise that entered at agent-fin's
step is wrong — and it has already propagated to his own section-3 draft and is queued for
agent-rev's assembly.

### 6.2 He retraces to the step where the premise entered

Marcus clicks **retrace** on agent-fin's exclusion step — **not** agent-rev's final number, and
**not** his own draft, but the **earliest step where the error entered** (brief §3e: "retrace any
previous step and intervene from there; downstream/cascading outputs change accordingly, but old
outputs are versioned"). He corrects the instruction: "exclude BOTH the August and September
one-offs."

```
Marcus retraces → agent-fin "exclude one-off" step
  edits the premise: "exclude August AND September one-offs"
  → the platform shows a CASCADE PREVIEW before anything re-runs:
      "This change re-runs 3 downstream steps:
         · agent-fin re-drafts section 2   (~$0.40)
         · agent-narr re-drafts section 3  (~$0.30)
         · agent-rev re-assembles          (~$0.20)
       Old versions (§2 v4, §3 v2) are preserved. Proceed?"
```

> **The cascade preview is the canary (`09` §2.3).** The risks analysis flags "cascade cost
> explosion" — a change near the root legitimately invalidates everything downstream. If a
> non-coder can't see a comprehensible "this re-runs N steps and costs ~$X" preview before
> committing, they won't trust the feature. The preview shown above is therefore a **hard
> acceptance gate**, not a nice-to-have (`09` §2.4). **Old outputs are versioned** (§2 v4, §3 v2
> are kept) — the brief's requirement (§3e), realized as the artifact-version chain (`02` §8.3).

### 6.3 The governance gate fires — and a NAMED HUMAN is on the consequential decision

Here is where M2 and the guardrail meet. Marcus's retrace changes a **board number** — a
consequential step. Under the **"Ask me once"** posture Priya set, and under the platform's
accountability default, a consequential change to a system-of-record number cannot land on
**only** Marcus's say-so when **Priya is the accountable human for that task**:

```
⏸ CONSEQUENTIAL DECISION — board number changing

   Marcus is retracing agent-fin's step (accountable: Priya).
   This changes the Q3 operating margin the board will see.

   → Recorded as a Decision (named human required):
       requested_by: Marcus    accountable: Priya
   → Priya is asked to confirm:  "Marcus found the September one-off was
      still in the margin. Approve the correction + re-run? (yes/no)"
```

Priya approves. The correction cascades, the new versions are produced, the old ones are kept, and
the **Decision is signed and logged** — requested by Marcus, approved by Priya, both named.

> **This is the honest position from the risks analysis (`09` §3.4, §4.5), shown in action.** The
> rich agent channel does **not** dissolve accountability into "the agents worked it out." Every
> **consequential decision keeps a named human on it** (`09` §3.4 commitment 2). The platform can
> always answer "who chose this, and when" — which is the accountability anchor enterprise legal
> will demand (`09` §4.5). It is not a vendor disclaimer; it is a **named, time-stamped,
> attributable** human authorization (`09` §4.5 recommended mitigation).
>
> **Pro:** the wrong board number cannot reach the board un-checked — a second named human caught
> it, and the accountable human signed the fix.
> **Con (real, `09` §4.2/§4.3):** gating consequential writes is exactly the **HITL-bottleneck**
> risk — gate too much and the "agents do your work end-to-end" value erodes into "except every
> number needs approval." Calibrating **which** changes are consequential is an ongoing,
> never-finished tuning problem, and every mis-calibration is either a hole (gated too little) or a
> UX death (gated too much). The platform's containment answer is **least-privilege + posture per
> objective** (`09` §4.3), so the gate fires on the genuinely consequential class, not on every
> keystroke — but getting that line right is real, continuing work.

### 6.4 Why the four-eyes structure can't be faked

The "second named human" check is structural, not a courtesy. Approvals require a **distinct
person**, verified cryptographically — a single human with two keys cannot self-approve, because
the gate tests the **person**, not the key (`02` §4.1, §9.1, the 4-eyes-on-`person_id` matrix).
In the scenario, Marcus and Priya are genuinely two people; if Marcus tried to approve his own
consequential change using a second identity, the gate would refuse it.

> **The "less lossy" guarantee, restated for governance.** In a human team, "did two people
> really sign off?" is a trust question. On the platform it is a cryptographic one — the gate
> **names** any attempt to fake a second approver (`02` §9.1).

---

## 7. The coordination log — why the whole thing is auditable

Everything above — every claim, every handoff, every step, every decision, every posture choice —
is recorded in **one append-only, signed, tamper-evident event stream**: the coordination log
(`02` §2.1, §2.2). The analysis is explicit: **this log IS the brief's "every working step is
traced and transparent" requirement** (`02` §2.2; `06` §3.1), realized as a single rendezvous
primitive every participant reads and writes through.

### 7.1 What the audit trail of the Q3 report looks like

```
Q3 board report — coordination log (excerpt, signed records)

  claim     agent-fin   "section 2"                    Priya
  claim     agent-narr  "section 3"  (ADJACENT banner)  Marcus
  decision  exclude August one-off   approved           Priya
  artifact  section 2 v4                                 agent-fin / Priya
  handoff   §2 v4 → agent-narr                           agent-fin → agent-narr
  retrace   agent-fin "exclude one-off" step             Marcus
  decision  add September one-off  requested→approved     Marcus → Priya   ← 2 named humans
  artifact  section 2 v5  (parent: v4)                    agent-fin / Priya
  artifact  section 3 v3  (parent: v2)                    agent-narr / Marcus
  artifact  final report v1                               agent-rev / Priya
```

Anyone with access can answer, months later, **without a meeting**: Who produced the board
margin? (agent-fin, under Priya.) Who caught the error? (Marcus.) Who approved the fix? (Priya,
named, time-stamped.) What did the number look like before? (§2 v4, preserved.) Was anything
tampered with? (No — the chain verifies, or it names whoever broke it; `02` §2.3 fork detection.)

### 7.2 The properties that make it trustworthy (plain language)

The log's correctness guarantees (`02` §2.3, the fold rules) translate to:

- **Nothing un-signed is visible.** A forged or hand-written record is invisible to everyone — it
  doesn't fold into shared state (`02` §2.3 rule 1).
- **No silent re-writing of history.** Two contradictory records at the same point in someone's
  chain are a contradiction that **names the liar** (`02` §2.3 rule 3). This is the structural
  form of "less lossy than human memory."
- **Nobody can mutate someone else's record.** You can only append to your own chain; touching
  another person's work requires the co-signed ceremony from §3.4 (`02` §2.3 rule 4).

> **Why this is a real network effect, not just retention (`06` §6, §7).** A workspace that holds
> the whole team's signed activity is **more valuable to join than an empty one** — the team-gravity
> loop (`06` §6.2). COLLABORATION is one of only two genuine multi-party network effects the
> analysis identifies (`06` §1, §7), because value rises as more **participants** join a shared
> workspace, not just as one person does more. The other is the cross-org artifact exchange (M4),
> which sits above this and ignites later (`06` §8).

---

## 8. The guardrail in full — ambiguity-preservation and the off-the-record mode

The risks analysis is emphatic (`09` §3): the brief's hypothesis is a **research BET**, not a
settled USP, and building M3 on the verbatim claim ("agents communicate better than you do") is an
internal inconsistency a sharp buyer will find (`09` §3.4). So the platform ships **the narrowed
position** — disrupt the handoff, not the relationship — with ambiguity-preservation as a
**first-class, day-one feature** (`09` §3.4 recommended mitigation).

### 8.1 The informal mode — deliberately ungoverned, by design

Not everything a team says should become a recorded objective. "Let's see how Q3 goes" is
**deliberately** unspecified — it preserves optionality, enables negotiation, allows face-saving,
and lets people defer commitment (`09` §3.1 point 3). Forcing it into a complete, recorded,
auto-acted-upon objective would:

- create a **discoverable record where deniability was the point** — a legal-discovery and privacy
  hazard (`09` §3.1 point 3), and
- strip out the **relationship bandwidth** that the "inefficient" hallway conversation actually
  carries — the human's non-measurable contribution (`09` §3.1 point 1, the CARE Mirror Thesis).

So the platform ships an explicit **"informal / not-an-objective" mode**: talk that is **not**
auto-structured, **not** recorded as a decision, and **not** auto-acted-upon (`09` §3.4).

```
In the Q3 workspace:

  [ Objective mode ]   — structured, recorded, agent-actionable, fully traced
  [ Informal mode  ]   — NOT structured, NOT a decision, NOT acted on; for "let's
                         see how Q3 goes" talk that should stay vague + off-record
```

Marcus and Priya can think out loud — "do we even want to flag the September item to the board, or
soften it?" — in informal mode, and **nothing acts on it** until one of them deliberately turns a
conclusion into an objective. The deliberation stays human; only the **commitment** becomes
governed work.

> **The honest cost of this feature (`09` §3.4 cons, stated not glossed).** The informal mode
> **complicates the otherwise-clean "everything is traced" story** — it is a second comms path
> that is **deliberately ungoverned**, and an ungoverned path is a place the security risks
> (prompt injection, blast radius — `09` §4) can hide. The platform's discipline: informal mode is
> for **talk, never for action** — it cannot touch a system of record, cannot send anything
> external, cannot move work. The moment a human promotes informal talk into an objective, the
> full governance + trace + posture machinery re-engages. The ungoverned path is bounded to
> deliberation, by construction.

### 8.2 How the platform validates the bet cheaply (instead of assuming it)

The analysis recommends instrumenting the hypothesis rather than asserting it (`09` §3.4). In this
flow, the data falls out of the audit trail the platform already keeps:

- **Do teammates route real handoffs through the agent channel** (the rich path) — or do they
  bypass it and keep using chat/email (the lossy path)? If they bypass it for real coordination,
  the hypothesis is failing in practice regardless of any benchmark (`09` §3.3 leading indicator).
- **Do round-trips drop?** Fewer "I thought you were doing that" failures, less re-keying, fewer
  "which version?" questions — the steelman's specific claims (`09` §3.1, `02` §4.1) — measured
  directly from the coordination log.
- **Do users ask for an informal / off-the-record mode?** That request **is** the signal that the
  ambiguity-preservation need is real and currently unmet (`09` §3.3 second indicator) — which is
  exactly why the platform ships it from day one.

> **The platform's honest marketing line (`09` §3.4 implications).** "We make your team's handoffs
> lossless and auditable, and we keep your ability to be informal and off-the-record." **Never**
> "agents communicate better than you do." The narrowed claim is **more** defensible, not less,
> because it aligns with the governance philosophy the whole ecosystem rests on (`09` §3.4 pros).

---

## 9. What's reused vs net-new (so the build is sized honestly)

Per the analysis's 80/15/5 read (`02` §10.3), this entire flow runs mostly on substrate that
**already exists and runs today** (`06` §6.3: "~80% built").

**Reused directly (~80%) — the substrate exists and runs:**

- the signed, append-only, hash-chained coordination log + fold rules + fork detection
  (`02` §10.3) — `~/repos/loom/.claude/`
- claims / claim-classes (SAME/ADJACENT/INDEPENDENT) + the reap ceremony (`02` §3) — loom
- identity triple + roster + the deterministic onboarding read-path (`02` §4, §6.1) — loom
- the L1–L5 posture ladder + the four-eyes gate matrix (`02` §8, §9.1) — pact
  (`~/repos/terrene/contrib/pact`) + eatp (`~/repos/loom/kailash-py`, skill 26) + aegis
  (`~/repos/dev/aegis`)
- the work-item ontology (Objective → Request → WorkSession → Artifact → Decision) — pact (`02` §1.2)
- versioned artifacts (the "old outputs preserved" chain) — pact + loom anchors (`02` §8.3)

**Adaptation (~15%) — re-target existing primitives (`02` §10.3):**

- generalize the claimable unit from **file path** to **Request** (a field swap, `02` §1.1)
- re-target the adjacency relation from the **file tree** to the **work-item DAG** (`02` §3.3)
- generalize the single-writer lease to a generic "deliverable-under-authorship" lease (`02` §5.2)

**Net-new (~5%) — genuinely new (`02` §10.3, `06` §6.3):**

- the **agent identity class** with two-level attribution (agent + accountable human) — §5.2 above
- **direct agent→log writes** (agents append claim/decision/handoff records as themselves) — §4.2
- the **non-developer UI** surfacing the log/posture/claims/trace as a screen (today: CLI + JSONL)
- the **informal / ambiguity-preservation mode** (§8) — the guardrail the risks analysis requires

> **Effort framing (autonomous cycles, not human-days).** The reused substrate is configuration +
> re-targeting work, parallelizable across the claim-engine, the work-item model, and the posture
> layer (independent surfaces). The agent-identity class + two-level attribution is the largest
> net-new piece (greenfield, ~2–3 cycles at the first-session factor). The non-developer UI and the
> informal mode are the two surfaces that most need usability evidence, so they should ship in a
> **deliberately reduced first form** and grow on evidence — the same discipline the analysis
> applies to M1 (`09` §2.4).

---

## 10. Open questions this flow surfaces (flagged, not hidden)

Honest gaps the analysis names and this flow depends on (`02` §11, `06` §6.3):

1. **Scale.** The substrate is designed for "~12 operators against one repo" (`02` §11.1). A
   product workspace may have **hundreds of agents + humans**. Does the coordination log survive
   10K+ participants / 1M+ records? **Open** — compaction exists but its scaling to product
   cardinality is unproven (`02` §11.1).
2. **SAME = halt vs merge, per work-item type.** Decided per-type (§3.3); unbuilt and never
   one-shot (`02` §11.2).
3. **Advisory vs enforced claims for autonomous agents.** loom claims are **advisory** (a human can
   ignore the banner). For an agent running on "Go ahead" (engine-internal: L5), advisory may be
   insufficient — the agent must **honor** the
   claim structurally. Are claims enforced (block) or advisory (banner) when the claimant is a
   fully-autonomous agent? **Open** (`02` §11.3).
4. **Agent attribution without a human in the loop.** For a fully-autonomous agent (on "Go
   ahead"), the accountable-
   human binding must be established **at delegation time**, not at action time — and that
   enrollment ceremony doesn't exist yet (`02` §11.4).
5. **The hypothesis itself.** Whether agent-mediated handoffs measurably beat human handoffs in
   real team use is the central BET (`09` §3, `06` §6.3). This flow is built to **validate it
   cheaply** (§8.2), not to assume it — and to remain a viable team product even if the bold
   version of the hypothesis is culturally rejected, because the **substrate survives as
   coordination plumbing** regardless (`09` §3.3).

---

## 11. One-paragraph summary (the thesis of this flow)

Two humans and several agents work one objective on a single shared substrate: work is **claimed**
with advisory leases whose **SAME/ADJACENT/INDEPENDENT** classes convert silent collisions into
loud, pre-edit halts; **handoffs** between humans and agents and between agents carry the **whole
record** — source, caveats, reasoning, version — losslessly and auditably (the brief's §3d
hypothesis **in action**, but narrowed to the handoff layer the evidence supports); **every step is
attributed** to a doer-agent under a named accountable human, transparent (input/output visible,
only the model's reasoning is a black box) and **interveneable**; a teammate can **retrace** another's
agent's step to the point a wrong premise entered, see a **cascade cost-preview**, and trigger a
re-run that preserves old versions — and because the change is consequential, a **named human signs
the decision** (the guardrail the risks analysis insists on); and the whole thing is recorded in one
**signed, tamper-evident coordination log** that makes "who did what, when, and was it altered" a
cryptographic question instead of a he-said-she-said one — while a deliberately-ungoverned
**informal mode** preserves the human's right to be vague, off-the-record, and uncommitted, because
that ambiguity is a feature, not a defect.
