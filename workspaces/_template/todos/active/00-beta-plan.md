# Lean Paid Beta — Implementation Plan

**Scope:** Minimum viable product for 3-5 paid beta organizations
**Channel:** Email only (WhatsApp deferred to post-beta)
**Interface:** Email-first (no app) + minimal web onboarding form
**Validation goal:** 3-5 organizations paying real money within 8 weeks of beta launch

**Architecture:**

- Backend: Python with Kailash SDK (Core + DataFlow + Kaizen)
- Database: PostgreSQL with pgvector for embeddings
- Email inbound: SendGrid Inbound Parse or Postmark inbound webhook
- Email outbound: SendGrid or Postmark
- AI: LLM via .env (classification, RAG synthesis, learning loop)
- Frontend: Minimal web onboarding only (Next.js or simple form)
- Billing: Stripe Checkout for subscription management

---

## Milestone 1: Project Setup & Data Layer

### TODO-01: Initialize project structure and dependencies

Set up Python project with pyproject.toml, directory structure, .env loading, and dev dependencies.

```
src/
  sequor/
    __init__.py
    config.py          # Settings from .env
    db/                # DataFlow models and migrations
    email/             # Email ingestion and sending
    ai/                # Classification, RAG, learning loop
    escalation/        # Escalation engine, auto-escalation
    digest/            # Daily digest generation
    onboarding/        # Account setup logic
    billing/           # Stripe integration
tests/
  unit/
  integration/
```

**Implements:** Project foundation
**Dependencies:** None
**Acceptance:** `pip install -e .` succeeds; `.env` loads; basic config accessible

### TODO-02: Database schema and DataFlow models

Create PostgreSQL schema with pgvector extension and DataFlow models for all beta entities:

- Tenant (with PDPA consent tracking)
- Account (email channel only for beta)
- BackupContact
- Contact (external)
- ChannelConsent
- Message (email only)
- Classification
- RAGRetrieval
- Response
- Escalation
- AuditEntry (D/T/R accountability)
- Document (for uploaded docs)
- LearnedAnswer (new entity for learning loop)
- RoutingOutcome

Implement per-tenant schema isolation as specified in data-model.md.

**Implements:** specs/data-model.md (all entities)
**Dependencies:** TODO-01
**Acceptance:** All models create/drop cleanly; pgvector extension available; tenant isolation verified with test query

### TODO-03: Database migrations setup

Set up Alembic (or DataFlow migrations) for versioned schema changes. Create initial migration from TODO-02.

**Implements:** specs/data-model.md (schema lifecycle)
**Dependencies:** TODO-02
**Acceptance:** `alembic upgrade head` creates all tables; `alembic downgrade base` drops cleanly

---

## Milestone 2: Email Infrastructure

### TODO-04: Inbound email processing — receive and parse

Implement email ingestion pipeline:

- Webhook endpoint to receive inbound emails from SendGrid/Postmark
- Parse email headers (From, To, Subject, Message-ID, In-Reply-To, References)
- Extract plain text body (strip HTML, handle multipart)
- Extract attachments (filename, MIME type)
- Create Message record in database
- Link to existing thread via In-Reply-To / References headers

**Implements:** specs/message-routing.md § Email — Async Channel, specs/channel-coordination.md § Email-First Escalation Interface
**Dependencies:** TODO-02
**Acceptance:** Sending a test email to the webhook creates a Message record with correct headers, body, and thread linkage

### TODO-05: Outbound email sending — infrastructure

Implement email sending via SendGrid/Postmark:

- Send structured emails (HTML + plain text multipart)
- Custom From address per account (coverage@account.company.com)
- Reply-To header set to a unique address per escalation (for reply-to-resolve)
- Message-ID tracking for threading
- Rate limiting (60 emails/minute/domain as per specs)

**Implements:** specs/message-routing.md § Email Deliverability
**Dependencies:** TODO-01
**Acceptance:** Sending a test email delivers successfully; email threads correctly in Gmail/Outlook; rate limiter prevents burst

### TODO-06: Wire email pipeline end-to-end

Connect inbound processing (TODO-04) to outbound sending (TODO-05) with the full message lifecycle:

- Inbound email → Message record → classify (placeholder for now) → respond or escalate (placeholder for now)
- This is the skeleton that TODO-07 through TODO-12 will fill in

