"""Sequor email service — SendGrid-backed email sending and templates."""

from sequor.email.rate_limiter import RateLimitExceededError
from sequor.email.sender import SendGridAPIError, SendGridEmailSender
from sequor.email.templates import (
    build_digest_email,
    build_digest_subject,
    build_escalation_email,
    build_escalation_subject,
    build_return_summary_email,
    build_return_summary_subject,
    build_weekly_recap_email,
    build_weekly_recap_subject,
)

__all__ = [
    "RateLimitExceededError",
    "SendGridAPIError",
    "SendGridEmailSender",
    "build_digest_email",
    "build_digest_subject",
    "build_escalation_email",
    "build_escalation_subject",
    "build_return_summary_email",
    "build_return_summary_subject",
    "build_weekly_recap_email",
    "build_weekly_recap_subject",
]
