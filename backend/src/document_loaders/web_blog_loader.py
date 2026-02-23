"""
Load blog posts from WordPress REST API (WEB_SOURCE_URL) with pagination.
Yields BlogPost (doc_id, doc_title, text + url, author, published_date, tags, category).
Uses _embed to resolve author and taxonomy names. No change to text extraction (no re-ingestion).
"""
import logging
import re
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Page size used for "last page" check when not in URL
DEFAULT_PAGE_SIZE = 100


@dataclass(frozen=True)
class BlogPost:
    """One post with content and WordPress metadata for BlogChunkMetadata."""

    doc_id: str
    doc_title: str
    text: str
    content_html: str = ""
    url: str | None = None
    author: str | None = None
    published_date: str | None = None
    tags: tuple[str, ...] = ()
    category: str | None = None


def _strip_html(html: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _url_with_page(base_url: str, page: int) -> str:
    """Add or replace page parameter in URL."""
    parsed = urlparse(base_url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["page"] = [str(page)]
    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def _ensure_embed_and_per_page(base_url: str) -> str:
    """Ensure URL has _embed and per_page so responses include author/terms and page size is explicit."""
    parsed = urlparse(base_url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "per_page" not in query:
        query["per_page"] = [str(DEFAULT_PAGE_SIZE)]
    if "_embed" not in query:
        query["_embed"] = ["1"]
    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def _get_page_size(base_url: str) -> int:
    """Return per_page from URL or DEFAULT_PAGE_SIZE for last-page check."""
    parsed = urlparse(base_url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    vals = query.get("per_page", [])
    if not vals:
        return DEFAULT_PAGE_SIZE
    try:
        return max(1, int(vals[0]))
    except (ValueError, TypeError):
        return DEFAULT_PAGE_SIZE


def _parse_embedded_author(post: dict) -> str | None:
    """Extract author name from post _embedded."""
    emb = post.get("_embedded") or {}
    authors = emb.get("author")
    if not authors or not isinstance(authors, list):
        return None
    first = authors[0] if isinstance(authors[0], dict) else None
    if not first:
        return None
    return first.get("name") or None


def _parse_embedded_terms(post: dict) -> tuple[list[str], str | None]:
    """Extract (tag_names, first_category_name) from post _embedded wp:term."""
    tag_names: list[str] = []
    category_name: str | None = None
    emb = post.get("_embedded") or {}
    term_groups = emb.get("wp:term")
    if not term_groups or not isinstance(term_groups, list):
        return (tag_names, category_name)
    for group in term_groups:
        if not isinstance(group, list):
            continue
        for t in group:
            if not isinstance(t, dict):
                continue
            tax = t.get("taxonomy")
            name = t.get("name")
            if not name:
                continue
            if tax == "post_tag":
                tag_names.append(str(name))
            elif tax == "category" and category_name is None:
                category_name = str(name)
    return (tag_names, category_name)


def _parse_post(post: dict) -> BlogPost | None:
    """Build BlogPost from WordPress post dict. Returns None if doc_id would be empty."""
    post_id = post.get("id")
    slug = (post.get("slug") or "").strip()
    if slug:
        doc_id = slug
    elif post_id is not None:
        doc_id = str(post_id)
    else:
        doc_id = ""

    title_obj = post.get("title") or {}
    content_obj = post.get("content") or {}
    title = title_obj.get("rendered", "") if isinstance(title_obj, dict) else str(title_obj)
    content_raw = content_obj.get("rendered", "") if isinstance(content_obj, dict) else str(content_obj)
    doc_title = _strip_html(title) or slug or doc_id
    text = _strip_html(content_raw)

    if not doc_id:
        return None

    link = post.get("link")
    url = str(link).strip() if link else None
    date_val = post.get("date")
    published_date = str(date_val).strip() if date_val else None

    author = _parse_embedded_author(post)
    tag_list, category = _parse_embedded_terms(post)

    return BlogPost(
        doc_id=doc_id,
        doc_title=doc_title,
        text=text,
        content_html=content_raw or "",
        url=url or None,
        author=author,
        published_date=published_date,
        tags=tuple(tag_list),
        category=category,
    )


def load_posts_from_web() -> list[BlogPost]:
    """
    Fetch blog posts from WordPress API (settings: web_source_url, web_start_page, web_max_pages).
    Uses _embed for author and terms. Returns list of BlogPost.
    """
    settings = get_settings()
    base_url = (settings.web_source_url or "").strip()
    if not base_url:
        logger.warning("WEB_SOURCE_URL is empty; no posts to load.")
        return []
    base_url = _ensure_embed_and_per_page(base_url)
    page_size = _get_page_size(base_url)
    start = settings.web_start_page
    max_pages = settings.web_max_pages
    out: list[BlogPost] = []
    with httpx.Client(timeout=60.0) as client:
        for page_num in range(start, start + max_pages):
            url = _url_with_page(base_url, page_num)
            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.warning("Web blog fetch failed for page %s: %s", page_num, e)
                break
            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                break
            for post in data:
                if not isinstance(post, dict):
                    continue
                parsed = _parse_post(post)
                if parsed is not None:
                    out.append(parsed)
            if len(data) < page_size:
                break
    return out


def iterate_posts_from_web():
    """
    Iterator over BlogPost from WordPress API.
    Fetches one page at a time and yields each post for iterative ingestion. Uses _embed for metadata.
    """
    settings = get_settings()
    base_url = (settings.web_source_url or "").strip()
    if not base_url:
        return
    base_url = _ensure_embed_and_per_page(base_url)
    page_size = _get_page_size(base_url)
    start = settings.web_start_page
    max_pages = settings.web_max_pages
    with httpx.Client(timeout=60.0) as client:
        for page_num in range(start, start + max_pages):
            url = _url_with_page(base_url, page_num)
            logger.info("Fetching page %s ...", page_num)
            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.warning("Web blog fetch failed for page %s: %s", page_num, e)
                break
            data = resp.json()
            if not isinstance(data, list) or len(data) == 0:
                logger.info("Page %s: no posts (end of list or empty).", page_num)
                break
            logger.info("Page %s: got %s posts, yielding for ingestion.", page_num, len(data))
            for post in data:
                if not isinstance(post, dict):
                    continue
                parsed = _parse_post(post)
                if parsed is not None:
                    yield parsed
            if len(data) < page_size:
                break
