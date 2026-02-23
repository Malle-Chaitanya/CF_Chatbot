"""
Diagnose why search returns [] while list_blog_chunks shows data.
Checks: (0) collection vector config, (1) objects have vectors,
        (2) vector dimension, (3) gRPC near_vector, (4) query embedding,
        (5) REST GraphQL nearVector (to see if server returns results).

Usage (from repo root, venv activated):
  set PYTHONPATH=backend\src
  python scripts/check_weaviate_vectors.py
"""
import json
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_backend_src = str(_repo_root / "backend" / "src")
if _backend_src not in sys.path:
    sys.path.insert(0, _backend_src)

from urllib.parse import urlparse

import weaviate
from weaviate.collections.classes.grpc import MetadataQuery

from config.settings import get_settings
from embeddings.embedding_client import embed_texts

COLLECTION_NAME = "BlogChunk"


def _connect():
    s = get_settings()
    p = urlparse(s.weaviate_url)
    host = p.hostname or "localhost"
    port = p.port or 8080
    grpc = 50051 if port == 8080 else 50052
    return weaviate.connect_to_local(host=host, port=port, grpc_port=grpc)


def _rest_near_vector(base_url: str, class_name: str, vector: list[float], limit: int = 5) -> list:
    """Run nearVector via REST GraphQL. Returns list of objects or [] on error."""
    import urllib.request
    url = f"{base_url.rstrip('/')}/v1/graphql"
    query = """
    query($vec: [Float]!) {
      Get {
        %s(nearVector: { vector: $vec }, limit: %d) {
          doc_id
          content
          _additional { distance }
        }
      }
    }
    """ % (class_name, limit)
    payload = json.dumps({"query": query, "variables": {"vec": vector}}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"   REST request failed: {e}")
        return []
    get_data = data.get("data", {}).get("Get", {})
    return get_data.get(class_name, [])


def main():
    settings = get_settings()
    expected_dim = settings.embedding_dimension
    print(f"Config: WEAVIATE_URL={settings.weaviate_url}")
    print(f"       EMBEDDING_MODEL={settings.embedding_model}  EMBEDDING_DIMENSION={expected_dim}\n")

    client = _connect()
    try:
        if not client.collections.exists(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist.")
            sys.exit(1)

        coll = client.collections.get(COLLECTION_NAME)

        # 0) Collection vector config (actual vector name in schema)
        print("0. Collection vector config (schema) ...")
        try:
            import urllib.request
            schema_url = f"{settings.weaviate_url.rstrip('/')}/v1/schema/{COLLECTION_NAME}"
            req = urllib.request.Request(schema_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                schema = json.loads(resp.read().decode())
            vec_cfg = schema.get("vectorConfig") or schema.get("vectorIndexConfig")
            if vec_cfg:
                print(f"   Vector config keys: {list(vec_cfg.keys()) if isinstance(vec_cfg, dict) else vec_cfg}")
            else:
                print("   (single default vector; no named vectorConfig)")
        except Exception as e:
            print(f"   Could not fetch schema: {e}")
        print()

        # 1) Fetch a few objects WITH vector
        print("1. Fetching 3 objects with include_vector=True ...")
        response = coll.query.fetch_objects(limit=3, include_vector=True)
        objects = list(response.objects)
        if not objects:
            print("   No objects returned. Collection may be empty or fetch failed.\n")
            sys.exit(1)
        print(f"   Got {len(objects)} object(s).\n")

        # 2) Check vector presence and dimension
        print("2. Checking stored vectors ...")
        for i, obj in enumerate(objects):
            vec = obj.vector if hasattr(obj, "vector") else getattr(obj, "vector", None)
            if vec is None:
                print(f"   Object {i + 1}: NO VECTOR (vector is None).")
            else:
                dim = len(vec.get("default", vec) if isinstance(vec, dict) else vec)
                print(f"   Object {i + 1}: vector length = {dim}")
                if dim != expected_dim:
                    print(f"   WARNING: dimension {dim} != config embedding_dimension {expected_dim}. Search will fail.")
        print()

        # Get first object's vector for Weaviate near_vector (client returns dict e.g. {"default": [floats]})
        stored_vector: list[float] = []  # for REST fallback
        first = objects[0]
        vec_raw = getattr(first, "vector", None)
        if vec_raw is None:
            print("3. Skipping near_vector test: no vector on first object.\n")
        else:
            if isinstance(vec_raw, dict):
                query_vec = vec_raw.get("default") or (list(vec_raw.values())[0] if vec_raw else None)
            else:
                query_vec = vec_raw
            if query_vec is None:
                query_vec = []
            if not isinstance(query_vec, list):
                query_vec = list(query_vec) if hasattr(query_vec, "__iter__") else []
            if not query_vec or not isinstance(query_vec[0], (int, float)):
                print("3. Skipping near_vector test: could not get a valid vector from first object.\n")
            else:
                stored_vector = list(query_vec)
                print(f"3. near_vector search using first object's vector (dim={len(query_vec)}) ...")
                r3 = coll.query.near_vector(
                    near_vector=query_vec,
                    limit=5,
                    return_metadata=MetadataQuery(distance=True),
                    target_vector="default",
                )
                n3 = len(list(r3.objects))
                print(f"   Results: {n3} object(s).")
                if n3 == 0:
                    print("   FAIL: near_vector with stored vector returned 0 results. Vector index or Weaviate config may be wrong.")
                else:
                    print("   OK: Vector search returns results when using a stored vector.\n")
        print()

        # 4) Search with query embedding (same as API)
        print("4. near_vector search using query embedding (like the API) ...")
        vectors = embed_texts(["microsoft 365 migration"])
        query_embedding: list[float] = []
        n4 = 0
        if not vectors:
            print("   Embedding failed (check OPENAI_API_KEY and model).\n")
        else:
            query_embedding = vectors[0]
            print(f"   Query vector dimension: {len(query_embedding)}")
            if len(query_embedding) != expected_dim:
                print(f"   WARNING: query dim {len(query_embedding)} != config {expected_dim}.")
            r4 = coll.query.near_vector(
                near_vector=query_embedding,
                limit=5,
                return_metadata=MetadataQuery(distance=True),
                target_vector="default",
            )
            n4 = len(list(r4.objects))
            print(f"   Results: {n4} object(s).")
            if n4 == 0:
                print("   FAIL: Search returns 0 chunks (gRPC).")
            else:
                print("   OK: Search returns results.")
        # 5) Same search via REST GraphQL (bypasses gRPC)
        print("\n5. REST GraphQL nearVector ...")
        rest_vec = query_embedding if query_embedding else stored_vector
        rest_results = _rest_near_vector(settings.weaviate_url, COLLECTION_NAME, rest_vec, 5)
        print(f"   Results: {len(rest_results)} object(s).")
        if not rest_vec:
            print("   (no vector available for REST test)")
        elif len(rest_results) > 0 and n4 == 0:
            print("   --> REST returns results but gRPC does not: use REST for search or fix gRPC/Weaviate.")
        elif len(rest_results) == 0 and n4 == 0:
            print("   --> REST also returns 0: vector index may not be used for search; check Weaviate server/version.")
        print("\nDone.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
