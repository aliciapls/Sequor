# Specs Index

This project has two tiers of specs. The **platform** is the vision — the agnostic agentic-work platform described in `workspaces/future-of-work`, where a non-coder gets any knowledge work done by stating an outcome to a governed, transparent agent. It is target-state and not yet implemented. The **comms wedge** is the shipped product (a multi-channel WhatsApp + email assistant for non-technical accounts), subsumed as the platform's first vertical: it describes behavior that ships today.

When reading specs: platform specs describe intended behavior (status TARGET-STATE); comms-wedge specs describe shipped behavior and are the authority on what exists now.

**Known spec↔code deviations are logged in [`DEVIATIONS.md`](DEVIATIONS.md)** (per `.claude/rules/specs-authority.md` Rule 6) — read it alongside any comms-wedge spec: it records where shipped code under-delivers vs an affirmative spec claim, where two specs contradict each other, and the recommended/pending disposition for each.

## Platform (target-state / vision)

| File                              | Domain       | Description                                                                                                                                                                                                                       |
| --------------------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `platform-overview.md`            | Platform     | TARGET-STATE entry point: the OBJECTIVE/PROCESS/DATA work model, the integration-layer inversion, the seven layers, moats M1–M4, the non-coder principle, the black-box boundary                                                  |
| `transparency-and-provenance.md`  | Transparency | TARGET-STATE: the transparency contract (glass-box vs black-box boundary), the content-addressed immutable provenance ledger, activity tracing/attribution, fan-out preview (M1/M2 record side)                                   |
| `intervention-and-versioning.md`  | Intervention | TARGET-STATE: retrace-to-any-step intervention + immutable versioning (moat M1) — provenance ledger node model, the cascade re-execution engine, determinism resolution, cost preview, irreversibility                            |
| `trust-posture-and-governance.md` | Governance   | TARGET-STATE: execution-time, posture-graded governance (moat M2) — the L1–L5 posture ladder, spending/scope envelope, plan-approval gate, HITL/HOTL, set before work runs                                                        |
| `coordination-and-teams.md`       | Coordination | TARGET-STATE: the multi-human + multi-agent shared-work substrate (moat M3) — claims, lossless handoffs, named-human accountability, tamper-evident log, informal mode                                                            |
| `artifact-system-and-registry.md` | Artifacts    | TARGET-STATE: how reusable know-how is encoded by non-coders, stored, versioned, exchanged (moat M4) — the five artifact layers, authoring loop, version lifecycle, intra/cross-org distribution, untrusted-publisher trust model |
| `connectors-and-integration.md`   | Connectors   | TARGET-STATE: how the agent reaches every enterprise system (L1) — the MCP connector framework, OAuth security model, per-objective least-privilege scoping, governed connectivity, multi-harness parity                          |

## Comms wedge (shipped)

| File                      | Domain        | Description                                                                                                                         |
| ------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `message-routing.md`      | Channels      | SHIPPED: Company WhatsApp Business API, email threading, per-account channel config, multi-channel deduplication                    |
| `rag-pipeline.md`         | AI/RAG        | SHIPPED: Document ingestion, embedding, retrieval, learning from human answers, hallucination controls, freshness                   |
| `response-accuracy.md`    | AI/Governance | SHIPPED: Confidence badges, structured email escalations, auto-escalation timing, D/T/R accountability                              |
| `data-model.md`           | Data          | SHIPPED: Account-based model (individual/department), Contact, Message, Escalation, AuditEntry entities; PDPA compliance            |
| `channel-coordination.md` | Channels      | SHIPPED: Email-first interface, no separate app, daily digest, WhatsApp + email coordination, contradictory response prevention     |
| `business-model.md`       | Business      | SHIPPED: Per-account pricing (not per-seat), flexible channels, channel partner model, geographic expansion, CAC/LTV unit economics |
| `onboarding.md`           | UX/Product    | SHIPPED: 5-step non-technical onboarding, no app required, email-first setup, optional WhatsApp, routing configuration              |
