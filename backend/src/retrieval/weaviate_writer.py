"""Batch insert chunks (content + metadata + vector) into Weaviate. Uses generate_chunk_key for UUID."""

import logging
from typing import Any
from urllib.parse import urlparse

import weaviate
from weaviate.collections.classes.data import DataObject
from weaviate.collections.classes.filters import Filter

from config.settings import get_settings
from chunking.metadata import generate_chunk_key

logger = logging.getLogger(__name__)

BATCH_SIZE = 80


def _connect(weaviate_url: str):
    parsed = urlparse(weaviate_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8080
    grpc_port = 50051 if port == 8080 else 50052
    return weaviate.connect_to_local(host=host, port=port, grpc_port=grpc_port)


def get_weaviate_client() -> Any:
    """Return a connected Weaviate client. Caller must close it when done (e.g. in a try/finally)."""
    settings = get_settings()
    return _connect(settings.weaviate_url)


def doc_exists_in_collection(collection_name: str, doc_id: str, client: Any = None) -> bool:
    """Return True if any chunk with this doc_id exists in the collection (avoids duplicate ingest)."""
    if not doc_id or not collection_name:
        return False
    own_client = client is None
    if own_client:
        settings = get_settings()
        client = _connect(settings.weaviate_url)
    try:
        coll = client.collections.get(collection_name)
        response = coll.query.fetch_objects(
            filters=Filter.by_property("doc_id").equal(doc_id),
            limit=1,
        )
        return len(response.objects) > 0
    finally:
        if own_client:
            client.close()


def get_doc_updated(collection_name: str, doc_id: str, client: Any = None) -> str | None:
    """Return the stored 'updated' value from any chunk with this doc_id, or None if not found."""
    if not doc_id or not collection_name:
        return None
    own_client = client is None
    if own_client:
        settings = get_settings()
        client = _connect(settings.weaviate_url)
    try:
        coll = client.collections.get(collection_name)
        response = coll.query.fetch_objects(
            filters=Filter.by_property("doc_id").equal(doc_id),
            limit=1,
        )
        if not response.objects:
            return None
        props = response.objects[0].properties
        return props.get("updated") if isinstance(props, dict) else None
    finally:
        if own_client:
            client.close()


def delete_chunks_by_doc_id(collection_name: str, doc_id: str, client: Any = None) -> int:
    """Delete all chunks with this doc_id. Returns number of objects deleted (matches)."""
    if not doc_id or not collection_name:
        return 0
    own_client = client is None
    if own_client:
        settings = get_settings()
        client = _connect(settings.weaviate_url)
    try:
        coll = client.collections.get(collection_name)
        result = coll.data.delete_many(where=Filter.by_property("doc_id").equal(doc_id))
        return getattr(result, "matches", 0) or 0
    finally:
        if own_client:
            client.close()


# Numeric fields: coerce to int so Weaviate INT schema gets integers (no float64).
_INT_PROPS = ("start_char", "end_char", "token_count", "chunk_index", "total_chunks", "comment_index")


def _metadata_to_properties(metadata: dict, chunk_text: str) -> dict:
    """Build Weaviate properties dict from metadata; exclude reserved names; omit None."""
    out = dict(metadata)
    out["content"] = chunk_text
    for key in _INT_PROPS:
        if key in out and out[key] is not None:
            val = out[key]
            if isinstance(val, (int, float)):
                out[key] = int(val)
    return {k: v for k, v in out.items() if k not in ("id", "vector") and v is not None}


def write_chunks(
    collection_name: str,
    chunks: list[tuple[str, dict | object, list[float]]],
    client: Any = None,
) -> None:
    """
    Insert chunks into Weaviate in batches.
    Each element of chunks is (chunk_text, metadata, vector).
    metadata can be a dict or Pydantic model with doc_id and chunk_index (used for UUID).
    """
    if not chunks:
        return
    # Normalize metadata to dict; exclude_none=True so Weaviate doesn't get fields not in schema
    normalized: list[tuple[str, dict, list[float]]] = []
    for chunk_text, meta, vector in chunks:
        if hasattr(meta, "model_dump"):
            meta = meta.model_dump(exclude_none=True)
        else:
            meta = {k: v for k, v in dict(meta).items() if v is not None}
        normalized.append((chunk_text, meta, vector))

    own_client = client is None
    if own_client:
        settings = get_settings()
        client = _connect(settings.weaviate_url)
    try:
        coll = client.collections.get(collection_name)
        total = 0
        for i in range(0, len(normalized), BATCH_SIZE):
            batch = normalized[i : i + BATCH_SIZE]
            objects = []
            for chunk_text, metadata, vector in batch:
                doc_id = metadata.get("doc_id")
                chunk_index = metadata.get("chunk_index")
                if doc_id is None or chunk_index is None:
                    raise ValueError("metadata must have doc_id and chunk_index")
                uuid_str = generate_chunk_key(doc_id, chunk_index)
                props = _metadata_to_properties(metadata, chunk_text)
                objects.append(
                    DataObject(properties=props, uuid=uuid_str, vector=vector)
                )
            result = coll.data.insert_many(objects)
            total += len(objects)
            if result.errors:
                for err in result.errors:
                    logger.error("Weaviate insert error: %s", err)
        num_batches = (len(normalized) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info("Weaviate: wrote %d chunks (%d batches) to %s", total, num_batches, collection_name)
    finally:
        if own_client:
            client.close()
