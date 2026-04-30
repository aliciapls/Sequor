---
name: DECISION-lean-beta-scope
description: Scoped /todos to lean paid beta — email only, one account per org, 24 todos across 8 milestones
type: DECISION
date: 2026-04-29
created_at: 2026-04-29T20:00:00+08:00
author: co-authored
phase: todos
tags: [scope, beta, mvp, prioritization]
---

## Decision

The implementation plan is scoped to a **lean paid beta** — the minimum product that lets 3-5 organizations pay real money and use it with real client messages. The goal is validation of willingness to pay and usage behavior, not a full production launch.

## What's in the beta (24 todos, 8 milestones)

1. **Foundation** — project setup, database schema, migrations
2. **Email infrastructure** — inbound parsing, outbound sending, pipeline skeleton
3. **Core AI** — classification, document ingestion, RAG retrieval, response generation
4. **Escalation & learning** — structured emails, reply-to-resolve, learning loop, auto-escalation
5. **Daily digest** — morning summary email
6. **Onboarding** — minimal web form (account setup, document upload, email channel connection)
7. **Billing & compliance** — Stripe subscriptions, basic PDPA consent
8. **Integration testing** — end-to-end happy path, escalation chain, error handling

## What's explicitly deferred to post-beta

- WhatsApp channel integration
- Multi-account support per organization
- Weekly recap email
- Document staleness detection and re-indexing
- Multi-channel deduplication
- Contradictory response prevention
- Channel partner infrastructure
- Full PDPA compliance suite
- SOC 2 / ISO 27001 certification
- Mobile app or dashboard
- Routing intelligence flywheel (cross-tenant learning)

## Why this scope

The core value proposition is: "AI handles your email inbox when you're busy." If that doesn't work at S$20/month on email alone, adding WhatsApp, dashboards, and compliance features won't fix it. The beta tests the fundamental hypothesis.

The learning loop is included because it's the key differentiator — the product gets smarter over time. Without it, the beta tests a commodity auto-responder, not the real product.

Billing is included because "sounds useful" is not validation. Paid usage is validation.

**Why:** A full build before validation risks months of engineering on features nobody uses. A lean beta risks weeks of engineering, and either validates the business or invalidates it quickly.

## For Discussion

- Is the onboarding web form necessary for beta, or could we onboard organizations manually and skip the form?
- Should billing be included from day one, or should we offer a free 2-week trial first?
- The learning loop (TODO-13) is architecturally coupled to RAG (TODO-09). If RAG quality is poor on real documents, the learning loop may also underperform. Is this a dependency risk?

## Related to

- Journal 0011-DISCOVERY-market-validation-signal: beta validates the "sounds useful" signal with real payment
- Journal 0009-DECISION-product-design-refinements: beta implements all five design refinements
