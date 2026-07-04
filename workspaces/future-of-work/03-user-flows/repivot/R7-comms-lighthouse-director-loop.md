# R7 — The comms lighthouse as the live proto-director loop

> Value principles embodied: P4 (meaningful oversight at scale), P7 (undo + trace = the trust surface), P2 (director, not builder), P3 (governance is the product). Wedge: comms (the live, shipped proving ground) → mid-market departmental edge.

## The walk (from the director's screen)

This flow is different from R1 and R2: it is **already shipped and running against real users.** The insight of the repivot is that the comms product's everyday loop — a human approving AI-drafted replies — is not a side feature. **That human is a proto-director, and this loop is the cheapest possible live test of the whole thesis.** Here is the loop as the manager, **Marco** (who runs a busy customer-support desk), lives it, reframed as the first director loop.

1. **A customer message arrives.** A client emails the shared support address: _"Has my order #4471 shipped, and can I still change the delivery address?"_ Marco does nothing yet — the system picks it up.

2. **The agent drafts a reply and shows its confidence.** Sequor's agent reads the message, searches the company's knowledge (past answers, docs, order info), and drafts: _"Hi — order #4471 shipped this morning; the address can no longer be changed, but we can reroute via the carrier. Here's how…"_ It attaches a plain-language **confidence badge** — high / moderate / low — so Marco knows at a glance how much to scrutinize.

3. **The posture decides whether Marco sees it first.** This is the director loop in action, exactly as R2 describes:
   - **High confidence, routine** → the agent can send automatically (supervise-by-exception), and Marco sees it later in his digest.
   - **Moderate confidence** → the agent **pauses and shows Marco the draft to approve or edit** before anything sends (pause-and-approve).
   - **Low confidence** → the agent hands Marco a blank compose with the context, because it would rather ask than guess.
     This message comes back **moderate** — so it waits for Marco.

4. **Marco approves, edits, or rewrites — this is the oversight moment.** He reads the draft, tweaks one sentence ("we can reroute via the carrier — I've started that for you"), and clicks **approve**. The reply goes to the customer. Marco spent fifteen seconds steering work he did not have to write from scratch. He is **directing**, not drafting.

5. **The system learns from Marco's correction.** Marco's edited answer is captured as new company knowledge, attributed to him and timestamped. The next time a similar question arrives, the agent already knows the better answer — coverage rises through use, not through a training project. **The human correction became durable institutional knowledge**, which is the feedback half of the director loop.

6. **Marco gets a digest, not a firehose.** Once a day, Sequor emails Marco a plain summary: how many replies the agent handled on its own, how many he approved, what got escalated, and what the system newly learned. This is oversight-at-scale that respects his attention — he steers the exceptions and reviews the whole in one glance, rather than rubber-stamping every message.

7. **Every step left a trace.** Behind the loop, each action — message received, draft generated, Marco approved/edited, reply sent, answer learned — is written to an append-only, human-attributed record. If a customer later disputes what was said, or a manager asks "who approved this reply?", the answer is one lookup: a named human, a timestamp, the exact text. That is P7's trust surface, live today.

### What this loop instruments (the two speculative bets)

The reason this shipped loop is the lighthouse: it **cheaply measures the two things the whole repivot is betting on** (`briefs/02-repivot-to-saas-2.0.md` §5), on real users, at low stakes.

- **Bet 1 — does a non-builder "director" exist as a real user (and buyer)?** Marco _is_ that person: a non-technical manager whose entire job in this loop is to approve, edit, steer, and correct agentic work. Sequor instruments his behavior — how often he approves vs. edits vs. rewrites, whether he trusts higher-confidence drafts more over time, whether he'd _pay_ for the control surface. Every real Marco is evidence for or against the single most speculative pillar of the repivot: that the director persona exists and is valuable.
- **Bet 2 — does the oversight loop actually deliver value?** The loop measures whether human-in-the-loop approval + learning genuinely improves outcomes: does coverage rise as corrections accumulate? Does the agent's confidence calibrate to Marco's real approve/reject decisions? Does the digest keep oversight meaningful instead of degrading to bulk-accept? These are the exact questions R2's anti-rubber-stamp design must answer — and this loop answers them with live data instead of a slide.

Marco experiences a helpful support tool. The business gets, for nearly free, a running validation of whether the director persona and the oversight-value thesis are real — the cheapest de-risking of the whole bet.

## Features exercised

- **Customer-message → agent-draft pipeline** — retrieval-grounded reply drafting with hallucination controls.
- **Confidence badges** — plain-language high/moderate/low signal on every draft, a fixed governance control the agent cannot edit.
- **Posture-driven routing** — auto-send / approve-a-draft / compose-yourself, decided by the director's chosen posture (the R2 loop, live).
- **Approve / edit / rewrite oversight action** — the director's fifteen-second steering moment.
- **Learning-from-corrections** — the director's edited answer becomes attributed, timestamped company knowledge.
- **Daily digest** — oversight-at-scale summary that surfaces exceptions and newly-learned answers.
- **Append-only provenance trace** — every step recorded and attributed to a named human.
- **Persona-and-value instrumentation** — behavioral metrics on the proto-director and the oversight loop.

## Deliverables / artifacts produced

- **Approved customer replies** — real outcomes delivered through the director loop.
- A growing **learned-knowledge base** of human-corrected answers, each attributed and timestamped.
- A **provenance trace** per interaction (message → draft → approve/edit → send → learn), auditable to a named human.
- **Daily/weekly digests** — the oversight summary artifact.
- **Persona-validation metrics** — evidence on Bet 1 (does the director exist/buy?): approve-vs-edit-vs-rewrite rates, trust trajectory, willingness-to-pay signals.
- **Oversight-value metrics** — evidence on Bet 2: coverage growth from corrections, confidence calibration against real approvals, digest-vs-rubber-stamp behavior.

## Reuse → net-new

**Reuses (shipped substrate):** essentially the entire loop is already built and deployed against real users (`09-comms-wedge-mapping.md` §1, §4) — the RAG draft pipeline with hallucination checks, confidence badges, three-tier confidence routing, learning-from-human-answers, D/T/R audit rows, the daily digest, and schema-per-tenant isolation. This is the ~80% substrate the repivot leans on, live in production.

**Net-new:** the **instrumentation layer** that reframes the shipped loop as a _measured_ proto-director experiment — the persona and oversight-value metrics (Bets 1 and 2) that turn everyday usage into thesis validation. Also net-new is the conceptual reframing that lets this loop _generalize_: the same approve/edit/learn/trace shape, pointed at cross-system objectives beyond comms (the R1/R2 product).

## Why it matters (grounded)

The pitch names this loop as the reason "we can build this cheaply": _"a human already approves AI-drafted responses and the system learns from corrections — that human is a proto-director. We instrument that loop to validate the whole thesis cheaply"_ (`13-pitch.md` §5). The two bets it instruments are the honest, stated risks of the entire repivot — the director persona is "the single most speculative pillar," and "approval degrades to rubber-stamp at volume" is the strongest counter-argument to any oversight product (`12-saas-2.0-thesis.md` §3 SPECULATIVE, §6). This flow is how those risks get retired with live evidence instead of assertion (`13-pitch.md` §10–§11).
