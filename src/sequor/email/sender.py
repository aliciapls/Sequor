"""Email sender implementation using SendGrid.

Sends outbound emails and returns a message ID for tracking.
Implements the EmailSender protocol from protocols.py.
"""

import structlog

from sequor.config import settings

logger = structlog.get_logger()


class EmailSenderImpl:
    """SendGrid-based email sender.

    Implements the EmailSender protocol.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the email sender.

        Args:
            api_key: SendGrid API key. Defaults to settings.sendgrid_api_key.
        """
        self._api_key = api_key or settings.sendgrid_api_key
        self._from_email: str | None = None
        self._from_name: str | None = None

    async def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: str | None = None,
        in_reply_to: str | None = None,
    ) -> str:
        """Send an email via SendGrid.

        Args:
            to: Recipient email address
            subject: Email subject line
            body_html: HTML content of the email
            body_text: Plain text content of the email
            reply_to: Optional reply-to address
            in_reply_to: Optional in-reply-to message ID for threading

        Returns:
            SendGrid message ID

        Raises:
            RuntimeError: If SendGrid is not configured or fails
        """
        if not self._api_key:
            logger.warning("email.sendgrid.not_configured")
            raise RuntimeError("SendGrid API key not configured. Set SENDGRID_API_KEY in .env")

        logger.info(
            "email.send.start",
            to=to,
            subject_length=len(subject),
            body_html_length=len(body_html),
        )

        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
        except ImportError:
            logger.error("email.sendgrid.import_failed")
            raise RuntimeError(
                "SendGrid package not installed. Run: pip install sendgrid"
            ) from None

        if not self._from_email:
            domain = settings.email_from_domain
            self._from_email = f"noreply@{domain}"
            self._from_name = "Sequor AI Assistant"

        mail = Mail(
            from_email=self._from_email,
            to_emails=to,
            subject=subject,
            html_content=body_html,
            plain_text_content=body_text,
        )

        mail.reply_to = Mail(address=reply_to) if reply_to else None

        if in_reply_to:
            mail.add_header("In-Reply-To", in_reply_to)
            mail.add_header("References", in_reply_to)

        try:
            sg = sendgrid.SendGridAPIClient(api_key=self._api_key)
            response = sg.send(mail)

            if response.status_code not in (200, 201, 202):
                logger.error(
                    "email.send.failed",
                    status_code=response.status_code,
                    body=response.body,
                )
                raise RuntimeError(f"SendGrid API returned {response.status_code}: {response.body}")

            message_id = response.headers.get("X-Message-Id", "unknown")

            logger.info(
                "email.send.ok",
                to=to,
                message_id=message_id,
                status_code=response.status_code,
            )

            return message_id

        except Exception as e:
            logger.error("email.send.error", to=to, error=str(e))
            raise RuntimeError(f"Failed to send email: {str(e)}") from None

    async def send_auto_reply(
        self,
        to: str,
        original_subject: str,
        response_content: str,
        confidence_badge: str,
        in_reply_to: str | None = None,
    ) -> str:
        """Send an AI-generated auto-reply email.

        Args:
            to: Recipient email address
            original_subject: Subject of the original message
            response_content: AI-generated response text
            confidence_badge: Confidence badge (high/moderate/low/uncertain)
            in_reply_to: Message ID to thread reply to

        Returns:
            SendGrid message ID
        """
        subject = (
            f"Re: {original_subject}"
            if not original_subject.startswith("Re:")
            else original_subject
        )

        badge_emoji = {
            "high": "✓",
            "moderate": "◐",
            "low": "◑",
            "uncertain": "?",
        }.get(confidence_badge, "")

        badge_label = confidence_badge.replace("_", " ").title()
        response_content_html = response_content.replace("\n", "<br>")

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f8f9fa; padding: 15px 20px; border-radius: 8px 8px 0 0; border-bottom: 1px solid #e9ecef; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-high {{ background: #d4edda; color: #155724; }}
        .badge-moderate {{ background: #fff3cd; color: #856404; }}
        .badge-low {{ background: #ffeaa7; color: #6d4c00; }}
        .badge-uncertain {{ background: #f8d7da; color: #721c24; }}
        .content {{ padding: 20px; background: white; }}
        .footer {{ padding: 15px 20px; font-size: 12px; color: #6c757d; background: #f8f9fa; border-radius: 0 0 8px 8px; }}
        .confidence {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #e9ecef; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="badge badge-{confidence_badge}">{badge_emoji} {badge_label} Confidence</span>
        <p style="margin: 10px 0 0 0; font-size: 13px; color: #6c757d;">
            This is an automated AI response. If you need human assistance, please reply with "HUMAN" or contact us directly.
        </p>
    </div>
    <div class="content">
        {response_content_html}
    </div>
    <div class="footer">
        <p style="margin: 0;">
            Powered by Sequor AI · This message was generated using AI assistance.<br>
            If you received this in error or wish to speak with a human, please reply with "HUMAN".
        </p>
    </div>
</body>
</html>
"""

        body_text = f"""{"=" * 60}

This is an automated AI response (Confidence: {badge_label})

{"=" * 60}

{response_content}

{"-" * 60}
If you need human assistance, please reply with "HUMAN" or contact us directly.

This message was generated using AI assistance.
Powered by Sequor AI
"""

        return await self.send_email(
            to=to,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            in_reply_to=in_reply_to,
        )


_email_sender: EmailSenderImpl | None = None


def get_email_sender() -> EmailSenderImpl:
    """Get or create the global email sender instance."""
    global _email_sender
    if _email_sender is None:
        _email_sender = EmailSenderImpl()
    return _email_sender
