# Sequor — AI Communication Coverage Platform

**Repository:** https://github.com/aliciapls/Sequor

---

## 1. Executive Summary

Sequor is an AI-powered communication coverage platform for small businesses. When the owner is unavailable, Sequor handles incoming email and WhatsApp messages — classifying them, generating auto-replies from uploaded documents, and escalating only what genuinely needs human attention.

**How it works in brief:**

1. Customer sends an email or WhatsApp message.
2. Sequor classifies it — routine, semi-routine, complex, or high-stakes.
3. High-confidence routine queries receive an immediate AI auto-reply drawn from the business's uploaded documents.
4. Low-confidence or complex queries escalate to a backup contact with an AI-prepared draft ready for review.
5. Every human resolution improves future auto-replies through the learning loop.

**Channels:** Email (SendGrid) and WhatsApp Business API (Meta Cloud API). Same-contact, same-topic messages across channels are recognized as one conversation.

**Pricing:** Free (50 messages/month, 1 operator, 3 documents) → Starter → Professional → Enterprise. Paid plans processed via Stripe.

**Compliance:** PDPA (Singapore) — consent tracking, right to erasure, HUMAN override, PII encrypted at rest.

**Deployment:** Vercel serverless functions (FastAPI + PostgreSQL + pgvector).

---

## 2. User Guide

### Signing Up

1. Go to the portal → **Sign Up**. Enter org name, your email, and password.
2. Create your first **Account** (your business) with a name and ownership type.
3. Add a **Backup Contact** — the human who receives escalations. They verify their email address.
4. Set your **Escalation SLA** — hours before an unresolved query escalates.
5. Complete DNS verification (Sequor generates the records to add).
6. Connect your first channel (email or WhatsApp).

### Uploading Documents

Sequor uses your own documents (PDF, DOCX, TXT — max 25MB) as the knowledge base for auto-replies.

1. Go to **Documents** → **Upload**.
2. Select your file. Assign a **Document Type**: FAQ, Price List, Policy, Roster, or Other.
3. Sequor parses, chunks, and indexes the document automatically.
4. When status shows **Ready**, the document is live.

**Document statuses:** Pending (upload received) → Indexing (being processed) → Ready (live) → Stale (needs re-indexing).

On startup, any document stuck at Indexing is automatically promoted to Ready.

### Key Phrases

Key Phrases are keywords that link a query directly to a document. "Return policy" → your policy document. "Pricing" → your price list.

1. Go to **Key Phrases**.
2. Add phrases manually or click **Suggest** to have AI propose phrases from your documents.
3. Assign each phrase to a document and set a **confidence boost**.

### Contacts

**Contacts** shows every customer who has messaged you — name, email, phone, channel preference, and a **Human Override** flag if they typed "HUMAN" to force manual handling.

### Escalations

Go to **Escalations** to see all queries routed to a human. Each shows: original message, AI classification and confidence, linked documents, status (Pending / Acknowledged / Resolved), and resolution summary.

To resolve: open the escalation, review or edit the AI draft, and click **Resolve**. Your answer is captured to improve future auto-replies.

### Glossary of Terms

| Term               | Meaning                                        |
| ------------------ | ---------------------------------------------- |
| Pending            | Upload received, processing not yet started    |
| Indexing           | Being parsed, chunked, and embedded            |
| Ready              | Fully indexed and active                       |
| Key Phrase         | Keyword linking a query to a specific document |
| Key Phrase Mapping | Link between a phrase and a document           |
| Auto-reply         | AI-generated response sent automatically       |
| Escalate           | Route to human backup contact                  |
| Include in Context | Documents used to generate the AI reply        |
| PDPA               | Singapore Personal Data Protection Act         |

---

## 3. Technical Overview

### Architecture

```
Email/WhatsApp → SendGrid/Meta Webhooks → FastAPI (Vercel)
  |-- InboundProcessor (email + WhatsApp)
  |-- AutoReplyService
  |     |-- MessageClassifier (LLM)
  |     |-- RAGPipeline (vector + BM25 hybrid)
  |     |-- ResponseGenerator
  |     |-- LearningLoop
  |-- EscalationService
  |-- BillingService (Stripe)
         |-- PostgreSQL + pgvector
```

**AI:** Ollama (`llama3.1`) for LLM; `nomic-embed-text` for embeddings. OpenAI `text-embedding-3-small` available as fallback. BM25 keyword search used when embeddings unavailable.

**Note:** Ollama cannot run on Vercel serverless. Without an OpenAI key, documents use BM25-only search.

### Environment Variables

| Variable                       | Required     | Description                                  |
| ------------------------------ | ------------ | -------------------------------------------- |
| `DATABASE_URL`                 | Yes          | PostgreSQL connection string                 |
| `JWT_SECRET`                   | Yes          | JWT signing secret (min 32 chars)            |
| `ENCRYPTION_MASTER_KEY`        | Yes          | Base64 32-byte key for PII encryption        |
| `APP_ENV`                      | Yes          | `production` on Vercel                       |
| `OPENAI_API_KEY`               | No           | Embedding fallback (enables semantic search) |
| `OLLAMA_BASE_URL`              | No           | Default: http://localhost:11434              |
| `SENDGRID_API_KEY`             | For email    | SendGrid API key                             |
| `STRIPE_API_KEY`               | For billing  | Stripe API key                               |
| `WHATSAPP_ACCESS_TOKEN`        | For WhatsApp | Meta API token                               |
| `WHATSAPP_PHONE_NUMBER_ID`     | For WhatsApp | WhatsApp phone number ID                     |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | For WhatsApp | Meta business account ID                     |

