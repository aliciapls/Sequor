# GAP: Document Status State Machine Not Implemented

## Severity: HIGH

## What

Documents are created directly with `status=DocumentStatus.ready` instead of the spec-required `pending → indexing → ready` flow.

## Location

`src/sequor/ai/ingestion.py:281`

## Spec Requirement

From `specs/rag-pipeline.md` § "Index Age Tracking":

> Upload generates a `Document` record with status `pending`
> Index is ready when all chunks are stored and indexed; `Document.status` → `ready`

## Evidence

```python
# Current code:
await session.execute(
    """
    INSERT INTO documents
    ...
    VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, :status, ...)
    """,
    ...
    "status": DocumentStatus.ready,  # Direct to ready — no pending/indexing flow
)
```

## Impact

- No user feedback during indexing (UI can't show "indexing in progress")
- Can't detect stuck indexing jobs
- Staleness detection can't work properly (no indexing timestamp)

## Fix Required

1. Create document with `status=pending`
2. Update to `status=indexing` when chunking starts
3. Update to `status=ready` when all chunks stored

## Status

Open — needs fix
