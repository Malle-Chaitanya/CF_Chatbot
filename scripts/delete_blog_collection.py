"""
Delete the BlogChunk collection from Weaviate (e.g. before recreating schema or after vector index issues).

Run from repo root (venv activated): python scripts/delete_blog_collection.py

When vector search returns 0 results (Weaviate 1.27 + HNSW): use flat index when recreating.
  1. python scripts/delete_blog_collection.py
  2. PYTHONPATH=backend\\src python scripts/init_schema.py --collection blog --vector-index flat
  3. python scripts/ingest_blog_from_web.py
See docs/TROUBLESHOOTING.md for full steps.
"""
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_backend_src = str(_repo_root / "backend" / "src")
if _backend_src not in sys.path:
    sys.path.insert(0, _backend_src)

from urllib.parse import urlparse

import weaviate

from config.settings import get_settings

COLLECTION_NAME = "BlogChunk"


def main():
    s = get_settings()
    p = urlparse(s.weaviate_url)
    host = p.hostname or "localhost"
    port = p.port or 8080
    grpc = 50051 if port == 8080 else 50052

    client = weaviate.connect_to_local(host=host, port=port, grpc_port=grpc)
    try:
        if client.collections.exists(COLLECTION_NAME):
            client.collections.delete(COLLECTION_NAME)
            print(f"Deleted collection '{COLLECTION_NAME}'.")
        else:
            print(f"Collection '{COLLECTION_NAME}' does not exist.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
