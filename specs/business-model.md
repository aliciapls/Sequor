# Business Model — Pricing, Unit Economics, and Growth

## Pricing Model: Per-Account (Not Per-Seat)

The product is priced **per account** — a communication point the company wants covered. A solo operator pays for 1 account. A 10-person firm might pay for 3 accounts (secretary, HR, operations). The company decides how many communication points they need covered.

### Free Tier

- 1 account, 1 backup contact
- 50 messages/month (inbound + outbound combined)
- 1 document upload (max 10 pages)
- Email channel only
- No WhatsApp
- No RAG auto-reply — all messages routed to backup via email
- Audit log: 7-day retention
- **Purpose**: acquisition; capture the moment a user thinks "I need this"

### Starter Tier — $20/month per account

- 1 account, 3 backup contacts
- 200 messages/month
- 5 document uploads
- Email OR WhatsApp channel (choose one)
- RAG auto-reply enabled (up to 90% confidence threshold)
- AI learns from human answers — gets smarter over time
- Audit log: 90-day retention
- **Purpose**: individual operators (solo consultants, freelancers)

### Professional Tier — $60/month per account

- Up to 5 accounts per organization
- 1,000 messages/month per account
- Unlimited document uploads
- Email + WhatsApp channels on each account
- RAG auto-reply up to 80% confidence threshold
- Advanced routing rules per account
- AI learning loop across all organization accounts
- Daily digest email, weekly recap email
- Audit log: 12-month retention
- **Purpose**: small teams and departments

### Enterprise Tier — $200/month per account

- Unlimited accounts per organization
- Unlimited messages (fair use; abuse protection)
- Unlimited documents
- Dedicated RAG pipeline (higher quality retrieval)
- Advanced routing rules, custom confidence thresholds per account
- PDPA/SOC2 compliance features
- Weekly recap + monthly analytics report via email
- Audit log: 24-month retention + export
- **Purpose**: organizations with compliance requirements or higher volume

---

## Per-Message Overages

Beyond the message quota, per-message pricing applies:

| Tier         | Overage Rate  |
| ------------ | ------------- |
| Free         | Not available |
| Starter      | $0.05/message |
| Professional | $0.03/message |
| Enterprise   | Negotiated    |

Excess messages are not cut off — they continue at overage rate, billed monthly.

---

## Freemium-to-Paid Conversion Mechanics

The free tier is designed to be genuinely useful (not a crippleware demo):

- A user can cover for a 1-week OOO on free tier (50 messages is enough for light inquiry volume)
- WhatsApp and multi-channel are gated behind Starter — this is the primary conversion lever
- RAG auto-reply is gated behind Starter — this is the second conversion lever

Conversion triggers:

1. User tries to connect WhatsApp → prompted to upgrade
2. User uploads 6+ documents → prompted to upgrade (Free limit: 1)
3. User goes OOO and exceeds 50 messages → prompted to upgrade
4. User wants a second account → prompted to upgrade (Professional required for multi-account)

---

## Per-Message vs. Subscription Economics

WhatsApp BSP costs are ~$0.05-0.10/message (inbound + outbound). Email has negligible marginal cost.

At Starter ($20/month, 200 messages included):

- Worst case: 200 messages × $0.10 = $20/month in BSP costs alone
- This leaves $0 for AI inference, hosting, and margin
- **Conclusion**: Starter pricing at $20/month does not cover BSP costs at high message volumes
- **Mitigation**: Message quota is set conservatively; most Starter users will not hit 200 messages/month in practice; the overage rate ensures high-volume users pay more

At Professional ($60/month, 1,000 messages):

- 1,000 messages × $0.07 (blended) = $70/month in BSP costs
- This DOES NOT work at $60/month flat
- **Implication**: Professional tier at $60/month is subsidized by Starter tier revenue; OR message quotas are lower than stated; OR Professional must be priced at $100+/month

---

## Alternative: Per-Query RAG Pricing

For the RAG auto-reply feature specifically (not message routing), a per-query pricing model may be more aligned:

- First 30 RAG queries/month: included in subscription
- Additional RAG queries: $0.10/query
- RAG query = one incoming message that triggers retrieval + synthesis

This aligns cost (BSP messages + AI inference per query) with value (query resolved automatically).

---

## Channel Partner Model

Direct sales to SEA SMEs has a high CAC ($150-400 for self-serve, $1,500+ for sales-assisted). Channel Partners reduce CAC:

**Target partners**: Accountants, HR firms, business advisors, SME business associations

- Partner has existing trust relationship with the SME
- Partner recommends the tool as part of their service offering
- Partner receives 20% recurring revenue share for every customer they refer
- Partner does NOT handle support or billing — that stays with the product

**Unit economics with channel partner**:

- CAC: $50-100 (warm referral vs. cold outreach)
- ACV: $240-720/year (Starter/Professional)
- LTV:CAC: 4.8:1 to 14.4:1 — viable even at low ACV

---

## Geographic Expansion Sequence

| Phase | Market                  | Rationale                                                                                                                       |
| ----- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Singapore               | PDPA compliance infrastructure ready; English-language support; payment rails established; highest willingness-to-pay in region |
| 2     | Malaysia / Thailand     | Similar PDPA regimes; English + local language; urban professional market                                                       |
| 3     | Indonesia / Philippines | Lower willingness-to-pay; local language required; payment rails less mature                                                    |

Pricing localization:

- Singapore: full pricing as stated
- Malaysia/Thailand: 70% of Singapore pricing (local market adjustment)
- Indonesia/Philippines: 40% of Singapore pricing (significant reduction; volume-based)

---

## Unit Economics Summary

| Metric                      | Self-Serve     | Channel Partner |
| --------------------------- | -------------- | --------------- |
| CAC                         | $150-400       | $50-100         |
| ACV (Starter, 1 account)    | $240/year      | $240/year       |
| ACV (Professional, 3 acct)  | $2,160/year    | $2,160/year     |
| LTV (3yr, 70% gross margin) | $504           | $504            |
| LTV:CAC                     | 1.3:1 to 3.4:1 | 5:1 to 10:1     |
| Payback period              | 8-18 months    | 6-12 months     |

**Critical dependency**: Customer life must exceed 24 months for self-serve to work at Starter ACV. Multi-account Professional customers improve unit economics significantly — a 3-account organization at $180/month has stronger LTV:CAC.

---

## Key Assumptions Requiring Validation

1. Median Starter customer message volume: if >200/month, overage revenue offsets BSP costs
2. Median customer life: if <18 months, only Channel Partner model works
3. Channel Partner referral rate: if <20% of customers come from partners, CAC stays high
4. Indonesia/Philippines pricing sensitivity: at 40% of Singapore pricing, does ACV still cover infrastructure costs?

---

## Cost Baseline (Singapore, Starter Tier)

| Cost Item                                     | Monthly Cost per Customer |
| --------------------------------------------- | ------------------------- |
| WhatsApp BSP (100 messages/mo avg)            | $5-10                     |
| AI inference (classification + RAG synthesis) | $3-8                      |
| Vector storage (pgvector)                     | $1-2                      |
| Compute (API servers)                         | $2-4                      |
| Email deliverability                          | $0.50-1                   |
| **Total**                                     | **$11.50-25**             |

Gross margin at $20/month Starter: negative to 43%. Only viable if volume is high enough to negotiate BSP rates down, or if overage revenue is significant.
