# Sequor — AI Communication Coverage Platform

**Repository:** https://github.com/aliciapls/Sequor

---

## 1. Executive Summary

Sequor is an AI-powered communication coverage platform for small businesses. When the owner is unavailable, Sequor handles incoming email and WhatsApp messages — classifying them, generating auto-replies from uploaded documents, and escalating only what genuinely needs human attention.

**How it works:**

1. Customer sends an email or WhatsApp message.
2. Sequor classifies it — routine, semi-routine, complex, or high-stakes.
3. High-confidence routine queries receive an immediate AI auto-reply drawn from the business's uploaded documents.
4. Low-confidence or complex queries escalate to a backup contact with an AI-prepared draft ready for review.
5. Every human resolution improves future auto-replies through the learning loop.

**Channels:** Email (SendGrid) and WhatsApp Business API (Meta Cloud API). Same-contact, same-topic messages across channels are recognized as one conversation.

**Pricing:** Free (50 messages/month) → Starter SGD 20/month (200 messages) → Professional → Enterprise. Paid plans via Stripe.

**Compliance:** PDPA (Singapore) — consent tracking, right to erasure, HUMAN override, PII encrypted at rest.

**Deployment:** Vercel serverless (FastAPI + PostgreSQL + pgvector).

---

## 2. Why Sequor — Business Case

### The Problem

Small businesses lose customers when they cannot respond quickly. A 5-hour delay in replying to a price inquiry often means the prospect moves on.

| Option            | Monthly Cost         | Setup Time    | Handles Documents    | Escalation with Draft |
| ----------------- | -------------------- | ------------- | -------------------- | --------------------- |
| **Sequor**        | From free            | Hours         | Yes                  | Yes                   |
| Virtual Assistant | $1,500–3,000         | Days to weeks | Only if trained      | N/A                   |
| Intercom AI       | $80–500+             | Days          | Yes                  | Partial               |
| DIY GPT API       | $50–500+ (API costs) | Days          | Requires engineering | No                    |
| No coverage       | $0                   | N/A           | N/A                  | N/A                   |

### Return on Investment

**Scenario: A Singapore SME with 2 staff, 300 inbound messages/month**

| Cost Element                             | Without Sequor                         | With Sequor Starter (SGD 20/mo)    |
| ---------------------------------------- | -------------------------------------- | ---------------------------------- |
| Staff time responding to routine queries | 10 hrs/month × SGD 25/hr = SGD 250     | 1 hr/month × SGD 25/hr = SGD 25    |
| Missed leads (5% lost to slow response)  | 15 lost × avg SGD 500 deal = SGD 7,500 | SGD 0                              |
| Auto-reply AI cost                       | SGD 0                                  | SGD 0 (within 200 msg limit)       |
| **Total monthly cost**                   | **SGD 7,750**                          | **SGD 25 + SGD 25 staff = SGD 50** |
| **Annual cost**                          | **SGD 93,000**                         | **SGD 600**                        |

**Payback period on first month of use: SGD 92,400 saved.**

For businesses receiving fewer than 50 messages/month, the free tier covers everything at zero cost.

### What Is Needed to Go Live

1. **DNS verification** — Add MX and TXT records for your email domain. Sequor generates the exact records to add. Takes 5–30 minutes.
2. **WhatsApp Business Account** (if using WhatsApp) — Create a Meta Business Account, verify your phone number, approve the WhatsApp Cloud API app. Takes 1–2 hours for Meta review.
3. **SendGrid account** (if using email) — Create account, verify a sender identity, add webhook URL. Free tier sufficient for most.
4. **Upload initial documents** — FAQ and policy documents minimum.
5. **Set escalation contacts** — At least one human backup contact.
6. **Configure SLA** — Hours before unresolved queries escalate.

**Total setup time for a non-technical owner: 2–4 hours.**

### Data Continuity and Exit

If Sequor ceases operation:

