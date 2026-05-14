"""Minimal web server for onboarding — serves signup form and API endpoint.

Uses FastAPI (lightweight, async, Pydantic integration). Runs with:
    uvicorn sequor.onboarding.app:app --reload
"""

import json as _json
import structlog
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

_logger = structlog.get_logger()

# In-memory rate limiters (per-process; sufficient for single-instance uvicorn)
_signup_limiter = IPRateLimiter(max_requests=5, window_seconds=3600)
_upload_limiter = IPRateLimiter(max_requests=20, window_seconds=3600)

app = FastAPI(title="Sequor Onboarding", version="0.1.0")

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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
        return JSONResponse(status_code=500, content={"detail": str(e)})


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
        return JSONResponse(status_code=500, content={"detail": "WHATSAPP_VERIFY_TOKEN not configured"})

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
            return JSONResponse(status_code=403, content={"detail": "Missing X-Hub-Signature-256 header"})

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

        return JSONResponse(status_code=200, content={"status": "ok", "results": serializable_results})
    except Exception:
        _logger.exception("whatsapp.inbound.error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Auth API ──────────────────────────────────────────────────────────────────


@app.get("/api/v1/debug/ping")
async def ping():
    return JSONResponse(content={"ok": True})


@app.get("/api/v1/debug/bcrypt-test")
async def bcrypt_test(password: str = "TestPass", hash: str = None):
    """Test bcrypt hash and verify on the server."""
    import bcrypt as bcrypt_module
    from passlib.context import CryptContext
    import sys
    result = {
        "bcrypt_module": sys.modules.get("bcrypt", None).__name__ if sys.modules.get("bcrypt") else "not_found",
        "bcrypt_file": getattr(sys.modules.get("bcrypt", None), "__file__", "unknown"),
        "password": password,
    }
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    try:
        # Test basic hash + verify with bcrypt direct
        hashed = bcrypt_module.hashpw(password.encode(), bcrypt_module.gensalt())
        verified = bcrypt_module.checkpw(password.encode(), hashed)
        result["bcrypt_version"] = bcrypt_module.__version__
        result["password_bytes_len"] = len(password.encode())
        result["hash"] = hashed.decode()
        result["hash_str_len"] = len(hashed.decode())
        result["bcrypt_direct_verify"] = verified
        # Test with passlib
        try:
            passlib_ok = pwd_context.verify(password, hashed.decode())
            result["passlib_verify"] = passlib_ok
        except Exception as e_pl:
            result["passlib_error"] = str(e_pl)
        # If a hash is provided, also test it with both
        if hash:
            try:
                verified2 = bcrypt_module.checkpw(password.encode(), hash.encode())
                result["hash_verify_bcrypt"] = verified2
            except Exception as e2:
                result["hash_verify_bcrypt_error"] = str(e2)
            try:
                passlib_ok2 = pwd_context.verify(password, hash)
                result["hash_verify_passlib"] = passlib_ok2
            except Exception as e3:
                result["hash_verify_passlib_error"] = str(e3)
            result["hash_provided"] = hash
            result["hash_provided_len"] = len(hash)
        return JSONResponse(content=result)
    except Exception as e:
        import traceback
        result["error"] = str(e)
        result["trace"] = traceback.format_exc()
        return JSONResponse(content=result)


@app.get("/api/v1/debug/login-full")
async def debug_login_full(email: str, password: str):
    """Replicate exact auth_login flow to find where it breaks."""
    from sequor.db.database import get_engine
    from sequor.db.encrypted_column import compute_email_blind_index, set_tenant_key
    from sequor.auth import verify_password, create_access_token_for_operator
    from sequor.db.encryption_keys import KeyManager
    from sequor.config import settings
    from sqlalchemy import select
    from sequor.db.models import BackupContact, Account
    from sqlalchemy.ext.asyncio import AsyncSession

    engine = get_engine()
    async with AsyncSession(engine) as session:
        blind_index = compute_email_blind_index(email)
        result = await session.execute(
            select(BackupContact).where(BackupContact.email_blind_index == blind_index)
        )
        operator = result.scalars().first()
        if not operator:
            return JSONResponse(status_code=401, content={"error": "operator not found"})

        pw_ok = verify_password(password, operator.password_hash)
        if not pw_ok:
            return JSONResponse(status_code=401, content={"error": "wrong password"})

        km = KeyManager(settings.encryption_master_key)
        tenant_key = await km.get_tenant_key(session, operator.tenant_id)
        set_tenant_key(tenant_key)

        # Access operator fields INSIDE session
        name = operator.name
        em = operator.email
        tier_val = operator.tier.value
        op_id = str(operator.id)
        tid = str(operator.tenant_id)
        aid = str(operator.account_id)

        await session.commit()

    # Access operator fields OUTSIDE session
    result_outside = {
        "inside_session_ok": True,
        "name_type": type(name).__name__,
        "email_type": type(em).__name__,
        "tier_value": tier_val,
        "name_repr": repr(name[:20]) if name else None,
        "email_repr": repr(em[:20]) if em else None,
    }

    # Try token creation
    try:
        token = create_access_token_for_operator(
            operator_id=op_id,
            tenant_id=tid,
            account_id=aid,
            name=name,
            email=em,
            role="admin" if tier_val == "primary" else "operator",
        )
        result_outside["token_created"] = True
        result_outside["token_len"] = len(token)
    except Exception as e:
        result_outside["token_error"] = str(e)
        result_outside["token_created"] = False

    # Try JSON serialization of response dict
    try:
        content = {
            "operator": {
                "id": op_id,
                "name": name,
                "email": em,
                "tenant_id": tid,
                "account_id": aid,
                "role": "admin" if tier_val == "primary" else "operator",
            }
        }
        import json
        json.dumps(content)
        result_outside["json_ok"] = True
    except Exception as e:
        result_outside["json_error"] = str(e)
        result_outside["json_ok"] = False

    return JSONResponse(content=result_outside)


@app.get("/api/v1/debug/login")
async def debug_login(email: str, password: str):
    """Step-by-step debug of login failure."""
    from sequor.db.database import get_engine
    from sequor.db.encrypted_column import compute_email_blind_index, set_tenant_key
    from sequor.auth import verify_password
    from sequor.db.encryption_keys import KeyManager
    from sequor.config import settings
    from sqlalchemy import select
    from sequor.db.models import BackupContact
    from sqlalchemy.ext.asyncio import AsyncSession

    step = {"email": email}

    # Step 1: Compute blind index
    try:
        blind_index = compute_email_blind_index(email)
        step["blind_index"] = blind_index
    except Exception as e:
        return JSONResponse(content={"step": "compute_blind_index", "error": str(e)})

    # Step 2: Find operator
    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(BackupContact).where(BackupContact.email_blind_index == blind_index)
        )
        operator = result.scalars().first()
        step["operator_found"] = operator is not None
        if operator:
            step["operator_id"] = str(operator.id)
            step["tenant_id"] = str(operator.tenant_id)
            step["stored_password_hash"] = operator.password_hash if operator.password_hash else None
        else:
            # Show what blind indexes ARE stored for emails containing "@example.com"
            all_result = await session.execute(
                select(BackupContact.email_blind_index, BackupContact.id).limit(20)
            )
            stored = [(str(r[0]), str(r[1])) for r in all_result.fetchall()]
            step["all_stored_indexes"] = stored
            step["looking_for"] = blind_index
            return JSONResponse(content={"step": "find_operator", "result": step})

        # Step 3: Verify password
        try:
            # Diagnostic: show exact types and lengths
            step["password_type"] = type(password).__name__
            step["password_len"] = len(password)
            step["password_hash_type"] = type(operator.password_hash).__name__
            step["password_hash_len"] = len(operator.password_hash) if operator.password_hash else 0
            step["password_hash_first10"] = operator.password_hash[:10] if operator.password_hash else None
            # Now try verify_password
            pw_ok = verify_password(password, operator.password_hash)
            step["password_ok"] = pw_ok
            if not pw_ok:
                return JSONResponse(content={"step": "verify_password", "result": step})
        except Exception as e:
            step["error"] = str(e)
            return JSONResponse(content={"step": "verify_password", "result": step})

        # Step 4: Get tenant key
        try:
            km = KeyManager(settings.encryption_master_key)
            tenant_key = await km.get_tenant_key(session, operator.tenant_id)
            step["tenant_key_ok"] = True
            set_tenant_key(tenant_key)
        except Exception as e:
            return JSONResponse(content={"step": "get_tenant_key", "error": str(e), "result": step})

        # Step 5: Decrypt email
        try:
            decrypted_email = operator.email
            step["decrypted_email"] = decrypted_email
        except Exception as e:
            return JSONResponse(content={"step": "decrypt_email", "error": str(e), "result": step})

        return JSONResponse(content={"step": "all_ok", "result": step})


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

    engine = get_engine()
    async with AsyncSession(engine) as session:
        blind_index = compute_email_blind_index(email)
        result = await session.execute(
            select(BackupContact).where(BackupContact.email_blind_index == blind_index)
        )
        operator = result.scalars().first()

        if not operator:
            return JSONResponse(status_code=401, content={"detail": "Invalid email or password"})

        if not operator.password_hash:
            return JSONResponse(status_code=401, content={"detail": "Invalid email or password"})

        if not verify_password(password, operator.password_hash):
            return JSONResponse(status_code=401, content={"detail": "Invalid email or password"})

        km = KeyManager(settings.encryption_master_key)
        tenant_key = await km.get_tenant_key(session, operator.tenant_id)
        set_tenant_key(tenant_key)

        # Capture all fields while session is open
        op_id = str(operator.id)
        op_name = operator.name
        op_email = operator.email
        op_tier = operator.tier.value
        op_tenant_id = str(operator.tenant_id)
        op_account_id = str(operator.account_id)

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

    response = JSONResponse(content={
        "status": "ok",
        "operator": {
            "id": op_id,
            "name": op_name,
            "email": op_email,
            "tenant_id": op_tenant_id,
            "account_id": op_account_id,
            "account_name": account_name,
            "role": "admin" if op_tier == "primary" else "operator",
        }
    })
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


