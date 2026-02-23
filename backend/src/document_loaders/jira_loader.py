"""
Load Jira tickets from a JSON file (Format 2 raw API export).
Normalizes ADF to plain text and API objects to scalars; yields one normalized ticket dict per ticket.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterator

from document_loaders.jira_utils import adf_to_plain_text, extract_scalar

logger = logging.getLogger(__name__)


def _normalize_field(value: Any, *, as_adf: bool = False) -> str:
    """If as_adf: treat value as ADF and convert to plain text. Else return scalar or string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if as_adf and isinstance(value, dict):
        return adf_to_plain_text(value).strip()
    return str(value).strip()


def _normalize_comment(c: Any) -> dict[str, Any] | None:
    """Normalize one comment: author -> author_display, body (ADF) -> body_plain, created."""
    if not isinstance(c, dict):
        return None
    author = c.get("author")
    author_display = extract_scalar(author) if author is not None else ""
    body = c.get("body")
    body_plain = _normalize_field(body, as_adf=True) if body is not None else ""
    created = c.get("created") or c.get("updated")
    if created is not None and not isinstance(created, str):
        created = str(created)
    return {
        "author_display": author_display or "",
        "author": author_display or "",
        "body_plain": body_plain,
        "body": body_plain,
        "created": created or "",
        "date": created or "",
    }


def load_jira_tickets_from_json(path: str | Path) -> Iterator[dict[str, Any]]:
    """
    Read JSON from path and yield one normalized ticket dict per ticket.
    Expects top-level "tickets" array (or "ticket" key for single ticket).
    Each ticket: key, summary, description (ADF or str), status, priority, assignee, reporter,
    created, updated, resolved, url, project_key, root_cause, combination, fix_description,
    comments[] (author, body, created). Normalizes ADF -> plain text and objects -> scalars.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Jira JSON file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    tickets = data.get("tickets") or data.get("ticket")
    if isinstance(tickets, dict):
        tickets = [tickets]
    if not isinstance(tickets, list):
        logger.warning("No 'tickets' or 'ticket' array in JSON; yielding nothing.")
        return

    for raw in tickets:
        if not isinstance(raw, dict):
            continue
        key = (raw.get("key") or raw.get("ticket_key") or "").strip()
        if not key:
            continue

        # Normalize ADF fields to plain text
        description = _normalize_field(raw.get("description"), as_adf=True)
        root_cause = _normalize_field(raw.get("root_cause"), as_adf=True)
        fix_description = _normalize_field(raw.get("fix_description"), as_adf=True)
        summary = _normalize_field(raw.get("summary") or raw.get("doc_title"))

        # Scalars from API objects
        status = extract_scalar(raw.get("status"))
        priority = extract_scalar(raw.get("priority"))
        assignee = extract_scalar(raw.get("assignee"))
        reporter = extract_scalar(raw.get("reporter"))
        issue_type = extract_scalar(raw.get("issue_type") or raw.get("issuetype"))

        # Dates and strings
        created = raw.get("created")
        if created is not None and not isinstance(created, str):
            created = str(created)
        updated = raw.get("updated")
        if updated is not None and not isinstance(updated, str):
            updated = str(updated)
        resolved = raw.get("resolved")
        if resolved is not None and not isinstance(resolved, str):
            resolved = str(resolved)

        project_key = (raw.get("project_key") or raw.get("project") or "").strip()
        if not project_key and key:
            # e.g. PRI-9796 -> PRI
            project_key = key.split("-")[0] if "-" in key else ""
        combination = (_normalize_field(raw.get("combination")) or "Unknown").strip() or "Unknown"

        # Comments
        comments_raw = raw.get("comments") or []
        if not isinstance(comments_raw, list):
            comments_raw = []
        comments = []
        for c in comments_raw:
            nc = _normalize_comment(c)
            if nc:
                comments.append(nc)

        yield {
            "key": key,
            "summary": summary,
            "doc_title": summary,
            "description": description,
            "root_cause": root_cause,
            "fix_description": fix_description,
            "status": status,
            "priority": priority,
            "assignee": assignee,
            "reporter": reporter,
            "issue_type": issue_type,
            "created": created,
            "updated": updated,
            "resolved": resolved,
            "project_key": project_key,
            "combination": combination,
            "comments": comments,
        }