- All data is exported in standard formats (CSV, JSON) on request.
- Database can be self-hosted using the Docker image and database schema.
- No proprietary lock-in — Sequor is a standard FastAPI application backed by PostgreSQL.

---

## 3. User Guide — Day-to-Day Operations

### What You Will Receive as a Backup Contact

When an escalation is created, you receive an email with this exact structure:

```
Subject: [UNRESOLVED] Question about pricing for bulk orders (Ref: a1b2c3d4)

Client: Sarah Tan (WhatsApp)
Received: 14 May 2026, 9:42 AM
AI attempted: Yes — Auto-reply
Confidence: Moderate (67%) — semi_routine
Requested via: WhatsApp

---
Hi, do you offer discounts for bulk orders of 500+ units?

---

→ Reply to this email to send your response to the client.
→ If unresolved by 14 May 2026, 2:00 PM, this will escalate to John Lim.

AI suggested response:
Yes, we do offer bulk discounts. Orders of 500+ units qualify for our
wholesale rate, which is 15% below our standard pricing. I can send
you the full wholesale catalogue if you'd like.
```

**Your options:**

- **Reply directly to the email** — your reply goes to the customer immediately.
- **Edit the AI suggested response** and send.
- **Compose your own** — the AI draft is a starting point, not a constraint.

### Customer Experience — First Contact

When a new customer sends their first message:

1. Sequor receives the message via SendGrid or Meta webhook.
2. If the contact is new, their consent is recorded (WhatsApp only in current build).
3. The AI classifies and either sends an auto-reply or creates an escalation.
4. The customer receives the auto-reply OR the escalation email is sent to the backup contact.
5. If escalated, the customer receives the backup's reply when they respond.

### How to Know If Auto-Replies Are Working

Check the **Dashboard** in the portal. It shows:

- Messages received this week
- Auto-replies sent
- Open escalations

**Rule of thumb:** If auto-replies sent ÷ messages received is above 70%, the AI is handling the majority of volume. If escalations are rising week-over-week, add more documents or key phrases.

### The HUMAN Override Feature

Customers type **"HUMAN"** (or "HUMAN help") in any message to force immediate escalation. Their contact record is flagged with a **Human Override** badge so your team handles them manually going forward.

### Common Operator Tasks

**Add a new document:**
Documents → Upload → select PDF, DOCX, or TXT → assign a type (FAQ, Price List, Policy, Roster, Other) → wait for status to show Ready (usually 30–60 seconds for small files).

**Add a key phrase:**
Key Phrases → Add → enter the phrase → assign to a document → set confidence boost (0.1–0.5). Use **Suggest** to have the AI propose phrases from your existing documents.

**Handle a PDPA erasure request:**
Settings → Compliance → Erase Contact Data → enter the contact's email. All personal data is deleted within 30 days per PDPA requirements.

**Escalation SLA breach:**
Each account has a configurable SLA (default: 4 hours). If an escalation is not resolved within that window, it automatically escalates to the second-tier backup contact and a breach notification is sent.

### Troubleshooting Common Situations

| Situation                                                | Likely Cause                                      | Action                                           |
| -------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------ |
| Customer says they replied but you didn't receive        | Message classified as high-stakes and escalated   | Check Escalations list                           |
| Auto-reply sounds wrong                                  | Document outdated or wrong document type assigned | Re-upload document, check type                   |
| Escalation email not received                            | Backup contact email wrong or spam folder         | Check Contacts → backup email                    |
| WhatsApp message got template instead of free-form reply | 24-hour session window expired                    | Message was sent as a template; no action needed |
| Document stuck at "Indexing"                             | Restart mid-processing                            | Wait for next startup repair or contact support  |

### Glossary of Terms

