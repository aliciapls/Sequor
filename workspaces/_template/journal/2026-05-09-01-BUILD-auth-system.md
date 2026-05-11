---
name: "2026-05-09-portal-real-backend"
description: "Built real portal backend: JWT auth, portal API endpoints, wired all portal pages to real data"
type: project
---

# Portal Real Backend Build

## What

Built the real operator portal backend from demo/stub code to functional production-quality system.

## Why

Portal was entirely demo code — client-side "auth" with hardcoded credentials, all pages showed hardcoded fake data, zero real API endpoints existed. User (PE investor context) needed a real working product.

## How

### Auth system

- Added `password_hash` field to `BackupContact` model to support operator login
- Created `src/sequor/auth.py` — JWT-based auth with bcrypt password hashing via `python-jose` + `passlib`
- `POST /api/v1/auth/login` — verifies credentials, returns JWT in HttpOnly cookie
- `POST /api/v1/auth/logout` — clears cookie
- `GET /api/v1/auth/me` — returns current operator from JWT

### Portal API endpoints

- `GET /api/v1/portal/dashboard` — messages this week, auto-replied, open escalations
- `GET /api/v1/portal/messages` — recent messages with contact info
- `GET /api/v1/portal/escalations` — escalation queue with priority, status, assignee
- `GET /api/v1/portal/escalations/{esc_id}` — single escalation detail
- `GET /api/v1/portal/contacts` — contact list with channel preferences

### Frontend wiring

- `login.html` — replaced demo credential box + JS with real `fetch()` to `/api/v1/auth/login`
- `_portal.html` base — sidebar user info fetches from `/api/v1/auth/me`; logout calls `/api/v1/auth/logout`
- `dashboard.html` — stat cards, messages table, escalations list all fetch from real APIs
- `messages.html` — message history table fetches from `/api/v1/portal/messages`
- `contacts.html` — contact table fetches from `/api/v1/portal/contacts`
- `escalations.html` — escalation table fetches from `/api/v1/portal/escalations`

## Key decisions

- JWT in HttpOnly cookie (not localStorage) — prevents XSS token theft
- `passlib` with bcrypt — industry standard, not rolling our own
- Portal routes check cookie directly (not `_portal_guard` function which was a no-op stub)
- All API responses return JSON with structured payload keys (`{messages: [...]}`, not raw arrays)
