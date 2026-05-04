"""Inbound email parsing for SendGrid Inbound Parse webhook payloads.

Extracts headers, plain text body, HTML body, and attachments from
raw email data. Returns a structured InboundEmail for downstream
processing (Message record creation, thread linking).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser, Parser
from email.utils import parseaddr
from typing import Any

import structlog

logger = structlog.get_logger()


def _sanitize_filename(name: str) -> str:
    """Strip path components and dangerous characters from attachment filenames."""
    safe = os.path.basename(name)
    safe = safe.replace("\x00", "").replace("\r", "").replace("\n", "")
    if ".." in safe or not safe:
        return "unnamed"
    return safe


def _sanitize_header_value(value: str | None) -> str | None:
    """Strip null bytes and control characters from parsed header values."""
    if value is None:
        return None
    return value.replace("\x00", "").replace("\r", "").replace("\n", "")


@dataclass
class InboundAttachment:
    filename: str
    content_type: str
    content: bytes


@dataclass
class InboundEmail:
    from_email: str
    from_name: str
    to_email: str
    subject: str
    message_id: str
    in_reply_to: str | None
    references: str | None
    body_text: str
    body_html: str | None
    attachments: list[InboundAttachment] = field(default_factory=list)

    @property
    def is_reply(self) -> bool:
        return bool(self.in_reply_to or self.references)

    @property
    def escalation_id(self) -> str | None:
        """Extract escalation_id from In-Reply-To or References header.

        SendGrid embeds the escalation_id via X-Sequor-Escalation-Id
        header, which shows up in References on replies.
        """
        for header_val in [self.in_reply_to, self.references]:
            if not header_val:
                continue
            match = re.search(r"<escalation-([a-f0-9-]+)@", header_val)
            if match:
                return match.group(1)
        return None


def parse_sendgrid_payload(payload: dict[str, Any]) -> InboundEmail:
    """Parse a SendGrid Inbound Parse webhook payload into an InboundEmail.

    SendGrid POSTs form-encoded fields: headers, text, html, attachments, etc.
    The 'headers' field is a JSON string with the raw email headers.
    """
    headers_raw = payload.get("headers", "")
    from_email, from_name = _parse_from(payload, headers_raw)

    body_text = payload.get("text", "")
    body_html = payload.get("html", "") or None

    to_email = payload.get("to", "")
    _, to_addr = parseaddr(to_email)
    if not to_addr:
        to_email_parsed = _extract_header(headers_raw, "To")
        _, to_addr = parseaddr(to_email_parsed or "")
    if not to_addr:
        to_addr = to_email

    subject = payload.get("subject", "") or _extract_header(headers_raw, "Subject") or ""

    message_id = _sanitize_header_value(_extract_header(headers_raw, "Message-Id") or _extract_header(headers_raw, "Message-ID")) or ""
    in_reply_to = _sanitize_header_value(_extract_header(headers_raw, "In-Reply-To"))
    references = _sanitize_header_value(_extract_header(headers_raw, "References"))

    attachments = _extract_attachments(payload)

    return InboundEmail(
        from_email=from_email,
        from_name=from_name,
        to_email=to_addr,
        subject=subject,
        message_id=message_id,
        in_reply_to=in_reply_to,
        references=references,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
    )


def parse_raw_email(raw_bytes: bytes) -> InboundEmail:
    """Parse a raw RFC 822 email message.

    Used when the webhook delivers the full raw email instead of
    parsed fields.
    """
    parser = BytesParser(policy=policy.default)
    msg = parser.parsebytes(raw_bytes)

    from_header = msg.get("From", "")
    from_name, from_email = parseaddr(from_header)

    to_header = msg.get("To", "")
    _, to_email = parseaddr(to_header)

    body_text, body_html = _extract_bodies(msg)

    attachments: list[InboundAttachment] = []
    for part in msg.walk():
        cd = part.get("Content-Disposition", "")
        if "attachment" in cd:
            fname = _sanitize_filename(part.get_filename() or "unnamed")
            content = part.get_payload(decode=True) or b""
            attachments.append(InboundAttachment(
                filename=fname,
                content_type=part.get_content_type(),
                content=content,
            ))

    return InboundEmail(
        from_email=from_email,
        from_name=from_name,
        to_email=to_email,
        subject=msg.get("Subject", ""),
        message_id=_sanitize_header_value(msg.get("Message-ID", "")) or "",
        in_reply_to=_sanitize_header_value(msg.get("In-Reply-To")),
        references=_sanitize_header_value(msg.get("References")),
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
    )


def strip_quoted_reply(text: str) -> str:
    """Strip quoted text from a reply, keeping only the new content.

    Handles common patterns:
    - On ... wrote: (Gmail, Outlook)
    - -----Original Message----- (Outlook)
    - > quoted lines
    - -- signature separator
    """
    if not text:
        return text

    patterns = [
        r"\nOn .+ wrote:\n",
        r"\n----*Original Message----*",
        r"\nFrom: .+\n.*\nTo: .+",
        r"\n\*_+\n",
        r"\n>.*",
    ]

    result = text
    for pattern in patterns:
        match = re.search(pattern, result, re.DOTALL)
        if match:
            result = result[:match.start()]

    result = re.sub(r"\n--\s+.*", "", result.strip(), flags=re.DOTALL)
    return result.strip()


def _parse_from(payload: dict[str, Any], headers_raw: str) -> tuple[str, str]:
    from_field = payload.get("from", "")
    name, email = parseaddr(from_field)
    if not email:
        from_header = _extract_header(headers_raw, "From")
        if from_header:
            name, email = parseaddr(from_header)
    return email, name


def _extract_header(headers_raw: str, name: str) -> str | None:
    if not headers_raw:
        return None
    for line in headers_raw.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            if key.strip().lower() == name.lower():
                return value.strip()
    return None


def _extract_bodies(msg: EmailMessage) -> tuple[str, str | None]:
    text_body = ""
    html_body = None

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if ct == "text/plain" and not text_body:
                payload = part.get_payload(decode=True)
                if payload:
                    text_body = payload.decode("utf-8", errors="replace")
            elif ct == "text/html" and html_body is None:
                payload = part.get_payload(decode=True)
                if payload:
                    html_body = payload.decode("utf-8", errors="replace")
    else:
        ct = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            decoded = payload.decode("utf-8", errors="replace")
            if ct == "text/html":
                html_body = decoded
                text_body = _html_to_text(decoded)
            else:
                text_body = decoded

    return text_body, html_body


def _html_to_text(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    return text.strip()


def _extract_attachments(payload: dict[str, Any]) -> list[InboundAttachment]:
    attachments: list[InboundAttachment] = []
    i = 1
    while True:
        filename = payload.get(f"attachment{i}")
        if filename is None:
            break
        safe_name = _sanitize_filename(filename if isinstance(filename, str) else "unnamed")
        content_type = payload.get(f"attachment{i}_type", "application/octet-stream")
        content_str = payload.get(f"attachment{i}", "")
        content = content_str.encode("utf-8") if isinstance(content_str, str) else content_str
        attachments.append(InboundAttachment(
            filename=safe_name,
            content_type=content_type,
            content=content,
        ))
        i += 1
    return attachments
