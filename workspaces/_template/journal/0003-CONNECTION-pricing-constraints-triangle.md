# CONNECTION: Three-way constraint conflict connects market, product, and technical specs

**Type:** CONNECTION
**Date:** 2026-04-19

## Finding

Three constraints in the brief form an unsolvable triangle for the target market:

1. **"Low-cost for nonprofits/SMEs"** ↔ **Viable SaaS unit economics**: At $30/month nonprofit pricing, only optimistic self-serve with 3+ year retention works. At $50/month, human sales becomes viable but pricing excludes nonprofits. The brief does not pick a lane.

2. **"No technical setup required"** ↔ **RAG pipeline quality**: RAG quality requires document preparation. Document preparation requires user effort and some level of technical understanding. "Upload a PDF" does not work when the user has no PDFs.

3. **"Accurate responses always"** ↔ **Autonomous query resolution**: Human-in-the-loop (confidence badges, contact approval before send) is the only architecture consistent with the accuracy constraint. Without it, the product either violates its own accuracy rule or routes everything to humans, defeating automation value.

## Why This Is a CONNECTION

These three tensions were independently identified by three separate agents working on different analysis dimensions (market, technical, business). The fact that they are the same underlying contradiction — the brief's authors did not resolve the fundamental product design choices — means the conflict is structural, not resolvable by better implementation.

## Implication

Before the spec can be written correctly, three product design decisions must be made:

1. Price point: nonprofit-accessible ($20-30/month) or SME-focused ($100+/month)?
2. RAG scope: v1 with no RAG (pure routing/logging) or v1 with doc preparation onboarding?
3. Automation level: human-in-the-loop (contact approves before send) or fully autonomous with confidence thresholding?

Each combination produces a different product. The spec cannot be written until these decisions are made.
