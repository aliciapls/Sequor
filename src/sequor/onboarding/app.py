"""Minimal web server for onboarding — serves signup form and API endpoint.

Uses FastAPI (lightweight, async, Pydantic integration). Runs with:
    uvicorn sequor.onboarding.app:app --reload
"""

import hashlib
import json as _json
import structlog
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sequor.onboarding.api import handle_signup
from sequor.onboarding.rate_limiter import IPRateLimiter, get_client_ip, _mask_ip
from sequor.billing.service import handle_webhook as handle_stripe_webhook
from sequor.dns.service import generate_dns_records, verify_dns_records
from sequor.schemas import DocumentUploadRequest, OnboardingRequest, StripeWebhookEvent

# Precomputed bcrypt hash used to equalize login timing on the no-contact and
# no-password paths, defeating the email-enumeration timing oracle (r2-security
# L2). NOT a secret — a fixed throwaway digest whose only purpose is to burn the
# same bcrypt CPU cycles whether or not the email exists.
_DUMMY_PASSWORD_HASH = "$2b$12$NC7MHZUuMc66eBiPfaeemO3phOr6VH5OfxnD.NHaP0Z3g5mu0PC1i"

_logger = structlog.get_logger()

# In-memory rate limiters (per-process; sufficient for single-instance uvicorn)
_signup_limiter = IPRateLimiter(max_requests=5, window_seconds=3600)
_upload_limiter = IPRateLimiter(max_requests=20, window_seconds=3600)


async def _reprocess_stuck_documents() -> None:
    """Mark documents stuck in 'indexing' as ready (BM25 fallback works without embeddings)."""
    from sequor.db.database import get_engine
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession
    from datetime import datetime, timezone

    engine = get_engine()
    async with AsyncSession(engine) as session:
        # Find documents stuck at 'indexing' with no vector embeddings
        result = await session.execute(
            text(
                """
                SELECT d.id, d.tenant_id, d.name
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id AND dc.embedding IS NOT NULL
                WHERE d.status = 'indexing' AND dc.id IS NULL
            """
            )
        )
        stuck = result.fetchall()
        if not stuck:
            _logger.info("reprocess_stuck.none_found")
            return
        _logger.info("reprocess_stuck.found", count=len(stuck))
        now = datetime.now(timezone.utc)
        for row in stuck:
            doc_id, tenant_id, name = row[0], row[1], row[2]
            await session.execute(
                text(
                    """
                    UPDATE documents
                    SET status = 'ready', last_indexed_at = :now
                    WHERE id = :doc_id
                """
                ),
                {"doc_id": doc_id, "now": now},
            )
            _logger.info(
                "reprocess_stuck.fixed",
                document_id=str(doc_id),
                tenant_id=str(tenant_id),
                name=name,
            )
        await session.commit()


@asynccontextmanager
async def _app_lifespan(app: FastAPI):
    """Startup: create tables if needed, then reprocess stuck documents."""
    try:
        from sequor.db.database import init_db

        await init_db()
        await _reprocess_stuck_documents()
    except Exception:
        _logger.exception("lifespan.startup.failed")
    yield


app = FastAPI(title="Sequor Onboarding", version="0.1.0", lifespan=_app_lifespan)


TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _render(name: str, request: Request, status_code: int = 200, **extra: object) -> HTMLResponse:
    """Render a template without hitting Jinja2's buggy LRUCache."""
    source = (TEMPLATES_DIR / name).read_text()
    tmpl = templates.env.from_string(source)
    return HTMLResponse(content=tmpl.render(request=request, **extra), status_code=status_code)


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
                "detail": ("Too many signup attempts. Please try again later."),
            },
        )

    body = await request.json()

    try:
        result = await handle_signup(body)
        return JSONResponse(status_code=201, content=result)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    except Exception:
        # Do not leak internal exception detail to the caller; log server-side.
        _logger.exception("onboarding.signup.error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Signup failed. Please try again."},
        )


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
                "detail": ("Too many upload attempts. Please try again later."),
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

    # Cap the read at 25MB (mirrors the portal upload limit) so a large upload
    # cannot exhaust process memory before any size check (r2-security M6). Read
    # one byte past the limit to distinguish "exactly at limit" from "over".
    _MAX_UPLOAD_BYTES = 25 * 1024 * 1024
    try:
        content = await file.read(_MAX_UPLOAD_BYTES + 1)
    except Exception:
        _logger.exception("onboarding.upload.read_failed")
        return JSONResponse(status_code=400, content={"detail": "Failed to read file"})

    if len(content) > _MAX_UPLOAD_BYTES:
        return JSONResponse(status_code=413, content={"detail": "File too large (max 25MB)"})

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

    # Signature check: skipped in development mode for local testing without SendGrid credentials.
    from sequor.config import settings

    if settings.app_env != "development":
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

        # Convert UUIDs to strings for JSON serialization
        serializable_result = {}
        for k, v in result.items():
            if hasattr(v, "__str__") and not isinstance(v, (str, int, float, bool, type(None))):
                serializable_result[k] = str(v)
            else:
                serializable_result[k] = v

        return JSONResponse(status_code=status_code, content=serializable_result)
    except Exception:
        _logger.exception("email.inbound.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/v1/whatsapp/inbound")
async def whatsapp_webhook_verify(request: Request):
    """Meta webhook verification — responds to the GET challenge.

    Meta sends GET with hub.mode=subscribe, hub.verify_token, hub.challenge.
    We verify the token matches WHATSAPP_VERIFY_TOKEN and return the challenge.
    """
    from sequor.config import settings

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if not all([mode, token, challenge]):
        return JSONResponse(status_code=404, content={"detail": "Missing verification params"})

    if mode != "subscribe":
        return JSONResponse(status_code=404, content={"detail": "Unknown mode"})

    expected_token = settings.whatsapp_verify_token
    if not expected_token:
        _logger.warning("whatsapp.verify.no_token_configured")
        return JSONResponse(
            status_code=500, content={"detail": "WHATSAPP_VERIFY_TOKEN not configured"}
        )

    if token != expected_token:
        _logger.warning("whatsapp.verify.token_mismatch")
        return JSONResponse(status_code=403, content={"detail": "Token mismatch"})

    _logger.info("whatsapp.verify.ok", mode=mode)
    return PlainTextResponse(content=challenge)


