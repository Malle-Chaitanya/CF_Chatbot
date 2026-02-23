"""
Fetch Jira tickets from the Jira REST API (Atlassian) using settings from .env.
Yields the same normalized ticket dict shape as load_jira_tickets_from_json for use in the same pipeline.
Uses JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEYS; filter by JIRA_INGEST_PAST_MONTHS (updated in past N months).
"""
from __future__ import annotations

import base64
import logging
from calendar import monthrange
from datetime import date
from typing import Any, Iterator

import httpx

from config.settings import get_settings
from document_loaders.jira_utils import adf_to_plain_text, extract_scalar

logger = logging.getLogger(__name__)

SEARCH_PAGE_SIZE = 100
REQUEST_TIMEOUT = 60.0


def _is_minimal_issue(issue: dict[str, Any]) -> bool:
    """True if issue has only id (new /search/jql returns minimal refs)."""
    if not issue or not isinstance(issue.get("id"), (str, int)):
        return False
    # Has key or full fields => not minimal
    if issue.get("key") or issue.get("issueKey"):
        return False
    if isinstance(issue.get("fields"), dict) and issue.get("fields"):
        return False
    return True


def _fetch_issue_by_id(
    client: httpx.Client,
    base_url: str,
    headers: dict[str, str],
    issue_id: str | int,
) -> dict[str, Any] | None:
    """GET /rest/api/3/issue/{id} to resolve full issue (key + fields). Returns None on failure."""
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{issue_id}"
    try:
        r = client.get(url, headers=headers)
        if r.status_code != 200:
            logger.warning("Jira GET issue %s: %s %s", issue_id, r.status_code, r.text[:200])
            return None
        return r.json()
    except Exception as e:
        logger.warning("Jira GET issue %s failed: %s", issue_id, e)
        return None


def _normalize_field(value: Any, *, as_adf: bool = False) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if as_adf and isinstance(value, dict):
        return adf_to_plain_text(value).strip()
    return str(value).strip()


def _normalize_comment(c: Any) -> dict[str, Any] | None:
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


def _issue_to_ticket(issue: dict[str, Any], settings: Any) -> dict[str, Any] | None:
    """Map one Jira REST API issue to our normalized ticket dict."""
    # Support both legacy (key) and new /search/jql (issueKey or key inside fields)
    key = (issue.get("key") or issue.get("issueKey") or "").strip()
    if not key and isinstance(issue.get("fields"), dict):
        key = (extract_scalar(issue["fields"].get("key")) or "").strip()
    if not key:
        return None
    fields = issue.get("fields") or {}

    summary = _normalize_field(fields.get("summary"))
    description = _normalize_field(fields.get("description"), as_adf=True)
    root_cause = _normalize_field(
        fields.get(settings.jira_field_root_cause) if settings.jira_field_root_cause else None,
        as_adf=True,
    )
    fix_description = _normalize_field(
        fields.get(settings.jira_field_fix_description) if settings.jira_field_fix_description else None,
        as_adf=True,
    )
    combination_raw = (
        fields.get(settings.jira_field_combination)
        if settings.jira_field_combination
        else None
    )
    if combination_raw is not None:
        if isinstance(combination_raw, list) and combination_raw:
            first = combination_raw[0]
            combination = (
                extract_scalar(first)
                or _normalize_field(first.get("value") if isinstance(first, dict) else first)
            )
        elif isinstance(combination_raw, dict):
            combination = extract_scalar(combination_raw) or _normalize_field(combination_raw.get("value"))
        else:
            combination = _normalize_field(combination_raw)
    else:
        combination = "Unknown"
    combination = (combination or "Unknown").strip() or "Unknown"

    status = extract_scalar(fields.get("status"))
    priority = extract_scalar(fields.get("priority"))
    assignee = extract_scalar(fields.get("assignee"))
    reporter = extract_scalar(fields.get("reporter"))
    issue_type = extract_scalar(fields.get("issuetype"))
    project = fields.get("project")
    project_key = extract_scalar(project) if isinstance(project, dict) else (project or "")
    if not project_key and key:
        project_key = key.split("-")[0] if "-" in key else ""

    created = fields.get("created")
    if created is not None and not isinstance(created, str):
        created = str(created)
    updated = fields.get("updated")
    if updated is not None and not isinstance(updated, str):
        updated = str(updated)
    resolved = fields.get("resolutiondate")
    if resolved is not None and not isinstance(resolved, str):
        resolved = str(resolved)

    comments_raw = []
    comment_obj = fields.get("comment")
    if isinstance(comment_obj, dict) and isinstance(comment_obj.get("comments"), list):
        comments_raw = comment_obj["comments"]
    comments = []
    for c in comments_raw:
        nc = _normalize_comment(c)
        if nc:
            comments.append(nc)

    return {
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
        "project_key": (project_key or "").strip(),
        "combination": combination,
        "comments": comments,
    }


