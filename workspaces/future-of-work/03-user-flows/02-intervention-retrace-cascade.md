# User Flow 02 — Retrace + Intervene + Cascade Re-Execution (the M1 signature flow)

> **Purpose.** This is the walkthrough of the platform's signature capability — **moat M1**: a non-coder
> reviews the recorded trace of work an agent did, rewinds to an earlier step, changes it, and the
> platform re-runs *only* the parts that genuinely depend on that change — while every prior result
> survives, untouched, as a named version you can compare against and return to. This is the "non-coder
> glass box with undo-from-anywhere" made tangible: what the user *sees*, *clicks*, and *gets back*.
>
> **Audience.** A technical founder deciding whether this flow is buildable and worth building, and a
> designer who will build the surface. Plain language throughout; every technical term is translated on
> first use (per `.claude/rules/communication.md`). Effort, where mentioned, is in **autonomous
> execution cycles** — focused sessions an AI agent system completes — never human-days or team-size
> (per `.claude/rules/autonomous-execution.md`).
>
> **Grounding.** Every load-bearing claim resolves to one of three files read in full:
> `01-analysis/07-transparency-intervention-architecture.md` (the architecture decision document; cited
> `07 §X`), `01-analysis/01-research/06-transparency-intervention-versioning.md` (the
> provenance/cascade/versioning research; cited `R06 §X`), and
> `02-plans/03-provenance-cascade-design.md` (the engine design plan; cited `Plan03 §X`). The brief
> (`briefs/01-vision.md` §3e–3f) is the authoritative requirement surface. Genuine uncertainty is
> flagged, not smoothed (per `.claude/rules/spec-accuracy.md`).
>
> **CLI-neutral.** This flow describes the *product surface a non-coder uses* — a screen, not a
> terminal. Where it touches engine internals, it names them conceptually, not in any one CLI's syntax
> (per `.claude/rules/cross-cli-artifact-hygiene.md`).
>
> **Companion flows.** User Flow 01 (the forward run: state intent → pick posture → watch the plan +
> execution stream) produces the trace this flow consumes. This flow begins where Flow 01 ends: the
> work is done, the report is on screen, and the user wants to *change something that already happened*.

---

## 0. The one-paragraph thesis of this flow

The user asked for a 3Q financial report. An agent planned it, fanned out to sub-agents, queried
systems, and produced a report — all recorded (Flow 01). Now the user is reading it and realises one
input was wrong: the bookings number was pulled for the wrong date range, or the revenue-recognition
assumption doesn't match how their finance team actually books revenue. In every tool that exists
today, the only options are "live with it" or "ask the agent to start over" — and starting over throws
away everything that *was* right. This flow gives a third option that no competitor has productized for
non-coders (`07 §1`, `R06 §0`): **open the trace, find the wrong step, fix it there, and let the
platform recompute only what that change actually touches** — the corrected revenue section and the
final report — while the costs and cash-flow sections it didn't touch stay exactly as they were, and
the *original* report survives as version 1 next to the corrected version 2. The user never sees code.
They see a timeline, a plain-language preview of what their change will cost, a confirm button, and two
versions side by side.

---

## 1. Where the user starts — the trace / timeline view

### 1.1 What's on screen

The user is looking at the finished 3Q report. A persistent control — call it **"Show how this was
made"** — opens the **trace view**: a vertical timeline of every step that produced this report, newest
at the top or oldest at the top (a user preference), rendered from the provenance ledger (the permanent,
inspectable record of everything the system did — `Plan03 §1`, `07 §3`).

Each step in the timeline is a card. A card shows, in plain language (this is the transparency surface
defined at `07 §2.1`, `R06 §5.1`, `Plan03 §2.1`):

