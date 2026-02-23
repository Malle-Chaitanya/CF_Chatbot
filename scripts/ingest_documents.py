"""
End-to-end ingestion: load docs from directory -> chunk -> embed -> write to Weaviate.
Usage: PYTHONPATH=backend\\src python scripts/ingest_documents.py --input-dir ./data/documents [--collection blog]
"""
import argparse
import logging
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "backend" / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from config.settings import get_settings
from config.collection_config import COLLECTION_REGISTRY
from document_loaders.directory_loader import load_documents_from_directory
from chunking.token_chunker import chunk_document
from chunking.blog_extraction import extract_blog_metadata
from embeddings.embedding_client import embed_texts
from retrieval.weaviate_writer import write_chunks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Ingest documents from a directory into Weaviate")
    parser.add_argument("--input-dir", required=True, help="Directory containing .txt/.md files")
    parser.add_argument(
        "--collection",
        default="blog",
        help="Collection key (e.g. blog, sharepoint). Default: blog",
    )
    args = parser.parse_args()
    key = args.collection.strip().lower()
    if key not in COLLECTION_REGISTRY:
        logger.error("Unknown collection: %s. Choose from: %s", args.collection, ", ".join(COLLECTION_REGISTRY))
        sys.exit(1)

    class_name, _ = COLLECTION_REGISTRY[key]
    input_dir = args.input_dir
    logger.info("Input dir: %s | Collection: %s (%s)", input_dir, key, class_name)

    # 1) Load documents
    docs = list(load_documents_from_directory(input_dir))
    num_docs = len(docs)
    if num_docs == 0:
        logger.warning("No .txt/.md documents found in %s", input_dir)
        sys.exit(0)

    # 2) Process per document: chunk -> embed -> write (keeps memory low; no single huge embed)
    total_chunks = 0
    for doc_id, doc_title, text in docs:
        chunks = chunk_document(text, doc_id, doc_title=doc_title, source_type=key)
        if not chunks:
            continue
        # For blog: extract migration source/destination/combination from name only; tags from name + content
        if key == "blog":
            extracted = extract_blog_metadata(doc_title, text)
            extra_meta = {
                "migration_source": extracted.migration_source,
                "migration_destination": extracted.migration_destination,
                "migration_combination": extracted.migration_combination,
                "tags": extracted.tags if extracted.tags else None,
            }
            extra_meta = {k: v for k, v in extra_meta.items() if v is not None}
            chunks = [(chunk_text, {**meta, **extra_meta}) for chunk_text, meta in chunks]
        texts = [c[0] for c in chunks]
        vectors = embed_texts(texts)
        if len(vectors) != len(chunks):
            logger.error("Embedding count mismatch for doc %s: %d vs %d", doc_id, len(vectors), len(chunks))
            sys.exit(1)
        triples = [(text, meta, vec) for (text, meta), vec in zip(chunks, vectors)]
        write_chunks(class_name, triples)
        total_chunks += len(chunks)
    logger.info("Documents: %d | Total chunks: %d", num_docs, total_chunks)

    logger.info("Ingestion complete. Exiting 0.")
    sys.exit(0)


if __name__ == "__main__":
    main()