@app.post("/api/v1/whatsapp/inbound")
async def whatsapp_inbound(request: Request):
    """Receive Meta Cloud API webhook for incoming WhatsApp messages."""
    raw_body = await request.body()
    signature_header = request.headers.get("x-hub-signature-256", "")

    # Verify Meta signature (skipped in development mode)
    from sequor.config import settings

    if settings.app_env != "development":
        if not signature_header:
            _logger.warning("whatsapp.inbound.no_signature")
            return JSONResponse(
                status_code=403, content={"detail": "Missing X-Hub-Signature-256 header"}
            )

        from sequor.whatsapp import verify_meta_signature

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

            # Wire AI pipeline: classify → RAG → auto-reply or escalate (WhatsApp)
            for result in results:
                if result.get("status") == "created" and not result.get("human_override"):
                    try:
                        from sequor.ai.client import get_ollama_client
                        from sequor.ai.classifier import MessageClassifier
                        from sequor.ai.rag_pipeline import RAGPipeline
                        from sequor.ai.vector_store import VectorStore
                        from sequor.whatsapp.auto_reply import (
                            WhatsAppAutoReplyService,
                            WhatsAppMessageContext,
                        )
                        from sequor.whatsapp.sender import get_whatsapp_sender
                        from sequor.ai.learning import LearningLoop
                        from uuid import UUID as _UUID

                        llm = get_ollama_client()
                        vector_store = VectorStore(engine)
                        classifier = MessageClassifier(llm_client=llm)
                        rag = RAGPipeline(vector_store=vector_store, llm_client=llm)
                        whatsapp_sender = get_whatsapp_sender()
                        learning = LearningLoop(engine=engine)

                        svc = WhatsAppAutoReplyService(
                            classifier=classifier,
                            rag_pipeline=rag,
                            whatsapp_sender=whatsapp_sender,
                            learning_loop=learning,
                        )

                        ctx = WhatsAppMessageContext(
                            tenant_id=_UUID(result["tenant_id"]),
                            account_id=_UUID(result["account_id"]),
                            contact_phone=result.get("contact_phone", ""),
                            message_id=_UUID(result["message_id"]),
                            body_text=result.get("body_text", ""),
                            channel="whatsapp",
                            external_message_id=result.get("external_message_id"),
                            session_expired=result.get("session_expired", False),
                        )
                        ai_result = await svc.process_message(ctx)
                        result["ai_routing"] = ai_result.routing_target
                        result["ai_confidence"] = ai_result.confidence_score
                        result["ai_message_sent"] = ai_result.message_sent
                        result["ai_sent_via_template"] = ai_result.sent_via_template
                    except Exception:
                        _logger.exception("whatsapp.inbound.ai_pipeline_failed")

            await session.commit()

        # Convert UUIDs to strings for JSON serialization
        serializable_results = []
        for r in results:
            serializable_r = {}
            for k, v in r.items():
                if hasattr(v, "__str__") and not isinstance(v, (str, int, float, bool, type(None))):
                    serializable_r[k] = str(v)
                else:
                    serializable_r[k] = v
            serializable_results.append(serializable_r)

        return JSONResponse(
            status_code=200, content={"status": "ok", "results": serializable_results}
        )
    except Exception:
        _logger.exception("whatsapp.inbound.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Auth API ──────────────────────────────────────────────────────────────────


@app.post("/api/v1/auth/login")
async def auth_login(request: Request):
    """Verify operator credentials and return a JWT in an HttpOnly cookie."""
    body = await request.json()
    email = body.get("email", "")
    password = body.get("password", "")

    if not email or not password:
        return JSONResponse(status_code=400, content={"detail": "Email and password required"})

    from sequor.db.database import get_engine
    from sequor.db.encrypted_column import compute_email_blind_index, set_tenant_key
    from sequor.auth import verify_password, create_access_token_for_operator
    from sequor.db.encryption_keys import KeyManager
    from sequor.config import settings
    from sqlalchemy import select
    from sequor.db.models import BackupContact, Account
    from sqlalchemy.ext.asyncio import AsyncSession

    try:
        engine = get_engine()
        async with AsyncSession(engine) as session:
            blind_index = compute_email_blind_index(email)
            # Use raw SQL to avoid triggering EncryptedString decryption
            # before we have the tenant key set
            from sqlalchemy import text

            row = await session.execute(
                text(
                    "SELECT id, tenant_id, account_id, name, password_hash, tier "
                    "FROM backup_contacts WHERE email_blind_index = :idx AND active = true"
                ),
                {"idx": blind_index},
            )
            contact = row.mappings().first()

            if not contact:
                # Burn equivalent bcrypt cycles so an absent email is not
                # measurably faster than a present one (r2-security L2).
                verify_password(password, _DUMMY_PASSWORD_HASH)
                return JSONResponse(
                    status_code=401, content={"detail": "Invalid email or password"}
                )

            password_hash = contact["password_hash"]
            if not password_hash:
                verify_password(password, _DUMMY_PASSWORD_HASH)
                return JSONResponse(
                    status_code=401, content={"detail": "Invalid email or password"}
                )

            if not verify_password(password, password_hash):
                return JSONResponse(
                    status_code=401, content={"detail": "Invalid email or password"}
                )

            op_id = str(contact["id"])
            op_name = contact["name"]
            op_tenant_id = str(contact["tenant_id"])
            op_account_id = str(contact["account_id"])
            op_tier = (
                contact["tier"].value if hasattr(contact["tier"], "value") else str(contact["tier"])
            )

            # Now set tenant key so we can read encrypted columns
            km = KeyManager(settings.encryption_master_key)
            tenant_key = await km.get_tenant_key(session, UUID(op_tenant_id))
            set_tenant_key(tenant_key)

            # Load the full ORM object now that tenant key is set
            result = await session.execute(
                select(BackupContact).where(BackupContact.id == contact["id"])
            )
            operator = result.scalars().first()
            op_email = operator.email if operator else email

            # `operator` can be None if the contact was removed between the
            # blind-index lookup and this re-select; the op_email line above
            # already anticipates it, so the account lookup MUST guard too
            # rather than dereference operator.account_id on None (r2 Pyright).
            account_name = ""
            if operator is not None:
                acct_result = await session.execute(
                    select(Account).where(Account.id == operator.account_id)
                )
                account = acct_result.scalars().first()
                account_name = account.name if account else ""

            await session.commit()

        token = create_access_token_for_operator(
            operator_id=op_id,
            tenant_id=op_tenant_id,
            account_id=op_account_id,
            name=op_name,
            email=op_email,
            role="admin" if op_tier == "primary" else "operator",
        )

        response = JSONResponse(
            content={
                "status": "ok",
                "operator": {
                    "id": op_id,
                    "name": op_name,
                    "email": op_email,
                    "tenant_id": op_tenant_id,
                    "account_id": op_account_id,
                    "account_name": account_name,
                    "role": "admin" if op_tier == "primary" else "operator",
                },
            }
        )
        response.set_cookie(
            key="sequor_session",
            value=token,
            httponly=True,
            secure=settings.app_env == "production",
            samesite="lax",
            path="/",
            max_age=60 * 60 * 24,
        )
        return response
    except Exception:
        # Never return the traceback/exception detail to an unauthenticated
        # caller — it leaks internal paths, stack frames, and possibly config
        # fragments. Log server-side; return a generic message.
        _logger.exception("login.error")
        return JSONResponse(status_code=500, content={"detail": "Login failed. Please try again."})


@app.post("/api/v1/admin/backfill-blind-indexes")
async def backfill_blind_indexes(request: Request):
    """Backfill email_blind_index for all existing BackupContact records.

    This is a one-time migration to support the new encrypted email login.
    """
    operator = _require_auth(request)
    # Cross-tenant migration op — restrict to admin operators. Without this any
    # authenticated operator could trigger a global iteration over every tenant's
    # BackupContact records (r2-security M4).
    if operator.get("role") != "admin":
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Admin role required")

    from sequor.config import settings
    from sequor.db.database import get_engine
    from sequor.db.encrypted_column import compute_email_blind_index, set_tenant_key
    from sequor.db.encryption_keys import KeyManager
    from sequor.db.models import BackupContact
    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession

    engine = get_engine()
    updated = 0
    errors = []

    async with AsyncSession(engine) as session:
        # Get all contacts missing blind index
        result = await session.execute(
            select(BackupContact).where(BackupContact.email_blind_index == None)
        )
        contacts = result.scalars().all()

        for contact in contacts:
            try:
                # Get tenant key
                km = KeyManager(settings.encryption_master_key)
                tenant_key = await km.get_tenant_key(session, contact.tenant_id)
                set_tenant_key(tenant_key)

                # Decrypt email (EncryptedString.process_result_value decrypts using context key)
                email = contact.email

                # Compute and store blind index
                blind_index = compute_email_blind_index(email)
                await session.execute(
                    update(BackupContact)
                    .where(BackupContact.id == contact.id)
                    .values(email_blind_index=blind_index)
                )
                updated += 1
            except Exception:
                # Log the detail server-side; do NOT echo raw exception text back
                # in the API response (r2-security M4).
                _logger.exception("admin.backfill.contact_failed", contact_id=str(contact.id))
                errors.append(str(contact.id))

        await session.commit()

    return JSONResponse(
        content={
            "status": "ok",
            "backfilled": updated,
            "errors": errors,
        }
    )


@app.post("/api/v1/auth/logout")
async def auth_logout():
    """Clear the session cookie."""
    from fastapi.responses import JSONResponse as JR

    response = JR(content={"status": "ok"})
    response.delete_cookie("sequor_session", path="/")
    return response


@app.get("/api/v1/auth/me")
async def auth_me(request: Request):
    """Return current operator info from the session cookie."""
    token = request.cookies.get("sequor_session")
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    from sequor.auth import decode_token

    payload = decode_token(token)
    if not payload:
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    return JSONResponse(
        content={
            "operator": {
                "id": payload.get("operator_id"),
                "name": payload.get("name"),
                "email": payload.get("email"),
                "tenant_id": payload.get("tenant_id"),
                "account_id": payload.get("account_id"),
                "role": payload.get("role"),
            }
        }
    )


# ── Portal API (authenticated) ─────────────────────────────────────────────────-


def _get_session_operator(request: Request) -> dict | None:
    """Extract operator from the session JWT cookie. Returns None if not authenticated."""
    token = request.cookies.get("sequor_session")
    if not token:
        return None
    from sequor.auth import decode_token

    payload = decode_token(token)
    if not payload:
        return None
    return payload


def _require_auth(request: Request) -> dict:
    """Get current operator or raise 401."""
    operator = _get_session_operator(request)
    if not operator:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Authentication required")
    return operator


@app.get("/api/v1/portal/dashboard")
async def portal_api_dashboard(request: Request):
    """Return dashboard stats for the authenticated operator's account."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]
    account_id = operator["account_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Message, Escalation, Response
    from datetime import datetime, timedelta, timezone

    engine = get_engine()
    async with AsyncSession(engine) as session:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        msg_count = await session.scalar(
            select(func.count(Message.id)).where(
                Message.tenant_id == tenant_id,
                Message.direction == "inbound",
                Message.received_at >= week_ago,
            )
        )

        auto_reply_count = await session.scalar(
            select(func.count(Response.id)).where(
                Response.tenant_id == tenant_id,
                Response.was_auto_sent == True,
                Response.sent_at >= week_ago,
            )
        )

        open_esc_count = await session.scalar(
            select(func.count(Escalation.id)).where(
                Escalation.tenant_id == tenant_id,
                Escalation.status.in_(["pending", "acknowledged", "notification_pending"]),
            )
        )

        today_count = await session.scalar(
            select(func.count(Message.id)).where(
                Message.tenant_id == tenant_id,
                Message.direction == "inbound",
                Message.received_at >= today_start,
            )
        )

        await session.commit()

    return JSONResponse(
        content={
            "stats": {
                "messages_this_week": msg_count or 0,
                "messages_today": today_count or 0,
                "auto_replied_this_week": auto_reply_count or 0,
                "open_escalations": open_esc_count or 0,
            }
        }
    )


@app.get("/api/v1/portal/messages")
async def portal_api_messages(request: Request, limit: int = 50, offset: int = 0):
    """Return recent messages for the authenticated operator's account."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select, desc
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Message, Contact

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Message, Contact)
            .join(Contact, Message.contact_id == Contact.id)
            .where(Message.tenant_id == tenant_id)
            .order_by(desc(Message.received_at))
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()
        await session.commit()

    messages = []
    for msg, contact in rows:
        messages.append(
            {
                "id": str(msg.id),
                "direction": msg.direction.value,
                "channel": msg.channel.value,
                "body_text": msg.body_text or "",
                "subject": msg.subject,
                "received_at": msg.received_at.isoformat() if msg.received_at else None,
                "contact": {
                    "id": str(contact.id),
                    "name": contact.name,
                    "phone": contact.phone,
                    "email": contact.email,
                },
            }
        )

    return JSONResponse(content={"messages": messages, "limit": limit, "offset": offset})


