"""
Ingest blog posts from WordPress URL into Weaviate when INITIALIZE_VECTORSTORE and ENABLE_WEB_SOURCE are true.
Uses blog-specific chunk sizes from .env (BLOG_CHUNK_TARGET_TOKENS, BLOG_CHUNK_OVERLAP_TOKENS).
Processes one post at a time (iterative) to avoid loading all posts into memory.

Usage (from repo root):
  set PYTHONPATH=backend\src
  python scripts/ingest_blog_from_web.py

Requires: run init_schema.py --collection blog once before first ingestion.
"""
import logging
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "backend" / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from config.settings import get_settings
from config.collection_config import COLLECTION_REGISTRY
from document_loaders.web_blog_loader import iterate_posts_from_web
from chunking.blog_section_chunker import chunk_blog_by_sections
from chunking.blog_extraction import extract_blog_metadata
from embeddings.embedding_client import embed_texts
from retrieval.weaviate_writer import write_chunks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BLOG_KEY = "blog"


def main():
    settings = get_settings()
    if not settings.initialize_vectorstore or not settings.enable_web_source:
        logger.info(
            "Blog-from-web ingestion skipped: INITIALIZE_VECTORSTORE=%s, ENABLE_WEB_SOURCE=%s. Set both true to ingest.",
            settings.initialize_vectorstore,
            settings.enable_web_source,
        )
        sys.exit(0)

    if not (settings.web_source_url or "").strip():
        logger.warning("WEB_SOURCE_URL is empty; nothing to ingest.")
        sys.exit(0)

    class_name, _ = COLLECTION_REGISTRY[BLOG_KEY]
    logger.info("Blog ingestion from web: %s (collection %s)", settings.web_source_url, class_name)

    total_posts = 0
    total_chunks = 0
    post_num = 0
    for post in iterate_posts_from_web():
        post_num += 1
        doc_id, doc_title = post.doc_id, post.doc_title
        logger.info("[%s] Processing post: %s", post_num, doc_id)
        chunks = chunk_blog_by_sections(
            post.content_html or "",
            doc_id,
            doc_title,
            fallback_plain_text=post.text,
        )
        if not chunks:
            logger.warning("[%s] No chunks for post %s, skipping.", post_num, doc_id)
            continue
        logger.info("[%s] Chunked into %s chunks, embedding ...", post_num, len(chunks))
        extracted = extract_blog_metadata(doc_title, post.text)
        # Merge WordPress metadata (url, author, published_date, tags, category) with extraction (migration_*, tags)
        api_tags = list(post.tags) if post.tags else []
        extracted_tags = extracted.tags or []
        combined_tags = list(dict.fromkeys(api_tags + extracted_tags))  # dedupe, API first
        extra_meta = {
            "chunk_role": "content",
            "url": post.url,
            "author": post.author,
            "published_date": post.published_date,
            "category": post.category,
            "tags": combined_tags if combined_tags else None,
            "migration_source": extracted.migration_source,
            "migration_destination": extracted.migration_destination,
            "migration_combination": extracted.migration_combination,
        }
        extra_meta = {k: v for k, v in extra_meta.items() if v is not None}
        chunks = [(chunk_text, {**meta, **extra_meta}) for chunk_text, meta in chunks]
        texts = [c[0] for c in chunks]
        vectors = embed_texts(texts)
        if len(vectors) != len(chunks):
            logger.error("Embedding count mismatch for doc %s: %d vs %d", doc_id, len(vectors), len(chunks))
            continue
        triples = [(text, meta, vec) for (text, meta), vec in zip(chunks, vectors)]
        logger.info("[%s] Writing %s chunks to Weaviate ...", post_num, len(triples))
        write_chunks(class_name, triples)
        total_chunks += len(chunks)
        total_posts += 1
        logger.info("[%s] Ingested post %s (%s chunks). Total so far: %s posts, %s chunks.", post_num, doc_id, len(chunks), total_posts, total_chunks)

    if total_posts == 0:
        logger.warning("Blog-from-web ingestion finished with 0 posts. Check WEB_SOURCE_URL and that WordPress returns posts.")
    else:
        logger.info("Blog-from-web ingestion complete. Posts: %s | Total chunks: %s", total_posts, total_chunks)
    sys.exit(0)


if __name__ == "__main__":
    main()
