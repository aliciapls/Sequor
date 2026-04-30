# GAP: Kaizen classifier accuracy is unvalidated

**Type:** GAP
**Date:** 2026-04-19

## Finding

Response accuracy spec uses 90%/60% confidence thresholds for auto-send vs. backup-routing decisions. These are placeholders. The actual Kaizen classifier accuracy on real SEA SME query corpus is unknown.

## Why This Matters

If classifier accuracy is 60% overall but 40% for the specific categories that determine automation (routine vs. complex), then the 90% confidence threshold is meaningless — the classifier is wrong 40% of the time at the decision boundary.

## Action Required

Before build: gather 200+ real queries from target users (SEA SMEs/nonprofits). Run Kaizen classifier against them. Measure precision, recall, F1 per category. Adjust thresholds based on actual accuracy. Without this validation, the response accuracy spec is built on assumptions.