| Term                   | Meaning                                                        |
| ---------------------- | -------------------------------------------------------------- |
| **Pending**            | Upload received; processing not yet started                    |
| **Indexing**           | Being parsed, chunked, and embedded for search                 |
| **Ready**              | Fully indexed and active for auto-replies                      |
| **Stale**              | Document may be outdated; re-index recommended                 |
| **Key Phrase**         | A keyword or phrase that routes a query to a specific document |
| **Key Phrase Mapping** | The link between a phrase and the document it routes to        |
| **Auto-reply**         | An AI-generated message sent automatically to a customer       |
| **Escalate**           | Route a query to a human backup contact                        |
| **Include in Context** | The documents the AI used to generate a reply                  |
| **PDPA**               | Singapore Personal Data Protection Act                         |
| **Human Override**     | Flag on a contact indicating they always want human handling   |

---

## 4. Technical Overview

### Architecture

```
Customer (Email/WhatsApp)
        |
        v
SendGrid / Meta Cloud API Webhooks
        |
        v
FastAPI on Vercel Serverless
  |-- InboundEmailProcessor / InboundWhatsAppProcessor
  |-- AutoReplyService
  |     |-- MessageClassifier (LLM — Ollama or OpenAI)
  |     |-- RAGPipeline (pgvector similarity + BM25 keyword)
  |     |-- ResponseGenerator
  |     |-- LearningLoop
  |-- EscalationService
  |-- BillingService (Stripe)
        |
        v
PostgreSQL + pgvector
```

**AI stack:** Primary: Ollama `llama3.1` for LLM, `nomic-embed-text` for embeddings. Fallback: OpenAI `text-embedding-3-small` (only if `OPENAI_API_KEY` is set). Without embeddings, BM25 keyword search handles document retrieval.

### Environment Variables

| Variable                       | Required     | Description                                   |
| ------------------------------ | ------------ | --------------------------------------------- |
| `DATABASE_URL`                 | Yes          | PostgreSQL connection string                  |
| `JWT_SECRET`                   | Yes          | JWT signing secret (min 32 chars, HS256)      |
| `ENCRYPTION_MASTER_KEY`        | Yes          | Base64 32-byte key for PII encryption at rest |
| `APP_ENV`                      | Yes          | `production` on Vercel                        |
| `OPENAI_API_KEY`               | No           | Enables semantic embeddings (costs apply)     |
| `OLLAMA_BASE_URL`              | No           | Default: `http://localhost:11434` (dev only)  |
| `SENDGRID_API_KEY`             | For email    | SendGrid API key                              |
| `STRIPE_API_KEY`               | For billing  | Stripe API key                                |
| `WHATSAPP_ACCESS_TOKEN`        | For WhatsApp | Meta Cloud API token                          |
| `WHATSAPP_PHONE_NUMBER_ID`     | For WhatsApp | WhatsApp phone number ID                      |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | For WhatsApp | Meta business account ID                      |

### Database Models

Core entities: `Tenant`, `Account`, `BackupContact`, `Contact`, `ChannelConsent`, `Message`, `Classification`, `Response`, `RAGRetrieval`, `Escalation`, `Document`, `DocumentChunk`, `LearnedAnswer`, `AuditEntry`, `RoutingOutcome`, `KeyPhraseMapping`.

**Multi-tenancy:** Every record keyed by `tenant_id`. Optional separate PostgreSQL schemas per tenant for stronger isolation.

**PII encryption:** Email and phone fields use `EncryptedString` with tenant-specific keys. Blind index (HMAC of email) enables login lookups without decrypting.

### AI Pipeline

**Classification:** LLM classifies each message into category (routine / semi_routine / complex / high_stakes) and urgency (low / medium / high / critical), with a confidence score.

**RAG retrieval:** Hybrid search — 70% cosine similarity from pgvector embeddings + 30% BM25 keyword score. Synthesized answers cross-checked against source passages for hallucination detection.

**Response routing:**

