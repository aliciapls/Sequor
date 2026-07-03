# M9 — Deployment / Infrastructure / Observability (cross-cutting)

> **What this milestone builds (plain language).** The ground the whole platform runs ON: the
> governed-core runtime actually deployed (the envoy-hybrid the runtime-ownership spike settles), the
> multi-tenant infrastructure that keeps each customer's data hermetically separate _at the
> infrastructure layer_, the durable provenance store with a retention/compaction policy so the
> ever-growing version history does not balloon storage forever, the observability layer (structured
> logs, a correlation/run id threaded through every step, a real/fake mode tag on every code path, the
> live decision-to-screen event stream), the SHADOW→enforce rollout mechanism that lets governance turn
> on under the _live_ comms product without breaking it, and the least-privilege secrets/connector-
> credential infrastructure.
>
> **Scope boundary (important).** The governance _logic_ (the posture machine, the plan-gate, the
> LLM-first classifier) is built and wired in M1. The cascade _engine_ is built in M4. The connectors
> are built in M3. M9 does NOT re-build any of those — it builds the **runtime/deployment/observability
> infrastructure they run on**: where the governed core is deployed, how tenants are isolated at the
> infra layer, where the durable store lives and how it is compacted, how every code path emits a
> correlated + mode-tagged log, how SHADOW flips to enforce reversibly on the live product, and how
> connector credentials are held least-privilege.
>
> **Two framing rules carried throughout.** (1) Foundation independence: the platform OWNS its
> governed-core runtime rather than depending on any proprietary SDK (per `rules/independence.md`;
> architecture §8.2) — the runtime-ownership spike (M0/C0) settles the exact shape, and M9 deploys it.
> (2) Tenant isolation is the highest-severity invariant: a missing `tenant_id` on a cache key, an
> audit row, or a metric label is a P0 cross-customer leak (per `rules/tenant-isolation.md`) — M9
> enforces it at the infrastructure layer, beneath the feature code.

---

## Dependency posture for this milestone

- **M9 is cross-cutting and spans the whole build.** The governed-core runtime deployment is gated by
  the C0 spike's verdict (does the platform own the loop?) and underlies every feature; the
  observability layer is needed from the first feature milestone (every code path must log with a
  correlation id + mode tag from day one); the durable-store + retention infra is needed wherever the
  ledger persists (M0/M4); the SHADOW→enforce mechanism is the rollout path for M1's governance on the
  live comms product. So M9's todos land incrementally alongside the feature milestones.
- **M9 builds infrastructure, it does not re-build features.** The runtime _logic_, governance _logic_,
  cascade _engine_, and connectors are owned by M0–M7. M9 owns: the runtime deployment, the infra-layer
  tenant isolation, the durable store + retention/compaction, observability (logs/correlation/mode-tags
  /event-stream infra), the rollout mechanism, and the secrets/credential infra.
- **The comms product is the live landing surface throughout.** The platform deploys on the comms
  product's existing Vercel + Neon Postgres stack and rolls governance in under SHADOW mode so the live
  product is never broken during rollout (comms-wedge plan §5; architecture §3.2, §11.1).

---

### M9-1 — Deploy the governed-core runtime (envoy-hybrid, per the C0 spike verdict)

- **Type:** BUILD
- **Implements:** specs/platform-overview.md §Layer-2 + §3.2 (envoy-hybrid) (+ architecture §8.3; roadmap §3; `rules/independence.md`)
- **What:** Deploy the governed-core runtime the C0 runtime-ownership spike settles — the
  reason→act→verify loop the platform OWNS (so transparency, two-phase intent/outcome signing, posture
  gating, and intervenable replay are native, not bolted on), built on Kailash-native frameworks, with
  no dependency on a proprietary SDK in the product core. The comms wedge stays on its existing deployed
  stack as the revenue-bearing landing surface while the governed runtime stands up beside it.
- **Reuses → Builds:** the envoy owned-runtime precedent + Kailash-native frameworks (Kaizen loop,
  Nexus surface, PACT+EATP governance, DataFlow data) + the comms product's deployed stack → the
  deployed governed-core runtime.
