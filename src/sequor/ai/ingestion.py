"""Document ingestion pipeline.

Orchestrates document upload through:
1. Validation
2. Parsing
3. Chunking
4. Embedding generation
5. Vector storage
6. Database record creation
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

from sequor.ai.chunker import Chunk, get_chunker_for_document_type
from sequor.ai.client import OllamaClient, get_ollama_client
from sequor.ai.document_parser import ParsedDocument, get_parser_for_file
from sequor.ai.vector_store import VectorStore

logger = structlog.get_logger()


@dataclass
class IngestionResult:
    """Result of document ingestion."""

    document_id: UUID
    name: str
    status: str
    chunk_count: int
    pages_total: int
    pages_failed: int
    error_message: str | None = None


class DocumentIngester:
    """Pipeline for ingesting documents into the RAG system.

    Implements the DocumentIngester protocol from protocols.py.
    """

    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

    SUPPORTED_EXTENSIONS = {"pdf", "docx", "xlsx", "xls", "csv", "txt", "png", "jpg", "jpeg"}

    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: OllamaClient | None = None,
        db_model: Any = None,
    ) -> None:
        """Initialize the document ingester.

        Args:
            vector_store: VectorStore for storing embeddings
            llm_client: Ollama client for embeddings
            db_model: DataFlow model registry for Document model
        """
        self._vector_store = vector_store
        self._llm = llm_client or get_ollama_client()
        self._db_model = db_model

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

        Raises:
            ValueError: If validation fails
            RuntimeError: If ingestion fails
        """
        logger.info(
            "ingestion.start",
            tenant_id=str(tenant_id),
            filename=filename,
            size_bytes=len(content),
            document_type=document_type,
        )

        self._validate(tenant_id, filename, content, document_type)

        document_id = await self._process_document(
            tenant_id=tenant_id,
            account_id=account_id,
            filename=filename,
            content=content,
            document_type=document_type,
        )

        logger.info(
            "ingestion.complete",
            document_id=str(document_id),
            filename=filename,
        )

        return document_id

    def _validate(
        self,
        tenant_id: UUID,
        filename: str,
        content: bytes,
        document_type: str,
    ) -> None:
        """Validate document before ingestion.

        Args:
            tenant_id: Tenant ID
            filename: Original filename
            content: File bytes
            document_type: Document type string

        Raises:
            ValueError: If validation fails
        """
        if not filename:
            raise ValueError("Filename is required")

        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: .{ext}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        if len(content) > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(content)} bytes. "
                f"Maximum size is {self.MAX_FILE_SIZE} bytes (25MB)"
            )

        if len(content) == 0:
            raise ValueError("File is empty")

        valid_types = {"faq", "roster", "price_list", "policy", "other"}
        if document_type not in valid_types:
            raise ValueError(
                f"Invalid document type: {document_type}. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

    async def _process_document(
        self,
        tenant_id: UUID,
        account_id: UUID,
        filename: str,
        content: bytes,
        document_type: str,
    ) -> UUID:
        """Process document through the ingestion pipeline.

        State machine: pending -> indexing -> ready

        Args:
            tenant_id: Tenant ID
            account_id: Account ID
            filename: Original filename
            content: File bytes
            document_type: Document type

        Returns:
            UUID of created document
        """
        from sequor.db.models import DocumentStatus

        file_hash = hashlib.sha256(content).hexdigest()

        # Stage 1: Create document with pending status
        if self._db_model:
            document_id = await self._create_document_record(
                tenant_id=tenant_id,
                account_id=account_id,
                filename=filename,
                file_hash=file_hash,
                document_type=document_type,
                chunk_count=0,
                pages_total=0,
                pages_failed=0,
                status=DocumentStatus.pending,
            )
        else:
            from uuid import uuid4

            document_id = uuid4()

        # Stage 2: Parse and update to indexing
        parser = get_parser_for_file(filename)
        parsed: ParsedDocument = await parser.parse(content, filename)

        if not parsed.text:
            logger.warning(
                "ingestion.parse.empty",
                filename=filename,
            )

        await self._update_document_status(
            document_id=document_id,
            status=DocumentStatus.indexing,
        )

        # Stage 3: Chunk and embed
        chunker = get_chunker_for_document_type(document_type)
        raw_chunks: list[Chunk] = chunker.chunk(
            parsed.text,
            metadata={"filename": filename, "document_type": document_type},
        )

        if not raw_chunks:
            logger.warning(
                "ingestion.chunk.empty",
                filename=filename,
            )

        # Try embedding generation — if Ollama is unavailable, store document without embeddings
        embeddings = None
        try:
            texts_to_embed = [chunk.text for chunk in raw_chunks]
            embeddings = await self._llm.generate_embeddings(texts_to_embed)
        except Exception as e:
            logger.warning(
                "ingestion.embedding.failed",
                filename=filename,
                error=str(e),
                chunk_count=len(raw_chunks),
            )
            # Document saved without embeddings — stays in 'indexing' status
            # A background job or next Ollama availability can reprocess it
            if self._db_model:
                await self._update_document_status(
                    document_id=document_id,
                    status=DocumentStatus.indexing,
                )
            return document_id

        chunk_data = [
            (chunk.index, chunk.text, emb)
            for chunk, emb in zip(raw_chunks, embeddings, strict=True)
        ]

        # Stage 4: Store chunks and mark as ready
        await self._vector_store.store_chunks(
            tenant_id=tenant_id,
            document_id=document_id,
            chunks=chunk_data,
        )

        if self._db_model:
            await self._update_document_status(
                document_id=document_id,
                status=DocumentStatus.ready,
            )

        logger.info(
            "ingestion.process.complete",
            document_id=str(document_id),
            filename=filename,
            chunks_created=len(chunk_data),
        )

        return document_id

    async def _create_document_record(
        self,
        tenant_id: UUID,
        account_id: UUID,
        filename: str,
        file_hash: str,
        document_type: str,
        chunk_count: int,
        pages_total: int,
        pages_failed: int,
        status: Any,
    ) -> UUID:
        """Create or update Document record in database.

        Args:
            tenant_id: Tenant ID
            account_id: Account ID
            filename: Original filename
            file_hash: SHA256 hash of file
            document_type: Document type enum
            chunk_count: Number of chunks created
            pages_total: Total pages in document
            pages_failed: Pages that failed to parse
            status: Initial DocumentStatus

        Returns:
            UUID of created/updated document
        """
        from sequor.db.models import DocumentType

        now = datetime.now(timezone.utc)

        doc_type = DocumentType(document_type)

        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession

        from sequor.db.database import get_engine

        async with AsyncSession(get_engine()) as session:
            result = await session.execute(
                text("""
                INSERT INTO documents
                (id, tenant_id, name, type, file_hash, chunk_count, indexed_at, last_indexed_at, status)
                VALUES (gen_random_uuid(), :tenant_id, :name, :type, :file_hash,
                 :chunk_count, :indexed_at, :last_indexed_at, :status)
                RETURNING id
                """),
                {
                    "tenant_id": tenant_id,
                    "name": filename,
                    "type": doc_type.value,
                    "file_hash": file_hash,
                    "chunk_count": chunk_count,
                    "indexed_at": now,
                    "last_indexed_at": now,
                    "status": status.value if hasattr(status, "value") else status,
                },
            )
            row = await result.fetchone()
            if row:
                doc_id = row[0]
            else:
                raise RuntimeError(
                    "INSERT INTO documents with RETURNING id returned no row — "
                    "this should not happen with PostgreSQL"
                )
            await session.commit()

        return doc_id

    async def _update_document_status(
        self,
        document_id: UUID,
        status: Any,
    ) -> None:
        """Update document status in database.

        Args:
            document_id: Document UUID
            status: New DocumentStatus
        """
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession

        from sequor.db.database import get_engine

        now = datetime.now(timezone.utc)
        status_value = status.value if hasattr(status, "value") else status

        async with AsyncSession(get_engine()) as session:
            await session.execute(
                text("""
                UPDATE documents
                SET status = :status, last_indexed_at = :last_indexed_at
                WHERE id = :id
                """),
                {
                    "status": status_value,
                    "last_indexed_at": now,
                    "id": document_id,
                },
            )
            await session.commit()