**Implements:** specs/message-routing.md § Configuration Contract
**Dependencies:** TODO-04, TODO-05
**Acceptance:** Email in → processing log → placeholder response out; full pipeline runs without errors

---

## Milestone 3: Core AI Pipeline

### TODO-07: Message classification engine

Implement LLM-based message classification:

- Classify incoming message by category (routine, semi_routine, complex, high_stakes)
- Classify urgency (low, medium, high, critical)
- Compute confidence score (0.0–1.0)
- Store reasoning text for audit trail
- Create Classification record in database

Use Kaizen agent for classification. Prompt reads the message and returns structured classification output.

**Implements:** specs/response-accuracy.md § Response Options, specs/data-model.md § Classification entity
**Dependencies:** TODO-02, TODO-06
**Acceptance:** Test messages classified correctly across all 4 categories; confidence scores reasonable; Classification records persisted

### TODO-08: Document ingestion pipeline

Implement document upload and processing:

- Accept uploads via onboarding API (PDF, DOCX, XLSX, CSV, TXT)
- Parse documents using appropriate parser per type
- Chunk documents (line-item for FAQs/price lists, section-based for policies, sentence-overlap for informal)
- Generate embeddings via configured embedding model (from .env)
- Store chunks and embeddings in PostgreSQL with pgvector
- Track document status (pending → indexing → ready)
- Track staleness (last_indexed_at)

**Implements:** specs/rag-pipeline.md § Document Ingestion Flow, § Chunking, § Embedding Generation
**Dependencies:** TODO-02
**Acceptance:** Upload a test PDF and XLSX; chunks created and embedded; vector similarity search returns relevant chunks for a test query

### TODO-09: RAG retrieval and synthesis

Implement the RAG query pipeline:

- Embed incoming query using same model as documents
- Hybrid search: vector similarity (pgvector) + BM25 keyword match
- Score passages by relevance × answerability (cross-check prompt)
- Synthesize response using LLM with retrieved passages
- Include citations in response (source document + chunk reference)
- Compute synthesis confidence score
- Create RAGRetrieval record in database

**Implements:** specs/rag-pipeline.md § Retrieval Flow, § Retrieval Confidence Scoring, § Synthesis
**Dependencies:** TODO-08
**Acceptance:** Query against test documents returns relevant passages; synthesis stays within retrieved content; hallucination detection flags un-cited claims

### TODO-10: Response generation with confidence scoring

Implement the response decision engine:

- Combine classification confidence + RAG synthesis confidence into overall confidence
- Route based on confidence thresholds:
  - > 90%: auto-reply to contact
  - 60-90%: generate escalation email with AI draft
  - < 60%: generate escalation email without AI draft
  - High-stakes: always escalate regardless of confidence
- Create Response record in database
- Write AuditEntry for every state transition

**Implements:** specs/response-accuracy.md § Response Options, § Confidence Badge Specification
**Dependencies:** TODO-07, TODO-09
**Acceptance:** Test messages at different confidence levels route correctly; high-stakes keywords always escalate; audit trail complete

---

## Milestone 4: Escalation & Learning Loop

### TODO-11: Structured escalation email generation

Implement the escalation email builder:

- Generate structured email as specified in specs (Subject, client info, confidence, original message, AI draft, escalation deadline)
- Set Reply-To to unique address per escalation (for reply-to-resolve)
- Send to account owner email
- Create Escalation record in database
- Write AuditEntry for escalation_created

**Implements:** specs/channel-coordination.md § Email-First Escalation Interface, § Unresolved Item Email Format
**Dependencies:** TODO-05, TODO-10
**Acceptance:** Low-confidence message triggers structured escalation email to account owner; email format matches spec; Escalation record created

### TODO-12: Reply-to-resolve handler

Implement email reply parsing and resolution:

- Parse inbound reply to escalation email (match via In-Reply-To header or unique reply address)
- Extract human response from reply body (strip quoted text, signatures)
- Send human response to original contact on the original channel
- Mark escalation as resolved
- Write AuditEntry for escalation_resolved
- Trigger learning loop (TODO-13)

