# DISCOVERY: WhatsApp 24hr window is the central breaking constraint

**Type:** DISCOVERY
**Date:** 2026-04-19

## Finding

All three independent analyses converged on the same breaking point: WhatsApp Business API enforces a 24-hour session window. The Sequor promises multi-day coverage, but WhatsApp sessions close on Day 2.

## Why This Matters

This is not a bug — it's a platform constraint. Pre-approved template messages can re-engage contacts, but:

- WhatsApp review takes 24-48 hours per new template
- Template pool is limited per business account
- The contact sees nothing for hours on urgent Day-2 follow-ups

## Implication for Spec

The spec must explicitly design around this constraint:

1. Pre-approve a library of generic template messages at onboarding (required before first OOO deployment)
2. Product design must acknowledge the 24hr coverage window as a hard limit, not a soft one
3. Email must be a first-class channel (not fallback) because it does not have this window constraint

## Cross-cutting

This finding appeared independently in the technical and business model analyses — both flagged WhatsApp API dependency as existential risk. Confirmed by two agents working in parallel with no knowledge of each other's findings.
