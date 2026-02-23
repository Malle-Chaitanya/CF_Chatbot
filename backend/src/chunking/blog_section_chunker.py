"""
Heading-aware chunking for blog posts. Parses HTML into sections (H2 / H2 > H3), then
token-chunks within each section and attaches heading_path to metadata. Improves retrieval
for step-based and migration blogs.
"""
import logging

from bs4 import BeautifulSoup

from chunking.token_chunker import chunk_document

logger = logging.getLogger(__name__)

# Blog source_type for chunk_document (uses BLOG_CHUNK_* settings)
BLOG_SOURCE_TYPE = "blog"


def parse_blog_sections(html: str) -> list[tuple[str | None, str]]:
    """
    Parse blog HTML into (heading_path, section_text) sections using H2 and H3.
    - H2 starts a new top-level section; heading_path = H2 text.
    - H3 starts a subsection; heading_path = "H2 > H3".
    - Content before first heading goes under "Introduction".
    - Removes script/style. Returns [] if no usable content.
    """
    if not html or not html.strip():
        return []
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    sections: list[tuple[str | None, str]] = []
    current_heading: str | None = "Introduction"
    current_h2: str | None = None
    current_h3: str | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_text, current_heading
        if current_text:
            section_text = " ".join(current_text).strip()
            if section_text:
                sections.append((current_heading, section_text))
            current_text = []

    for element in soup.find_all(["h2", "h3", "p", "li"]):
        name = element.name
        text = element.get_text(separator=" ", strip=True)
        if not text:
            continue
        if name == "h2":
            flush()
            current_h2 = text
            current_h3 = None
            current_heading = current_h2
            current_text = []
        elif name == "h3":
            flush()
            current_h3 = text
            current_heading = f"{current_h2} > {current_h3}" if current_h2 else current_h3
            current_text = []
        else:
            current_text.append(text)

    flush()

    if not sections:
        # No block elements found; treat whole body as one section
        body_text = soup.get_text(separator=" ", strip=True)
        if body_text:
            sections.append(("Introduction", body_text))

    return sections


def chunk_blog_by_sections(
    html: str,
    doc_id: str,
    doc_title: str | None,
    *,
    fallback_plain_text: str = "",
) -> list[tuple[str, dict]]:
    """
    Heading-aware chunking for blog: parse HTML into sections, token-chunk each section,
    attach heading_path and global chunk_index. Uses blog chunk sizes from settings.

    If html is empty or parse yields no sections, falls back to chunk_document(fallback_plain_text)
    with heading_path=None.
    """
    logger.info("Parsing sections (HTML length: %s chars) ...", len(html or ""))
    sections = parse_blog_sections(html)
    logger.info("Parsed %s sections.", len(sections))

    if not sections:
        chunks = chunk_document(
            fallback_plain_text,
            doc_id,
            doc_title=doc_title,
            source_type=BLOG_SOURCE_TYPE,
        )
        for chunk_text, meta in chunks:
            meta["heading_path"] = None
        return chunks

    result: list[tuple[str, dict]] = []
    global_index = 0
    for section_idx, (heading_path, section_text) in enumerate(sections, 1):
        if not section_text.strip():
            continue
        logger.info("Chunking section %s/%s (%s chars) ...", section_idx, len(sections), len(section_text))
        section_chunks = chunk_document(
            section_text,
            doc_id,
            doc_title=doc_title,
            source_type=BLOG_SOURCE_TYPE,
        )
        for chunk_text, meta in section_chunks:
            # Copy so we don't mutate chunker output; set heading_path and global index
            meta = dict(meta)
            meta["heading_path"] = heading_path
            meta["chunk_index"] = global_index
            result.append((chunk_text, meta))
            global_index += 1

    return result
