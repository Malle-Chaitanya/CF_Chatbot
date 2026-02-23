"""
Debug script: list how chunks are stored for each blog post in Weaviate.

Usage (from repo root, with venv activated or PYTHONPATH=backend\\src):
  python scripts/list_blog_chunks.py
      Summary: chunk count per post (doc_id | url | N chunks).

  python scripts/list_blog_chunks.py --detail N
      Summary + full BLOG METADATA and CHUNKS for the first N posts (sorted by doc_id).

  python scripts/list_blog_chunks.py --doc-id SLUG
  python scripts/list_blog_chunks.py --url "https://..."
      One post: BLOG METADATA (doc_id, url, doc_title, author, tags, migration_*, etc.)
                and CHUNKS (chunk_index, heading_path, token_count, content preview).

  python scripts/list_blog_chunks.py --doc-id SLUG --full-content
      Same as above but print full chunk content (no preview truncation).

  python scripts/list_blog_chunks.py --no-preview
      Omit content preview when showing one post.

Requires: Weaviate running and BlogChunk collection populated (e.g. after ingest_blog_from_web.py).
"""
import argparse
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_backend_src = str(_repo_root / "backend" / "src")
if _backend_src not in sys.path:
    sys.path.insert(0, _backend_src)

from urllib.parse import urlparse

import weaviate
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.grpc import Sort

from config.settings import get_settings

COLLECTION_NAME = "BlogChunk"
CONTENT_PREVIEW_LEN = 200

# Blog metadata keys (same for all chunks of a post); exclude chunk-specific/content.
BLOG_META_KEYS = (
    "doc_id",
    "url",
    "doc_title",
    "author",
    "published_date",
    "category",
    "tags",
    "migration_source",
    "migration_destination",
    "migration_combination",
    "migration_type",
    "source_type",
    "chunk_role",
)


def _connect():
    s = get_settings()
    p = urlparse(s.weaviate_url)
    host = p.hostname or "localhost"
    port = p.port or 8080
    grpc = 50051 if port == 8080 else 50052
    return weaviate.connect_to_local(host=host, port=port, grpc_port=grpc)


def _props(obj):
    return dict(obj.properties) if obj.properties else {}


def _print_blog_metadata_and_chunks(objects, *, content_preview_len=CONTENT_PREVIEW_LEN, full_content=False):
    """Print a clear BLOG METADATA section and CHUNKS section from a list of chunk objects."""
    if not objects:
        return
    props_list = [_props(obj) for obj in objects]
    first = props_list[0]

    print("  " + "=" * 76)
    print("  BLOG METADATA")
    print("  " + "-" * 76)
    for key in BLOG_META_KEYS:
        val = first.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            val = ", ".join(str(x) for x in val) if val else ""
        print(f"    {key}: {val}")
    print("  " + "-" * 76)
    print("  CHUNKS")
    print("  " + "-" * 76)
    for i, props in enumerate(props_list):
        idx = props.get("chunk_index", "?")
        heading = props.get("heading_path") or "(no heading)"
        tokens = props.get("token_count")
        token_str = f" ({tokens} tokens)" if tokens is not None else ""
        print(f"    [{i + 1}] chunk_index={idx}  heading_path={heading!r}{token_str}")
        content = (props.get("content") or "").strip()
        if content and (full_content or content_preview_len > 0):
            if full_content:
                for line in content.splitlines():
                    print(f"        {line}")
            else:
                preview = (content[:content_preview_len] + "…") if len(content) > content_preview_len else content
                preview_1line = preview.replace("\n", " ")
                print(f"        content: {preview_1line}")
        print()
    print("  " + "=" * 76)


