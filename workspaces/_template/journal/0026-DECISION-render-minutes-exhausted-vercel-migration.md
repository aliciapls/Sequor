---
name: render-minutes-exhausted-vercel-migration
description: Render free tier minutes exhausted — journal decision to switch deployment platform
type: decision
---

# Decision: Migrate from Render to Vercel

## Trigger

Render free tier exhausted during development session. Every deploy burns
minutes; no further deploys possible until next billing cycle or plan upgrade.

## What's Deployed But Not Yet Live

Commit `9669d6c` — clean document hub UI (detail modal, key phrases popup,
delete endpoint). Pushed to `main`, awaiting deployment.

## Assessment: Can Vercel Host a FastAPI App?

**Short answer: yes, via Vercel Serverless Functions + a custom runtime.**

Vercel supports arbitrary Python runtimes via `vercel.json` and a
`vc==0.*` build step. FastAPI on Vercel uses:
- `@vercel/python` — Python runtime
- `vercel dev` / `vc build` pipeline
- ASGI adapter (`starlette`) with a custom entrypoint

Key constraints for Sequor's FastAPI on Vercel:
1. **No background tasks / lifespan events** — Vercel functions are
   stateless request/response; startup lifespan (`_app_lifespan`) runs
   on every cold start. Acceptable for `_reprocess_stuck_documents()`.
2. **No persistent process** — rate limiters are in-memory (already the
   case); no change needed.
3. **Database connectivity** — Vercel functions can reach the Render
   Postgres via its external connection string. Same as Render's runtime.
4. **Static files** — Vercel serves `static/` directly; FastAPI's
   `StaticFiles` mount works.
5. **Environment variables** — `DATABASE_URL`, `JWT_SECRET`,
   `ENCRYPTION_MASTER_KEY` need to be in Vercel project settings.

## Recommended Next Steps

1. Create `vercel.json` at repo root with Python runtime + custom build
2. Adapt `app.py` entrypoint to Vercel's Python runtime contract
3. Move env vars from `render.yaml` → Vercel project dashboard
4. Connect GitHub repo to Vercel for auto-deploy on push

## Blocking Questions

- Does Vercel free tier support external Postgres connections?
  (Hobby plan: yes, serverless functions can reach any internet endpoint)
- Does Sequor need background workers / cron? (If so, Vercel Cron or
  external task queue required)

## Status

**PENDING** — not started. Sequor repo is pushed; deployment platform
migration is the next decision to make.
