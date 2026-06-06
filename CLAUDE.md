# Kailash COC — Multi-CLI (Python)

This repository is configured with the **multi-CLI COC (Cognitive Orchestration for Codegen) setup** for building with the Kailash Python SDK. It ships the same institutional knowledge surface — agents, skills, rules, commands, hooks — to three driving CLIs: **Claude Code**, **Codex**, and **Gemini CLI**.

## Per-CLI Baselines

Each CLI loads its own root-level baseline file at session start:

| CLI         | Baseline file | Source                                                       |
| ----------- | ------------- | ------------------------------------------------------------ |
| Claude Code | `CLAUDE.md`   | this file (project-owned — preserved across syncs)           |
| Codex       | `AGENTS.md`   | regenerated from `.claude/rules/` via `.claude/bin/emit.mjs` |
| Gemini CLI  | `GEMINI.md`   | regenerated from `.claude/rules/` via `.claude/bin/emit.mjs` |

The rule set, framework directives, and philosophy are identical across the three. Divergence lives only in delegation syntax (`Agent(subagent_type=...)` on CC, native `@<agent>` on Gemini, `/prompts:<name>` on Codex) and per-CLI config trees (`.codex/`, `.gemini/`).

## Absolute Directives

These override ALL other instructions. They govern behavior before any rule file is consulted.

### 0. Foundation Independence — No Commercial Coupling

Kailash Python SDK is a **Terrene Foundation project** (Singapore CLG). It is fully independent. There is NO relationship between Kailash Python SDK and any commercial product, proprietary codebase, or commercial entity. Do not reference, compare with, or design against any proprietary product. Do not use language like "open-source version of X" or "Python port of Y." Kailash Python SDK IS the product — not a derivative of anything. This directive is the complete policy.

### 1. Framework-First

Never write code from scratch before checking whether the Kailash frameworks already handle it.

- Direct SQL / SQLAlchemy / Django ORM → **dataflow-specialist**
- Custom HTTP servers, FastAPI, Flask, custom routers → **nexus-specialist**
- Custom MCP server/client code → **mcp-specialist**
- Custom LLM wrappers, provider abstraction layers, agent loops → **kaizen-specialist**
- Custom RBAC / access control / audit logging → **pact-specialist**
- Custom training loops, feature stores, drift monitoring → **ml-specialist**
- Custom fine-tuning / LoRA / model serving → **align-specialist**

### 2. .env Is the Single Source of Truth

All API keys and model names MUST come from `.env`. Never hardcode model strings like `"gpt-4"` or `"claude-3-opus"`. Root `conftest.py` auto-loads `.env` for pytest. See `.claude/rules/env-models.md`.

### 3. Implement, Don't Document

When you discover a missing feature, endpoint, or record — **implement or create it**. Do not note it as a gap and move on. The only acceptable skip is explicit user instruction. See `.claude/rules/zero-tolerance.md`.

### 4. Zero Tolerance

Pre-existing failures MUST be fixed, not reported. Stubs are BLOCKED. Naive fallbacks are BLOCKED. SDK bugs get GitHub issues, not workarounds. See `.claude/rules/zero-tolerance.md`.

### 5. Recommended Reviews

- **Code review** (reviewer) after file changes — RECOMMENDED
- **Security review** (security-reviewer) before commits — strongly recommended
- **Real infrastructure recommended** in Tier 2/3 tests

### 6. LLM-First Agent Reasoning

When building AI agents: **the LLM does ALL reasoning. Tools are dumb data endpoints.** No if-else routing, no keyword matching, no regex classification in agent decision paths. Deterministic logic is BLOCKED unless the user explicitly opts in. See `.claude/rules/agent-reasoning.md`.

## Workspace Commands

Phase commands map 1:1 across the three CLIs. The prompt body is shared — only the invocation surface differs:

| Command      | Phase | CC syntax    | Codex syntax         | Gemini syntax |
| ------------ | ----- | ------------ | -------------------- | ------------- |
| `/analyze`   | 01    | `/analyze`   | `/prompts:analyze`   | `/analyze`    |
| `/todos`     | 02    | `/todos`     | `/prompts:todos`     | `/todos`      |
| `/implement` | 03    | `/implement` | `/prompts:implement` | `/implement`  |
| `/redteam`   | 04    | `/redteam`   | `/prompts:redteam`   | `/redteam`    |
| `/codify`    | 05    | `/codify`    | `/prompts:codify`    | `/codify`     |
| `/release`   | —     | `/release`   | `/prompts:release`   | `/release`    |
| `/ws`        | —     | `/ws`        | `/prompts:ws`        | `/ws`         |
| `/wrapup`    | —     | `/wrapup`    | `/prompts:wrapup`    | `/wrapup`     |

