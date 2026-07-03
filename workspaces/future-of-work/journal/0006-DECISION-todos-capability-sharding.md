# 0006 — DECISION: /todos decomposed the platform into 11 capability-first milestones (101 todos)

- **Type:** DECISION
- **Date:** 2026-07-03
- **Phase:** /todos → /codify (workspace: future-of-work)
- **Author:** jack-hong

## Decision

Decomposed `02-plans/02-capability-roadmap.md` (the C0–C7 proof sequence) into **101 todos across 11 milestones** in `todos/active/` (M0–M10 + `00-INDEX.md`), sequenced by **dependency order + value** (capability-first, Decision B).

**Milestones:** M0 spikes (C0 runtime-ownership, C1 single-step replay) · M1 governance/M2-moat (C2) · M2 non-coder surface (C3) · M3 cross-system reach (C4) · M4 retrace/cascade engine/M1-moat (C5) · M5 cross-org exchange/M4-moat (C6) · M6 team substrate/M3-moat · M7 the capability-proven demo · M8 testing · M9 deploy/infra · M10 docs.

**Discipline applied:** BUILD / WIRE / TEST are separate todos; every governance manager carries the orphan-detection trio (hot-path call site + Tier-2 wiring test); the C5 cascade engine is pre-sharded into 4 invariant-focused shards + a separate UI shard + retention; effort in autonomous cycles.

**Decision D applied** ([[0003-GAP-unproven-bets-and-netnew-unknowns]] superseded for planning): the team substrate (M6) is built as FOUNDATIONAL, not gated behind a validation spike; the former agent-comms "BET" (C7a) is re-scoped to NON-GATING corroborating instrumentation; the §13 roadmap ledger was swept to match. **Decision C applied:** D/T/R = Department/Team/Role wired into M6 accountability todos.

## Gate

Structural gate — the human approves WHAT is built and WHY (the plan), not HOW/WHEN (execution). Approved by the owner directing `/codify` + commit. `/implement` executes autonomously from here, honoring the two named human gates (the C0 runtime-ownership direction; the SHADOW→enforce flip on the live comms product).

Source: `todos/active/00-INDEX.md`, `02-plans/02-capability-roadmap.md`.