**Implements:** specs/channel-coordination.md § Reply-to-Resolve Mechanism
**Dependencies:** TODO-04, TODO-05, TODO-11
**Acceptance:** Replying to escalation email sends response to original sender; escalation marked resolved; audit trail updated

### TODO-13: Learning loop — capture human answers

Implement the knowledge capture from human responses:

- When escalation is resolved (TODO-12), extract the question-answer pair
- Create LearnedAnswer record (original query + human response + source attribution)
- Embed the learned answer using same embedding model
- Add to the vector store alongside document chunks
- Flag learned answers with source_type = "human_answer"
- Include in daily digest: count of new learned answers

**Implements:** specs/rag-pipeline.md § Learning from Human Answers
**Dependencies:** TODO-09, TODO-12
**Acceptance:** Resolving an escalation adds a LearnedAnswer; future similar queries retrieve the learned answer; source attribution shows "human_answer"

### TODO-14: Auto-escalation timer

Implement SLA-based auto-escalation:

- When escalation is created, schedule a check at SLA deadline (default: 4 hours)
- If escalation is not resolved by deadline:
  1. Send same structured email to backup contact
  2. Update escalation record tier
  3. If backup also doesn't respond within SLA, notify second-tier
  4. If no one responds, flag as "breached"
- Use a background task scheduler (APScheduler or similar)

**Implements:** specs/channel-coordination.md § Auto-Escalation
**Dependencies:** TODO-11
**Acceptance:** Unresolved escalation auto-escalates to backup after 4 hours; second-tier notified after 8 hours; breached flag set if no one responds

---

## Milestone 5: Daily Digest & Operations

### TODO-15: Daily digest email generation

Implement daily digest:

- Scheduled job (every morning at 8:00 AM local time)
- Query all messages, escalations, and resolutions for the past 24 hours
- Generate digest email with counts: auto-resolved, pending, escalated, breached, new learned answers
- Send to account owner email

**Implements:** specs/channel-coordination.md § Daily Digest Email
**Dependencies:** TODO-10, TODO-11, TODO-13
**Acceptance:** Digest email sent at scheduled time; counts match database state; format matches spec

### TODO-16: Auto-reply email generation

Implement the auto-reply email for high-confidence responses:

- Generate reply email with confidence badge footer
- Include citation footer: "[Auto-generated; X% confidence. Sources: Doc1, Doc2]"
- Send to original contact
- Write AuditEntry for response_auto_sent
- Thread correctly (In-Reply-To original message)

**Implements:** specs/response-accuracy.md § Confidence Badge Specification, § Routine Query flow
**Dependencies:** TODO-05, TODO-10
**Acceptance:** High-confidence query gets auto-replied with confidence badge; email threads correctly; audit entry written

---

## Milestone 6: Onboarding

### TODO-17: Minimal web onboarding — account setup

Build a minimal web form (single page, React/Next.js or simple HTML form) for:

1. Organization name + email + password (sign up)
2. Account name + ownership type (individual/department)
3. Owner email (receives escalations)
4. Email channel setup (enter inbox to monitor — e.g., hello@company.com)
5. Routing rule template selection (All to backup / FAQ-only / Full AI)
6. Backup contact (name + email)
7. Escalation SLA timing (default 4 hours)

On submit: create Tenant, Account, and BackupContact records; send verification email to owner.

**Implements:** specs/onboarding.md § Onboarding Flow Steps 1-5
**Dependencies:** TODO-02
**Acceptance:** User can complete setup in under 10 minutes; all records created correctly; verification email sent

### TODO-18: Minimal web onboarding — document upload

Add document upload to onboarding form:

- File upload widget (PDF, DOCX, XLSX, CSV, TXT)
- Show "No documents? No problem — the AI learns from your answers over time." message
- Upload triggers document ingestion pipeline (TODO-08)
- Show indexing progress

**Implements:** specs/onboarding.md § Step 3: Upload Documents (Optional)
**Dependencies:** TODO-08, TODO-17
**Acceptance:** User can upload a document during onboarding; document is indexed and ready for queries

### TODO-19: Email channel connection — DNS setup instructions

Generate DNS instructions for the user:

- Display DKIM/SPF records needed for the user's domain
- Copy-to-clipboard for each record
- Verification check (poll DNS until verified)
- If user can't set DNS: offer SMTP relay as fallback