@app.get("/api/v1/portal/escalations")
async def portal_api_escalations(request: Request, limit: int = 50, offset: int = 0):
    """Return escalations for the authenticated operator's account."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select, desc
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Escalation, Message, Contact, BackupContact

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Escalation, Message, Contact, BackupContact)
            .join(Message, Escalation.message_id == Message.id)
            .join(Contact, Message.contact_id == Contact.id)
            .join(BackupContact, Escalation.backup_contact_id == BackupContact.id)
            .where(Escalation.tenant_id == tenant_id)
            .order_by(desc(Escalation.assigned_at))
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()
        await session.commit()

    escalations = []
    for esc, msg, contact, backup in rows:
        escalations.append(
            {
                "id": str(esc.id),
                "status": esc.status.value,
                "priority": esc.priority.value,
                "assigned_at": esc.assigned_at.isoformat() if esc.assigned_at else None,
                "acknowledged_at": esc.acknowledged_at.isoformat() if esc.acknowledged_at else None,
                "resolved_at": esc.resolved_at.isoformat() if esc.resolved_at else None,
                "resolution_summary": esc.resolution_summary,
                "message": {
                    "id": str(msg.id),
                    "body_text": msg.body_text or "",
                    "subject": msg.subject,
                    "received_at": msg.received_at.isoformat() if msg.received_at else None,
                },
                "contact": {
                    "id": str(contact.id),
                    "name": contact.name,
                    "phone": contact.phone,
                },
                "assigned_to": {
                    "id": str(backup.id),
                    "name": backup.name,
                },
            }
        )

    return JSONResponse(content={"escalations": escalations, "limit": limit, "offset": offset})


@app.post("/api/v1/portal/escalations/{esc_id}/resolve")
async def portal_api_escalation_resolve(request: Request, esc_id: str):
    """Mark an escalation as resolved."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    body = await request.json() or {}
    resolution_summary = body.get("resolution_summary", "Resolved via portal")

    from sequor.db.database import get_engine
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Escalation

    engine = get_engine()
    async with AsyncSession(engine) as session:
        await session.execute(
            update(Escalation)
            .where(Escalation.tenant_id == tenant_id, Escalation.id == esc_id)
            .values(status="resolved", resolution_summary=resolution_summary)
        )
        await session.commit()

    return JSONResponse(content={"status": "ok"})


