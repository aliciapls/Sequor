# Session Journal: 2026-05-05 — Sequor Portal + Demo Setup

## Session Goal

PE investor demo preparation: make the operator portal fully functional and prepare live demo infrastructure for email and WhatsApp inbound webhooks.

---

## Work Completed

### 1. Portal Mobile Responsiveness

**Problem:** Portal pages were unusable on mobile — sidebar was fixed 252px with no collapse behavior, content was compacted.

**Fix Applied to `src/sequor/onboarding/templates/_portal.html`:**

- Added hamburger button inside `.topbar-left` with inline SVG icon
- Added `.sidebar-overlay` div for backdrop when sidebar is open on mobile
- Added `@media (max-width: 768px)` CSS block in a **separate** `<style>` tag (after the main `</style>`) to prevent child template overrides from stripping it
- Added `toggleSidebar()` JS function and `updateHamburger()` viewport-aware show/hide logic
- Mobile behaviors: sidebar slides in from left, overlay darkens background, hamburger appears in topbar only on mobile
- Stats grid switches from 4 columns to 2 columns on mobile

**Bug Encountered:** Initial mobile CSS was placed inside `{% block page_style %}` — a Jinja2 override block. Child templates like `dashboard.html` redefine this block, stripping the mobile CSS. The rendered page showed `{% block page_style %}{% endblock %}` as literal text at the top because the block content was overridden.

**Bug Fix:** Mobile CSS moved to a second `<style>` block after the closing `</style>` tag, outside any Jinja2 blocks.

### 2. Operator Portal Pages — Full Inventory

All portal pages use Jinja2 `{% extends "_portal.html" %}` with `templates.TemplateResponse()` in FastAPI routes:

| Route                          | Template              | Status                       |
| ------------------------------ | --------------------- | ---------------------------- |
| `/portal/login`                | `login.html`          | Standalone HTML (no Jinja2)  |
| `/portal/signup`               | `register.html`       | Standalone HTML (no Jinja2)  |
| `/portal/dashboard`            | `dashboard.html`      | ✅ Jinja2 + TemplateResponse |
| `/portal/messages`             | `messages.html`       | ✅ Jinja2 + TemplateResponse |
| `/portal/escalations`          | `escalations.html`    | ✅ Jinja2 + TemplateResponse |
| `/portal/escalations/{esc_id}` | `escalation.html`     | ✅ Jinja2 + TemplateResponse |
| `/portal/auto-replies`         | `auto-replies.html`   | ✅ Jinja2 + TemplateResponse |
| `/portal/contacts`             | `contacts.html`       | ✅ Jinja2 + TemplateResponse |
| `/portal/documents`            | `documents.html`      | ✅ Jinja2 + TemplateResponse |
| `/portal/keyphrases`           | `keyphrases.html`     | ✅ Jinja2 + TemplateResponse |
| `/portal/channels`             | `channels.html`       | ✅ Jinja2 + TemplateResponse |
| `/portal/subscription`         | `subscription.html`   | ✅ Jinja2 + TemplateResponse |
| `/portal/settings`             | Inline HTML in app.py | ✅                           |

**Auth Flow:**

- Login: `sessionStorage.setItem('sequor_operator', ...)` + `document.cookie = 'sequor_session=...'` (both set client-side)
- Portal routes: server checks `request.cookies.get("sequor_session")`, redirects to login if absent
- Logout: `sessionStorage.clear()` + redirect

**Demo credentials:**

- `demo@sequor.com` / `demo1234` (also `owner@integrationtest.com` / `demo1234`)
- Hardcoded in `login.html` JS as `DEMO_ACCOUNTS` array

**Root `/` serves `signup.html`** — the product landing page with:

- Sticky header (Log in ghost button + Get started primary button)
- Hero section with duck-egg blue gradient
- Metrics strip: 80% auto-replied, 4hr SLA, 2min setup, PDPA compliant
- 6-card feature grid
- Live dashboard iframe preview
- 4-tier pricing grid (Free $0, Solo $15, Starter $35 featured, Professional $55)
- All "Get started" buttons link to `/portal/signup`
- Footer with product links

### 3. Landing Page → Portal Signup Fix

**Problem:** `/portal/signup` was incorrectly serving `signup.html` (the landing page) instead of the actual signup form.

**Root Cause:** The `/portal/signup` route used `HTMLResponse(content=_read_template("signup.html"))` which returned the landing page.

**Fix:** Created `register.html` (standalone signup form with no Jinja2) and updated the route to serve it:

```python
@app.get("/portal/signup", response_class=HTMLResponse)
async def portal_signup():
    html = (TEMPLATES_DIR / "register.html").read_text()
    return HTMLResponse(content=html)
```

### 4. Email Inbound Webhook Setup

**Server running at:** `http://localhost:8000`

**Webhook endpoint:** `POST /api/v1/email/inbound`

- Accepts JSON payload (or form-encoded from SendGrid)
- Verifies signature header in non-development mode
- Routes through `InboundEmailProcessor`
- If message is `status=created` and not `escalation_resolved`, triggers AI pipeline:
  - `MessageClassifier` → classifies intent
  - `RAGPipeline` → retrieves relevant document context
  - `AutoReplyService` → generates and sends reply
  - `LearningLoop` → records feedback for improvement
- Commits to DB and returns JSON response

**AI pipeline wiring in app.py lines 238-281:**

```python
if result.get("status") == "created" and not result.get("escalation_resolved"):
    llm = get_ollama_client()
    vector_store = VectorStore(engine)
    classifier = MessageClassifier(llm_client=llm)
    rag = RAGPipeline(vector_store=vector_store, llm_client=llm)
    email_sender = SendGridEmailSender()
    learning = LearningLoop(engine=engine)
    service = AutoReplyService(classifier=classifier, rag_pipeline=rag,
                                email_sender=email_sender, learning_loop=learning)
    ctx = MessageContext(tenant_id=..., account_id=..., ...)
    ai_result = await service.process_message(ctx)
```

