"""
Extract migration source, destination, combination and tags from blog post name (and content for tags).
If source/destination are not mentioned in the blog name, they are None; migration_combination = "source to destination" only when both are identified.
Tags are identified from known keywords in title and content so retrieval can use tags + semantic search.
"""

import re
from typing import NamedTuple

# Canonical display names; we match case-insensitively against title
KNOWN_PLATFORMS = [
    "Egnyte",
    "Box",
    "Google Drive",
    "Googledrive",
    "G Suite",
    "Dropbox",
    "SharePoint",
    "Share Point",
    "OneDrive",
    "One Drive",
    "Microsoft 365",
    "M365",
    "Office 365",
    "O365",
    "Salesforce",
    "Slack",
    "Teams",
    "Confluence",
    "Jira",
    "External Shares",
]
# For matching: sort by length descending so "Microsoft 365" matches before "Microsoft"
_platforms_lower = [(p.lower(), p) for p in sorted(KNOWN_PLATFORMS, key=len, reverse=True)]

# Tags: keywords that we detect in title or content to populate tags (for retrieval)
KNOWN_TAG_KEYWORDS = [
    "migration",
    "external shares",
    "content migration",
    "cloud migration",
    "file migration",
    "sharepoint",
    "onedrive",
    "microsoft 365",
    "m365",
    "egnyte",
    "box",
    "google drive",
    "dropbox",
    "slack",
    "teams",
    "confluence",
    "jira",
    "salesforce",
]
_tag_keywords_lower = [(t.lower(), t) for t in sorted(KNOWN_TAG_KEYWORDS, key=len, reverse=True)]


class ExtractedBlogMeta(NamedTuple):
    migration_source: str | None
    migration_destination: str | None
    migration_combination: str | None
    tags: list[str]


def _find_platform_in_text(text: str) -> str | None:
    """Return first matching canonical platform name in text (case-insensitive), or None."""
    lower = text.lower()
    for low, canonical in _platforms_lower:
        if low in lower:
            return canonical
    return None


def extract_from_blog_name(doc_title: str) -> tuple[str | None, str | None, str | None]:
    """
    Parse blog post name for migration source and destination.
    Returns (migration_source, migration_destination, migration_combination).
    If not identified from the blog name, all are None.
    migration_combination is "source to destination" only when both are found.
    """
    if not doc_title or not doc_title.strip():
        return None, None, None
    title = doc_title.strip()
    # Pattern: "X to Y" or "from X to Y" (to separates source from destination)
    to_match = re.search(r"(?:from\s+)?(.+?)\s+to\s+(.+)", title, re.IGNORECASE | re.DOTALL)
    if not to_match:
        return None, None, None
    before_to = to_match.group(1).strip()
    after_to = to_match.group(2).strip()
    source = _find_platform_in_text(before_to)
    destination = _find_platform_in_text(after_to)
    if source and destination and source != destination:
        combination = f"{source} to {destination}"
        return source, destination, combination
    return None, None, None


def extract_tags(doc_title: str, text: str) -> list[str]:
    """
    Identify tags from known keywords that appear in doc_title or text.
    Returns deduplicated list of tag strings (canonical form) for retrieval.
    """
    combined = f"{doc_title or ''} {text or ''}".lower()
    found: set[str] = set()
    for low, canonical in _tag_keywords_lower:
        if low in combined and canonical not in found:
            found.add(canonical)
    return sorted(found)


def extract_blog_metadata(doc_title: str, text: str = "") -> ExtractedBlogMeta:
    """
    Extract migration source, destination, combination from blog name only;
    extract tags from blog name and content.
    """
    source, destination, combination = extract_from_blog_name(doc_title)
    tags = extract_tags(doc_title, text)
    return ExtractedBlogMeta(
        migration_source=source,
        migration_destination=destination,
        migration_combination=combination,
        tags=tags,
    )
