# 0001 — DISCOVERY: ~80% of the platform substrate already exists as shipped ecosystem assets

- **Type:** DISCOVERY
- **Date:** 2026-06-06
- **Phase:** /analyze → /codify (workspace: future-of-work)
- **Author:** jack-hong

## Finding

The agentic-work-platform vision is buildable rather than a from-scratch moonshot: the hard substrate is already shipped across the Terrene/Kailash ecosystem (Phase A research, `01-analysis/01-research/`):

- **loom** (`~/repos/loom`) — the COC artifact splitter IS the cross-org "create/modify/store/share artifacts" engine (brief 3g): variant overlays, two-gate `/sync`, proposal lifecycle (append-never-overwrite), `obsoleted:` recall, disclosure-scrub.
- **PACT** (`~/repos/terrene/contrib/pact`) — D/T/R (Department/Team/Role) governance, operating envelopes, clearance, SupervisorOrchestrator/ApprovalBridge/EventBridge/EmergencyBypass = the M2 permission-envelope + approval substrate.
- **EATP** (in `~/repos/loom/kailash-py`) — TrustPlane/BudgetTracker/PostureStore = posture + budget.
- **aegis** (`~/repos/dev/aegis`) — progressive **L1–L5 posture state machines**, multi-operator coordination, crypto trust anchors = the closest existing implementation of the brief's "choose a posture beforehand + interveneable steps."
- **envoy** (`~/repos/dev/envoy`) — multi-CLI parity = harness-agnostic operation.
- 400+ artifacts already authored; the comms wedge already deployed.

## Why it matters

Re-frames the build from "invent a platform" to "compose shipped DNA + build the concentrated net-new 20%." It is the evidence for the brief's implicit 80/15/5 reuse thesis.

## Caveat (load-bearing)

Primitives ≠ a finished product; **codegen** primitives ≠ **enterprise-work** capability. The 80% is a head start, not a shortcut. Net-new risk concentrates in (a) the non-coder self-service surface, (b) the M1 retrace/cascade engine, (c) the untrusted-publisher trust model. See [[0003-GAP-unproven-bets-and-netnew-unknowns]].

Source: `01-analysis/08-product-focus-80-15-5.md`, `01-analysis/01-research/{01,02,03,04,09}`.
