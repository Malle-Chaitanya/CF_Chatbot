"""Load .txt and .md files from a directory. Yields (doc_id, doc_title, text)."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_documents_from_directory(dir_path: str):
    """
    Scan directory for .txt and .md files; yield (doc_id, doc_title, text).
    doc_id: stable unique id (relative path with / normalized to _).
    Skip binary/empty files; UTF-8 only; on decode error log and skip.
    """
    root = Path(dir_path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (".txt", ".md"):
            continue
        try:
            raw = path.read_bytes()
        except OSError as e:
            logger.warning("Skip %s: %s", path, e)
            continue
        if not raw.strip():
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.warning("Skip %s (decode error): %s", path, e)
            continue
        # doc_id: relative path, normalized for Weaviate (no / or \ in id)
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path.name
        doc_id = str(rel).replace("\\", "_").replace("/", "_").strip()
        doc_title = path.stem or path.name
        yield doc_id, doc_title, text
