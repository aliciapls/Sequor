# Redteam Eval-Harness — Sequor comms-wedge

Probe-driven adversarial + regression harness owned by `/redteam` (Step 4b). It
asserts SEMANTIC / intent + defect-closure properties that Tier-1/2/3 suites do
not directly target, and it **accretes** a regression probe for every defect any
redteam round surfaces (the semantic twin of `tests/regression/`).

## Contract

- **Probe-driven, never regex-on-semantic** (`rules/probe-driven-verification.md`).
  Offline probes are STRUCTURAL (import + assert, AST shape, code-shape, behavioral
  call-and-assert) — never keyword/substring scoring of model prose. Probes that
  need a live LLM/Postgres are marked `@pytest.mark.probe_online` and skip cleanly
  offline with an explicit reason (never a regex fallback).
- **Accretion, never pruned.** Each round appends probes for its findings; a closed
  defect keeps its probe forever so a future refactor re-surfaces the regression.
- A failing probe = HIGH finding; "Tier-1/2/3 pass" is INSUFFICIENT.

## Probe inventory (as of Round 5, 2026-07-05)

`test_security_regression_probes.py` — R1 auth-bypass, R2 fail-closed config / admin
gate / onboarding upload bound / login timing, R3 N1 portal upload bound / N3 rate
limiter fail-closed / N4 inbound unverifiable-reject / N6 DNS logged-not-silent.
`test_spec_compliance_probes.py` — R3 NEW-3 answerability floor, NEW-5 hallucination
per-claim denominator, D1 digest api (`gather_digest_data`/`format_digest_email`).
`../unit/test_r5_regression_fixes.py` — R5-02 WhatsApp verify-token constant-time
compare + reject-mismatch; G3 500-handler no-traceback-leak; G2 keyphrase/mappings
`select`/`desc` name-resolution (R2 NameError-fix behavioral guard).

## Online probes (deferred — need infra)

Semantic probes that need a live LLM judge (refusal-vs-rationalization, badge-content
correctness, hallucination-judgment quality) and Tier-2/3 probes that need Postgres
(`gather_digest_data` execution, encryption round-trip through the ORM) are enumerated
as `@pytest.mark.probe_online` stubs to be filled when infra is provisioned — they
skip with `reason="probe-unavailable: requires <LLM|postgres>"`, never regex-fallback.
