# 06 — User Flow: A3 unified confidence gate + badge

How the auto-send gate unification (analysis `01-analysis/10-...`, plan `02-plans/06-...`)
changes what each user sees. The binding change: **the confidence the operator sees on the
badge is the SAME quantity that decided whether the AI auto-sent** — today they are two
different numbers from two different stages, so a message can be auto-sent while its badge
reads "uncertain."

## Why this flow exists (the user-visible bug today)

A contact messages the business. The AI classifies it (classifier LLM, confident) AND retrieves

- synthesizes an answer (RAG, maybe uncertain). Today:

* The **auto-send gate** reads the _classifier_ confidence → high → **auto-sends**.
* The **badge** the contact/operator sees reads the _synthesis_ confidence → low → badge says
  "Uncertain."

So the contact receives an auto-reply labelled "Uncertain," and the operator's audit log shows
a low-confidence message that was sent without them. That mismatch is the product's biggest risk
("sending wrong information is worse than sending none"). A3 makes the gate and the badge one
number.

## Flow — a routine query (unified confidence HIGH)

1. **Contact** emails/WhatsApp-messages the business.
2. AI classifies (routine) + retrieves a fresh doc passage + synthesizes. Unified confidence
   computes to 0.93.
3. `should_auto_respond(0.93 ≥ Account.confidence_threshold)` → **auto-send**.
4. **Contact** receives the reply with a badge that honestly reads the same 0.93 → "High
   confidence" (email X-AI-Confidence header + footer; WhatsApp footer carries the figure).
5. **Operator** sees it in the daily digest as auto-resolved at 93% — the number matches what
   the contact saw. No surprise.

## Flow — confident classifier, uncertain RAG (the bug case, now handled)

1. Contact asks something the classifier tags routine+confident (0.95) but RAG retrieval is weak
   (synthesis 0.3 — no passage actually answers it).
2. Unified confidence = 0.95 × 0.3 × … ≈ low.
3. `should_auto_respond` → **route to backup**, NOT auto-send.
4. **Contact** gets no auto-reply (correct — the AI was not actually sure). **Operator** gets the
   structured escalation with the AI draft + the low unified-confidence badge + RAG citations,
   and decides.
5. Pre-A3 this auto-sent with an "Uncertain" badge; post-A3 it correctly escalates.

## Flow — operator tunes the threshold

1. Operator sets `Account.confidence_threshold` higher (e.g., 0.95) because their domain is
   compliance-sensitive.
2. The unified predicate now requires ≥0.95 to auto-send; 0.90 (which would have auto-sent at
   the default) routes to backup instead.
3. If the operator tries <0.70, the existing acknowledgement prompt fires ("the AI will send
   responses it is less certain about…") — unchanged, now actually wired to the real gate.

## Flow — high-stakes (unchanged, verified)

High-stakes (medical/legal/financial) or HIGH/CRITICAL urgency → the dispatcher routes to
backup BEFORE any confidence gate (`response.py::generate` l.86–91). The contact never gets an
auto-reply; operator + backup are notified immediately. A3 does not touch this — verification
confirmed it already fires.

## What is NOT in this flow

- The WhatsApp "Reply STOP" opt-out keyword — that's §NEW-8 (a compliance decision about the
  Meta opt-out word), separate from the confidence-figure render A3 adds.
- The badge's staleness warning ("[Sources may be outdated…]") — already specified in
  `response-accuracy.md`, feeds the unified quantity's staleness factor; not a new flow.
