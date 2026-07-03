# R3 — Put an Agent to Work Across ≥2 Existing Systems (the Core Loop)

> Value principles embodied: P1 (integrate-and-govern, never replace), P2 (director, not builder), P7 (undo + trace = the trust surface). Also touches P3 (governance as the product) and P4 (meaningful oversight). Wedge: mid-market / SMB departmental edge (the "governed cross-system objective" entry point per the pitch §8); the same loop runs at low stakes on the comms lighthouse.

## The walk (from the director's screen)

The director here is **Dana**, an accounts-receivable manager at a mid-sized company. Dana is not a coder. She has never written a workflow, a script, or a line of configuration. She has two systems her team already lives in: an **accounting ledger** (the system of record for what customers owe) and **email** (where follow-ups get sent). Sequor sits on top of both — it does not replace either.

**1. Dana states an objective in plain language.**
Dana opens Sequor and types, in her own words:

> "Reconcile this month's invoices against the ledger, and draft follow-up emails for anything unpaid past 30 days."

She attaches the invoice spreadsheet her team exported. That is the entire input. She did not pick tools, name systems, or describe steps — she described the outcome she wants, the way she would to a capable new hire.

**2. Sequor shows the plan BEFORE anything runs (the glass box opens early).**
Instead of silently going to work, the agent first shows Dana what it intends to do — a small, readable diagram of its plan, laid out as numbered steps with a fan-out where the work splits:

- Step 1 — **Read** the attached invoices (30 rows).
- Step 2 — **Read** the ledger to find the recorded payment status for each invoice (connects to: Accounting Ledger, read-only).
- Step 3 — **Compare** each invoice to its ledger record; flag the ones unpaid past 30 days (expected: ~6 of 30, based on the data it just read).
- Step 4 (fan-out) — For each flagged invoice, **draft** a follow-up email in the company's tone (connects to: Email, draft-only — nothing sent yet).
- Step 5 — **Assemble** a summary: what was reconciled, what was flagged, the drafts ready for review.

Each step names _which system it touches_ and _whether it reads or writes_. Beside the plan is an estimated cost and time. This plan is a real, recorded object — not a loading spinner. Dana can read it top to bottom and understand exactly what is about to happen, in business terms.

Crucially, **governance sits between the agent and each system.** The agent never talks to the ledger or to email directly. Every read and every write passes through a control layer that checks it against the limits Dana's company set up front — a **least-privilege envelope**. In plain terms: the agent was handed a narrow key, not the master key. For this job the envelope allows _read_ on the ledger and _draft_ on email, and nothing else. Even if the agent tried to delete a ledger entry or send an email outright, the control layer would refuse — the permission simply isn't in the envelope.

**3. Dana approves according to the posture she set beforehand.**
Before this job ever ran, Dana chose _how much rein_ to give the agent — a one-time, plain-language choice she made from three buttons. This is the "how much autonomy" decision, made once, up front, per kind of job. What she sees now depends on which she picked. All three behaviours are part of the product:

- **"Go ahead" (the agent runs on its own).** The plan appears, Dana glances at it, and the agent proceeds without waiting — because reconcile-and-draft is low-risk (it reads money data but only _drafts_ emails; nothing leaves the building). Dana is _on_ the loop: she watches it happen live and can hit stop at any moment, but she is not asked to approve each step. This is the right setting for routine, reversible work.

- **"Ask me once" (one approval, at the plan → run boundary).** The plan appears with a single **Approve / Change / Cancel** choice. Nothing runs until Dana clicks Approve. She reads the fan-out, sees it will draft 6 emails and touch only the ledger read-only, and approves once. From there the agent runs the whole plan straight through. One gate, at the moment that matters most — before any work starts.

- **"Step through with me" (approve each consequential step).** The agent pauses at every step that touches a system and asks. Dana approves "read the ledger," then later approves "draft this specific email," and so on. She is _in_ the loop — the agent literally cannot proceed past a step until she says yes. This is the setting for high-stakes work where she wants to see each move before it happens. It is slower by design; that is the point.

Whichever posture is active, the safety envelope from step 2 still holds underneath it. Posture decides _how often Dana is asked_; the envelope decides _what is even possible_. The two are independent: "Go ahead" does not mean "do anything" — it means "do the permitted things without stopping to ask."

**4. The agent executes across the connected systems — read from one, write to another.**
The agent now does the work, reading from the **ledger** (system A) and writing drafts into **email** (system B). This is the heart of P1: two systems the company already owns, orchestrated together, neither replaced. Concretely:

- It reads the 30 invoices and the matching ledger records.
- It finds 6 invoices unpaid past 30 days (one fewer than its estimate — one was paid yesterday and the ledger already reflected it; the glass box shows this).
- It drafts 6 follow-up emails, each grounded in the actual amount and due date it read from the ledger — no invented numbers.
- Every one of those reads and writes went _through_ the control layer, each checked against the envelope, each stamped with who authorized it (Dana) and under which posture.

**5. Every step is traced live (the glass box stays open).**
As the agent works, Dana's screen shows a running timeline — each step lighting up as it starts and finishes:

- **What went in** (the invoice rows, the ledger query).
- **What the agent decided** ("6 flagged, 24 current").
- **What tool it called** ("read ledger: status for invoices #1001–#1030").
- **What came back** (the actual ledger rows).
- **What it produced** (the 6 drafts), each saved as a versioned result.

