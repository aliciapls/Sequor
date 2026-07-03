# M8 — Testing Infrastructure (cross-cutting)

> **What this milestone builds (plain language).** The shared way the whole platform proves it works:
> a three-tier test harness, the real-infrastructure fixtures every feature test runs against (the
> live Neon Postgres database and the durable store), the **probe-driven** verification harness that
> judges the platform's _meaning-bearing_ behaviors (did the agent's classifier reach the right
> verdict? is a recommendation/refusal good quality? can a non-coder actually read the trace?) — NOT
> by scanning for keywords, and the one end-to-end regression test that runs the capability-proven
> demo walk exactly as the docs teach it. Plus the regression suite and the CI matrix that runs all of
> it on every change.
>
> **Scope boundary (important).** The per-component wiring tests — the Tier-2 test that proves the
> governance manager is actually called on the hot path (M1), the cascade-engine fixture-graph tests
> (M4), the connector tests (M3), the surface walk segments (M2) — live INSIDE their own feature
> milestones, per the build/wire/test discipline. M8 does NOT duplicate them. M8 builds the
> **cross-cutting infrastructure** those per-component tests stand on: the harness itself, the
> real-infra fixtures, the probe machinery, the docs-exact end-to-end regression, and the CI matrix.
> Where a per-component test exists, M8 references it rather than re-authoring it.
>
> **Two framing rules carried throughout** (roadmap §1): (1) a capability is "proven" only against
> **real infrastructure and a real user-facing walk** — a passing unit test in isolation is necessary
> but insufficient (per `rules/testing.md` Tier 2/3 and `rules/user-flow-validation.md`); (2) any
> assertion about a _semantic_ property of system output MUST be **probe-driven**, never regex/keyword
> (per `rules/probe-driven-verification.md`). These two rules are the spine of this milestone.

---

## Dependency posture for this milestone

- **M8 is cross-cutting and spans the whole build.** The harness and the real-infra fixtures are
  needed from the first feature milestone onward; the probe harness is needed wherever a semantic
  assertion is made (governance classifier verdict, recommendation/refusal quality, non-coder
  legibility); the docs-exact end-to-end regression can only run once the capability-demo composition
  (M7) exists. So M8's todos land incrementally alongside the feature milestones, not in a single late
  block.
- **M8 builds infrastructure, it does not re-test components.** The per-component Tier-2 wiring tests
  are owned by M1–M7. M8 owns: the 3-tier harness shape, the shared real-infra fixtures those tests
  consume, the probe verification layer, the end-to-end docs-exact regression, the regression suite
  convention, and the CI matrix that runs everything.
- **Probe-driven is non-negotiable for semantic claims.** The platform is LLM-first: the
  consequentiality classifier, the recommendation/refusal quality, the non-coder legibility checks are
  all _meaning_ judgments. Verifying them with regex/keyword answers the wrong question (did a string
  appear) instead of the right one (did the system perform the behavior). The probe harness is the
  structural defense.

---

### M8-1 — Stand up the 3-tier test harness shape (Tier 1 unit / Tier 2 integration / Tier 3 e2e)

- **Type:** BUILD
- **Implements:** specs/platform-overview.md §reuse-vs-new (+ `rules/testing.md` § 3-Tier Testing; roadmap §1 proof discipline)
- **What:** Build the shared harness scaffolding that sorts every test into Tier 1 (unit, mocking
  allowed, fast), Tier 2 (integration, real infrastructure, NO mocking), and Tier 3 (end-to-end, real
  everything, every write verified by read-back). Define the markers, the directory layout, and the
  conftest/fixture wiring so a feature milestone's per-component test drops into the right tier without
  re-inventing the plumbing.
- **Reuses → Builds:** the Kailash 3-tier testing conventions + the comms wedge's existing test suite
  shape → the platform-wide harness scaffold (tier markers, directory layout, shared conftest).
- **Invariants:** Tier-2/3 use real infra, NO mocking (`@patch`/`MagicMock`/`unittest.mock` BLOCKED in
  Tier 2/3); Tier-1 stays offline + fast; tests isolated (clean setup/teardown, no cross-test state);
  deterministic (seeded randomness, no time-dependent assertions).
- **Sizing:** ~1 cycle.
- **Depends on:** none (foundational; lands first so feature milestones inherit it).
- **Acceptance (confirm / falsify):** **Confirm:** a new feature test can be placed in any tier and
  picks up the shared fixtures + markers with no per-test plumbing; `pytest --collect-only` enumerates
  all three tiers. **Falsify:** a Tier-2 test silently runs against a mock (the harness does not block
  mocking in Tier 2/3), OR tiers leak fixtures across the boundary (a Tier-1 stub reaches Tier-2).

