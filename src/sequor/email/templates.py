from __future__ import annotations

"""Email template functions for all notification types.

Pure functions that accept TypedDict data and return (html, text) tuples.
No I/O, no external dependencies beyond stdlib + compliance helpers.
"""

from typing import TypedDict

from sequor.compliance import build_consent_notice


# ---------------------------------------------------------------------------
# Input data types
# ---------------------------------------------------------------------------


class EscalationEmailData(TypedDict):
    escalation_id: str
    contact_name: str
    contact_channel: str
    received_at: str
    ai_attempted: str
    confidence_score: float
    confidence_category: str
    original_message_body: str
    escalation_deadline: str
    backup_name: str
    suggested_response: str | None
    org_name: str
    one_line_summary: str


class DigestEmailData(TypedDict):
    account_name: str
    date: str
    ai_handled_count: int
    rag_resolved_count: int
    learned_answers_count: int
    pending_count: int
    oldest_unresolved_hours: float | None
    escalated_count: int
    breached_count: int
    new_knowledge_count: int
    new_knowledge_topics: list[str]
    org_name: str


class WeeklyRecapData(TypedDict):
    account_name: str
    date_range: str
    total_messages: int
    ai_auto_resolved: int
    human_resolved: int
    pending: int
    ai_accuracy_pct: float
    top_topics: list[str]
    knowledge_new: int
    knowledge_total: int
    avg_ai_response_minutes: float
    avg_human_response_hours: float
    org_name: str


class ReturnSummaryData(TypedDict):
    account_name: str
    date_range: str
    total_received: int
    auto_resolved: int
    backup_resolved: int
    still_pending: int
    pending_items: list[dict]
    new_answers_learned: int
    org_name: str


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _html_escape(s: str) -> str:
    import html

    return html.escape(s, quote=True)


def _sanitize_header(value: str) -> str:
    return "".join(c for c in value if ord(c) > 0x1F and ord(c) != 0x7F)


def _html_wrapper(subject: str, body_html: str, org_name: str) -> str:
    consent = build_consent_notice(org_name)
    esc_subject = _html_escape(subject)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head><meta charset="utf-8">'
        f"<title>{esc_subject}</title></head>\n"
        '<body style="font-family:Arial,Helvetica,sans-serif;color:#333;'
        'max-width:600px;margin:0 auto;padding:20px;">\n'
        f"{body_html}\n"
        '<hr style="border:none;border-top:1px solid #ddd;margin:24px 0;">'
        f'<p style="font-size:12px;color:#999;">{_html_escape(consent)}</p>'
        "</body>\n</html>"
    )


def _format_confidence(score: float) -> str:
    return f"{score:.0%}"


# ---------------------------------------------------------------------------
# Auto-reply email
# ---------------------------------------------------------------------------


def build_auto_reply_email(
    response_content: str,
    confidence_badge: str,
) -> tuple[str, str]:
    """Build an auto-reply email for high-confidence AI responses."""
    confidence_note = f"Confidence: {confidence_badge}."
    body_html = (
        "<div style='font-size:14px;white-space:pre-wrap;'>"
        f"{_html_escape(response_content)}</div>"
        "<hr style='border:none;border-top:1px solid #eee;margin:16px 0;'>"
        "<p style='font-size:12px;color:#999;'>"
        "This reply was generated automatically by your AI assistant. "
        f"{confidence_note} "
        "If you believe this response needs correction, please contact the business directly."
        "</p>"
    )
    html = _html_wrapper("Auto-Reply", body_html, "Sequor")

    text = (
        f"{response_content}\n\n"
        "---\n"
        "This reply was generated automatically by your AI assistant. "
        f"{confidence_note} "
        "If you believe this response needs correction, please contact the business directly."
    )
    return html, text


# ---------------------------------------------------------------------------
# Escalation email
# ---------------------------------------------------------------------------


def build_escalation_subject(data: EscalationEmailData) -> str:
    short_id = str(data["escalation_id"])[:8]
    return _sanitize_header(f"[UNRESOLVED] {data['one_line_summary']} (Ref: {short_id})")


