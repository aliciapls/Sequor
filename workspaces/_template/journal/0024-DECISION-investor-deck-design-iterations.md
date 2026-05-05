---
name: DECISION-investor-deck-design-iterations
description: Deck redesigns to achieve clean investor-grade look — palette, font, competitor analysis
type: DECISION
date: 2026-05-05
author: co-authored
phase: implement
tags: [pptx, investor, design, deck]
---

## Decisions Made

### Palette: White + Light Teal

User explicitly requested white + duck egg blue. Dark teal was rejected for cover and background use. Final palette:

- **Background**: Pure white (#FFFFFF) on all slides
- **Accent**: Light teal (#D4EAF4, #AAE5E8) for card borders, dividers, bubbles
- **Headers / bars**: Light-medium teal (#29AAA, #1E758F) — not dark
- **Text**: Dark teal (#1475A0 range) for headers, slate gray for body
- **Dark panels**: Removed from cover and all interior slides

### Font: Calibri

`Inter` is not installed on the user's Mac. PowerPoint fell back to Arial with different metrics, breaking all alignment. Switched to Calibri (guaranteed on Mac/Windows).

### Competitor Analysis: Based on Research

Slides 7 built from actual research findings (journals 0008, 0010):

- OpenClaw → personal WhatsApp, no company accounts, no compliance
- Superhuman / SaneBox → reply faster when present, no coverage when absent
- Zendesk / Intercom → manual routing, expensive, not for SE Asia SMBs
- Tidio / Freshdesk → basic AI assist, no RAG, no learning loop, no PDPA

Sequor's differentiation: company accounts, email-first interface, compounding learning loop, smart escalations with PII redaction, PDPA built-in.

### Setup Time: Honest Figure

"2 minute setup" claim was wrong. Realistic estimates:

- WhatsApp connect: ~3 min
- Email connect: ~5 min
- Doc upload (50 docs): ~5 min
- Config: ~10 min

Slide reflects "~5 min for 50 documents" with a Document Quality note.

## Files Changed

- `workspaces/_template/sequor_deck_final.py` — final investor deck script (16 slides)
- `workspaces/_template/Sequor_Investor_Deck_May2026.pptx` — generated output

## Pending: External Email Setup

Email webhook demo still paused — needs Mailgun sandbox or SendGrid with domain. See journal 0022.
