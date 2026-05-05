"""Minimal web server for onboarding — serves signup form and API endpoint.

Uses FastAPI (lightweight, async, Pydantic integration). Runs with:
    uvicorn sequor.onboarding.app:app --reload
"""

import json as _json
import structlog
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sequor.onboarding.api import handle_signup
from sequor.onboarding.rate_limiter import IPRateLimiter, get_client_ip, _mask_ip
from sequor.billing.service import handle_webhook as handle_stripe_webhook
from sequor.dns.service import generate_dns_records, verify_dns_records
from sequor.schemas import DocumentUploadRequest, OnboardingRequest, StripeWebhookEvent

_logger = structlog.get_logger()

# In-memory rate limiters (per-process; sufficient for single-instance uvicorn)
_signup_limiter = IPRateLimiter(max_requests=5, window_seconds=3600)
_upload_limiter = IPRateLimiter(max_requests=20, window_seconds=3600)

app = FastAPI(title="Sequor Onboarding", version="0.1.0")

TEMPLATES_DIR = Path(__file__).parent / "templates"


@app.get("/", response_class=HTMLResponse)
async def signup_page():
    """Serve the onboarding signup form."""
    html = (TEMPLATES_DIR / "signup.html").read_text()
    return HTMLResponse(content=html)


@app.post("/api/v1/onboarding")
async def create_account(request: Request):
    """Process signup form submission."""
    client_ip = get_client_ip(request)
    if not _signup_limiter.is_allowed(client_ip):
        _logger.warning(
            "onboarding.signup.rate_limited",
            client_ip=_mask_ip(client_ip),
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    "Too many signup attempts. Please try again later."
                ),
            },
        )

    body = await request.json()

    try:
        result = await handle_signup(body)
        return JSONResponse(status_code=201, content=result)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    except Exception as e:
        _logger.exception("onboarding.signup.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.post("/api/v1/onboarding/upload")
async def upload_document(
    request: Request,
    tenant_id: str = Form(...),
    account_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a document during onboarding."""
    client_ip = get_client_ip(request)
    if not _upload_limiter.is_allowed(client_ip):
        _logger.warning(
            "onboarding.upload.rate_limited",
            client_ip=_mask_ip(client_ip),
        )
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    "Too many upload attempts. Please try again later."
                ),
            },
        )

    try:
        req = DocumentUploadRequest(
            document_type=document_type,
            filename=file.filename or "",
        )
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})

    try:
        tid = UUID(tenant_id)
        aid = UUID(account_id)
    except ValueError:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid tenant_id or account_id (must be UUID)"},
        )

    try:
        content = await file.read()
    except Exception:
        _logger.exception("onboarding.upload.read_failed")
        return JSONResponse(status_code=400, content={"detail": "Failed to read file"})

    try:
        from sequor.ai.ingestion import DocumentIngester
        from sequor.ai.vector_store import VectorStore
        from sequor.ai.client import get_ollama_client
        from sequor.db.database import get_engine

        engine = get_engine()
        vector_store = VectorStore(engine)
        ingester = DocumentIngester(
            vector_store=vector_store,
            llm_client=get_ollama_client(),
        )
        document_id = await ingester.ingest(
            tenant_id=tid,
            account_id=aid,
            filename=req.filename,
            content=content,
            document_type=req.document_type,
        )
        return JSONResponse(
            status_code=201,
            content={
                "status": "ok",
                "document_id": str(document_id),
                "filename": req.filename,
                "document_type": req.document_type,
            },
        )
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    except Exception:
        _logger.exception("onboarding.upload.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/v1/dns/records")
async def dns_records(domain: str):
    """Return DNS records needed for the given domain."""
    if not domain or "." not in domain:
        return JSONResponse(status_code=422, content={"detail": "Valid domain required"})
    records = generate_dns_records(domain)
    return JSONResponse(content={"domain": domain, "records": records})


@app.get("/api/v1/dns/verify")
async def dns_verify(domain: str):
    """Check whether DNS records are in place for the given domain."""
    if not domain or "." not in domain:
        return JSONResponse(status_code=422, content={"detail": "Valid domain required"})
    result = verify_dns_records(domain)
    return JSONResponse(content=result)


@app.post("/api/v1/billing/webhook")
async def stripe_webhook(request: Request):
    """Process Stripe webhook events with signature verification."""
    body = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        from sequor.billing.service import verify_webhook_signature
        verify_webhook_signature(body, signature)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

    try:
        parsed = _json.loads(body)
        event = StripeWebhookEvent(**parsed)
        from sequor.db.database import get_engine
        from sqlalchemy.ext.asyncio import AsyncSession

        engine = get_engine()
        async with AsyncSession(engine) as session:
            await handle_stripe_webhook(session, event)

        return JSONResponse(status_code=200, content={"status": "ok"})
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    except Exception:
        _logger.exception("billing.webhook.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.post("/api/v1/email/inbound")
async def email_inbound(request: Request):
    """Receive SendGrid Inbound Parse webhook for incoming emails."""
    raw_body = await request.body()
    signature = request.headers.get("x-twilio-email-event-webhook-signature")

    # Reject if signature header is missing — mandatory verification
    if not signature:
        _logger.warning("email.inbound.no_signature")
        return JSONResponse(status_code=403, content={"detail": "Missing signature header"})

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    try:
        from sequor.email.inbound import InboundEmailProcessor
        from sequor.db.database import get_engine
        from sequor.db.crud import SessionCrud
        from sqlalchemy.ext.asyncio import AsyncSession

        engine = get_engine()
        async with AsyncSession(engine) as session:
            crud = SessionCrud(session)
            processor = InboundEmailProcessor(db_express=crud)
            result = await processor.process_sendgrid_payload(
                payload=payload,
                raw_body=raw_body.decode("utf-8", errors="replace") if raw_body else None,
                signature=signature,
            )

            # Wire AI pipeline: classify → RAG → auto-reply or escalate
            if result.get("status") == "created" and not result.get("escalation_resolved"):
                try:
                    from sequor.ai.client import get_ollama_client
                    from sequor.ai.classifier import MessageClassifier
                    from sequor.ai.rag_pipeline import RAGPipeline
                    from sequor.ai.vector_store import VectorStore
                    from sequor.email.auto_reply import AutoReplyService, MessageContext

                    llm = get_ollama_client()
                    vector_store = VectorStore(engine)
                    classifier = MessageClassifier(llm_client=llm)
                    rag = RAGPipeline(vector_store=vector_store, llm_client=llm)

                    from sequor.email.sender import SendGridEmailSender
                    from sequor.ai.learning import LearningLoop
                    email_sender = SendGridEmailSender()
                    learning = LearningLoop(engine=engine)

                    service = AutoReplyService(
                        classifier=classifier,
                        rag_pipeline=rag,
                        email_sender=email_sender,
                        learning_loop=learning,
                    )
                    from uuid import UUID as _UUID

                    ctx = MessageContext(
                        tenant_id=_UUID(result["tenant_id"]),
                        account_id=_UUID(result["account_id"]),
                        contact_email=result.get("contact_email", payload.get("from", "")),
                        message_id=_UUID(result["message_id"]),
                        subject=None,
                        body_text=payload.get("text", ""),
                        channel="email",
                        external_message_id=payload.get("message_id"),
                        in_reply_to=payload.get("in_reply_to"),
                    )
                    ai_result = await service.process_message(ctx)
                    result["ai_routing"] = ai_result.routing_target
                    result["ai_confidence"] = ai_result.confidence_score
                except Exception:
                    _logger.exception("email.inbound.ai_pipeline_failed")

            await session.commit()

        status_code = 200
        if result.get("status") == "rejected":
            status_code = 403

        return JSONResponse(status_code=status_code, content=result)
    except Exception:
        _logger.exception("email.inbound.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.post("/api/v1/whatsapp/inbound")
async def whatsapp_inbound(request: Request):
    """Receive Meta Cloud API webhook for incoming WhatsApp messages."""
    raw_body = await request.body()
    signature_header = request.headers.get("x-hub-signature-256", "")

    # Verify Meta signature (mandatory)
    if not signature_header:
        _logger.warning("whatsapp.inbound.no_signature")
        return JSONResponse(status_code=403, content={"detail": "Missing X-Hub-Signature-256 header"})

    from sequor.whatsapp import verify_meta_signature
    from sequor.config import settings

    if not verify_meta_signature(
        settings.whatsapp_app_secret,
        raw_body,
        signature_header,
    ):
        _logger.warning("whatsapp.inbound.signature_invalid")
        return JSONResponse(status_code=403, content={"detail": "Invalid signature"})

    try:
        payload = await request.json()
    except Exception:
        _logger.warning("whatsapp.inbound.parse_failed")
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON payload"})

    try:
        from sequor.whatsapp.inbound import InboundWhatsAppProcessor
        from sequor.db.database import get_engine
        from sequor.db.crud import SessionCrud
        from sqlalchemy.ext.asyncio import AsyncSession

        engine = get_engine()
        async with AsyncSession(engine) as session:
            crud = SessionCrud(session)
            processor = InboundWhatsAppProcessor(db_express=crud)
            results = await processor.process_meta_payload(payload)

            if not results or results[0].get("status") == "no_account":
                return JSONResponse(status_code=200, content={"status": "ignored"})

            await session.commit()

        return JSONResponse(status_code=200, content={"status": "ok", "results": results})
    except Exception:
        _logger.exception("whatsapp.inbound.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
