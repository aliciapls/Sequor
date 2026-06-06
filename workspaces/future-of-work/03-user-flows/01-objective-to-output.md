# User Flow 01 — Objective → Traced Output: the core non-coder flow

> **What this is.** A step-by-step walk of the platform's signature flow, told from the
> point of view of a **non-coder** — someone who has never written a line of code and never
> will. They state what they want in plain words; the agent does the work across systems
> that used to be separate; every move is shown on screen and recorded; the finished work
> arrives with a full, inspectable history of how it was made.
>
> **The example is the brief's own.** A user asks for a "3Q financial report." The brief
> (`briefs/01-vision.md` §3e) uses exactly this case to describe the platform: the user
> states intent → the agent decides to spin up 3 agents → that decision is surfaced on
> screen and recorded → the user has chosen a **posture** (how much rein the agent gets)
> beforehand → execution proceeds → every step is traced → the user can rewind any step and
> the consequences recompute while old versions survive. This document makes that walk
> concrete: what the user **sees**, what the agent **does**, where the **governance gates**
> fire, and what the **disposition** is at each step — for all three postures.
>
> **Audience & style.** Written for a founder deciding whether this flow is legible enough
> for a non-coder to live in daily. Plain language throughout; every technical term is
> translated on first use (per `.claude/rules/communication.md`). The flow is told as a
> screen narration, not an API trace — because the screen is what the user has to be able to
> act on.
>
> **Grounding.** Every load-bearing claim resolves to one of: the brief
> (`briefs/01-vision.md` §3e–3f), the transparency/intervention architecture
> (`01-analysis/07-transparency-intervention-architecture.md`), the trust-posture plan
> (`02-plans/04-trust-posture-permissions-plan.md`), or the CLI-harness research
> (`01-analysis/01-research/05-cli-harness-universal-interface.md`). Genuine uncertainty is
> flagged, not smoothed over (per `.claude/rules/spec-accuracy.md` — this is a user-flow
> narration of _target-state_ behaviour, and the open design risks are called out in §8).

---

## 0. The flow in one paragraph

