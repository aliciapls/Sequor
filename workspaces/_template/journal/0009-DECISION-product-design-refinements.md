---
name: DECISION-product-design-refinements
description: Five key design refinements that reshape the product from individual tool to company coverage layer
type: DECISION
date: 2026-04-29
created_at: 2026-04-29T19:00:00+08:00
author: co-authored
phase: analyze
tags: [product-design, architecture, differentiation]
---

## Decision

Five design refinements were made to the product based on analysis and challenge sessions:

### 1. Account-Based Model (Not Per-Seat)

The product is organized around accounts — communication points the company wants covered — not individual user seats. A solo operator has one account. A firm might have three (secretary, HR, operations). Each account independently configures its channels, routing rules, and escalation chain.

**Why:** Per-seat pricing assumes individual OOO coverage. The real product value is covering a company's communication points — whether that's one person's inbox or a department's shared channel. Accounts map to how companies actually think about communication ownership.

### 2. Email-First, No App

The entire product interface is email. No separate app, no dashboard. Employees interact through their existing inbox — unresolved items arrive as structured emails, replying resolves them, ignoring triggers escalation.

**Why:** "No another platform to toggle between" was a user requirement. Building a separate app creates adoption friction. Email is already the universal interface for knowledge workers. The inbox IS the task tracker.

### 3. Company WhatsApp Number (Not Personal)

WhatsApp uses a company-owned Business API number. Employees never connect their personal WhatsApp. This keeps personal phones personal and gives the company a professional client-facing presence.

**Why:** Privacy boundary between work and personal. Employees won't want their personal WhatsApp connected to a business tool. Company number also looks professional — clients see "Acme Consulting," not "John's iPhone."

### 4. Flexible Channel Choice Per Account

Each account chooses its channels: email only, WhatsApp only, or both. No channel is mandatory. Start simple, add complexity later.

**Why:** Reduces onboarding friction. A firm can start with email only (zero platform risk) and add WhatsApp when ready. Not forcing both channels from day one removes a common adoption barrier.

### 5. Learning from Human Answers

The AI learns from every human response to an escalation. No upfront document preparation required. The knowledge base grows organically through usage.

**Why:** The internal documents assumption was flagged as a gap (journal 0001). Most SMEs don't have clean docs. The learning loop removes this dependency — the product works from day one and gets smarter over time.

## For Discussion

- If the learning loop produces low-quality entries (e.g., a rushed human reply), does the AI learn bad answers? What quality gate is needed?
- Does "no app" limit the product's ability to surface analytics and trends that a dashboard would show better?
- Could the account model create confusion for very small teams where one person wears multiple hats (secretary, HR, ops)?

## Related to

- Journal 0001-GAP-internal-docs-assumption: learning loop resolves the document gap
- Journal 0008-GAP-product-commercial-viability-reckoning: these refinements address the differentiation concerns raised there
