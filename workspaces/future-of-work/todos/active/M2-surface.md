# M2 — Non-coder self-service surface / net-new build #1 (C3)

> **What this milestone proves.** A non-technical operator configures an objective's
> **process, connectors, posture, and knowledge with zero engineering** — no code, no engineer
> (capability roadmap §6 C3; architecture §2 L7 "Work Interface"). The agent **drafts the
> process artifacts from observed work**, the non-coder **describes and corrects** (§6.5
> non-coder-authoring-paradox mitigation), and the configured objective then runs. This is the
> escape from the documented 95%-of-pilots-fail mode (platform-overview §2; roadmap §6.1).
>
> **The pairing you must hold (load-bearing).** C3's falsifier is the "last 20% death" — the
> wizard handles ~90% of a real company process but needs an engineer for the final ~10%
> (roadmap §6.2, §6.4). That falsifier is **only neutralized by C5's rewind/transparency
> engine** (the M1 milestone): when the configured process runs, the user sees every step and
> can correct the un-configured 10% in-flight. **C3 alone is a wizard; C3+C5 is a wizard whose
> gaps are visible and correctable.** Several todos below are therefore PROVABLE only once C5
> exists — flagged per-todo in `Depends on`.
>
> **Reuse anchor (the ~80%).** The shipped comms onboarding wizard (a non-technical person
> configures channels in <10 minutes, no app — roadmap §6.1, §6.3) is the scaffold for the
> generalized surface; PACT's web objectives/approvals screens scaffold the approval surface
> (architecture §2.4). The bulk of net-new is the **surface UX**, sized by usability-walk
> milestones, not LOC (roadmap §6.6).
>
> **Acceptance discipline.** Every C3 surface todo's acceptance REQUIRES a **non-coder
> usability walk with receipts** per `.claude/rules/user-flow-validation.md` — a literal walk
> (invoke the surface, observe what the user sees, follow the next step), receipts embedded,
> scrubbed. A passing test next to a confusing walk is institutional theatre (the surface
> looking right is not the user succeeding).
>
> **Conventions.** Effort in autonomous execution cycles (`.claude/rules/autonomous-execution.md`),
> never human-days. Plain language, CLI-neutral (`.claude/rules/cross-cli-artifact-hygiene.md`),
> modern UI/UX for the surface. BUILD (the surface) and WIRE (to live connectors / objective
> execution) are SEPARATE todos so a beautiful surface with no live wiring is caught as the
> orphan it would be (`.claude/rules/orphan-detection.md`).

---

### M2-1 — DESIGN the non-coder configuration model and on-screen vocabulary