@app.post("/api/v1/admin/backfill-blind-indexes")
async def backfill_blind_indexes(request: Request):
    """Backfill email_blind_index for all existing BackupContact records.

    This is a one-time migration to support the new encrypted email login.
    """
    _require_auth(request)  # require authentication

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
            except Exception as e:
                errors.append(f"{contact.id}: {e}")

        await session.commit()

    return JSONResponse(content={
        "status": "ok",
        "backfilled": updated,
        "errors": errors,
    })


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

    return JSONResponse(content={
        "operator": {
            "id": payload.get("operator_id"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "tenant_id": payload.get("tenant_id"),
            "account_id": payload.get("account_id"),
            "role": payload.get("role"),
        }
    })


# ── Portal API (authenticated) ──────────────────────────────────────────────────

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

    return JSONResponse(content={
        "stats": {
            "messages_this_week": msg_count or 0,
            "messages_today": today_count or 0,
            "auto_replied_this_week": auto_reply_count or 0,
            "open_escalations": open_esc_count or 0,
        }
    })


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
        messages.append({
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
            }
        })

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
        escalations.append({
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
        })

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
    return JSONResponse(content={
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
    })


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

    return JSONResponse(content={
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
    })


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
            .order_by(desc(Document.uploaded_at))
            .limit(limit)
            .offset(offset)
        )
        docs = result.scalars().all()
        await session.commit()

    return JSONResponse(content={
        "documents": [
            {
                "id": str(d.id),
                "name": d.name,
                "document_type": d.document_type.value if d.document_type else None,
                "status": d.status.value if d.status else None,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            }
            for d in docs
        ]
    })


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

    return JSONResponse(content={
        "whatsapp": {
            "phone_number_id": settings.whatsapp_phone_number_id or "",
            "business_account_id": settings.whatsapp_business_account_id or "",
            "webhook_url": whatsapp_webhook,
            "configured": bool(settings.whatsapp_phone_number_id and settings.whatsapp_access_token),
        },
        "email": {
            "from_domain": settings.email_from_domain or "",
            "webhook_url": email_webhook,
            "configured": bool(settings.sendgrid_api_key),
        },
    })


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
        tenant_result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalars().first()

        account_result = await session.execute(
            select(Account).where(Account.id == account_id)
        )
        account = account_result.scalars().first()

        # Count operators (BackupContact records) for this account
        operator_count = await session.scalar(
            select(func.count(BackupContact.id)).where(
                BackupContact.account_id == account_id
            )
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

        await session.commit()

    # Plan limits by plan type
    plan_limits = {
        "free": {"messages": 50, "operators": 1, "documents": 3},
        "starter": {"messages": 200, "operators": 3, "documents": 5},
        "professional": {"messages": None, "operators": 5, "documents": None},
        "enterprise": {"messages": None, "operators": None, "documents": None},
    }

    plan_name = tenant.plan.value if tenant else "free"
    limits = plan_limits.get(plan_name, plan_limits["free"])
    message_limit = limits["messages"]
    operator_limit = limits["operators"]
    document_limit = limits["documents"]

    # Stripe checkout URL for upgrades (Stripe portal is configured separately)
    upgrade_available = plan_name in ("free", "starter")

    return JSONResponse(content={
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
    })


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
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("subscription.html", {"request": request})


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


def _portal_guard(request: Request):
    """Check if operator is logged in. Redirects to /portal/login if not."""
    from fastapi.responses import RedirectResponse
    token = request.cookies.get("sequor_session") or request.headers.get("x-session-token")
    operator = sessionStorage = None
    if token:
        try:
            import json as _json
        except ImportError:
            _json = None
    if not operator:
        return RedirectResponse(url="/portal/login", status_code=302)
    return None


def _read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text()


@app.get("/portal/dashboard")
async def portal_dashboard(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/portal/messages")
async def portal_messages(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("messages.html", {"request": request})


@app.get("/portal/escalations")
async def portal_escalations(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("escalations.html", {"request": request})


@app.get("/portal/escalations/{esc_id}")
async def portal_escalation_detail(request: Request, esc_id: str):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("escalation.html", {"request": request})


@app.get("/portal/auto-replies")
async def portal_auto_replies(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("auto-replies.html", {"request": request})


@app.get("/portal/contacts")
async def portal_contacts(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("contacts.html", {"request": request})


@app.get("/portal/documents")
async def portal_documents(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("documents.html", {"request": request})


@app.get("/portal/keyphrases")
async def portal_keyphrases(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("keyphrases.html", {"request": request})


@app.get("/portal/channels")
async def portal_channels(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("channels.html", {"request": request})


@app.get("/portal/settings")
async def portal_settings(request: Request):
    token = request.cookies.get("sequor_session")
    if not token:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("settings.html", {"request": request})