@app.get("/api/v1/portal/escalations/{esc_id}")
async def portal_api_escalation_detail(request: Request, esc_id: str):
    """Return a single escalation with full details."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Escalation, Message, Contact, BackupContact

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Escalation, Message, Contact, BackupContact)
            .join(Message, Escalation.message_id == Message.id)
            .join(Contact, Message.contact_id == Contact.id)
            .join(BackupContact, Escalation.backup_contact_id == BackupContact.id)
            .where(Escalation.tenant_id == tenant_id, Escalation.id == esc_id)
        )
        row = result.first()
        await session.commit()

    if not row:
        return JSONResponse(status_code=404, content={"detail": "Escalation not found"})

    esc, msg, contact, backup = row
    return JSONResponse(
        content={
            "escalation": {
                "id": str(esc.id),
                "status": esc.status.value,
                "priority": esc.priority.value,
                "assigned_at": esc.assigned_at.isoformat() if esc.assigned_at else None,
                "acknowledged_at": esc.acknowledged_at.isoformat() if esc.acknowledged_at else None,
                "resolved_at": esc.resolved_at.isoformat() if esc.resolved_at else None,
                "resolution_summary": esc.resolution_summary,
                "message": {
                    "id": str(msg.id),
                    "body_text": msg.body_text or "",
                    "subject": msg.subject,
                    "channel": msg.channel.value,
                    "direction": msg.direction.value,
                    "received_at": msg.received_at.isoformat() if msg.received_at else None,
                },
                "contact": {
                    "id": str(contact.id),
                    "name": contact.name,
                    "phone": contact.phone,
                    "email": contact.email,
                },
                "assigned_to": {
                    "id": str(backup.id),
                    "name": backup.name,
                },
            }
        }
    )


@app.get("/api/v1/portal/contacts")
async def portal_api_contacts(request: Request, limit: int = 100, offset: int = 0):
    """Return contacts for the authenticated operator's account."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select, desc
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Contact

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Contact)
            .where(Contact.tenant_id == tenant_id)
            .order_by(desc(Contact.last_seen))
            .limit(limit)
            .offset(offset)
        )
        contacts = result.scalars().all()
        await session.commit()

    return JSONResponse(
        content={
            "contacts": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "company": c.company,
                    "tags": c.tags or [],
                    "channel_preference": c.channel_preference.value,
                    "last_seen": c.last_seen.isoformat() if c.last_seen else None,
                }
                for c in contacts
            ]
        }
    )


