"""Unit tests for the document upload endpoint during onboarding."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4


@pytest.fixture
def client():
    from sequor.onboarding.app import app
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestDocumentUploadEndpoint:
    def test_rejects_missing_fields(self, client):
        res = client.post("/api/v1/onboarding/upload")
        assert res.status_code == 422

    def test_rejects_invalid_document_type(self, client):
        res = client.post(
            "/api/v1/onboarding/upload",
            data={
                "tenant_id": str(uuid4()),
                "account_id": str(uuid4()),
                "document_type": "invalid_type",
            },
            files={"file": ("test.pdf", b"content", "application/pdf")},
        )
        assert res.status_code == 422

    def test_rejects_invalid_uuid(self, client):
        res = client.post(
            "/api/v1/onboarding/upload",
            data={
                "tenant_id": "not-a-uuid",
                "account_id": str(uuid4()),
                "document_type": "faq",
            },
            files={"file": ("test.pdf", b"content", "application/pdf")},
        )
        assert res.status_code == 422

    def test_rejects_path_traversal_filename(self, client):
        res = client.post(
            "/api/v1/onboarding/upload",
            data={
                "tenant_id": str(uuid4()),
                "account_id": str(uuid4()),
                "document_type": "faq",
            },
            files={"file": ("../etc/passwd", b"content", "application/pdf")},
        )
        assert res.status_code == 422

    def test_rejects_unsupported_extension(self, client):
        """Unsupported extension is caught by DocumentIngester validation."""
        res = client.post(
            "/api/v1/onboarding/upload",
            data={
                "tenant_id": str(uuid4()),
                "account_id": str(uuid4()),
                "document_type": "faq",
            },
            files={"file": ("test.exe", b"content", "application/octet-stream")},
        )
        # DocumentIngester raises ValueError for unsupported extension
        assert res.status_code in (422, 500)

    @patch("sequor.ai.ingestion.DocumentIngester.ingest", new_callable=AsyncMock)
    @patch("sequor.ai.vector_store.VectorStore.__init__", return_value=None)
    @patch("sequor.ai.client.get_ollama_client")
    def test_successful_upload_returns_201(self, mock_llm, mock_vs_init, mock_ingest):
        mock_ingest.return_value = uuid4()

        from sequor.onboarding.app import app
        from fastapi.testclient import TestClient
        test_client = TestClient(app)

        res = test_client.post(
            "/api/v1/onboarding/upload",
            data={
                "tenant_id": str(uuid4()),
                "account_id": str(uuid4()),
                "document_type": "faq",
            },
            files={"file": ("test.pdf", b"some content", "application/pdf")},
        )
        assert res.status_code == 201
        body = res.json()
        assert body["status"] == "ok"
        assert body["document_type"] == "faq"
        assert body["filename"] == "test.pdf"
