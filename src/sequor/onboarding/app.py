"""Minimal web server for onboarding — serves signup form and API endpoint.

Uses FastAPI (lightweight, async, Pydantic integration). Runs with:
    uvicorn sequor.onboarding.app:app --reload
"""

from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sequor.onboarding.api import handle_signup
from sequor.billing.service import handle_webhook as handle_stripe_webhook
from sequor.dns.service import generate_dns_records, verify_dns_records
from sequor.schemas import DocumentUploadRequest, OnboardingRequest, StripeWebhookEvent

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
    body = await request.json()

    try:
        result = await handle_signup(body)
        return JSONResponse(status_code=201, content=result)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.post("/api/v1/onboarding/upload")
async def upload_document(
    tenant_id: str = Form(...),
    account_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a document during onboarding."""
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
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"Failed to read file: {e}"})

    try:
        from sequor.ai.ingestion import DocumentIngester
        from sequor.ai.vector_store import VectorStore
        from sequor.ai.client import get_ollama_client

        vector_store = VectorStore()
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
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


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
        parsed = await request.json()
        event = StripeWebhookEvent(**parsed)
        from sequor.db.database import get_engine
        from sqlalchemy.ext.asyncio import AsyncSession

        engine = get_engine()
        async with AsyncSession(engine) as session:
            await handle_stripe_webhook(session, event)

        return JSONResponse(status_code=200, content={"status": "ok"})
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