@app.get("/api/v1/portal/documents")
async def portal_api_documents(request: Request, limit: int = 100, offset: int = 0):
    """Return documents for the authenticated operator's account."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select, desc
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Document

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Document)
            .where(Document.tenant_id == tenant_id)
            .order_by(desc(Document.indexed_at))
            .limit(limit)
            .offset(offset)
        )
        docs = result.scalars().all()

        # Build response while session is still open (avoid DetachedInstanceError)
        docs_response = [
            {
                "id": str(d.id),
                "name": d.name,
                "document_type": d.type.value if d.type else None,
                "status": d.status.value if d.status else None,
                "uploaded_at": d.indexed_at.isoformat() if d.indexed_at else None,
            }
            for d in docs
        ]
        await session.commit()

    return JSONResponse(content={"documents": docs_response})


@app.delete("/api/v1/portal/documents/{document_id}")
async def portal_api_delete_document(request: Request, document_id: str):
    """Delete a document and its chunks. Requires tenant ownership."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import text

    engine = get_engine()

    async with engine.connect() as conn:
        # Verify ownership
        check = await conn.execute(
            text("SELECT tenant_id FROM documents WHERE id = :id"),
            {"id": UUID(document_id)},
        )
        row = check.fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": "Document not found"})
        if str(row[0]) != tenant_id:
            return JSONResponse(status_code=403, content={"error": "Not yours to delete"})

        # Delete chunks first (foreign key)
        await conn.execute(
            text("DELETE FROM document_chunks WHERE document_id = :id"),
            {"id": UUID(document_id)},
        )
        # Delete key phrase mappings
        await conn.execute(
            text("DELETE FROM keyphrase_mappings WHERE document_id = :id"),
            {"id": UUID(document_id)},
        )
        # Delete document
        await conn.execute(
            text("DELETE FROM documents WHERE id = :id"),
            {"id": UUID(document_id)},
        )
        await conn.commit()

    return JSONResponse(content={"status": "deleted"})


@app.post("/api/v1/portal/documents/upload")
async def portal_api_upload_document(
    request: Request,
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a document from the portal using session auth."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]
    account_id = operator["account_id"]

    client_ip = get_client_ip(request)
    if not _upload_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Too many upload attempts. Please try again later."},
        )

    try:
        content = await file.read()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Failed to read file"})

    # Check file size (25MB)
    if len(content) > 25 * 1024 * 1024:
        return JSONResponse(
            status_code=400, content={"error": "File too large. Maximum size is 25MB."}
        )

    # Check file extension
    filename = file.filename or ""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx", "txt"):
        return JSONResponse(
            status_code=400, content={"error": "Unsupported file type. Use PDF, DOCX, or TXT."}
        )

    try:
        from sequor.ai.ingestion import DocumentIngester
        from sequor.ai.vector_store import VectorStore
        from sequor.ai.client import get_ollama_client
        from sequor.db.database import get_engine
        from sequor.db.models import DocumentStatus

        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession
        from datetime import datetime, timezone

        engine = get_engine()
        vector_store = VectorStore(engine)

        now = datetime.now(timezone.utc)
        doc_type_value = document_type

        async with AsyncSession(engine) as session:
            result = await session.execute(
                text(
                    """
                INSERT INTO documents
                (id, tenant_id, name, type, file_hash, chunk_count, indexed_at, last_indexed_at, status)
                VALUES (gen_random_uuid(), :tenant_id, :name, :type, :file_hash,
                 :chunk_count, :indexed_at, :last_indexed_at, :status)
                RETURNING id
                """
                ),
                {
                    "tenant_id": UUID(tenant_id),
                    "name": filename,
                    "type": doc_type_value,
                    "file_hash": hashlib.sha256(content).hexdigest(),
                    "chunk_count": 0,
                    "indexed_at": now,
                    "last_indexed_at": now,
                    "status": DocumentStatus.pending.value,
                },
            )
            row = result.fetchone()
            if row is None:
                raise RuntimeError("document insert returned no id row")
            document_id = row[0]
            await session.commit()

        # Now process with ingester (it will update status to indexing/ready)
        ingester = DocumentIngester(
            vector_store=vector_store,
            llm_client=get_ollama_client(),
        )
        await ingester._update_document_status(
            document_id=document_id,
            status=DocumentStatus.indexing,
        )

        # Parse and chunk
        from sequor.ai.document_parser import get_parser_for_file
        from sequor.ai.chunker import get_chunker_for_document_type

        parser = get_parser_for_file(filename)
        parsed = await parser.parse(content, filename)

        chunker = get_chunker_for_document_type(document_type)
        raw_chunks = chunker.chunk(
            parsed.text,
            metadata={"filename": filename, "document_type": document_type},
        )

        # Try embeddings
        try:
            texts_to_embed = [chunk.text for chunk in raw_chunks]
            embeddings = await ingester._llm.generate_embeddings(texts_to_embed)

            chunk_data = [
                (chunk.index, chunk.text, emb)
                for chunk, emb in zip(raw_chunks, embeddings, strict=True)
            ]

            await vector_store.store_chunks(
                tenant_id=UUID(tenant_id),
                document_id=document_id,
                chunks=chunk_data,
            )

            await ingester._update_document_status(
                document_id=document_id,
                status=DocumentStatus.ready,
            )
        except Exception as e:
            _logger.warning(
                "portal.upload.embedding.failed", document_id=str(document_id), error=str(e)
            )
            # Store chunks without embeddings and mark ready (BM25 still works)
            chunk_data = [(chunk.index, chunk.text, None) for chunk in raw_chunks]
            if chunk_data:
                await vector_store.store_chunks(
                    tenant_id=UUID(tenant_id),
                    document_id=document_id,
                    chunks=chunk_data,
                )
            await ingester._update_document_status(
                document_id=document_id,
                status=DocumentStatus.ready,
            )

        return JSONResponse(
            status_code=201,
            content={
                "status": "ok",
                "document_id": str(document_id),
                "filename": filename,
                "document_type": document_type,
            },
        )
    except ValueError as e:
        return JSONResponse(status_code=422, content={"error": str(e)})
    except Exception as e:
        _logger.exception("portal.upload.error", error=str(e), error_type=type(e).__name__)
        # Categorize for a helpful hint, but do NOT echo the raw exception
        # message to the caller (it can leak internal detail). Full detail is
        # logged server-side above.
        error_msg = str(e).lower()
        if "ollama" in error_msg or "connection" in error_msg:
            return JSONResponse(
                status_code=500,
                content={"error": "AI service unavailable. Please try again shortly."},
            )
        elif "timeout" in error_msg:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Upload timed out. The document may be too large or the AI service is slow."
                },
            )
        elif "vector" in error_msg or "embedding" in error_msg:
            return JSONResponse(
                status_code=500,
                content={"error": "Document processing error. Please try again."},
            )
        else:
            return JSONResponse(
                status_code=500, content={"error": "Upload failed. Please try again."}
            )


