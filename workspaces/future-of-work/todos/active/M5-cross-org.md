# M5 — Cross-Org Artifact Exchange (C6, moat M4): Design-First Trust, Then The Registry

> **What this milestone proves (plain language).** A company can safely run a work-recipe published
> by another company it has never met — a procedure, a checklist, a specialized agent — against its
> own real systems, with confidence that the recipe can only do what it openly declared it needs, can
> never quietly grab more, and can be pulled back from everyone at once if it turns out to be bad.
> This is the platform's network-effects engine: know-how becomes a tradeable asset, not a thing
> locked in one expert's head.
>
> **The two-stage ordering, stated honestly (do NOT collapse it).** Within-org sharing ships FIRST.
> It has no cold-start gap — the producer and the consumer are the same company, so the existing
> bounded-trust machinery (loom's splitter, variant overlays, recall, the within-org codify loop)
> already covers it with NO new trust model. Cross-org opens SECOND, and ONLY after the
> untrusted-publisher trust model (the design todo below) has landed and been reviewed — because that
> design constrains the shape of the registry, and getting it wrong forces an expensive
> re-architecture. (roadmap §9.2, §10.2; plan 01 §6.3–§6.4; artifact-system-and-registry.md §4–§5,
> §8, §11.)
>
> **What is genuinely new vs reused (the 80/15/5 honesty).** ~80% already runs in production for one
> org's artifacts: the five-layer artifact taxonomy, the proposal lifecycle (append-never-overwrite),
> the variant-overlay engine, the disclosure-scrub on intake, and — the trust keystone — the recall /
> obsoletion primitive that already purges a bad artifact from 30+ consumers on their next pull. ~15%
> is re-pointing those primitives at the org boundary instead of the repo boundary (org-axis variant
> overlays, work-domain tiers). ~5% is genuinely new and design-first: establishing a STRANGER's
> trustworthiness when there is no shared enrollment authority, plus marketplace-grade licensing /
> attribution. The moat is in that 5%; the reused 80% is necessary but not defensible.
> (artifact-system-and-registry.md §6.3, §8; roadmap §9.4.)
>
> **The supply-chain problem, named precisely.** This is NOT the marketplace-quality problem ("is
> this recipe any good?"). It is the supply-chain problem: when company B runs company A's recipe, B
> is running A's instructions inside B's own agent against B's connected systems, WITH B's authority.
> A careless or malicious A could exfiltrate data, skip a compliance step, or take an action B never
> intended. No shipping product solves this. (roadmap §9.1; artifact-system-and-registry.md §8.1,
> §9.1.)

---

## Dependency and sharding posture for this milestone

- **The trust-model DESIGN gates the cross-org BUILD and the registry surface — this is a hard gate,
  decided here at /todos time.** M5-1 (the design deliverable) MUST land and be reviewed before any
  cross-org publish/subscribe code (M5-6) or registry surface (M5-7, M5-8) starts. The design is a
  written, reviewed document, not code; its acceptance is "a human reviewed it and it answers every
  falsifier below." (roadmap §9.2, §9.5; plan 01 §6.4.)
- **Within-org sharing (M5-2, M5-3, M5-4) depends on NOTHING new** and can ship in parallel with, or
  ahead of, the trust-model design. The loom machinery already handles bounded-trust within one org;
  these todos are re-pointing and a non-coder review surface, not invention. (roadmap §9.2; plan 01
  §6.4; artifact-system-and-registry.md §4.)
- **The trust model is greenfield novel architecture** — apply the ~2–3× first-session factor. The
  registry surface is ~3–5 cycles, but ONLY counted AFTER the design lands. Do not fold the design
  effort and the registry effort into one estimate. (roadmap §9.5; plan 01 §6.4.)
- **Default-deny is the load-bearing invariant on the consume path, and it taxes the very engine M4
  depends on — this trade-off is real and must NOT be glossed.** Every per-envelope approval gate is
  a place adoption can leak; default-deny + per-envelope approval adds friction exactly where the
  network effect needs flow. Trust-by-reputation is rejected anyway, because the first high-reputation
  poisoned recipe is the category-defining incident. The design todo MUST state this con symmetrically.
  (roadmap §9.5; artifact-system-and-registry.md §9.1 "honest limit".)
- **The cross-org channel deliberately crosses the tenant boundary — `tenant_id` isolation is
  necessary but INSUFFICIENT here.** Every other channel in the platform is tenant-sealed; this is the
  one channel that is meant to be permeable. So tenant-isolation-by-`tenant_id` MUST be paired with an
  explicit, net-new cross-tenant-grant model on this one channel. Getting permeability wrong in either
  direction is fatal: too sealed kills the flywheel, too permeable ends the company on one leak.
  (roadmap §9.3; artifact-system-and-registry.md §9.5; `tenant-isolation.md`.)
- **Orphan-detection / facade-manager discipline applies.** Any `*Registry` / `*Store` / `*Service`-
  shaped class (the publish/subscribe surface, the intake fence) MUST land with a production call site
  on the real consume path + a Tier-2 wiring test in the same change — never a facade with no caller.
  (plan 01 §6.4; `orphan-detection.md`, `facade-manager-detection.md`.)
- **BUILD and WIRE are SEPARATE todos throughout.** The intake fence engine, its wiring into the
  consume path, and the registry UI surface are distinct deliverables.

---

### M5-1 — DESIGN: the untrusted-publisher trust model (the gating deliverable)

- **Type:** DESIGN
- **Implements:** specs/artifact-system-and-registry.md §8 (+ plan: 02-plans/01 §6.3–§6.4; roadmap §9.1–§9.3)
- **What:** Produce a written, reviewed design (NOT code) for how a consuming org safely runs a
  recipe published by an untrusted external org. The design MUST specify, with worked examples: (a)
  the **capability-envelope declaration** — every cross-org recipe declares the tool/clearance
  envelope it needs (which systems, which data classes, which actions); (b) the **posture-gated
  intake** — the consumer's posture (M2) decides whether the declared envelope is auto-granted or
  human-approved; (c) the **default-deny intake fence** — a recipe cannot escalate beyond its declared
  envelope at runtime, full stop; (d) the **mechanical over-broad-scope detector** — how intake review
  flags "this 'format a report' recipe also wants write-access to the payments system"; (e) the
  **cross-tenant-grant model** — the explicit grant that permits the one channel that crosses the
  tenant boundary, since `tenant_id` isolation alone is insufficient; (f) **external-publisher
  provenance** — what can be cryptographically proven about a stranger (published-by-verified-org,
  authored-by-verified-person, captured-from-real-work, usage/recall history) when there is no shared
  roster; (g) **recall-reaches-all** — recall must purge from every consumer regardless of the trust
  posture they ran under. The design MUST state symmetric cons (default-deny taxes the network effect;
  capability-scoping can be technically narrow yet practically broad — a "format a report" recipe that
  legitimately needs ERP read access).
- **Reuses → Builds:** loom crypto substrate (commit-signing keys, hash-chained coordination log,
  2-of-N quorum, `refs/coc/**` rulesets); recall / obsoletion primitive (production-grade); Gate-1
  human-classify intake as the supply-chain fence; disclosure-scrub on intake; aegis fork-relationship
  asymmetry (upstream-generic-only, client-data-never-leaks-down) as the governance shape → external-
  publisher provenance, the cross-tenant-grant model, the default-deny intake fence, and the
  mechanical over-broad-scope detector. The crypto primitives are a strong starting point; binding a
  STRANGER's signed provenance to a trust root the consumer recognizes (no shared enrollment) is the
  net-new design.
- **Invariants:** default-deny on the consume path (a recipe runs ONLY against its declared, consumer-
  approved envelope); capability-scoped recipes (no runtime escalation past the declared envelope);
  recall-reaches-all consumers; tenant-isolation by `tenant_id` PLUS an explicit cross-tenant-grant on
  the one channel that crosses the boundary; the agent that runs a recipe is a producer, never an
  authority — a human always gates placement.
- **Sizing:** ~2–3 cycles (greenfield novel architecture; first-session ~2–3× factor applies; this is
  design, not code, but it is the load-bearing 5%). SHARD only if the cross-tenant-grant model and the
  intake-fence design diverge enough to need separate review passes.
- **Depends on:** nothing new (it consumes the existing crypto substrate + M2 posture as inputs). This
  design GATES M5-6, M5-7, M5-8 (the cross-org build + registry). Note: it does NOT gate the within-org
  todos (M5-2 through M5-4).
- **Acceptance (confirm / falsify):** **Confirms** — a reviewer can read the design and answer each of
  (a)–(g) above with a concrete mechanism, and the intake fence is shown to mechanically detect an
  over-broad scope request (the 'format a report' recipe wanting payments write-access) on a worked
  example. **Falsifies** — intake cannot mechanically detect over-broad scope (the fence is then
  unenforceable), OR capability-scoping is too coarse for heterogeneous enterprise systems (a recipe's
  declared-but-practically-broad envelope makes default-deny meaningless), OR the cross-tenant-grant
  model is left as "tenant_id handles it" (it does not — this channel crosses the boundary by design).
  Human review gate: a named human confirms the design answers every falsifier before any cross-org
  code starts.

---

### M5-2 — BUILD: re-point the artifact taxonomy + proposal lifecycle to general work (within-org)

- **Type:** BUILD
- **Implements:** specs/artifact-system-and-registry.md §1, §3 (+ plan: 02-plans/01 §6.2; roadmap §9.2)
- **What:** Generalize the five-layer artifact taxonomy (skills / rules / commands / agents / hooks)
  and the proposal lifecycle so they carry BUSINESS-domain know-how (month-end close, client
  onboarding) instead of only codegen artifacts. De-couple the word "codegen" from the tier
  vocabulary. The proposal lifecycle (pending_review → reviewed → distributed), append-never-overwrite,
  and the authoring lease are reused unchanged; only the domain vocabulary generalizes.
- **Reuses → Builds:** loom five-layer artifact system; proposal lifecycle; append-never-overwrite;
  authoring lease (`codify-lease.js`) → the same machinery carrying business-domain artifacts (a
  mechanical manifest/overlay change, no architectural change).
- **Invariants:** append-never-overwrite (no version silently destroyed); the author never writes code
  (artifacts captured from observed work); the agent drafts, a human approves (no autonomous catalog
  entry); trust class travels with the artifact; tenant-isolation on all per-org artifact storage.
- **Sizing:** ~1 cycle (mechanical re-pointing; high feedback loop). No shard.
- **Depends on:** nothing new (within-org needs no trust model — the bounded-trust machinery already
  handles one org).
- **Acceptance (confirm / falsify):** **Confirms** — a non-codegen process (e.g. "onboard a new
  client" as a command + a billing-guardrail rule) is captured, stored through the proposal lifecycle,
  and a second edit produces version 2 with version 1 preserved. **Falsifies** — the taxonomy cannot
  hold a non-codegen process without a code-shaped escape hatch, or an edit overwrites a prior version.
  Real-infra Tier-2 test + a user-facing walk: capture a process, edit it, confirm version 1 survives.

---

### M5-3 — BUILD: the non-coder plain-language change-review surface (within-org)

- **Type:** BUILD
- **Implements:** specs/artifact-system-and-registry.md §2.2 (+ plan: 02-plans/01 §6.2; roadmap §9.2; user-flow 04 §2.3)
- **What:** Build the surface where a non-coder reviews and edits a captured artifact as
  plain-language steps and boundaries — NEVER as code or a git diff. Each step and each boundary is
  individually editable, addable, removable. Provenance (who captured it, from which session, which
  verified person, which org) is auto-filled and un-fakeable. Two save dispositions: "Save as draft"
  (private) and "Save & make available to my team" (enters within-org distribution). The same surface
  handles modifications: a teammate's correction appears in the same plain-language form, attributed,
  and the owner accepts / declines / asks-for-clarification — acceptance produces a new version.
- **Reuses → Builds:** the codify-from-observed-work loop (captures the artifact draft); signed
  provenance substrate (the un-fakeable "who/how" stamp) → the genuinely-new plain-language
  authoring/review UI (today artifacts are reviewed as git diffs by engineers — exactly what a
  non-coder cannot do).
- **Invariants:** the author never writes code (plain-language only, never a diff); provenance is
  auto-filled and un-fakeable; agent drafts, human approves; acceptance produces a new version, never
  an overwrite; tenant-isolation on the per-org artifact corpus.
- **Sizing:** ~2–3 cycles (net-new UX; the largest within-org net-new piece). SHARD into capture-
  review vs modification-review if the two review flows diverge.
- **Depends on:** M5-2 (the generalized taxonomy the surface renders). Nothing else new.
- **Acceptance (confirm / falsify):** **Confirms** — a non-coder, in a usability walk, reviews a
  captured artifact as plain-language steps, edits one step and one boundary, sees the auto-filled
  provenance, and saves it for their team — without seeing any code or diff. A teammate's correction
  later appears in the same form and produces version 2 on acceptance. **Falsifies** — the non-coder
  is shown a diff or code at any point, or cannot complete an edit without engineering help.
  User-facing walk with receipts (per `user-flow-validation.md`).

---

### M5-4 — BUILD + WIRE: within-org distribution via the splitter + org-axis variant overlays

- **Type:** BUILD
- **Implements:** specs/artifact-system-and-registry.md §4.1, §4.4, §5.1 (+ plan: 02-plans/01 §6.4; roadmap §9.2)
- **What:** Wire within-org discovery (a teammate states intent; the platform surfaces a matching
  saved artifact via the semantic `description:` field) and the org-default-vs-team-override variant
  overlay axis (`variants/<team>/rules/foo.md` overrides `rules/foo.md`). One team runs the org-default
  process while another overrides one boundary and inherits every other step. The loom splitter IS the
  share-across-teams engine; this is re-pointing its overlay axis from language×CLI to
  org-default×team-override, which is mechanically identical to adding an axis.
- **Reuses → Builds:** loom two-gate splitter (the artifact control plane); variant-overlay engine
  (replacement / addition / base-only semantics); the `description:`-as-discovery semantic-match
  primitive → the org-axis overlay + within-org discovery surface.
- **Invariants:** distribution is additive-with-obsoletion (consumer-local overrides preserved; only
  declared-obsolete paths purge); the splitter is the only outbound path; overlay is asymmetric
  (improvements flow up to the org-default, team overrides never leak sideways); tenant-isolation on
  the per-org corpus.
- **Sizing:** ~1 cycle (mechanical axis addition; high feedback loop). No shard.
- **Depends on:** M5-2, M5-3. Nothing else new (within-org needs no trust model).
- **Acceptance (confirm / falsify):** **Confirms** — a teammate states intent and the platform
  surfaces a matching saved artifact; one team overrides a single boundary on the org-default and
  inherits every other step; when the org-default improves, the overriding team gets the improvement
  without losing its override. **Falsifies** — discovery fails to surface a matching artifact, or a
  team override is lost when the base improves, or an override leaks to a team that did not set it.
  Real-infra Tier-2 + a user-facing walk: two teams, one shared org-default, one override, one upstream
  improvement.

---

### M5-5 — WIRE: re-point the disclosure-scrub + recall primitives to the org boundary

- **Type:** WIRE
- **Implements:** specs/artifact-system-and-registry.md §5.3, §9.2 (+ plan: 02-plans/01 §6.2; roadmap §9.4)
- **What:** Point the existing intake disclosure-scrub at the ORG boundary (strip client names,
  internal system paths, credentials, employee PII before an artifact leaves the org — scanner pass +
  human body-scrub, halt on any finding) and confirm the recall / obsoletion primitive purges a
  recalled artifact from every consumer on next pull while preserving each consumer's local overrides.
  These primitives already exist and run; this todo wires them to the org boundary and proves them on
  the org-exchange path. The recall keystone must be proven BEFORE cross-org opens, because a
  marketplace that lets strangers publish must be able to un-publish instantly and universally.
- **Reuses → Builds:** disclosure-scrub on intake (production-grade); recall / obsoletion primitive
  ("the ONLY mechanism by which 30+ downstream repos purge stale artifacts") → both re-pointed and
  proven on the org-exchange path.
- **Invariants:** disclosure-scrub runs FIRST, before placement (Gate-1 placement enters permanent
  history before Gate-2; scrubbing at output is partial-after-the-fact); recall is single-declarative
  and universal; recall preserves consumer-local overrides; recall-reaches-all regardless of posture.
- **Sizing:** ~1 cycle (wiring + proving existing primitives). No shard.
- **Depends on:** M5-4 (the within-org distribution path the scrub/recall guard). Independent of the
  trust-model design (these are the reused 80%).
- **Acceptance (confirm / falsify):** **Confirms** — a candidate artifact with a client name is halted
  at intake until genericized; a recall marks a version un-runnable on every consumer's next pull,
  offers a named safe replacement, and preserves a consumer's local override. **Falsifies** — the
  scrub lets a client name through, or a recall fails to reach a consumer / destroys its override.
  Real-infra Tier-2: scrub-halt-on-finding + recall-purges-all-preserving-overrides, with read-back.

---

### M5-5a — TEST: the recall keystone wiring test (recall-purges-from-all + preserves-non-recalled)

- **Type:** TEST
- **Implements:** specs/artifact-system-and-registry.md §5.3, §9.2 (+ plan: 02-plans/01 §6.2; roadmap §9.4; `facade-manager-detection.md`, `orphan-detection.md`)
- **What:** Add a dedicated Tier-2 regression test for the recall keystone — the primitive that gates
  cross-org. Because recall is the keystone the entire cross-org marketplace depends on (a marketplace
  that lets strangers publish MUST be able to un-publish instantly and universally), it owes a separate
  wiring test of its own — exactly as the M1 manager-shape classes owe Tier-2 wiring tests per
  `facade-manager-detection.md`. The test MUST exercise, against real infrastructure: (a) a recall
  PURGES the recalled artifact from EVERY consumer on next pull (multi-consumer fan-out, not a single
  consumer); (b) a recall PRESERVES every non-recalled artifact AND every consumer's local overrides
  (the recall does not over-purge); (c) recall-reaches-all regardless of the trust posture each consumer
  ran under. This is the regression that catches a recall that silently misses a consumer or destroys a
  non-recalled artifact / override.
- **Reuses → Builds:** the M5-5 wired recall/obsoletion path → a dedicated multi-consumer Tier-2
  regression test asserting the externally-observable purge + preservation effects.
- **Invariants:** recall purges from ALL consumers (no consumer silently missed); recall preserves
  non-recalled artifacts AND consumer-local overrides; recall-reaches-all regardless of posture;
  tenant-isolation honored across the multi-consumer fan-out.
- **Sizing:** ~1 cycle (test-only, over the M5-5 wired path; high feedback loop). No shard.
- **Depends on:** M5-5 (the wired recall path the test exercises). Gates cross-org per the keystone
  ordering — the recall wiring test MUST be green BEFORE cross-org opens (M5-6/M5-7/M5-8).
- **Acceptance (confirm / falsify):** **Confirms** — the test sets up ≥2 consumers, recalls one
  artifact, and asserts on next pull that the recalled artifact is un-runnable on EVERY consumer while
  every non-recalled artifact AND every consumer's local override survives intact, across differing
  postures. **Falsifies** — the test passes when a recall misses a consumer, OR when a recall destroys a
  non-recalled artifact / override, OR when posture changes the recall's reach. Real-infra Tier-2,
  multi-consumer fan-out, with read-back.

---

### M5-6 — BUILD: the default-deny intake fence + capability-envelope enforcement (cross-org)

- **Type:** BUILD
- **Implements:** specs/artifact-system-and-registry.md §8.2–§8.3, §9.1 (+ plan: 02-plans/01 §6.4; roadmap §9.3)
- **What:** Implement the default-deny intake fence from the M5-1 design: a consumed cross-org recipe
  declares its required tool/clearance envelope; the fence enforces that the recipe runs ONLY against
  the declared, consumer-approved scopes and cannot escalate at runtime; and intake review mechanically
  detects an over-broad scope request (the 'format a report' recipe also wanting payments
  write-access). An unverified-publisher recipe runs locked at the most-cautious posture in a
  restricted sandbox against test data first. This is the net-new 5% — build it strictly from the
  reviewed M5-1 design, not from scratch.
- **Reuses → Builds:** M2 posture model (the consumer-side brake applied at the install boundary);
  loom crypto substrate; the Gate-1 human-classify intake → the default-deny fence, the
  capability-envelope runtime enforcement, and the mechanical over-broad-scope detector.
- **Invariants:** default-deny on the consume path; capability-scoped recipes (no runtime escalation
  past the declared envelope); unverified publishers sandboxed and locked to the most-cautious posture;
  the consumer-side brake is a default not a lock (state this honestly — a consumer who raises every
  unvetted recipe to autonomous defeats it); tenant-isolation + cross-tenant-grant on the channel.
- **Sizing:** ~3–5 cycles (net-new, load-bearing). SHARD: (1) capability-envelope declaration +
  runtime enforcement; (2) the mechanical over-broad-scope detector; (3) the unverified-publisher
  sandbox + locked-posture path. Each shard carries default-deny + tenant-isolation in its invariant
  list.
- **Depends on:** **M5-1 (the design — HARD GATE; this todo cannot start until the design lands and is
  reviewed).** Also M2 posture model.
- **Acceptance (confirm / falsify):** **Confirms** — a consumed recipe runs ONLY against its
  declared + consumer-approved scopes and is blocked when it attempts an undeclared action; intake
  mechanically flags a 'format a report' recipe that also requests payments write-access; an unverified
  recipe runs sandboxed against test data, locked to the most-cautious posture. **Falsifies** — a
  recipe escalates past its declared envelope at runtime, OR intake fails to detect the over-broad
  scope, OR an unverified recipe can be raised to autonomous on first run. Real-infra Tier-2 +
  user-facing walk with receipts: declare an envelope, attempt an out-of-envelope action, confirm the
  block.

---

### M5-7 — BUILD: external-publisher provenance + cross-tenant-grant + licensing/attribution (cross-org)

- **Type:** BUILD
- **Implements:** specs/artifact-system-and-registry.md §8.2, §8.4, §8.5, §9.3 (+ plan: 02-plans/01 §6.2; roadmap §9.4)
- **What:** Build signed-artifact provenance from an EXTERNAL publisher (versus an enrolled operator):
  what a consumer can verify about a stranger (verified-org, verified-person, captured-from-real-work,
  usage/recall history) anchored to the consuming tenant's own identity provider rather than a shared
  remote. Build the explicit cross-tenant-grant model that permits the one channel that crosses the
  tenant boundary. Build marketplace-grade licensing/attribution (free / paid / attribution-required),
  including the license-conflict resolution on a derived (variant-overlaid) artifact, per the M5-1
  design.
- **Reuses → Builds:** loom crypto substrate (signing, hash-chained log, quorum, rulesets); aegis
  fork-relationship asymmetry (upstream-generic-only, client-data-never-leaks-down) → external-
  publisher provenance, the cross-tenant-grant model, and the licensing/attribution mechanism.
- **Invariants:** tenant-isolation by `tenant_id` PLUS the explicit cross-tenant-grant on this one
  channel (necessary-but-insufficient `tenant_id` alone); overlay is asymmetric (improvements flow up
  to the generic; org-specific data never leaks down or out via a derivative); two-level attribution
  composes across a re-published variant; recall-reaches-all.
- **Sizing:** ~3–5 cycles (net-new). SHARD: (1) external-publisher provenance + IdP anchoring; (2) the
  cross-tenant-grant model; (3) licensing/attribution + derived-artifact conflict resolution.
- **Depends on:** **M5-1 (the design — HARD GATE).** Also M5-6 (the fence the provenance grade gates).
- **Acceptance (confirm / falsify):** **Confirms** — a consumer can see what is provable about an
  external publisher (verified-org / verified-person / captured-from-real-work / usage history); the
  cross-tenant-grant explicitly permits the boundary-crossing channel and nothing else; a derived
  artifact carries the base's attribution forward and a free-derivative-of-paid-base is blocked at
  re-publish. **Explicit cross-org MODIFY case (brief §3g lists "modified" across orgs):** a consuming
  org MODIFIES a consumed EXTERNAL recipe (variant-overlays / edits a recipe authored by a different
  org) and republishes the result as a derivative under the trust model — the derivative carries BOTH
  the upstream external base's attribution/license AND the modifying org's own provenance forward; the
  base publisher's license terms (e.g. attribution-required, or a paid-base block on a free derivative)
  are honored on the cross-org republish; and a later recall of the EXTERNAL base reaches the derivative
  (recall-reaches-all composes across the cross-org modify-and-republish). **Falsifies** — a stranger's
  provenance cannot be bound to a trust root the consumer recognizes, OR the cross-tenant channel works
  without an explicit grant (silent permeability), OR a derived artifact strips the base's license, OR a
  cross-org MODIFIED-and-republished derivative loses the external base's attribution/license or escapes
  the external base's recall. Real-infra Tier-2 + walk: verify a publisher, grant the channel, modify an
  external recipe, re-publish the derivative, and confirm attribution + license + recall-reach survive
  across the org boundary.

---

### M5-8 — BUILD + WIRE: the cross-org registry surface (publish / subscribe / discover)

- **Type:** BUILD
- **Implements:** specs/artifact-system-and-registry.md §5.1, §5.4, §6.2 (+ plan: 02-plans/01 §6.4; roadmap §9.4)
- **What:** Build the thin publish/subscribe + discovery surface ON TOP of the splitter (the registry
  is loom-with-a-discovery-surface-bolted-on, not a rewrite). Generalize tier subscriptions from
  language/CLI tiers to work-domain tiers (finance, legal, ops) and the subscription block to a
  cross-org subscription registry (org-A-authors → org-B-consumes with no shared remote). The catalog
  shows, per artifact: publisher (verified-org flag), usage count, recall count, trust class, license,
  provenance summary, rating. Wire the registry to consume the M5-6 fence and M5-7 provenance — a
  recipe is only installable through the fence, only after its provenance grade is shown.
- **Reuses → Builds:** loom splitter (the artifact control plane); the `description:`-as-discovery
  semantic-match foundation; tier-subscription mechanism → the cross-org publish/subscribe surface +
  the discovery/search catalog.
- **Invariants:** the splitter is the only outbound path (no second outbound channel); default-deny on
  the consume path (install only through the M5-6 fence); recall-reaches-all on next pull;
  tenant-isolation + cross-tenant-grant; unverified publishers surfaced loudly in the catalog.
- **Sizing:** ~3–5 cycles (registry surface, counted ONLY after M5-1 design lands). SHARD: (1) the
  publish/subscribe data path; (2) the discovery/search catalog UI.
- **Depends on:** \*\*M5-1 (design — HARD GATE), M5-6 (the fence), M5-7 (provenance + cross-tenant-grant
  - licensing).\*\* The registry is the last thing built, because every prior piece constrains its shape.
- **Acceptance (confirm / falsify):** **Confirms** — an org publishes a recipe; a different org with no
  shared remote discovers it via the catalog (seeing publisher-verified flag, usage, recalls, trust
  class, license), installs it ONLY through the default-deny fence, runs it within its declared
  envelope, and receives a recall on next pull if the publisher issues one. **Falsifies** — a recipe is
  installable bypassing the fence, OR discovery cannot surface a cross-org recipe with no shared
  remote, OR a recall fails to reach a cross-org consumer. Real-infra Tier-2 + a full user-facing walk
  with receipts: publish → discover → install-through-fence → run-in-envelope → recall-reaches-consumer.
