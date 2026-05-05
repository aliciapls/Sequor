# Sequor PE Demo Guide

## What to show PE investors

> "This is a **coverage layer** for lean teams. When a message arrives, our AI reads it, classifies it, and either answers it from the knowledge base or routes it to the right person — without anyone having to be everywhere."

**The problem:** Every team has the same gap — too much inbound, not enough people to handle it. Email piles up. WhatsApp goes unanswered. Follow-ups slip. Hiring isn't happening this quarter.

**The product:** Sequor reads every message. Routine queries get answered automatically. Everything else routes to the right person — with an AI draft so they can respond in seconds, not minutes.

**The math (from our brief):** Gloria Mark's interruption research: 20-25 min recovery per interruption. 10-15 interruptions/day × 5 min = 50-75 min lost/day. At S$80/hour = S$400-600/week recovered. Against S$60/month/seat — not a cost, a recovery.

---

## Quick-start (5 minutes)

```bash
# 1. Start Ollama (AI brain)
ollama serve
ollama pull llama3.1
ollama pull nomic-embed-text

# 2. Start the demo server
./scripts/demo/start_demo.sh

# 3. In another terminal — send test messages
./scripts/demo/send_test_message.sh email routine     # Auto-reply demo
./scripts/demo/send_test_message.sh email complex     # Escalation demo
```

Open the URL shown by start_demo.sh in your browser.

---

## Demo flow to walk PE through

### 1. Signup (2 min)

Open the UI, walk through the 5-step onboarding:

- Step 1: Your organization
- Step 2: Account setup
- Step 3: Email channel
- Step 4: WhatsApp (optional)
- Step 5: Backup contacts

Explain: "5 minutes, no technical knowledge needed."

### 2. Upload documents (1 min)

Upload a sample FAQ. This becomes the knowledge base.

### 3. Send a test message (2 min)

```bash
# Routine query — auto-replied
./scripts/demo/send_test_message.sh email routine

# Complex query — escalated with AI draft
./scripts/demo/send_test_message.sh email complex
```

Watch the server logs show:

```
email.inbound.received     → Message created
classifier.classify.ok      → category=routine, confidence=87%
response.generate.ok       → was_auto_sent=True  ← email sent!
```

vs

```
email.inbound.received     → Message created
classifier.classify.ok      → category=complex, confidence=43%
response.generate.ok        → escalation_needed=True, escalation_has_ai_draft=True
escalation.created          → sent to Bob (backup)
```

### 4. Show what the client sees

- Routine: Client gets an email reply within seconds, from the AI
- Complex: Client gets an acknowledgement, backup contact gets the escalation

---

## For a LIVE demo with a groupmate

To receive real messages from your groupmate, you need ngrok + real API credentials.

### WhatsApp (most impressive)

1. **Create Meta developer account** — https://developers.facebook.com
2. **Create a WhatsApp test app** — WhatsApp > Getting Started > Test Numbers
3. **Add a test phone number** (no business verification needed for test numbers)
4. **Configure webhook URL** in Meta developer console:
   - Callback URL: `https://YOUR-NGROK-URL/api/v1/whatsapp/inbound`
   - Verify token: (set in .env as `WHATSAPP_VERIFY_TOKEN`)
5. **Start ngrok:** `ngrok http 8000`
6. **Your groupmate messages the test number** — shows up live in your server

### Email (SendGrid Inbound Parse)

1. **Set up SendGrid Inbound Parse** — needs MX record for a domain pointing to SendGrid
2. **Configure webhook URL** in SendGrid: `https://YOUR-NGROK-URL/api/v1/email/inbound`
3. **Your groupmate sends to your inbound address** — shows up live

> Note: Email webhook setup requires DNS MX changes and can take up to 48 hrs for propagation. WhatsApp is faster for a same-day demo.

---

## What each file does

| File                         | Purpose                                        |
| ---------------------------- | ---------------------------------------------- |
| `start_demo.sh`              | Starts server + ngrok tunnel                   |
| `send_test_message.sh`       | Simulates incoming message (email or WhatsApp) |
| `run_demo.py`                | Full programmatic demo of the AI pipeline      |
| `test_email_payload.json`    | Sample inbound email payload                   |
| `test_whatsapp_payload.json` | Sample inbound WhatsApp payload                |

---

## Key URLs when server is running

| Service          | URL                                           |
| ---------------- | --------------------------------------------- |
| Signup UI        | http://localhost:8000                         |
| API base         | http://localhost:8000/api/v1                  |
| Email inbound    | http://localhost:8000/api/v1/email/inbound    |
| WhatsApp inbound | http://localhost:8000/api/v1/whatsapp/inbound |

---

## Troubleshooting

**Ollama not running:**

```bash
ollama serve
ollama pull llama3.1
```

**Database error:**

```bash
# Check PostgreSQL is running
psql -h localhost -U postgres -d sequor -c "SELECT 1"
```

**ngrok not working:**

```bash
# Sign up free at https://ngrok.com
# Then:
ngrok config add-authtoken YOUR_TOKEN
ngrok http 8000
```

**Messages not showing up:**

- Check server logs: `tail -f /tmp/sequor_demo_server.log`
- The webhook endpoints require specific headers (see test payloads)
