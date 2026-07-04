# R1 — Director onboarding & connect existing systems

> Value principles embodied: P1 (integrate-and-govern, never replace), P2 (director, not builder), P3 (governance is the product), P5 (cross-vendor neutrality). Wedge: mid-market (departmental edge), with enterprise-compliance-grade audit built in from day one.

## The walk (from the director's screen)

Meet **Dana**, an operations manager at a 60-person logistics firm. Dana is not a coder. She has heard "put AI agents to work" from every direction and cannot, because no one can tell her what an agent would be allowed to touch or prove afterward what it did. Sequor is where she starts.

1. **Dana signs up** with her work email. There is no software to install and no code to write. The first screen asks one plain-language question: _"What do you manage, and which systems does your team use every day?"_ She types "customer operations" and picks from a visual list: her CRM (Salesforce), the shared mailbox (Google Workspace), the support desk (Zendesk), and the finance system (a NetSuite ERP). She is naming the systems her company **already** owns — Sequor is not replacing any of them.

2. **Sequor explains what a connection is, before asking for one.** A short card says, in Dana's words: _"A connection lets Sequor read and act inside a system on your behalf — but only as much as you allow, only for the jobs you approve. You can see and revoke it any time."_ No jargon about tokens or scopes. Just: what it does, what it can't do, how to undo it.

3. **Dana connects the first system (the CRM) — scoped to an objective, not handed the keys.** She clicks "Connect Salesforce." Sequor's connector opens Salesforce's own official login. Dana logs in **as herself, inside Salesforce** — Sequor never sees her password. Then Sequor asks the objective-shaped question: _"What kind of work should agents be allowed to do here?"_ Dana picks **"Read customer records and log activity"** and explicitly leaves **"Change opportunity values"** and **"Delete records"** switched off. This is **least-privilege per-objective scoping**: the connection grants only what that class of job needs — nothing more. A plain-language summary appears: _"Agents can look up customers and add notes. Agents cannot change deal amounts or delete anything. You approved this on 3 July."_

4. **Dana connects the rest the same way.** The mailbox connects with **"Read incoming customer mail and draft replies (drafts only — nothing sends without approval)."** The support desk connects with **"Read tickets and propose responses."** The ERP she connects **read-only** — _"Look up invoice status, never post transactions."_ Each connection shows the same three-line summary: what's allowed, what's blocked, when she approved it.

5. **Sequor draws Dana her connected workspace.** A single screen now shows all four systems as connected tiles, each with its scope in plain language and a live **health dot** (connected / needs attention). Crucially, this is **one control surface across four different vendors** — something no single vendor's own tools can give her, because each governs only its own silo. Dana can see her whole operation's agent-surface in one place.

6. **Behind the scenes, Sequor seals Dana's company off from everyone else.** Her company's data, connections, and future agent activity live in an isolated tenant — architecturally separated from every other customer, so no other company can ever see or reach her systems. Dana doesn't configure this; it's the default. A one-line note reassures her: _"Your workspace is private to your company and isolated by design."_

7. **Every step Dana just took is already on the record.** Before she has run a single agent, Sequor has written a **connection audit record**: which systems were connected, the exact scope chosen for each, that Dana (a named human) approved each one, and when. Dana sees a "Download audit record" button and understands, without being told twice, that this is the receipt she could hand to a compliance officer or auditor.

At the end of onboarding Dana has done nothing technical. She has named her systems, chosen in plain language what agents may and may not do in each, and walked away with a single connected workspace and a signed paper trail — **before any agent has touched anything.**

## Features exercised

- **Objective-scoped connectors** — standard connectors to CRM / mail / ticketing / ERP / docs, each granted least-privilege permission tied to a class of job, not blanket access.
- **Delegated login (no credential capture)** — the director authenticates inside each system's own login; Sequor never stores passwords.
- **Plain-language scope summaries** — every connection renders as "what's allowed / what's blocked / who approved / when," no technical vocabulary.
- **Connected-workspace control surface** — one cross-vendor screen showing every system, its scope, and live connection health.
- **Tenant isolation (default-on)** — each company's workspace is architecturally sealed from every other customer.
- **Connection audit record** — an exportable, human-attributed log of every connection and its approved scope, produced automatically.
- **Revoke / re-scope controls** — the director can tighten or withdraw any connection at any time.

## Deliverables / artifacts produced

- A **connected workspace**: the director's systems (CRM/mail/ticketing/ERP) joined under one cross-vendor control surface.
- A **connection audit record**: for each system, the granted scope, the named human who approved it, and the timestamp — exportable as a compliance receipt.
- A set of **per-objective scope policies** (least-privilege grants) that later govern what agents can do in each system.
- A **sealed tenant boundary** isolating the company's data and activity from all other customers.

## Reuse → net-new

**Reuses (shipped substrate):** the comms product already proves the hard half of this flow — non-technical, no-app onboarding in under ten minutes, and schema-per-tenant isolation built to a real regulator's bar (`01-analysis/01-research/09-comms-wedge-mapping.md` §4.4, §4.5). PACT's D/T/R accountability grammar supplies the "who approved what, when" shape of the connection audit record. The connector pattern generalizes the comms channel adapters (email/WhatsApp) to any system-of-record as a governed tool.

**Net-new:** the director-facing **multi-vendor connect-and-scope UI** (objective-scoped least-privilege choices rendered in plain language), the **single cross-vendor connected-workspace surface** (comms today connects one tool-cluster; this spans CRM+mail+ticketing+ERP), and the **connection audit record as a first-class exportable artifact** produced at connect time rather than at run time.

## Why it matters (grounded)

The single loudest fact in the market is that systems of record survive and harden — every incumbent layers agents _on top of_ them, and **61% of CIOs buy AI from vendors they already use** while build-vs-buy swung to **76% bought** (`12-saas-2.0-thesis.md` §3, ESTABLISHED #6). Onboarding that connects-and-governs the systems Dana already owns — instead of asking her to replace them — rides that fact instead of fighting it. And by producing an audit receipt _before_ any agent runs, Sequor makes governance the product, not a feature bolted on later (`13-pitch.md` §3, §6 P1/P3).
