---
type: DECISION
date: 2026-05-25
project: sequor
topic: Vercel + Neon deployment live, Render migration complete
phase: deploy
tags: [vercel, neon, deployment, serverless, encryption, login]
---

## Decision

Migrated production hosting from Render (free tier build minutes exhausted) to Vercel + Neon PostgreSQL. App is live at https://sequor.vercel.app.

## What Changed

- **Hosting**: Vercel serverless functions (`@vercel/python` runtime)
- **Database**: Neon PostgreSQL (free tier, serverless, auto-suspend)
- **Dependencies**: Stripped all 8 unused Kailash SDK packages from Vercel build — bundle dropped from 992 MB to under 500 MB
- **Template rendering**: Bypassed Jinja2's LRUCache (broken in serverless) via `env.from_string()` direct rendering
- **Login flow**: Fixed EncryptedString chicken-and-egg — initial blind index lookup uses raw SQL to avoid triggering column decryption before tenant key is available
- **Blind index**: Signup now computes blind index from `owner_email` (not `backup_email`) since users log in with their owner email
- **Auto-login**: After signup, the app automatically logs the user in and redirects to dashboard instead of requiring a separate login step

## Bugs Fixed This Session

1. Bundle too large (992 MB > 500 MB limit) — removed unused Kailash SDK deps
2. `Jinja2Templates(auto_reload=True)` — unsupported kwarg in newer Jinja2
3. Missing `python-multipart` dependency for FastAPI form handling
4. `DATABASE_URL` empty on Vercel — env vars corrupted after project re-link, re-set all four
5. `ENCRYPTION_MASTER_KEY` and `JWT_SECRET` also empty — same root cause
6. Jinja2 LRUCache `unhashable type: 'dict'` in serverless — bypassed with `from_string()`
7. `init_db()` not called before querying tables on fresh database
8. Signup computed blind index from `backup_email` instead of `owner_email`
9. Login ORM query triggered `EncryptedString` decryption before tenant key was set
10. Login handler had broken indentation (code outside `async with` session block)
11. Signup redirected to login page instead of auto-logging in

## Alternatives Considered

- **Supabase**: Also free-tier PostgreSQL, but Neon has tighter Vercel integration
- **Railway**: $5 free credit, not truly free
- **Staying on Render**: Would require paid plan for build minutes

## Rationale

Vercel has no build minute charges (the exact thing that burned Render's budget). Neon pauses after inactivity, keeping costs at $0 during development. Both are sustainable for the building phase.

## Consequences

- Old accounts from Render database are gone — fresh start on Neon
- Vercel serverless functions have 10s execution limit (may need optimization later)
- Neon free tier has 0.5 GB storage limit
- Preview deployments won't have `DATABASE_URL` (Vercel requires branch-specific env vars for preview)

## Key Files

- `vercel.json` — Vercel build config
- `api/index.py` — ASGI entry point, adds `src/` to Python path
- `requirements.txt` — lean deps for Vercel (no Kailash SDK)
- `.vercelignore` — excludes `pyproject.toml` and `uv.lock` from build
- `.python-version` — tells Vercel to use Python 3.12
- `src/sequor/onboarding/app.py` — `_render()` bypasses Jinja2 cache, login uses raw SQL
- `src/sequor/onboarding/service.py` — blind index from `owner_email`, not `backup_email`
- `src/sequor/onboarding/templates/register.html` — auto-login after signup
