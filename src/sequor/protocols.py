"""Protocol interfaces for cross-branch dependencies.

Branch 3 (onboarding, operations) depends on features from Branch 1 (email)
and Branch 2 (AI/RAG). These Protocol classes define the interfaces Branch 3
needs so it can develop and test independently.

At merge time, swap in the real implementations from the other branches.
"""

from typing import Any, Protocol
from uuid import UUID


class EmailSender(Protocol):
    """Branch 1 provides — sends an email and returns a message ID."""

    async def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: str | None = None,
        in_reply_to: str | None = None,
    ) -> str: ...


class MessageFetcher(Protocol):
    """Branch 1 provides — queries messages from the database."""

    async def count_messages_since(
        self,
        tenant_id: UUID,
        hours: int = 24,
    ) -> dict[str, int]: ...


class DocumentIngester(Protocol):
    """Protocol for document ingestion — implemented by sequor.ai.ingestion.DocumentIngesterImpl."""

    async def ingest(
        self,
        tenant_id: UUID,
        account_id: UUID,
        filename: str,
        content: bytes,
        document_type: str,
    ) -> UUID: ...


class DocumentIngesterImpl:
    """Branch 2 implementation — uploads and indexes a document.

    Uses the AI ingestion pipeline for parsing, chunking, embedding, and storage.
    """

    def __init__(self, db_pool: Any = None) -> None:
        from sequor.ai.client import get_ollama_client
        from sequor.ai.ingestion import DocumentIngester as AIDocumentIngester
        from sequor.ai.vector_store import VectorStore

        self._db_pool = db_pool
        self._vector_store = VectorStore(db_pool) if db_pool else None
        self._ingester = AIDocumentIngester(
            vector_store=self._vector_store,
            llm_client=get_ollama_client(),
        )

    async def ingest(
        self,
        tenant_id: UUID,
        account_id: UUID,
        filename: str,
        content: bytes,
        document_type: str,
    ) -> UUID:
        """Ingest a document into the RAG pipeline.

        Args:
            tenant_id: Tenant ID
            account_id: Account ID
            filename: Original filename
            content: File content as bytes
            document_type: One of 'faq', 'roster', 'price_list', 'policy', 'other'

        Returns:
            UUID of the created document record
        """
        if self._vector_store is None:
            raise RuntimeError("DocumentIngester requires a database pool")

        return await self._ingester.ingest(
            tenant_id=tenant_id,
            account_id=account_id,
            filename=filename,
            content=content,
            document_type=document_type,
        )


# Default instance
_default_ingester: DocumentIngesterImpl | None = None


def get_document_ingester(db_pool: Any = None) -> DocumentIngesterImpl:
    """Get or create the default DocumentIngester instance."""
    global _default_ingester
    if _default_ingester is None:
        _default_ingester = DocumentIngesterImpl(db_pool)
    return _default_ingester


class DigestDataSupplier(Protocol):
    """Branches 1 + 2 provide — returns counts for the daily digest."""

    async def get_digest_data(
        self,
        tenant_id: UUID,
        hours: int = 24,
    ) -> dict: ...