### M8-2 — Real-infra Tier-2/3 fixtures: live Neon Postgres + the durable provenance store

- **Type:** BUILD
- **Implements:** specs/transparency-and-provenance.md §2.5 (ledger source of truth) + specs/data-model.md §Multi-Tenancy (+ `rules/testing.md` Tier 2/3, NO mocking; comms-wedge plan §0 Vercel+Neon)
- **What:** Build the shared Tier-2/3 fixtures that bring up the _real_ backing stores every
  integration test needs — a live Neon Postgres database (the deployed comms product's database
  technology) and the durable provenance store (the Kailash durable store the ledger persists into) —
  with per-test schema isolation so concurrent tests do not collide, and teardown that yields + cleans
  up (never returns without cleanup).
- **Reuses → Builds:** the comms product's Vercel + Neon Postgres deploy + the Kailash durable store
  (`DBCheckpointStore` / `StoreFactory`) → shared real-infra fixtures the platform's Tier-2/3 tests
  consume.
- **Invariants:** Tier-2/3 = real infra, NO mocking; every fixture is tenant-scoped (schema-per-tenant,
  matching the shipped comms isolation) so a test cannot read another tenant's rows; fixtures yield +
  cleanup (never return, no resource leak); every write verified with a read-back per State Persistence
  Verification.
- **Sizing:** ~1–2 cycles (+ SHARD if the Neon fixture and the durable-store fixture diverge in setup
  complexity — shard one store per session).
- **Depends on:** M8-1.
- **Acceptance (confirm / falsify):** **Confirm:** a Tier-2 test runs against a real Neon Postgres
  schema + the real durable store, two concurrent tests do not collide (schema isolation holds), and a
  write is verified by a subsequent read-back. **Falsify:** a test passes against an in-memory
  substitute (real infra not actually exercised), OR concurrent tests cross-contaminate (tenant/schema
  isolation broken in the fixture), OR a fixture leaks a connection at teardown (`ResourceWarning`).

### M8-3 — Probe-driven verification harness: the LLM-first classifier verdict

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §LLM-first-classifier + specs/transparency-and-provenance.md §5 (`plan_proposed`) (+ `rules/probe-driven-verification.md` MUST-1/2; `rules/agent-reasoning.md`; CLAUDE.md Directive 6)
- **What:** Build the probe (a structured query with a defined expected-answer schema and a
  deterministic scoring rule) that judges whether the platform's LLM-first consequentiality classifier
  reached the _right verdict_ ("is this action consequential? auto / flag / HELD / block") — asking the
  behavior directly, NOT scanning the response for keywords like `write`/`send`/`delete`. The probe
  uses an LLM-as-judge with JSON-schema output (or a domain oracle), never a regex over prose.
- **Reuses → Builds:** the probe-driven-verification runbook (`skills/12-testing-strategies`) + an
  LLM-judge harness → the classifier-verdict probe with its expected-answer schema + scoring rule.
- **Invariants:** semantic verification = probe-driven, NOT regex/keyword (regex for a semantic claim
  is BLOCKED); every probe carries an expected-answer schema (free-text answers BLOCKED); the probe is
  the authoritative gate-review verdict, paired with any advisory lexical hook (a lexical hook alone is
  BLOCKED); no probe-unavailable regex fallback (structural-or-skip, never regex-best-effort).
- **Sizing:** ~1 cycle.
- **Depends on:** M8-1; the classifier exists in M1 (governance) — the probe judges it.
- **Acceptance (confirm / falsify):** **Confirm:** a probe (not a regex) scores the classifier's
  verdict against a JSON-schema answer with a deterministic rule, and correctly distinguishes "agent
  judged this consequential and HELD it" from "agent never classified it." **Falsify:** the verdict is
  scored by keyword presence (e.g. matches `recommend`/`send`), so it passes on "I cannot recommend"
  — the exact semantic blindness the rule blocks.

### M8-4 — Probe-driven harness: recommendation / refusal quality

- **Type:** BUILD
- **Implements:** specs/platform-overview.md §6 (non-coder principle) (+ `rules/recommendation-quality.md`; `rules/probe-driven-verification.md` MUST-2; `rules/communication.md`)
- **What:** Build the probe that judges the _quality_ of the platform's recommendations and refusals
  surfaced to the non-coder — does a recommendation carry a pick + implications + symmetric pros/cons in
  plain language? does a refusal cite the governing reason and hold the line? — using a schema-bound
  LLM-judge, not a keyword scan. This is what keeps "recommend, don't menu" and "refuse cleanly"
  honestly measured rather than asserted.
- **Reuses → Builds:** the probe harness (M8-3) + the recommendation-quality + communication rule
  contracts → the recommendation/refusal-quality probe with schema + scoring.