def fetch_jira_tickets_from_api() -> Iterator[dict[str, Any]]:
    """
    Fetch issues from Jira REST API (settings: jira_server, jira_email, jira_api_token, jira_project_keys).
    Yields one normalized ticket dict per issue (same shape as load_jira_tickets_from_json).
    """
    settings = get_settings()
    base = (settings.jira_server or "").rstrip("/")
    email = (settings.jira_email or "").strip()
    token = (settings.jira_api_token or "").strip()
    project_keys = (settings.jira_project_keys or "PRI").strip()
    if not base or not email or not token:
        logger.warning("Jira API skipped: set JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN in .env")
        return
    projects = [p.strip() for p in project_keys.split(",") if p.strip()]
    if not projects:
        logger.warning("Jira API skipped: JIRA_PROJECT_KEYS is empty")
        return
    jql = "project in (" + ",".join(projects) + ")"
    statuses_str = getattr(settings, "jira_ingest_statuses", "") or ""
    statuses = [s.strip() for s in statuses_str.split(",") if s.strip()]
    if statuses:
        # Only resolved/closed (or whatever statuses are set in .env)
        quoted = ", ".join(f'"{s}"' for s in statuses)
        jql += f" AND status in ({quoted})"
    past_months = getattr(settings, "jira_ingest_past_months", 0) or 0
    if past_months > 0:
        today = date.today()
        year, month = today.year, today.month - past_months
        while month <= 0:
            month += 12
            year -= 1
        day = min(today.day, monthrange(year, month)[1])
        since = date(year, month, day).isoformat()
        jql += f' AND updated >= "{since}"'
    # Latest first: so "first N" = N most recently updated (window per run)
    jql += " ORDER BY updated DESC, key ASC"
    max_tickets = getattr(settings, "jira_ingest_max_tickets", 0) or 0
    logger.info("Jira API: fetching tickets (JQL: %s)%s", jql[:200] + ("..." if len(jql) > 200 else ""), f" | max {max_tickets}" if max_tickets > 0 else "")
    # Use new search/jql endpoint (old /rest/api/3/search returns 410 Gone)
    url = f"{base}/rest/api/3/search/jql"
    auth_str = f"{email}:{token}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_b64}",
    }
    total_yielded = 0
    page_num = 0
    next_page_token: str | None = None
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        while True:
            body: dict[str, Any] = {"jql": jql, "maxResults": SEARCH_PAGE_SIZE}
            if next_page_token:
                body["nextPageToken"] = next_page_token
            try:
                resp = client.post(url, headers=headers, json=body)
            except Exception as e:
                logger.error("Jira API request failed: %s", e)
                return
            if resp.status_code != 200:
                logger.error("Jira API error: %s %s", resp.status_code, resp.text[:500])
                return
            data = resp.json()
            # Support both legacy /search (issues) and new /search/jql (values) response shape
            issues = data.get("issues") or data.get("values") or []
            if not issues:
                logger.warning("No issues in page %s; response keys: %s", page_num, list(data.keys()))
            is_last = data.get("isLast", True)
            next_page_token = (data.get("nextPageToken") or "").strip() or None
            page_num += 1
            logger.info("Jira API: page %s, got %s issues, isLast=%s", page_num, len(issues), is_last)
            # New /search/jql returns minimal issues (only id); fetch full issue by id when needed
            if page_num == 1 and issues:
                first = issues[0] if isinstance(issues[0], dict) else None
                if first is not None and _is_minimal_issue(first):
                    logger.info("Jira API: search returns minimal issues (id only); fetching full issue per id")
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                if "issue" in issue and isinstance(issue["issue"], dict):
                    issue = issue["issue"]
                if _is_minimal_issue(issue):
                    full = _fetch_issue_by_id(client, base, headers, issue["id"])
                    if full is None:
                        continue
                    issue = full
                ticket = _issue_to_ticket(issue, settings)
                if ticket:
                    yield ticket
                    total_yielded += 1
                    if max_tickets > 0 and total_yielded >= max_tickets:
                        logger.info("Jira API: reached max tickets (%s), stopping fetch.", max_tickets)
                        break
            if max_tickets > 0 and total_yielded >= max_tickets:
                break
            if is_last or len(issues) == 0:
                break
            if not next_page_token and not is_last:
                logger.warning("Jira API: no nextPageToken but isLast=false; stopping pagination")
                break
    logger.info("Jira API: fetch complete. Total tickets yielded: %s", total_yielded)