def run_summary(client, detail_n=0, content_preview_len=CONTENT_PREVIEW_LEN, full_content=False):
    """Iterate all BlogChunk objects and print chunk count per post. If detail_n > 0, show full metadata + chunks for first N posts."""
    coll = client.collections.get(COLLECTION_NAME)
    by_doc: dict[str, dict] = {}
    total = 0
    for obj in coll.iterator(include_vector=False):
        total += 1
        props = _props(obj)
        doc_id = props.get("doc_id") or "(no doc_id)"
        url = props.get("url") or ""
        by_doc.setdefault(doc_id, {"url": url, "chunks": []})
        if not by_doc[doc_id]["url"] and url:
            by_doc[doc_id]["url"] = url
        by_doc[doc_id]["chunks"].append(
            {
                "chunk_index": props.get("chunk_index"),
                "heading_path": props.get("heading_path"),
            }
        )
    print(f"Total chunks in {COLLECTION_NAME}: {total}\n")
    print("Per-post summary (doc_id | url | chunk count)")
    print("-" * 80)
    sorted_doc_ids = sorted(by_doc.keys())
    for doc_id in sorted_doc_ids:
        info = by_doc[doc_id]
        count = len(info["chunks"])
        url = info["url"] or "(no url)"
        print(f"  {doc_id} | {url} | {count} chunks")
    print("-" * 80)
    print(f"Posts: {len(by_doc)} | Chunks: {total}")

    if detail_n > 0:
        print(f"\n\nDetail for first {detail_n} post(s):\n")
        for doc_id in sorted_doc_ids[:detail_n]:
            response = coll.query.fetch_objects(
                filters=Filter.by_property("doc_id").equal(doc_id),
                sort=Sort.by_property("chunk_index", ascending=True),
                limit=1000,
            )
            objs = list(response.objects)
            print(f"  POST: doc_id = {doc_id!r}")
            _print_blog_metadata_and_chunks(
                objs,
                content_preview_len=content_preview_len,
                full_content=full_content,
            )
            print()


def run_single_post(client, *, doc_id=None, url=None, verbose=True, content_preview_len=CONTENT_PREVIEW_LEN, full_content=False):
    """Fetch chunks for one post (by doc_id or url), sort by chunk_index, print BLOG METADATA + CHUNKS."""
    coll = client.collections.get(COLLECTION_NAME)
    if doc_id is not None:
        flt = Filter.by_property("doc_id").equal(doc_id)
        label = f"doc_id={doc_id!r}"
    else:
        flt = Filter.by_property("url").equal(url)
        label = f"url={url!r}"

    response = coll.query.fetch_objects(
        filters=flt,
        sort=Sort.by_property("chunk_index", ascending=True),
        limit=1000,
    )
    objects = list(response.objects)
    print(f"Post ({label}): {len(objects)} chunks\n")
    if not objects:
        print("  (none)")
        return
    _print_blog_metadata_and_chunks(
        objects,
        content_preview_len=content_preview_len if verbose else 0,
        full_content=full_content and verbose,
    )


def main():
    parser = argparse.ArgumentParser(
        description="List how blog chunks are stored in Weaviate (summary or single post)."
    )
    parser.add_argument(
        "--doc-id",
        metavar="SLUG",
        help="Show chunks only for this doc_id (post slug).",
    )
    parser.add_argument(
        "--url",
        metavar="URL",
        help="Show chunks only for this blog URL.",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="When showing one post, do not print content preview.",
    )
    parser.add_argument(
        "--detail",
        type=int,
        metavar="N",
        default=0,
        help="In summary mode: also print full BLOG METADATA + CHUNKS for the first N posts.",
    )
    parser.add_argument(
        "--full-content",
        action="store_true",
        help="Print full chunk content (not just preview). Use with --doc-id/--url or --detail.",
    )
    parser.add_argument(
        "--preview-len",
        type=int,
        metavar="LEN",
        default=CONTENT_PREVIEW_LEN,
        help=f"Max characters per chunk content preview (default {CONTENT_PREVIEW_LEN}).",
    )
    args = parser.parse_args()
    if args.doc_id and args.url:
        parser.error("Use only one of --doc-id or --url")
        sys.exit(1)

    client = _connect()
    try:
        if not client.collections.exists(COLLECTION_NAME):
            print(f"Collection '{COLLECTION_NAME}' does not exist. Run init_schema.py --collection blog and ingest.")
            sys.exit(1)
        preview_len = 0 if args.no_preview else args.preview_len
        if args.doc_id:
            run_single_post(
                client,
                doc_id=args.doc_id,
                verbose=not args.no_preview,
                content_preview_len=preview_len,
                full_content=args.full_content,
            )
        elif args.url:
            run_single_post(
                client,
                url=args.url,
                verbose=not args.no_preview,
                content_preview_len=preview_len,
                full_content=args.full_content,
            )
        else:
            run_summary(
                client,
                detail_n=args.detail,
                content_preview_len=args.preview_len,
                full_content=args.full_content,
            )
    finally:
        client.close()


if __name__ == "__main__":
    main()
