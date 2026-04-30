# GAP: PDPA PII in contact messages — retention and erasure

**Type:** GAP
**Date:** 2026-04-19

## Finding

Data model spec says contacts' messages are retained for 24 months (PDPA). But contact messages may contain PII: NRIC numbers (Singapore), passport data, phone numbers, addresses. Classification and RAGRetrieval records store the raw message text — this is PII.

## The Problem

- Right to erasure: a contact can request deletion of their data
- But Classification/RAGRetrieval records contain the original message text with PII
- AuditEntry is immutable — cannot be deleted or anonymized
- Deleting the Contact record leaves orphaned message content in Classification/RAGRetrieval

## What Is Missing

A PII detection layer: when a message arrives, a PII scanner should detect NRIC, passport numbers, credit card numbers, etc. Those fields should be redacted from the stored text and replaced with `[PII REDACTED]`. The raw PII is never stored.

AuditEntry retains the full message for accountability, but the message content stored in Classification/RAGRetrieval is PII-scrubbed.

## Action Required

Add PII handling section to data-model.md. Specify: what PII types are detected, where redaction happens (ingestion pipeline), and how erasure requests are handled for Classification/RAGRetrieval records.
