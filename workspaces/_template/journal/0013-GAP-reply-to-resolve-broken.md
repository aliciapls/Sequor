---
type: GAP
date: 2026-05-05
status: open
priority: critical
---

# Reply-to-Resolve Is Broken

The core product promise — "your team replies to the escalation email and the item is resolved" — does not work end-to-end.

**Two missing pieces:**

1. **No inbound email webhook endpoint.** SendGrid has nowhere to POST incoming replies. There is no `POST /api/v1/email/inbound` route. Without it, customer replies to escalation emails vanish into the void.

2. **InboundEmailProcessor never resolves escalations.** Even if the webhook existed, `InboundEmailProcessor` only creates a new Message record. It never calls `EscalationService.resolve_escalation()`. The escalation stays open forever.

**Impact:** Every escalation that gets a human reply stays open indefinitely. SLA timers keep ticking. Digest emails show stale items. The learning loop never captures the human's answer. The human thinks they resolved it; the system disagrees.

**Fix:** Create inbound webhook endpoint in the email module. Wire `InboundEmailProcessor` to detect replies-to-escalation (match thread key or in-reply-to header) and call `resolve_escalation()` with the reply content.