Dana is not reading logs or code. She is reading a plain-language activity feed she could hand to her boss. If something looked wrong mid-run, she could stop it — under "Step through" she'd be asked before each move anyway.

**6. Dana ends up with the work done and the receipts.**
When the run finishes, Dana has: 6 reconciled-and-drafted follow-ups sitting in email as drafts (ready for her final send), a summary of what was reconciled, and a complete trace she can replay. Nothing was sent without her — the envelope guaranteed that. Every action carries a line back to her approval. If an auditor later asks "who let the agent touch the ledger, and what exactly did it do?", the answer is one exportable record away.

**The honest hard parts (stated plainly, not hidden):**

- **The agent is not perfectly predictable.** It runs on a language model, which can read the same data and phrase a draft differently on two runs, or occasionally mis-flag an edge case. That is _why_ the plan-first, trace-everything, envelope-bounded design exists — the director sees and bounds the work rather than trusting it blind. The product's job is to make the agent's moves _legible and reversible_, not to pretend they are deterministic.
- **"Go ahead" is a ceiling, not a blank cheque.** If the system detects the agent misbehaving (repeatedly trying actions outside its envelope, or hitting an error pattern), it automatically tightens the reins — drops to a more cautious posture — without waiting for Dana. Upgrades to _more_ autonomy need a human; downgrades to _less_ happen automatically the instant something looks wrong.
- **Legibility for a non-coder is the frontier, not a solved problem.** Showing a fan-out plan a manager can actually read — and helping her tell a "correct but surprising" result from a genuine error — is the part the product must keep earning through real use. This flow is the first honest cut, not the finished answer.

## Features exercised

- **Plain-language objective intake** — the director states an outcome; no tools, steps, or config named.
- **Pre-execution plan surfacing (the `plan_proposed` decision)** — the agent's fan-out plan is captured as a first-class, on-screen, approvable object _before_ any step runs.
- **Three-button posture selector** — "Go ahead" / "Ask me once" / "Step through with me," set once per job-type in plain language; maps internally to the graduated trust ladder.
- **Posture-gated approval routing** — the chosen posture decides whether the plan auto-runs, waits for one approval, or pauses at each consequential step.
- **Least-privilege permission envelope** — a narrow, per-objective grant (read-ledger, draft-email, nothing else); governance sits _between_ the agent and every connector.
- **Cross-system orchestration via standard connectors** — read from system A (ledger), write to system B (email), neither replaced.
- **Live glass-box trace** — inputs, decisions, tool calls, tool results, outputs streamed to a plain-language timeline as work happens.
- **Automatic posture downgrade (safety floor)** — misbehaviour tightens the reins without waiting for the human.
- **Accountability lineage** — every action stamped with the human who authorized it and the posture in force.

## Deliverables / artifacts produced

- **Provenance trace (v1)** — the permanent, inspectable, step-by-step record of the whole run (inputs, decisions, tool calls, results, outputs), each output versioned. This is the substrate R4 rewinds into.
- **Completed cross-system work** — 6 reconciled invoices and 6 follow-up email drafts, each grounded in real ledger data, ready for the director's final send.
- **The approved plan record** — the fan-out the director saw and approved (or watched auto-run), retained as an audit object showing what was intended before execution.
- **Cost-and-time estimate** — shown before the run, alongside the plan, so the director commits with eyes open.
- **Accountability / audit record** — every read and write tied to the director's approval, the active posture, and the envelope it passed through; exportable as an oversight bundle.

## Reuse → net-new

**Shipped substrate reused:**

- **PACT governance records** — the plan, the approval, and each step land as `AgenticDecision` / `Run` / `AgenticArtifact` records; the least-privilege envelope, the HELD-and-approve pause, and the live decision stream (`EventBridge` → screen) are existing PACT machinery.
- **EATP posture machinery** — the three-button selector maps onto the shipped, persisted, signed trust ladder (with the automatic-downgrade safety floor); budgets/clearances come from the existing `BudgetTracker` / `PostureStore`.
- **Kailash durable store + `run_id` spine** — every step is stamped and persisted through the durable execution store that already ships.
- **MCP connectors** — the read-from-ledger / write-to-email bridges are standard connectors into the systems the company already owns.

**Net-new (the concentrated 20%):**

- **The `plan_proposed` surface + posture-gated plan approval** — turning the agent's fan-out into an approvable object _before_ execution, and wiring the chosen posture to decide auto-run vs one-gate vs step-through.
- **The director timeline UI** — rendering the live glass-box trace and the plan as something a non-coder can read and act on (the open design frontier).
- **An LLM-judged "is this step consequential?" assessment** replacing the old keyword classifier, so the step-through gate fires on genuine risk, not matched words.

## Why it matters (grounded)

This is the single near-term proof the pitch stakes everything on (§11): _a non-technical director puts an agent to work across two of their existing systems, under a posture they chose beforehand, and walks away with the work done, a live trace, and an audit bundle they could hand a regulator._ It rides the best-evidenced fact in the market — systems of record survive and incumbents layer agents _on top_ of them (Deloitte ≥5 years; 61% of CIOs buy AI from vendors they already use) — instead of fighting it. And it directly answers the market's #1 blocker: not agent capability, but _deployable control_ (governance is the top-cited barrier to scaling agents; EU AI Act Art. 14 makes human oversight a dated legal requirement from Aug 2026). The loop is what turns "we can't safely let the agent act" into "we deployed it, with a director on the loop and an auditor-ready record."