| On the card                  | What the user reads                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------- |
| **What this step did**       | "Pulled Q3 bookings from the CRM" · "Worked out recognised revenue" · "Wrote the revenue section"   |
| **What went in**             | The inputs it consumed — the date range, the assumption, the prior step's result                    |
| **What it reached out to**   | The tool call — "queried the CRM for bookings between 1 Jul and 30 Sep"                              |
| **What came back**           | The tool result — "412 bookings, total \$3.1M"                                                       |
| **What it produced**         | The output — the number, the paragraph, the section — marked **v1**                                  |
| **How it ran**               | A small badge: the **posture** in force when it ran — "Ran on its own" / "You approved this" / "You stepped through this" — plus model, cost, and time (`07 §2.1` metadata row; `Plan03 §6` invariant 5) |

The cards are connected by lines showing **what fed what** — step B sits below step A because B used
A's result (the `depends_on` edges from `Plan03 §1.2`). This is the part that makes intervention *safe*
for a non-coder: you can only let a non-expert change something if they can *see* what they're changing
and what hangs off it (`07 §1`, the "transparency makes depth legible" point).

### 1.2 The one honest boundary, stated on the surface

One thing the trace deliberately does **not** show: *how the model thought*. The cards show what went
in and what came out of every model call, but not the model's internal reasoning — because that is
either not exposed by the model at all, changes between model versions, or is the most sensitive content
(`07 §2.2`, `R06 §5.3`, `Plan03 §2.2`). Where a model *volunteers* a short summary of its approach, the
card shows that summary. The product copy states this plainly so the promise is never over-claimed
(`07 §2.2`): **"We show you everything that went into and came out of each step, including any summary
the AI gives of its own approach. We can't show you the AI's private reasoning — no one can record that
faithfully."**

This boundary is also a *trust* honesty: the system gives **traceability** (every action traces back to
its inputs and the human authority that permitted it) — it cannot give **accountability** (that a human
actually understood it). The glass box makes understanding *possible*; it can't force it (`07 §2.3`,
`Plan03 §2.3`). The surface promises the glass box, not the looking.

### 1.3 What the user does next

The user scrolls the revenue branch of the timeline, reading the cards. On the **"Pulled Q3 bookings
from the CRM"** card they see the input: *"date range: 1 Apr – 30 Sep"* — a six-month range, not the Q3
three-month range they wanted. (Or, on the **"Worked out recognised revenue"** card, the assumption
*"recognise on invoice date"* when their finance team recognises on delivery.) They click that card's
**"Change this step"** control. This is the retrace.

---

## 2. Retracing to an earlier step — and what "retrace" means here

### 2.1 The user picks the step

Clicking **"Change this step"** opens the step in an editable view. It shows the same card content, but
now the **inputs are editable fields** the user understands:

- For the bookings step: a **date-range picker** pre-filled with `1 Apr – 30 Sep`.
- For the revenue-recognition step: a **plain-language assumption selector** ("Recognise revenue on:
  ☑ invoice date / ☐ delivery date / ☐ contract start") pre-filled with the recorded choice.

The user is editing *one step's inputs* — not writing code, not editing the report directly. They change
the date range to `1 Jul – 30 Sep` (or flip the assumption to "delivery date"). They have not committed
anything yet.

### 2.2 What the platform does the instant they edit (and why old work is safe)

The moment the user changes that input, the platform does **not** mutate the recorded step. It prepares
a **new** version of that step — call it the corrected step — with a new input fingerprint, and leaves
the original step and its recorded output completely untouched (`07 §5.1` step 2; `R06 §2.1` step 2;
`Plan03 §3.1` step 2). This is the structural guarantee behind "old outputs are versioned": nothing is
overwritten, ever (the **immutability** invariant — `Plan03 §6` #1, `07 §3.4` #1). The original
bookings number, the original revenue section, the original report — all still exist, byte-for-byte,
identifiable by their content fingerprint (a short code that changes completely if even one byte
changes, the way Git identifies a commit — `Plan03 §1.3`, `07 §3.2`).

So before the user has even confirmed anything, the safety property holds: **the change cannot destroy
what was there.** The worst case is they preview the consequence and decide not to do it.

### 2.3 The v1 honesty: linear retrace, no branching

Here is a limit the surface states plainly rather than hiding. In v1, retracing **advances the single
main timeline in place** — it does not create a parallel "what-if" branch you can hold next to the
original and compare side-by-side as two living timelines (`Plan03 §4.2`, §4.3, §8.3; `07 §5.2`).

The engine *could* support branching cheaply — because everything is content-fingerprinted, a fork
reuses all unchanged history by reference and only the diverging part is new data (`R06 §2.2`,
`Plan03 §1.3` #2). The reason v1 omits it is **not** cost; it is **legibility**. "Rewind, fork, compare
two timelines, merge or revert" is the single hardest concept in this whole product for a non-coder —
Git-style branching is hard even for programmers (`07 §8` unknown #1; `R06 §2.2`; `Plan03 §4.3`). v1
ships the *value* of branching (nothing is ever lost; you can always go back to any prior version)
**without** the *confusing concept* (parallel divergent timelines). The cost, stated honestly: to
compare two genuinely different approaches, the user works **sequentially** — make the change, look at
the result, and if they prefer the original, **revert** to it — rather than viewing both at once
(`Plan03 §4.3`, §8.3 row 1). Branching is the first post-v1 extension, added only after the linear
surface is validated with real non-coder users (`Plan03 §4.3`).

> **In the user's words on screen:** *"Changing this step will update your report. Your current version
> is saved — you can always come back to it."* No mention of branches, forks, or timelines. The mental
> model is "edit + undo," not "version control."

---

## 3. The cascade COST PREVIEW — the gate that makes a non-coder safe

### 3.1 Why a preview exists at all

This is the single most important screen in the flow, and it exists because of a real risk named in the
analysis: a change near the *root* of a wide tree of dependent steps can *legitimately* invalidate
everything downstream of it. Content-fingerprint skipping (§4) bounds the *unnecessary* re-runs, but if
the user genuinely changed something everything depends on, everything genuinely must re-run — and that
could be large, slow, and costly (`07 §7.3` "the cost-preview problem"; `07 §8` #3; `R06 §8`;
`Plan03 §8.4` #3). A non-coder must never trigger a big, expensive, surprising recomputation by
accident. So before anything runs, the platform shows a **plain-language preview of the blast radius**
and asks for an explicit yes.

### 3.2 What the preview shows

After the user edits the input (§2.1) and before they confirm, the platform walks the dependency graph
to find every step downstream of the changed one, then *estimates* — from the recorded cost and time of
those steps last time they ran (`07 §7.2` `ExecutionMetric` reuse; `R06 §8`; `Plan03 §7.2`) — what the
recompute will involve. The preview reads, in plain language:

```
┌─ Preview: what your change will do ─────────────────────────────┐
│                                                                  │
│  You changed:  Q3 bookings date range                            │
│                1 Apr – 30 Sep  →  1 Jul – 30 Sep                  │
│                                                                  │
│  This will re-do 4 of the 9 steps that made your report:         │
│    • Recognised-revenue calculation                              │
│    • Revenue section write-up                                    │
│    • Report assembly                                             │
│    • Executive summary                                           │
│                                                                  │
│  These 5 steps stay exactly as they are (your change             │
│  doesn't affect them):                                           │
│    • Q3 costs pull        • Costs section                        │
│    • Cash-flow pull       • Cash-flow section                    │
│    • Title page                                                  │
│                                                                  │
│  Estimated:  ~40 seconds · about \$0.12 · 2 AI calls re-run       │
│                                                                  │
│        [ Keep the original ]        [ Apply my change ]          │
└──────────────────────────────────────────────────────────────────┘
```

The "**re-run 4 of 9**" framing is the heart of the value proposition made visible: the user *sees* that
their fix is surgical, not a from-scratch redo. The "**these 5 stay exactly as they are**" line is the
"only affected downstream" guarantee (`Plan03 §6` #4 cascade minimality) shown as reassurance — the
costs and cash-flow work they were happy with is provably untouched.

### 3.3 The confirm gate

The preview's **"Apply my change"** button is the confirm gate. Nothing recomputes until the user clicks
it. This is the deliberate-exclusion-from-v1 of *automatic cascade execution without preview*
(`Plan03 §8.3` row 4): the pro is that one root edit can never silently trigger a giant re-run; the
honest con is that it adds one click to every rewind. For a non-coder editing a financial report, that
click is the right trade — the alternative (a surprising \$-and-minutes recompute the user didn't
sanction) is exactly the failure this gate prevents.

If the preview shows a *large* blast radius (say, the user changed something near the root and the
estimate is "re-do 8 of 9 steps, ~6 minutes, ~\$2.40"), the same screen surfaces it loudly so the user
makes an informed choice — the preview's whole job is to make a big cascade *visible before* it runs,
not after (`07 §8` #3).

> **Uncertainty flagged (per `spec-accuracy.md`).** The *accuracy* of the estimate is an open design
> point: it is derived from historical step cost/latency (`ExecutionMetric`), and an LLM re-run's cost
> can vary from last time. v1 should label it an estimate ("~40 seconds," "about \$0.12"), not a
> promise, and the resolution path is engine design + calibration against real runs (`Plan03 §8.4` #3,
> `07 §8` #3).

---

## 4. The recompute — "only affected downstream," shown as it happens

### 4.1 What runs and what doesn't

On confirm, the engine re-runs the dirty steps in dependency order. For each downstream step it
recomputes that step's input fingerprint from its (possibly-unchanged) upstream. **If the fingerprint
matches what was recorded, the step is skipped and its recorded output is reused** — only steps whose
inputs *actually* changed re-run (`07 §5.1` step 4; `R06 §2.1` step 4; `Plan03 §3.1` step 4). This is
the mechanism behind the preview's "5 steps stay exactly as they are": the costs pull, the costs
section, the cash-flow pull, the cash-flow section, and the title page all recompute to *identical*
fingerprints, so they're skipped — instantly, at no cost.

A subtle and valuable behaviour to surface: the cascade can **halt early**. If a step that depended on
the changed one happens to produce an identical result anyway (because the changed input didn't actually
move *its* output), the change stops propagating right there — its descendants are skipped too
(`07 §5.1` step 4; `R06 §2.1` step 4; `Plan03 §3.1` step 4). The user doesn't need to understand this;
they just see fewer steps re-run than they might have feared, which the preview already told them.

### 4.2 What the user watches

The trace view animates: the 4 affected cards show a "re-doing…" state in dependency order; the 5
untouched cards show a quiet "unchanged" check. This is the same live event stream Flow 01 used to show
the work happening the first time (`07 §4.1`, `R06 §4.1`) — reused here to show the *recompute*
happening. When it finishes, each re-run step has a **new output marked v2**, sitting above its v1.

### 4.3 The non-deterministic-step handling — the genuinely hard part, made a visible choice

Here is the problem the brief's vision glosses and this flow must not (`07 §5.3`, `R06 §3` gap 4,
`Plan03 §4`): **AI steps are non-deterministic — the same prompt can give a different answer next
time.** "Rewind and re-run" is clean for a spreadsheet (it recalculates the same way every time); it is
genuinely hard when the steps being re-run are *model calls* that may legitimately answer differently
the second time.

The platform's rule, and the default the user experiences (`07 §5.3`; `R06 §3` gap 4, §7.1 invariant 3;
`Plan03 §4.2`, §6 #3):

- **For every step the user did NOT touch: reuse the recorded output.** The engine reuses the exact
  recorded answer by fingerprint and does *not* call the model again. This is why a rewind is
  predictable and free for untouched steps — and why the costs/cash-flow sections come back identical,
  not subtly reworded. (Reuse = the "**replay**" intent from `07 §5.3`.)
- **For the step the user DID change: an explicit choice, surfaced — never a silent default.** Because
  the user changed this step's input, re-running its *model call* is sometimes what they want (a fresh
  answer for the new input) and sometimes not (they only wanted the number recomputed, not the prose
  reworded). Guessing wrong silently is the worst outcome (`07 §5.3`, `Plan03 §4.2`). So the platform
  asks, on the changed step:

```
┌─ One quick choice for the revenue section ──────────────────────┐
│                                                                  │
│  You changed an input this section is based on. Should the AI:   │
│                                                                  │
│   ◉  Write a fresh version using your new number                 │
│        (the wording may change too)                              │
│                                                                  │
│   ○  Keep the existing wording, just update the number           │
│        (only re-run what your change affects)                    │
│                                                                  │
│                              [ Continue ]                        │
└──────────────────────────────────────────────────────────────────┘
```

The first option is the "**re-run**" intent (re-execute the model with the changed input; the answer may
legitimately differ — `07 §5.3` re-run row). The second is the conservative path (recompute the
dependent values without re-generating prose where avoidable).

### 4.4 The legitimate-divergence honesty

When a re-run *does* re-generate a model step, the new answer may differ from the old in ways that are
*correct but surprising* to a non-coder — *"I only changed the date and now the whole tone of the
revenue section is different."* The product must make this **legible**, not pretend re-runs are
deterministic (`07 §5.3` legitimate-divergence caveat; `Plan03 §4.2` con (c)). So when v2 differs from
v1 in more than the number, the surface flags it: *"Heads up — re-writing this section also changed some
wording. Compare the versions to see what's different."* — and links straight to the compare view (§5).
This is a UX obligation, and it is part of why the non-coder versioning UX is the dominant risk in the
whole product (`07 §8` #1, `Plan03 §8.4` #1).

> **Honest framing of the burden.** The per-step "fresh version vs keep wording" choice (§4.3) is a real
> conceptual load this flow *partly pushes onto the user*. If users find it confusing, the feature feels
> unpredictable (`07 §7.3` cons; `Plan03 §4.2` con (a); `07 §8` #2). v1's mitigation is to (a) default
> the untouched steps to silent reuse so the choice only appears on the *one* step the user actually
> edited, and (b) make the consequence legible after the fact (§4.4). Whether that is enough is a
> genuine open question resolved only by testing with real non-coders (`Plan03 §8.4` #2).

---

## 5. The new version appears alongside the old — compare and restore

### 5.1 What the user sees when it's done

The report on screen is now the corrected one, labelled **v2**. But v1 did not disappear. A version
control surfaces on the report (and on each section that changed):

```
Revenue section:  ● v2 (current) · changed just now      ○ v1 · original
Full report:      ● v2 (current)                          ○ v1
```

Every re-run step's output was written as a **new version with a back-pointer to the prior version** —
the lineage `v1 → v2` is a chain, nothing overwritten (`Plan03 §1.4`, §5; `R06 §2.1` step 5;
`07 §5.1` step 5). The user can click **v1** on any changed item to view exactly what it was before
their edit.

### 5.2 Compare two versions — a content diff, no recompute

Selecting **"Compare v1 and v2"** opens a side-by-side view of the two versions of that output. This is
purely a **content comparison** — it does not re-run anything (`R06 §2.2`, `Plan03 §5`). For the revenue
section it might show: the bookings figure changed `$3.1M → $1.8M`, the recognised-revenue line changed
accordingly, and (if the user chose "fresh version" at §4.3) the surrounding prose, highlighted. For a
text output the diff is highlighted phrase-by-phrase; for a number, the before/after values.

This compare-versions surface is what converts "old outputs are versioned" from a storage fact into a
*usable* feature: the user can see precisely *what their intervention changed* and decide whether they
prefer it (`07 §5.4` step 7).

### 5.3 Restore (revert) — cheap and lossless

If the user looks at the comparison and decides the original was better, **"Restore v1"** repoints the
report back to v1. Because nothing was ever destroyed — v2 didn't overwrite v1, it sat *next to* it —
restore is just changing which version is "current"; the data was never lost (the immutability
invariant — `Plan03 §5`, §6 #1; `07 §3.4` #1). And v2 isn't destroyed by the restore either; it remains
available, so the user can flip back again. In v1's linear model (§2.3) this sequential
"make-change → compare → keep-or-restore" loop is *how* a non-coder explores alternatives, standing in
for the side-by-side branching deferred to post-v1 (`Plan03 §4.3`, §8.3 row 1).

### 5.4 The intervention is itself recorded — a permanent, audited event

The rewind is not a silent edit to history. *"User X changed the Q3 bookings date range at the bookings
step at time T"* is written as a **new audit record** in the provenance ledger — who retraced, what they
changed, when (`07 §5.4` step 8, §3.4 #6; `R06 §7.1` audit-completeness invariant; `Plan03 §6` #6).
This means the trace view itself now shows the intervention as part of the story: a future reader (or the
same user next quarter) sees that the report was corrected, by whom, and from what to what. The glass box
records the act of reaching into it.

---

## 6. The full worked example, start to finish (the brief's 3Q report)

Tracing the brief's own example end-to-end through the surface above (`07 §5.4`, `Plan03 §5`), with the
prompt's CRM-bookings-date-range variant as the concrete edit:

1. **The work was done (Flow 01).** "I want a 3Q financial report." Posture chosen beforehand: **"Ask
   me once."** The agent proposed a fan-out — three sub-agents, one each for **revenue**, **costs**,
   **cash flow** — shown on screen as an approvable plan before anything ran; the user approved once;
   the work executed and was recorded. The report is on screen. (Posture surfacing is moat M2, the
   subject of its own flow; here it is the *context* the trace inherits — each step carries its
   posture-at-time badge per §1.1.)

2. **The user opens the trace** (§1). They scroll the **revenue** branch and reach the **"Pulled Q3
   bookings from the CRM"** card. Its input reads *date range: 1 Apr – 30 Sep* — a six-month pull, not
   Q3. The error is now *visible*, which it never is in today's tools.

3. **The user retraces** (§2). They click **"Change this step,"** and in the date-range picker change
   `1 Apr – 30 Sep` to `1 Jul – 30 Sep`. The original bookings step and its `$3.1M` output are left
   untouched — preserved as v1 the instant the edit begins (§2.2).

4. **The cost preview appears** (§3). *"This will re-do 4 of the 9 steps: recognised-revenue, revenue
   section, report assembly, executive summary. These 5 stay exactly as they are: costs pull, costs
   section, cash-flow pull, cash-flow section, title page. ~40 seconds · about \$0.12."* The user reads
   that the **costs and cash-flow work they were happy with is provably untouched**, and clicks **"Apply
   my change."**

5. **The cascade recomputes only what's affected** (§4). The revenue downstream and the final report
   re-run; the **costs** and **cash-flow** sub-agents' steps are **skipped** because their input
   fingerprints are unchanged (`07 §5.4` step 6). On the changed revenue step, the user is asked the one
   determinism question (§4.3) — they pick "keep the existing wording, just update the number." The
   bookings figure recomputes to `$1.8M`, recognised revenue updates, the revenue section and report
   re-flow with the corrected number.

6. **Versions appear** (§5). The original revenue section and original report survive as **v1**; the
   corrected ones are **v2**, back-pointed to v1. The user opens **"Compare v1 and v2"** and sees
   exactly the bookings/revenue figures change, prose otherwise intact (because they chose "keep
   wording"). Satisfied, they keep v2; had they preferred the original, **"Restore v1"** is one click
   and lossless.

7. **The intervention is audited** (§5.4): *"User X changed the Q3 bookings date range from
   1 Apr – 30 Sep to 1 Jul – 30 Sep at the bookings step at time T"* is now a permanent record visible
   in the trace.

Every step above maps to an existing primitive *except* the cascade in step 5 and the timeline/compare
surface in steps 2–6 — which is exactly the 80%-reuse / 20%-net-new split the architecture keeps
returning to (`07 §5.4` closing note; `Plan03 §0`, §3.1). The hard new engineering (the reactive cascade
engine) is bounded and testable; the open frontier is the *legibility* of this surface for non-coders
(`07 §8`, `Plan03 §8.4`).

---

## 7. Where this flow first ships — the comms wedge

The first place a real user walks this flow is **not** the full 3Q-report scenario but the **comms
wedge** — the existing Sequor communication-coverage product, folded in as the first vertical
(`R06 §6.2`, `07 §6.4`, `Plan03 §8.1`). Its work is a small, concrete instance of the same graph:

```
Message  →  Classification  →  RAG-retrieval  →  Response  →  (auto-send | Escalate)
```

Each is a Step; the drafted `Response` is a versioned Output; the classification reasoning and the
retrieved passages are recorded I/O (`R06 §6.2`). The wedge's *existing* discipline — log a
classification correction as a new audit row — is literally this flow's retrace-and-version primitive
**already specified in prose** (`R06 §6.2`, `Plan03 §8.1`). So the first real walk of this flow is:

> A support lead opens the trace on a drafted reply, sees the message was **mis-classified** (routed as
> "billing" when it was "cancellation"), clicks **"Change this step,"** corrects the classification, and
> the platform re-runs the retrieval + the drafted response — *only* those — while preserving the
> original draft as v1. The lead compares the two drafts and sends the corrected one.

This proves retrace + intervene + cascade on a **4-step flow** before generalising to arbitrary
multi-agent objectives like the 3Q report (`Plan03 §8.1`, §8.2). Governance runs in **observe-only
mode** under the live product during rollout, so nothing the user relies on today breaks while the new
surface is calibrated (`R06 §6.2`, `Plan03 §8.1`).

**Effort to a working end-to-end walk on the wedge: ~4–6 autonomous execution cycles** (the engine + the
ledger wiring), because the substrate — the data model, the durable store, the event stream, the posture
machine — is reused, not rebuilt (`R06 §7`, `07 §6.3`, `Plan03 §8.2`). This estimate is the *engine*;
the non-coder *surface* described in this document is the open-ended frontier that is iterated against
real users, not built in one pass (`Plan03 §8.2`, §8.4 #1).

---

## 8. The v1 limits, stated together and honestly

A non-coder needs to know what this flow does *not* do in v1, so the promise is never over-claimed. All
of these are deliberate cuts with named pros and cons (`Plan03 §8.3`; `07 §8`):

| v1 limit                                                 | Why v1 omits it (pro)                                                                                  | The honest cost (con)                                                                                                          |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Linear retrace only — no parallel branches**          | Removes the single hardest non-coder concept (Git-style divergent timelines) from the first release (§2.3) | "Explore a what-if side-by-side" is deferred; users compare *sequentially* via make-change → compare → restore. Immutable versions are the safety net, not branches. |
| **One change at a time per cascade**                    | A single, previewable blast radius the user can reason about; keeps the cost preview honest             | A user wanting to change two unrelated inputs does it as two rewinds, each with its own preview/confirm.                       |
| **Cost preview is an estimate, not a promise**          | Honest about LLM cost variance; avoids a false guarantee (§3.3)                                        | The actual recompute may cost a little more or less than shown; v1 labels it "~" and calibrates over time (`Plan03 §8.4` #3). |
| **Determinism choice surfaced per edited step**         | Never guesses silently on the one decision where guessing wrong is the worst outcome (§4.3)             | It is a real conceptual burden on the user; whether it confuses non-coders is an open question resolved only by testing (`07 §8` #2). |
| **Every version kept forever (no compaction yet)**      | Simplest correct behaviour; nothing is ever lost                                                       | Storage grows with every re-run; content-addressing dedupes identical bytes but not version *count*. A retention policy is owed before scale (`Plan03 §8.3` row 5, §8.4 #5). |
| **Single-process live updates**                         | Correct and simple for the first deployment                                                            | A multi-replica deployment needs a distributed update channel — a scaling step, not a v1 blocker (`Plan03 §8.3` row 3, §8.4 #6). |

And the two limits that are *unknowns*, not cuts — the things that decide whether this flow is *usable*,
not whether it can be *built* (`07 §8`, `Plan03 §8.4`):

1. **The non-coder versioning UX is genuinely unsolved.** "Rewind, change, see only the affected parts
   redo, compare, restore" for someone who has never used version control is the dominant risk in the
   whole product. v1's linear-no-branching cut is the primary mitigation, but the residual risk is real
   and is where this flow is most likely to fail. It is treated as **iterative discovery with real
   non-coder users**, not a one-shot build (`07 §8` #1, `Plan03 §8.4` #1).
2. **The "fresh version vs keep wording" choice may confuse non-coders.** It is surfaced (§4.3) precisely
   because silently guessing is worse — but the choice itself is a burden, and whether the framing lands
   is unresolved until tested (`07 §8` #2, `Plan03 §8.4` #2).

The honest shape of the bet (`07 §8`, `Plan03 §8.4`): **the engine is the tractable part; making this
surface legible to a non-coder is the frontier.** That is the conjunction this flow exists to prove — and
the moat no surface-thesis competitor has assembled in one non-coder interface (`07 §1`, `R06 §0`).

---

## 9. Source ledger

Every claim above resolves to one of:

- **`briefs/01-vision.md`** §3e (retrace-and-intervene, downstream cascade, versioned old outputs;
  posture chosen beforehand), §3f (the black-box boundary), §4 Decisions A (comms wedge) / B
  (capability-first).
- **`01-analysis/07-transparency-intervention-architecture.md`** (`07 §X`) — §1 (why it's the moat +
  the hard problems), §2 (transparency contract + black-box boundary + traceability-not-accountability),
  §3 (provenance ledger + the six invariants), §5 (intervention + cascade mechanism + determinism re-run
  / replay / branch + the 3Q worked example), §6 (reuse vs new + the comms wedge), §7 (recommendation +
  symmetric pros/cons + the cost-preview problem), §8 (the ranked unknowns).
- **`01-analysis/01-research/06-transparency-intervention-versioning.md`** (`R06 §X`) — §0 (80/20
  framing), §2 (intervention semantics: dirty-mark + content-hash skip + version-on-rerun + branching),
  §3 (durable-execution reuse + the determinism gap), §4 (live decision/event stream), §5 (the recorded
  I/O envelope + black-box boundary), §6 (the comms-wedge instance of the graph), §7 (the six
  invariants + the ~4–6-cycle estimate), §8 (risks: cost explosion, storage growth, single-process bus,
  ingestion contract).
- **`02-plans/03-provenance-cascade-design.md`** (`Plan03 §X`) — §1 (content-addressed data model +
  versioned nodes), §2 (transparency contract), §3 (cascade mechanism + durable-execution reuse), §4
  (non-determinism: reuse-recorded default + explicit regenerate + linear-no-branching v1 cut with
  symmetric pros/cons), §5 (immutable versioning + compare + revert + audited intervention), §6 (the six
  invariants + the recommended shard map), §7 (reuse vs extend), §8 (the reduced v1 scope + effort
  estimate + the ranked unknowns + symmetric exclusion table).
- **The strategic spine** — moat M1 (transparent, versioned, intervene-from-any-step work; strongest
  moat, hardest build), the "transparency makes depth legible" point, the compete-on-substrate-not-
  surface stance, Decisions A and B.
- **COC rules** — `communication.md` (plain language, outcomes not implementation),
  `recommendation-quality.md` (symmetric pros/cons), `autonomous-execution.md` (effort in cycles),
  `spec-accuracy.md` (flag uncertainty, don't paper over), `cross-cli-artifact-hygiene.md` (CLI-neutral
  prose), `tenant-isolation.md` / `orphan-detection.md` (the invariants the engine must hold, surfaced
  here as user-visible guarantees).