### 5. WhatsApp Inbound Webhook Setup

**Webhook endpoint:** `POST /api/v1/whatsapp/inbound`

- Meta signature verification (skipped in development mode)
- `GET /api/v1/whatsapp/inbound` handles Meta webhook verification challenge
- Routes through `InboundWhatsAppProcessor`
- Processes incoming messages, stores to DB

**Webhook verify token:** `settings.whatsapp_verify_token`

### 6. ngrok Tunnel Setup

**ngrok command:** `ngrok http 8000`
**Public URL:** `https://badland-swizzle-childlike.ngrok-free.dev`
**Required for:** Exposing local webhook endpoint to external services (SendGrid, Mailgun, Meta WhatsApp)

**Error encountered:** `ERR_NGROK_334` — tunnel already online from previous session. **Fix:** `pkill -f "ngrok http"` then restart.

### 7. Live Demo Curl Commands

**WhatsApp inbound:**

```bash
curl -s -X POST http://localhost:8000/api/v1/whatsapp/inbound \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[{"id":"...","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"phone_number_id":"PHONE_NUMBER_ID","display_phone_number":"15550000000"},"contacts":[{"wa_id":"15550000000","profile":{"Name":"Alice"}}],"messages":[{"from":"15550000000","id":"wamid.HBgLMTU1NTAwMDAwMDAw","timestamp":"'$(date +%s)'","type":"text","text":{"body":"Hi, I need help with my order #12345"}}]}}]}]}'
```

**Email inbound:**

```bash
curl -s -X POST http://localhost:8000/api/v1/email/inbound \
  -H "Content-Type: application/json" \
  -d '{"from":"customer@example.com","to":"demo@sequor.com","subject":"Urgent: Order inquiry","text":"Hello, I sent a payment yesterday but have not received confirmation. Order ref: ORD-9876","message_id":"msg-'$(date +%s)'"}'
```

### 8. Email External Demo — Paused

**Attempted:** Setting up Mailgun sandbox or SendGrid for real external email reception.
**Blocked by:** No domain with MX record access available for the demo.
**Decision:** Pause external email testing. Use curl simulation for demo instead.

**For future setup when domain is available:**

1. Get Mailgun sandbox domain (e.g. `sandbox123456.mailgun.org`)
2. Add groupmate's email as Authorized Recipient
3. Groupmate verifies via Mailgun email link
4. Set Mailgun Inbound Parse route to `https://badland-swizzle-childlike.ngrok-free.dev/api/v1/email/inbound`
5. Test: groupmate sends to `demo@sandbox123456.mailgun.org` → appears in portal

---

## Key Files Modified

- `src/sequor/onboarding/app.py` — FastAPI app with all routes, Jinja2Templates setup, AI pipeline wiring
- `src/sequor/onboarding/templates/_portal.html` — Base Jinja2 layout with mobile-responsive CSS fix
- `src/sequor/onboarding/templates/login.html` — Standalone login page (no Jinja2), sets auth cookie
- `src/sequor/onboarding/templates/register.html` — Standalone signup form (no Jinja2)
- `src/sequor/onboarding/templates/signup.html` — Product landing page with iframe dashboard preview
- `src/sequor/onboarding/templates/dashboard.html` — Dashboard with stats, charts, recent messages
- `src/sequor/onboarding/templates/subscription.html` — Subscription/billing page
- `src/sequor/onboarding/templates/messages.html` — Message history
- `src/sequor/onboarding/templates/escalations.html` — Escalation queue
- `src/sequor/onboarding/templates/auto-replies.html` — Auto-reply log
- `src/sequor/onboarding/templates/contacts.html` — Backup contacts
- `src/sequor/onboarding/templates/documents.html` — Document hub
- `src/sequor/onboarding/templates/keyphrases.html` — Key phrase mappings
- `src/sequor/onboarding/templates/channels.html` — Channel configuration
- `src/sequor/onboarding/templates/escalation.html` — Escalation detail page

## Key Architecture Decisions

1. **Standalone HTML for login/register/landing** — These don't use Jinja2 template inheritance. They are self-contained HTML files served via `HTMLResponse(content=path.read_text())`. This avoids Jinja2 block override issues.

2. **Jinja2 for portal pages** — All authenticated portal pages use `{% extends "_portal.html" %}` with `templates.TemplateResponse()` so the base layout (sidebar, topbar, user info) is shared.

3. **Cookie-based auth** — `sequor_session` cookie is set client-side on login/signup. FastAPI route guards check `request.cookies.get("sequor_session")`. Portal pages redirect to login if cookie absent.

4. **AI pipeline triggered post-commit** — In `email_inbound`, the AI pipeline runs inside the `async with AsyncSession(engine) as session` block, after `crud` operations but before `session.commit()`. This ensures DB state is consistent before AI processing.

5. **Mobile CSS outside Jinja2 blocks** — All universal CSS that must not be overridden by child templates is placed in a separate `<style>` block after `</style>`.

---

## Pending / Future Work

- [ ] External email webhook — set up Mailgun sandbox or SendGrid with domain MX records
- [ ] WhatsApp Meta webhook verification — needs public URL + proper verify token in `.env`
- [ ] Dashboard data — currently static/sample data; real data flows from actual webhook processing
- [ ] Escalation detail page — `escalation.html` template exists but escalation data model wiring unclear
- [ ] `.env` configuration for WhatsApp verify token, SendGrid API key, Stripe keys
