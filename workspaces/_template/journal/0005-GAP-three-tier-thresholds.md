# GAP: Three-Tier Confidence Thresholds Not Implemented

## Severity: HIGH

## What

Only two confidence tiers implemented instead of the three tiers specified in `specs/response-accuracy.md`.

## Location

`src/sequor/ai/response.py:103-113`

## Spec Requirement

From `specs/response-accuracy.md` § "Response Options":

- > 90%: auto-reply to contact
- 60-90%: generate escalation email WITH AI draft for review
- < 60%: generate escalation email WITHOUT AI draft

## Current Implementation

```python
# Only two tiers:
was_auto_sent = (
    classification.confidence >= 0.9
    and classification.category in [...]
    and synthesis.confidence_badge in ["high", "moderate"]
)
escalation_needed = (
    synthesis.confidence_badge == "uncertain"
    or synthesis.confidence_score < 0.3
    or classification.category == MessageCategory.COMPLEX
)
```

## Impact

- Users in the 60-90% confidence range don't get an AI draft to review
- Escalation emails at all confidence levels below 90% look the same
- No way to give users "here's what AI thinks, please review and edit"

## Fix Required

Implement three tiers:

- > 90%: auto-reply (current behavior)
- 60-90%: escalate WITH AI draft (new — currently same as <60%)
- < 60%: escalate WITHOUT AI draft (current = all non-auto-reply)

## Status

Open — needs fix
