---
type: DISCOVERY
author: co-authored
date: 2026-07-14
workspace: future-of-work
tags: [codify, patterns, convergence]
---

# DISCOVERY — R7+R8 Pattern Extraction Surface

## What was discovered

The R7 and R8 redteam cycles converged on 5 distinct, reusable patterns across 2 domains:

### Security domain (R8)

1. **str(e) in API responses** — The pattern is always: catch → `logger.warning("ctx",
error=str(e))` → return generic `JSONResponse`. The audit surface is grep-able:
   `grep -rn 'str(e)' src/ --include='*.py' | grep -v '_logger\|# \|logger\.'`

2. **Exception chain preservation** — `raise RuntimeError("generic") from e` preserves
   the traceback while keeping the message safe.

### AI Client domain (R7)

3. **NaN/Inf float guards** — `math.isfinite()` on every confidence/threshold read from
   DB or user input. Both write and read sides.

4. **Lenient JSON for LLM output** — LLMs produce malformed JSON frequently; always use
   lenient parsing with repair heuristics.

5. **Provider migration checklist** — grep for ALL old references, update `__all__`,
   check docstrings, verify factory function, document aliases.

## Why it matters

These are the patterns that cost the most redteam rounds to discover and fix. Without
codification, the next session that touches an API handler or AI client path will
re-introduce the same failure modes. The agent and skill make these patterns load
automatically when the relevant files are touched.
