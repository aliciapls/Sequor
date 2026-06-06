# Red-Team Findings — Target-State Platform Specs

**Scope.** The seven target-state platform specs (`platform-overview`, `transparency-and-provenance`, `intervention-and-versioning`, `trust-posture-and-governance`, `coordination-and-teams`, `artifact-system-and-registry`, `connectors-and-integration`) + `specs/_index.md`, cross-checked against `briefs/01-vision.md`, the analysis (`01-analysis/`), the plans (`02-plans/`), the user flows (`03-user-flows/`), and the shipped comms-wedge specs.

**Method.** Read all 7 platform specs + index in full; read the brief; mechanically verified sibling-spec references, the L1–L5 numbering, the Step/Output/Decision model, the six invariants, status blockquotes, index completeness, and net-new markings via `grep`/`ls`. Findings carry ID, severity, exact location, defect, impact (why), and fix. Honesty already present in the specs is rewarded (§ "Honesty already present"), not re-flagged.

**Bottom line.** The seven specs are genuinely DETAILED authorities (not thin summaries) — each carries flows, contracts, invariants, edge cases, and explicit REUSE/NET-NEW dispositions. The TARGET-STATE blockquote is present on all 7. The index is complete (7 platform + 7 comms, two labeled sections, no comms spec dropped). The net-new parts (M1 cascade engine, untrusted-publisher trust model) are honestly marked. BUT there is one **systemic BLOCKING defect** — the entry-point spec routes all 7 layers to detailed sibling specs **whose filenames do not exist** — plus a **HIGH terminology collision** (two different "L1–L5" scales used unqualified, including inside one spec) and **HIGH cross-spec content duplication** between the transparency and intervention specs that re-opens the full-sibling-drift hazard `specs-authority.md` Rule 5b exists to close.

---

## BLOCKING

### B1 — `platform-overview.md` routes every layer to a sibling spec filename that does not exist (15 dangling references across 4 specs)

**Location.** `specs/platform-overview.md` §4 (all seven layer summaries, lines 95–113); also `connectors-and-integration.md` §intro+§7.1+§7.5+invariant-8+§8.1+open-decisions; `artifact-system-and-registry.md` §6.1+§sources; `transparency-and-provenance.md` §8.

**What's wrong.** The entry-point spec ends each of its seven layer summaries with "→ _Detailed sibling spec: `<name>.md`_". **Every one of those seven filenames is wrong** — none exists on disk:

| platform-overview cites     | actually exists as                                                  |
| --------------------------- | ------------------------------------------------------------------- |
| `work-interface.md`         | (no file — L7 has no detailed spec at all)                          |
| `orchestration-runtime.md`  | (no file — L2 has no detailed spec at all)                          |
| `governance-substrate.md`   | `trust-posture-and-governance.md`                                   |
| `provenance-cascade.md`     | `transparency-and-provenance.md` + `intervention-and-versioning.md` |
| `coordination-substrate.md` | `coordination-and-teams.md`                                         |
| `artifact-registry.md`      | `artifact-system-and-registry.md`                                   |
| `connector-layer.md`        | `connectors-and-integration.md`                                     |

`connectors-and-integration.md` compounds it: its intro and §7/§8 cite `specs/orchestration-runtime.md`, `specs/governance-substrate.md`, `specs/provenance-and-versioning.md`, `specs/artifact-system.md`, and `specs/record-model.md` — **all dangling** (the real names are `trust-posture-and-governance.md`, `transparency-and-provenance.md`/`intervention-and-versioning.md`, `artifact-system-and-registry.md`; `orchestration-runtime.md` and `record-model.md` do not exist at all). `artifact-system-and-registry.md` cites `specs/artifact-system.md` (its own non-existent short name). Total: **15 distinct dangling `*.md` references** (`work-interface`, `orchestration-runtime`, `governance-substrate`, `provenance-cascade`, `coordination-substrate`, `artifact-registry`, `connector-layer`, `provenance-and-versioning`, `artifact-system`, plus the future-split names `posture-governance`, `cascade-engine`, `record-model`, `untrusted-publisher-trust`, `marketplace-registry`, `artifact-authoring`).