| Confidence | Category                | Action                                        |
| ---------- | ----------------------- | --------------------------------------------- |
| >= 90%     | routine/semi_routine    | Auto-reply sent immediately                   |
| 60–90%     | routine/semi_routine    | Escalate with AI draft for human review       |
| < 60%      | any                     | Escalate without draft                        |
| any        | high_stakes or critical | Immediate escalation regardless of confidence |

**Learning loop:** When a backup contact resolves an escalation, the human's reply is captured as a Q&A pair and embedded. Future queries search this learned set alongside documents.

### WhatsApp-Specific

Meta's 24-hour session window: free-form text replies only within 24 hours of a customer message. Outside the window, pre-approved template messages are mandatory. The word **"HUMAN"** triggers forced immediate escalation. Rate limits: 250 messages/min globally; 1 per 6 seconds per user.

### Authentication

JWT (HS256, 24-hour expiry) stored in `HttpOnly` cookie. Roles: `admin` (primary backup contact) or `operator`. Tenant isolation via `tenant_id` from JWT payload.

### Key API Endpoints

| Endpoint                                  | Method          | Auth | Description                            |
| ----------------------------------------- | --------------- | ---- | -------------------------------------- |
| `/api/v1/onboarding`                      | POST            | No   | Create tenant, account, backup contact |
| `/api/v1/auth/login`                      | POST            | No   | Login → JWT cookie                     |
| `/api/v1/auth/me`                         | GET             | Yes  | Current operator profile               |
| `/api/v1/portal/documents/upload`         | POST            | Yes  | Upload document (multipart)            |
| `/api/v1/portal/documents/{id}`           | DELETE          | Yes  | Delete document and chunks             |
| `/api/v1/portal/escalations`              | GET             | Yes  | List escalations                       |
| `/api/v1/portal/escalations/{id}/resolve` | POST            | Yes  | Resolve with human answer              |
| `/api/v1/portal/keyphrase/mappings`       | GET/POST/DELETE | Yes  | Key phrase → document mappings         |
| `/api/v1/email/inbound`                   | POST            | No   | SendGrid inbound webhook               |
| `/api/v1/whatsapp/inbound`                | POST            | No   | Meta WhatsApp webhook                  |
| `/api/v1/billing/webhook`                 | POST            | No   | Stripe webhook (signature verified)    |
| `/api/v1/portal/upgrade`                  | POST            | Yes  | Create Stripe checkout session         |

### Deployment

- **Platform:** Vercel (serverless Python via `@vercel/python` runtime)
- **Entry:** `api/index.py` exports `application = app` (FastAPI ASGI app)
- **Build:** `pip install -e .` via `vercel.json` `installCommand`
- **Routing:** All traffic routes to `api/index.py`

### Project Structure

```
src/sequor/
  ai/
    client.py       -- Ollama/OpenAI client
    classifier.py   -- Message classifier (LLM)
    rag_pipeline.py -- Hybrid retrieval + synthesis
    vector_store.py -- pgvector + BM25
    response.py     -- Response generator
    learning.py     -- Learning loop
    ingestion.py    -- Document parser and chunker
  auth.py           -- JWT auth, bcrypt
  billing/          -- Stripe integration
  compliance.py     -- PDPA, HUMAN override, erasure
  config.py        -- pydantic-settings from .env
  db/
    models.py      -- All SQLAlchemy entities
    encrypted_column.py -- EncryptedString type
    schema_manager.py -- Tenant schema creation
  email/
    inbound.py     -- SendGrid webhook processor
    sender.py      -- SendGrid email sender
    auto_reply.py  -- Full email AI pipeline
    templates.py    -- Email HTML/text templates
  escalation/
    service.py     -- Escalation workflow
    sla.py         -- SLA deadline calculator
    scheduler.py    -- Breach detection (runs every 5 min)
  onboarding/
    app.py        -- All routes and templates
    service.py     -- Onboarding business logic
  whatsapp/
    inbound.py    -- Meta webhook processor
    sender.py      -- Meta Cloud API sender
    auto_reply.py  -- Full WhatsApp AI pipeline
  protocols.py      -- EmailSender/WhatsAppSender interfaces
  schemas.py        -- Pydantic validation models
api/
  index.py          -- Vercel ASGI entry point
vercel.json         -- Vercel build + route config
Dockerfile           -- Container image for self-hosting
.github/workflows/   -- CI/CD pipelines
```

