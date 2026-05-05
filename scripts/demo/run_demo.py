#!/usr/bin/env .venv/bin/python
"""Sequor Demo — Coverage Layer for Lean Teams.

Run this script to see the full product flow:
  1. An inbound email arrives
  2. The AI reads and classifies it
  3. RAG retrieves the answer from the knowledge base
  4. An auto-reply goes out (routine query)
  5. An escalation is created (complex query)

Usage:
  python scripts/demo/run_demo.py

Requires:
  - Ollama running at http://localhost:11434 (or set OLLAMA_BASE_URL)
  - PostgreSQL running (or set DATABASE_URL)
  - All .env variables configured

For a full UI demo, also run:
  uvicorn sequor.onboarding.app:app --reload --port 8000
Then open http://localhost:8000
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from sequor.ai.classifier import MessageClassifier
from sequor.ai.client import OllamaClient
from sequor.ai.rag_pipeline import RAGPipeline
from sequor.ai.vector_store import VectorStore
from sequor.ai.response import ResponseGenerator
from sequor.email.auto_reply import AutoReplyService, MessageContext
from sequor.email.sender import SendGridEmailSender
from sequor.email.inbound import InboundEmailProcessor
from sequor.db.database import get_engine
from sequor.db.crud import SessionCrud
from sequor.config import settings


DEMO_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
DEMO_CONTACT_EMAIL = "client@example.com"
DEMO_MESSAGE_ID = uuid.uuid4()


def print_header(text: str) -> None:
    width = 72
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def print_step(step: int, text: str) -> None:
    print(f"\n[Step {step}] {text}")
    print("-" * 60)


def print_result(label: str, value: str) -> None:
    print(f"  {label:30s} {value}")


async def setup_demo_data(crud: SessionCrud) -> None:
    """Create demo tenant, account, and contact if they don't exist."""
    print_step(1, "Setting up demo data...")

    # Create tenant
    try:
        tenant = await crud.read("Tenant", str(DEMO_TENANT_ID))
        print_result("Tenant", f"already exists: {tenant['name']}")
    except Exception:
        tenant = await crud.create("Tenant", {
            "id": str(DEMO_TENANT_ID),
            "name": "Acme Consulting",
            "email_domain": "acmeconsulting.com",
            "plan": "professional",
        })
        print_result("Tenant", f"created: {tenant['name']}")

    # Create account
    try:
        account = await crud.read("Account", str(DEMO_ACCOUNT_ID))
        print_result("Account", f"already exists: {account['name']}")
    except Exception:
        account = await crud.create("Account", {
            "id": str(DEMO_ACCOUNT_ID),
            "tenant_id": str(DEMO_TENANT_ID),
            "name": "Acme Sales Team",
            "ownership_type": "department",
            "owner_email": "team@acmeconsulting.com",
            "channels": ["email"],
        })
        print_result("Account", f"created: {account['name']}")

    # Create contact
    try:
        existing = await crud.list("Contact", {"tenant_id": str(DEMO_TENANT_ID), "email": DEMO_CONTACT_EMAIL})
        if existing:
            contact = existing[0]
        else:
            raise ValueError("not found")
    except Exception:
        contact = await crud.create("Contact", {
            "id": str(uuid.uuid4()),
            "tenant_id": str(DEMO_TENANT_ID),
            "email": DEMO_CONTACT_EMAIL,
            "name": "Alice Client",
        })

    print_result("Contact", contact["email"])

    # Create backup contact
    try:
        existing = await crud.list("BackupContact", {"account_id": str(DEMO_ACCOUNT_ID)})
        if existing:
            backup = existing[0]
        else:
            raise ValueError("not found")
    except Exception:
        backup = await crud.create("BackupContact", {
            "id": str(uuid.uuid4()),
            "tenant_id": str(DEMO_TENANT_ID),
            "account_id": str(DEMO_ACCOUNT_ID),
            "name": "Bob Backup",
            "email": "bob@acmeconsulting.com",
            "tier": "primary",
            "active": True,
        })
    print_result("Backup contact", backup["email"])

    print_result("Setup", "complete ✓")


