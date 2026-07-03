# M3 — Cross-system reach (C4)

> **What this milestone proves.** The paradigm-shift proof at its minimum: **one agent runs an
> objective across ≥2 systems that previously required a human to bridge them** — governed,
> least-privilege (capability roadmap §7 C4; architecture §7 L1 connector layer). Today the
> human is the integration layer carrying data across ERP, CRM, spreadsheets, portals; this
> milestone makes the AGENT the integration layer (platform-overview §3 the inversion). Comms
> today exercises one tool-cluster (inbox + knowledge base); it does NOT prove cross-system
> orchestration — that gap is the platform's real build (roadmap §7.1).
>
> **The two disciplines that make it the moat, not a commodity.** (1) **Tools are dumb
> endpoints; the LLM does ALL reasoning** — `get_order(id) → record`, never
> `handle_order_issue(...)` with `if order.status == "delivered"` logic buried in tool code
> (connectors-and-integration.md §3; `.claude/rules/agent-reasoning.md`). Decision logic in tool
> code is invisible to the reasoning trace — it breaks the C1/C5 transparency contract. (2)
> **Governance sits BETWEEN the agent and each connector** — a write to a system of record can
> be HELD until a human approves (connectors §4.4, §5; roadmap §7.2). Connectivity is a
> commodity; only GOVERNED connectivity differentiates.
>
> **Governance reuse anchor.** C4 uses the M1 governance milestone (PACT/EATP envelopes +
> verification gradient + ApprovalBridge/HELD) as the between-agent-and-connector enforcement
> point (architecture §7.3; roadmap §7.3). This milestone does NOT rebuild governance — it wires
> the shipped governance as the enforcement gate on every connector call.
>
> **Sizing shape (read before sharding).** Connector porting is **boilerplate-heavy and scales
> ~5× further before sharding triggers** (one pattern stamped per connector — roadmap §7.3,
> §7.4). The **governed-curation + least-privilege-envelope-derivation logic is load-bearing and
> shards separately** (roadmap §7.4). BUILD a connector and WIRE it under governed-curation +
> least-privilege are SEPARATE todos: a ported connector with no governance between agent and
> connector is raw connectivity, not the moat.
>
> **The honest tension flagged.** The least-privilege envelope derivation must NOT itself become
> decision-logic in tools, or it violates the dumb-endpoints rule (connectors §4.2, §4.3; roadmap
> §7.4). M3-4 holds this invariant explicitly.
>
> **Conventions.** Effort in autonomous execution cycles (`.claude/rules/autonomous-execution.md`),
> never human-days. Plain language, CLI-neutral (`.claude/rules/cross-cli-artifact-hygiene.md`).
> Acceptance for C4 REQUIRES a **real ≥2-system run with governance + least-privilege** — not a
> unit test in isolation, and per `.claude/rules/orphan-detection.md` every governance/connector
> manager wired into the hot path needs a real call site AND a Tier-2 test proving the framework
> calls it.

---

### M3-1 — DESIGN the dumb-endpoint connector contract + the record vs virtual-file decision