- **Invariants:** semantic verification = probe-driven, NOT regex/keyword; expected-answer schema on
  every probe (fields: `has_pick`, `implications_present`, `cons_stated`, `plain_language`); no
  sentiment/"sounds concerned" free-text judging; structural sub-checks (e.g. option-marker count) may
  stay deterministic but the quality judgment is the probe.
- **Sizing:** ~1 cycle.
- **Depends on:** M8-3.
- **Acceptance (confirm / falsify):** **Confirm:** a probe scores a recommendation as pass only when it
  carries a pick, implications, honest cons, and plain language — and fails a bare option-menu even
  though the menu contains the option words. **Falsify:** the check passes whenever
  `I recommend`/`Option` strings appear regardless of whether a pick + cons + plain-language were
  actually present (regex through the back door).

### M8-5 — Probe-driven harness: non-coder legibility checks

- **Type:** BUILD
- **Implements:** specs/transparency-and-provenance.md §7 #1 (non-coder versioning UX, dominant risk) + specs/intervention-and-versioning.md §6 (+ `rules/probe-driven-verification.md`; `rules/user-flow-validation.md`)
- **What:** Build the probe that judges whether a non-coder can _read the glass-box trace and the
  version history_ — "which version of this output is current?", "what did this step consume and
  produce?", "what will this rewind re-run?" — answered correctly within seconds, from the surface a
  non-coder actually sees. This is the legibility frontier (the dominant open unknown); the probe makes
  it measurable rather than asserted. The probe judges comprehension, not string presence.
- **Reuses → Builds:** the probe harness (M8-3) + the user-flow-validation walk discipline → the
  legibility probe (structured comprehension questions + expected-answer schema + scoring) layered over
  the actual non-coder surface.
- **Invariants:** semantic verification = probe-driven, NOT regex/keyword; the probe runs against the
  literal user-facing surface (not a substitute path) per `user-flow-validation.md`; expected-answer
  schema on every comprehension question; receipts (verbatim question + observed answer + disposition)
  scrubbed before embedding in any public-surface artifact.
- **Sizing:** ~1 cycle.
- **Depends on:** M8-3; the rewind/version UI exists in M2/M4 — the probe judges its legibility.
- **Acceptance (confirm / falsify):** **Confirm:** a probe (not a regex) scores whether a non-coder
  answered "which version is current?" / "what will this rewind re-run?" correctly from the real
  surface, with receipts. **Falsify:** legibility is "verified" by checking the page contains the word
  "version" (string presence), OR the check runs against a developer view instead of the non-coder
  surface (substitute path).

### M8-6 — Docs-exact end-to-end pipeline regression for the capability-proven demo walk

- **Type:** TEST
- **Implements:** specs/platform-overview.md §3.3 (six-property acceptance test) + §capability-proof (+ `rules/testing.md` § End-to-End Pipeline Regression; roadmap §12; M7 milestone)
- **What:** Build the single Tier-2+ regression test that executes the capability-proven demo walk
  EXACTLY as the docs/runbook teach it (objective → posture → plan-gate → two-system execution → live
  trace → rewind + re-cascade → versioned) against real infrastructure, asserting the final
  user-visible outcome at each handoff — so a field MISSING from an A→B handoff (the failure no
  per-primitive test can see) is caught. Lives in the regression suite, grep-able by name.
- **Reuses → Builds:** the M7 composed demo segments + the real-infra fixtures (M8-2) → the docs-exact
  end-to-end regression test.
- **Invariants:** Tier-2/3 = real infra, NO mocking; the test runs the DOCS-EXACT walk (not a
  hand-tuned variant); every write verified with read-back; all six ledger invariants hold across the
  composed path; semantic assertions in the walk (e.g. the classifier verdict, legibility) reuse the
  M8-3/4/5 probes, not regex.
- **Sizing:** ~1 cycle.
- **Depends on:** M8-2, M8-3, M8-4, M8-5; the M7 composition must exist to run end-to-end.
- **Acceptance (confirm / falsify):** **Confirm:** the docs-exact demo regression runs green on real
  infrastructure end-to-end, asserting the user-visible outcome at each handoff (no field silently
  dropped). **Falsify:** the regression passes per-primitive but the composed handoff drops a field
  (the A→B contract breaks and only the end-to-end test would have caught it), OR the test is a
  hand-tuned variant that does not match the docs the user follows.

### M8-7 — The regression suite + CI matrix that runs every tier on every change

- **Type:** BUILD
- **Implements:** specs/platform-overview.md §reuse-vs-new (+ `rules/testing.md` § Regression Testing + Test-Once Protocol; `rules/git.md` § Branch Protection)
- **What:** Build the regression-suite convention (every bug fix lands a behavioral regression test in
  `tests/regression/`, never deleted) and the CI matrix that runs Tier-1 on every push, Tier-2/3
  against real infra as the merge gate, and the docs-exact end-to-end regression (M8-6) as the final
  gate — so no change reaches the release branch without the full matrix passing. Numerical claims in
  the suite (test counts, coverage) are produced by a verifying command, not hand-typed.