- **Invariants:** Foundation independence (no proprietary SDK in the product core); two-phase signing
  native (intent-before-action + outcome-after, both signed); every runtime path logged with a
  correlation/run id + mode tag (M9-4); tenant isolation enforced at the runtime boundary; no
  half-implementation (a referenced runtime capability is functional, not a stub).
- **Sizing:** ~2–3 cycles (greenfield runtime-deploy factor; the C0 spike must have settled the
  own-the-loop verdict first).
- **Depends on:** C0 (M0 spike — its verdict sets the runtime architecture).
- **Acceptance (confirm / falsify):** **Confirm:** the governed-core runtime is deployed, runs the
  reason→act→verify loop natively with two-phase signing, depends on no proprietary SDK, and the comms
  product keeps running on its existing stack throughout. **Falsify:** transparency/intervention/replay
  cannot be made native without depending on a proprietary loop (independence broken), OR the deploy
  takes the live comms product offline.

### M9-2 — Multi-tenant infrastructure + tenant-isolation enforcement at the infra layer

- **Type:** BUILD
- **Implements:** specs/transparency-and-provenance.md §2.6 invariant 2 (tenant isolation) + specs/data-model.md §Multi-Tenancy (+ `rules/tenant-isolation.md`; comms-wedge plan §2.3)
- **What:** Build the multi-tenant infrastructure that keeps each customer's data hermetically separate
  at the infrastructure layer — schema-per-tenant (matching the shipped comms isolation), a `tenant_id`
  dimension required on every cache key / durable-store namespace / queue, a typed error (not a silent
  "default" fallback) when a multi-tenant read arrives without a tenant, and tenant-scoped invalidation
  so clearing one tenant's cache never clears another's. This is the infra-layer floor beneath every
  feature's own tenant handling.
- **Reuses → Builds:** the comms product's schema-per-tenant isolation (PDPA-tested against a real
  regulator) → the platform-wide infra-layer tenant-isolation enforcement (cache-key namespacing,
  strict-mode typed error, tenant-scoped invalidation).
- **Invariants:** every cache key / audit row / durable-store namespace carries `tenant_id` (the
  content-addressed namespace is a named cross-tenant leak vector — hard gate); missing tenant_id on a
  multi-tenant read raises a typed error (silent "default"/"global"/"" fallback BLOCKED); invalidation
  is tenant-scoped; metric labels carry tenant_id only bounded (M9-4).
- **Sizing:** ~1–2 cycles (+ SHARD if cache-key namespacing and the strict-mode typed-error path each
  carry their own invariant set — shard one concern per session).
- **Depends on:** M9-1 (the runtime the isolation wraps).
- **Acceptance (confirm / falsify):** **Confirm:** a tenant-isolation probe (per the audit protocol)
  shows zero cross-tenant leakage — every cache key/namespace carries tenant_id, a tenant-less
  multi-tenant read raises a typed error, and invalidating one tenant's cache leaves others intact.
  **Falsify:** two tenants with overlapping primary keys read each other's cached records (tenant_id
  missing on a key), OR a missing tenant_id silently defaults to a shared slot.

### M9-3 — Durable provenance store + retention/compaction infrastructure

- **Type:** BUILD
- **Implements:** specs/transparency-and-provenance.md §2.5 + §6.2 + §7 #5 (retention policy owed) (+ architecture §4.5, §12 #8; `rules/tenant-isolation.md`)
- **What:** Build the durable provenance store (the permanent, content-addressed record the ledger
  persists into) and the retention/compaction infrastructure it needs — large artifacts stored by
  reference (content-hash) not inline, identical bytes deduped across versions, and a
  retention/compaction policy so the ever-growing version COUNT (content-addressing dedupes bytes, not
  versions) does not balloon storage without bound. This is the operational policy the transparency
  spec flags as owed before scale.
- **Reuses → Builds:** the Kailash durable store (`DBCheckpointStore` tiered memory→disk→DB, gzip) +
  the aegis compaction-checkpoint precedent → the deployed durable provenance store + retention/
  compaction infra.
- **Invariants:** immutability (a re-run appends a new version, never overwrites); large artifacts
  stored by reference, never inline; content-address dedup across versions; every stored
  namespace/blob carries `tenant_id` (cross-tenant content-address leak is the named P0 vector);
  retention/compaction never deletes the verifying chain head needed to re-derive history.
