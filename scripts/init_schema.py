"""
Initialize Weaviate schema (Phase 2).
Creates one Weaviate class per --collection with that collection's metadata schema.
Vector dimension from settings; no vectorizer (we supply vectors from OpenAI).

Usage:
  PYTHONPATH=backend\\src python scripts/init_schema.py --collection blog
  PYTHONPATH=backend\\src python scripts/init_schema.py --collection blog --vector-index flat

HNSW: Uses explicit config (distance_metric=cosine, ef_construction=128, max_connections=32).
For stable HNSW use Weaviate >= 1.29 (docker-compose) and a full clean reset after upgrade;
see docs/TROUBLESHOOTING.md.

If vector search returns 0 results, try:
  1. Use --vector-index flat (quick fix), or
  2. Upgrade Weaviate to 1.29+, remove volume, recreate schema with hnsw, re-ingest.
"""
import argparse
import importlib
import sys
import types
from pathlib import Path
from typing import Union, get_args, get_origin
from urllib.parse import urlparse

# When run from repo root with PYTHONPATH=backend\src, config/chunking resolve
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root / "backend" / "src") not in sys.path:
    sys.path.insert(0, str(_repo_root / "backend" / "src"))

import weaviate
from weaviate.classes.config import Configure, DataType, Property, VectorDistances

from config.settings import get_settings
from config.collection_config import COLLECTION_REGISTRY


def _weaviate_properties_from_model(metadata_model):
    """Build Weaviate Property list from a Pydantic metadata model (field name -> DataType).
    Correctly maps Optional[int], Optional[str], list[str], bool, and plain types.
    """
    props = []
    for name, field_info in metadata_model.model_fields.items():
        ann = field_info.annotation
        origin = get_origin(ann)
        args = get_args(ann) if ann is not type(None) else ()

        # Optional[T] is Union[T, None] or (Python 3.10+) T | None (UnionType)
        is_optional = (
            (origin is Union and len(args) == 2 and type(None) in args)
            or (getattr(types, "UnionType", None) is not None and origin is types.UnionType and type(None) in args)
        )
        if is_optional and args:
            real_type = next(a for a in args if a is not type(None))
        else:
            real_type = ann

        real_origin = get_origin(real_type)
        real_args = get_args(real_type) if real_type is not type(None) else ()

        if real_origin is list:
            if real_args and real_args[0] is str:
                props.append(Property(name=name, data_type=DataType.TEXT_ARRAY))
            else:
                props.append(Property(name=name, data_type=DataType.TEXT))
        elif real_type is str:
            props.append(Property(name=name, data_type=DataType.TEXT))
        elif real_type is int:
            props.append(Property(name=name, data_type=DataType.INT))
        elif real_type is bool:
            props.append(Property(name=name, data_type=DataType.BOOL))
        else:
            props.append(Property(name=name, data_type=DataType.TEXT))
    return props


def _connect_client(weaviate_url: str):
    """Connect to Weaviate using weaviate_url (e.g. http://localhost:8081)."""
    parsed = urlparse(weaviate_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8080
    # Default gRPC port often offset from HTTP (e.g. 50051 or 50052)
    grpc_port = 50051 if port == 8080 else 50052
    return weaviate.connect_to_local(host=host, port=port, grpc_port=grpc_port)


def main():
    parser = argparse.ArgumentParser(description="Create Weaviate class for a collection")
    parser.add_argument("--collection", required=True, help="Collection key: blog, sharepoint, jira, transcripts, email, sharepoint2")
    parser.add_argument(
        "--vector-index",
        choices=("hnsw", "flat"),
        default="hnsw",
        help="Vector index type: hnsw (default, faster search) or flat (brute-force, use if hnsw returns 0 results)",
    )
    args = parser.parse_args()
    key = args.collection.strip().lower()
    if key not in COLLECTION_REGISTRY:
        print(f"Unknown collection: {args.collection}. Choose from: {', '.join(COLLECTION_REGISTRY)}")
        sys.exit(1)

    class_name, metadata_path = COLLECTION_REGISTRY[key]
    module_path, attr = metadata_path.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    metadata_model = getattr(mod, attr)

    settings = get_settings()
    dim = settings.embedding_dimension

    if args.vector_index == "flat":
        index_config = Configure.VectorIndex.flat()
    else:
        # Explicit HNSW config for stable search (avoids default ambiguities on Weaviate 1.27–1.29).
        index_config = Configure.VectorIndex.hnsw(
            distance_metric=VectorDistances.COSINE,
            ef_construction=128,
            max_connections=32,
        )

    client = _connect_client(settings.weaviate_url)
    try:
        if client.collections.exists(class_name):
            print(f"Collection '{class_name}' already exists.")
            return
        properties = _weaviate_properties_from_model(metadata_model)
        client.collections.create(
            name=class_name,
            description=f"Chunks for {key}",
            properties=properties,
            vector_config=Configure.Vectors.self_provided(
                vector_index_config=index_config
            ),
        )
        print(f"Created collection '{class_name}' (vector index: {args.vector_index}, dimension from first insert: {dim}).")
    finally:
        client.close()


if __name__ == "__main__":
    main()
