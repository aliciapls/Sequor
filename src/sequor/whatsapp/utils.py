"""Shared WhatsApp utilities."""


def mask_phone(phone: str) -> str:
    """Mask a phone number for safe logging.

    Preserves country code prefix and last 3 digits.
    Short numbers (<=5 chars) are fully masked.
    """
    if not phone:
        return "***"
    cleaned = phone.replace("+", "").replace("-", "").replace(" ", "")
    if len(cleaned) <= 5:
        return "***"
    prefix = phone[:3] if phone.startswith("+") else phone[:2]
    suffix = phone[-3:]
    return f"{prefix}***{suffix}"