### Database Models

Core entities: `Tenant`, `Account`, `BackupContact`, `Contact`, `ChannelConsent`, `Message`, `Classification`, `Response`, `RAGRetrieval`, `Escalation`, `Document`, `DocumentChunk`, `LearnedAnswer`, `AuditEntry`, `RoutingOutcome`, `KeyPhraseMapping`.

**Multi-tenancy:** Every record keyed by `tenant_id`. Optional separate PostgreSQL schemas per tenant.

**PII encryption:** Email and phone fields encrypted at rest using `EncryptedString` with tenant-specific keys. Blind index on `BackupContact.email` enables login lookups without decrypting.

### AI Pipeline

**Classification:** LLM classifies each message into category (routine / semi_routine / complex / high_stakes) and urgency (low / medium / high / critical), with confidence score.

**RAG retrieval:** Hybrid search — 70% cosine similarity on pgvector embeddings + 30% BM25 keyword score. Synthesized answers cross-checked against source passages for hallucination detection.

**Response routing:**

| Confidence | Category                | Action                            |
| ---------- | ----------------------- | --------------------------------- |
| >= 90%     | routine/semi_routine    | Auto-reply sent                   |
| 60–90%     | routine/semi_routine    | Escalate with AI draft for review |
| < 60%      | any                     | Escalate without draft            |
| any        | high_stakes or critical | Immediate escalation              |

**Learning loop:** Human escalation resolutions captured as Q&A pairs, embedded, and stored. Future queries search this learned set with 0.5 cosine similarity threshold.

### WhatsApp-Specific

Meta's 24-hour session window: free-form replies only within 24 hours of a customer message. Outside the window, pre-approved template messages are sent instead.

Messages exactly "HUMAN" or starting with "HUMAN" trigger immediate forced escalation.

Rate limits: 250 messages/min globally; 1 per 6 seconds per user.

### Authentication

JWT (HS256, 24-hour expiry) stored in `HttpOnly` cookie. Roles: `admin` (primary backup contact) or `operator`. Tenant isolation enforced at query level via `tenant_id` from JWT.

### Key API Endpoints

| Endpoint                                  | Method          | Auth | Description                            |
| ----------------------------------------- | --------------- | ---- | -------------------------------------- |
| `/api/v1/onboarding`                      | POST            | No   | Create tenant, account, backup contact |
| `/api/v1/auth/login`                      | POST            | No   | Login → JWT cookie                     |
| `/api/v1/auth/me`                         | GET             | Yes  | Current operator                       |
| `/api/v1/portal/documents/upload`         | POST            | Yes  | Upload document                        |
| `/api/v1/portal/documents/{id}`           | DELETE          | Yes  | Delete document                        |
| `/api/v1/portal/escalations`              | GET             | Yes  | List escalations                       |
| `/api/v1/portal/escalations/{id}/resolve` | POST            | Yes  | Resolve escalation                     |
| `/api/v1/portal/keyphrase/mappings`       | GET/POST/DELETE | Yes  | Key phrase mappings                    |
| `/api/v1/email/inbound`                   | POST            | No   | SendGrid webhook                       |
| `/api/v1/whatsapp/inbound`                | POST            | No   | Meta webhook                           |
| `/api/v1/billing/webhook`                 | POST            | No   | Stripe webhook                         |
| `/api/v1/portal/upgrade`                  | POST            | Yes  | Stripe checkout                        |

### Deployment

- **Platform:** Vercel (serverless Python, `@vercel/python` runtime)
- **Entry:** `api/index.py` — exports `application = app` (FastAPI ASGI app)
- **Build:** `pip install -e .` via `vercel.json` `installCommand`
- **All traffic** routes to `api/index.py`

### Project Structure

```
src/sequor/
  ai/          -- LLM client, classifier, RAG, vector store, learning loop
  auth.py      -- JWT auth, bcrypt password hashing
  billing/     -- Stripe integration
  compliance.py -- PDPA consent, HUMAN override, erasure
  config.py    -- pydantic-settings from .env
  db/          -- SQLAlchemy models, encrypted columns, schema manager
  email/       -- Inbound processing, auto-reply, SendGrid sender
  escalation/  -- Escalation service, SLA scheduler
  onboarding/  -- FastAPI app, all routes, Jinja2 templates
  protocols.py -- EmailSender/WhatsAppSender interfaces
  schemas.py   -- Pydantic validation models
  whatsapp/    -- Inbound processing, auto-reply, Meta sender
api/
  index.py     -- Vercel ASGI entry point
vercel.json    -- Vercel build + route config
```

### Known Limitations

1. **No semantic embeddings on Vercel without OpenAI key.** Ollama cannot run serverless. BM25 keyword search used as fallback.
2. **WhatsApp 24-hour session window.** Free-form replies restricted to 24 hours; template messages required outside the window.
3. **No real-time portal updates.** Server-rendered HTML; users refresh to see new escalations.
4. **Rate limits.** Email: 60/min. WhatsApp: 250/min global, 1/6s per user.

### Taking Over This Project

**First-read files:**

- `src/sequor/onboarding/app.py` — All routes
- `src/sequor/ai/rag_pipeline.py` — Core AI logic
- `src/sequor/escalation/service.py` — Escalation workflow
- `src/sequor/db/models.py` — All entities
- `src/sequor/config.py` — All configuration

**Run locally:**

```bash
uv venv && uv sync
cp .env.example .env  # fill in values
uv run uvicorn sequon.onboarding.app:app --reload
```

Requires a real PostgreSQL database with pgvector extension. SQLite will not work.
