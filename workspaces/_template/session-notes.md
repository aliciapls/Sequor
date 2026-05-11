---
name: "session-notes"
description: "Session notes — portal wiring sessions"
---

# Session Notes

## Commits

- `69fec5d` (2026-05-11): feat: redesign signup landing page — remove emoji, sharpen copy, align pricing
- `27ab119` (2026-05-11): feat: wire register.html to real signup API, remove demo hardcoding
- `ce5d7ba` (2026-05-11): feat: wire channels and subscription pages to real API endpoints

## What's done

**Auth:**

- `src/sequor/auth.py` — JWT via python-jose, bcrypt via passlib
- `POST /api/v1/auth/login|logout`, `GET /api/v1/auth/me`
- HttpOnly cookie, JWT in `sequor_session`

**Portal APIs:**

- `GET /api/v1/portal/dashboard|messages|escalations|escalations/{id}|contacts|documents`
- `POST /api/v1/portal/escalations/{id}/resolve`
- `GET /api/v1/portal/channels` — WhatsApp/SendGrid config from settings
- `GET /api/v1/portal/subscription` — plan, limits, live usage stats

**Frontend wired:**

- login, dashboard, messages, contacts, escalations, escalation detail, documents, keyphrases, auto-replies, channels, subscription

**Signup/Register:**

- `signup.html` — landing page redesign: no emoji, sharpened copy, GTM-aligned pricing grid
- `register.html` — wired to POST /api/v1/onboarding with correct OnboardingRequest payload
- Login page shows "Account created!" banner when redirected from signup

## Still pending

- Stripe billing portal: subscription page shows plan/usage but upgrade button is not wired to Stripe Checkout
- WhatsApp message templates table in channels.html is still static (meta templates require Meta API integration)

## GTM Brief Pricing Reference

- Free: $0 (50 msgs, 1 user, 3 docs)
- Solo: $15 (standalone, not per-seat)
- Starter: $35/seat/mo (3-5 seats, 200 msgs/seat, 5 docs)
- Professional: $55/seat/mo (5+ seats, unlimited msgs)