**Why it matters.** `specs-authority.md` Rule 1 requires `_index.md` + working cross-references so phases "read `_index.md` to find relevant files, then read only those." `spec-accuracy.md` MUST Rule 1 requires every cited reference to resolve at merge. Here the **single entry-point spec — the one a `/implement` or `/todos` agent reads first to navigate the domain — points every navigation arrow at a 404.** An agent following "→ detailed sibling spec `governance-substrate.md`" reads nothing, then either (a) silently proceeds on the overview's thin summary (the exact alignment-drift FM-5 specs-authority exists to prevent), or (b) burns a cycle discovering the real filename. Two of the seven layers (L7 Work Interface, L2 Orchestration Runtime) have **no detailed spec at all** — yet the overview promises one ("→ Detailed sibling spec: `work-interface.md`" / "`orchestration-runtime.md`"), so the missing-spec gap is disguised as a naming typo. This is a structural lie about the spec set's own shape.

**Fix.** (1) Rewrite all seven platform-overview layer pointers to the real filenames; for L7 and L2, replace the false "→ Detailed sibling spec" promise with an honest "→ no detailed sibling spec yet (TARGET-STATE gap — owed)". (2) Sweep `connectors-and-integration.md` and `artifact-system-and-registry.md` for the dangling `specs/*.md` references and repoint them. (3) Add a `_index.md`-driven verification step (or a redteam grep) asserting every `specs/*.md` reference resolves. (4) For the future-split names (`posture-governance`, `cascade-engine`, `record-model`, etc.), keep them but mark them explicitly as _proposed future split targets, not yet created_ so they are not mistaken for existing siblings (see also H3).

---

## HIGH

### H1 — Two different "L1–L5" scales used unqualified across the spec set (and inside a single spec), with no disambiguation in the entry-point spec

**Location.** `platform-overview.md` §4 (L1–L7 = architectural LAYERS) vs §3 governance line + §5 moat-table M2 row (L1–L5 / "L3/L4/L5" = POSTURE rungs); `intervention-and-versioning.md` line 7 ("posture-graded governance (L3/L4/L5)"); `connectors-and-integration.md` §5.2/§7.2 ("L5/AUTONOMOUS", "locked at L3"); `trust-posture-and-governance.md` §1.1 (the canonical reconciliation that the others ignore).

**What's wrong.** The platform uses **"L<n>" for two completely different ordered scales**:

- **Architectural layers** — `platform-overview.md` §4 names them L1 (Connector) → L2 (Runtime) → L3 (Governance) → L4 (Provenance) → L5 (Artifact) → L6 (Coordination) → L7 (Work Interface).
- **Posture rungs** — `trust-posture-and-governance.md` §1 names L1 (Pseudo) → L2 (Tool) → L3 (Supervised) → L4 (Delegating) → L5 (Autonomous).

