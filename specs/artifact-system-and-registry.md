# Artifact System & Registry

> Status: TARGET-STATE (vision / not yet implemented). This spec describes the intended platform; the comms wedge (shipped) specs are separate.

This is the domain-truth authority for **how reusable knowledge-work is encoded, authored by non-coders, stored, versioned, and exchanged** — first within one organization, then across organizational boundaries. It is the encoding-and-exchange half of moat **M4** ("governed, versioned, provenance-tracked cross-organization artifact exchange" — the platform's primary network-effects engine).

Scope boundaries: this spec owns the artifact *layers*, the *authoring loop*, the *proposal/version lifecycle*, *intra-org and cross-org distribution*, and the *untrusted-publisher trust/provenance model*. It does NOT own execution-time posture mechanics (that is the governance spec — moat M2), the multi-human coordination substrate (moat M3), or the discovery/search UI surface beyond the data contract it depends on.

REUSE legend used throughout: **[REUSED: loom]** = the mechanism runs in production today in `~/repos/loom` for one org's codegen artifacts; **[ADAPT]** = the mechanism exists in the right shape but must be generalized; **[NET-NEW]** = genuinely new, design-first, no precedent in the ecosystem DNA.

---

## 1. The five artifact layers — the encoding of PROCESS/PROCEDURE

An **artifact** is a piece of company know-how turned into a thing the agent can *run* — not a document *about* a process, the process itself, executable (user-flow `04` §0). The platform encodes all reusable work as exactly five layer shapes. These shapes are **domain-agnostic by construction**: the layer taxonomy is about *artifact shape*, not about codegen (research `01` §0, §7a.1). The same five shapes that encode "how we run a code review" encode "how we close the books at month-end."

[REUSED: loom] The taxonomy, format contracts, and authoring discipline run in production at `loom/.claude/rules/cc-artifacts.md`. [ADAPT] The only generalization is de-coupling the word "codegen" from the tier vocabulary (§5).

| Layer | What it encodes (plain language) | Role in PROCESS/PROCEDURE | On-disk shape | How the harness loads it | Runtime behavior |
| --- | --- | --- | --- | --- | --- |
| **SKILLS** | Reference know-how the agent looks up when relevant ("how we categorize expenses for tax") | The *context* a procedure draws on | `<name>/SKILL.md` + sub-files; Markdown + frontmatter | Semantic activation via the `description:` field | Injected into context when the model judges the description matches intent; progressive disclosure pulls sub-files on demand |
| **RULES** | A boundary the agent must always respect ("never refund over $500 without manager sign-off") | The *guardrails* a procedure runs inside | `<name>.md`; Markdown + frontmatter (`priority:`, `scope:`, `paths:`) | Baseline rules every turn; path-scoped only when touching a matching path | Prescriptive prose the model must honor; re-surfaced by hooks every turn |
| **COMMANDS** | A named procedure you invoke by name ("run the month-end close") | The *procedure* itself, top-level | `<name>.md`; Markdown + frontmatter | Injected as a user-message prompt at `/name` invocation | The body's numbered steps become the agent's task for that turn |
| **AGENTS** | A specialist with its own judgment + tools ("our contract-review specialist") | The *judgment* a procedure delegates to | `<name>.md`; Markdown + frontmatter (tools allowlist, model) | Loaded when delegated to, by name | A sub-agent with its own context, tool allowlist, and per-agent hooks |
| **HOOKS** | An automatic safety tripwire on specific actions ("pause before anything touches payroll") | The *deterministic* guardrail | `<name>.js`; CommonJS script | Registered in the harness settings hook table | Fires on lifecycle events; can block an action or inject context |

### 1.1 Layer selection invariants

These hold whenever the platform proposes an artifact shape (the user never picks the shape — the platform picks it and explains it in plain language; user-flow `04` §2.2):

- A **named procedure** → COMMAND. An **always-respected boundary** → RULE. **Reference know-how** → SKILL. **Judgment + conditional recovery paths** → AGENT. A **deterministic tripwire on an action** → HOOK.
- A SKILL that grows conditional branches and recovery paths is an AGENT in disguise — promote it (research `01` §1a).
- HOOKS check **structure** (a path prefix, an exit code, an action type), never **semantics** — semantic judgment is the agents' job at review time.
- The layer's *body* is CLI-neutral; per-CLI surface differences are handled by the emitter, not by the author (§7).

### 1.2 Why five layers and not one blob

Encoding a process as one monolithic document fails the same way a 2,000-line function fails: the next reader (human or agent) cannot find the one boundary that matters. Separating *boundary* (rule) from *procedure* (command) from *reference* (skill) from *judgment* (agent) from *tripwire* (hook) lets each piece be reviewed, versioned, recalled, and overlaid independently. A recall of a buggy procedure (§6.5) leaves the org's guardrails untouched; an override of a guardrail (§6.4) leaves the procedure inherited.

---

## 2. Non-coder authoring — capture from observed work

The defining constraint: **users are not coders** (brief §3a). Artifacts are NOT hand-authored. The platform captures an artifact by **watching a person do the work once** and proposing the artifact back in plain language (user-flow `04` §0, §2).

### 2.1 The generalized codify-from-observed-work loop

[REUSED: loom] The origination mechanism is `/codify` — a production loop that reads a structured digest of a completed work session and drafts artifact changes for a human to approve (research `01` §3a: "observe → digest → codify into real artifacts"). [ADAPT] Today the digest captures *code-session* signals (`file_counts.pythonFiles`); generalizing it to capture *non-coding* work is the stated adaptation (research `01` §7b.4, §8.3) and is flagged as **real, unbuilt work** — a research risk, not a from-scratch build.

The loop, generalized:

```
person does a real piece of work once, in the one interface, stating intent
   │   (the agent does the work WITH them; corrections are the gold)
   ▼
platform digests the session → identifies the repeatable shape
   │   (a named procedure + the boundaries the person enforced mid-work)
   ▼
platform PROPOSES an artifact (picks the layer shape; explains in plain language)
   │   unprompted, as a gentle nudge — [Review] [Not now] [Never suggest]
   ▼
person REVIEWS + EDITS in the change-review surface (§2.2) → stores it
```

The load-bearing moment is the **correction**: when the person intervenes mid-work ("never activate billing until the signed contract is on file"), that intervention is the company-specific judgment that lives only in the expert's head today. The platform captures it without a separate authoring step (user-flow `04` §2.1).

### 2.2 The change-review surface (non-coder authoring + edit)

[NET-NEW] Under the production system, artifacts are reviewed as Git diffs by engineers — exactly what a non-coder cannot do (research `01` §7b.4). The plain-language change-review surface is a genuinely-new build. Its contract:

- Renders the artifact as **plain-language steps and boundaries**, never as code or a diff.
- Each step and each boundary is individually editable, addable, removable.
- Shows **provenance** auto-filled and un-fakeable (who captured it, from which session, which verified person, which org).
- Offers two save dispositions: **Save as draft** (private, `pending_review`) or **Save & make available to my team** (enters intra-org distribution, §4).

The same surface is the **change-review surface for modifications**: when a teammate's correction proposes an improvement to an existing artifact (user-flow `04` §3.2), the owner sees the suggested change in the same plain-language form, with the suggester attributed, and accepts / declines / asks-for-clarification. Acceptance produces a new version (§3), never an overwrite.

### 2.3 Agent-as-producer, never agent-as-authority

The agent **drafts**; a human **approves**. This is invariant (platform-model `04` §3.2). The drafted artifact is attributed to **both** the producing agent AND the human accountable for it — two-level attribution (platform-model `04` §3.3). An agent may generate supply; it may never enter the catalog autonomously. This is the same Gate-1 "human classifies every change; automated suggestion permitted, automated placement is not" discipline (research `01` §2b) applied at the authoring boundary.

---

## 3. Storage, versioning, and the proposal lifecycle

### 3.1 The proposal as the unit of change

[REUSED: loom] Every artifact creation or modification flows as a **proposal** — the unit of artifact change that moves from authoring to distribution. Its three-state lifecycle (research `01` §3b; `artifact-flow.md` § Proposal Lifecycle):

```
authoring creates           Gate-1 classifies              Gate-2 distributes
pending_review ──────────►  reviewed  ──────────────────►  distributed
       ▲   │ append              ▲ │ append (resets to            │ archive + create fresh
       └───┘ pending_review      └─┘ pending_review)              ▼
```

| Status | Meaning | Authoring behavior | Distribution behavior |
| --- | --- | --- | --- |
| `pending_review` | New changes, not yet classified | **Append** new changes to the `changes:` array | Gate-1: review and classify |
| `reviewed` | Classified, not yet distributed | **Append** (resets status to `pending_review`) | Gate-2: distribute |
| `distributed` | Classified AND distributed | **Archive** and create fresh | Skip (already processed) |

Each proposal change entry carries: `file`, `action`, `suggested_tier`, `canonical_path`, `reason`, `diff_lines`, `trust_class` (§3.4), and `adaptation_notes` (research `01` §3b).

### 3.2 Append-never-overwrite (the version-preservation invariant)

[REUSED: loom] When new changes arrive and a proposal already exists in `pending_review` or `reviewed`, the new entries MUST be **appended** to the existing `changes:` array — never replace the file (`artifact-flow.md` § Append, Never Overwrite). Overwriting an unprocessed proposal is **silent data loss** — an earlier capture session's knowledge gone with no trace.

Consequences this invariant guarantees for a non-coder:

- No future edit silently destroys a prior version (user-flow `04` §2.3).
- An improvement (e.g. Devin's DPA step, user-flow `04` §3.2) produces **version 2**, with the contributor attributed and version 1 preserved.
- A recall (§6.5) can offer a *specific prior version* as the safe replacement because every version is retained, never overwritten.

### 3.3 Concurrency: the authoring lease

[REUSED: loom] Two concurrent authoring runs would clobber the artifact corpus, so a **lease** over the scope files gates origination (research `01` §3a; `codify-lease.js`). The lease records the scope fingerprint, the working branch, and the release timestamp. [ADAPT] In the multi-author org setting, lease scope is keyed per artifact-corpus-path so two people capturing *different* processes proceed in parallel while two capturing the *same* one serialize.

### 3.4 Trust classification (the run-risk grade, owned by the governance spec)

Before an artifact is shareable, it is graded for **how much autonomy it should be allowed** — the L1–L5 posture ladder (brief §3e). This grade is **stored with the artifact and travels with it** to every consumer (user-flow `04` §3.1). New or sensitive artifacts default cautious (an artifact that touches billing defaults to L3 step-by-step, user-flow `04` §2.4). [REUSED: loom for the posture model — moat M2]; this spec only records that the grade is an artifact-level stored field that travels with distribution. The posture mechanics are the governance spec's authority.

---

## 4. Intra-org sharing — the within-org loop (ignites first)

This is the stage that **ignites first** and has **no cold-start gap**, because producer and consumer are the *same organization* (network-effects `06` §8.4; platform-model `04` §6.3: "supply = demand = same customer"). It is the PERSONALIZATION + ENGAGEMENT compounding loop.

### 4.1 Discovery within the org

A teammate states intent; the platform surfaces a matching saved artifact ("Your team has a saved process for this: 'Onboard a new client', by Maria, used 4 times, runs cleanly"; user-flow `04` §3.1). [ADAPT] Discovery today is the manifest plus the skill `description:` semantic-match; the reusable foundation is that **the `description:` field is already a semantic discovery primitive** (research `01` §7b.2). A richer search/catalog surface is [NET-NEW] (§6.2) but the semantic-match foundation carries over.

### 4.2 Run-with-travelling-trust-class

When a teammate runs a shared artifact, the **trust class travels with it**: first-time run defaults to the artifact's stored class (L3 step-by-step), and the boundaries fire exactly as the author designed them (user-flow `04` §3.1). The consumer chooses the posture under which it runs — the consumer's brake (governance spec / moat M2).

### 4.3 The knowledge-contribution feedback (transaction D feeds B)

[REUSED: loom mechanism] A teammate's correction flows back through the same codify-from-observed-work loop that captured the original (user-flow `04` §3.2). The correction produces a proposed improvement; the **artifact owner** adjudicates (their call); acceptance yields a new version with the contributor attributed (§3.2). The flywheel, in one company: **capture → use → correct → improve → re-use** — the consumer is also a producer, producing for free as work exhaust (platform-model `04` §4.3, §3.2).

### 4.4 Intra-org variant overlays (org-default vs team-override)

[REUSED: loom] The variant-overlay engine resolves a single source against overlays with three semantics (research `01` §2a; `artifact-flow.md` § Variant Overlay Semantics):

- **Replacement** — an override exists for a slot AND a base exists → override wins.
- **Addition** — an override exists, no base → added.
- **Base only** — no override → base used as-is.

[ADAPT] Today the overlay axes are language × CLI; generalizing to an **org-default-vs-team-override axis** is mechanically identical — `variants/<team>/rules/foo.md` overrides `rules/foo.md` (research `01` §7a.3, ~1 session). One team can run an org-default close-process while another overrides one boundary, inheriting every other step.

---

## 5. Cross-org exchange — the governed marketplace (M4, ignites second)

This is the prize and the hard part: making it as safe to run **another company's process inside your company against your real data** as installing a reviewed app (platform-model `04` §1). It is sequenced **second**, after the within-org loop has produced a seed catalog AND the net-new untrusted-publisher trust model (§8) has been designed — because that model *constrains* the cross-org surface and MUST land first (network-effects `06` §8.3; platform-model `04` §7.3).

### 5.1 The splitter IS the share-across-teams engine

[REUSED: loom] The single most load-bearing reuse claim: **loom's two-gate splitter IS the "share across teams/orgs" engine** (research `01` §7a.2). A registry is loom-with-a-discovery-surface-bolted-on, not a rewrite. The platform treats the splitter as the **artifact control plane** and builds the registry as a thin publish/discover surface ON TOP of it (research `01` §7d).

The two gates, generalized from cross-repo to cross-org:

- **Gate-1 (inbound — review + scrub + classify):** a human at the publishing org classifies each change as **Global** (org-wide), **Variant** (one team / one consumer), or **Skip**. Automated suggestions permitted; **automated placement is not** (research `01` §2b; `artifact-flow.md` § Human Classifies Every Change). A **disclosure-scrub runs first** (§5.3).
- **Gate-2 (outbound — distribute):** merges source + variant overlays into each subscribing consumer per its tier subscriptions. This is a **merge** (consumers may carry legitimate local overrides), not an overwrite (research `01` §2b).

[ADAPT] Tier subscriptions generalize from `cc`/`co`/`coc`/language tiers to **work-domain tiers** (finance, legal, ops) — "mechanically identical to adding a tier" (research `01` §7b.3, ~1 session). The `repos:` subscription block generalizes to a **cross-org subscription registry**: today every consumer is a clone of ONE Git remote under one org; org-A-authors → org-B-consumes with no shared remote is the [NET-NEW] publish/subscribe surface (research `01` §7b.1, ~3–5 sessions, gated on §8 landing first).

### 5.2 Variant overlays across orgs (adapt without forking)

[REUSED: loom] The same overlay engine of §4.4, one axis up. A consuming org adapts a published base with a local override and **inherits upstream improvements automatically** without losing the override (user-flow `04` §4.4): the base's billing rule is *replaced* for the consumer only; every other step is *inherited*; when the publisher improves the base, the consumer gets the improvement, and the consumer's private override **never leaks back to the publisher**. This is the asymmetric, upstream-generic-only direction (§8.4).

### 5.3 Disclosure-scrub on intake (the cross-org safety gate, already built)

[REUSED: loom] Before any artifact leaves the org, a **mandatory disclosure-scrub** strips client names, internal system paths, credentials, and employee PII — precisely because a shared artifact reaches many consumers once distributed (research `01` §2b "Intake Disclosure Scrub"; `artifact-flow.md` § Intake Disclosure Scrub; `upstream-issue-hygiene.md` MUST-2). This is **exactly the cross-org safety gate** — the machinery exists; it gets pointed at the org boundary instead of the repo boundary (research `01` §7a.4). The scrub is two mechanical actions run *first*: an automated scanner pass over the candidate artifact files, plus a human scrub of the proposal body. A non-zero scanner exit OR any finding **halts** until genericized; placement does not proceed. Gate-1 placement enters the publisher's permanent history *before* Gate-2 runs, so scrubbing at intake (not at output) is the only redaction that is not partial-after-the-fact.

### 5.4 Tier subscriptions (the consumer's pull cadence)

[REUSED: loom + ADAPT for org axis] A consumer subscribes to one or more tiers; on its own cadence it pulls the merge of base + its subscribed-variant overlays. The subscription is the consumer's choice; the publisher does not push into a consumer. The obsoletion list (§6.5) is the one exception that propagates on the next pull regardless.

---

## 6. Marketplace surfaces — what is reused vs net-new

### 6.1 The governance spine, gathered (build status)

This table is the strategic core: almost everything is already built; the net-new clusters on the cross-org-untrusted boundary (user-flow `04` §5).

| Property | What it does (plain) | Build status |
| --- | --- | --- |
| **Provenance** | Proves *who* made it + *how* (captured from real work), cryptographically | **[REUSED: loom]** — signed identity substrate (platform-model `04` §3.3) |
| **Trust classification (L1–L5)** | How much autonomy the artifact gets; default-cautious for sensitive | **[REUSED: loom]** — posture model M2 (governance spec) |
| **Disclosure scrub** | Strips private data before an artifact leaves the org | **[REUSED: loom]** — intake scrub (§5.3) |
| **Variant overlay** | Adapt a shared artifact locally without forking; inherit upstream fixes | **[REUSED: loom]** — overlay engine, ~1 session to add org axis (§5.2) |
| **Recall / obsoletion** | Pull a bad artifact from every consumer on next pull | **[REUSED: loom]** — obsoletion primitive, production-grade (§6.5) |
| **Discovery / search** | Find an artifact across publishers | **[ADAPT/NET-NEW]** — `description:`-as-discovery foundation reused; catalog/search surface new (§6.2) |
| **Untrusted-publisher gate** | Treat unknown publishers with sharply higher caution | **[NET-NEW]** — the load-bearing 5%, design-first (§8) |
| **Licensing + attribution** | Free / paid / attribution-required for cross-org artifacts | **[NET-NEW]** — provenance exists, licensing unbuilt (§8.5) |

### 6.2 Discovery / registry surface

[NET-NEW surface, ADAPT foundation] loom has no search / index / rating; discovery today = the manifest + semantic `description:` matching (research `01` §7b.2). The marketplace needs a catalog showing, per artifact: publisher (verified-org flag), usage count, recall count, trust class, license, provenance summary, and rating. The reusable foundation is that **artifacts already carry a semantic description that doubles as a discovery signal** — the search surface is built on top of that primitive, not from zero.

### 6.3 What loom provides vs what the marketplace adds (the 80/15/5 split)

| Requirement | REUSED from loom (the splitter is the engine) | NET-NEW / ADAPT |
| --- | --- | --- |
| **Created** | Five-layer taxonomy + authoring meta-skills + codify-from-observed-work | [ADAPT] non-coding capture; [NET-NEW] plain-language change-review surface (§2.2) |
| **Modified** | Proposal lifecycle, append-never-overwrite, lease, versioned corpus | [NET-NEW] non-coder change-review UI for modifications (§2.2) |
| **Stored** | Single-source corpus + tier classification + obsoletion list | [NET-NEW] registry/index/search surface (§6.2) |
| **Shared (intra-org)** | Two-gate splitter, variant overlays, additive-with-obsoletion | [ADAPT] org-axis variant + work-domain tiers (~1 session each) |
| **Shared (cross-org)** | Disclosure-scrub, recall, asymmetric overlay precedent | [NET-NEW] cross-org publish/subscribe surface (~3–5 sessions, gated); untrusted-publisher trust model (§8); licensing (§8.5) |

---

## 7. Multi-CLI / harness-neutral encoding

The platform is harness-agnostic (brief §3e). [REUSED: loom/envoy] The same artifact is expressed across multiple agent CLIs from a single canonical source under a strict parity contract (research `01` §6; `~/repos/dev/envoy`). The author edits the canonical layer body once; an emitter produces each CLI surface, applying the variant overlay + a parity check + byte-budget abridgement. This is foundational, not headline (it commoditizes; the moat is the governed exchange on top).

Parity contract (what MUST match vs MAY diverge): the artifact's semantic body MUST be byte-identical across CLIs (hard-block on drift); delegation *syntax* and example forms MAY diverge per CLI (soft-warn). Some artifacts map to a CLI's **native primitive** and are deliberately not emitted as copies. For a non-coder author this is invisible — they author intent once; the multi-CLI expansion is the platform's job. This spec records only that the *artifact body is the contract and the per-CLI surface is an emission of it* — the parity-enforcement mechanics are the cross-CLI spec's authority.

---

## 8. The untrusted-publisher trust & provenance model (NET-NEW, design-first)

This is the **genuinely-new 5%** and the **load-bearing dependency of the entire cross-org thesis** (research `01` §7c.1; platform-model `04` §7.3; network-effects `06` §8.3). It MUST be designed **before** the cross-org publish/subscribe surface, because it constrains that surface (research `01` §7d). Marked NET-NEW in full; the design directions below are *flagged candidates, not chosen mechanisms*.

### 8.1 Why the existing trust substrate does not cover this

[REUSED foundation, but insufficient] loom's coordination substrate proves identity for **enrolled** operators: a signed coordination log, a roster, a 2-of-N quorum, `refs/coc/**` server rulesets (`multi-operator-coordination.md` §1–6). Its threat model is **bounded-trust** — "the adversary is a legitimate team member with repo write access" (`multi-operator-coordination.md` § threat model). A cross-org marketplace faces publishers you have **never met and have no shared enrollment with**. An external publisher is not on anyone's roster. Signed-artifact provenance from an *external* publisher (vs an enrolled operator) is **not yet modeled** (research `01` §7c.1). The cryptographic primitives are a strong starting point; the missing piece is establishing a stranger's trustworthiness with no shared enrollment authority.

### 8.2 Signing & attestation (design directions)

[NET-NEW] The artifact and its provenance must be signed by the publisher such that a consumer can verify *what can be proven* about it: published by a verified organization, authored by a verified person at that org, captured from real work (not hand-typed), and a usage/recall history. The likely shape — flagged, not chosen — is "aegis-shape runtime records, anchored against the consuming tenant's own identity provider instead of a shared Git remote" (platform-model `04` §9.6; aegis at `~/repos/dev/aegis`). The signing substrate (commit-signing keys, hash-chained log, quorum, server rulesets) is the starting point; binding an *external* publisher's signed provenance to a trust root the consumer recognizes is the new design.

### 8.3 Trust classification of the publisher (verified vs unverified gate)

[NET-NEW] The marketplace distinguishes **verified** from **unverified** publishers and treats them sharply differently (user-flow `04` §4.3):

- **Verified publisher:** consumer sees provenance ("published by a verified org, authored by a verified person, captured from real work, N companies run it, 0 recalls"), then chooses a run posture (defaulting cautious for a process new to them).
- **Unverified publisher:** the gate is sharply different — "we CANNOT prove who made this, or that it came from real work; it has no usage history; it may be fine, it may be malicious." If the consumer proceeds: it runs **locked at L3** (pause every step, cannot be raised to autonomous until it earns a verified track record) and **runs in a restricted sandbox against test data first**.

The **consumer-side brake** (run a stranger's artifact cautiously, sandboxed, locked-L3) is [REUSED: loom — moat M2] applied at the install boundary (platform-model `04` §4.2 "governed at install AND at run"). What is [NET-NEW] is *establishing publisher trustworthiness in the first place*.

### 8.4 Asymmetric publish/consume governance (the closest existing precedent)

[REUSED precedent, NET-NEW wiring] The closest existing precedent for the asymmetry the marketplace needs is the aegis fork-relationship rule (research `01` §7c.2; `~/repos/dev/aegis/.claude/rules/aegis-fork-relationship.md`): the canonical/registry artifact stays generic; org-specific overrides are allowed; improvements may flow **up** to the generic; one org's client-specific data must **never leak down** to others. This asymmetric, upstream-generic-only governance is the exact shape — and it already exists as a baseline rule in the commercial fork. Wiring it to *untrusted external* publishers is the design that must be done first.

### 8.5 Licensing & attribution (NET-NEW)

[NET-NEW] Provenance capture exists; **licensing** (free / paid / attribution-required) for a third-party work artifact is unbuilt (research `01` §7c.3). The publish gate presents the license choice (free-with-attribution / paid-with-price / internal-only). Attribution is two-level (the producing agent + the accountable human; platform-model `04` §3.3). The mechanism — enforcing a license, tracking attribution across a re-published variant, resolving conflicting licenses on a derived artifact (§9.3) — is to be built.

---

## 9. Edge cases & failure modes

### 9.1 A malicious / poisoned shared artifact

A published artifact is a *process that runs inside a consumer's company against real data* — not an app in a sandbox (platform-model `04` §7.1). Defenses, layered:

- **At publish:** the disclosure-scrub (§5.3) blocks leaking the publisher's own data outward, and Gate-1 human-classify blocks unreviewed placement. These protect the *publisher*, not the consumer, from a poisoned payload — so the consumer-side defenses below are the load-bearing ones.
- **At discovery:** the verified/unverified publisher gate (§8.3) flags an unknown publisher loudly.
- **At install:** an unverified artifact is **sandboxed against test data first** and **locked at L3** (§8.3) — the blast radius of a malicious artifact is bounded to a paused, observable, test-data run.
- **At run:** the consumer's posture choice (moat M2) is the brake. **Honest limit:** the brake is a *default, not a lock* — a consumer who raises every unvetted artifact to L5 to save time defeats it (platform-model `04` §7.3). The platform defaults sensitive/unverified artifacts cautious and locks unverified ones at L3, but a determined consumer can over-trust. The posture ladder *reduces* the blast radius; it does not *eliminate* it.
- **After the fact:** recall (§9.2) is the remedy when an artifact turns malicious or buggy *after* it was trusted.

### 9.2 Recall propagation

[REUSED: loom] A publisher (or the platform) must be able to **pull a bad artifact back from every consumer**. The obsoletion mechanism is the cross-org "recall" primitive, **already production-grade** — "the ONLY mechanism by which 30+ downstream repos can purge stale artifacts" (research `01` §2d; `cross-repo.md` Rule 4). On every consuming org's next pull, a recalled version: stops being runnable, offers a named safe replacement version, and **preserves each consumer's local overrides** (e.g. a consumer's deposit-rule override carries forward to the replacement untouched; user-flow `04` §4.5). The consumer sees the recall loud, in plain language, with the safe-upgrade path one click away, and **no private data is touched**.

Propagation invariants:
- Recall is a **single declarative entry** that drives a universal purge — it does not require touching each consumer (research `01` §2d).
- Recall propagates on the consumer's **next pull**, not as a push — bounded by the consumer's pull cadence (§5.4). A consumer that has not pulled since the recall still runs the recalled version until its next pull; the recall reason is surfaced loudly on that pull.
- Append-never-overwrite (§3.2) guarantees the named safe-replacement version still exists to offer.

**Why recall is the trust keystone for an untrusted-publisher catalog:** a marketplace that lets strangers publish MUST be able to un-publish instantly and universally, or one bad artifact poisons every consumer with no remedy. Recall is the consumer's protection against a producer who turns malicious *after the fact* — and it is the single piece of the cross-org trust story that is **already production-grade**, a real competitive advantage over existing skills/MCP directories that lack governed recall (network-effects `06` §8.2).

### 9.3 License conflicts

[NET-NEW] When a consumer adapts a published artifact via a variant overlay (§5.2) and re-publishes the result, the derived artifact composes the base's license with the overlay author's intent. Conflict cases the design must resolve:

- **Attribution-required base, un-attributed derivative:** the derivative MUST carry the base's attribution forward (two-level attribution composes; §8.5). Stripping it is blocked at the re-publish gate.
- **Paid base, free derivative:** re-publishing a free derivative of a paid base is a license violation; the re-publish gate MUST detect the base→derivative license relationship and block or require the base's license terms to carry forward.
- **Internal-only base, outbound derivative:** an org-default base marked internal-only cannot be the base of an outbound publish — the asymmetric upstream-generic-only direction (§8.4) is the structural defense (the private override never leaks down; here it must also never leak *out* via a derivative).

License-conflict resolution is unbuilt; it is part of the §8.5 NET-NEW licensing design and MUST be designed alongside the cross-org surface, not after.

### 9.4 Curation at marketplace scale (open question)

[UNCERTAIN] The Gate-1 "human classifies every change" discipline (§5.1) works for one-org-many-repos; the substrate is designed for ~12 operators (platform-model `04` §7.3; network-effects `06` §8.3). Whether human-in-the-loop curation survives thousands of cross-org publishers, or must become reputation-weighted / partially automated, is **unresolved**. The existing rule (suggestion-automated, placement-human) is the floor; scaling it is an open design question, not a solved one. This is flagged, not answered, here.

### 9.5 Personalization vs tenant-isolation tension

[UNCERTAIN — permanent design tension] The more the platform curates per-org artifacts, the more per-org data it concentrates, and the more catastrophic a cross-tenant leak becomes (network-effects `06` §4.3). The comms wedge enforces hard schema-per-tenant isolation by design (sealed silos); the marketplace requires *deliberate* cross-tenant permeability. The variant-overlay + Gate distribution is the candidate mechanism, but its interaction with hard tenant isolation is undesigned (platform-model `04` §9.5). Isolation strong enough to protect every tenant, permeable enough to share when the org chooses — getting permeability wrong in either direction is fatal (too sealed: no cross-org flywheel; too permeable: one leak ends the company). This tension is *why* the cross-org stage ignites second, after the trust model lands.

---

## 10. Invariants (the contract, gathered)

1. **Layer shapes are domain-agnostic.** The five layers encode any knowledge-work process, not just codegen (§1).
2. **The author never writes code.** Every artifact is captured from observed work and reviewed in plain language (§2).
3. **The agent drafts; a human approves.** No artifact enters any catalog autonomously; agent-produced artifacts carry two-level attribution (§2.3).
4. **Append-never-overwrite.** No version is ever silently destroyed (§3.2).
5. **Trust class travels with the artifact.** Stored at authoring, applied at every consumer (§3.4).
6. **The splitter is the only outbound path.** Two gates, human-classify-every-change, disclosure-scrub-on-intake (§5).
7. **Distribution is additive-with-obsoletion.** Consumer-local overrides are preserved; only declared-obsolete paths purge (§9.2).
8. **Overlay is asymmetric.** Improvements flow up to the generic; org-specific data never leaks down (or out via a derivative) (§5.2, §8.4, §9.3).
9. **Unverified publishers are sandboxed and locked-L3.** The consumer-side brake bounds a poisoned artifact's blast radius — but it is a default, not a lock (§8.3, §9.1).
10. **Recall is single-declarative and universal.** One entry purges a recalled artifact from every consumer on next pull, preserving overrides (§9.2).

---

## 11. Where this spec would split

If this domain grows, the natural split points are: (a) **`artifact-authoring.md`** — the codify-from-observed-work loop + change-review surface in full detail once §2.2 is designed; (b) **`untrusted-publisher-trust.md`** — the §8 NET-NEW trust model once its mechanism is chosen (it is the load-bearing 5% and will outgrow a section); (c) **`marketplace-registry.md`** — the §6.2 discovery/search/rating surface + the cross-org publish/subscribe data contract once that surface is specified. The trust-model split (b) should happen first, since §8 is design-first and constrains everything downstream of it.

---

## 12. Sources

- Research: `workspaces/future-of-work/01-analysis/01-research/01-coc-artifact-system.md` (§1 taxonomy; §2 splitter/variant/recall; §2d obsoletion; §3 codify lifecycle; §6 multi-CLI; §7 cross-org synthesis + 80/15/5; §7c genuinely-new untrusted-publisher; §7d sizing).
- Platform model: `workspaces/future-of-work/01-analysis/04-platform-model.md` (§2 transaction B+D; §3 producers + attribution; §4 consumers + governed install/run; §7 curated marketplace + own-vs-rent; §7.3 cons; §9 open questions).
- Network effects: `workspaces/future-of-work/01-analysis/06-network-effects.md` (§4 personalization; §6 collaboration; §8 two-stage ignition + cold-start; §8.6 symmetric pros/cons).
- User flow: `workspaces/future-of-work/03-user-flows/04-artifact-authoring-sharing.md` (Stage A capture; Stage B intra-org; Stage C cross-org; §5 governance spine; §7 proven-vs-new one-screen summary).
- Brief: `workspaces/future-of-work/briefs/01-vision.md` (§3g artifacts across orgs; §3a non-coder; §3e posture; §3f transparency; §1b processes vary co-to-co).
- Ecosystem DNA (by path): loom `~/repos/loom`; pact `~/repos/terrene/contrib/pact`; eatp `~/repos/loom/kailash-py`; aegis `~/repos/dev/aegis` (fork-relationship asymmetry precedent); envoy `~/repos/dev/envoy` (multi-CLI parity).
- COC rules (by path): `.claude/rules/artifact-flow.md` (proposal lifecycle, intake scrub, variant overlay); `.claude/rules/multi-operator-coordination.md` (signed identity substrate, bounded-trust threat model); `.claude/rules/upstream-issue-hygiene.md` (disclosure redaction); `.claude/rules/cross-repo.md` (obsoletion purge).
