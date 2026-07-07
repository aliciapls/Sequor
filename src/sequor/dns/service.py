"""DNS setup service — generates DNS records and verifies domain ownership.

Provides SPF, DKIM, and DMARC record generation for the user's sending
domain, a DNS verification check, and SMTP relay fallback instructions.
"""

import structlog
import dns.resolver

logger = structlog.get_logger()

# Bound every outbound resolution so an attacker-supplied domain that points at
# a slow/blackholed resolver cannot tie up a worker (N2 latency-amplification).
_DNS_TIMEOUT_SECONDS = 5.0


def generate_dns_records(domain: str, selector: str = "sequor") -> list[dict]:
    """Generate SPF, DKIM, and DMARC DNS records for a domain.

    Returns a list of dicts with keys: type, host, value, description.
    """
    return [
        {
            "type": "TXT",
            "host": domain,
            "value": "v=spf1 include:mail.sequor.app ~all",
            "description": "SPF — authorizes Sequor to send email on behalf of your domain",
        },
        {
            "type": "CNAME",
            "host": f"{selector}._domainkey.{domain}",
            "value": f"{selector}.domainkey.mail.sequor.app",
            "description": "DKIM — lets recipients verify emails were sent by Sequor and not tampered with",
        },
        {
            "type": "TXT",
            "host": f"_dmarc.{domain}",
            "value": "v=DMARC1; p=none; rua=mailto:dmarc@sequor.app",
            "description": "DMARC — tells receivers what to do if SPF or DKIM fails (start with 'none' to monitor)",
        },
    ]


def verify_dns_records(domain: str, selector: str = "sequor") -> dict:
    """Check whether the required DNS records are in place.

    Returns a dict with 'verified' (bool), 'records' (list of status dicts),
    and 'errors' (list of strings).
    """
    results = []
    all_ok = True

    # Check SPF
    spf_ok = _check_spf(domain)
    results.append(
        {
            "type": "SPF",
            "host": domain,
            "verified": spf_ok,
        }
    )
    if not spf_ok:
        all_ok = False

    # Check DKIM (CNAME)
    dkim_ok = _check_dkim(domain, selector)
    results.append(
        {
            "type": "DKIM",
            "host": f"{selector}._domainkey.{domain}",
            "verified": dkim_ok,
        }
    )
    if not dkim_ok:
        all_ok = False

    # Check DMARC
    dmarc_ok = _check_dmarc(domain)
    results.append(
        {
            "type": "DMARC",
            "host": f"_dmarc.{domain}",
            "verified": dmarc_ok,
        }
    )
    if not dmarc_ok:
        all_ok = False

    return {
        "verified": all_ok,
        "records": results,
        "errors": [r["type"] for r in results if not r["verified"]],
    }


def _check_spf(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, "TXT", lifetime=_DNS_TIMEOUT_SECONDS)
        for rdata in answers:
            txt = rdata.to_text()
            if "v=spf1" in txt and "sequor" in txt.lower():
                return True
        return False
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False  # record genuinely absent — the expected not-yet-configured case
    except Exception:
        logger.warning("dns.spf_check.error", domain=domain, exc_info=True)
        return False


def _check_dkim(domain: str, selector: str) -> bool:
    try:
        hostname = f"{selector}._domainkey.{domain}"
        answers = dns.resolver.resolve(hostname, "CNAME", lifetime=_DNS_TIMEOUT_SECONDS)
        for rdata in answers:
            target = str(rdata.target).rstrip(".")
            if "sequor" in target.lower():
                return True
        return False
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False  # record genuinely absent — the expected not-yet-configured case
    except Exception:
        logger.warning("dns.dkim_check.error", domain=domain, exc_info=True)
        return False


def _check_dmarc(domain: str) -> bool:
    try:
        hostname = f"_dmarc.{domain}"
        answers = dns.resolver.resolve(hostname, "TXT", lifetime=_DNS_TIMEOUT_SECONDS)
        for rdata in answers:
            txt = rdata.to_text()
            if "v=DMARC1" in txt:
                return True
        return False
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False  # record genuinely absent — the expected not-yet-configured case
    except Exception:
        logger.warning("dns.dmarc_check.error", domain=domain, exc_info=True)
        return False