These collide head-on. In `platform-overview.md` §5 the M2 moat row reads "Execution-time, posture-graded governance **(L3/L4/L5)**" — here L3/L4/L5 means **postures** (Supervised/Delegating/Autonomous) — but three rows of the _same table_, and §4 of the _same spec_, use L3/L4/L5 to mean **layers** (Governance/Provenance/Artifact). A reader cannot tell which L3 is meant without already knowing the answer. `intervention-and-versioning.md` line 7 propagates the ambiguity ("posture-graded governance (L3/L4/L5)"). `connectors-and-integration.md` writes "L5/AUTONOMOUS" and "locked at L3" (posture sense) in a spec whose own home layer is "L1" (layer sense, per the overview's "This spec is the L1 connector layer").

Critically, `trust-posture-and-governance.md` §1.1 **already pins the binding resolution**: "the canonical EATP five-rung enum is the internal source of truth; the brief's L3/L4/L5 labels MUST NOT be shipped as the enum... Shipping the brief's labels... confuses every reader who knows the existing system." Yet the entry-point spec and the intervention spec do exactly that — float "L3/L4/L5" as if it were a settled posture label — and the overview adds the second, conflicting layer scale on top.

**Why it matters.** This is the spec-authority full-sibling concern made concrete: the same token (`L3`) denotes two different things across siblings, and the authority spec (`trust-posture-and-governance.md` §1.1) that resolves it is contradicted by the navigation spec (`platform-overview.md`) that every reader hits first. A `/todos` agent reading "posture-graded governance (L3/L4/L5)" in the moat table cannot know if "L3" is the Governance layer or the Supervised posture — and the trust-posture spec explicitly says the L3/L4/L5 posture labels MUST NOT ship. This is the precise "cross-spec terminology drift" failure mode.

**Fix.** (1) In `platform-overview.md`, stop using bare "L1–L5" for postures. The M2 row should read "posture-graded governance (the 3-button control over the L1–L5 _posture_ ladder)" and explicitly disambiguate layer-L vs posture-L the first time both appear (e.g., a one-line note: "Architectural layers are L1–L7; the posture ladder is a separate L1–L5 scale — see `trust-posture-and-governance.md` §1.1"). (2) In `intervention-and-versioning.md` line 7, replace "posture-graded governance (L3/L4/L5)" with "posture-graded governance (the L1–L5 posture ladder)" — never the brief's bare L3/L4/L5. (3) Adopt `trust-posture-and-governance.md` §1.1's resolution everywhere: surface the three buttons (Go ahead / Ask me once / Step through) in prose; reserve bare "L<n>" for the canonical posture enum and qualify it as "posture L<n>" wherever a layer "L<n>" could be confused.

### H2 — Transparency and intervention specs DUPLICATE the data model, the determinism table, and the six invariants verbatim instead of one owning + one referencing (full-sibling drift hazard)

**Location.** `transparency-and-provenance.md` §2.1 (three node kinds), §2.2 (typed edges), §2.3 (content-addressing), §2.4 (versioned nodes), §2.6 (six invariants), §4 (determinism Re-run/Replay/Branch table) **≈ duplicated in** `intervention-and-versioning.md` §2.1, §2.2, §2.3, §2.4, §6.1 (same determinism table), §7 (same six invariants).

**What's wrong.** Both specs carry the **same Step/Output/Decision node table, the same five typed edges, the same content-addressing formula, the same six invariants (Immutability / Tenant-isolation / Determinism-boundary / Cascade-minimality / Posture-at-time / Audit-completeness), and the same three-row determinism table** — as full restatements, not references. The six-invariant blocks are near-verbatim copies (transparency §2.6 vs intervention §7). `specs-authority.md` Rule 9 says workspace specs should reference canonical artifacts rather than restate; more importantly Rule 5b mandates that any spec edit triggers full-sibling re-derivation because "same concept named two ways" and "field-shape divergence" emerge only from the full sweep — and these two specs are already drifting:

- **Step field-shape divergence (already present).** Transparency's Step table lists `step_id (content hash)` and `run_id` as load-bearing fields; intervention's Step table **omits both** `step_id` and `run_id`. Same node, two different field lists.
- **Cosmetic identity-formula drift.** Transparency: `step_id = hash(inputs_hash + prompt_ref/code_ref + sorted(dependency_step_hashes))`. Intervention: `step_identity = hash(inputs_hash + code_or_prompt_ref + sorted(dependency_step_hashes))`. Same intent, two names (`step_id` vs `step_identity`; `prompt_ref/code_ref` vs `code_or_prompt_ref`).

**Why it matters.** This is exactly the two-source-of-truth condition `specs-authority.md` Rule 5b was written for: "editing one dataclass without re-deriving the full sibling set lets narrow-scope APPROVE verdicts ship with silent cross-spec drift." The next `/implement` shard that adds a field to the Step model in one spec will silently diverge from the other; a reader citing "the Step's load-bearing fields" gets a different answer depending on which spec they opened. The `step_id`/`run_id` omission is the drift _already manifest_.

**Fix.** Designate ONE owner for the shared provenance data model — `transparency-and-provenance.md` is the natural owner (it self-describes as "the data model" authority in §2). `intervention-and-versioning.md` should reference it by section pointer ("the Step/Output/Decision model + six invariants are owned by `transparency-and-provenance.md` §2; this spec consumes them") and keep only what is unique to it (the cascade mechanism §4, retrace §3, irreversibility §8.3). Reconcile the Step field list (add `step_id`/`run_id` to intervention or, preferably, delete intervention's copy and reference). Align the identity-formula token (`step_id` vs `step_identity`).

### H3 — `transparency-and-provenance.md` §8 "domain split note" describes a split as FUTURE that has ALREADY HAPPENED under different names

**Location.** `transparency-and-provenance.md` §8 (lines 242–249).

**What's wrong.** §8 reads: "If it grows past ~400 lines, the natural split per `specs-authority.md` Rule 8 **is**: ... `intervention-and-versioning.md` — §4 determinism + cascade...; `posture-governance.md` — §5 fan-out + the L3/L4/L5 ladder...". But `intervention-and-versioning.md` **already exists as a full 277-line sibling**, and the governance domain **already exists as `trust-posture-and-governance.md`** (NOT `posture-governance.md`, which does not exist). The note frames as a _prospective_ split what is already a _completed_ split — and names a non-existent file (`posture-governance.md`) as the target.

**Why it matters.** A reader takes §8 at face value: "these domains live in this file until it grows, then they'll split out." False — they already live in separate, fully-written siblings, and §4/§5/§6/§2 are duplicated across them (H2). The note actively misleads about the spec set's structure and re-asserts the dangling `posture-governance.md` name (B1). It also conflicts with §7 of the same spec, which references the determinism content as owned here, while §8 says it will be split out.

**Fix.** Rewrite §8 to past tense and correct names: "The intervention/determinism/cascade domain IS split out into `intervention-and-versioning.md`; the posture/governance domain IS owned by `trust-posture-and-governance.md`. This file is the provenance + transparency authority and references those siblings by contract point." Resolve the H2 duplication consistent with this corrected ownership statement.

---

## MEDIUM

### M1 — `intervention-and-versioning.md` is missing a top H1 title above the status blockquote (status line is line 1, title is line 3)

**Location.** `intervention-and-versioning.md` lines 1–3; same pattern in `coordination-and-teams.md` and `connectors-and-integration.md`.

**What's wrong.** Three of the seven specs put the `> Status: TARGET-STATE` blockquote as **line 1**, with the `# Title` on line 3. The other four (`platform-overview`, `transparency-and-provenance`, `trust-posture-and-governance`, `artifact-system-and-registry`) put the `# Title` on line 1 and the status blockquote second. Inconsistent ordering; some Markdown renderers and the `head -1` introspection used by tooling will surface a blockquote where a title is expected.

**Why it matters.** Cosmetic/consistency, not a correctness gap — every spec DOES carry the status blockquote (the load-bearing honesty requirement is met). But the inconsistency makes mechanical title extraction unreliable and signals the set was authored by uncoordinated passes. Low blast radius.

**Fix.** Standardize: `# Title` on line 1, status blockquote immediately below, across all 7. (Minor.)

### M2 — "D/T/R" is correctly disambiguated in trust-posture but the brief's wrong expansion is not flagged in the entry-point spec, where a reader meets it first

**Location.** `platform-overview.md` §4 L3 summary + §10 source ledger ("pact — D/T/R") vs `trust-posture-and-governance.md` §11 (the correction).

**What's wrong.** The brief's reference table (`briefs/01-vision.md` line 57) and casual usage treat "D/T/R" loosely; `trust-posture-and-governance.md` §11 correctly pins it: "the brief's shorthand 'D/T/R = Decision/Task/Review' is **incorrect**. D/T/R is the addressing grammar [Department/Team/Role]." Good catch — but `platform-overview.md` (the entry point) uses "D/T/R accountability" in §4-L3 and §10 with **no expansion and no pointer to the §11 correction**, so a reader who starts at the overview (as intended) meets "D/T/R" undefined and may carry the brief's wrong expansion.

**Why it matters.** The correction exists but is buried in the deepest spec; the term is introduced undefined in the shallowest. Minor terminology-onboarding gap, not a contradiction (the specs that define it agree).

**Fix.** In `platform-overview.md` §4-L3, expand on first use: "D/T/R accountability (Department/Team/Role addressing — see `trust-posture-and-governance.md` §11; NOT the brief's Decision/Task/Review)."

### M3 — Connectors spec references `specs/governance-substrate.md` 4× as the authority for posture/envelope internals, but that authority is `trust-posture-and-governance.md` — a reader cannot follow the deferral

**Location.** `connectors-and-integration.md` §4.2, §5.3, §7.1-invariant, §7.2-invariant, open-decisions table (all defer envelope/posture internals to `specs/governance-substrate.md`).

**What's wrong.** This is a specific, high-frequency instance of B1 worth calling out on its own: the connectors spec is _correctly_ designed to NOT restate governance internals (good separation), and explicitly defers them — "the posture (`specs/governance-substrate.md`) plus the envelope dimension together decide..." — but the deferral target **does not exist**. Five distinct deferrals all point at a 404. The reader who tries to follow "see the governance substrate spec for the envelope internals" lands nowhere.

**Why it matters.** The separation-of-concerns design is sound and is the right pattern (avoids the H2 duplication problem) — but a deferral to a non-existent authority is worse than a duplication, because the reader gets _nothing_. Until B1 is fixed, every "defer to governance-substrate" in the connectors spec is a dead end.

**Fix.** Repoint all `specs/governance-substrate.md` references in the connectors spec to `trust-posture-and-governance.md` (subsumed by the B1 sweep, but flagged separately because the connectors spec's clean-deferral design makes these references load-bearing for comprehension, not just navigation).

---

## LOW

### L1 — `connectors-and-integration.md` claims "the strategic spine names four moats; the CONNECTION network effect rides on this layer" — "CONNECTION network effect" terminology is not defined or cross-referenced in any sibling spec

**Location.** `connectors-and-integration.md` §6 (heading "How connectors map to the CONNECTION network-effect").

**What's wrong.** §6 introduces "the CONNECTION network effect" (caps, as a named thing) and says "the strategic spine names four moats; the CONNECTION network effect rides on this layer." Network effects are a distinct concept from the four moats (M1–M4), and the term is presented as canonical ("THE CONNECTION network effect") but appears in no other platform spec and is not defined in `platform-overview.md` §5 (which enumerates only M1–M4). The grounding is `06-network-effects.md` (a workspace artifact), not a sibling spec.

**Why it matters.** Minor — a reader meets a capitalized named concept that no sibling spec corroborates; it reads as authoritative but is single-spec-local. Not a contradiction, just an un-cross-referenced term.

**Fix.** Either define the network-effect taxonomy once (in `platform-overview.md`, alongside the moats) and reference it, or downgrade "the CONNECTION network effect" to plain language ("connectors drive a within-org and cross-org network effect") to avoid implying a canonical named concept that isn't established platform-wide.

### L2 — `_index.md` comms-wedge section is honest and complete, but does not warn that two platform specs (transparency, intervention) and two comms specs share overlapping "data model" vocabulary

**Location.** `specs/_index.md` (both sections).

**What's wrong.** The index is complete and correctly split (7 platform target-state + 7 comms shipped; positive finding). A minor sharp edge: `data-model.md` (comms, shipped) and the platform's `transparency-and-provenance.md` §2 / `intervention-and-versioning.md` §2 both describe a "data model," and `coordination-and-teams.md` §10 owns "the coordination fields of the work-item ontology" while `data-model.md` (comms) owns the comms entities. A reader searching "data model" gets four hits with no disambiguation in the index.

**Why it matters.** Low — the index descriptions are accurate enough to disambiguate on a careful read (comms `data-model.md` says "Account-based model... PDPA"; platform specs say "provenance ledger"). Just a findability nit.

**Fix.** Optional: add a one-line note in `_index.md` that the platform provenance data model (`transparency-and-provenance.md` §2) is distinct from the shipped comms `data-model.md`.

---

## Honesty already present (NOT re-flagged — credit where due)

- **All 7 platform specs carry the `> Status: TARGET-STATE (vision / not yet implemented)` blockquote.** The shipped-vs-vision boundary is honestly drawn; no platform spec can be mistaken for shipped behavior. The `_index.md` reinforces it ("It is target-state and not yet implemented" / "platform specs describe intended behavior (status TARGET-STATE)").
- **The `_index.md` is complete and correctly bifurcated** — 7 platform rows + 7 comms rows, two clearly-labeled sections ("Platform (target-state / vision)" and "Comms wedge (shipped)"), every comms spec present (`message-routing`, `rag-pipeline`, `response-accuracy`, `data-model`, `channel-coordination`, `business-model`, `onboarding`); none dropped.
- **The genuinely net-new parts are honestly marked.** The M1 cascade engine is repeatedly tagged NET-NEW ("the single net-new framework component", "NET-NEW composition over REUSED primitives", "the only mostly-net-new piece") with the runtime-ownership spike named as the gating risk. The untrusted-publisher trust model is tagged "[NET-NEW] in full ... design-first ... the load-bearing 5%" and correctly sequenced ("MUST be designed before the cross-org publish/subscribe surface"). Neither is over-claimed as shipped.
- **The traceability-not-accountability honesty caveat travels consistently** across `platform-overview.md` §7, `transparency-and-provenance.md` §1.4, `trust-posture-and-governance.md` §7.5, and `intervention-and-versioning.md` §8.3 — no spec over-claims accountability.
- **The agent-comms-beats-human-comms thesis is honestly fenced as an unproven research BET, not a USP**, in `platform-overview.md` §4-L6, `coordination-and-teams.md` §6.2/§6.3/§13#5, consistently with the risks analysis (`09-risks-failure-points.md` §3). The narrowed defensible position ("disrupt the handoff, not the relationship") + the informal/ambiguity-preservation guardrail are present.
- **The L1–L5 numbering reconciliation is explicitly pinned** in `trust-posture-and-governance.md` §1.1 (three colliding conventions named; brief's labels explicitly forbidden as enum names; aegis enum marked `[UNVERIFIED]`). The defect (H1) is that the _other_ specs don't honor it — not that the authority spec is unaware.
- **The brief's wrong "D/T/R = Decision/Task/Review" is explicitly corrected** in `trust-posture-and-governance.md` §11.
- **The Step/Output/Decision model and content-hash formula are semantically consistent** between the transparency and intervention specs (the defect H2 is duplication + minor field/token drift, not contradiction — the models agree on substance).
- **M1/M2/M4 sequencing is consistent across specs** — "M2 ships first (PACT+EATP shipped); M1 is harder/later" (`platform-overview.md` §5, `trust-posture-and-governance.md` §14) and "cross-org ignites second after the trust model lands" (`artifact-system-and-registry.md` §4/§5). No sequencing contradiction.
- **No spec contradicts the brief's six-property acceptance test or the OBJECTIVE/PROCESS/DATA model** — the work model is consistent platform-overview → connectors → coordination.
- **Specs are genuinely DETAILED authorities, not thin summaries** — each carries node tables with load-bearing fields, typed edges, enumerated invariants, edge-case contracts (streaming/large-artifact/tool-failure/partial-run; injection/rotation/rate-limit; SAME-collision/stale-reap/fork), explicit REUSE/ADAPT/NET-NEW per capability, and flagged-not-smoothed open unknowns per `spec-accuracy.md` discipline.

---

## Specs-vs-plans/analysis consistency

Spot-checked: the specs' moat homes (M1→L4, M2→L3, M3→L6, M4→L5), the 80/15/5 split, the cascade-engine-as-sole-net-new-framework-component, the SHADOW-mode rollout, the per-objective least-privilege envelope, and the two-stage (within-org then cross-org) ignition all trace correctly to `02-plans/01-architecture.md`, `02-plans/03-provenance-cascade-design.md`, `02-plans/04-trust-posture-permissions-plan.md`, and the analysis files cited in each spec's source ledger. **No spec-vs-plan contradiction found.** The defects above are intra-spec-set (naming, duplication, navigation), not spec-vs-plan divergence.

---

## VERDICT

**BLOCKING-GAPS** — 1 BLOCKING (B1: every layer in the entry-point spec routes to a non-existent sibling filename; 15 dangling refs; 2 layers have no detailed spec at all but the overview promises one), 3 HIGH (L1–L5 dual-scale collision unqualified incl. inside one spec; transparency↔intervention verbatim data-model/invariant duplication with already-manifest Step-field drift; transparency §8 future-split note describing an already-completed split + a non-existent target), 3 MEDIUM, 2 LOW. Counts: **BLOCKING 1, HIGH 3, MEDIUM 3, LOW 2.** The content is strong and honest; the wiring between the seven siblings is broken and must be fixed before the set can serve as the navigable domain authority `specs-authority.md` requires.
