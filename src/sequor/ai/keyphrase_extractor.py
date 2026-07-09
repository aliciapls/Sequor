"""Per-document key-phrase extraction + auto-mapping creation.

Used by the portal upload handler to suggest key phrases from a document's
own text the moment it is uploaded, so the user no longer has to hand-add
them via the "Add one" link.

Best-effort by design: every public entry point returns an empty list on
any failure (LLM down, unparseable response, DB error) and never raises.
Uploads MUST NOT be blocked by key-phrase suggestion failures.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

_logger = structlog.get_logger()

# Tunables — kept conservative to bound cost and context.
_MAX_PHRASES = 8
_MAX_CONTEXT_CHARS = 4000
_MAX_PHRASE_LEN = 120  # guard against LLM dumping a sentence as a "phrase"

_SYSTEM_PROMPT = (
    "You identify the short phrases a customer might write in a message that a "
    "given business document would answer. Each phrase is 2-5 words, in the "
    'natural wording a customer would type. Return ONLY JSON: {"phrases": ["...", "..."]} '
    "— no prose, no markdown fences."
)


async def extract_key_phrases(text: str, llm_client: Any) -> list[str]:
    """Extract up to 8 customer-style key phrases from document text via the LLM.

    Pure function (LLM only; no DB). Returns [] on any failure — never raises.
    """
    text = (text or "").strip()
    if not text:
        return []
    try:
        prompt = (
            "From the document below, extract 5-8 short phrases (2-5 words each) "
            "that a customer might write in a message which this document answers. "
            "Prefer concrete, specific terms (product names, policies, actions) over "
            "generic ones.\n\n"
            f"DOCUMENT:\n{text[:_MAX_CONTEXT_CHARS]}\n\n"
            'Return ONLY JSON: {"phrases": ["...", ...]}'
        )
        raw = await llm_client.generate(
            prompt=prompt, system=_SYSTEM_PROMPT, temperature=0.3, max_tokens=400
        )
        return _dedupe_and_cap(_parse_phrases(raw))
    except Exception as e:  # LLM down / timeout — pre-acknowledged best-effort
        # fallback (zero-tolerance Rule 3 carve-out): log + return [] so the
        # upload proceeds without suggestions rather than failing.
        _logger.warning("keyphrase.extract_failed", error=str(e))
        return []


async def create_suggested_mappings(
    *,
    session: Any,
    tenant_id: str,
    document_id: Any,
    phrases: list[str],
) -> list[str]:
    """Create ``KeyPhraseMapping`` rows for ``phrases`` (deduped).

    ``session`` must already have the tenant context bound for RLS. Returns the
    list of phrases actually created. Skips phrases already mapped for this
    tenant+document; the unique constraint is the race backstop. Never raises.
    """
    if not phrases:
        return []
    try:
        from sequor.db.models import KeyPhraseMapping, KeyPhraseMappingType
        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        existing = await session.execute(
            select(KeyPhraseMapping.phrase).where(
                KeyPhraseMapping.tenant_id == tenant_id,
                KeyPhraseMapping.document_id == str(document_id),
            )
        )
        existing_lower = {p.lower() for p in existing.scalars().all()}

        created: list[str] = []
        for phrase in phrases:
            if phrase.lower() in existing_lower:
                continue
            # SAVEPOINT per row so a duplicate (race) only rolls back that row,
            # not the mappings already added earlier in this loop.
            try:
                async with session.begin_nested():
                    session.add(
                        KeyPhraseMapping(
                            tenant_id=tenant_id,
                            phrase=phrase,
                            aliases="",
                            document_id=str(document_id),
                            mapping_type=KeyPhraseMappingType.auto_reply,
                            confidence_boost=1.0,
                        )
                    )
            except IntegrityError:  # expected: duplicate under (tenant, phrase, doc)
                _logger.debug("keyphrase.duplicate_skipped", phrase=phrase)
                continue
            existing_lower.add(phrase.lower())
            created.append(phrase)
        await session.commit()
        return created
    except Exception as e:  # pre-acknowledged best-effort fallback (Rule 3 carve-out)
        _logger.warning("keyphrase.create_mappings_failed", error=str(e))
        try:
            await session.rollback()
        except Exception:
            pass
        return []


def _dedupe_and_cap(phrases: list[str]) -> list[str]:
    """Normalize, case-insensitively dedupe, and cap at ``_MAX_PHRASES``."""
    seen: set[str] = set()
    clean: list[str] = []
    for p in phrases:
        p = (p or "").strip().strip('"').strip("'").strip()
        if not p or len(p) > _MAX_PHRASE_LEN:
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        clean.append(p)
        if len(clean) >= _MAX_PHRASES:
            break
    return clean


def _parse_phrases(raw: str) -> list[str]:
    """Tolerantly parse an LLM response into a list of phrase strings.

    Handles ``{"phrases": [...]}`` objects, bare JSON arrays, common
    alternate keys, and output wrapped in markdown code fences. Returns []
    if nothing parseable.
    """
    if not raw:
        return []
    s = raw.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if "\n" in s:  # drop a leading language tag line (e.g. ```json)
            first, _, rest = s.partition("\n")
            if first.strip().isalpha():
                s = rest
        s = s.strip("`").strip()

    data = _json_loads_lenient(s)
    if isinstance(data, dict):
        for k in ("phrases", "key_phrases", "keyphrases", "suggestions", "keywords"):
            v = data.get(k)
            if isinstance(v, list):
                return [str(x) for x in v]
        return []
    if isinstance(data, list):
        return [str(x) for x in data]
    return []


def _json_loads_lenient(s: str) -> Any:
    """json.loads, then fall back to slicing out the first JSON array/object."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("[", "]"), ("{", "}")):
        start = s.find(opener)
        end = s.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(s[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None
