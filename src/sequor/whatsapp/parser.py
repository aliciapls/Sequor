"""Parse Meta Cloud API webhook payloads into structured data."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InboundWhatsApp:
    """A single inbound WhatsApp message extracted from a Meta webhook payload."""

    from_phone: str
    to_phone: str
    message_id: str
    body_text: str
    message_type: str
    timestamp: str
    contact_name: str | None = None
    media_id: str | None = None
    media_mime_type: str | None = None
    interactive_payload: dict | None = None


def parse_meta_webhook_payload(payload: dict) -> list[InboundWhatsApp]:
    """Extract inbound WhatsApp messages from a Meta Cloud API webhook payload.

    Meta sends a nested structure:
        entry[].changes[].value.messages[]

    Status updates (delivered, read) and system events are silently skipped.
    Returns an empty list if no actionable messages are found.
    """
    messages: list[InboundWhatsApp] = []

    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})

            # Skip status updates (delivered, read, etc.)
            if "statuses" in value and "messages" not in value:
                continue

            # Extract business phone number for account resolution
            metadata = value.get("metadata", {})
            to_phone = metadata.get("display_phone_number", "")

            # Build contact name lookup from the contacts array
            contact_names: dict[str, str] = {}
            for contact in value.get("contacts", []):
                wa_id = contact.get("wa_id", "")
                name_obj = contact.get("profile", {})
                if wa_id and name_obj:
                    contact_names[wa_id] = name_obj.get("name", "")

            for msg in value.get("messages", []):
                parsed = _parse_single_message(msg, to_phone, contact_names)
                if parsed:
                    messages.append(parsed)

    return messages


def _parse_single_message(
    msg: dict,
    to_phone: str,
    contact_names: dict[str, str],
) -> InboundWhatsApp | None:
    """Parse a single message object from the Meta payload."""
    msg_type = msg.get("type", "")
    from_phone = msg.get("from", "")
    message_id = msg.get("id", "")
    timestamp = msg.get("timestamp", "")

    if not from_phone or not message_id:
        return None

    body_text = ""
    media_id = None
    media_mime_type = None
    interactive_payload = None

    if msg_type == "text":
        text_obj = msg.get("text", {})
        body_text = text_obj.get("body", "")

    elif msg_type == "interactive":
        interactive = msg.get("interactive", {})
        interactive_payload = interactive
        itype = interactive.get("type", "")
        if itype == "button_reply":
            body_text = interactive.get("button_reply", {}).get("title", "")
        elif itype == "list_reply":
            body_text = interactive.get("list_reply", {}).get("title", "")
        else:
            body_text = str(interactive)

    elif msg_type in ("image", "document", "audio", "video", "sticker"):
        media_obj = msg.get(msg_type, {})
        media_id = media_obj.get("id")
        media_mime_type = media_obj.get("mime_type")
        body_text = media_obj.get("caption", "") or f"[{msg_type}]"

    elif msg_type == "location":
        loc = msg.get("location", {})
        body_text = f"[location] {loc.get('latitude')}, {loc.get('longitude')}"

    elif msg_type == "contacts":
        body_text = "[contacts]"

    elif msg_type == "reaction":
        emoji = msg.get("reaction", {}).get("emoji", "")
        body_text = f"[reaction: {emoji}]"

    else:
        body_text = f"[{msg_type}]"

    contact_name = contact_names.get(from_phone)

    return InboundWhatsApp(
        from_phone=from_phone,
        to_phone=to_phone,
        message_id=message_id,
        body_text=body_text,
        message_type=msg_type,
        timestamp=timestamp,
        contact_name=contact_name,
        media_id=media_id,
        media_mime_type=media_mime_type,
        interactive_payload=interactive_payload,
    )