**Implements:** specs/onboarding.md § Step 2: Create Account — Email channel setup
**Dependencies:** TODO-05
**Acceptance:** DNS instructions display correctly; verification detects when records are added; fallback to SMTP relay works

---

## Milestone 7: Billing & Compliance

### TODO-20: Stripe billing integration

Implement subscription management:

- Stripe Checkout for sign-up (Starter tier: S$20/month)
- Webhook handler for subscription events (active, past_due, canceled)
- Update Tenant.plan based on Stripe subscription status
- Grace period handling (7 days past due before degrading service)
- No separate billing page — Stripe manages the payment flow

**Implements:** specs/business-model.md § Pricing Model
**Dependencies:** TODO-17
**Acceptance:** User can sign up and pay via Stripe; subscription status reflected in database; service degrades gracefully on non-payment

### TODO-21: PDPA consent handling

Implement basic PDPA compliance for beta:

- Collection notice included in first auto-reply email: "This inbox is managed by [Company]'s AI assistant. Your message is processed to route it correctly. Reply HUMAN to speak with a person."
- HUMAN override detection (exact match or starts-with "HUMAN ")
- ChannelConsent record created on first contact
- Contact right to erasure: API endpoint to delete all PII for a contact
- No PII in AuditEntry (UUID references only)

**Implements:** specs/data-model.md § PDPA-Specific Requirements, specs/message-routing.md § HUMAN rejection path
**Dependencies:** TODO-02, TODO-16
**Acceptance:** Auto-reply includes consent notice; HUMAN override works; erasure endpoint deletes all PII; AuditEntry contains no PII

---

## Milestone 8: Integration Testing & Launch Readiness

### TODO-22: End-to-end integration test — happy path

Test the complete flow:

1. Organization signs up via onboarding (TODO-17)
2. Uploads a test document (TODO-18)
3. Sends a test email to the monitored inbox (TODO-04)
4. AI classifies and retrieves from document (TODO-07, TODO-09)
5. High-confidence query: auto-reply sent (TODO-16)
6. Low-confidence query: escalation email sent (TODO-11)
7. Human replies to escalation: response sent to contact (TODO-12)
8. Learned answer available for future queries (TODO-13)
9. Daily digest sent next morning (TODO-15)

**Implements:** Full pipeline validation
**Dependencies:** TODO-04 through TODO-16
**Acceptance:** All 9 steps complete without errors; audit trail has entries for every state transition; no mock data in the pipeline

### TODO-23: End-to-end integration test — escalation chain

Test escalation timing and multi-tier routing:

1. Send a low-confidence query
2. Verify escalation email sent to account owner
3. Wait for SLA to expire (configurable short timeout for testing)
4. Verify auto-escalation to backup contact
5. Verify second-tier escalation if backup doesn't respond
6. Verify "breached" flag if no one responds
7. Verify breached items appear in daily digest

**Implements:** specs/channel-coordination.md § Auto-Escalation, § SLA Tracking
**Dependencies:** TODO-14, TODO-15
**Acceptance:** Full escalation chain works; timing matches configured SLA; breached items flagged correctly

### TODO-24: Error handling and resilience

Implement error handling for production edge cases:

- Email delivery failure: retry 3 times over 1 hour, then alert
- LLM API failure: route everything to escalation (fail-safe)
- Database connection loss: graceful degradation
- Malformed inbound email: log and skip, don't crash
- Duplicate email delivery: idempotency via external_message_id
- Rate limiting on outbound email

**Implements:** specs/response-accuracy.md § Error States and Fallbacks
**Dependencies:** TODO-06
**Acceptance:** Each error case handled gracefully; no crashes; audit trail maintained; fail-safe always routes to escalation

---

## Post-Beta (NOT in this build cycle)

The following are explicitly deferred to post-beta, to be prioritized based on beta feedback:

- WhatsApp channel integration (full WhatsApp Business API)
- Multi-account support per organization
- Weekly recap email
- Document staleness detection and re-indexing
- Multi-channel deduplication
- Contradictory response prevention
- Channel partner infrastructure
- Full PDPA compliance suite (data portability, breach notification workflow)
- SOC 2 / ISO 27001 certification groundwork
- Mobile app or dashboard (only if beta feedback demands it)
- Routing intelligence flywheel (cross-tenant learning)
