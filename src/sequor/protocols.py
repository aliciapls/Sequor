from __future__ import annotations

"""Protocol interfaces for cross-branch dependencies.

Branch 3 (onboarding, operations) depends on features from Branch 1 (email)
and Branch 2 (AI/RAG). These Protocol classes define the interfaces Branch 3
needs so it can develop and test independently.

At merge time, swap in the real implementations from the other branches.
"""

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
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
    """Branch 2 provides — uploads and indexes a document."""

    async def ingest(
        self,
        tenant_id: UUID,
        account_id: UUID,
        filename: str,
        content: bytes,
        document_type: str,
    ) -> UUID: ...


class DigestDataSupplier(Protocol):
    """Branches 1 + 2 provide — returns counts for the daily digest."""

    async def get_digest_data(
        self,
        tenant_id: UUID,
        hours: int = 24,
    ) -> dict: ...
