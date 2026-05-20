---
name: vercel-deployment-platform-migration
description: Migration from Render to Vercel for Sequor deployment
type: project
---

# Vercel Deployment Platform Migration

## Decision

**Why:** Render free tier build minutes exhausted, blocking all new deploys.

**How to apply:** Sequor deploys to Vercel instead of Render. Code committed to GitHub automatically triggers Vercel deploys.

## Key Changes

### 1. Vercel Runtime Fix

The `@vercel/python` runtime requires a top-level ASGI app object named `application` or `app`, not an async function handler.

**File:** `api/index.py`

```python
# BEFORE (broken)
async def handler(req, context):
    # async function handler — Vercel can't find the app

# AFTER (working)
from sequor.onboarding.app import app
application = app  # top-level ASGI app
```

**Why:** `@vercel/python` inspects the module for an `app`/`application` object at import time. An async function wrapper doesn't satisfy this.

### 2. Vercel Configuration

**File:** `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": { "installCommand": "pip install -e ." }
    }
  ],
  "routes": [{ "src": "/(.*)", "dest": "api/index.py" }]
}
```

### 3. Environment Variables Required on Vercel

| Variable                | Value                        | Required                               |
| ----------------------- | ---------------------------- | -------------------------------------- |
| `DATABASE_URL`          | PostgreSQL connection string | Yes                                    |
| `JWT_SECRET`            | `openssl rand -hex 32`       | Yes                                    |
| `ENCRYPTION_MASTER_KEY` | `openssl rand -base64 32`    | Yes                                    |
| `APP_ENV`               | `production`                 | Yes                                    |
| `OPENAI_API_KEY`        | OpenAI API key               | No — falls back to BM25 keyword search |

**Note:** User chose NOT to use OpenAI API key — cost reason. Documents will use BM25 keyword search instead of semantic embeddings.

### 4. Ollama Embedding Fallback

**File:** `src/sequor/ai/client.py`

Ollama is unavailable on Vercel (no local process). OpenAI `text-embedding-3-small` used as fallback. Without OpenAI key, chunks are stored without embeddings and document is marked `ready` (BM25 fallback).

### 5. Startup Document Repair

**File:** `src/sequor/onboarding/app.py`

`_reprocess_stuck_documents()` now actually UPDATES stuck documents to `ready` status on every app startup — previously only logged without fixing.

## Commit History (this migration)

- `cd23c98` fix: expose FastAPI app as ASGI 'application' for @vercel/python runtime
- `6e5bd36` (prior session) fix: openai embedding fallback, stuck document repair

## Status

Awaiting Vercel deployment confirmation from user. User to add env vars in Vercel dashboard → Settings → Environment Variables, then deploy.

## Related

- `workspaces/_template/journal/0026-DECISION-render-minutes-exhausted-vercel-migration.md` — prior decision log