def build_escalation_email(data: EscalationEmailData) -> tuple[str, str]:
    subject = build_escalation_subject(data)
    confidence = _format_confidence(data["confidence_score"])
    suggested_section = ""
    suggested_text = ""
    if data["suggested_response"]:
        suggested_text = (
            f"\nAI suggested response (edit before sending or compose your own):\n"
            f"{data['suggested_response']}"
        )
        suggested_section = (
            '<p style="background:#f0f7ff;padding:12px;border-left:3px solid #0066cc;'
            f'font-size:14px;">AI suggested response:<br><br>'
            f"{_html_escape(data['suggested_response'])}</p>"
        )

    body_html = (
        f"<h2 style='color:#c00;margin:0 0 16px;'>{_html_escape(subject)}</h2>"
        "<table style='font-size:14px;border-collapse:collapse;'>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Client:</td>"
        f"<td style='padding:4px 0;'>{_html_escape(data['contact_name'])} "
        f"({_html_escape(data['contact_channel'])})</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Received:</td>"
        f"<td style='padding:4px 0;'>{_html_escape(data['received_at'])}</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>AI attempted:</td>"
        f"<td style='padding:4px 0;'>{_html_escape(data['ai_attempted'])}</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Confidence:</td>"
        f"<td style='padding:4px 0;'>{confidence} &mdash; "
        f"{_html_escape(data['confidence_category'])}</td></tr>"
        "</table>"
        "<hr style='border:none;border-top:1px solid #eee;margin:16px 0;'>"
        f"<div style='font-size:14px;white-space:pre-wrap;'>"
        f"{_html_escape(data['original_message_body'])}</div>"
        "<hr style='border:none;border-top:1px solid #eee;margin:16px 0;'>"
        "<p style='font-size:13px;color:#555;'>"
        "&rarr; Reply to this email to send your response to the client.<br>"
        f"&rarr; If unresolved by {_html_escape(data['escalation_deadline'])}, "
        f"this will escalate to {_html_escape(data['backup_name'])}."
        "</p>"
        f"{suggested_section}"
    )

    html = _html_wrapper(subject, body_html, data["org_name"])

    text = (
        f"Client: {data['contact_name']} ({data['contact_channel']})\n"
        f"Received: {data['received_at']}\n"
        f"AI attempted: {data['ai_attempted']}\n"
        f"Confidence: {confidence} — {data['confidence_category']}\n"
        f"Requested via: {data['contact_channel']}\n"
        "\n"
        f"{data['original_message_body']}\n"
        "\n"
        "---\n"
        "→ Reply to this email to send your response to the client.\n"
        f"→ If unresolved by {data['escalation_deadline']}, "
        f"this will escalate to {data['backup_name']}.\n"
        f"{suggested_text}"
    )

    return html, text


# ---------------------------------------------------------------------------
# Daily digest email
# ---------------------------------------------------------------------------


def build_digest_subject(data: DigestEmailData) -> str:
    return _sanitize_header(f"[COVERAGE DIGEST] {data['date']} — {data['account_name']}")


