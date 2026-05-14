# Session: FAQ / Setup Guide + Channel Pages — 2026-05-15

## What Happened

Created a new FAQ / Setup Guide page at `/portal/faq` with clear step-by-step instructions for connecting WhatsApp and Email channels, plus adding documents.

## Pages Created/Changed

### New: `/portal/faq` — Setup Guide

**File:** `src/sequor/onboarding/templates/faq.html`

Clear numbered step-by-step guides in card format:

**WhatsApp Setup (5 steps):**

1. Create Meta Business Account at business.meta.com
2. Create WhatsApp Business App, add your phone number
3. Copy Phone Number ID and Business Account ID
4. Generate a permanent access token in Meta developer portal
5. Enter credentials in Sequor at /portal/channels

**Email Setup (5 steps):**

1. Create SendGrid account (free tier works)
2. Authenticate your domain in SendGrid (Settings → Sender Authentication → Domain Authentication)
3. Add DNS records (CNAME + MX) at your domain registrar
4. Set up inbound parse webhook in SendGrid → point to the URL shown on Channels page
5. Enter your domain in Sequor at /portal/channels

**Documents Setup (3 steps):**

1. Go to Document Hub (/portal/documents)
2. Upload PDF/DOCX/TXT files for AI knowledge base
3. Add Key Phrase Maps (/portal/keyphrases) to link customer phrases to documents

### Changed: `/portal/channels` — Channels Page

**File:** `src/sequor/onboarding/templates/channels.html`

- Added "Setup Guide" button in top-right of page header, linking to /portal/faq

### Changed: `/portal/settings` — Settings Page

Multiple CSS fixes throughout session (see 2026-05-14 session log for full history)

- Final CSS: section padding drives horizontal space, row padding drives vertical, sibling border between sections

### Changed: Sidebar Navigation

**File:** `src/sequor/onboarding/templates/_portal.html`

- Added "Setup Guide" link (id="nav-faq") under Account section of sidebar

### Changed: App Route

**File:** `src/sequor/onboarding/app.py`

- Added route for `/portal/faq` (GET)

## Key Design Decisions

- **Minimal credentials** — users don't need to create API keys or open developer portals beyond what's described in the steps
- **All inline** — no external docs to maintain, instructions live right on the page
- **No account-saving yet** — WhatsApp credentials are still read-only (stored as env vars). A future session will add per-account credential storage so users can save their own credentials from the UI

## Commits Pushed (today)

- `b076b46` feat: add FAQ / Setup Guide page with step-by-step instructions
- `cdc3b86` feat: add Setup Guide link to sidebar navigation
- `656eec6` docs: journal settings page CSS rewrite session
- `c04d32d` fix: simplify settings CSS using section padding + sibling border
- `4d6394f` fix: match subscription page card-body spacing pattern
- `8747803` fix: use div instead of h3 for section labels
- `956205c` fix: tighten h3 spacing with line-height:1
- `50b785a` fix: unify settings page row spacing
- `c3a95cb` fix: rewrite settings page CSS for clean spacing
- `a77a793` fix: prevent footer text wrapping on signup page
- `04f2f27` feat: add show password toggle to login page

## Files Changed

- `src/sequor/onboarding/templates/faq.html` (NEW)
- `src/sequor/onboarding/templates/channels.html`
- `src/sequor/onboarding/templates/_portal.html`
- `src/sequor/onboarding/templates/settings.html`
- `src/sequor/onboarding/templates/login.html`
- `src/sequor/onboarding/templates/register.html`
- `src/sequor/onboarding/app.py`
- `workspaces/_template/journal/2026-05-14-SETTINGS-PAGE-REWRITE.md` (NEW)
- `workspaces/_template/journal/2026-05-15-SETUP-GUIDE-AND-CHANNEL-PAGES.md` (NEW)