### Startup Repair

On every application startup, `_reprocess_stuck_documents()` promotes any document stuck at `indexing` to `ready`. This prevents documents from being permanently stuck if a restart occurs mid-processing.

---

## 5. Developer Guide — Taking Over This Project

### First-Read Files

Read these files in order before making any changes:

1. **`src/sequor/onboarding/app.py`** — All HTTP routes, auth middleware, request handlers.
2. **`src/sequor/ai/rag_pipeline.py`** — Core AI logic: classification, RAG retrieval, synthesis, hallucination detection.
3. **`src/sequor/escalation/service.py`** — Escalation creation, SLA breach detection, second-tier escalation.
4. **`src/sequor/db/models.py`** — All database entities and their relationships.
5. **`src/sequor/config.py`** — Every configuration variable and its source.

### Local Development Setup

```bash
# Requires: Python 3.11+, PostgreSQL 15+, pgvector extension
uv venv && uv sync
cp .env.example .env  # fill in all required values
python -c "CREATE EXTENSION IF NOT EXISTS vector;" # in your postgres DB
uv run uvicorn sequor.onboarding.app:app --reload
```

The app runs at `http://localhost:8000`. Portal pages are at `/portal/*`.

**Why PostgreSQL + pgvector is required:** SQLite cannot be used because it has no vector search capability. The AI pipeline uses hybrid retrieval — 70% pgvector cosine similarity + 30% BM25 keyword scoring — to find the most relevant document passages. This requires pgvector. Managed PostgreSQL with pgvector is available from Supabase, Neon, or Render from ~SGD 5/month for typical small-business usage. This cost is separate from Sequor licensing.

### Dependencies on External Services

| Service                 | Purpose                    | Cost                      |
| ----------------------- | -------------------------- | ------------------------- |
| PostgreSQL + pgvector   | Database and vector search | ~SGD 5–15/month (managed) |
| SendGrid                | Email sending and inbound  | Yes (100 emails/day free) |
| Stripe                  | Billing                    | Yes (test mode)           |
| Meta WhatsApp Cloud API | WhatsApp messaging         | Yes                       |
| Ollama                  | Local LLM (dev only)       | Yes                       |

For production on Vercel: Ollama is unavailable; set `OPENAI_API_KEY` or rely on BM25 search.

### Docker — Self-Hosting

```bash
# Build
docker build -t sequor .

# Run
docker run -d \
  --name sequor \
  -p 8080:8080 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/sequor" \
  -e JWT_SECRET="your-32-char-secret" \
  -e ENCRYPTION_MASTER_KEY="base64-32-byte-key" \
  -e APP_ENV="production" \
  -e SENDGRID_API_KEY="SG.xxx" \
  -e STRIPE_API_KEY="sk_live_xxx" \
  -e WHATSAPP_ACCESS_TOKEN="EAAxxx" \
  -e WHATSAPP_PHONE_NUMBER_ID="123456789" \
  -e WHATSAPP_BUSINESS_ACCOUNT_ID="987654321" \
  sequor
```

The `Dockerfile` uses `python:3.13-slim`, installs dependencies via `uv sync`, and runs uvicorn on port 8080.

### CI/CD Pipeline

The project includes two GitHub Actions workflows:

**`validate.yml`** — Runs on every push and PR to main:

- Validates COC directory structure (`.claude/agents/`, `.claude/skills/`, etc.)
- Checks for Kailash SDK path contamination in project files
- Counts agents, skills, rules, and commands

