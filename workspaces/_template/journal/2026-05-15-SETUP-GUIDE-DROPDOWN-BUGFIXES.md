# Session: Setup Guide Dropdown + Bug Fixes — 2026-05-15

## What Happened

Continued work on the FAQ/Setup Guide page and fixed several bugs that emerged.

## Changes Made

### FAQ/Setup Guide — Accordion Style

Converted from always-open cards to collapsible accordion dropdowns. Each section (WhatsApp, Email, Documents) starts collapsed and expands on click.

**Files:** `src/sequor/onboarding/templates/faq.html`

### Escalation Badge — Hidden by Default

Fixed escalation badge in sidebar to only show when count > 0. Was showing "0" or stale value.

- Added `escalation_count` to `/api/v1/portal/me` response from database query
- Badge uses `display:none` inline by default, `.visible` CSS class to show
- JS hides badge when count is 0, shows when count > 0

**Files:** `src/sequor/onboarding/templates/_portal.html`, `src/sequor/onboarding/app.py`

### Portal Me Endpoint — Crash Fix

The escalation count query was crashing `/api/v1/portal/me` for all users, breaking user info display on every page.

Wrapped entire endpoint in try/except — returns defaults (empty name/email, escalation_count=0) if any step fails, so user info always loads.

**Files:** `src/sequor/onboarding/app.py`

### Template Caching — Root Cause

`Jinja2Templates(directory=str(TEMPLATES_DIR))` was caching compiled templates in server memory. `auto_reload=True` added so template changes are reflected without server restart.

**Files:** `src/sequor/onboarding/app.py`

### Setup Guide Icon

Changed icon from question mark (?) to a list/checklist icon (3 horizontal lines with bullets) to avoid looking like a help button.

**Files:** `src/sequor/onboarding/templates/_portal.html`, `src/sequor/onboarding/templates/channels.html`

## Commits Pushed

- `461358f` feat: escalation badge hidden, FAQ simplified, Setup Guide icon to list/checklist
- `1fc26a9` fix: add inline display:none to FAQ accordion bodies
- `e0f5ae7` fix: enable Jinja2 auto_reload to fix template caching
- `0732aa0` fix: TEMP marker to verify deployment (reverted)
- `9cb7561` fix: wrap portal_me in try/except, returns defaults on crash

## Files Changed

- `src/sequor/onboarding/templates/faq.html`
- `src/sequor/onboarding/templates/_portal.html`
- `src/sequor/onboarding/templates/channels.html`
- `src/sequor/onboarding/app.py`

## Still Pending / To Do

- WhatsApp and Email credential saving from UI (channels page credentials are read-only, stored as env vars)
- Verify escalation count API is working correctly (was crashing before fix)