@app.get("/api/v1/portal/keyphrase/mappings")
async def portal_api_keyphrase_mappings(request: Request):
    """Return all key phrase mappings for the authenticated operator's tenant."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select, desc
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import KeyPhraseMapping, Document

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(KeyPhraseMapping, Document.name)
            .join(Document, KeyPhraseMapping.document_id == Document.id)
            .where(KeyPhraseMapping.tenant_id == tenant_id)
            .order_by(desc(KeyPhraseMapping.usage_count), KeyPhraseMapping.phrase)
        )
        rows = result.all()

        mappings = []
        for row in rows:
            km = row[0]
            doc_name = row[1]
            mappings.append(
                {
                    "id": str(km.id),
                    "phrase": km.phrase,
                    "aliases": km.aliases or "",
                    "document_id": str(km.document_id),
                    "document_name": doc_name,
                    "mapping_type": km.mapping_type.value,
                    "confidence_boost": km.confidence_boost,
                    "usage_count": km.usage_count,
                    "is_active": km.is_active,
                    "created_at": km.created_at.isoformat() if km.created_at else None,
                }
            )

        await session.commit()

    return JSONResponse(content={"mappings": mappings})


@app.post("/api/v1/portal/keyphrase/mappings")
async def portal_api_keyphrase_create(request: Request):
    """Create a new key phrase mapping."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import KeyPhraseMapping, Document, KeyPhraseMappingType
    from sqlalchemy import select
    from pydantic import BaseModel

    class CreateMappingRequest(BaseModel):
        phrase: str
        aliases: str = ""
        document_id: str
        mapping_type: str = "auto_reply"
        confidence_boost: float = 1.0

    try:
        body = await request.json()
        req = CreateMappingRequest(**body)
    except Exception:
        return JSONResponse(content={"error": "Invalid request body"}, status_code=400)

    # Validate document belongs to tenant
    engine = get_engine()
    async with AsyncSession(engine) as session:
        doc_result = await session.execute(
            select(Document).where(Document.id == req.document_id, Document.tenant_id == tenant_id)
        )
        doc = doc_result.scalar_one_or_none()
        if not doc:
            return JSONResponse(content={"error": "Document not found"}, status_code=404)

        mapping_type = (
            KeyPhraseMappingType(req.mapping_type)
            if req.mapping_type
            else KeyPhraseMappingType.auto_reply
        )

        new_mapping = KeyPhraseMapping(
            tenant_id=tenant_id,
            phrase=req.phrase,
            aliases=req.aliases,
            document_id=req.document_id,
            mapping_type=mapping_type,
            confidence_boost=req.confidence_boost,
        )
        session.add(new_mapping)
        await session.commit()
        await session.refresh(new_mapping)

    return JSONResponse(
        content={
            "id": str(new_mapping.id),
            "phrase": new_mapping.phrase,
            "aliases": new_mapping.aliases or "",
            "document_id": str(new_mapping.document_id),
            "document_name": doc.name,
            "mapping_type": new_mapping.mapping_type.value,
            "confidence_boost": new_mapping.confidence_boost,
            "usage_count": new_mapping.usage_count,
            "is_active": new_mapping.is_active,
            "created_at": new_mapping.created_at.isoformat() if new_mapping.created_at else None,
        },
        status_code=201,
    )