**`auto-merge.yml`** — Auto-merges dependency updates (Dependabot-style).

**To add a production deployment workflow**, create `.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: python-version: '3.13'
      - run: pip install uv
      - run: uv sync
      - run: uv run pytest tests/ -x

  deploy-vercel:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

Add `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` as GitHub Secrets.

### Database Migrations

Sequor uses SQLAlchemy auto-migrate. Models in `db/models.py` are the schema source of truth. On startup, the app creates or updates tables automatically via `create_all()`.

**Multi-schema tenants:** When a new `Tenant` is created, `schema_manager.py` creates a separate PostgreSQL schema and runs `create_all()` within it. Schema name is derived from the tenant ID.

### Testing

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/sequor --cov-report=term-missing

# Specific module
uv run pytest tests/test_rag_pipeline.py -v
```

### Debugging Common Issues

**Documents stuck at Indexing:**
`_reprocess_stuck_documents()` runs on every startup. Manually: `UPDATE documents SET status = 'ready' WHERE status = 'indexing';`

**Auto-replies not sending:**
Check `AutoReplyService` in `email/auto_reply.py`. Verify Ollama is running (`curl http://localhost:11434/api/tags`). On Vercel, verify `OPENAI_API_KEY` is set.

**Escalations not arriving:**
Verify backup contact email is valid. Check SLA scheduler is started (`scheduler_enabled = True` in config). On Vercel serverless: the SLA scheduler requires a background process — Vercel's free tier does not support background tasks; consider a cron job on a separate worker or self-hosting with the Docker image.

**Webhook not reaching the app:**
For email: verify SendGrid webhook URL is `https://your-domain/api/v1/email/inbound`.
For WhatsApp: verify Meta webhook URL is `https://your-domain/api/v1/whatsapp/inbound` and the verify token matches `whatsapp_verify_token` in config.

### Staging Environment

Create a separate Vercel project for staging:

1. Duplicate your Vercel project from Settings → General → Duplicate Project.
2. Set `APP_ENV=staging` in staging environment variables.
3. Use a separate Stripe webhook endpoint for test mode events.
4. Point staging DNS to the staging deployment URL.
5. Use `STRIPE_TEST_API_KEY` with `sk_test_` prefix in staging.

### Rollback Procedure

**Vercel:**

1. Go to Deployments → find the last working deployment.
2. Click the three-dot menu → **Redeploy**.
3. Select the commit SHA of the known-good version.

**Self-hosted (Docker):**

```bash
# Stop current container
docker stop sequor

# Find the previous image tag
docker images sequor

# Roll back to previous image
docker run -d --name sequor-new -p 8080:8080 sequor:<previous-tag>

# Verify
curl https://your-domain/health
```

### Observability

Structured logs via `structlog`. Key log namespaces: `ollama.*`, `email.*`, `whatsapp.*`, `escalation.*`, `rag.*`. Set `LOG_LEVEL=DEBUG` for verbose output.

For production monitoring: add Sentry to `app.py` lifespan:

```python
import sentry_sdk
sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])
```

### Key Architectural Decisions

1. **Ollama as primary LLM** — Zero per-token cost in development. OpenAI fallback enables production without self-hosted infrastructure.
2. **Hybrid RAG (0.7 vector + 0.3 BM25)** — Pure vector search misses keyword queries; BM25 alone misses semantic matches.
3. **Learning loop from escalation resolutions** — Human answers rank above document passages in retrieval.
4. **EncryptedString for PII** — Blind index enables login lookups without decrypting.
5. **Per-tenant schemas (optional)** — For customers requiring strict data isolation.

---

## 6. Pre-Launch Checklist

The following gaps were identified in a codebase audit. Items must be resolved before production launch.

### Critical — Must Fix Before Any User Traffic

