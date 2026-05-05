"""Shared email utilities to avoid DRY violations across modules."""


def mask_email(email: str) -> str:
    """Mask an email address for safe logging.

    Preserves first character of local part and the full domain.
    Short local parts (<=2 chars) are fully masked.
    """
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[0]}***@{domain}"