- **Type:** DESIGN
- **Implements:** specs/connectors-and-integration.md §2 (MCP connector framework), §2.3 (record-model open decision), §3 (the dumb-endpoints keystone) (+ plan: 02-plans/01-architecture.md §7.1–§7.2, §7.4)
- **What:** Define the connector contract every ported connector MUST satisfy: a connector is a dumb data endpoint (`get_X(id) → record`, `write_X(record) → result`) with ZERO decision logic; all reasoning lives in the logged model I/O. RESOLVE the open architectural decision — business objects surfaced as a record-tool API vs as files in a virtual file system (connectors §2.3) — in favour of the **record-model** (a record-tool API: `get_X(id) → record`, `write_X(record) → result`), per architecture §7.4 and §12 #5 and consistent with M2-3's records-not-files non-coder surface. The virtual-file alternative is rejected because it re-acquires the developer file/folder mental model the brief explicitly inverts and forces the agent to parse paths instead of reading records. One contract spec, no connector code.
- **Reuses → Builds:** the MCP connector protocol (the now-standard agent-reaches-a-system-as-a-tool surface) + the >1,000 existing MCP connectors as the shape reference → the dumb-endpoint contract + the resolved record-model (per architecture §7.4 / §12 #5) that every connector port and every governance wrap consumes.
- **Invariants:** tools-dumb-endpoints (no decision logic in any connector method); governed-connectivity (the contract reserves the enforcement seam between agent and connector); tenant-isolation (every connector call carries tenant_id by contract).
- **Sizing:** ~1 cycle. Pure design; the contract is the 3-sentence-describable spec the porting + wiring shards depend on. Within the per-session budget.
- **Depends on:** none. (Consumes the M1 governance milestone's envelope/gradient shapes as the enforcement-seam reference, but does not require them built.)
- **Acceptance (confirm / falsify):** Confirm — the contract spec states, testably, that a conforming connector exposes only data-move methods and that any reasoning in a connector is a contract violation; the record-vs-virtual-file decision is RESOLVED to the record-model (per architecture §7.4 / §12 #5) with the consequence named (connectors expose `get_X`/`write_X` record APIs, NOT file-path methods). Falsify — the contract permits (or is silent on) decision logic inside a connector method, OR leaves the record-vs-virtual-file decision open/staged rather than resolved to the record-model.

---

### M3-2 — BUILD connector #1 (read from a system of record) under the dumb-endpoint contract

- **Type:** BUILD
- **Implements:** specs/connectors-and-integration.md §2 (connector framework), §5.1 (read direction), §3.1 (dumb-endpoint principle) (+ plan: 02-plans/01-architecture.md §7.5; 02-plans/02-capability-roadmap.md §7.3)
- **What:** Port the first connector — a READ from a ledger/records system (e.g. pull Q3 entries) — as a dumb endpoint conforming to M3-1's contract. Build only the connector (the data-move methods); the governed-curation wrap + least-privilege scoping are SEPARATE todos (M3-4, M3-5).
- **Reuses → Builds:** the MCP protocol + the existing connector ecosystem + comms' own channel adapters as the first connector instances → connector #1 as a conforming dumb endpoint.
- **Invariants:** tools-dumb-endpoints (the connector only fetches/returns rows; it decides nothing); tenant-isolation (every read scoped to tenant_id); governed-connectivity (the connector exposes the seam but does NOT self-govern — governance is M3-4).
- **Sizing:** ~1 cycle, boilerplate-heavy (connector porting stamps out the contract pattern — may absorb up to ~5× the base budget before sharding triggers per roadmap §7.4). SHARD note: if porting a connector family, one connector per shard is over-sharding — batch conforming reads in one shard; split only when a connector needs non-boilerplate auth/pagination logic.
- **Depends on:** M3-1.
- **Acceptance (confirm / falsify):** Confirm — connector #1 reads real rows from the live records system through the MCP protocol, exposes only data-move methods, and the read is logged as a tool call in the trace; verified against real infra (Tier-2, no mocking per `.claude/rules/testing.md`). Falsify — the connector contains any conditional business logic (dumb-endpoint violation), OR the read is not surfaced legibly in the reasoning trace.

---

### M3-3 — BUILD connector #2 (write to a document/output system) under the dumb-endpoint contract

- **Type:** BUILD
- **Implements:** specs/connectors-and-integration.md §5.1 (write direction), §5.2 (the structural rule), §3.1 (dumb-endpoint principle) (+ plan: 02-plans/01-architecture.md §7.5; 02-plans/02-capability-roadmap.md §7.2 confirm-criterion "write to a document/output system")
- **What:** Port the second connector — a WRITE to a document/output system (the second, formerly-siloed system the objective reaches) — as a dumb endpoint conforming to M3-1's contract. The write path is built here; the HELD-until-human governance on the write is the M3-4 wiring (a write to a system of record must be governable).
- **Reuses → Builds:** the MCP protocol + the existing connector ecosystem → connector #2 as a conforming dumb endpoint with a write method that exposes the governance seam.
- **Invariants:** tools-dumb-endpoints (the write method moves data, decides nothing); tenant-isolation (writes scoped to tenant_id); governed-connectivity (the write exposes the enforcement seam for M3-4's HELD gate; it does NOT self-approve).
- **Sizing:** ~1 cycle, boilerplate-heavy (same porting pattern as M3-2). Within budget; live feedback loop against real infra with read-back verification of every write per `.claude/rules/testing.md`.
- **Depends on:** M3-1. (Parallel-eligible with M3-2 — different connector, different system; per worktree isolation each porting shard gets its own worktree.)
- **Acceptance (confirm / falsify):** Confirm — connector #2 writes to the live output system through MCP, exposes only data-move methods, and every write is verified with a read-back; Tier-2, no mocking. Falsify — the write method buries any decision logic, OR the write executes without exposing the seam where governance (M3-4) must gate it.

---

### M3-4 — WIRE governed curation: governance sits BETWEEN the agent and each connector

- **Type:** WIRE
- **Implements:** specs/connectors-and-integration.md §4.4 (governance between agent and connector), §5 (read vs write-to-system-of-record gate), §5.3 (the 5-dim envelope governs the write gate) (+ plan: 02-plans/01-architecture.md §7.3; 02-plans/02-capability-roadmap.md §7.2–§7.3)
- **What:** Wire the M1-milestone governance (PACT/EATP envelope + verification gradient + ApprovalBridge/HELD) as the enforcement point BETWEEN the agent and each connector from M3-2/M3-3 — so a write to a system of record is HELD until a human approves, and any call outside the envelope is blocked. This is the discipline that turns raw connectivity into the governed connectivity that is the moat.
- **Reuses → Builds:** C2/M1 governance (envelopes, the auto/flag/HELD/block gradient, ApprovalBridge, the live decision-to-screen stream) as the between-agent-and-connector enforcement → the governed-curation wrap on each connector.
- **Invariants:** governed-connectivity (a write to a system of record requires the envelope to permit it OR a human gate — connectors §5.2); tools-dumb-endpoints (the governance wrap is enforcement, NOT decision logic moved into the connector); tenant-isolation (every governed call + every HELD/audit row scoped to tenant_id); no-orphan (a real call site from the connector hot path into the governance manager + a Tier-2 test proving the framework calls it on the connector path — `.claude/rules/orphan-detection.md`, `.claude/rules/facade-manager-detection.md`).
- **Sizing:** ~1–2 cycles. This is the load-bearing logic (NOT boilerplate) — it shards separately from connector porting per roadmap §7.4. SHARD note: wire one connector's governance at a time (read-gate, then write-HELD-gate) — each carries the no-orphan invariant set (call site + Tier-2 wiring test) and shards separately per `.claude/rules/orphan-detection.md`. The PACT-is-facade-heavy orphan risk is real: the wiring is proven only by an externally observable effect (a HELD write, an audit row).
- **Depends on:** M3-2, M3-3, AND the M1 governance milestone (the shipped envelope/gradient/ApprovalBridge it wires). C4 uses M1 governance as the between-agent-and-connector enforcement (roadmap §7.3).
- **Acceptance (confirm / falsify):** Confirm — a real run where a write to the system of record is HELD until a human approves AND a call outside the envelope is blocked, with the decision surfaced on screen and an audit row written; a Tier-2 integration test proves the framework calls the governance manager on the connector hot path with an externally observable effect (the HELD write / the audit row). Falsify — governance ships as a facade that never executes on the connector path (the orphan failure — beautifully wired, zero hot-path call sites), OR business logic had to be buried in connector code to make cross-system sequencing work (breaking the dumb-endpoints + transparency contract).

---

### M3-5 — WIRE per-objective least-privilege envelope derivation (narrow-and-earned, not broad-and-assumed)

- **Type:** WIRE
- **Implements:** specs/connectors-and-integration.md §4.2 (least-privilege per objective), §4.3 (the tension), §4.1 (credential contract) (+ plan: 02-plans/01-architecture.md §7; 02-plans/02-capability-roadmap.md §7.2 confirm-criterion "minimum tool/clearance envelope … not the union of everything connected", §7.4)
- **What:** Wire the derivation of a per-objective least-privilege envelope — the agent is granted only the minimum tool/clearance scope the objective needs, NOT the union of everything connected. The envelope is derived per objective and enforced at the connector boundary (composing with M3-4's gate).
- **Reuses → Builds:** the EATP/PACT 5-dimension envelope + monotonic-tightening (a sub-agent gets only a tighter box) + clearance machinery → the per-objective least-privilege derivation + enforcement.
- **Invariants:** least-privilege-per-objective (narrow-and-earned: the envelope is the objective's minimum, re-derived per objective); tools-dumb-endpoints (the derivation logic lives in the governed core, NOT inside tool code — the explicit honest tension per connectors §4.3 / roadmap §7.4); governed-connectivity; tenant-isolation; no-orphan (real call site + Tier-2 test proving the derived envelope actually constrains a live call).
- **Sizing:** ~1–2 cycles. Load-bearing logic (the derivation holds the least-privilege invariant) — shards separately from connector porting and from M3-4's gate. SHARD note: keep envelope-DERIVATION and envelope-ENFORCEMENT reasoning within one shard's invariant budget; the derivation must NOT leak decision logic into tools — if holding that tension pushes past the budget, split derivation (governed core) from the enforcement call site.
- **Depends on:** M3-4 (the governance gate the envelope feeds), the M1 governance milestone (the envelope primitive).
- **Acceptance (confirm / falsify):** Confirm — a real run where the agent for a given objective can reach ONLY the minimum tools/clearance that objective needs, and a call to a connected-but-not-needed system is denied by the derived envelope; a Tier-2 test proves the derived envelope constrains a live call. Falsify — the agent must be over-provisioned with broad standing access to function (re-acquiring the concentrated-blast-radius risk — roadmap §7.2), OR the least-privilege derivation became decision-logic inside tool code (violating dumb-endpoints — the §4.3 tension).

---

### M3-5a — TEST the governed-curation wiring (Tier-2, governance sits between agent and connector)

- **Type:** TEST
- **Implements:** specs/connectors-and-integration.md §4.4 (governance between agent and connector), §5 (write-to-system-of-record gate) (+ plan: 02-plans/01-architecture.md §7.3; 02-plans/02-capability-roadmap.md §7.2–§7.3)
- **What:** A SEPARATE Tier-2 wiring test (`test_governed_curation_wiring.py`) that proves the M3-4 governed-curation manager actually sits on the connector hot path between the agent and each connector — not that it CAN govern in isolation, but that the framework CALLS it on every connector read/write. The test imports the governance through the framework facade (not the manager class directly), triggers a real connector call, and asserts an externally observable governance effect (a HELD write awaiting approval, an audit row written, a call outside the envelope blocked). This is the `.claude/rules/facade-manager-detection.md` Rule 2 wiring proof — distinct from M3-6's full end-to-end, which exercises the whole ≥2-system sequence.
- **Reuses → Builds:** the M3-4 wired governed-curation manager + real infra → the grep-able Tier-2 wiring test that proves governance is on the hot path, not an orphan facade.
- **Invariants:** no-orphan (the test proves the framework calls the governance manager on the connector path with an externally observable effect — `.claude/rules/orphan-detection.md` Rule 2, `.claude/rules/facade-manager-detection.md` Rule 2); governed-connectivity (verified: a write was HELD / a call outside the envelope was blocked); tenant-isolation (verified: the HELD/audit row carries tenant_id).
- **Sizing:** ~1 cycle. Tier-2 wiring test against real infra with a live feedback loop. Within budget. SHARD note: this is the wiring-proof test ONLY (one manager, one hot-path assertion); the cross-system sequence is M3-6.
- **Depends on:** M3-4 (the governed-curation manager this test exercises).
- **Acceptance (confirm / falsify):** Confirm — `test_governed_curation_wiring.py` imports governance through the framework facade, triggers a real connector call, and asserts an externally observable governance effect (HELD write / audit row / blocked-outside-envelope call); the test is named so its absence is grep-able. Falsify — the test exercises the governance manager in isolation (mocking the framework's call into it), proving the manager CAN govern but NOT that the framework CALLS it on the hot path (the exact orphan failure the test exists to catch).

---

### M3-5b — TEST the least-privilege-envelope wiring (Tier-2, an over-broad envelope is denied)

- **Type:** TEST
- **Implements:** specs/connectors-and-integration.md §4.2 (least-privilege per objective), §4.3 (the tension) (+ plan: 02-plans/01-architecture.md §7; 02-plans/02-capability-roadmap.md §7.2 confirm-criterion "minimum tool/clearance envelope … not the union of everything connected", §7.4)
- **What:** A SEPARATE Tier-2 wiring test (`test_least_privilege_envelope_wiring.py`) that proves the M3-5 per-objective least-privilege envelope actually CONSTRAINS a live connector call — specifically, that an over-broad request (a call to a connected-but-not-needed system, i.e. outside the derived envelope) is DENIED at the connector boundary. The test derives an envelope for a narrow objective, then attempts a call the envelope does not grant, and asserts the denial is enforced (not merely logged). This is distinct from M3-6's end-to-end, which verifies the happy-path ≥2-system run held only the minimum envelope.
- **Reuses → Builds:** the M3-5 wired least-privilege derivation + enforcement + real infra → the grep-able Tier-2 wiring test that proves the derived envelope denies an over-broad call.
- **Invariants:** least-privilege-per-objective (verified: a call outside the derived envelope is denied at the connector boundary); no-orphan (the test proves the derived envelope actually constrains a live call — `.claude/rules/orphan-detection.md` Rule 2); tools-dumb-endpoints (verified: the denial is enforcement at the boundary, NOT decision logic inside tool code); tenant-isolation.
- **Sizing:** ~1 cycle. Tier-2 wiring test against real infra with a live feedback loop. Within budget. SHARD note: this is the envelope-denial wiring-proof ONLY (derive narrow envelope, attempt over-broad call, assert denial); the happy-path ≥2-system run is M3-6.
- **Depends on:** M3-5 (the least-privilege envelope derivation this test exercises), M3-4 (the gate the envelope composes with).
- **Acceptance (confirm / falsify):** Confirm — `test_least_privilege_envelope_wiring.py` derives an envelope for a narrow objective, attempts a call to a connected-but-not-needed system (outside the envelope), and asserts the call is DENIED by the derived envelope at the connector boundary; the test is named so its absence is grep-able. Falsify — an over-broad call outside the derived envelope is permitted (the envelope does not actually constrain), OR the denial is only logged rather than enforced.

---

### M3-6 — TEST the real ≥2-system run end-to-end (the C4 capability proof)

- **Type:** TEST
- **Implements:** specs/connectors-and-integration.md §9 (the connector layer in one objective, end-to-end) (+ plan: 02-plans/02-capability-roadmap.md §7.2 the C4 confirm/falsify criteria; 02-plans/01-architecture.md §9 one-objective-end-to-end)
- **What:** Exercise the full C4 proof: one agent runs an objective across the two formerly-siloed systems (read from M3-2's records system, write to M3-3's output system) through dumb-endpoint connectors, with M3-4's governance between agent and each connector and M3-5's least-privilege envelope in force. Verify all reasoning is in the logged model I/O (nothing buried in tool code).
- **Reuses → Builds:** the wired connectors + governed curation + least-privilege envelope + the live trace → the end-to-end C4 capability proof (the real ≥2-system run with governance + least-privilege).
- **Invariants:** tools-dumb-endpoints (verified: all reasoning is in the logged model I/O, no decision logic in any tool); governed-connectivity (verified: a write was HELD until human approval); least-privilege-per-objective (verified: only the minimum envelope was granted); tenant-isolation (verified: every connector call scoped to tenant_id).
- **Sizing:** ~1 cycle. Integration/E2E proof with a live feedback loop (Tier-3 against real infra, every write verified with read-back per `.claude/rules/testing.md`). Within budget.
- **Depends on:** M3-2, M3-3, M3-4, M3-5, M3-5a, M3-5b. (M3-5a/M3-5b are the separate Tier-2 wiring-proof tests for governed-curation and least-privilege; this todo is the full ≥2-system end-to-end ON TOP of those wiring proofs, not a substitute for them.) This is the gate for the end-to-end demo, which by definition needs ≥2 systems (roadmap §7.4). The full traced-and-rewindable demo is complete only once C5 (the M1 rewind engine) also lands.
- **Acceptance (confirm / falsify):** Confirm — a real ≥2-system run: the agent reads from system A and writes to system B in one objective, the write is governed (HELD until approved), the agent held only the least-privilege envelope, and the whole sequence is transparent in the trace with no business logic buried in tools; Tier-3 receipts against real infra. Falsify — cross-system sequencing could not be done without burying business logic in tool code (breaking transparency), OR the agent had to be over-provisioned to function (breaking least-privilege).
