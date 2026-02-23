"""
Jira ADF (Atlassian Document Format) and API object normalization.
Used by the Jira loader and chunker to produce meaningful text only (no raw dicts/URLs).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Safe recursion limit for malformed or deeply nested ADF
ADF_MAX_DEPTH = 50


def adf_to_plain_text(doc: Any, depth: int = 0) -> str:
    """Convert ADF (e.g. {'type': 'doc', 'content': [...]}) to a single plain-text string.
    Uses safe recursion with depth limit. Handles paragraph, text, lists, tables,
    mentions (attrs.text only), hardBreak (newline), media/inlineCard (placeholder or ignore).
    """
    if depth > ADF_MAX_DEPTH:
        logger.warning("ADF recursion depth exceeded %s; truncating.", ADF_MAX_DEPTH)
        return ""

    if doc is None:
        return ""

    if isinstance(doc, str):
        return doc

    if not isinstance(doc, dict):
        return str(doc)

    node_type = doc.get("type") or ""
    content = doc.get("content")
    if not isinstance(content, list):
        content = []

    # Mention: output @text only (not id, accessLevel)
    if node_type == "mention":
        attrs = doc.get("attrs") or {}
        text = attrs.get("text") or ""
        return f"@{text}" if text else ""

    # HardBreak: newline (critical for embeddings)
    if node_type == "hardBreak":
        return "\n"

    # Text leaf (marks are formatting only, not nested content)
    if node_type == "text":
        return doc.get("text") or ""
    if node_type in ("mark", "emoji"):
        return "".join(adf_to_plain_text(c, depth + 1) for c in content)

    # Media: placeholder (do not store raw JSON)
    if node_type == "media":
        attrs = doc.get("attrs") or {}
        alt = attrs.get("alt") or attrs.get("title") or "attachment"
        return f"[Attachment: {alt}]"

    # InlineCard: ignore or minimal placeholder
    if node_type == "inlineCard":
        attrs = doc.get("attrs") or {}
        url = attrs.get("url") or ""
        return f"[Link: {url}]" if url else ""

    # Table: flatten to readable lines (tableRow -> tableCell -> paragraph -> text)
    if node_type == "table":
        rows_text = []
        for row in content:
            if not isinstance(row, dict) or (row.get("type") or "") != "tableRow":
                continue
            cells = []
            for cell in row.get("content") or []:
                if not isinstance(cell, dict) or (cell.get("type") or "") != "tableCell":
                    continue
                cell_text = "".join(
                    adf_to_plain_text(block, depth + 1)
                    for block in (cell.get("content") or [])
                ).strip()
                if cell_text:
                    cells.append(cell_text)
            if cells:
                rows_text.append(" | ".join(cells))
        return "\n".join(rows_text)

    if node_type == "tableRow":
        return "".join(adf_to_plain_text(c, depth + 1) for c in content)

    if node_type == "tableCell":
        return "".join(adf_to_plain_text(c, depth + 1) for c in content)

    # Paragraph, heading, blockQuote, codeBlock, panel
    if node_type in ("paragraph", "heading", "blockQuote", "codeBlock", "panel", "rule"):
        parts = [adf_to_plain_text(c, depth + 1) for c in content]
        joined = " ".join(p for p in parts if p)
        if node_type == "paragraph" and content and joined:
            return joined + "\n"
        return joined + "\n" if joined else ""

    # Lists
    if node_type in ("bulletList", "orderedList"):
        items = []
        for item in content:
            if isinstance(item, dict) and (item.get("type") or "") == "listItem":
                items.append(adf_to_plain_text(item, depth + 1))
        return "\n".join(p for p in items if p) + "\n" if items else ""

    if node_type == "listItem":
        return "".join(adf_to_plain_text(c, depth + 1) for c in content)

    # Doc root or other container
    if node_type == "doc" or node_type == "layoutSection" or node_type == "layoutColumn":
        return "".join(adf_to_plain_text(c, depth + 1) for c in content)

    # mediaSingle, extension, etc.
    if node_type == "mediaSingle":
        return "".join(adf_to_plain_text(c, depth + 1) for c in content)

    # Unknown: recurse content
    return "".join(adf_to_plain_text(c, depth + 1) for c in content)


def extract_scalar(obj: Any) -> str | None:
    """Extract a single scalar (name, id, or displayName) from a Jira API object.
    If obj is already a string, return it. Otherwise take name, displayName, or id.
    Used for status, priority, assignee, reporter so we never store avatarUrls/self/raw dicts.
    """
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj.strip() or None
    if not isinstance(obj, dict):
        return str(obj).strip() or None
    # Prefer displayName for users, name for status/priority/issue_type
    for key in ("displayName", "name", "id"):
        val = obj.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None
