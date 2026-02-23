"""
Check if Jira ingestion is ready to run.
Run from repo root: PYTHONPATH=backend\\src python scripts/check_jira_ingest_ready.py
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
backend_src = repo_root / "backend" / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

def main():
    errors = []
    warnings = []

    # 1. Settings
    try:
        from config.settings import get_settings
        from config.collection_config import COLLECTION_REGISTRY
    except Exception as e:
        print("FAIL: Could not load config:", e)
        return 1
    s = get_settings()

    if not (s.jira_server or "").strip():
        errors.append("JIRA_SERVER is empty in .env")
    else:
        print("  JIRA_SERVER: set")
    if not (s.jira_email or "").strip():
        errors.append("JIRA_EMAIL is empty in .env")
    else:
        print("  JIRA_EMAIL: set")
    if not (s.jira_api_token or "").strip():
        errors.append("JIRA_API_TOKEN is empty in .env")
    else:
        print("  JIRA_API_TOKEN: set")
    if not (s.jira_project_keys or "").strip():
        errors.append("JIRA_PROJECT_KEYS is empty in .env")
    else:
        print("  JIRA_PROJECT_KEYS:", s.jira_project_keys.strip())
    if not getattr(s, "enable_jira_source", True):
        errors.append("ENABLE_JIRA_SOURCE is false; set true to ingest")
    else:
        print("  ENABLE_JIRA_SOURCE: true")

    if not (s.openai_api_key or "").strip():
        warnings.append("OPENAI_API_KEY is empty; LLM summary will be skipped (ticket heading used)")
    else:
        print("  OPENAI_API_KEY: set (for LLM summary)")
    if not (s.weaviate_url or "").strip():
        errors.append("WEAVIATE_URL is empty")
    else:
        print("  WEAVIATE_URL:", s.weaviate_url)

    if "jira" not in COLLECTION_REGISTRY:
        errors.append("jira not in COLLECTION_REGISTRY")
    else:
        print("  COLLECTION_REGISTRY[jira]: OK")

    # 2. Imports (loader, chunker, embed, writer, summary)
    try:
        from document_loaders.jira_api import fetch_jira_tickets_from_api
        from chunking.jira_section_chunker import chunk_jira_ticket
        from embeddings.embedding_client import embed_texts
        from retrieval.weaviate_writer import write_chunks, doc_exists_in_collection, get_doc_updated, delete_chunks_by_doc_id
        from ingestion.jira_summary import generate_ticket_summary
        print("  Imports (jira_api, chunker, embed, writer, summary): OK")
    except Exception as e:
        errors.append("Import failed: " + str(e))

    # 3. Weaviate + JiraChunk schema (optional; may fail if Weaviate not running)
    try:
        from retrieval.weaviate_writer import _connect
        jira_class = COLLECTION_REGISTRY["jira"][0]
        client = _connect(s.weaviate_url)
        try:
            coll = client.collections.get(jira_class)
            print("  Weaviate %s collection: exists" % jira_class)
        except Exception as e:
            warnings.append("Weaviate %s collection missing or unreachable: " % jira_class + str(e)
                            + " -> Run: PYTHONPATH=backend\\src python scripts/init_schema.py --collection jira")
        finally:
            client.close()
    except Exception as e:
        warnings.append("Weaviate connection failed (is it running?): " + str(e))

    # Summary
    print()
    if errors:
        print("NOT READY (fix these):")
        for e in errors:
            print("  -", e)
    if warnings:
        print("Warnings:")
        for w in warnings:
            print("  -", w)
    if not errors:
        print("READY to ingest. Run: PYTHONPATH=backend\\src python scripts/ingest_jira.py")
        return 0
    return 1


if __name__ == "__main__":
    print("=== Jira ingestion readiness ===\n")
    sys.exit(main())