@app.delete("/api/v1/portal/keyphrase/mappings/{mapping_id}")
async def portal_api_keyphrase_delete(request: Request, mapping_id: str):
    """Delete a key phrase mapping."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import KeyPhraseMapping

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            delete(KeyPhraseMapping).where(
                KeyPhraseMapping.id == mapping_id, KeyPhraseMapping.tenant_id == tenant_id
            )
        )
        await session.commit()

    return JSONResponse(content={"deleted": True})


@app.get("/api/v1/portal/keyphrase/suggestions")
async def portal_api_keyphrase_suggestions(request: Request):
    """Generate key phrase suggestions from uploaded documents using AI."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Document

    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Document).where(
                Document.tenant_id == tenant_id, Document.status != None  # noqa: E501
            )
        )
        docs = result.scalars().all()
        # Build response while session is open (avoid DetachedInstanceError)
        docs_response = [
            {
                "id": str(d.id),
                "name": d.name,
                "type": d.type.value if d.type else None,
            }
            for d in docs
        ]
        await session.commit()

    if not docs_response:
        return JSONResponse(
            content={"suggestions": [], "message": "Upload documents first to get suggestions"}
        )

    # Gather document text content (limit to first 3 docs, 2000 chars each for suggestion generation)
    doc_summaries = []
    for doc in docs_response[:3]:
        # Use name as summary since body_text might not be populated
        doc_summaries.append(f"- {doc['name']} ({doc['type'] or 'document'})")

    doc_context = "\n".join(doc_summaries)

    # Get existing mappings to avoid suggesting already-mapped phrases
    existing_mappings = set()
    async with AsyncSession(engine) as session:
        from sequor.db.models import KeyPhraseMapping as KPM

        result = await session.execute(select(KPM.phrase).where(KPM.tenant_id == tenant_id))
        existing = result.scalars().all()
        for p in existing:
            existing_mappings.add(p.lower())
        await session.commit()

    # Generate suggestions using LLM
    try:
        from sequor.ai.client import get_ollama_client

        llm = get_ollama_client()

        system_prompt = """You are a helpful assistant that identifies key phrases customers might use when asking about topics covered in business documents. Given a list of documents, suggest 8-12 common phrases or questions customers would use. Focus on natural language questions and short topic phrases. Return ONLY a JSON array of strings, nothing else. Example: ["pricing", "how much does it cost", "refund policy", "cancel subscription"]"""

        prompt = f"""Based on these documents:\n{doc_context}\n\nSuggest 8-12 key phrases (in English) that customers might use when asking about topics in these documents. Include both short phrases and natural questions. Return ONLY a JSON array of strings."""

        suggestions_text = await llm.generate(
            prompt=prompt, system=system_prompt, temperature=0.5, max_tokens=500
        )

        # Parse the JSON response
        import json

        suggestions = json.loads(suggestions_text)

        # Filter out already-mapped phrases
        new_suggestions = [s for s in suggestions if s.lower() not in existing_mappings]

        # Build response with document associations (all suggestions apply to all docs for now)
        result_suggestions = []
        for phrase in new_suggestions:
            for doc in docs_response[:3]:
                result_suggestions.append(
                    {
                        "phrase": phrase,
                        "document_id": doc["id"],
                        "document_name": doc["name"],
                    }
                )

        return JSONResponse(
            content={
                "suggestions": result_suggestions,
                "source_documents": [d["id"] for d in docs_response[:3]],
            }
        )
    except Exception as e:
        import structlog

        logger = structlog.get_logger()
        logger.warning("keyphrase_suggestions.failed", error=str(e))
        return JSONResponse(
            content={
                "suggestions": [],
                "error": "Could not generate suggestions. Make sure Ollama is running.",
            }
        )


@app.get("/api/v1/portal/channels")
async def portal_api_channels(request: Request):
    """Return channel configuration for the authenticated operator's account."""
    operator = _require_auth(request)
    from sequor.config import settings

    # Build webhook URLs from the request
    scheme = "https" if request.url.scheme == "https" else "http"
    host = request.headers.get("host", "localhost")
    whatsapp_webhook = f"{scheme}://{host}/api/v1/whatsapp/inbound"
    email_webhook = f"{scheme}://{host}/api/v1/email/inbound"

    return JSONResponse(
        content={
            "whatsapp": {
                "phone_number_id": settings.whatsapp_phone_number_id or "",
                "business_account_id": settings.whatsapp_business_account_id or "",
                "webhook_url": whatsapp_webhook,
                "configured": bool(
                    settings.whatsapp_phone_number_id and settings.whatsapp_access_token
                ),
            },
            "email": {
                "from_domain": settings.email_from_domain or "",
                "webhook_url": email_webhook,
                "configured": bool(settings.sendgrid_api_key),
            },
        }
    )