async def demo_routine_query(crud: SessionCrud) -> dict:
    """Demo: Routine question — answered automatically from RAG."""
    print_header("DEMO SCENARIO A — Routine Query (Auto-Reply)")

    # Simulate inbound email payload (SendGrid Inbound Parse format)
    payload = {
        "from": DEMO_CONTACT_EMAIL,
        "to": "team@acmeconsulting.com",
        "subject": "Pricing question",
        "text": "Hi, do you offer monthly billing? Thanks!",
        "sender_ip": "203.0.113.42",
        "message_id": str(uuid.uuid4()),
        "date": datetime.now().isoformat(),
    }
    raw_body = json.dumps(payload)

    print_step(2, "Inbound email received")

    # Create inbound message record
    from sequor.db.models import MessageChannel, MessageDirection
    from sequor.email.inbound import InboundEmailProcessor

    processor = InboundEmailProcessor(db_express=crud)
    result = await processor.process_sendgrid_payload(
        payload=payload,
        raw_body=raw_body,
        signature="dummy",  # Bypassed in dev mode
    )

    print_result("Status", result.get("status", "unknown"))
    print_result("Message ID", str(result.get("message_id", "")))
    print_result("Tenant ID", str(result.get("tenant_id", "")))

    # Wire AI pipeline
    print_step(3, "AI Pipeline — Classify + RAG + Auto-Reply")

    llm = OllamaClient()
    engine = get_engine()
    vector_store = VectorStore(engine)
    classifier = MessageClassifier(llm_client=llm)
    rag = RAGPipeline(vector_store=vector_store, llm_client=llm)
    email_sender = SendGridEmailSender()

    ctx = MessageContext(
        tenant_id=DEMO_TENANT_ID,
        account_id=DEMO_ACCOUNT_ID,
        contact_email=DEMO_CONTACT_EMAIL,
        message_id=uuid.UUID(result["message_id"]),
        subject="Pricing question",
        body_text=payload["text"],
        channel="email",
        external_message_id=payload["message_id"],
        in_reply_to=None,
    )

    service = AutoReplyService(
        classifier=classifier,
        rag_pipeline=rag,
        email_sender=email_sender,
    )

    ai_result = await service.process_message(ctx)

    print_result("Routing", ai_result.routing_target)
    print_result("Confidence", f"{ai_result.confidence_score:.0%}")
    print_result("Confidence badge", ai_result.confidence_badge)
    print_result("Email sent", str(ai_result.email_sent))
    print_result("Escalated", str(ai_result.escalated))

    if ai_result.email_sent:
        print("\n  → Auto-reply sent to client (answered from knowledge base)")
    elif ai_result.escalated:
        print("\n  → Routed to backup contact for review")

    return {
        "scenario": "routine",
        "routing": ai_result.routing_target,
        "confidence": ai_result.confidence_score,
        "badge": ai_result.confidence_badge,
        "auto_reply": ai_result.email_sent,
        "escalated": ai_result.escalated,
    }


async def demo_complex_query(crud: SessionCrud) -> dict:
    """Demo: Complex query — escalated to human backup."""
    print_header("DEMO SCENARIO B — Complex Query (Escalation)")

    payload = {
        "from": DEMO_CONTACT_EMAIL,
        "to": "team@acmeconsulting.com",
        "subject": "Contract negotiation",
        "text": (
            "We'd like to discuss custom terms for an annual contract. "
            "Can we schedule a call to negotiate pricing and SLA guarantees? "
            "This is for a 50-seat enterprise deal."
        ),
        "sender_ip": "203.0.113.42",
        "message_id": str(uuid.uuid4()),
        "date": datetime.now().isoformat(),
    }
    raw_body = json.dumps(payload)

    print_step(2, "Inbound email received")

    processor = InboundEmailProcessor(db_express=crud)
    result = await processor.process_sendgrid_payload(
        payload=payload,
        raw_body=raw_body,
        signature="dummy",
    )

    print_result("Status", result.get("status", "unknown"))
    print_result("Message ID", str(result.get("message_id", "")))

    print_step(3, "AI Pipeline — Classify + RAG + Escalation")

    llm = OllamaClient()
    engine = get_engine()
    vector_store = VectorStore(engine)
    classifier = MessageClassifier(llm_client=llm)
    rag = RAGPipeline(vector_store=vector_store, llm_client=llm)
    email_sender = SendGridEmailSender()

    ctx = MessageContext(
        tenant_id=DEMO_TENANT_ID,
        account_id=DEMO_ACCOUNT_ID,
        contact_email=DEMO_CONTACT_EMAIL,
        message_id=uuid.UUID(result["message_id"]),
        subject="Contract negotiation",
        body_text=payload["text"],
        channel="email",
        external_message_id=payload["message_id"],
        in_reply_to=None,
    )

    service = AutoReplyService(
        classifier=classifier,
        rag_pipeline=rag,
        email_sender=email_sender,
    )

    ai_result = await service.process_message(ctx)

    print_result("Routing", ai_result.routing_target)
    print_result("Confidence", f"{ai_result.confidence_score:.0%}")
    print_result("Confidence badge", ai_result.confidence_badge)
    print_result("Email sent", str(ai_result.email_sent))
    print_result("Escalated", str(ai_result.escalated))

    if ai_result.escalated:
        print("\n  → Routed to backup contact with AI draft for review")
    elif ai_result.email_sent:
        print("\n  → Auto-reply sent to client")

    return {
        "scenario": "complex",
        "routing": ai_result.routing_target,
        "confidence": ai_result.confidence_score,
        "badge": ai_result.confidence_badge,
        "auto_reply": ai_result.email_sent,
        "escalated": ai_result.escalated,
    }


