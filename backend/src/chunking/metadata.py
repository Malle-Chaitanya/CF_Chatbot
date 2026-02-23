"""Chunk key generation for Weaviate object UUIDs. Per-collection metadata lives in blog_metadata, sharepoint_metadata, etc."""

import uuid


def generate_chunk_key(doc_id: str, chunk_index: int) -> str:
    """Generate a unique, deterministic UUID for a chunk. Weaviate expects UUID format; avoids collisions."""
    safe_id = doc_id.replace(" ", "_").replace("/", "_").replace("\\", "_").strip()
    name = f"{safe_id}_{chunk_index}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))
