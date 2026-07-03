# R4 — Oversee & Intervene: Rewind, Change, Re-run Only What's Affected

> Value principles embodied: P4 (meaningful oversight at scale, not rubber-stamp), P7 (undo + trace = the trust surface). Also grounds P2 (director, not builder — you can only safely consume work you didn't build if you can see and correct it). Wedge: mid-market / SMB departmental edge; proven first on the comms lighthouse's 4-step flow. Follows directly from R3 — R4 operates on the trace R3 produced.

## The walk (from the director's screen)

The director is **Dana** again, the accounts-receivable manager from R3. Her agent has just finished a slightly bigger job: a **quarterly receivables report** built by fanning out across three sub-tasks — one for _overdue balances_ (read from the ledger), one for _cash collected this quarter_ (read from the ledger), and one for _customer contact status_ (read from email history). The three were assembled into a single report. Dana chose "Ask me once," approved the plan, and the report is done. Now she reviews it — and this is where oversight becomes _real_ rather than a rubber stamp.

**1. Dana reviews the trace and spots a wrong step.**
Reading the report's overdue-balances section, something looks off. Dana opens the glass-box timeline from R3 and walks back through the _overdue_ sub-task. Two steps back, she sees exactly what the agent did:

- It read the ledger for balances past due.
- It applied a **cut-off date of "past 30 days."**
- But her company's policy for this report is **"past 45 days"** — the agent used the wrong threshold, so a batch of 31-to-44-day invoices got counted as overdue when they shouldn't be.

Because every step recorded _what went in and what came out_ in plain language, Dana can _see_ the mistake — she didn't have to guess or reverse-engineer a wrong number. This is the whole reason the glass box exists: it makes a non-coder's correction _possible_.

**2. Dana rewinds to that step and changes one input.**
She clicks **"rewind to here"** on the "apply cut-off" step. Sequor shows her that step's recorded inputs, the decision it made, and the output it produced. She changes the single input that was wrong: **30 → 45 days.** She changes nothing else.

Behind the scenes, this does _not_ overwrite anything. The original step and its output are kept, untouched, as **version 1**. Her edit creates a _new_ version of that step. Nothing is destroyed — the old report still exists exactly as it was.

**3. The engine works out what genuinely needs to re-run — and shows a cost-preview first.**
This is the part that makes the feature usable instead of terrifying. Sequor does _not_ blindly redo the whole report. It traces which parts of the work actually _depended_ on the thing Dana changed, and it re-runs **only those** — leaving everything else exactly as recorded. Before it commits to anything, it shows Dana a **preview** of what her change will cost:

> Your change to the cut-off date affects:
>
> - the **overdue-balances** sub-task (re-runs — its input changed)
> - the **final assembled report** (re-runs — it uses the overdue numbers)
>
> Your change does **not** affect:
>
> - the **cash-collected** sub-task (kept as-is — it never used the cut-off date)
> - the **customer-contact** sub-task (kept as-is — it never used the cut-off date)
>
> Estimated: 2 steps re-run, ~30 seconds, small cost. Proceed?

Two of the three sub-tasks are left completely alone. The system knows they're unaffected because their recorded inputs didn't change — a fingerprint of each step's inputs matches what it was before, so re-running them would produce identical output, and the engine skips them. Dana sees, in plain language and _before committing_, exactly how far her one edit ripples. No surprise bill, no accidental redo of an hour of work.

**4. Dana makes the explicit per-step choice: re-run with my edit, or keep the recorded output.**
For the steps that _are_ affected, Sequor asks a clear question rather than guessing:

- For the **overdue-balances** step — the one whose input she actually changed — she chooses **"re-run with my edit (get a fresh result)."** She _wants_ new numbers here; that's the whole point.
- For a downstream **narrative-summary** step that merely re-phrases the numbers, she's offered the same choice. She could keep the recorded wording and just let the numbers flow through, or regenerate the prose. She picks re-run so the summary reflects the corrected figures.

Why ask at all? Because the agent runs on a language model, and re-running a language-model step can legitimately produce a _different_ answer — sometimes correct but surprising ("I only changed the date and the summary's whole tone shifted"). Guessing silently would be the worst outcome. So the choice is Dana's, made explicitly, step by step, where it matters. For every step she _didn't_ touch and _doesn't_ choose to regenerate, Sequor reuses the exact recorded output — predictable and free.

**5. The re-run happens; a clean new version is produced; the old one survives.**
The overdue sub-task and the final report re-run with 45 days. The result is saved as **version 2** of the report, with a pointer back to version 1. Dana can:

- **Compare** version 1 and version 2 side by side — see precisely what changed (fewer invoices flagged overdue, corrected totals) and what didn't.
- **Revert** to version 1 if she decides she preferred it — because it was never destroyed, going back is instant and lossless.

**6. The intervention itself is audited.**
Dana's correction is not a silent edit. Sequor records a permanent line: _"Dana changed the overdue cut-off from 30 to 45 days at this step, at this time; re-ran the overdue sub-task and the final report; kept the cash and contact sub-tasks; produced report v2 from v1."_ If anyone later asks why the Q-report changed between Monday and Tuesday, the answer is in the record — with Dana's name on it. Oversight that leaves a trace is oversight that _counts_.

**Honest about the v1 limits (stated, not hidden):**

- **Linear retrace only — no branching yet.** In this first version Dana can rewind and change _the main line_ of work; she cannot spin up two side-by-side "what-if" versions and compare them as parallel branches. If she wants to explore an alternative, she does it one at a time: change, look, and revert if she doesn't like it. The kept-version history is her safety net — nothing is lost — but it is a _sequence_, not a set of parallel branches. Branching is deliberately deferred because "compare two diverging timelines" is a concept even programmers find hard, and shipping it to a non-coder before the simple case is proven would be the fastest way to lose her. It's the first thing added once the linear experience is validated with real users.
- **A re-run of a model step may differ in ways that surprise a non-coder.** The product's obligation is to _show what changed and why_ between versions — not to pretend re-runs are deterministic. Making "correct but surprising" legible is an ongoing UX responsibility, not a solved problem.
- **The per-step "re-run vs keep" choice is a genuine conceptual load.** It's the honest price of not guessing wrong silently. If users find it confusing, that's a signal to refine the surface — this flow is the first cut, and real-use feedback is expected to reshape it.
- **A change near the _root_ of the work legitimately re-runs a lot.** The cost-preview exists precisely so a big cascade is a _choice the director sees and confirms_, never a surprise. Content-fingerprinting bounds the _unnecessary_ re-runs; it cannot shrink a genuinely wide change — it can only make its size visible before Dana commits.

## Features exercised

- **Glass-box trace review** — the plain-language, step-by-step record from R3, walkable by a non-coder.
- **Rewind-to-any-step** — select a past step, see its recorded inputs / decision / output, and edit one input.
- **Immutable versioning** — an edit appends a new version; the original step and output are never overwritten.
- **Dependency-aware cascade (reactive re-execution)** — the engine re-runs only the steps that genuinely depended on the change.
- **Fingerprint-skip ("only affected downstream")** — steps whose inputs didn't actually change are recognized as identical and skipped, halting the ripple early.
- **Cost-preview before commit** — a plain-language preview of what will re-run, what won't, and the estimated cost/time, shown _before_ anything executes.
- **Explicit per-step "re-run with my edit / keep the recorded output" choice** — the director decides, per step, rather than the system guessing.
- **Version compare + lossless revert** — side-by-side v1 vs v2, and instant return to a prior version.
- **Intervention audit record** — who rewound, what they changed, when, and what re-ran — a permanent, named entry.

## Deliverables / artifacts produced

- **Version 2 of the work** — the corrected report, with a back-pointer to version 1; both survive.
- **Cost-preview record** — the pre-commit estimate of affected steps and cost the director saw and approved.
- **Intervention audit record** — the permanent, named entry documenting the rewind, the changed input, the re-run scope, and the version transition.
- **Updated provenance trace (v1 substrate, extended)** — the same immutable ledger from R3, now carrying the new step-version, the skipped-vs-re-run decisions, and the intervention event, all inspectable and replayable.
- **A comparison view** — the concrete diff between version 1 and version 2 the director can read (what changed, what didn't).

## Reuse → net-new

**Shipped substrate reused:**

- **PACT records** — the versioned outputs ride `AgenticArtifact` (which already carries `content_hash` + `version` + `parent_artifact_id` — the immutable version chain is _already_ modeled); the dependency edges the cascade walks are the existing `AgenticRequest.depends_on` set; the intervention lands as an immutable `AuditEntry`.
- **Kailash durable store + `WorkflowDAG` + memoization** — `WorkflowDAG.descendants()` finds what's downstream; the content-fingerprint skip generalizes the same "skip completed, reuse cached" logic Kailash already runs inside a single run (crash-recovery, idempotency) — lifted from "within one run" to "across runs."
- **`ExecutionMetric` history** — the cost-preview estimate is read from the historical cost/latency the platform already records.
- **MCP connectors** — re-runs that touch a system go back through the same governed connectors from R3, under the same envelope.

**Net-new (the concentrated core):**

- **The reactive cascade engine** — dirty-marking downstream + fingerprint-skip + version-on-re-run, with the reuse-recorded-vs-regenerate policy for non-deterministic model steps. This is _the_ genuinely new component (the ~5% the whole platform is built to enable).
- **The director timeline UI** — the rewind surface, the cost-preview, the per-step choice, and the version-compare view, all rendered for a non-coder (the open design frontier).

## Why it matters (grounded)

This is what makes "director, not builder" (P2) actually work: consuming work you did _not_ build is impossible to trust without the ability to _see it, correct it, and keep the old version_ — the pitch's P7. It is also the direct answer to the strongest counter-argument against any oversight product — that approval degrades into rubber-stamp bulk-accept at volume (P4). Meaningful steering means the director can reach into a specific wrong step, fix it, and have _only the affected work_ recompute — not re-approve a wall of output. The engine is the tractable, mostly-reused part; the honest frontier is legibility for non-coders, which is why v1 deliberately ships the immutable-version safety net _without_ the confusing branch-and-compare surface. Proven first on the comms lighthouse's 4-step flow — where a human correcting an AI-drafted response _already_ logs a correction as a new version — it validates the whole thesis at low stakes before generalizing.
