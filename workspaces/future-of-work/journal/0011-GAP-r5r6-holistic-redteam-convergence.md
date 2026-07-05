---
type: GAP
slug: r5r6-holistic-redteam-convergence
date: 2026-07-05
round: R5/R6 (holistic post-multi-wave)
---

# R5/R6 Holistic Redteam — Convergence + Surfaced Gaps

## What happened

Holistic post-multi-wave `/redteam` across the union of R1–R4 comms-wedge fixes. 4 parallel
auditors (spec-parity, security, correctness, test-coverage) re-derived every check from
scratch; R6 adversarially confirmed the R5 delta. **CONVERGED: defect surface 0 CRITICAL /
0 HIGH un-logged; all R1–R4 fixes independently verified holding; 2 consecutive clean rounds.**

The prior rounds' fixes were genuine, not self-report theatre — the auth-bypass pin, fail-closed
encryption default, upload bounds, rate-limiter fail-closed, DNS hardening, and the hallucination
math were all confirmed present + correct in HEAD.

## Gaps the prior 4 rounds missed (all now closed or logged)

**RISK — R5-01 (MED): unauthenticated onboarding document ingestion.** `POST /api/v1/onboarding/upload`
takes `tenant_id`/`account_id` as form fields with no auth/ownership proof → RAG-poisoning vector.
Mitigated by unguessable 122-bit tenant UUID + FK-must-preexist + rate limit. Logged (DEVIATIONS
R5-01); disposition is a flow decision (gate behind a short-lived onboarding token).

**GAP — spec claimed shipped behavior that does not exist (spec-accuracy Rule 1/5):**

- F1 — `rag-pipeline.md` claimed "File is scanned for malware (ClamAV or equivalent)"; no scan in code.
- **F2 (HIGH, compliance) — `data-model.md` claimed retention "enforced via a nightly batch job that
  purges records"; no purge job exists → PDPA over-retention exposure.** Highest-priority new item.
- F3 — `message-routing.md` claimed the routing flywheel is "architected from day 1"; `RoutingOutcome`
  model exists but nothing writes it, and `RoutingThresholdConfig`/`RoutingOutcomeAggregate` have no class.
  All three false "shipped" claims softened to DEVIATIONS deviation-pointers; the features logged as
  F5-gated builds.

**GAP — regression-test accretion (testing.md: behavioral over source-grep):**

- G2/G3 — the R2 keyphrase NameError fix and the R1 500-handler traceback-leak fix had been closed by
  source-sweeps only; added behavioral regression tests.
- Suite-hang — `test_email_retry::test_raises_after_all_retries_exhausted` read backoff at send-time
  (outside the settings patch) and slept on the real default (~35 min), hanging the suite; patched the
  wall-clock sleep (suite now ~2s). A time-dependent Tier-1 test (testing.md violation).

**GAP — spec self-consistency the R3 banner over-claimed as applied:** CS-5 (template count 5→6),
CS-6 (Free-tier retention row), dangling NEW-8. All reconciled.

## Why this matters

The holistic re-derivation caught what per-shard rounds structurally cannot: false affirmative spec
claims (a spec that lies is worse than a spec with a logged gap), un-tested prior fixes (a fix without
a regression test silently regresses), and a suite-hang that made the whole test surface un-runnable
in a normal window. None was a live CRITICAL/HIGH bug — the value was converting un-logged risk into
logged, tracked, F5-gated work + closing the test-accretion holes.

## Follow-ups (see .session-notes ledger)

F5 greenlight gates the A1/A2/A3/A4 builds; recommend folding F2 (PDPA purge) into the A1/A2 data-layer
wave. R5-01 + R5-03 dispositions in `04-validate/round5/00-DECISION-PACKET-R5.md`. PR #7 push + merge is
the owner's production-deploy gate (branch is 8 commits ahead of origin, unpushed). `/whoami
--enroll-genesis` before the next `/release` (repo is fresh-substrate-adopter).