def build_digest_email(data: DigestEmailData) -> tuple[str, str]:
    subject = build_digest_subject(data)
    oldest = (
        f"{data['oldest_unresolved_hours']:.1f} hours ago"
        if data["oldest_unresolved_hours"] is not None
        else "N/A"
    )
    topics_list = (
        "".join(
            f'<li style="font-size:13px;">{_html_escape(t)}</li>'
            for t in data["new_knowledge_topics"]
        )
        or '<li style="font-size:13px;color:#999;">None today</li>'
    )

    body_html = (
        f"<h2 style='margin:0 0 16px;'>{_html_escape(subject)}</h2>"
        "<h3 style='color:#333;font-size:16px;'>AI Activity</h3>"
        f"<p style='font-size:14px;'>AI handled automatically: "
        f"<strong>{data['ai_handled_count']}</strong> messages</p>"
        "<ul style='font-size:13px;color:#555;'>"
        f"<li>Resolved by RAG: {data['rag_resolved_count']}</li>"
        f"<li>Resolved by learned answers: {data['learned_answers_count']}</li>"
        "</ul>"
        "<h3 style='color:#333;font-size:16px;'>Your Attention Needed</h3>"
        f"<p style='font-size:14px;'>Pending your response: "
        f"<strong>{data['pending_count']}</strong> items</p>"
        f"<p style='font-size:13px;color:#555;'>Oldest unresolved: {oldest}</p>"
        "<h3 style='color:#333;font-size:16px;'>Escalations</h3>"
        f"<p style='font-size:14px;'>Escalated to backup: "
        f"<strong>{data['escalated_count']}</strong> items</p>"
        "<ul style='font-size:13px;color:#555;'>"
        f"<li>Breached SLA: {data['breached_count']} (need attention)</li>"
        "</ul>"
        "<h3 style='color:#333;font-size:16px;'>Knowledge Base</h3>"
        f"<p style='font-size:14px;'>New knowledge learned: "
        f"<strong>{data['new_knowledge_count']}</strong> answers added</p>"
        f"<ul>{topics_list}</ul>"
    )

    html = _html_wrapper(subject, body_html, data["org_name"])

    topics_text = "\n".join(f'  - "{t}"' for t in data["new_knowledge_topics"])
    if not topics_text:
        topics_text = "  (none today)"

    text = (
        f"{subject}\n"
        "\n"
        f"AI handled automatically: {data['ai_handled_count']} messages\n"
        f" - Resolved by RAG: {data['rag_resolved_count']}\n"
        f" - Resolved by learned answers: {data['learned_answers_count']}\n"
        "\n"
        f"Pending your response: {data['pending_count']} items\n"
        f" - Oldest unresolved: {oldest}\n"
        "\n"
        f"Escalated to backup: {data['escalated_count']} items\n"
        f" - Breached SLA: {data['breached_count']} (need attention)\n"
        "\n"
        f"New knowledge learned: {data['new_knowledge_count']} "
        f"answers added to knowledge base\n"
        f"{topics_text}"
    )

    return html, text


# ---------------------------------------------------------------------------
# Weekly recap email
# ---------------------------------------------------------------------------


def build_weekly_recap_subject(data: WeeklyRecapData) -> str:
    return _sanitize_header(f"[WEEKLY RECAP] {data['date_range']} — {data['account_name']}")


def build_weekly_recap_email(data: WeeklyRecapData) -> tuple[str, str]:
    subject = build_weekly_recap_subject(data)
    total = data["total_messages"] or 1
    ai_pct = data["ai_auto_resolved"] / total * 100
    human_pct = data["human_resolved"] / total * 100

    topics_list = (
        "".join(
            f"<li style='font-size:13px;'>{_html_escape(t)}</li>" for t in data["top_topics"][:5]
        )
        or '<li style="font-size:13px;color:#999;">No topics recorded</li>'
    )

    body_html = (
        f"<h2 style='margin:0 0 16px;'>{_html_escape(subject)}</h2>"
        f"<p style='font-size:14px;'>Messages this week: "
        f"<strong>{data['total_messages']}</strong></p>"
        "<ul style='font-size:13px;color:#555;'>"
        f"<li>AI auto-resolved: {data['ai_auto_resolved']} ({ai_pct:.0f}%)</li>"
        f"<li>Human resolved: {data['human_resolved']} ({human_pct:.0f}%)</li>"
        f"<li>Pending: {data['pending']}</li>"
        "</ul>"
        f"<p style='font-size:14px;'>AI accuracy: "
        f"<strong>{data['ai_accuracy_pct']:.0f}%</strong> "
        "(based on client acceptance/rejection)</p>"
        "<h3 style='color:#333;font-size:16px;'>Top Queries</h3>"
        f"<ol>{topics_list}</ol>"
        f"<p style='font-size:14px;'>Knowledge base growth: "
        f"{data['knowledge_new']} new answers learned this week "
        f"({data['knowledge_total']} total)</p>"
        f"<p style='font-size:14px;'>Average response time: "
        f"{data['avg_ai_response_minutes']:.0f} minutes (AI) / "
        f"{data['avg_human_response_hours']:.1f} hours (human)</p>"
    )

    html = _html_wrapper(subject, body_html, data["org_name"])

    topics_text = "\n".join(f" - {t}" for t in data["top_topics"][:5])

    text = (
        f"{subject}\n"
        "\n"
        f"Messages this week: {data['total_messages']}\n"
        f" - AI auto-resolved: {data['ai_auto_resolved']} ({ai_pct:.0f}%)\n"
        f" - Human resolved: {data['human_resolved']} ({human_pct:.0f}%)\n"
        f" - Pending: {data['pending']}\n"
        "\n"
        f"AI accuracy: {data['ai_accuracy_pct']:.0f}% "
        "(based on client acceptance/rejection)\n"
        f"Most common queries:\n{topics_text}\n"
        f"Knowledge base growth: {data['knowledge_new']} new answers "
        f"learned this week ({data['knowledge_total']} total)\n"
        f"Average response time: {data['avg_ai_response_minutes']:.0f} "
        f"minutes (AI) / {data['avg_human_response_hours']:.1f} hours (human)"
    )

    return html, text


