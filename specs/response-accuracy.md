# Response Accuracy — Governance and Escalation

## Core Design Principle

The brief states: "sending wrong information is worse than sending none." This is the binding constraint on the response pipeline. Every architectural decision flows from this.

The product's value = auto-replies that resolve routine queries.
The product's biggest risk = auto-replies that send wrong information.

These are in direct tension. The resolution is **human-in-the-loop for uncertain cases**.

---

## Response Options

### Option A: High Precision (Safe, Low Automation)

- Auto-respond only when: RAG confidence > 95% AND classifier confidence > 95%
- Route everything else to backup
- **Result**: ~30-40% of routine queries auto-resolved; ~60-70% routed to humans
- **Risk**: Users feel the AI doesn't do much; value proposition weakens

### Option B: High Recall (High Automation, Risky)

- Auto-respond when either confidence > 70%
- Route only ambiguous items
- **Result**: ~70-80% auto-resolved; some wrong answers sent
- **Risk**: Hallucination damages trust; one viral incident kills the product

### Option C: Human-in-the-Loop with Confidence Badges (Balanced) — **REQUIRED**

- Every AI-generated response carries a confidence badge: "I'm X% confident this answer is correct"
- For confidence > 90%: auto-send with badge
- For confidence 60-90%: route to backup for review and approval before sending
- For confidence < 60%: route to backup with a suggested response for the backup to edit and send
- All responses are logged regardless of path

**Option C is the only design consistent with the brief's stated constraint. Without human-in-the-loop, the product cannot satisfy "accurate responses always" while also delivering automation value.**

---

## Confidence Badge Specification

### Badge Levels

| Confidence Range | Badge Text            | Behavior                                                           |
| ---------------- | --------------------- | ------------------------------------------------------------------ |
| > 95%            | "High confidence"     | Auto-send with badge; log to audit trail                           |
| 80-95%           | "Moderate confidence" | Auto-send with explicit badge; backup can override                 |
| 60-80%           | "Low confidence"      | Route to backup; backup reviews and approves or edits before send  |
| < 60%            | "Uncertain"           | Route to backup with suggested response; backup composes and sends |

### Badge Display

- In WhatsApp: appended as a footer note — "[Auto-generated; 92% confidence. Reply STOP to speak with a human]"
- In email: added as an X-AI-Confidence header + visible footer
- The badge MUST NOT be editable by the AI or configurable by the user — it is a fixed governance control

---

## Escalation Paths

### Routine Query (high confidence RAG + high confidence classifier)

1. AI generates response from RAG retrieval
2. Confidence badge attached
3. Auto-sent to contact
4. Logged to audit trail with full retrieval citations
5. Backup sees summary in daily digest (informational only)

### Semi-Routine Query (medium confidence)

1. AI generates response
2. Route to account owner via structured escalation email with AI draft included
3. Account owner receives: contact message + AI-generated response + confidence badge + RAG citations
4. Account owner replies to the email to approve, edit, or rewrite — the reply is sent to the client
5. If no reply within SLA window (default: 4 hours), auto-escalate to backup contact via email

### Complex Query (low confidence or no RAG match)

1. AI generates escalation summary
2. Route to account owner via structured email with: contact message + RAG citations (even if empty) + classification reasoning + suggested routing
3. Account owner composes reply and responds via email
4. If no reply within SLA, auto-escalate to backup contact
5. Human answer is captured and added to the knowledge base for future learning

### High-Stakes Query (medical, legal, financial keywords detected)

1. Never auto-respond — route directly to account owner and backup via email immediately
2. Recipients receive: contact message + classification (HIGH_STAKES) + urgency flag
3. The product MUST NOT attempt RAG resolution for queries flagged as high-stakes

---

## D/T/R Accountability (PACT Governance)

Every message and action in the system is accountable under D/T/R:

- **D (Doer)**: The AI agent that classified, retrieved, or generated the response
- **T (Type)**: The action taken — message_classified, rag_retrieved, response_auto_sent, escalation_routed, backup_notified
- **R (Recipient)**: The contact who received the message or the backup who received the escalation

Audit rows are written for every state transition:

- Message received
- Message classified
- RAG retrieved (or RAG returned empty)
- Response generated
- Response sent (auto or manual)
- Escalation created
- Escalation acknowledged by backup
- Escalation resolved

---

## Hallucination Controls

### RAG Retrieval Hallucination

- Retrieval confidence score MUST be computed and included in response confidence
- If the retriever fetches a document passage that matches the query vector but does not actually answer the question (detected via cross-check prompt), the retrieval confidence is reduced
- Cross-check prompt: "Does this passage answer the user's question? Answer yes/no." If no, do not use passage even if vector similarity is high

### Synthesis Hallucination

- LLM synthesis prompt MUST include: "Do not add information not present in the retrieved documents. If you are uncertain, say so."
- The AI MUST cite specific document sources for each factual claim in the response
- Responses with fabrication (no cited source) are flagged and confidence reduced

### Staleness Detection

- Each document has a `last_indexed_at` timestamp
- If a document's index age exceeds the configured **per-document-type** staleness threshold (7 days for rosters/price lists, 30 days for policies — the canonical rule in `rag-pipeline.md`; resolved 2026-07-05 per `DEVIATIONS.md` CS-3), RAG retrieval from that document is flagged as potentially stale
- The response confidence badge MUST include a staleness warning when any retrieved document is past its type's staleness threshold: "[Sources may be outdated — last updated X days ago]"

---

## Error States and Fallbacks

| Error State                    | Fallback Behavior                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------------- |
| RAG returns empty              | Route to backup with "no matching information" summary                             |
| Classifier confidence < 20%    | Route to backup immediately; do not generate response                              |
| Backup is also OOO             | Route to second-tier backup; if none, log as pending and alert primary on return   |
| WhatsApp session window closed | Send pre-approved template message; log as "template re-engagement"                |
| Email deliverability failure   | Retry up to 3 times over 1 hour; if all fail, alert backup via alternative channel |

---

## Confidence Threshold Configuration

The 90%/60% thresholds are defaults. The user may adjust them at configuration time, with one constraint:

- Thresholds below 70% for auto-send require explicit user acknowledgement: "You are setting auto-send confidence to X%. This means the AI will send responses it is less certain about. Wrong responses may be sent to your contacts."
- High-stakes categories (medical, legal, financial) ALWAYS route to backup regardless of confidence threshold

---

## Audit Trail

Every message, classification, retrieval, response, and escalation is logged. The audit trail is:

- Tenant-isolated (no tenant can see another tenant's logs)
- Immutable (append-only; no deletion)
- Exportable (user can download their audit log as CSV)
- Retained per plan tier — 90 days (Starter), 12 months (Professional), 24 months (Enterprise) — the canonical schedule in `data-model.md`. (PDPA governs retention _limitation_ and protection, not a fixed minimum; the earlier "24 months minimum (PDPA requirement)" was a mis-statement — 24 months is the Enterprise-tier maximum, not a floor. Resolved 2026-07-05 per `DEVIATIONS.md` CS-4.)

The primary user sees on return: a summary email of all messages received during OOO, what was auto-resolved (and the confidence of each), what was escalated, and what is still pending. No dashboard login required — everything is in the inbox.