- **Reuses → Builds:** the existing CI + the platform's tiered harness (M8-1) + real-infra fixtures
  (M8-2) → the regression suite convention + the CI matrix wiring.
- **Invariants:** every bug fix carries a behavioral regression test (source-grep-as-sole-assertion
  BLOCKED); regression tests never deleted; Tier-2/3 real infra in CI, NO mocking; merge gate blocks on
  the full matrix (direct push to main rejected); numerical claims verified by command, not recalled.
- **Sizing:** ~1 cycle.
- **Depends on:** M8-1, M8-2, M8-6.
- **Acceptance (confirm / falsify):** **Confirm:** the CI matrix runs Tier-1 + Tier-2/3 (real infra) +
  the docs-exact end-to-end regression on every change, and a merge is blocked when any tier fails.
  **Falsify:** a change merges with a tier skipped or run against mocks, OR a regression test for a
  past bug was deleted in a later refactor (the bug class re-opens silently).

### M8-8 — Docs-exact end-to-end regression for the SHIPPED comms-wedge flows (merge gate)

- **Type:** TEST
- **Implements:** specs/message-routing.md + specs/rag-pipeline.md + specs/response-accuracy.md + specs/channel-coordination.md (+ `rules/testing.md` § End-to-End Pipeline Regression; roadmap §0 Decision A — comms is the revenue-bearing wedge that must keep running)
- **What:** Build the Tier-2+ regression test that exercises the LIVE comms product's end-to-end flow
  EXACTLY as its shipped docs teach it — message arrives → consequentiality/intent classification → RAG
  retrieval → response drafting → HITL escalation when the confidence gate trips — against real
  infrastructure, asserting the user-visible outcome at each handoff. This is the **merge gate that
  protects the shipped, revenue-bearing comms product**: platform work (governance wiring, the cascade
  engine, connector curation) MUST NOT silently regress the comms flows people are paying for today
  (Decision A: comms is a wedge that must keep running, not a throwaway demo). Lives in the regression
  suite, grep-able by name. **Distinct from M8-6** — M8-6 regresses the platform-capability demo walk
  (objective → posture → plan-gate → two-system execution → rewind → version); M8-8 regresses the
  already-shipped comms-wedge pipeline (message → classification → RAG → response → escalation). Both
  are merge gates; they cover different products.
- **Reuses → Builds:** the comms product's shipped flows + the four comms specs (message-routing,
  rag-pipeline, response-accuracy, channel-coordination) + the real-infra fixtures (M8-2) → the
  docs-exact comms-wedge end-to-end regression.
- **Invariants:** Tier-2/3 = real infra, NO mocking; the test runs the DOCS-EXACT shipped comms flow
  (not a hand-tuned variant); every write verified with read-back; tenant isolation holds on every
  comms read/write; semantic assertions in the flow (the classifier's intent/consequentiality verdict,
  response/refusal quality) reuse the M8-3/M8-4 probes, not regex.
- **Sizing:** ~1 cycle.
- **Depends on:** M8-2, M8-3, M8-4; the shipped comms product (already deployed).
- **Acceptance (confirm / falsify):** **Confirm:** the docs-exact comms-wedge regression runs green on
  real infrastructure end-to-end (message → classification → RAG → response → escalation), asserts the
  user-visible outcome at each handoff, and is wired as a merge gate so a platform change that breaks a
  live comms flow is blocked before it reaches main. **Falsify:** platform work merges while a shipped
  comms flow is silently broken (the revenue-bearing product regressed with no gate firing — the exact
  failure Decision A's "comms must keep running" forbids), OR the test is a hand-tuned variant that
  does not match the docs the comms users follow.

---

## Milestone-level acceptance

The testing infrastructure is **proven** when: the 3-tier harness exists and feature milestones drop
their per-component tests into it without re-plumbing; Tier-2/3 fixtures bring up real Neon Postgres +
the durable store with tenant isolation and read-back verification; the platform's three classes of
semantic assertion (classifier verdict, recommendation/refusal quality, non-coder legibility) are each
judged by a **probe with a schema, not a regex**; the docs-exact capability-demo regression (M8-6) runs
green on real infrastructure end-to-end; the docs-exact SHIPPED-comms-wedge regression (M8-8) runs green
as a merge gate so platform work cannot silently regress the revenue-bearing comms product (Decision A);
and the CI matrix runs every tier on every change as a blocking merge gate. The per-component wiring
tests remain owned by M1–M7 — M8 is the shared ground they stand on, not a duplicate of them.
