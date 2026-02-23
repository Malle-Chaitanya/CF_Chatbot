"""
Generate a short, accurate summary of a Jira ticket using an LLM.
Supports two modes:
- Chunk-based (recommended): build summary context from chunks, then summarize. Holistic and robust.
- Field-based (legacy): summarize from raw ticket fields (description, root_cause, fix, first comment).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Cap total context sent to LLM for summary (keeps ingestion stable)
MAX_SUMMARY_CONTEXT_CHARS = 4000

# Legacy: max chars per section when summarizing from raw fields
_DESC_MAX = 2000
_ROOT_MAX = 800
_FIX_MAX = 800
_COMMENT_MAX = 500


def build_summary_context(
    chunks: list[tuple[str, dict[str, Any]]],
    max_chars: int = MAX_SUMMARY_CONTEXT_CHARS,
) -> str:
    """
    Build a single context string from chunked ticket content for LLM summarization.
    Includes: summary (heading), description (problem), root_cause, fix_description,
    and all comment chunks as Discussion (bounded by max_chars). Trims to max_chars.
    chunks: list of (chunk_text, metadata); metadata must have "section" and "doc_id".
    """
    if not chunks:
        return ""
    doc_id = (chunks[0][1].get("doc_id") or chunks[0][1].get("ticket_key") or "").strip()
    by_section: dict[str, list[tuple[str, dict]]] = {}
    for text, meta in chunks:
        sec = (meta.get("section") or "other").strip()
        by_section.setdefault(sec, []).append((text.strip(), meta))

    parts: list[str] = []
    for label, section_key in [
        ("Heading", "summary"),
        ("Problem", "description"),
        ("Root Cause", "root_cause"),
        ("Fix", "fix_description"),
    ]:
        section_chunks = by_section.get(section_key, [])
        if section_chunks:
            text = "\n".join(t[0] for t in section_chunks[:3])  # at most 3 parts if split
            if text:
                parts.append(f"{label}:\n{text}")

    comment_chunks = by_section.get("comment", [])
    if comment_chunks:
        discussion_parts = [text for text, _ in comment_chunks]
        parts.append("Discussion:\n" + "\n\n".join(discussion_parts))

    combined = f"Ticket: {doc_id}\n\n" + "\n\n".join(parts)
    if len(combined) > max_chars:
        combined = combined[: max_chars - 50].rsplit("\n", 1)[0] + "\n\n[truncated]"
    return combined.strip()


def generate_summary_from_context(
    context: str,
    *,
    ticket_key: str = "",
    api_key: str | None = None,
    model: str | None = None,
    max_context_chars: int = MAX_SUMMARY_CONTEXT_CHARS,
) -> str:
    """
    Generate a 1–2 sentence summary from pre-built chunk context. Single LLM pass.
    Returns empty string on failure; caller should keep existing summary/title.
    """
    if not (context or "").strip():
        return ""
    context = context.strip()[:max_context_chars]
    try:
        from openai import OpenAI
        from config.settings import get_settings
        settings = get_settings()
        key_override = api_key if api_key is not None else settings.openai_api_key
        if not (key_override or "").strip():
            logger.debug("Jira LLM summary skipped: no OpenAI API key")
            return ""
        logger.info("Generating LLM summary from chunks for %s", ticket_key or "?")
        client = OpenAI(api_key=key_override or settings.openai_api_key)
        model_name = model or settings.llm_model
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical analyst. Summarize this Jira ticket in 1–2 sentences including: what problem occurred, root cause (if known), and how it was resolved. Use only the information provided. Output only the summary, no prefix or quotes.",
                },
                {"role": "user", "content": context},
            ],
        )
        summary = (response.choices[0].message.content or "").strip()
        return summary[:500] if summary else ""
    except Exception as e:
        logger.warning("Jira LLM summary from context failed for %s: %s", ticket_key or "?", e)
        return ""


def generate_ticket_summary(
    ticket: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """
    Analyze the full ticket (description, root_cause, fix_description, comments) and return
    a 1–2 sentence summary. Returns empty string on failure or if no content to summarize;
    caller should fall back to ticket["summary"] or ticket["doc_title"].
    """
    key = (ticket.get("key") or "").strip()
    description = (ticket.get("description") or "").strip()[: _DESC_MAX]
    root_cause = (ticket.get("root_cause") or "").strip()[: _ROOT_MAX]
    fix_description = (ticket.get("fix_description") or "").strip()[: _FIX_MAX]
    comments = ticket.get("comments") or []
    first_comment = ""
    if isinstance(comments, list) and comments:
        c = comments[0] if isinstance(comments[0], dict) else {}
        first_comment = (c.get("body_plain") or c.get("body") or "").strip()[: _COMMENT_MAX]

    combined = "\n\n".join(
        filter(
            None,
            [
                f"Description:\n{description}" if description else "",
                f"Root cause:\n{root_cause}" if root_cause else "",
                f"Fix description:\n{fix_description}" if fix_description else "",
                f"First comment:\n{first_comment}" if first_comment else "",
            ]
        )
    ).strip()
    if not combined:
        return ""

    try:
        from openai import OpenAI
        from config.settings import get_settings
        settings = get_settings()
        key_override = api_key if api_key is not None else settings.openai_api_key
        if not (key_override or "").strip():
            logger.debug("Jira LLM summary skipped: no OpenAI API key")
            return ""
        logger.info("Generating LLM summary for %s", key or "?")
        client = OpenAI(api_key=key_override or settings.openai_api_key)
        model_name = model or settings.llm_model
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical writer. Given a Jira ticket's main content, write a single short summary (1-2 sentences) that describes what the ticket is about: the problem and how it was resolved (if stated). Use neutral, factual language. Output only the summary, no prefix or quotes.",
                },
                {
                    "role": "user",
                    "content": f"Ticket key: {key}\n\nContent:\n{combined}",
                },
            ],
        )
        summary = (response.choices[0].message.content or "").strip()
        return summary[: 500] if summary else ""
    except Exception as e:
        logger.warning("Jira LLM summary failed for %s: %s", key or "?", e)
        return ""