async def main() -> None:
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           SEQUOR — Coverage Layer for Lean Teams             ║")
    print("║                                                              ║")
    print("║  AI reads every message. Routine queries get answered        ║")
    print("║  automatically. Everything else routes to the right person.  ║")
    print("║                                                              ║")
    print("║  No more inbox overwhelm. No missed follow-ups.            ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Check Ollama
    print_header("Checking dependencies")
    llm = OllamaClient()
    try:
        available = await llm.is_available()
        if available:
            print_result("Ollama", f"{settings.ollama_base_url} — connected ✓")
            print_result("Model", settings.llm_model)
        else:
            print_result("Ollama", "NOT AVAILABLE — AI pipeline will escalate by default")
            print("  Run: ollama serve")
            print("  Or set OLLAMA_BASE_URL in .env")
    except Exception as e:
        print_result("Ollama", f"Error: {e}")

    # Check database
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            print_result("Database", "PostgreSQL — connected ✓")
    except Exception as e:
        print_result("Database", f"Error: {e}")
        print("Set DATABASE_URL in .env")
        return

    # Setup demo data
    engine = get_engine()
    async with engine.connect() as conn:
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            crud = SessionCrud(session)
            await setup_demo_data(crud)
            await session.commit()

    # Run demos
    engine = get_engine()
    async with engine.connect() as conn:
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            crud = SessionCrud(session)

            results = []
            results.append(await demo_routine_query(crud))
            await session.commit()

    engine = get_engine()
    async with engine.connect() as conn:
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            crud = SessionCrud(session)

            results.append(await demo_complex_query(crud))
            await session.commit()

    # Summary
    print_header("Demo Complete — What just happened")
    print("""
  A. Routine Query (Pricing question)
     → AI classified as 'routine' with high confidence
     → RAG retrieved the billing info from your documents
     → Auto-reply sent to client immediately (no human needed)

  B. Complex Query (Contract negotiation)
     → AI classified as 'complex' or 'high_stakes'
     → Confidence below auto-reply threshold
     → Escalation created with AI draft → sent to backup contact
     → Bob reviews and responds (or edits the AI draft)

  This is coverage. Every message handled, nothing missed,
  even when your whole team is in back-to-back meetings.
    """)

    print_header("Running the full UI demo")
    print("""
  1. Start the server:
     uvicorn sequor.onboarding.app:app --reload --port 8000

  2. Open http://localhost:8000 in your browser

  3. Fill out the signup form — it's a real 5-step onboarding flow:
     Step 1: Your organization
     Step 2: Account setup
     Step 3: Email channel configuration
     Step 4: WhatsApp (optional)
     Step 5: Backup contacts

  4. Upload some FAQ documents — these become the knowledge base

  5. Send a test email to your configured inbound address
     — watch it get classified, answered, or escalated in real time
    """)


if __name__ == "__main__":
    asyncio.run(main())
