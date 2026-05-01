"""Thread key derivation for escalation deduplication.

The thread key is a stable SHA256 hash of the contact identity + topic.
Two messages from the same contact about the same topic within 72 hours
belong to the same escalation thread.
"""

import hashlib
import re

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

_STOP_WORDS = frozenset([
    "a", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "has", "he", "in", "is", "it", "its", "of", "on",
    "that", "the", "to", "was", "were", "will", "with",
    "i", "me", "my", "we", "our", "you", "your",
    "please", "can", "could", "would", "should",
    "this", "what", "when", "where", "which", "who", "how",
    "do", "does", "did", "have", "had", "hi", "hello",
    "tell",
])

_SIGNIFICANT_WORD_RE = re.compile(r"^[a-zA-Z]+$")


def normalize_email(email: str) -> str:
    """Normalize an email address: lowercase, stripped."""
    return email.strip().lower()


def normalize_phone(phone: str) -> str:
    """Normalize a phone number: digits only."""
    return "".join(c for c in phone if c.isdigit())


def _is_meaningful(word: str) -> bool:
    return (
        len(word) >= 3
        and word.lower() not in _STOP_WORDS
        and bool(_SIGNIFICANT_WORD_RE.match(word))
    )


def extract_topic(message_body: str, max_words: int = 5) -> str:
    """Extract the first N significant words from a message body.

    - Lowercases the text
    - Splits on whitespace and punctuation
    - Removes stop words and very short tokens
    - Returns up to max_words, joined by spaces
    """
    words = message_body.lower().split()
    significant = [w.strip(".,!?;:\"'()[]{}") for w in words if _is_meaningful(w)]
    return " ".join(significant[:max_words])


def derive_thread_key(
    contact_email: str | None,
    contact_phone: str | None,
    message_body: str,
) -> str:
    """Derive a stable SHA256 thread key from contact identity + topic.

    The key is deterministic: same contact + same topic = same key.
    This enables deduplication across channels and time.

    Logic:
      identity = normalize_email(contact_email)
                 OR normalize_phone(contact_phone)
                 OR "unknown" if both are absent
      topic    = extract_topic(message_body)  # first 5 significant words
      key      = SHA256(identity + "|" + topic)

    Args:
        contact_email: the contact's email address (nullable)
        contact_phone: the contact's phone number (nullable)
        message_body: the message content to extract topic from

    Returns:
        SHA256 hex digest (64 characters)
    """
    if contact_email:
        identity = normalize_email(contact_email)
    elif contact_phone:
        identity = normalize_phone(contact_phone)
    else:
        identity = "unknown"

    topic = extract_topic(message_body)
    raw = f"{identity}|{topic}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
