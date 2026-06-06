# 01 — The COC Five-Layer Artifact System

> Research for the Agentic Work Platform (brief objective **3g**: "artifacts are easily created, modified, stored, and shared across organizations and teams").
> Grounded in `~/repos/loom`, `~/repos/loom/kailash-coc-claude-{py,rs}`, `~/repos/dev/envoy`, `~/repos/dev/aegis`, and this repo's `.claude/`.
> All claims cite real files. Uncertainty flagged inline as **[UNCERTAIN]**.

---

## 0. Executive summary

The platform's brief asks for work artifacts that are "easily created, modified, stored, and shared across organizations and teams." **That machinery already exists and runs in production** — it is the COC (Cognitive Orchestration for Codegen) artifact system in `~/repos/loom`. Today it does this for **one organization's codegen artifacts** across ~6 distribution targets and 30+ downstream consumers. The brief's requirement is to generalize this from _codegen artifacts within one org_ to _general work artifacts across many orgs_.

The system has five artifact layers (AGENTS, SKILLS, RULES, HOOKS, COMMANDS), a single-source-of-truth "splitter" (loom) with a two-gate distribution model and a language×CLI variant-overlay system, a codify lifecycle that originates artifact changes from observed work, and a multi-CLI emission layer (envoy) that expresses the same artifact across Claude Code / Codex / Gemini under a strict parity contract.

**The 80% that already exists**: the layer taxonomy, the authoring discipline (three meta-skills), the splitter (`/sync` two-gate), the variant overlay engine, the proposal lifecycle (`.proposals/latest.yaml`), the parity/bijection enforcement, and the codify→loom→sync flow.
**The 15% to adapt**: cross-_org_ (not just cross-repo) distribution boundaries; a registry/marketplace surface; de-coupling "codegen" from the artifact taxonomy.
**The 5% genuinely new**: trust/provenance for _untrusted third-party_ artifacts (today the threat model is bounded-trust _within_ one team — see §7).

---

## 1. The five artifact layers

The canonical layer taxonomy is defined in `loom/.claude/rules/cc-artifacts.md` and restated in each meta-skill's header. The skills name the layers explicitly: **L1 Intent = agents, L2 Context = skills, L3 Guardrails = rules + hooks, L4 Instructions = commands** (per `skill-authoring/SKILL.md`, `command-authoring/SKILL.md`, `hook-authoring/SKILL.md`).

