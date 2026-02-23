"""
Jira section-based chunker: one ticket (normalized dict) -> list of (chunk_text, metadata).
Level 1 = ticket (parent); Level 2 = sections (summary, description, root_cause, fix_description);
Level 3 = comments (one chunk per comment). Oversized sections are split by tokens (no truncation loss).

Chunk order preserves the technical story: problem -> cause -> fix -> discussion.
  - summary: overview (Ticket Key, Combination, Status, etc.)
  - description: problem
  - root_cause: cause (ticket_chunk_type=problem)
  - fix_description: fix (ticket_chunk_type=resolution)
  - comment (each): discussion (ticket_chunk_type=resolution)
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Split sections larger than this into subchunks so embedding API never sees > 8191 tokens
MAX_SAFE_TOKENS_PER_SECTION = 6000


def _token_count(text: str) -> int:
    """Return approximate token count (cl100k_base). Fallback: chars // 4."""
    if not text:
        return 0
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(0, len(text) // 4)


def _split_section_by_tokens(text: str, max_tokens: int = MAX_SAFE_TOKENS_PER_SECTION) -> list[str]:
    """
    Split long section text into subchunks each <= max_tokens. Prefer breaks at paragraph/newline.
    Production-safe: no truncation; every part is embedded and stored.
    """
    if not text or _token_count(text) <= max_tokens:
        return [text] if text else []
    enc = None
    tokens = None
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
    except Exception:
        pass
    if tokens is None or enc is None:
        # Fallback: split by chars (max_tokens * 4)
        max_chars = max_tokens * 4
        parts = []
        rest = text
        while rest:
            if len(rest) <= max_chars:
                parts.append(rest)
                break
            chunk = rest[:max_chars]
            for sep in ("\n\n", "\n", ". "):
                idx = chunk.rfind(sep)
                if idx > max_chars // 2:
                    chunk = chunk[: idx + len(sep)].rstrip()
                    rest = rest[len(chunk):].lstrip()
                    parts.append(chunk)
                    break
            else:
                parts.append(chunk)
                rest = rest[max_chars:]
        return parts
    parts = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        if end < len(tokens) and "\n" in chunk_text:
            last_nl = chunk_text.rfind("\n")
            if last_nl > len(chunk_text) // 2:
                chunk_text = chunk_text[: last_nl + 1].rstrip()
                chunk_tokens = enc.encode(chunk_text)
                end = start + len(chunk_tokens)
        parts.append(chunk_text)
        start = end
    return parts


def _date_only(iso_or_str: Any) -> str | None:
    """Return date part YYYY-MM-DD from ISO string or None."""
    if iso_or_str is None or not str(iso_or_str).strip():
        return None
    s = str(iso_or_str).strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else (s[:10] if len(s) >= 10 else s)


def _build_summary_content(ticket: dict[str, Any]) -> str:
    """Build structured summary chunk content (one field per line, consistent prefixes)."""
    lines = []
    key = (ticket.get("key") or "").strip()
    if key:
        lines.append(f"Ticket Key: {key}")
    pk = (ticket.get("project_key") or "").strip()
    if pk:
        lines.append(f"Project: {pk}")
    it = (ticket.get("issue_type") or "").strip()
    if it:
        lines.append(f"Issue Type: {it}")
    summary = (ticket.get("summary") or ticket.get("doc_title") or "").strip()
    if summary:
        lines.append(f"Summary: {summary}")
    status = (ticket.get("status") or "").strip()
    if status:
        lines.append(f"Status: {status}")
    priority = (ticket.get("priority") or "").strip()
    if priority:
        lines.append(f"Priority: {priority}")
    combo = (ticket.get("combination") or "").strip() or "Unknown"
    lines.append(f"Combination: {combo}")
    assignee = (ticket.get("assignee") or "").strip()
    if assignee:
        lines.append(f"Assignee: {assignee}")
    reporter = (ticket.get("reporter") or "").strip()
    if reporter:
        lines.append(f"Reporter: {reporter}")
    created = _date_only(ticket.get("created"))
    if created:
        lines.append(f"Created: {created}")
    resolved = _date_only(ticket.get("resolved"))
    if resolved:
        lines.append(f"Resolved: {resolved}")
    return "\n".join(lines)


def build_summary_chunk_content(ticket: dict[str, Any]) -> str:
    """
    Build the structured summary chunk text for a ticket (Ticket Key, Summary, Status, etc.).
    Used when the ticket summary has been updated (e.g. after LLM summary from chunks) and
    the first chunk must be replaced with this content.
    """
    return _build_summary_content(ticket)


def chunk_jira_ticket(ticket: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """
    Turn one normalized Jira ticket dict into section chunks.
    Input: at least key, summary; optional description, root_cause, fix_description, comments;
    optional parent fields: status, priority, assignee, reporter, created, resolved, combination,
    issue_type, project_key, updated.
    comments: list of dicts with author_display (or author), created, body_plain (or body).
    Output: list of (chunk_text, metadata) with doc_id=ticket_key, chunk_index, total_chunks,
    section, ticket_chunk_type, ticket_has_resolution, ticket_has_root_cause.
    Empty sections are skipped.
    """
    key = (ticket.get("key") or "").strip()
    if not key:
        logger.warning("Ticket has no key; skipping.")
        return []

    # Parent metadata (scalars only)
    def g(k: str, default: str | None = None) -> str | None:
        v = ticket.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            return default
        return str(v).strip() if isinstance(v, str) else str(v)

    parent = {
        "doc_id": key,
        "ticket_key": key,
        "source_type": "jira",
        "collection": "JiraTickets",
        "project_key": g("project_key"),
        "issue_type": g("issue_type"),
        "priority": g("priority"),
        "status": g("status"),
        "combination": g("combination") or "Unknown",
        "assignee": g("assignee"),
        "reporter": g("reporter"),
        "doc_title": g("summary") or g("doc_title"),
        "created": g("created"),
        "updated": g("updated"),
        "resolved": g("resolved"),
    }
    # Remove None so metadata matches schema (omit None)
    parent = {k: v for k, v in parent.items() if v is not None}

    description = (ticket.get("description") or "").strip() if isinstance(ticket.get("description"), str) else ""
    root_cause = (ticket.get("root_cause") or "").strip() if isinstance(ticket.get("root_cause"), str) else ""
    fix_description = (ticket.get("fix_description") or "").strip() if isinstance(ticket.get("fix_description"), str) else ""
    comments_raw = ticket.get("comments") or []
    if not isinstance(comments_raw, list):
        comments_raw = []

    ticket_has_resolution = bool(fix_description) or len(comments_raw) > 0
    ticket_has_root_cause = bool(root_cause)

    chunks: list[tuple[str, dict[str, Any]]] = []

    # Summary chunk (structured format; consistent prefixes for embeddings)
    summary_content = _build_summary_content(ticket)
    if summary_content:
        meta = dict(parent)
        meta["section"] = "summary"
        meta["ticket_chunk_type"] = "summary"
        meta["ticket_has_resolution"] = ticket_has_resolution
        meta["ticket_has_root_cause"] = ticket_has_root_cause
        chunks.append((summary_content, meta))

    # Helper: emit one chunk per (subchunk) so oversized sections are split, not truncated
    def _add_section_chunks(
        content: str,
        section: str,
        ticket_chunk_type: str,
    ) -> None:
        if not content:
            return
        meta = dict(parent)
        meta["section"] = section
        meta["ticket_chunk_type"] = ticket_chunk_type
        meta["ticket_has_resolution"] = ticket_has_resolution
        meta["ticket_has_root_cause"] = ticket_has_root_cause
        if _token_count(content) <= MAX_SAFE_TOKENS_PER_SECTION:
            chunks.append((content, meta))
            return
        tok_count = _token_count(content)
        parts = _split_section_by_tokens(content)
        if len(parts) > 1:
            logger.info(
                "Split oversized section %s (%s tokens) into %s subchunks (ticket %s)",
                section, tok_count, len(parts), key,
            )
        total_parts = len(parts)
        for part_idx, part in enumerate(parts):
            part_meta = dict(meta)
            part_meta["section_part_index"] = part_idx + 1
            part_meta["section_part_total"] = total_parts
            chunks.append((part, part_meta))

    # Description
    _add_section_chunks(description, "description", "problem")

    # Root cause
    _add_section_chunks(root_cause, "root_cause", "problem")

    # Fix description
    _add_section_chunks(fix_description, "fix_description", "resolution")

    # Comments (one chunk per comment)
    for i, c in enumerate(comments_raw):
        if not isinstance(c, dict):
            continue
        author = (c.get("author_display") or c.get("author") or "")
        if isinstance(author, dict):
            author = (author.get("displayName") or author.get("name") or str(author))[:200]
        else:
            author = str(author).strip()[:200]
        created_at = c.get("created") or c.get("date") or ""
        if isinstance(created_at, str):
            created_at = _date_only(created_at) or created_at[:10]
        else:
            created_at = str(created_at)[:10]
        body = (c.get("body_plain") or c.get("body") or "")
        if not isinstance(body, str):
            body = str(body)
        body = body.strip()
        content_parts = []
        if author:
            content_parts.append(f"Author: {author}")
        if created_at:
            content_parts.append(f"Date: {created_at}")
        if content_parts:
            content_parts.append("")
        content_parts.append(body)
        content = "\n".join(content_parts).strip()
        if not content:
            continue
        meta = dict(parent)
        meta["section"] = "comment"
        meta["ticket_chunk_type"] = "resolution"
        meta["comment_index"] = i + 1
        meta["ticket_has_resolution"] = ticket_has_resolution
        meta["ticket_has_root_cause"] = ticket_has_root_cause
        if _token_count(content) <= MAX_SAFE_TOKENS_PER_SECTION:
            chunks.append((content, meta))
        else:
            tok_count = _token_count(content)
            parts = _split_section_by_tokens(content)
            logger.info(
                "Split oversized comment %s (%s tokens) into %s subchunks (ticket %s)",
                i + 1, tok_count, len(parts), key,
            )
            total_parts = len(parts)
            for part_idx, part in enumerate(parts):
                part_meta = dict(meta)
                part_meta["comment_part_index"] = part_idx + 1
                part_meta["comment_part_total"] = total_parts
                chunks.append((part, part_meta))

    # Set chunk_index and total_chunks on every chunk
    total = len(chunks)
    result = []
    for idx, (text, meta) in enumerate(chunks):
        meta = dict(meta)
        meta["chunk_index"] = idx
        meta["total_chunks"] = total
        result.append((text, meta))

    return result
