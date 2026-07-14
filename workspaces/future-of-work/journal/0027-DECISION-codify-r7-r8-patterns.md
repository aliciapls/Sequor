---
type: DECISION
author: co-authored
date: 2026-07-14
workspace: future-of-work
tags: [codify, r7, r8, security, ai-client]
---

# DECISION — Codify R7+R8 Security & AI Client Patterns

## Decision

Created two project artifacts capturing the institutional knowledge from the R7
(post-DeepSeek migration) and R8 (str(e) error message leakage) redteam convergence
cycles:

1. **Agent** `.claude/agents/project/security-sequor.md` — Sequor-specific security
   patterns: error message hygiene, AI client safety (NaN/Inf guards), system prompt
   injection defense, lenient JSON parsing, CI deploy idempotency.

2. **Skill** `.claude/skills/project/sequor-patterns.md` — Quick-reference patterns
   for the same surface: audit commands, provider migration checklist, key file map.

Both encode patterns that were learned across 5 redteam rounds (R7: 3 rounds, R8: 2 rounds)
and are now institutional knowledge that every future Sequor session loads.

## Why

These patterns are the highest-value extractable knowledge from the R7+R8 cycles:

- **str(e) leakage** (R8) — the #1 security pattern in this codebase. 9 sites fixed
  across 2 commits; the pattern (log real error → return generic message) must be
  preserved on every future API handler and AI client change.

- **NaN/Inf guards** (R7) — a same-class gap that recurred across write-side (R7-04)
  and read-side (M2). The pattern must be checked on every new confidence/float path.

- **Provider migration** (R7) — the MiniMax→DeepSeek migration left 5 stale references.
  The checklist prevents recurrence.

- **CI deploy idempotency** (R7) — `cancel-in-progress: true` with inline rationale.

## Self-referential gate

Not triggered — project agents and skills (`.claude/agents/project/`,
`.claude/skills/project/`) are outside the self-referential surface allowlist.