Source-of-truth definitions live in `.claude/commands/`; Codex mirrors at `.codex/prompts/<name>.md`; Gemini at `.gemini/commands/<name>.toml`.

## Agent Invocation — Per-CLI Syntax

Semantics identical; syntax differs:

```python
# CC
Agent(subagent_type="dataflow-specialist", prompt="...")
```

```
# Codex: delegated through the Codex agent layer (see .claude/agents/codex-architect.md)
```

```
# Gemini: @<agent-name> — matches .gemini/agents/<name>.md
@dataflow-specialist <task>
```

## Rules Index

All rules live in `.claude/rules/` and apply to every CLI. Rule content is shared via loom's slot-keyed variant overlay system — see `.claude/rules/variant-authoring.md` + `.claude/rules/cross-cli-parity.md`.

Global baseline rules (always loaded):

- **Foundation independence** — Absolute Directive 0 above (stated inline; no separate rule file)
- **Autonomous execution model** — `rules/autonomous-execution.md`
- **Zero tolerance** — `rules/zero-tolerance.md`
- **Agent orchestration + quality gates** — `rules/agents.md`
- **Git workflow** — `rules/git.md`
- **Security** — `rules/security.md`
- **Communication style** — `rules/communication.md`
- **Cross-CLI parity** — `rules/cross-cli-parity.md`
- **Worktree isolation** — `rules/worktree-isolation.md`

Path-scoped rules (loaded when touching matching files):

- **LLM-first agent reasoning** — `rules/agent-reasoning.md` (`**/kaizen/**`, `**/*agent*`)
- **DataFlow pool** — `rules/dataflow-pool.md` (`**/dataflow/**`)
- **Env + models** — `rules/env-models.md` (`**/*.py`, `.env*`)
- **3-tier testing** — `rules/testing.md` (`tests/**`, `**/*test*`, `**/*spec*`)
- **Kailash patterns** — `rules/patterns.md` (`**/*.py`)
- **CC artifact quality** — `rules/cc-artifacts.md` (CC-only; excluded from Codex/Gemini emission)

The full rule corpus lives in `.claude/rules/` (66 rules); the list above highlights the always-on baseline plus the most common path-scoped rules. Every other rule loads automatically when you touch a file matching its scope.

**Note**: Codex and Gemini do NOT honor YAML `paths:` frontmatter for path-scoped loading — both CLIs use directory-hierarchy loading only. See `.claude/agents/codex-architect.md` and `gemini-architect.md` for the native-surface mappings.

## Agents

One `.claude/agents/` source tree; three surfaces. Specialist agents (`agents/frameworks/*`, `agents/implementation/*`, `agents/quality/*`, `agents/frontend/*`, `agents/testing/*`, `agents/release/*`, `agents/analysis/*`) emit to `.gemini/agents/<name>.md` for Gemini's `@<agent>` invocation. CC-specific agents (`cc-architect.md`, `cli-orchestrator.md`, architect meta-agents, `management/*`) stay CC-only.

## Critical Execution Rules

```python
# ALWAYS: runtime.execute(workflow.build())
# NEVER: workflow.execute(runtime)
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())

# Async (Docker/Nexus):
runtime = AsyncLocalRuntime()
results, run_id = await runtime.execute_workflow_async(workflow.build(), inputs={})

# String-based nodes only
workflow.add_node("NodeType", "node_id", {"param": "value"})

# Return structure is always (results, run_id)
```

## Kailash Platform

| Framework    | Purpose                                | Install                        |
| ------------ | -------------------------------------- | ------------------------------ |
| **Core SDK** | Workflow orchestration, 140+ nodes     | `pip install kailash`          |
| **DataFlow** | Zero-config database operations        | `pip install kailash-dataflow` |
| **Nexus**    | Multi-channel deployment (API+CLI+MCP) | `pip install kailash-nexus`    |
| **Kaizen**   | AI agent framework                     | `pip install kailash-kaizen`   |
| **PACT**     | Organizational governance (D/T/R)      | `pip install kailash-pact`     |
| **ML**       | Classical + deep learning lifecycle    | `pip install kailash-ml`       |
| **Align**    | LLM fine-tuning / serving              | `pip install kailash-align`    |

All frameworks are built ON Core SDK — they don't replace it.

## Project Memory Sync

The `.claude/` surface (and the `.codex/` / `.gemini/` mirrors + `AGENTS.md` / `GEMINI.md`) is distributed from the `kailash-coc-py` multi-CLI template via `/sync`. Re-run `/sync` to pull template updates; project application code (`src/`, `api/`, `specs/`, `tests/`, `deploy/`) is never touched by sync. `AGENTS.md` and `GEMINI.md` are regenerated from `.claude/rules/` — do not hand-edit them; edit the rules instead.
