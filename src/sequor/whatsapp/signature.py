"""Meta Cloud API webhook signature verification."""

import hashlib
import hmac


def verify_meta_signature(
    app_secret: str,
    raw_body: bytes,
    signature_header: str,
) -> bool:
    """Verify the X-Hub-Signature-256 header from Meta webhook.

    Meta signs the raw request body with HMAC-SHA256 using the app secret.
    The header format is ``sha256=<hex_digest>``.

    Returns False if the signature is missing, malformed, or does not match.
    """
    if not app_secret or not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    received = signature_header[len("sha256="):]

    return hmac.compare_digest(expected, received)
