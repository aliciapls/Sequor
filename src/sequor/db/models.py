"""
SQLAlchemy ORM models for Sequor.

All models use UUID primary keys, timestamps, and proper foreign keys.
Pgvector embedding columns are included on DocumentChunk and LearnedAnswer.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    UniqueConstraint,
    Integer,
    String,
    Text,
    Unicode,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sequor.db.base import Base
from sequor.db.encrypted_column import EncryptedString


# ---------------------------------------------------------------------------
# Enum definitions
# ---------------------------------------------------------------------------


class TenantPlan(str, enum.Enum):
    free = "free"
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"


class OwnershipType(str, enum.Enum):
    individual = "individual"
    department = "department"


class AccountChannel(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"


class AccountStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class ContactTier(str, enum.Enum):
    primary = "primary"
    second_tier = "second_tier"


class ChannelPreference(str, enum.Enum):
    whatsapp = "whatsapp"
    email = "email"
    either = "either"


class ConsentChannel(str, enum.Enum):
    whatsapp = "whatsapp"
    email = "email"


class OptInMethod(str, enum.Enum):
    first_contact_notice = "first_contact_notice"
    explicit_checkbox = "explicit_checkbox"
    verbal = "verbal"


class WithdrawalMethod(str, enum.Enum):
    replied_human = "replied_human"
    replied_stop = "replied_stop"
    settings_change = "settings_change"


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageChannel(str, enum.Enum):
    whatsapp = "whatsapp"
    email = "email"


class ClassificationCategory(str, enum.Enum):
    routine = "routine"
    semi_routine = "semi_routine"
    complex = "complex"
    high_stakes = "high_stakes"


class ClassificationUrgency(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DocumentType(str, enum.Enum):
    faq = "faq"
    roster = "roster"
    price_list = "price_list"
    policy = "policy"
    other = "other"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    indexing = "indexing"
    ready = "ready"
    stale = "stale"
    error = "error"


class SourceType(str, enum.Enum):
    human_answer = "human_answer"
    document = "document"


class ConfidenceBadge(str, enum.Enum):
    high = "high"
    moderate = "moderate"
    low = "low"
    # Matches the DB enum (migration 5ab03308b1f3) and the value produced by the
    # RAG/response path (ai/response.py, ai/rag_pipeline.py). Omitting it raised
    # ValueError when persisting an uncertain / low-answerability response.
    uncertain = "uncertain"


class KeyPhraseMappingType(str, enum.Enum):
    auto_reply = "auto_reply"
    include_context = "include_context"
    escalate = "escalate"
    uncertain = "uncertain"


class EscalationStatus(str, enum.Enum):
    pending = "pending"
    acknowledged = "acknowledged"
    resolved = "resolved"
    expired = "expired"
    notification_pending = "notification_pending"


class EscalationPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DoerType(str, enum.Enum):
    ai_agent = "ai_agent"
    backup_contact = "backup_contact"
    user = "user"
    system = "system"


class RecipientType(str, enum.Enum):
    contact = "contact"
    backup_contact = "backup_contact"
    user = "user"
    system = "system"


class RoutingTarget(str, enum.Enum):
    backup_contact = "backup_contact"
    escalation_queue = "escalation_queue"
    auto_respond = "auto_respond"
    primary_user = "primary_user"


# ---------------------------------------------------------------------------
# Helper for default UUID / timestamp
# ---------------------------------------------------------------------------


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    plan: Mapped[TenantPlan] = mapped_column(
        Enum(TenantPlan, name="tenant_plan", create_constraint=True),
        nullable=False,
        default=TenantPlan.free,
    )
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    schema_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pdpa_consent_recorded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    accounts = relationship("Account", back_populates="tenant", lazy="selectin")
    backup_contacts = relationship("BackupContact", back_populates="tenant", lazy="selectin")
    contacts = relationship("Contact", back_populates="tenant", lazy="selectin")

    __table_args__ = (Index("ix_tenants_email_domain", "email_domain"),)

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} name={self.name!r} plan={self.plan.value}>"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ownership_type: Mapped[OwnershipType] = mapped_column(
        Enum(OwnershipType, name="ownership_type", create_constraint=True), nullable=False
    )
    owner_email: Mapped[str] = mapped_column(
        EncryptedString(field_name="owner_email"), nullable=False
    )
    channels: Mapped[list] = mapped_column(
        ARRAY(String(20)), nullable=False, default=lambda: [AccountChannel.email.value]
    )
    email_address: Mapped[Optional[str]] = mapped_column(
        EncryptedString(field_name="email_address"), nullable=True
    )
    whatsapp_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    backup_contact_ids: Mapped[Optional[list]] = mapped_column(ARRAY(Uuid), nullable=True)
    routing_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.90)
    escalation_sla_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status", create_constraint=True),
        nullable=False,
        default=AccountStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="accounts")

    __table_args__ = (
        Index("ix_accounts_tenant_id", "tenant_id"),
        Index("ix_accounts_owner_email", "owner_email"),
        Index("ix_accounts_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Account id={self.id} name={self.name!r} status={self.status.value}>"


class BackupContact(Base):
    __tablename__ = "backup_contacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(EncryptedString(field_name="backup_email"), nullable=False)
    # Blind index for login lookups — HMAC of email with global lookup key
    email_blind_index: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(
        EncryptedString(field_name="backup_phone"), nullable=True
    )
    tier: Mapped[ContactTier] = mapped_column(
        Enum(ContactTier, name="contact_tier", create_constraint=True), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="backup_contacts")

    __table_args__ = (
        Index("ix_backup_contacts_tenant_id", "tenant_id"),
        Index("ix_backup_contacts_account_id", "account_id"),
        Index("ix_backup_contacts_tier", "tier"),
        Index("ix_backup_contacts_email_blind_index", "email_blind_index"),
    )

    def __repr__(self) -> str:
        return f"<BackupContact id={self.id} name={self.name!r} tier={self.tier.value}>"


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(
        EncryptedString(field_name="contact_email"), nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        EncryptedString(field_name="contact_phone"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String(100)), nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    channel_preference: Mapped[ChannelPreference] = mapped_column(
        Enum(ChannelPreference, name="channel_preference", create_constraint=True),
        nullable=False,
        default=ChannelPreference.email,
    )
    human_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="contacts")

    __table_args__ = (
        Index("ix_contacts_tenant_id", "tenant_id"),
        Index("ix_contacts_email", "email"),
        Index("ix_contacts_phone", "phone"),
    )

    def __repr__(self) -> str:
        return f"<Contact id={self.id} name={self.name!r}>"


class ChannelConsent(Base):
    __tablename__ = "channel_consents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[ConsentChannel] = mapped_column(
        Enum(ConsentChannel, name="consent_channel", create_constraint=True), nullable=False
    )
    opt_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    opt_in_method: Mapped[OptInMethod] = mapped_column(
        Enum(OptInMethod, name="opt_in_method", create_constraint=True), nullable=False
    )
    opt_in_notice_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    opt_out_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawal_method: Mapped[Optional[WithdrawalMethod]] = mapped_column(
        Enum(WithdrawalMethod, name="withdrawal_method", create_constraint=True), nullable=True
    )

    __table_args__ = (
        Index("ix_channel_consents_tenant_id", "tenant_id"),
        Index("ix_channel_consents_contact_id", "contact_id"),
        Index("ix_channel_consents_contact_channel", "contact_id", "channel"),
    )

    def __repr__(self) -> str:
        return f"<ChannelConsent id={self.id} contact_id={self.contact_id} channel={self.channel.value}>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection, name="message_direction", create_constraint=True), nullable=False
    )
    channel: Mapped[MessageChannel] = mapped_column(
        Enum(MessageChannel, name="message_channel", create_constraint=True), nullable=False
    )
    external_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    in_reply_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    whatsapp_session_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_messages_tenant_id", "tenant_id"),
        Index("ix_messages_contact_id", "contact_id"),
        Index("ix_messages_received_at", "received_at"),
        Index("ix_messages_external_message_id", "external_message_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} direction={self.direction.value} channel={self.channel.value}>"
        )


class Classification(Base):
    __tablename__ = "classifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    classifier: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[ClassificationCategory] = mapped_column(
        Enum(ClassificationCategory, name="classification_category", create_constraint=True),
        nullable=False,
    )
    urgency: Mapped[ClassificationUrgency] = mapped_column(
        Enum(ClassificationUrgency, name="classification_urgency", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    __table_args__ = (
        Index("ix_classifications_tenant_id", "tenant_id"),
        Index("ix_classifications_message_id", "message_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Classification id={self.id} category={self.category.value}"
            f" confidence={self.confidence:.2f}>"
        )


class RAGRetrieval(Base):
    __tablename__ = "rag_retrievals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    document_ids: Mapped[Optional[list]] = mapped_column(ARRAY(Uuid), nullable=True)
    passages: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    retrieval_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    synthesis_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    __table_args__ = (
        Index("ix_rag_retrievals_tenant_id", "tenant_id"),
        Index("ix_rag_retrievals_message_id", "message_id"),
    )

    def __repr__(self) -> str:
        return f"<RAGRetrieval id={self.id} retrieved_at={self.retrieved_at}>"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", create_constraint=True), nullable=False
    )
    file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", create_constraint=True),
        nullable=False,
        default=DocumentStatus.pending,
    )

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", lazy="selectin")

    __table_args__ = (
        Index("ix_documents_tenant_id", "tenant_id"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_tenant_type", "tenant_id", "type"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} name={self.name!r} status={self.status.value}>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_tenant_id", "tenant_id"),
        Index("ix_document_chunks_document_id", "document_id"),
        UniqueConstraint(
            "tenant_id", "document_id", "chunk_index", name="uq_document_chunks_tenant_doc_idx"
        ),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} doc={self.document_id} idx={self.chunk_index}>"


class LearnedAnswer(Base):
    __tablename__ = "learned_answers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type", create_constraint=True), nullable=False
    )
    source_escalation_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    embedding = mapped_column(Vector(768), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    __table_args__ = (
        Index("ix_learned_answers_tenant_id", "tenant_id"),
        Index("ix_learned_answers_account_id", "account_id"),
    )

    def __repr__(self) -> str:
        return f"<LearnedAnswer id={self.id} source={self.source_type.value}>"


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    rag_retrieval_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("rag_retrievals.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_badge: Mapped[ConfidenceBadge] = mapped_column(
        Enum(ConfidenceBadge, name="confidence_badge", create_constraint=True), nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    was_auto_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_backup_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    backup_approver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("backup_contacts.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        Index("ix_responses_tenant_id", "tenant_id"),
        Index("ix_responses_message_id", "message_id"),
    )

    def __repr__(self) -> str:
        return f"<Response id={self.id} badge={self.confidence_badge.value}>"


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    response_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("responses.id", ondelete="SET NULL"), nullable=True
    )
    backup_contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("backup_contacts.id", ondelete="CASCADE"), nullable=False
    )
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus, name="escalation_status", create_constraint=True),
        nullable=False,
        default=EscalationStatus.pending,
    )
    priority: Mapped[EscalationPriority] = mapped_column(
        Enum(EscalationPriority, name="escalation_priority", create_constraint=True),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_escalations_tenant_id", "tenant_id"),
        Index("ix_escalations_message_id", "message_id"),
        Index("ix_escalations_backup_contact_id", "backup_contact_id"),
        Index("ix_escalations_status", "status"),
        Index("ix_escalations_assigned_at", "assigned_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Escalation id={self.id} status={self.status.value} priority={self.priority.value}>"
        )


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    doer_type: Mapped[DoerType] = mapped_column(
        Enum(DoerType, name="doer_type", create_constraint=True), nullable=False
    )
    doer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_type: Mapped[RecipientType] = mapped_column(
        Enum(RecipientType, name="recipient_type", create_constraint=True), nullable=False
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    __table_args__ = (
        Index("ix_audit_entries_tenant_id", "tenant_id"),
        Index("ix_audit_entries_doer", "doer_type", "doer_id"),
        Index("ix_audit_entries_recipient", "recipient_type", "recipient_id"),
        Index("ix_audit_entries_occurred_at", "occurred_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditEntry id={self.id} action={self.action_type!r}>"


class RoutingOutcome(Base):
    __tablename__ = "routing_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    classification_category: Mapped[str] = mapped_column(String(50), nullable=False)
    classification_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    routing_target: Mapped[RoutingTarget] = mapped_column(
        Enum(RoutingTarget, name="routing_target", create_constraint=True), nullable=False
    )
    backup_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("backup_contacts.id", ondelete="SET NULL"), nullable=True
    )
    escalation_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalation_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolution_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    auto_response_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_response_rejected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_routing_outcomes_tenant_id", "tenant_id"),
        Index("ix_routing_outcomes_message_id", "message_id"),
        Index("ix_routing_outcomes_routing_target", "routing_target"),
    )

    def __repr__(self) -> str:
        return f"<RoutingOutcome id={self.id} target={self.routing_target.value}>"


class KeyPhraseMapping(Base):
    __tablename__ = "key_phrase_mappings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    phrase: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    mapping_type: Mapped[KeyPhraseMappingType] = mapped_column(
        Enum(KeyPhraseMappingType, name="key_phrase_mapping_type", create_constraint=True),
        nullable=False,
        default=KeyPhraseMappingType.auto_reply,
    )
    confidence_boost: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_key_phrase_mappings_tenant_id", "tenant_id"),
        Index("ix_key_phrase_mappings_document_id", "document_id"),
        Index("ix_key_phrase_mappings_phrase", "phrase"),
        UniqueConstraint(
            "tenant_id", "phrase", "document_id", name="uq_key_phrase_mapping_tenant_phrase_doc"
        ),
    )

    def __repr__(self) -> str:
        return f"<KeyPhraseMapping id={self.id} phrase={self.phrase!r}>"
