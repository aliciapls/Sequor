# R2 — Set governance & posture BEFORE any work

> Value principles embodied: P3 (governance is the product, priced as compliance), P4 (meaningful oversight at scale, not rubber-stamp), P2 (director, not builder), P7 (undo + trace = the trust surface). Wedge: mid-market (departmental edge) with enterprise-compliance-grade controls.

## The walk (from the director's screen)

Dana has connected her systems (see R1). Sequor now does the thing no other tool makes her do: it stops and asks her to decide **how much freedom each kind of job gets — before a single agent runs.** Nothing can act until she has set the rules.

1. **Sequor frames the choice as a plain-language dial, not a settings panel.** The screen says: _"For each kind of work, choose how closely you want to watch."_ Three options, each described in Dana's terms:
   - **Pause-and-approve** — _"The agent prepares the work and waits. Nothing happens until you say yes. Best for anything you'd want to see before it goes out."_
   - **Ask-once** — _"The agent checks with you once at the start, then completes the job. Good for routine work you trust after a quick look."_
   - **Supervise-by-exception** — _"The agent just does the work and only interrupts you when something looks unusual or risky. Best for high-volume, low-stakes tasks."_

2. **Dana assigns a posture to each kind of job.** She sets **"Reply to customer emails" → Pause-and-approve** (she wants to see every reply before it sends). She sets **"Log activity in the CRM" → Supervise-by-exception** (routine, low-risk, high-volume). She sets **"Look up invoice status for a customer" → Ask-once**. She is choosing oversight per _class of job_, in plain language — she never writes a rule, a script, or config.

3. **Sequor shows Dana the safety floor she cannot go below.** When she tries to set a sensitive job — **"Issue a refund"** — to Supervise-by-exception, Sequor gently blocks it: _"Refunds always require your approval. You can watch this one more closely than the floor, but not less."_ This is the **safety floor rule: the real posture is the stricter of what Dana chose and what the system requires — `min(chosen, system-floor)`.** Dana can tighten oversight anywhere; she can never loosen it below the built-in minimum for a sensitive action. She understands instantly: the guardrails protect her even from her own too-generous setting.

4. **Dana sets budgets — plain limits, not code.** _"How much work should an agent do before checking back?"_ She caps the email-reply job at **"50 drafts per day, then pause for review"** and the CRM-logging job at **"200 updates per day."** A budget is a ceiling on autonomous action; hit it, and the agent pauses and reports rather than running unbounded.

5. **Dana sets clearances — the hard "never" list.** A section titled _"Places agents must never go"_ lets her draw bright lines in plain language. She adds **"Never touch payroll," "Never change deal amounts," "Never delete a customer record," "Never email anyone outside our company without approval."** These are absolute — no posture, budget, or agent decision can cross them. They are the walls of the room agents work inside.

6. **Dana marks always-approve actions.** Some actions she wants to personally bless every single time, regardless of how routine they look: **"Anything that sends money," "Anything that emails our top-20 accounts," "Anything that changes a contract."** She flags these as **always-approve**, and they will surface to her for a yes/no no matter what posture the surrounding job carries.

7. **Sequor answers Dana's real worry — "won't I just rubber-stamp everything?"** A short explainer shows how supervise-by-exception is engineered to _not_ become one-click-approve-500: the agent scores its own confidence, surfaces only the unusual cases, and when volume is high it shows Dana a **representative sample to spot-check** rather than a wall of 500 identical approvals. Meaningful oversight is designed in, so her attention lands where it matters (`13-pitch.md` §6, P4).

8. **Dana reviews and approves the whole posture in one plain-language summary.** Sequor shows her the complete picture: each job, its oversight level, its budget, the clearances, the always-approve list, and — where the safety floor overrode her — a note saying so. She reads it like a policy memo, not a config file. She clicks **"Approve and activate."**

9. **Sequor versions and records the policy.** The moment Dana approves, Sequor saves this as **version 1 of her governance policy**, stamped with her name and the date, and keeps it. If she changes a posture next month, the old version is retained — so there is always an answer to _"what were the rules on the day that agent acted?"_ Only now, with the rules set and recorded, will Sequor let any agent begin work.

Dana has authored a complete governance regime for autonomous work — autonomy levels, budgets, hard limits, and personal-sign-off actions — entirely in plain language, and she has proof of exactly what she decided and when.

## Features exercised

- **Per-job posture selection** — pause-and-approve / ask-once / supervise-by-exception, chosen per class of work in plain language.
- **Safety-floor enforcement** — effective posture = the stricter of the director's choice and the system's minimum for that action (`min(chosen, system-floor)`); the director can tighten, never loosen below the floor.
- **Budgets** — plain-language ceilings on how much an agent may do autonomously before pausing to report.
- **Clearances (hard "never" list)** — absolute no-go boundaries ("never touch payroll") that no agent decision can cross.
- **Always-approve actions** — director-flagged actions that surface for personal yes/no every time, regardless of job posture.
- **Anti-rubber-stamp oversight design** — confidence scoring, exception surfacing, and batch-with-sampling so supervise-by-exception stays meaningful at volume.
- **Versioned governance policy** — every policy state saved, human-attributed, and retained so past rules are always recoverable.
- **Pre-work gate** — no agent runs until a policy is approved and active.

## Deliverables / artifacts produced

- A **versioned governance policy (v1)**: every job's posture, budget, clearance, and always-approve setting — human-attributed and dated.
- A **safety-floor reconciliation record**: where the director's choice was overridden by the system minimum, and why, in plain language.
- A set of **hard clearance boundaries** (the "never" list) enforced across every connected system.
- An **always-approve action list** that routes flagged actions to the director for explicit sign-off.
- The **activation gate state**: proof that governance was set _before_ any agent work began.

## Reuse → net-new

**Reuses (shipped substrate):** the comms product already runs graduated autonomy in miniature — its confidence-band routing (auto-send / approve-a-draft / compose-yourself) is exactly posture with fixed bands, and its D/T/R audit rows are the accountability grammar (`09-comms-wedge-mapping.md` §2.1, §2.3). The general posture machinery — the L1–L5 trust ladder, `min(chosen, floor)` reconciliation, human-gated changes — already ships in EATP's posture store and the aegis governed runtime; PACT supplies clearances and envelopes.

**Net-new:** the **director-facing governance authoring UI** that turns a fixed code policy into a _chosen-beforehand, plain-language, per-job_ posture (comms hard-codes three bands; this lets Dana choose oversight per class of work), the **budget + always-approve + clearance surfaces** rendered for a non-technical manager, and **policy versioning as the trust surface** (comms has immutable audit but not user-authored, retained, versioned policy).

## Why it matters (grounded)

Governance is the **#1 cited barrier** to deploying agents — only ~30% of organizations call themselves governance-ready — and **EU AI Act Article 14 makes effective human oversight a dated legal requirement from 2 August 2026** (`12-saas-2.0-thesis.md` §3, ESTABLISHED #9–#10). Setting posture _before_ work, with a safety floor and a versioned record, is precisely the "risk-tiered oversight engineered against the rubber-stamp failure mode" the thesis names as the answer to the strongest counter-argument against oversight products (`12-saas-2.0-thesis.md` §5, move #3). This flow is the product's spine: governance-as-the-deliverable, priced as compliance, not convenience (`13-pitch.md` §6, P3/P4).