- **Sizing:** ~1–2 cycles.
- **Depends on:** M9-1, M9-2; C1 (the content-addressed step records the store persists).
- **Acceptance (confirm / falsify):** **Confirm:** the durable store persists content-addressed
  Step/Output nodes with tenant_id on every namespace, dedupes identical bytes across versions, stores
  large artifacts by reference, and a retention/compaction pass bounds version-count growth without
  losing the chain needed to re-derive history. **Falsify:** version count grows unbounded with no
  compaction path (storage balloons), OR compaction drops a node needed to re-derive a prior version,
  OR a stored blob lacks tenant_id (cross-tenant dedup leak).

### M9-4 — Observability: structured logs + correlation/run_id propagation + real/fake mode tags

- **Type:** BUILD
- **Implements:** specs/transparency-and-provenance.md §1.1 (OTel GenAI span shape) (+ `rules/observability.md` structured logging/correlation/mode-tags; `rules/zero-tolerance.md` Rule 1 log-triage)
- **What:** Build the observability layer every code path emits into: structured logs (not free-text
  prints), a correlation/`run_id` threaded through every step of a run so one objective's whole trace is
  reconstructable, and a `mode=real|fake` tag on every code path so a test/demo running against fake
  data is never mistaken for real. This is the cross-cutting logging spine; the per-feature ledger
  writes (M0/M4) feed into it.
- **Reuses → Builds:** the OpenTelemetry GenAI semantic-conventions span shape (industry standard,
  already emitted by the Kailash Core SDK) → the platform-wide structured-log + correlation-id +
  mode-tag layer.
- **Invariants:** every code path logged with a correlation/run_id + mode tag; no secrets/PII in logs
  (connection strings, tokens, credentials masked — per `rules/security.md`); structured logging (no
  bare prints); WARN+ entries owned and fixed, not deferred (per zero-tolerance Rule 1); the live OTel
  spans feed the durable ledger (ledger is source of truth), not a second disagreeing store.