| #   | Gap                                                                                                                                                             | Fix Location                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 1   | **SLA scheduler never starts** — `create_scheduler()` is defined but never called in `app.py` lifespan. Breach detection and second-tier escalation never fire. | `src/sequor/onboarding/app.py` — add scheduler to FastAPI lifespan            |
| 2   | **JWT dev-secret fallback** — if `JWT_SECRET` is unset, falls back to `"dev-secret-change-in-production"` — tokens can be forged.                               | `src/sequor/auth.py:54-57, 64` — remove fallback, raise on startup            |
| 3   | **PDPA erasure leaves Message.body_text** — customer's original message body remains in database after erasure.                                                 | `src/sequor/compliance.py:133-140` — add body_text nullification              |
| 4   | **Plan message limits not enforced** — free tier's 50-message limit is display-only. No rejection or upgrade prompt.                                            | `src/sequor/onboarding/app.py` — add check in email/WhatsApp inbound handlers |

### High — Should Fix Before Launch

| #   | Gap                                                                                                                                       | Fix Location                                                     |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 5   | **WhatsApp template not verified** — `"acknowledgement"` template hardcoded but never confirmed to exist in Meta account. Silent failure. | `src/sequor/whatsapp/auto_reply.py:349-351` — add template check |
| 6   | **No email ChannelConsent record** — WhatsApp tracks consent; email does not. PDPA compliance gap.                                        | `src/sequor/email/inbound.py` — add `_ensure_consent()` call     |
| 7   | **Chunk search loads all rows to memory** — `VectorStore.search()` does `fetchall()` then filters in Python. Will OOM at scale.           | `src/sequor/ai/vector_store.py:122-131` — add SQL LIMIT          |
| 8   | **No health check endpoint** — load balancers have no `/health` to probe.                                                                 | `src/sequor/onboarding/app.py` — add `@app.get("/health")`       |
| 9   | **Over-broad PDPA erasure** — if contact has no messages, ALL document chunk embeddings for the tenant are deleted.                       | `src/sequor/compliance.py:147-149` — scope to contact's own data |

### Medium — Address Before Scaling

| #   | Gap                                                                                                           | Fix Location                                                     |
| --- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 10  | **WhatsApp escalation doesn't feed learning loop** — only email escalation resolutions capture human answers. | `src/sequor/whatsapp/inbound.py` — add `_capture_learning()`     |
| 11  | **Hallucination check silently passes on malformed LLM output** — should reject synthesis instead.            | `src/sequor/ai/rag_pipeline.py:361-363` — reject on parse error  |
| 12  | **Rate limiter per-worker** — in-memory, not shared across uvicorn workers.                                   | `src/sequor/whatsapp/rate_limiter.py` — use Redis-backed limiter |
| 13  | **Event deduplication not worker-safe** — Stripe dedup uses in-memory dict.                                   | `src/sequor/billing/service.py:23-35` — use Redis-backed dedup   |
| 14  | **No observability endpoint** — no `/metrics` for Prometheus.                                                 | `src/sequor/onboarding/app.py` — add `/metrics` route            |
| 15  | **No error reporting** — no Sentry or equivalent.                                                             | Add `sentry-sdk` to `app.py` lifespan                            |

---

## 7. Known Gaps — Acceptable with Mitigations

| Gap                                         | Why Acceptable                               | Mitigation                                             |
| ------------------------------------------- | -------------------------------------------- | ------------------------------------------------------ |
| BM25-only search without OpenAI key         | Works for keyword queries                    | Set `OPENAI_API_KEY` when budget allows                |
| WhatsApp 24-hour session window             | Meta policy; templates are industry standard | Design templates during onboarding                     |
| Server-rendered portal (no WebSocket)       | Simple, no client complexity                 | Refresh acceptable for small teams                     |
| Email consent not tracked                   | WhatsApp consent tracked                     | Add `_ensure_consent()` for email before email scaling |
| No background scheduler on Vercel free tier | Vercel limits; SLA scheduler needs a worker  | Self-host with Docker or use a cron service            |
