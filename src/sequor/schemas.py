"""Pydantic validation models for all user-facing inputs.

Every API endpoint and form submission accepts a Pydantic model, not raw dicts.
Invalid input is rejected before any database write.
"""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

# Pattern to detect HTML tags in string inputs
_HTML_RE = re.compile(r"<[^>]+>")


def _reject_html(v: str) -> str:
    if _HTML_RE.search(v):
        raise ValueError("HTML is not allowed in this field")
    return v.strip()


class OnboardingRequest(BaseModel):
    """Signup form — creates Tenant, Account, and BackupContact."""

    org_name: str = Field(min_length=1, max_length=255)
    owner_email: EmailStr
    owner_password: str = Field(min_length=8, max_length=72)
    account_name: str = Field(min_length=1, max_length=255)
    ownership_type: str = Field(pattern=r"^(individual|department)$")
    backup_name: str = Field(min_length=1, max_length=255)
    backup_email: EmailStr
    escalation_sla_hours: int = Field(ge=1, le=72, default=4)
    routing_rule: str = Field(pattern=r"^(all_to_backup|faq_only|full_ai)$", default="full_ai")

    @field_validator("org_name", "account_name", "backup_name")
    @classmethod
    def no_html(cls, v: str) -> str:
        return _reject_html(v)

    @field_validator("owner_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class DocumentUploadRequest(BaseModel):
    """Document upload during onboarding."""

    document_type: str = Field(pattern=r"^(faq|roster|price_list|policy|other)$")
    filename: str = Field(min_length=1, max_length=255)

    @field_validator("filename")
    @classmethod
    def safe_filename(cls, v: str) -> str:
        # Reject path traversal
        if "/" in v or "\\" in v or ".." in v:
            raise ValueError("Invalid filename")
        return _reject_html(v)


class EmailChannelSetupRequest(BaseModel):
    """Email channel configuration during onboarding."""

    email_address: EmailStr
    display_name: str = Field(min_length=1, max_length=255)

    @field_validator("display_name")
    @classmethod
    def no_html(cls, v: str) -> str:
        return _reject_html(v)


class StripeWebhookEvent(BaseModel):
    """Inbound Stripe webhook event — validates structure before processing."""

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    data: dict


class ContactErasureRequest(BaseModel):
    """Request to delete all PII for a contact (PDPA right to erasure)."""

    contact_id: str = Field(min_length=1)
    confirmed: bool = Field(strict=True)

    @field_validator("confirmed")
    @classmethod
    def must_confirm(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Erasure requires explicit confirmation (confirmed=True)")
        return v