- **Sizing:** ~1–2 cycles.
- **Depends on:** M9-1.
- **Acceptance (confirm / falsify):** **Confirm:** every code path emits a structured log carrying a
  correlation/run_id (one run's whole trace reconstructable from logs) + a mode=real|fake tag, and no
  secret/PII appears in any log line. **Falsify:** a code path logs without a correlation id (the
  trace cannot be stitched), OR a fake-mode run is indistinguishable from real in the logs (no mode
  tag), OR a credential leaks into a log line.

### M9-5 — The decision-to-screen event-stream infrastructure

- **Type:** BUILD
- **Implements:** specs/transparency-and-provenance.md §5.2 (live stream) + specs/trust-posture-and-governance.md §plan-approval-gate (+ architecture §3.2, §12 #6 single-process event bus)
- **What:** Build the live decision-to-screen event-stream infrastructure — the durable/distributed
  channel that carries plan-proposed decisions, held actions, and posture changes to the non-coder's
  screen as work happens. The shipped event bus is single-process in-memory; a multi-replica deployment
  needs a durable/distributed bus (the in-ecosystem path is a SQL task queue with SKIP LOCKED or a Redis
  fan-out). This is the infra that makes the M1 governance plan-gate and the M0/M4 live trace visible.
- **Reuses → Builds:** the PACT EventBridge/EventBus WebSocket fan-out (single-process today) + the
  SQL-task-queue / Redis fan-out path → the durable/distributed decision-to-screen event-stream infra.
- **Invariants:** the live stream is the ephemeral feed; the durable ledger is the source of truth (the
  stream writes into the ledger, no second disagreeing store); every streamed event carries a
  correlation/run_id + tenant_id; mode tag on every event (real/fake); no secrets/PII in streamed
  payloads.
- **Sizing:** ~1–2 cycles.
- **Depends on:** M9-1, M9-4.
- **Acceptance (confirm / falsify):** **Confirm:** a plan-proposed decision + a held action + a posture
  change stream to the screen live, carry correlation/run_id + tenant_id + mode tag, and survive a
  multi-replica deployment (durable/distributed bus, not single-process). **Falsify:** the event stream
  is single-process and silently drops events under multi-replica load, OR a streamed event lacks a
  correlation id / tenant scope (cross-tenant or untraceable event leak).

### M9-6 — SHADOW→enforce rollout mechanism on the live comms product (reversible)

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §SHADOW-mode (+ comms-wedge plan §5 SHADOW-mode rollout; architecture §3.2, §3.5; roadmap §5)
- **What:** Build the rollout mechanism that runs governance under the live comms product in SHADOW mode
  (observe what _would_ be held or blocked without blocking anything), then flips a single tenant/
  objective from observe to enforce — reversibly, so a bad flip rolls straight back with no customer
  disruption. The flip is the structural human gate (it changes real user behavior); the mechanism makes
  it one switch, not a redeploy.
- **Reuses → Builds:** PACT `EnforcementMode.SHADOW` + the deployed comms product → the reversible
  SHADOW→enforce flip mechanism per tenant/objective.
- **Invariants:** SHADOW observes-without-blocking (the live product is never broken during
  observation); the flip is reversible (rollback is a switch, not a redeploy); the flip is human-gated
  (structural gate — it changes real user behavior); every would-hold/would-block observation is logged
  with correlation/run_id + tenant_id + mode tag; defaults preserve current comms behavior until flipped.
- **Sizing:** ~1 cycle.
- **Depends on:** M9-1, M9-4; M1 (the governance logic SHADOW observes).
- **Acceptance (confirm / falsify):** **Confirm:** governance runs in SHADOW on the live comms product
  logging what it _would_ hold/block without affecting any customer, and a single tenant/objective can
  be flipped observe→enforce and back (the flip is reversible). **Falsify:** SHADOW silently blocks a
  real action (it is not observe-only), OR the flip cannot be reversed without a redeploy / causes
  customer disruption.

### M9-7 — Secrets + connector-credential infrastructure (least-privilege)

- **Type:** BUILD
- **Implements:** specs/connectors-and-integration.md §OAuth-security-model + §least-privilege (+ `rules/security.md` § No Hardcoded Secrets / No secrets in logs; architecture §7)
- **What:** Build the secrets + connector-credential infrastructure: every connector credential held in
  environment/secret storage (never hardcoded, never in git), scoped to the minimum privilege the
  objective needs (not the union of everything connected), and never written to a log. This is the
  infra-layer credential floor beneath the M3 connectors and the governed-connectivity discipline.
- **Reuses → Builds:** the comms product's existing connector-credential handling + the MCP OAuth 2.1
  resource-server model → the platform-wide least-privilege secrets/credential infra.
- **Invariants:** no hardcoded secrets (env/secret-store only; `.env` never in git); least-privilege per
  objective (narrow-and-earned envelope, not broad standing access); no secrets/credentials in logs
  (masked at every log + receipt site, per `rules/security.md`); credential decode routes through a
  single shared helper (no hand-rolled per-site decode drift).
- **Sizing:** ~1 cycle.
- **Depends on:** M9-1, M9-4; M3 (the connectors the credentials serve).
- **Acceptance (confirm / falsify):** **Confirm:** every connector credential is held in secret storage
  (none in source/git), scoped least-privilege per objective, and a security scan shows zero credentials
  in any log line. **Falsify:** a credential is hardcoded or committed, OR a connector is granted broad
  standing access beyond the objective's need, OR a credential appears in a log/receipt.

---

## Milestone-level acceptance

The deployment/infra/observability layer is **proven** when: the governed-core runtime is deployed per
the C0 verdict with no proprietary-SDK dependency and the comms product keeps running throughout;
tenant isolation holds at the infra layer (a probe shows zero cross-tenant leakage on cache keys, audit
rows, namespaces); the durable provenance store persists content-addressed nodes with a working
retention/compaction policy that bounds version-count growth; every code path emits a structured log
with a correlation/run_id + real/fake mode tag and no secrets/PII; the decision-to-screen event stream
is durable/distributed and tenant-scoped; the SHADOW→enforce flip runs governance under the live comms
product reversibly and human-gated; and connector credentials are held least-privilege with none in
source, git, or logs. The feature logic remains owned by M0–M7 — M9 is the ground they run on.
