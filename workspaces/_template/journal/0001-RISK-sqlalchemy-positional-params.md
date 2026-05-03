# RISK: SQLAlchemy Positional Parameter Bug in auto_reply.py and ingestion.py

## Severity: CRITICAL

## What

PostgreSQL `$1, $2, $3` positional parameter notation used in SQLAlchemy `session.execute()` calls. SQLAlchemy expects `:name` named parameters or `text()` wrapper with bound parameters.

## Locations

- `src/sequor/email/auto_reply.py:247` — INSERT into responses
- `src/sequor/email/auto_reply.py:294` — SELECT from backup_contacts
- `src/sequor/email/auto_reply.py:316` — INSERT into escalations
- `src/sequor/ai/ingestion.py:291` — INSERT into documents

## Evidence

```python
await session.execute(
    """
    INSERT INTO responses
    (id, tenant_id, message_id, content, confidence_badge,
     confidence_score, was_auto_sent, sent_at)
    VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
    """,
    context.tenant_id,  # positional list — SQLAlchemy ignores this for $N placeholders
    context.message_id,
    ...
)
```

## Impact

- Will error at runtime when database is PostgreSQL
- OR will misbind parameters causing data corruption
- No tests exist to catch this — all 10 AI modules have ZERO tests

## Fix Required

1. Import `text` from sqlalchemy
2. Convert `$1, $2` to `:tenant_id, :message_id`
3. Pass parameters as dict: `session.execute(text(sql), {"tenant_id": ..., ...})`

## Status

Open — needs fix before merge