The user types or says what they want, in their own words, on whatever surface they already
live in (chat, email, a web panel). Before anything runs, the agent shows its **plan** — "to
do this I'll spin up 3 helpers, one to pull the ledger, one to pull the sales records, one to
write it up; estimated cost about $X" — as a card on screen. The user has already picked, for
this one task, how much freedom the agent has: **Go ahead** (the agent runs and the user just
watches), **Ask me once** (the agent runs after a single approval of the plan), or **Step
through with me** (the agent pauses for the user's approval at every consequential step). The
agent then works **across systems that used to be separate** — the accounting system, the
sales system, the spreadsheets — by talking to each through a connector, so the user never
opens any of them. Every input, every decision, every system it touched, every result, and
the final report are recorded on a timeline. The report arrives with a "show your work"
button: the user can open any step, see exactly what it used and produced, and — if something
is wrong — rewind to that step, change it, and let only the affected parts recompute, while
the original survives as a saved version. The single thing never shown is the model's private
"thinking"; everything that goes _into_ and _comes out of_ it is shown
(`briefs/01-vision.md` §3f; `07-…architecture.md` §2.2).

---

## 1. The paradigm shift this flow embodies — why it matters before the walk

Today, producing a 3Q financial report means a human being the **integration layer**: open
the accounting system (ERP) and export the general ledger; open the sales system (CRM) and
export the bookings; open Excel to reconcile them; open Word to write the narrative; chase
three colleagues for missing numbers; copy-paste between five tools, each with its own login,
its own layout, its own quirks (`briefs/01-vision.md` §1; `05-cli-harness…` §0, §2). The
person is the glue.

This flow inverts that. The user states the **objective**; the **agent becomes the
integration layer**, reaching every system through connectors; the human's job shrinks to two
things they are actually good at — **saying what they want** and **governing how it's done**
(`05-cli-harness…` §7 item 1; strategic spine: "from N siloed vertical systems, human =
integration layer → ONE agnostic interface, agent = integration layer, human states intent +
governs"). The plumbing that makes this possible — the connector standard (MCP), the
parallel-helper mechanism (subagents), and the always-on recording — already exists in the
agent harness; it has simply been configured for coders, and this flow re-points it at
ordinary knowledge work (`05-cli-harness…` §1, §2, §6.1).

**Why the recording is not optional decoration.** Code work has a free, instant truth-check:
the compiler and the test suite tell you immediately if you got it wrong. Most office work
has no compiler — there is no instant machine that says "this report is wrong"
(`05-cli-harness…` §2, §6.2). The transparency-and-intervention surface in this flow **is the
substitute for the missing compiler**: it is what lets a non-expert catch and correct a wrong
turn, because they can _see_ what the agent did. That is why the whole product is built around
it, and why this flow is the product's spine, not a feature.

---

## 2. The cast of on-screen objects (so the walk reads cleanly)

The user only ever interacts with a small, plain vocabulary of on-screen things. Each maps to
a real recorded object underneath (`07-…architecture.md` §2.1, §3.1), but the user never sees
the underlying names.

| What the user sees on screen       | Plain meaning                                                                    | Underlying record (user never sees this)                                         |
| ---------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **"What do you want done?"** box   | Where they state the objective                                                   | the objective record                                                             |
| **The plan card**                  | "Here's what I'm about to do: 3 helpers, est. $X" — shown _before_ anything runs | a `plan_proposed` decision (`04-trust-posture…` §4.2)                            |
| **The three posture buttons**      | _Go ahead_ / _Ask me once_ / _Step through with me_ — picked beforehand          | the canonical 5-rung trust posture, mapped 3→1 (`04-trust-posture…` §1.2)        |
| **The live timeline**              | A scrolling list of "what's happening now," each row a step                      | the provenance ledger's steps, streamed live (`07-…architecture.md` §2.1, §3.3)  |
| **An approval card**               | "This step would do X / spend $Y — Approve / Edit / Reject"                      | a held decision awaiting a human (`04-trust-posture…` §4.1, §4.3)                |
| **The budget bar**                 | "You've used $X of your $Y limit for this task"                                  | the per-objective budget tracker, alerts at 80/95/100% (`04-trust-posture…` §5)  |
| **"Show your work" on any output** | Opens the step's inputs, what it touched, what it made                           | the step's recorded input/tool-call/output envelope (`07-…architecture.md` §2.1) |
| **"Rewind to here"**               | Go back to a past step and change it                                             | an intervention; spawns a new version + recompute (`07-…architecture.md` §5.1)   |
| **Version chips (v1, v2…)**        | Old results saved; you can compare and revert                                    | the immutable version chain (`07-…architecture.md` §3.1, §5.2)                   |

A note on surface (per Decision B, capability-first, surface deferred): the walk below shows
a **web panel** because it is the clearest way to narrate "the user sees X." The same flow
works chat-first or email-first — the comms wedge is email/WhatsApp-first today
(`05-cli-harness…` §3.1). The _objects_ are the contract; the _surface_ is pluggable.

---

## 3. The canonical walk — "Ask me once" (the recommended default-feel posture)

This is the brief's own worked example (`briefs/01-vision.md` §3e): the user picks **"Ask me
once"** beforehand, so they get exactly **one** approval gate — at the plan, before any work
runs — and then the agent proceeds on its own, with the user watching the live timeline.

> **Why "Ask me once" leads the walk.** It is the posture that best shows the platform's whole
> shape in one pass: a plan surfaced and approved _beforehand_, then autonomous execution the
> user merely observes, then full traceability and the ability to rewind after the fact. It is
> also the posture the brief's example implicitly uses ("agent asks for one permission before
> executing" — `briefs/01-vision.md` §3e). The L4 and L3 variants in §4–§5 then show how the
> gates shift.

### Step 1 — The user states the objective

**What the user sees.** A single box: _"What do you want done?"_ They type:

> _"I want the 3Q financial report."_

That's it. No tool to open, no template to fill, no menu of report types. They say it the way
they'd say it to a colleague.

**What the agent does.** It reads the intent, recognises this is a multi-part task, and forms
a plan — but **does not run anything yet**. Forming-the-plan-before-acting is the load-bearing
move (`04-trust-posture…` §4; `07-…architecture.md` §4.1).

**Governance gate.** None yet — stating intent is free. The posture the user picked
(_Ask me once_) is already in force and recorded as the setting this whole task runs under
(`04-trust-posture…` §7.1).

**Disposition.** Proceed to plan surfacing.

---

### Step 2 — The agent surfaces its PLAN on screen, before running

**What the user sees.** A **plan card** appears:

```
Here's my plan for "3Q financial report":

  Helper 1 — Revenue
     → pull the general ledger from the accounting system for Q3
  Helper 2 — Bookings
     → pull signed deals from the sales system for Q3
  Helper 3 — Narrative
     → write the management summary from Helpers 1 & 2

  These 3 helpers run at the same time.
  Estimated cost: about $4.   Estimated time: ~2 minutes.

  [ Approve ]   [ Edit the plan ]   [ Reject ]
```

This is the exact moment the brief describes: _"agent decides to spin up 3 agents → these
decisions are surfaced on screen, recorded"_ (`briefs/01-vision.md` §3e). The plan is a
**first-class, inspectable object** — not buried in a log, not implied, but shown as a card
the user can read and act on (`07-…architecture.md` §2.1 row "Agent decisions, plans, and
fan-outs"; §4.1).

**What the agent does.** It captures the plan as an approvable object and **blocks** —
nothing executes until the user responds, because the posture is _Ask me once_
(`04-trust-posture…` §4.1: the held-decision mechanism creates an approval record and returns
"not yet" until a human approves).

**Governance gate — THE one gate for this posture.** _Ask me once_ = exactly one structural
checkpoint, at the plan→execute boundary (`04-trust-posture…` §1.2, §2). The user reviews:
3 helpers, ~$4, ~2 min. They click **Approve**.

> What "Edit the plan" would do: the user could, e.g., add "and email it to the board" or
> "only Q3, not year-to-date" — the plan card is editable before commit. What "Reject" would
> do: nothing runs; the agent asks what to change.

**Disposition.** Approved → execution begins. The approval is recorded: _who_ approved,
_when_, against _which plan version_ (`04-trust-posture…` §4.1; `07-…architecture.md` §3.4
invariant 6).

---

### Step 3 — Execution across formerly-siloed systems, traced live

**What the user sees.** The **live timeline** starts scrolling. Plain rows, in real time:

```
● Helper 1 (Revenue)  — connecting to the accounting system…
● Helper 2 (Bookings) — connecting to the sales system…
● Helper 3 (Narrative)— waiting for Helpers 1 & 2
  ─────────────────────────────────────────────
● Helper 1 — read Q3 general ledger (1,204 entries)          ✓
● Helper 2 — read 87 signed deals for Q3                     ✓
● Helper 1 — converted EUR/GBP deals at quarter-avg rate     ✓
● Helper 3 — drafting the management summary…
  Budget: ▓▓▓░░░░░░░  $1.80 of $4.00
```

The user is **watching work happen across three different systems at once** — the accounting
system, the sales system — without opening any of them. The agent is the integration layer
(`05-cli-harness…` §2; strategic spine). The budget bar ticks up live (`04-trust-posture…`
§5).

**What the agent does.** Each helper runs as a chain of steps. For **every** step it records,
and streams to the screen (`07-…architecture.md` §2.1, §3.3):

- **the inputs** it consumed (which ledger, which date range),
- **the tool calls** — the actual actions in the world: "query the ledger for Q3 revenue,"
  "fetch signed deals" — reached through a **connector** to each business system
  (`05-cli-harness…` §1.4, §3.4: the same connector standard that wires a coding agent to
  `git` wires this agent to the ERP/CRM),
- **the tool results** — the rows that came back (the ground truth the agent then reasons
  over),
- **the output** it produced — each gets a content fingerprint and is saved as **version 1**.

Crucially, the **reasoning lives in the model, and the tools are dumb data endpoints** — the
connector just fetches/returns rows, it does not decide anything (`05-cli-harness…` §5.2;
`.claude/rules/agent-reasoning.md`). That is _why_ the trace is meaningful: everything except
the model's private thinking is on the timeline (`05-cli-harness…` §5.2; `briefs…` §3f).

**Governance gate.** None blocking — under _Ask me once_, once the plan is approved the agent
auto-approves each step **inside the agreed scope and budget** (`04-trust-posture…` §1.2:
DELEGATING = auto-approve inside scope). If a step tried to go _outside_ scope (e.g. spend
past the $4 cap, or touch a data type the envelope forbids), it would flip to a hold and an
approval card would appear — but in the happy path here, it doesn't.

**Disposition.** All three helpers complete; outputs saved as v1.

---

### Step 4 — The final output is assembled and delivered with its provenance

**What the user sees.** The report appears, with a quiet but load-bearing affordance:

```
✓ 3Q Financial Report — ready                         [ Open ]  [ Show your work ]

   Revenue:   $12.4M   (Helper 1)
   Bookings:  $14.1M   (Helper 2)
   Summary:   "Q3 revenue grew 8% QoQ, driven by…"   (Helper 3)

   Made from: 1,204 ledger entries + 87 deals.  Cost: $3.60.  Took 1m52s.
```

The **"Show your work"** button is the brief's transparency promise made tangible
(`briefs…` §3f). Click it, and the timeline expands so the user can open **any** step and see
exactly what went in and what came out — the revenue number traces back to the precise ledger
rows; the summary traces back to the two sub-outputs it was written from
(`07-…architecture.md` §2.1, §5.4 step 3).

**What the agent does.** It assembles the three sub-outputs into the final report (itself a
versioned output) and presents it alongside its provenance — the recorded origin and history
of every piece (`07-…architecture.md` §3, §5.4 step 4).

**Governance gate.** None — delivery of an in-scope result under an approved plan is the
expected terminal state.

**Disposition.** **Delivered, with provenance.** The user has a report they can trust _because
they can inspect how it was made_ — not because they were told to trust it. This is the
honesty boundary the architecture insists on: the platform delivers **traceability** (you
_can_ see and check), not **accountability** (it cannot force you to have understood)
(`07-…architecture.md` §2.3; `04-trust-posture…` §7.4).

---

### Step 5 — The user spots a problem and REWINDS (intervene-from-any-step)

This is the part no competitor has put in front of a non-coder (`07-…architecture.md` §1).

**What the user sees.** Reading the revenue section, the user realises the agent used the
wrong exchange-rate assumption for the EUR/GBP deals (it used quarter-average; the user's
finance team uses quarter-end). They click **"Show your work"** on the revenue number, find
the step labelled _"converted EUR/GBP deals at quarter-avg rate,"_ and click **"Rewind to
here."**

```
Rewind to:  Helper 1 — "converted EUR/GBP deals at quarter-avg rate"

  This step used:   the FX assumption = "quarter-average"
  Change it to:     [ quarter-end ▼ ]

  When I redo this, do you want me to:
    ( ) Re-figure this step with your change   (fresh result)
    ( ) Keep this step's recorded result, just flow the change downstream

  [ Apply change ]      [ Cancel ]
```

**What the agent does.** Changing the input creates a **new version of that step** — the
original step and its result are **untouched** (immutability: "old outputs are versioned" —
`briefs…` §3e; `07-…architecture.md` §5.1 steps 1–2, §3.4 invariant 1). The agent then walks
everything downstream of that step and re-runs **only the parts that actually depend on the
change** (`07-…architecture.md` §5.1 steps 3–4).

**Governance gate — the rewind itself is governed and recorded.** Two things fire:

1. The **per-step choice** above (re-figure vs keep-recorded) is surfaced explicitly, because
   model steps don't always produce the same answer twice and guessing silently is the worst
   outcome (`07-…architecture.md` §5.3). The user picks _"Re-figure this step with your
   change."_
2. The intervention is **audited** — _this user changed the FX assumption at this step at this
   time_ becomes a permanent record (`07-…architecture.md` §3.4 invariant 6, §5.4 step 8).

**Disposition.** The recompute runs. On the live timeline the user watches:

```
● Helper 1 — re-figured FX at quarter-end rate            ✓  (v2)
● Helper 1 — recomputed Q3 revenue: $12.1M (was $12.4M)   ✓  (v2)
● Helper 3 — rewrote the revenue paragraph                ✓  (v2)
○ Helper 2 (Bookings)   — unchanged, skipped ✓
○ Costs / cash-flow     — unchanged, skipped ✓
```

Only the revenue chain and the final summary recomputed; **bookings was left completely
alone** because its inputs never changed — its fingerprint still matched, so the system skipped
it (`07-…architecture.md` §5.4 step 6, §3.2 "only recompute what changed"). The user now has
**v2** of the report, can **compare v1 vs v2 side by side**, and can **revert to v1** if they
prefer it (`07-…architecture.md` §5.4 step 7). Nothing was lost.

**This is the whole product in one gesture:** a non-coder caught a domain mistake the agent
made, fixed it by changing one plain-language assumption, and the consequences recomputed
correctly — without redoing the work, and without destroying the original.

---

## 4. Variant — same objective under "Go ahead" (engine-internal: L5 `AUTONOMOUS`)

Same request — _"I want the 3Q financial report"_ — but the user picked **"Go ahead"**
beforehand. Plain meaning: _run it on your own; I'm watching and I can stop you, but don't
ask me to approve each step_ (`04-trust-posture…` §1.2: AUTONOMOUS; the human is **on** the
loop, not **in** it — `04-trust-posture…` §2).

**Where the gates differ (this is the only difference that matters to the user):**

| Step                              | "Ask me once" (§3)                            | **"Go ahead" (this variant)**                                                                                                                                                                                                         |
| --------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Plan surfacing (Step 2)**       | Plan card **blocks**; user must Approve       | Plan card is **shown and recorded**, then **auto-approves** — the agent doesn't wait. The user sees "Plan: 3 helpers, ~$4 — running" and execution starts immediately (`04-trust-posture…` §4.2: posture decides auto/once/each-step) |
| **Execution (Step 3)**            | Auto-runs inside scope after the one approval | Auto-runs inside scope from the start; identical live timeline + budget bar                                                                                                                                                           |
| **Anything outside scope**        | Would flip to a hold                          | **Blocked outright** (not held-for-approval): AUTONOMOUS auto-approves _inside_ the envelope and **blocks** anything outside it (`04-trust-posture…` §2, line "AUTONOMOUS … outside scope → BLOCK")                                   |
| **Delivery + rewind (Steps 4–5)** | Identical                                     | Identical — transparency and rewind are **independent of posture**                                                                                                                                                                    |

**What the user sees that's distinctive.** The plan card flashes up with a brief, visible
"running…" — the decision is still **surfaced and recorded** (the brief requires this
regardless of posture — `briefs…` §3e: "surfaced on screen, recorded"), it just doesn't pause.
A small **"Pause"** / **"Stop"** control is always present, because _Go ahead_ still puts the
human on the loop — they can abort mid-flight (`04-trust-posture…` §4.2 item 2, the `USER`
pause trigger).

**Why "Go ahead" is safe to offer (the non-obvious part).** It is **not** a blank cheque. The
operative posture is always `min(what the user chose, the system's safety floor)`, and the
floor **auto-downgrades the instant something looks wrong** — a repeated problem drops the
agent straight to the most restrictive mode (`04-trust-posture…` §7.1, §9; principle: upgrades
are human-gated, downgrades fire automatically). So "Go ahead" means "run freely _within the
fence I set_, and the system slams the fence tighter the moment you misbehave."

**Disposition.** Same as §3 — **delivered with provenance**, rewindable — but reached with
**zero** approval interruptions. This is the posture for routine, well-bounded, low-stakes
work the user has done many times and trusts the agent to handle.

**Honest trade-off (symmetric, per `.claude/rules/recommendation-quality.md`).** _Go ahead_
buys speed and zero interruption; it costs the user the chance to catch a wrong plan _before_
it spends money and time. The mitigations are real (scope cap, budget cap, auto-downgrade,
full rewind-after-the-fact) but they are _recovery_, not _prevention_ — the user finds the
mistake after the spend, not before. The recommendation is therefore to default new users to
_Ask me once_ and let them opt up to _Go ahead_ per-task once they trust a given workflow
(`04-trust-posture…` §9: default to supervised, user opts up).

---

## 5. Variant — same objective under "Step through with me" (engine-internal: L3 `SUPERVISED`)

Same request, but the user picked **"Step through with me."** Plain meaning: _pause and let me
approve every consequential thing you're about to do_ (`04-trust-posture…` §1.2: SUPERVISED;
the human is **in** the loop — a blocking node inside the work path — `04-trust-posture…` §2).
This is the posture for high-stakes, unfamiliar, or sensitive work where the user wants their
hands on every lever.

**Where the gates differ:** now **multiple** approval cards fire, one per consequential step,
not just one at the plan.

**The walk under L3:**

### Step 1 — State intent. Same as §3 Step 1.

### Step 2 — Plan surfaced; user approves the plan (gate 1 of several).

```
Plan: 3 helpers (Revenue / Bookings / Narrative), ~$4.   [ Approve ]  [ Edit ]  [ Reject ]
```

Same plan card. User approves. But under _Step through_, this is the **first** of several
gates, not the only one.

### Step 3 — Each consequential action pauses for approval.

Now the timeline runs **one step at a time**, each pausing on an approval card:

```
Helper 1 wants to:  READ the Q3 general ledger from the accounting system
   (1,204 entries · read-only · no spend)
   [ Approve ]   [ Edit ]   [ Reject ]
```

The user approves. Next:

```
Helper 1 wants to:  CONVERT EUR/GBP deals using "quarter-average" FX rate
   [ Approve ]   [ Edit ]   [ Reject ]
```

**Here the user catches the FX mistake _before_ it happens** — they click **Edit**, change
the rate to quarter-end, and approve. Under L3, the wrong assumption never even runs; the
user fixed it at the gate, not by rewinding afterward.

And so on, one consequential action at a time, until the report is assembled.

**What "consequential" means, and the one design subtlety.** Not _every_ tiny step pauses —
only **consequential** ones (a real read of a system of record, a spend, an external send).
Deciding what counts as consequential is done by the **model judging it**, not by matching
keywords — Sequor's own rules forbid keyword routing in agent decisions
(`04-trust-posture…` §9.1 item 1; `05-cli-harness…` §5.2). This is a deliberate, principled
choice that carries a real cost: an extra model judgement on each action is slower and costlier
than an instant keyword check, and the mitigation (judge once per step-type, reuse the verdict)
is **unproven at scale** — flagged honestly in §8 (`04-trust-posture…` §10 #2).

**Governance gates.** Several — one per consequential action. The human is structurally **in**
the loop: the agent literally cannot proceed past each gate without them
(`04-trust-posture…` §2: SUPERVISED = every consequential action → HOLD → HITL).

**Disposition.** **Delivered with provenance** — same final artifact, same rewindability — but
reached with the user approving (and sometimes editing) each consequential move along the way.
Most errors are caught _before_ they execute, rather than rewound after.

**Honest trade-off (symmetric).** _Step through_ maximises control and prevents mistakes at the
source; it costs the user time and attention — a many-step objective means many approval cards,
which can feel like death by a thousand clicks for routine work. The recommendation: use _Step
through_ for the first run of a new or sensitive workflow, then drop to _Ask me once_ or _Go
ahead_ once the user has seen it behave correctly a few times.

---

## 6. The three postures side by side (the user's actual mental model)

This is the one table a user needs to internalise. Everything else is detail.

|                               | **Go ahead**                                 | **Ask me once**                  | **Step through with me**                |
| ----------------------------- | -------------------------------------------- | -------------------------------- | --------------------------------------- |
| **In plain words**            | "Run it; I'm watching"                       | "Show me the plan, then run it"  | "Ask me before each real action"        |
| **Approval gates**            | Zero (plan shown, auto-approves)             | **One** (at the plan)            | **Many** (one per consequential action) |
| **Human is…**                 | **on** the loop (monitor, can abort)         | **on** the loop + one checkpoint | **in** the loop (blocks each step)      |
| **Catches mistakes…**         | after the fact, by rewinding                 | mostly after, some at the plan   | **before** they execute, at each gate   |
| **Best for**                  | routine, trusted, low-stakes                 | the everyday default             | new / sensitive / high-stakes           |
| **Costs the user**            | risk of an unwanted spend before they notice | one review per task              | time + attention, many clicks           |
| **Engine posture (internal)** | L5 `AUTONOMOUS`                              | L4 `DELEGATING`                  | L3 `SUPERVISED`                         |

Source: `04-trust-posture…` §1.2, §2, §9.4. Two facts hold across **all three**: (a) the plan
is always **surfaced and recorded** before running, even when it auto-approves
(`briefs…` §3e); (b) **transparency and rewind are posture-independent** — you can always show
the work and rewind any step, no matter which posture ran it (`07-…architecture.md` §5, which
is orthogonal to §4 posture).

> **Why three buttons and not the engine's five rungs.** The underlying engine has five levels;
> the user sees three. This is a deliberate narrowing — it trades a power-user's access to the
> two hidden rungs (interface-only and co-plan-first) for a control a non-coder can actually
> reason about (`04-trust-posture…` §1.2 cons). Recorded here as a known limitation, not an
> accident.

---

## 7. What is shown vs. what stays a black box (the boundary, stated crisply)

The user should never be confused about what they can and cannot inspect, because a fuzzy
boundary is a broken promise (`07-…architecture.md` §2). The flow shows **everything the agent
puts into and gets out of the world and the model**, and nothing of the model's private
internal computation.

| **Always shown on the timeline**                           | **Never shown (the black box)**                         |
| ---------------------------------------------------------- | ------------------------------------------------------- |
| What each step took as input (the data, the prior results) | The model's private step-by-step "scratchpad" reasoning |
| The agent's plan and its fan-out decision ("3 helpers")    | The model's internal numbers/weights                    |
| Every tool call — which system, what it asked for          | _Why_ the model picked one word over another            |
| Every tool result — the rows that came back                |                                                         |
| Every output, versioned                                    |                                                         |
| Which posture was in force, the cost, the time             |                                                         |

Source: `07-…architecture.md` §2.1–2.2; `briefs…` §3f. **The one subtlety:** if the model
_itself_ volunteers a short summary of its approach at its output, that summary **is** shown
(it came out of the model's surface). What is never shown is the raw internal cognition, which
no one — not even the model's maker — can faithfully record (`07-…architecture.md` §2.2). The
boundary the user can rely on: _"We show everything that goes into and comes out of the model.
We do not claim to show how it thinks inside."_

---

## 8. The honest unknowns this flow depends on (flagged, not glossed)

This is a narration of **target-state** behaviour. Several pieces of it ride on design
problems that are genuinely unsolved, and the founder must hold them clearly. Ranked by how
likely they are to make this flow _unusable for a non-coder_ (not unbuildable — the engine is
the tractable part; legibility is the frontier — `07-…architecture.md` §10; `04-trust-posture…`
§10).

1. **The rewind/version UX for non-coders (the dominant risk).** "Rewind, compare two
   versions, revert" are concepts even programmers find hard (version control is famously
   confusing). Step 5's gesture is the heart of the product _and_ the place it is most likely
   to bewilder a non-expert. No research file resolves this; it is iterative design + user
   testing (`07-…architecture.md` §8 #1, §10; `04-trust-posture…` §10 #1).
2. **"Re-figure vs keep-recorded" (Step 5's per-step choice).** Because model steps don't
   always answer the same way twice, the user is asked to choose between a fresh result and the
   saved one. If that choice confuses them, the feature feels unpredictable. Surfacing it
   honestly (rather than guessing silently) is the right call, but the wording is unsolved
   (`07-…architecture.md` §5.3, §8 #2).
3. **The cost/latency of judging "is this consequential?" by model on every action (the "Step
   through" posture).** The
   principled no-keyword-routing choice (§5) adds a model call per action; the caching
   mitigation is unproven at scale, so a many-step _Step through_ run could feel sluggish or
   expensive (`04-trust-posture…` §10 #2).
4. **The "Go ahead" confirmation gesture.** Letting a user opt _up_ to more autonomy must use a
   gesture the agent itself cannot fake on the user's behalf (a typed confirmation, a
   re-auth) — the developer version is a paste-back code, and the non-coder equivalent needs
   design (`04-trust-posture…` §7.2, §10 #3).
5. **A surprising-but-correct recompute (Step 5).** When a re-figure genuinely changes a model
   step, the new result may differ in ways that are _correct_ but _surprising_ ("I only changed
   the FX rate and the whole summary's tone shifted"). The flow must make _what changed and why_
   legible between versions, or the recompute feels arbitrary (`07-…architecture.md` §5.3).
6. **Many humans, one objective (the team dimension).** The brief is team-oriented
   (`briefs…` §3d); when several stakeholders share one report, whose posture governs, and how
   approvals compose, is unspecified — it is where this flow meets the multi-human substrate
   (`04-trust-posture…` §10 #4).
7. **A wide cascade with no cost preview.** A change near the _root_ of a big task can
   legitimately invalidate everything downstream; without a "this rewind will recompute ~N
   steps, est. $X — proceed?" preview, a single edit could trigger a large, surprising re-run
   (`07-…architecture.md` §8 #3).

The first two decide whether the _signature gesture_ (Step 5) lands for its audience. They are
the bet, stated honestly.

---

## 9. Why this flow is the moat, in one line per moat

- **M1 (transparent, versioned, intervene-from-any-step).** Steps 4–5 _are_ M1: the glass box
  with an undo-from-anywhere button, put in front of a non-coder. No surface-thesis competitor
  has productized this for non-coders (`07-…architecture.md` §1; strategic spine: lead the
  story with M1).
- **M2 (execution-time, posture-graded governance).** Steps 2–3 and the §4–§5 variants _are_
  M2: the rein chosen _beforehand_, the plan surfaced as an approvable object, gates that fire
  per posture. Ship this first — it's the most-proven moat (`04-trust-posture…` §0; spine).
- **M3 (multi-human + agent substrate).** The team dimension (§8 #6) is where this flow extends
  to many stakeholders sharing one objective (`04-trust-posture…` §12).
- **M4 (governed cross-org artifact exchange).** The provenance attached to the delivered
  report (Step 4) is exactly what makes a work-artifact safe to _publish and consume across
  orgs_ later — the network-effects engine (strategic spine; `07-…architecture.md` §3).

The flow does not compete on "an agent does your work in one interface" — that surface is
contested (Claude Cowork, GA April 2026). It competes on the **substrate underneath**: that the
work is transparent, governed beforehand, correctable from any step, and carries its
provenance. That conjunction is the moat (strategic spine; `07-…architecture.md` §1).

---

## 10. Source ledger

Every load-bearing claim above resolves to one of:

- **`briefs/01-vision.md`** — §1 (the multi-tool pain / human-as-integration-layer), §3e (the
  3Q-report worked example: state intent → spin up 3 agents → surfaced + recorded → posture
  beforehand → L5/L4/L3 → retrace + intervene → versioned), §3f (the transparency boundary:
  input/output shown, model's thinking is the black box), §4 Decisions A (comms wedge) and B
  (capability-first, surface deferred).
- **`01-analysis/07-transparency-intervention-architecture.md`** — §1 (why it's the moat +
  the symmetric risks), §2 (the transparency contract; what's recorded vs the black box;
  traceability-not-accountability), §3 (the provenance ledger + the six invariants), §4
  (posture surfacing; plan-as-approvable-object; HITL/HOTL; safety floor), §5 (intervention +
  cascade recompute; branching; re-run vs replay vs branch; the worked 3Q example, §5.4),
  §8/§10 (the risk register).
- **`02-plans/04-trust-posture-permissions-plan.md`** — §1.2 (the 3-button → 5-rung mapping),
  §2 (HITL/HOTL = the posture choice; structural vs execution gates), §3 (envelopes;
  delegation-only-tightens), §4 (plan_proposed card; USER pause; verdict→prose renderer), §5
  (per-objective budget + 80/95/100% alerts), §7 (set/upgrade/downgrade; challenge-nonce →
  non-coder gesture; signed anchors), §9 (the recommended v1 model; default-supervised-opt-up;
  min(user, floor); SHADOW rollout), §10 (the usability unknowns), §11 (comms-wedge plug-in),
  §12 (relationship to M1/M3/M4).
- **`01-analysis/01-research/05-cli-harness-universal-interface.md`** — §0/§2 (the harness is
  a domain-agnostic work runtime configured for coding; ~9 of 12 capabilities transfer), §1.4
  (MCP as the universal connector; same protocol for `git` and for SAP/Salesforce), §2/§6.2
  (no-compiler → transparency/posture is the load-bearing substitute), §3.4 (dev-MCP →
  business-MCP), §5.2 (tools are dumb endpoints, the LLM reasons — the enabler of the
  transparent trace).
- **The strategic spine (Phase A)** — moats M1–M4 and their build order; the agent-as-
  integration-layer paradigm shift; "transparency makes depth legible"; the Cowork surface
  threat; Decisions A and B.
- **COC rules** — `communication.md` (plain language, outcomes-not-implementation),
  `recommendation-quality.md` (symmetric pros/cons on every posture trade-off),
  `agent-reasoning.md` (no keyword routing — the L3 consequentiality judgement),
  `spec-accuracy.md` (flag the §8 unknowns, don't paper over them),
  `autonomous-execution.md` (the open-design risks framed as the frontier, not staffing).
