---
type: RISK
date: 2026-05-04
created_at: 2026-05-04T12:54:00.160Z
author: co-authored
session_id: f36cc689-282b-43a4-b21d-1eb50eea630a
project: sequor
topic: Red team findings - webhook verification, header injection, TOCTOU, stats correctness
phase: redteam
tags: [security, red-team, webhook, header-injection, toctou]
---

# Red team security fixes

## Summary

Addressed 12 findings from automated red team review spanning CRITICAL to MEDIUM severity.

## Critical Fixes

1. **SendGrid webhook HMAC-SHA256 signature verification**
   - Added to inbound email processing
   - Configurable via SENDGRID_WEBHOOK_VERIFICATION_KEY

2. **Header injection prevention**
   - Applied `_sanitize_header` to all header-bound email fields
   - Added strict email address validation on to, reply_to, in_reply_to, escalation_id

3. **Digest stats triple-count bug fix**
   - rag_resolved_count now correctly counts responses with rag_retrieval_id
   - learned_answers_count now uses recent_learned instead of auto_responses

4. **Full-table scan replacement**
   - find_breach_escalations now uses targeted read() calls
   - Uses collected backup/account IDs instead of scanning entire table

## High Fixes

5. **send_escalation_email added to EmailSender protocol** — was a runtime crash
6. **TOCTOU race guard** — re-verifies after status update, added status check to escalate_to_second_tier
7. **Attachment filename sanitization** — prevents path traversal via basename + null byte stripping
8. **Null byte and CRLF stripping** — applied to all parsed email header values

## Medium Fixes

9. **default_confidence_threshold range validation** — [0.0, 1.0]
10. **datetime.utcnow() deprecated** — replaced with datetime.now(timezone.utc)
11. **EscalationNotFoundError guard** — added to acknowledge_escalation
12. **10-second shutdown timeout** — added to SLA scheduler stop()

## Risk Assessment

All CRITICAL and HIGH findings resolved. Medium fixes applied to improve robustness. System is significantly more resistant to injection attacks and race conditions.

## Related

- Commit: 7425cefb1358
