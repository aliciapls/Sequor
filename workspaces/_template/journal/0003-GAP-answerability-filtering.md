# GAP: Answerability < 0.3 Filtering Not Implemented

## Severity: HIGH

## What

The `min_answerability` parameter is defined in `VectorStore.search()` but never used to filter passages. Per spec, passages with answerability < 0.3 should be excluded even if vector similarity is high.

## Location

`src/sequor/ai/vector_store.py:106`

## Spec Requirement

From `specs/rag-pipeline.md` § "Retrieval Confidence Scoring":

> If answerability < 0.3, the passage is excluded even if vector similarity is high.

## Evidence

```python
# Parameter defined:
min_answerability: float = 0.3,  # line 106

# But never used in filtering logic — code only computes scores, doesn't filter
for chunk in chunks:
    combined_score = ...
    # Missing: if combined_score < min_answerability: continue
```

## Impact

Low-quality passages with high vector similarity but low answerability pass through to synthesis. This increases hallucination risk and reduces response quality.

## Fix Required

Add filtering logic after computing answerability:

```python
if combined_score < min_answerability:
    continue  # skip this passage
```

## Status

Open — needs fix