# ---------------------------------------------------------------------------
# Return summary email
# ---------------------------------------------------------------------------


def build_return_summary_subject(data: ReturnSummaryData) -> str:
    return _sanitize_header(f"[OOO COMPLETE] {data['date_range']} — {data['account_name']}")


def build_return_summary_email(data: ReturnSummaryData) -> tuple[str, str]:
    subject = build_return_summary_subject(data)

    pending_rows = "".join(
        f"<tr><td style='padding:6px 12px 6px 0;font-size:13px;'>"
        f"{_html_escape(item.get('summary', ''))}</td>"
        f"<td style='padding:6px 0;font-size:12px;'>"
        f"{_html_escape(item.get('urgency', ''))}</td></tr>"
        for item in data["pending_items"]
    )
    pending_section = ""
    if data["pending_items"]:
        pending_section = (
            "<h3 style='color:#c00;font-size:16px;'>"
            "Pending items requiring your attention:</h3>"
            "<table style='border-collapse:collapse;width:100%;'>"
            f"{pending_rows}</table>"
        )

    body_html = (
        f"<h2 style='margin:0 0 16px;'>{_html_escape(subject)}</h2>"
        "<table style='font-size:14px;border-collapse:collapse;'>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>"
        f"Messages received:</td><td style='padding:4px 0;'>"
        f"<strong>{data['total_received']}</strong></td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>"
        f"Auto-resolved by AI:</td><td style='padding:4px 0;'>"
        f"{data['auto_resolved']}</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>"
        f"Resolved by backup:</td><td style='padding:4px 0;'>"
        f"{data['backup_resolved']}</td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>"
        f"Still pending:</td><td style='padding:4px 0;'>"
        f"<strong>{data['still_pending']}</strong></td></tr>"
        "</table>"
        f"{pending_section}"
        f"<p style='font-size:14px;margin-top:16px;'>"
        f"AI learned {data['new_answers_learned']} new answers "
        f"from your team's responses this period.</p>"
    )

    html = _html_wrapper(subject, body_html, data["org_name"])

    pending_text = ""
    for item in data["pending_items"]:
        summary = item.get("summary", "")
        urgency = item.get("urgency", "")
        pending_text += f"  - [{urgency}] {summary}\n"
    if not pending_text:
        pending_text = "  (none)\n"

    text = (
        f"{subject}\n"
        "\n"
        f"Messages received: {data['total_received']}\n"
        f" - Auto-resolved by AI: {data['auto_resolved']}\n"
        f" - Resolved by backup: {data['backup_resolved']}\n"
        f" - Still pending: {data['still_pending']}\n"
        "\n"
        "Pending items requiring your attention:\n"
        f"{pending_text}"
        "\n"
        f"AI learned {data['new_answers_learned']} new answers "
        "from your team's responses this period."
    )

    return html, text
