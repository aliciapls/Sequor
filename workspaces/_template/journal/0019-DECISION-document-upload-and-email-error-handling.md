---
type: DECISION
date: 2026-05-04
created_at: 2026-05-04T12:54:00.160Z
author: co-authored
session_id: f36cc689-282b-43a4-b21d-1eb50eea630a
project: sequor
topic: Document upload in onboarding and comprehensive email error handling
phase: implement
tags: [whatsapp, email, escalation, document-upload, retry, stripe-webhook]
---

# Document upload in onboarding and comprehensive email error handling

## Decision

Added POST /api/v1/onboarding/upload endpoint with Step 4 to signup form, and implemented comprehensive email error handling with retry logic, LLM failover, Stripe webhook verification, and escalation email failure handling.

## Context

The onboarding flow needed document upload capability for identity verification. Email notifications needed reliability improvements including:

- Retry with exponential backoff (3 attempts over ~35min)
- LLM failover wrapper (safe_generate returns should_escalate on failure)
- Stripe webhook signature verification and idempotency tracking
- Escalation email failure handling (sets notification_pending status)

## Implementation

**Document upload (TODO-18):**

- POST /api/v1/onboarding/upload endpoint
- Step 4 added to signup form with file upload widget
- Validates via DocumentUploadRequest schema
- Triggers ingestion pipeline

**Email error handling (TODO-24):**

- Exponential backoff: 0, 300, 1800 seconds (3 attempts)
- `safe_generate` returns `should_escalate=True` on LLM failure
- Stripe webhook HMAC-SHA256 signature verification
- Idempotency tracking for webhook deduplication
- Escalation email failure sets `notification_pending` status

## Consequences

- Users can now upload documents during onboarding
- Email failures no longer silently fail — retry with escalation fallback
- Stripe webhooks are verified and deduplicated
- 23 new unit tests covering these features

## Related

- Commit: b28c6433f671
- Supersedes: [Sequor onboarding gap analysis]
