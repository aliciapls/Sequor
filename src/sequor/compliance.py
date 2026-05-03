"""PDPA compliance constants and helpers.

Single source of truth for consent notice text, HUMAN keyword detection,
and erasure verification. All compliance-facing code imports from here.
"""

# The consent notice included in every first auto-reply to a contact.
# Must be a complete sentence explaining AI processing and the opt-out mechanism.
CONSENT_NOTICE = (
    "This inbox is managed by {org_name}'s AI assistant. "
    "Your message is processed to route and respond to your inquiry. "
    "Reply HUMAN to speak with a person."
)

# Keywords that trigger immediate opt-out (case-insensitive, exact or starts-with)
OPT_OUT_KEYWORDS = {"HUMAN", "STOP"}


def is_opt_out(message_body: str) -> bool:
    """Check if a message body contains an opt-out keyword.

    Matches HUMAN or STOP as the entire message, or as the first word.
    Case-insensitive.
    """
    stripped = message_body.strip().upper()
    if not stripped:
        return False
    first_word = stripped.split()[0]
    return first_word in OPT_OUT_KEYWORDS


def build_consent_notice(org_name: str) -> str:
    """Format the consent notice with the organization's name."""
    return CONSENT_NOTICE.format(org_name=org_name)


# Fields on the Contact model that constitute PII and must be erased.
PII_FIELDS = {"email", "phone", "name", "company"}

# Fields to scrub (set to None) on erasure.
ERASURE_NULL_FIELDS = {
    "email": None,
    "phone": None,
    "name": "[erased]",
    "company": None,
    "tags": None,
}