@app.get("/api/v1/portal/subscription")
async def portal_api_subscription(request: Request):
    """Return subscription and usage data for the authenticated operator's account."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]
    account_id = operator["account_id"]

    from sequor.db.database import get_engine
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import Tenant, Account, Message, Document, BackupContact
    from datetime import datetime, timezone

    engine = get_engine()
    async with AsyncSession(engine) as session:
        # Get tenant and account info
        tenant_result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = tenant_result.scalars().first()

        account_result = await session.execute(select(Account).where(Account.id == account_id))
        account = account_result.scalars().first()

        # Count operators (BackupContact records) for this account
        operator_count = await session.scalar(
            select(func.count(BackupContact.id)).where(BackupContact.account_id == account_id)
        )

        # Messages this month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        messages_this_month = await session.scalar(
            select(func.count(Message.id)).where(
                Message.tenant_id == tenant_id,
                Message.direction == "inbound",
                Message.received_at >= month_start,
            )
        )

        # Documents uploaded
        document_count = await session.scalar(
            select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
        )

        # Capture tenant fields inside session before it closes (avoids lazy-load failure)
        tenant_plan = tenant.plan.value if tenant else "free"
        tenant_name = tenant.name if tenant else ""

        await session.commit()

    # Plan limits by plan type
    plan_limits = {
        "free": {"messages": 50, "operators": 1, "documents": 3},
        "starter": {"messages": 200, "operators": 3, "documents": 5},
        "professional": {"messages": None, "operators": 5, "documents": None},
        "enterprise": {"messages": None, "operators": None, "documents": None},
    }

    plan_name = tenant_plan
    limits = plan_limits.get(plan_name, plan_limits["free"])
    message_limit = limits["messages"]
    operator_limit = limits["operators"]
    document_limit = limits["documents"]

    # Stripe checkout URL for upgrades (Stripe portal is configured separately)
    upgrade_available = plan_name in ("free", "starter")

    return JSONResponse(
        content={
            "plan": {
                "name": plan_name,
                "display_name": plan_name.capitalize(),
                "message_limit": message_limit,
                "operator_limit": operator_limit,
                "document_limit": document_limit,
            },
            "usage": {
                "messages_this_month": messages_this_month or 0,
                "operator_count": operator_count or 0,
                "document_count": document_count or 0,
            },
            "upgrade_available": upgrade_available,
        }
    )


@app.get("/api/v1/portal/me")
async def portal_api_me(request: Request):
    """Return current operator's profile with decrypted email and account name."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]
    account_id = operator["account_id"]

    from sequor.db.database import get_engine
    from sequor.db.encryption_keys import KeyManager
    from sequor.db.encrypted_column import set_tenant_key
    from sequor.config import settings
    from sqlalchemy import select, func
    from sqlalchemy.ext.asyncio import AsyncSession
    from sequor.db.models import BackupContact, Account, Escalation

    name = operator.get("name", "")
    email = ""
    role = operator.get("role", "")
    account_name = ""
    escalation_count = 0

    try:
        engine = get_engine()
        async with AsyncSession(engine) as session:
            # Set tenant key so EncryptedString columns decrypt on read
            km = KeyManager(settings.encryption_master_key)
            tenant_key = await km.get_tenant_key(session, UUID(tenant_id))
            set_tenant_key(tenant_key)

            result = await session.execute(
                select(BackupContact).where(BackupContact.id == operator["operator_id"])
            )
            contact = result.scalars().first()

            acct_result = await session.execute(select(Account).where(Account.id == account_id))
            account = acct_result.scalars().first()

            # Count unresolved escalations for sidebar badge
            count_result = await session.execute(
                select(func.count(Escalation.id)).where(
                    Escalation.tenant_id == tenant_id,
                    Escalation.status != "resolved",
                )
            )
            escalation_count = count_result.scalar() or 0

            # Capture fields while session is open (encrypted strings need tenant key context)
            name = contact.name if contact else operator.get("name", "")
            email = contact.email if contact else ""
            role = operator.get("role", "")
            account_name = account.name if account else ""
    except Exception as e:
        _logger.exception("portal_api_me.error", error=str(e))

    return JSONResponse(
        content={
            "name": name,
            "email": email,
            "role": role,
            "account_name": account_name,
            "escalation_count": escalation_count,
        }
    )


@app.post("/api/v1/portal/upgrade")
async def portal_api_upgrade(request: Request):
    """Create a Stripe Checkout session for plan upgrade."""
    operator = _require_auth(request)
    tenant_id = operator["tenant_id"]
    email = operator.get("email", "")

    from sequor.billing.service import create_checkout_session

    success_url = str(request.url_for("portal_subscription")) + "?upgrade=success"
    cancel_url = str(request.url_for("portal_subscription")) + "?upgrade=cancelled"

    checkout_url = await create_checkout_session(
        tenant_id=UUID(tenant_id),
        owner_email=email,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    if not checkout_url:
        return JSONResponse(
            status_code=503,
            content={"error": "Checkout is not available. Please try again later."},
        )

    return JSONResponse(content={"checkout_url": checkout_url})


@app.get("/portal/subscription")
async def portal_subscription(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("subscription.html", request)


@app.get("/portal/login", response_class=HTMLResponse)
async def portal_login():
    """Operator login page."""
    html = (TEMPLATES_DIR / "login.html").read_text()
    return HTMLResponse(content=html)


@app.get("/portal/signup", response_class=HTMLResponse)
async def portal_signup():
    """Operator signup page."""
    html = (TEMPLATES_DIR / "register.html").read_text()
    return HTMLResponse(status_code=200, content=html)


@app.get("/portal/logout")
async def portal_logout():
    """Clear session and redirect to login."""
    from fastapi.responses import RedirectResponse

    response = RedirectResponse(url="/portal/login", status_code=302)
    response.delete_cookie("sequor_session", path="/")
    return response


def _read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text()


@app.get("/portal/dashboard")
async def portal_dashboard(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        try:
            return _render("login.html", request)
        except Exception:
            # Never render a traceback into the page — this branch is
            # unauthenticated. Log server-side; return a static error.
            _logger.exception("template.render_failed", template="login.html")
            return HTMLResponse(
                "<h1>Something went wrong</h1><p>Please try again later.</p>",
                status_code=500,
            )
    try:
        return _render("dashboard.html", request)
    except Exception:
        _logger.exception("template.render_failed", template="dashboard.html")
        return HTMLResponse(
            "<h1>Something went wrong</h1><p>Please try again later.</p>",
            status_code=500,
        )


@app.get("/portal/messages")
async def portal_messages(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("messages.html", request)


@app.get("/portal/escalations")
async def portal_escalations(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("escalations.html", request)


@app.get("/portal/escalations/{esc_id}")
async def portal_escalation_detail(request: Request, esc_id: str):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("escalation.html", request)


@app.get("/portal/auto-replies")
async def portal_auto_replies(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("auto-replies.html", request)


@app.get("/portal/contacts")
async def portal_contacts(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("contacts.html", request)


@app.get("/portal/documents")
async def portal_documents(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("documents.html", request)


@app.get("/portal/keyphrases")
async def portal_keyphrases(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("keyphrases.html", request)


@app.get("/portal/channels")
async def portal_channels(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("channels.html", request)


@app.get("/portal/faq")
async def portal_faq(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("faq.html", request)


@app.get("/portal/settings")
async def portal_settings(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return _render("login.html", request)
    return _render("settings.html", request)
