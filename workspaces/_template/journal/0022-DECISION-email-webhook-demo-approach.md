# Decision: Email/Webhook Demo Approach

## Date: 2026-05-05

## Context

For the PE investor demo, we needed a way to show the full inbound email + WhatsApp → AI pipeline → portal update flow in real-time with an external groupmate.

## Options Considered

### 1. Curl simulation (CURRENT)

- Groupmate tells us what they'd type, we paste into curl command
- Webhook receives it, AI pipeline runs, portal updates
- Works today, no external setup needed

### 2. Mailgun Sandbox

- Free tier, no domain purchase needed
- Requires adding groupmate's email as Authorized Recipient
- Groupmate must verify email via Mailgun confirmation link
- Gets a sandbox address like `demo@sandbox123456.mailgun.org`
- Setup time: ~5-10 minutes if groupmate is available to verify

### 3. SendGrid + Domain MX Records

- Requires owning a domain (~$10-15/year)
- MX records must point to SendGrid
- Proper production-style setup
- More permanent but requires domain purchase + DNS config

## Decision

**PAUSED** — We decided to pause external email testing for now.

The curl simulation approach is sufficient for the demo. Future work: set up Mailgun sandbox or proper SendGrid domain if needed for actual production use.

## Next Steps (when resuming)

1. Get Mailgun sandbox account → get sandbox domain (e.g. `sandbox123456.mailgun.org`)
2. Add groupmate's email as authorized recipient
3. Groupmate confirms via email verification link
4. Set Mailgun Inbound Parse route to `https://badland-swizzle-childlike.ngrok-free.dev/api/v1/email/inbound`
5. Test end-to-end: groupmate sends real email → appears in portal

## Why This Matters

Email webhook integration is the primary inbound channel for the product. A working external demo would significantly strengthen the PE demo by showing a real email flowing through the entire pipeline.
