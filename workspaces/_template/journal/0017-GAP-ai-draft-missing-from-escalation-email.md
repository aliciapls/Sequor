---
type: GAP
date: 2026-05-05
status: open
priority: medium
---

# AI Draft Not Included in Escalation Emails

When confidence is 60-90%, the system generates an AI-suggested reply and sets `escalation_has_ai_draft=True`. But the escalation email sent to the human never includes this draft content.

**What happens today:** The human receives an escalation email saying "hey, this needs your attention" with the original customer message. They have to compose a reply from scratch.

**What should happen:** The email should include the AI's suggested reply so the human can review, edit, and send — turning a 5-minute task into a 30-second review. This is a key productivity feature for the target SME user who is not a professional support agent.

**The disconnect:** `EscalationService.create_escalation()` computes the response content but passes the escalation object to the email template without the AI draft. The template doesn't have a field for it either.

**Fix:** Pass `response_result.content` through to the escalation email template. Add a "Suggested reply" section in the email body when present. The human can copy-edit it into their reply.