| Layer                                    | Role (1-line)                                | On-disk (CC)                                   | Format                                                        | How harness loads it                                                               | Runtime behavior                                                                                                                                       |
| ---------------------------------------- | -------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **AGENTS** (L1 Intent)                   | Specialist judgment + procedure + tools      | `.claude/agents/**/<name>.md`                  | Markdown + YAML frontmatter                                   | Loaded when delegated to (by name)                                                 | A sub-agent with its own context, tool allowlist, model, and per-agent hooks                                                                           |
| **SKILLS** (L2 Context)                  | Reference knowledge, looked up on demand     | `.claude/skills/<name>/SKILL.md` (+ sub-files) | Markdown + YAML frontmatter                                   | **Semantic activation** via `description:` field                                   | Injected into context when the model judges the description matches intent; progressive disclosure pulls sub-files only when referenced                |
| **RULES** (L3 Guardrails, prose)         | Always-on / path-scoped boundary enforcement | `.claude/rules/<name>.md`                      | Markdown + YAML frontmatter (`priority:`, `scope:`, `paths:`) | Baseline rules load every turn; path-scoped load only when editing a matching file | Prescriptive prose the model must honor; surfaced again via hooks every turn                                                                           |
| **HOOKS** (L3 Guardrails, deterministic) | Runtime tripwires on tool/session events     | `.claude/hooks/<name>.js`                      | CommonJS Node script                                          | Registered in `.claude/settings.json` `hooks` block                                | Fires on lifecycle events (`SessionStart`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`); can block tool calls (`exit 2`) or inject context |
| **COMMANDS** (L4 Instructions)           | Named procedure the user invokes             | `.claude/commands/<name>.md`                   | Markdown + YAML frontmatter                                   | Injected as a **user-message prompt** at `/name` invocation                        | The body's numbered steps become the agent's task for that turn                                                                                        |

Current loom inventory (counted 2026-06-05): **39 agents, 36 skills (405 total skill `.md` files), 70 rules, 30 hooks, 41 commands, 499 variant-overlay files.**

### 1a. AGENTS — concrete example

`loom/.claude/agents/analysis/analyst.md` frontmatter:

```yaml
---
name: analyst
description: "Analysis specialist. Use for failure point analysis, risk assessment, requirements breakdown, or ADRs."
tools: Read, Grep, Glob
model: opus
hooks:
  PreToolUse:
    - matcher: "*"
      hooks:
        - type: command
          command: 'node "$CLAUDE_PROJECT_DIR/.claude/hooks/provenance-capture-tool.js"'
          timeout: 5
---
```

Key facts: `description:` **≤120 chars** with a trigger phrase ("Use for…"); body **≤400 lines** (`cc-artifacts.md` MUST NOT "No knowledge dumps"); `tools:` is the read-only allowlist; agents may carry their **own hooks** (here, provenance capture on every tool use). An agent is _judgment + procedure_; if a "skill" grows conditional branches and recovery paths it is an agent in disguise (`command-authoring/SKILL.md` decision table).

### 1b. SKILLS — concrete example

`loom/.claude/skills/skill-authoring/SKILL.md` frontmatter:

```yaml
---
name: skill-authoring
description: "Authoring or auditing skills (CC/Codex/Gemini). Frontmatter, description ≤200 chars, progressive disclosure, variant overlays."
tools:
  - Read
  - Glob
  - Grep
---
```

Key facts: the **`description:` field IS the activation mechanism** — selection is semantic (LLM matches _failure-mode language_), not keyword. Cap **≤200 chars** (`cc-artifacts.md` Rule 1b). Real evidence cited in that rule: on 2026-05-06, **47 of 47 skill descriptions were dropped from the CC listing** because cumulative description bytes exceeded the ~1% listing budget; trimming the worst 18 to ≤200 chars restored visibility. SKILL.md body must answer ~80% of routine questions without sub-file reads (progressive disclosure, `cc-artifacts.md` Rule 2). Sub-files load on demand via explicit cross-reference.

### 1c. RULES — concrete example

`loom/.claude/rules/journal.md` frontmatter:

```yaml
---
priority: 10
scope: path-scoped
paths:
  - "journal/**"
  - "**/journal/**"
---
```

Key facts: `scope:` is one of `baseline` (always-on), `path-scoped` (loads only when editing a matching path), or `skill-embedded` (inlined into a skill, reaches the model only when the skill is active — `skill-authoring/SKILL.md` § Skill-Embedded Rule Pattern). The harness recognizes **`paths:`** for scoping; `globs:` is NOT a recognized key and would silently load the rule on every file (`cc-artifacts.md` Rule 5). Rule bodies use a `<!-- slot:neutral-body -->` / `<!-- slot:examples -->` partition so the splitter can keep the semantic body byte-identical across CLIs while letting examples diverge (see §6). Each rule carries DO / DO NOT examples + a **Why:** rationale + (for post-2026-05-05 rules) a `## Trust Posture Wiring` section.

### 1d. HOOKS — concrete example

`loom/.claude/hooks/user-prompt-rules-reminder.js` (event `UserPromptSubmit`) injects critical rules into the conversation on **every** user message — "the PRIMARY mechanism that survives context compression, because it runs fresh on every turn (independent of memory)." Every hook installs a `setTimeout` fallback that emits `{continue: true}` and exits before the runtime kill window (`cc-artifacts.md` Rule 7 — "a hanging hook blocks the entire session indefinitely"). Hooks check **structure** (path prefix, env var, exit code, AST shape), never semantics (semantics is the agents' job at gate review — `cc-artifacts.md` MUST NOT "No semantic analysis in hooks"). Halting branches must route through `lib/instruct-and-wait.js::emit()` with six fields (severity, what_happened, why, agent_must_report, agent_must_wait, user_summary) so a blocked tool call becomes a structured handoff rather than an opaque "Execution stopped by hook" (`hook-authoring/SKILL.md` § Output Discipline).

### 1e. COMMANDS — concrete example

`loom/.claude/commands/codify.md` frontmatter:

```yaml
---
name: codify
description: "Load phase 05 (codify) for the current workspace. Update existing agents and skills with new knowledge."
---
```

Key facts: body **≤150 lines** (`cc-artifacts.md` Rule 3) because commands "inject as user messages and compete with the actual user prompt." Reference content → skills; review rubrics → agents; boundary enforcement → rules (`command-authoring/SKILL.md` decision table). Some commands map to a CLI's **native primitive** and are deliberately NOT emitted (e.g. `/review` → Codex's native `codex review`; see §6).

---

## 2. loom as the source-of-truth "splitter"

loom is the **central splitter/distributor** — it does NOT originate artifact changes. The authority chain (`loom/.claude/rules/artifact-flow.md`):

- **atelier/** — CC + CO methodology authority (the base discipline).
- **loom/** — COC authority + central splitter. _"loom Splits, Never Originates."_
- **BUILD repos** (`kailash-py`, `kailash-rs`, `kailash-prism`) — SDK source; originate code proposals.
- **USE-template repos** (`kailash-coc-claude-{py,rs}`, `kailash-coc-{py,rs}`) — originate COC-artifact proposals; ALSO distribution points.
- **downstream consumers** (end-user projects, kaizen-cli-py, etc.) — pull-only.

### 2a. Variant overlay system (global vs language vs CLI)

Single source + overlays (`loom/.claude/guides/co-setup/05-variant-architecture.md`, `loom/.claude/variants/README.md`). Every artifact belongs to exactly **one tier**: `cc` (Claude-Code-universal), `co` (methodology-universal), `coc` (codegen, language-agnostic), or a language variant. The variant tree (`loom/.claude/variants/`) holds axes:

- Language: `py/`, `rs/`, `prism/`, `base/`
- CLI: `codex/`, `gemini/`
- Ternary (language × CLI): `py-codex/`, `py-gemini/`, `rs-codex/`, `rs-gemini/`

**Overlay semantics** (`artifact-flow.md` § Variant Overlay Semantics):

- _Replacement_ — variant file + global file both exist → **variant wins**.
- _Addition_ — variant exists, no global → **added**.
- _Global only_ — no variant → global used as-is.

So one artifact authored once at `.claude/rules/foo.md` propagates as-is to every target unless a `variants/<axis>/rules/foo.md` overrides one slot. The tier and overlay mappings are all declared in `loom/.claude/sync-manifest.yaml` (150KB; tiers at line 605, variants at 1069, variant_only at 1584, repos at 2161).

### 2b. Gate-1 classification + Gate-2 distribution

`/sync` (`loom/.claude/commands/sync.md`) runs two sequential gates at loom:

- **Gate 1 (inbound — review + scrub + classify):** ingests proposals from the BUILD stream and the USE-template stream. **A human classifies each change** as _Global_ (`.claude/{type}/{file}`, all targets), _Variant_ (`.claude/variants/{lang}/{type}/{file}`, one target), or _Skip_. "Automated suggestions permitted; automated placement is not" (`artifact-flow.md` § Human Classifies Every Change). A **disclosure-scrub runs first** (`scan-synced-disclosure.mjs --root`) — a proposal body reaches 30+ consumers once split, so any client/operator identifier must be genericized before placement (`artifact-flow.md` § Intake Disclosure Scrub).
- **Gate 2 (outbound — distribute):** merges loom source + variant overlays into each USE template per that repo's `tier_subscriptions`. This is a _merge_ (templates may have legitimate local content), not an overwrite. Steps include: compute expected state for the target, per-file merge decision (UNCHANGED/NEW/MODIFIED/TEMPLATE-ONLY), present merge plan (no bulk "apply all"), apply, update `.coc-sync-marker` + `.claude/VERSION`, bump SDK pins, install deps, verify hooks (`sync.md` Step "Two Gates").

`/sync` is the **only outbound path** ("No other command or manual process" — `artifact-flow.md`). Pre-emit validation (`validate-emit.mjs`) gates 7 structural invariants before Gate 1; a remote-freshness check prevents distributing from a stale local main.

### 2c. How one artifact propagates to many consumers

```
author once at loom/.claude/rules/foo.md (or a proposal from a USE-template /codify)
   │  Gate 1: human classifies global vs variant; disclosure-scrubbed
   ▼
loom/.claude/{rules/foo.md  OR  variants/py/rules/foo.md}
   │  Gate 2: /sync py|rs|all  →  apply variant overlay per tier_subscriptions
   ▼
kailash-coc-claude-py, kailash-coc-py, kailash-coc-claude-rs, kailash-coc-rs, coc-base …
   │  each downstream end-user project runs its OWN /sync to pull
   ▼
30+ downstream consumer repos
```

### 2d. The obsoletion mechanism (purge across all consumers)

Additive sync preserves target-only files, **except** paths declared in the manifest's `obsoleted:` list (line 1799), which are deleted on every sync (`~/repos/.claude/rules/cross-repo.md` Rule 4). This is "the ONLY mechanism by which 30+ downstream repos can purge stale orphan directories." Live example in the manifest: `variants/` itself is obsoleted from consumers (2026-06-01) after a leak of operator-PII hostnames was found in a consumer's tracked `variants/` tree — a single declarative entry drives the universal purge. **This is the cross-org "recall a bad artifact" primitive the marketplace will need.**

---

## 3. The authoring / codify lifecycle

### 3a. `/codify` originates proposals (`loom/.claude/commands/codify.md`)

`/codify` is COC phase 05. Its flow:

1. **Acquire codify lease** (`hooks/lib/codify-lease.js`) — two concurrent `/codify` runs would clobber the rule corpus, so a lease over the scope files (`.proposals/latest.yaml`, `learning-codified.json`, `sync-manifest.yaml`) gates it. Live lease state at `loom/.claude/learning/codify-lease.json` shows the scope fingerprint, branch (`codify/<display_id>-<date>`), and release timestamp.
2. **Consume the learning digest** — read `learning-digest.json` (structured summary of observations captured by hooks into `observations.jsonl`), `learning-codified.json` (what was already done), recent journal DECISION/DISCOVERY entries, and `.session-notes`. This closes the loop: **observe → digest → codify into real artifacts.**
3. **Deep knowledge extraction** from `docs/` + `specs/`.
4. **Update agents / skills / rules** in canonical locations (with `cc-architect` enforcing `cc-artifacts.md` compliance).
5. **Trust Posture Wiring (MANDATORY for new rules)** — every new rule gets a `## Trust Posture Wiring` section (8 canonical fields); cc-architect FAILS the codify if it's missing.
6. **Create the upstream proposal**, routed by repo class (BUILD / USE-template / loom / downstream).

### 3b. The `.proposals` manifest (`loom/.claude/.proposals/latest.yaml`)

The proposal is the unit of artifact change that flows to the splitter. Its three-state lifecycle (`artifact-flow.md` § Proposal Lifecycle):

```
/codify creates           /sync Gate 1 classifies        /sync Gate 2 distributes
pending_review ──────────► reviewed ─────────────────────► distributed
```

Live example fields from `latest.yaml` (a real distributed proposal): `source_repo`, `codify_date`, `status: distributed`, `distributed_targets: [kailash-coc-claude-py, kailash-coc-py, kailash-coc-claude-rs, kailash-coc-rs, kailash-coc-claude-rb]`, and a `changes:` array where each entry carries `file`, `action`, `suggested_tier`, `canonical_path`, `reason`, `diff_lines`, `trust_posture`, `follow_up`, and `adaptation_notes` (e.g. "Drop-in for atelier. The five conditions are CLI- and language-agnostic … so no variant overlay or slot partition is required — emits globally to all CLI targets unchanged"). The lifecycle is **append-never-overwrite**: a new `/codify` appends to an unprocessed proposal (overwriting `pending_review` is "silent data loss" — `artifact-flow.md` MUST: Append, Never Overwrite).

### 3c. End-to-end: issues → codify → loom → sync

```
issue routed by change TYPE
  ├─ COC-artifact (method/rule/skill/agent)  → USE-template repo → /codify → proposal ─┐
  ├─ SDK code bug/feature                     → BUILD repo → cross-SDK-first → /codify ─┤
  └─ CC/CO methodology                        → atelier → /sync-to-coc ────────────────┤
                                                                                       ▼
                                          loom SPLITTER (Gate-1 human classify + scrub)
                                              ├─ /sync-to-build → BUILD repos
                                              └─ /sync → USE templates → downstream pull
```

A narrow exception (`artifact-flow.md` § Co-Owner-Directed Origination) lets loom originate directly when a co-owner directs it in-session AND a journal `DECISION` entry with the verbatim directive lands BEFORE the edit — the journal entry IS the audit trail that the splitter rule otherwise requires.

---

## 4. What makes a well-formed artifact (the three authoring skills)

loom ships three meta-skills — themselves COC artifacts — that encode the authoring contract. They live in the `co` tier (universal methodology) and are explicitly multi-CLI by body design.

### 4a. `skill-authoring` (`loom/.claude/skills/skill-authoring/SKILL.md`)

- `name:` matches directory; `description:` **≤200 chars**, _failure-mode language_, **no keyword-dump** (≥4 quoted alternates BLOCKED).
- `tools:` (preferred neutral form) vs `allowed-tools:` (legacy CC form the emitter renames).
- SKILL.md body 150–250 lines, answers **80%** without sub-file reads; sub-files surfaced via index.
- `MANDATORY` framing for strong preconditions.
- Variant overlays via slot markers; no CC-native delegation syntax in prose.

### 4b. `command-authoring` (`loom/.claude/skills/command-authoring/SKILL.md`)

- Three emissions per command: CC `.claude/commands/<n>.md` (Markdown), Codex `.codex/prompts/<n>.md` (Markdown passthrough — but invocation is now `bin/coc <name>` since Codex deprecated repo-local prompts), Gemini `.gemini/commands/<n>.toml` (TOML wrap).
- Body **≤150 lines**; neutral phrasing; native-primitive carve-outs (`cli_emit_exclusions`).
- Every new command MUST be wired into `sync-manifest.yaml` under a tier or it ships to nobody.

### 4c. `hook-authoring` (`loom/.claude/skills/hook-authoring/SKILL.md`)

- One script `.claude/hooks/<n>.js`, three runtimes; `COC_RUNTIME` env (`cc`/`codex`/`gemini`) + `lib/runtime.js::parseHook()` normalizes event names.
- Mandatory `setTimeout` fallback; halting branches via `instruct-and-wait.js::emit()`.
- **`severity: "block"` requires a structural/AST signal** — lexical regex matches may only be `halt-and-report`/`advisory` (`hook-output-discipline.md` MUST-2).
- **The Codex Bash-only gap + MCP-guard bijection** (see §5).
- Path resolution: `CLAUDE_PROJECT_DIR || GEMINI_PROJECT_DIR || payload.cwd` (Codex exports no project-dir var).

Each skill ends with an **Audit Checklist** — the same checklist `cc-architect` runs at `/codify`. This is the "well-formed artifact" definition operationalized.

---

## 5–6 are the multi-CLI dimension — see below.

## 5. The Codex Bash-only gap + MCP-guard bijection

A critical real-world constraint for _any_ multi-harness platform: **Codex hooks fire on Bash/shell tool invocations only.** `apply_patch` (Codex's file-write primitive), Write-equivalents, MCP tool calls, and web search/fetch do NOT fire `PreToolUse`/`PostToolUse` (`hook-authoring/SKILL.md` § Hook Coverage Gap; `codex-architect.md` § Hooks Coverage). So for non-Bash surfaces the `.claude/codex-mcp-guard/` MCP server is the only enforcement point — it wraps every non-Bash tool and re-runs the same predicate set. **Validator-13** (at `/sync` emit time) enforces a **bijection**: every predicate function in `.claude/hooks/*.js` MUST have a coverage-equivalent reject condition in `codex-mcp-guard/policies.json`, recognized via three AST shapes (A: `process.exit(N≥2)`; B: returns `{exitCode:N≥2}` routed to exit; C: returns `{isError:true, content}` — the MCP response form). Divergence hard-blocks the sync.

## 6. Multi-CLI parity / bijection / native-primitive carve-outs (envoy)

The same artifact is expressed across three harnesses under a strict contract (`loom/.claude/rules/cross-cli-parity.md`, mirrored in `envoy/.claude/rules/cross-cli-parity.md`; the orchestration agent is `loom/.claude/agents/cli-orchestrator.md`).

**Parity contract** (what MUST match vs MAY diverge):

- **MUST match (hard-block on drift):** the `neutral-body` slot byte-identical across CLIs; `frontmatter.priority`; `frontmatter.scope`. "Parity violations don't fail at emit time — they fail at user time, when a rule shipped to Codex is quietly weaker than the same rule shipped to CC."
- **MAY diverge (soft-warn):** the `examples` slot (CC uses `Agent(subagent_type=…)`, Codex uses `codex_agent(…)` / natural-language spawn, Gemini uses `@specialist`).
- **`scrub_tokens`** cover delegation _syntax_ only (`Agent(`, `codex_agent(`, `@specialist`, `subagent_type`, `run_in_background`) — extending them to semantic phrases (`MUST`, `never`) "turns the drift audit into a null check" and is BLOCKED.

**Surface mapping** (`codex-architect.md` § Codex-Native Primitives):

| CC surface                 | Codex equivalent                                              | Gemini equivalent                                          |
| -------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------- |
| `CLAUDE.md` baseline       | `AGENTS.md` (git-root→cwd walk)                               | `GEMINI.md`                                                |
| `settings.json` hooks      | `.codex/hooks.json` (Bash-only)                               | `.gemini/settings.json` `hooks` (`BeforeTool`/`AfterTool`) |
| `Agent(subagent_type=…)`   | natural-language spawn / `codex exec`                         | `@specialist`                                              |
| `SKILL.md`                 | `.codex/skills/<n>/SKILL.md` (native)                         | Gemini skill surface                                       |
| `/analyze`, `/todos` …     | `bin/coc <phase> "…"` dispatcher                              | `/<name>` (TOML command)                                   |
| `paths:` path-scoped rules | **NOT honored** — Codex uses directory-hierarchy loading only | **[UNCERTAIN]** — needs gemini-architect read              |

**Native-primitive carve-outs:** some CC commands map to a CLI's own native primitive; emitting a copy would shadow it. `/review` → Codex's native `codex review` → declared in `sync-manifest.yaml::cli_emit_exclusions.codex`. New commands with a native counterpart MUST add an exclusion entry before landing (`command-authoring/SKILL.md` § Native-Primitive Carve-Outs).

The **single-source contract**: one author edits the canonical `.claude/<type>/<name>`; the emitter (`bin/emit-cli-artifacts.mjs`, driven by `coc-sync`) produces the three CLI surfaces, applying overlays + the parity check + byte-budget abridgement. The `cli-orchestrator` agent's five verbs (`sees`/`arbitrates`/`guides`/`audits`/`orchestrates`) bound each step to ≤10 invariants per the capacity budget.

---

## 7. CRITICAL SYNTHESIS — loom machinery → cross-org work-artifact registry

The brief wants artifacts "easily created, modified, stored, and shared across organizations and teams." loom already does this for **one org's codegen artifacts**. Mapping:

| Marketplace requirement | What EXISTS in loom (reuse)                                                                                                                    | What's MISSING / to adapt                                                                                                                    |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Created**             | Five-layer taxonomy + three authoring meta-skills + `/codify` origination from observed work                                                   | Generalize "codegen" → general work domains (the taxonomy is already domain-agnostic in shape)                                               |
| **Modified**            | Proposal lifecycle (`pending_review→reviewed→distributed`), append-never-overwrite, codify-lease concurrency gate, versioned `.claude/VERSION` | Per-org fork/version semantics; visible change-review UI for non-coders                                                                      |
| **Stored**              | Canonical single-source tree + tier classification in `sync-manifest.yaml`; obsoletion list for recall                                         | A _registry/index_ surface (search, discovery, ratings) — does not exist; today discovery is the manifest + `description:` semantic matching |
| **Shared across orgs**  | Two-gate `/sync` splitter, variant overlays (language×CLI), 30+ downstream consumers, multi-CLI parity                                         | **Cross-ORG** trust boundary; today all targets are clones of ONE GitHub remote under bounded-trust                                          |

### 7a. The 80% that is directly reusable

1. **Layer taxonomy + format contracts** — agents/skills/rules/hooks/commands with the exact frontmatter/line-cap/scope discipline. Domain-agnostic by construction (`cc-artifacts.md` is about _artifact shape_, not codegen).
2. **The splitter** — `/sync` two-gate, human-classify, variant-overlay, additive-with-obsoletion. This IS the "share across teams" engine. A registry is `loom` with a discovery surface bolted on.
3. **Variant overlay engine** — global-vs-specialized resolution (replacement/addition/global-only) generalizes from language×CLI to _org-default vs org-override_. Today: `variants/py/rules/foo.md` overrides `rules/foo.md`. Tomorrow: `variants/<org>/rules/foo.md`.
4. **Proposal lifecycle + codify** — the create/modify path with audit trail, lease concurrency, and disclosure-scrub-on-intake (the intake scrub is _exactly_ the cross-org safety gate, already built).
5. **Multi-CLI parity + bijection + carve-outs** — the platform is "harness-agnostic" (brief 3e); envoy already proves the same artifact across Claude Code/Codex/Gemini with a hard parity contract.
6. **Recall primitive** — the `obsoleted:` declarative purge pulls a bad artifact from every consumer on next sync (the marketplace "unpublish/recall" requirement, already shipping).

### 7b. The 15% to adapt

1. **Cross-ORG distribution boundary.** Today every target is a clone of ONE remote. A marketplace needs org-A authoring → org-B consuming with no shared remote. The variant axis and tier subscriptions are the right _shape_; the missing piece is publish/subscribe across org boundaries (the manifest's `repos:` block would become a cross-org subscription registry).
2. **Discovery/registry surface.** loom has no search/index/rating; discovery today = the manifest + skill `description:` semantic matching. A marketplace needs a catalog. **Reusable foundation:** the `description:`-as-activation pattern is already a semantic discovery primitive.
3. **De-couple "codegen."** Tiers are `cc`/`co`/`coc`/language; a general-work platform needs work-domain tiers (finance, legal, ops…). Mechanically identical to adding a tier in `sync-manifest.yaml`.
4. **Non-coder authoring UX.** The brief (3a) says users aren't coders, but artifacts today are hand-authored Markdown/JS. `/codify`-from-observed-work is the bridge — generalize "observe a session, propose an artifact" to non-coding work.

### 7c. The 5% genuinely new

1. **Untrusted third-party trust model.** loom's `multi-operator-coordination.md` threat model is **bounded-trust** — "the adversary is a legitimate team member with repo write access." A cross-org marketplace faces _untrusted publishers_. The cryptographic substrate (commit-signing keys, hash-chained coordination log, 2-of-N quorum, `refs/coc/**` server rulesets) is a strong starting point, but signed-artifact provenance from an _external_ publisher (vs an enrolled operator) is not yet modeled.
2. **Asymmetric publish/consume governance.** The closest existing precedent is `aegis/.claude/rules/aegis-fork-relationship.md`: the canonical product MUST stay generic; client forks adapt; **fork→product upstreaming allowed, product→fork client-leakage BLOCKED.** This asymmetric model (generic registry artifact ↔ org-specific override; upstream-generic-only) is the exact governance shape a cross-org marketplace needs, and it already exists as a baseline rule in the commercial fork.
3. **Marketplace-grade versioning/licensing/attribution** for third-party artifacts — provenance capture exists (`hooks/provenance-capture-tool.js`, `learning/provenance/`), but licensing/attribution for shared work artifacts is unbuilt.

### 7d. Architectural recommendation (autonomous-execution framing)

The platform should treat loom's splitter as the **artifact control plane** and build the registry/marketplace as a thin discovery+publish surface ON TOP of it, not a rewrite. Estimated autonomous-execution sizing: generalizing tiers + adding org-axis variants is **~1 session** (mechanical manifest + overlay work, high feedback loop); the cross-org publish/subscribe registry surface is **~3–5 sessions** (new surface, needs the untrusted-publisher trust model designed first); the untrusted-provenance trust model is a **novel-architecture decision** (greenfield, ~2–3× first-session factor per `autonomous-execution.md`) and should be designed before the registry surface is built, since it constrains it.

---

## 8. Open questions / uncertainty flags

1. **[UNCERTAIN]** Gemini's exact equivalent for `paths:` path-scoped rules and its native-primitive carve-out list — needs a `gemini-architect.md` read (not done in this pass).
2. **[UNCERTAIN]** Whether the multi-CLI USE repos (`kailash-coc-py`, `kailash-coc-rs`) are fully live yet — the manifest header (lines 105–106) says "Pre-Phase-E6 (today): the multi-CLI USE repos do not yet exist; current sync targets are `kailash-coc-claude-*`." So the multi-CLI distribution may still be partly aspirational vs cc-only-legacy in production. **Flag for the platform: confirm production multi-CLI distribution status.**
3. How `/codify`-from-observed-work generalizes to **non-coding** work sessions (the learning system's `observations.jsonl` currently captures code-session signals like `file_counts.pythonFiles`).
4. Whether the registry should reuse loom's GitHub-clone distribution or move to a true pub/sub service — the brief's cross-org requirement pushes toward the latter, but loom's git-native model is the proven one.

---

## 9. Sources consulted

- Brief: `~/repos/projects/Sequor/workspaces/future-of-work/briefs/01-vision.md`
- Layer taxonomy: `~/repos/loom/.claude/rules/cc-artifacts.md`
- Authoring skills: `~/repos/loom/.claude/skills/{skill-authoring,command-authoring,hook-authoring}/SKILL.md`
- Splitter/lifecycle: `~/repos/loom/.claude/commands/{sync.md,codify.md}`, `~/repos/loom/.claude/rules/artifact-flow.md`
- Variant architecture: `~/repos/loom/.claude/guides/co-setup/05-variant-architecture.md`, `~/repos/loom/.claude/variants/README.md`
- Manifest: `~/repos/loom/.claude/sync-manifest.yaml` (tiers L605, variants L1069, obsoleted L1799, repos L2161)
- Proposal: `~/repos/loom/.claude/.proposals/latest.yaml`
- Multi-CLI: `~/repos/loom/.claude/rules/cross-cli-parity.md`, `~/repos/loom/.claude/agents/{cli-orchestrator.md,codex-architect.md}`, `~/repos/dev/envoy/.claude/rules/cross-cli-parity.md`, `~/repos/dev/envoy/specs/`
- Concrete artifacts: `~/repos/loom/.claude/agents/analysis/analyst.md`, `~/repos/loom/.claude/hooks/user-prompt-rules-reminder.js`, `~/repos/loom/.claude/rules/journal.md`
- Cross-org precedent: `~/repos/dev/aegis/.claude/rules/aegis-fork-relationship.md`
- Trust substrate: `~/repos/projects/Sequor/.claude/rules/multi-operator-coordination.md`, `~/repos/loom/.claude/learning/{codify-lease.json,observations.jsonl}`
- Cross-repo obsoletion: `~/repos/.claude/rules/cross-repo.md`