- **Type:** DESIGN
- **Implements:** specs/platform-overview.md §2 (OBJECTIVE/PROCESS/DATA), §6 (non-coder principle) (+ plan: 02-plans/01-architecture.md §2.1–§2.2 the three re-interfaces; 02-plans/02-capability-roadmap.md §6.1)
- **What:** Define the complete on-screen object vocabulary a non-coder configures an objective with — the intent box, business-object views (a purchase order, a ticket — NOT files), the connector-selection surface, the three-button posture chooser, the knowledge-and-roster config — and the plain-meaning → underlying-record mapping for each (so the user never sees the engine names). One screen-flow spec, no code.
- **Reuses → Builds:** comms onboarding wizard (the proven <10-min no-app config pattern) + PACT web objectives/approvals screens → the generalized configuration-model spec that turns "configure comms coverage" into "configure ANY objective."
- **Invariants:** non-coder-depth (no-code common case); config-as-artifact (the configured process is captured as artifacts + memory, NOT bespoke code); tenant-isolation (every per-customer config carries tenant_id).
- **Sizing:** ~1 cycle. Pure design; the on-screen vocabulary is the 3-sentence-describable contract every later surface shard consumes. Within the per-session budget (no load-bearing logic).
- **Depends on:** none. (This is the spec the BUILD shards consume; it does NOT itself need C5, but it MUST define the rewind/timeline view's place as a hook for the C5 pairing.)
- **Acceptance (confirm / falsify):** Confirm — a non-coder reading the screen-flow spec (read aloud, plain language) can say back, in their own words, what each of the five config surfaces is for and what "save" does. Falsify — any surface requires a technical term the spec does not translate on first use, OR the business-object view is described in file/folder terms (the developer mental model the brief explicitly inverts). Receipts: the read-back walk per `.claude/rules/user-flow-validation.md`.

---

### M2-2 — BUILD the intent box + live timeline shell (the non-coder front door)

- **Type:** BUILD
- **Implements:** specs/platform-overview.md §3 (the integration-layer inversion, agentic interface) (+ plan: 02-plans/01-architecture.md §2.2 row "intent surface"; user-flow 03-user-flows/01-objective-to-output.md §2 cast-of-objects, §3 Step 1)
- **What:** Build the plain "What do you want done?" intent box where a non-coder states an outcome in their own words, plus the live timeline shell that will render steps as they happen (rows of plain "what's happening now"). Surface only — the timeline renders a fixture stream in this shard; live wiring is M2-7.
- **Reuses → Builds:** comms channel adapters (email/chat-first surface, no separate app) → the generalized intent surface + the scrolling live-timeline component.
- **Invariants:** non-coder-depth (a plain box, no template/menu wall); config-as-artifact (the stated objective is captured as an objective record, not free text discarded); tenant-isolation.
- **Sizing:** ~1–2 cycles. Front-end component work with a live feedback loop (each rendered fixture row is testable), so it may run at the higher per-session budget. SHARD note: if the timeline-rendering logic (step grouping, status chips, budget bar) exceeds the surface budget, split the timeline component into its own shard.
- **Depends on:** M2-1.
- **Acceptance (confirm / falsify):** Confirm — a non-coder, in a usability walk, types an objective in their own words (not a template) and sees a coherent live timeline render against the fixture stream; receipts per `.claude/rules/user-flow-validation.md`. Falsify — the user reaches for a menu/template because the box doesn't accept plain language, OR the timeline rows are unreadable to a non-coder (jargon, raw IDs).

---

### M2-3 — BUILD the business-object views (records, not files)

- **Type:** BUILD
- **Implements:** specs/platform-overview.md §2 (DATA element — systems as endpoints, business objects as the unit) (+ plan: 02-plans/01-architecture.md §2.2 row "business-object/record model"; connectors-and-integration.md §2.3 the record-model decision)
- **What:** Build the non-coder views of business objects — a purchase order, a ticket, an opportunity — surfaced as records the user reads and acts on, NOT as files in a folder tree. The unit of work is a record in a system of record, never a file the user must understand as a developer would.
- **Reuses → Builds:** PACT web objectives/approvals screens (record-shaped surfaces) + comms wedge's account/contact/message record model → the generalized business-object view layer.
- **Invariants:** non-coder-depth (records, not a file system); tenant-isolation (every record view scoped to the customer's tenant_id); config-as-artifact (which object types a customer cares about is captured as config).
- **Sizing:** ~1–2 cycles. Surface work; live feedback loop against fixture records. SHARD note: per-object-type rendering is boilerplate-heavy (~5× the base budget before sharding triggers — one component stamped per object type); the object-type SELECTION/config logic is the small load-bearing part and stays in M2-1's model.
- **Depends on:** M2-1.
- **Acceptance (confirm / falsify):** Confirm — a non-coder usability walk: the user opens a purchase order / ticket, reads it, and acts on it without ever encountering a file/folder metaphor; receipts. Falsify — the user is asked to navigate files or interpret a record as a document path, re-acquiring the developer mental model.

---

### M2-4 — BUILD the three-button posture chooser (over the canonical 5-rung enum)

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §1.2 (three plain buttons → canonical posture mapping) (+ plan: 02-plans/02-capability-roadmap.md §6.3; user-flow 03-user-flows/01-objective-to-output.md §6 the three postures side by side)
- **What:** Build the per-objective posture chooser — three plain buttons "Go ahead" / "Ask me once" / "Step through with me" — presented over the canonical 5-rung trust posture enum kept internal (the user never sees `L5_DELEGATED`). The chooser is set BEFORE the objective runs; default new users to "Ask me once," let them opt up per-task.
- **Reuses → Builds:** the shipped EATP posture machinery (`PostureStateMachine`, `PostureStore`) + comms wedge escalation/confidence surfaces → the three-button presentation layer (surface only; the live enforcement wiring is the M1 governance milestone (capability C2), not this shard).
- **Invariants:** non-coder-depth (three buttons a non-coder can reason about, not five rungs); config-as-artifact (the chosen posture is captured per objective); tenant-isolation.
- **Sizing:** ~1 cycle. Small presentation layer over a shipped enum; live feedback loop. Within budget.
- **Depends on:** M2-1; AND M1-2/M1-3 (per-objective posture enforcement). (Note: the chooser SETS posture here; the between-agent-and-action ENFORCEMENT lives in the M1 governance work (capability C2) — this surface shard must not silently no-op the enforcement, see M2-7 wiring. The chooser is therefore NOT a standalone orphan: it is the front-end of M1's enforcement seam, and the wiring seam below depends on M1-2/M1-3 to make the chosen posture actually constrain the run.)
- **Acceptance (confirm / falsify):** Confirm — a non-coder usability walk: the user picks a posture for an objective, understands in plain words what each button means, and the choice is recorded against the objective; receipts. Falsify — the user cannot distinguish the three buttons in plain language, OR an engine rung name leaks to the surface.

---

### M2-5 — BUILD the connector-selection surface + knowledge-and-roster config

- **Type:** BUILD
- **Implements:** specs/connectors-and-integration.md §1 (connectors at the surface as a selection, not code) (+ plan: 02-plans/01-architecture.md §2.3 business-system connectors at the surface; artifact-system-and-registry.md §2 non-coder authoring for the knowledge side)
- **What:** Build the surface where a non-coder picks which systems to plug in ("connect my Gmail, my Salesforce, my company drive") from a list — no code, exactly the comms wizard's channel-selection pattern generalized — plus the knowledge config (point at the knowledge store) and the roster/approval config (who approves what). Surface/selection only; the live MCP wiring underneath is the M3 connector milestone.
- **Reuses → Builds:** comms onboarding wizard (channel-selection in <10 min, no app) + PACT approvals screens (roster/gate config) → the generalized connector-selection + knowledge + roster config surface.
- **Invariants:** non-coder-depth (pick from a list, never configure a connector by writing code); config-as-artifact (connector selections + knowledge pointers + roster captured as per-customer config artifacts); tenant-isolation.
- **Sizing:** ~1–2 cycles. Surface work, live feedback loop. SHARD note: the connector-PICKER UI is boilerplate-shaped; the least-privilege-envelope-derivation it feeds is load-bearing and lives in the M3 milestone (M3-4), NOT here — keep this shard selection-only.
- **Depends on:** M2-1.
- **Acceptance (confirm / falsify):** Confirm — a non-coder usability walk: the user selects systems to connect, points at their knowledge, and sets who approves what, entirely from lists/plain forms, no code; receipts. Falsify — any selection requires a config file, a code snippet, or an engineer; OR the surface exposes raw connector/scope internals a non-coder cannot reason about.

---

### M2-6 — BUILD the agent-drafts-from-observed-work + non-coder-corrects loop (the C3 sub-proof)

- **Type:** BUILD
- **Implements:** specs/artifact-system-and-registry.md §2.1 (generalized codify-from-observed-work loop), §2.2 (the change-review surface) (+ plan: 02-plans/02-capability-roadmap.md §6.5 the non-coder-authoring-paradox mitigation; user-flow 04-artifact-authoring-sharing.md §2.2–§2.3)
- **What:** Build the loop where the platform watches a completed piece of work, **drafts the process artifacts** (a command for the procedure + a rule for the boundary) from the observed steps and the user's plain-language description, and surfaces them in a **plain-language change-review screen** where the non-coder describes-and-corrects. The agent encodes; the human approves. This is the direct mitigation of the non-coder-authoring-paradox (artifacts are otherwise authored by developer-adjacent people).
- **Reuses → Builds:** the shipped codify-from-observed-work loop (today captures code-session signals) + the comms wedge's learning-from-human-answers loop → the generalized process-artifact draft + the non-coder plain-language change-review/edit surface (NOT a Git diff).
- **Invariants:** non-coder-depth (review/edit in plain-language steps and rules, never code/Markdown/Git); config-as-artifact (the corrected process IS the captured artifact); agent-as-producer-never-authority (a human approves before anything enters the catalog); tenant-isolation.
- **Sizing:** ~2 cycles. The draft-generation has a live feedback loop (each drafted artifact is testable against a fixture session); the plain-language review surface is the larger net-new UX. SHARD note: split the DRAFT-from-observed-work generation (load-bearing, the codify generalization) from the change-review SURFACE (UX) if the pair exceeds the budget — they are separate concerns.
- **Depends on:** M2-1, M2-3 (the change-review screen reuses the business-object view layer). PAIRED with C5: the falsifier below ("agent encodes a plausible-but-wrong process the non-coder cannot detect") is only fully neutralized once C5's transparency lets the non-coder verify the encoding by WATCHING it run — so this todo's depth-falsifier is not closed until the M1/C5 rewind engine exists.
- **Acceptance (confirm / falsify):** Confirm — a non-coder usability walk: the user does a piece of work once, the platform proposes a command + rule in plain language, the user corrects one step and approves, and the corrected artifact is stored with provenance; receipts per `.claude/rules/user-flow-validation.md`. Falsify — the agent encodes a plausible-but-WRONG process the non-coder cannot detect from the review screen alone (the paradox's falsifier — coupling to the legibility bet), OR the review surface forces the user into code/Markdown/Git.

---

### M2-7 — WIRE the configuration surface to live connectors + live objective execution

- **Type:** WIRE
- **Implements:** specs/platform-overview.md §3 (the configured objective runs end-to-end) (+ plan: 02-plans/02-capability-roadmap.md §6.2 "the configured objective then runs"; 02-plans/01-architecture.md §9 one-objective-end-to-end)
- **What:** Wire the BUILT surfaces (M2-2 intent box + timeline, M2-4 posture, M2-5 connector selection, M2-6 captured process) to live objective execution — so a non-coder's configured objective actually RUNS against live connectors, with the live timeline streaming real steps (not a fixture). This is the orphan-detection gate: the surface is only proven when it drives real execution on the hot path.
- **Reuses → Builds:** the runtime objective-execution loop + the M3-milestone connector wiring + C2 governance enforcement → the wiring that turns the configured objective into a live run on the actual surface.
- **Invariants:** config-as-artifact (the live run consumes the captured config, not a re-entered one); tenant-isolation (live connector calls + timeline scoped to tenant_id); non-coder-depth (the run requires no engineer to launch); no-orphan (a real call site from the surface into objective execution + a Tier-2 test proving the framework calls it — `.claude/rules/orphan-detection.md`).
- **Sizing:** ~1–2 cycles. Integration wiring with a live feedback loop (each wired surface is testable end-to-end against real infra). SHARD note: wire one surface at a time (intent→run, then posture→enforcement, then connector-selection→live-MCP) — each carries the no-orphan invariant set (call site + Tier-2 test) and shards separately per `.claude/rules/orphan-detection.md`.
- **Depends on:** M2-2, M2-4, M2-5, M2-6; AND the M1 governance milestone (capability C2 — the posture ENFORCEMENT between agent and action that the M2-4 chooser feeds, via M1-2/M1-3); AND the M3 milestone (live connectors + between-agent-and-connector governance) — C4 reuses M1 governance as the between-agent-and-connector enforcement, so this wiring consumes M3's governed connectors AND M1's posture enforcement. The full end-to-end demo (a non-coder configures and the objective runs across systems, traced and rewindable) is only complete once C5 (rewind) AND M3 (≥2-system reach) land.
- **Acceptance (confirm / falsify):** Confirm — a non-coder, in a usability walk, configures a brand-new objective end-to-end (systems, process, posture, knowledge) and it RUNS against live connectors with the live timeline streaming real steps — no engineer touched it; receipts per `.claude/rules/user-flow-validation.md`, plus a Tier-2 test proving the framework calls into objective execution from the surface. Falsify — the configured objective needs a code change or an engineer to actually run (the orphan failure: surface built, never wired), OR the live run silently diverges from the captured config.
