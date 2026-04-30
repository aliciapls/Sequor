# GAP: Internal docs assumption is false for target market

**Type:** GAP
**Date:** 2026-04-19

## Finding

The brief assumes internal documents exist in retrievable format (FAQs, rosters, price lists). The target market (lean SMEs/nonprofits) largely lacks these in structured form:

- FAQs: locked in WhatsApp chat histories, email threads, or not written down
- Rosters: emailed spreadsheets or whiteboards
- Price lists: business cards or outdated PDFs

## Implication

The RAG pipeline value proposition fails at the input stage unless a document preparation/onboarding layer is built. This layer does not yet exist in the spec.

## Action Required

Before building, audit 5-10 actual target orgs' document state. If most lack structured docs, either: (a) scope RAG out of v1, or (b) build doc preparation onboarding as a core feature, not an afterthought.
