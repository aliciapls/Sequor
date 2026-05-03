"""Email module for Sequor.

Exports:
- EmailSenderImpl: SendGrid-based email sender
- EmailSender: Protocol for email sending
- AutoReplyService: Full auto-reply orchestration pipeline
- MessageContext: Context for message processing
- AutoReplyResult: Result of auto-reply processing
"""

from sequor.email.auto_reply import (
    AutoReplyResult,
    AutoReplyService,
    MessageContext,
    get_auto_reply_service,
)
from sequor.email.sender import (
    EmailSenderImpl,
    get_email_sender,
)

__all__ = [
    "EmailSenderImpl",
    "get_email_sender",
    "AutoReplyService",
    "get_auto_reply_service",
    "MessageContext",
    "AutoReplyResult",
]
