"""
Ingest Jira tickets into Weaviate (JiraChunk collection) iteratively, without duplicates.
Fetches from Jira API (.env: JIRA_*, JIRA_INGEST_PAST_MONTHS, JIRA_INGEST_MAX_TICKETS).
Filter: only tickets updated in the past N months (JIRA_INGEST_PAST_MONTHS=2). Max 1000 per run (JIRA_INGEST_MAX_TICKETS).
Tickets already in Weaviate are skipped. Always generates ticket summary via LLM.
Writes a run manifest to data/jira/ (JSON) with how many tickets, which tickets, and summary.

Usage (from repo root):
  set PYTHONPATH=backend\src
  python scripts/ingest_jira.py
  python scripts/ingest_jira.py --collection jira

Requires: init_schema.py --collection jira once before first ingestion.
"""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "backend" / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from config.collection_config import COLLECTION_REGISTRY
from config.settings import get_settings
from document_loaders.jira_api import fetch_jira_tickets_from_api
from chunking.jira_section_chunker import chunk_jira_ticket, build_summary_chunk_content
from embeddings.embedding_client import embed_texts
from retrieval.weaviate_writer import (
    write_chunks,
    doc_exists_in_collection,
    get_doc_updated,
    delete_chunks_by_doc_id,
    get_weaviate_client,
)
from ingestion.jira_summary import build_summary_context, generate_summary_from_context

# Log format: timestamp + level + message; easy to follow during ingestion
_LOG_FMT = "%(asctime)s [%(levelname)s] %(message)s"
_LOG_DATE = "%Y-%m-%d %H:%M:%S"
repo_root_for_log = Path(__file__).resolve().parent.parent
_log_dir = repo_root_for_log / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
_log_file = _log_dir / "jira_ingest.log"
logging.basicConfig(
    level=logging.INFO,
    format=_LOG_FMT,
    datefmt=_LOG_DATE,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_log_file, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

JIRA_KEY = "jira"
DATA_JIRA_DIR = "data/jira"


def _write_ingest_manifest(repo_root: Path, run_at: str, summary: dict, tickets: list[dict]) -> Path | None:
    """Write JSON manifest to data/jira/ (timestamped + latest). Returns path to timestamped file or None."""
    data_dir = repo_root / DATA_JIRA_DIR
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning("Could not create data/jira dir: %s", e)
        return None
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    payload = {
        "run_at": run_at,
        "collection": "JiraChunk",
        "summary": summary,
        "tickets": tickets,
    }
    timestamped_path = data_dir / f"jira_ingest_{ts}.json"
    latest_path = data_dir / "latest_ingest.json"
    try:
        with open(timestamped_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info("Ingest manifest written to %s and %s", timestamped_path, latest_path)
        return timestamped_path
    except OSError as e:
        logger.warning("Could not write ingest manifest: %s", e)
        return None


def main():
    parser = argparse.ArgumentParser(description="Ingest Jira tickets into Weaviate (from Jira API)")
    parser.add_argument(
        "--collection",
        default=JIRA_KEY,
        help="Collection key (default: jira). Uses JiraChunk class.",
    )
    args = parser.parse_args()
    key = args.collection.strip().lower()
    if key not in COLLECTION_REGISTRY:
        logger.error("Unknown collection: %s. Choose from: %s", args.collection, ", ".join(COLLECTION_REGISTRY))
        sys.exit(1)

    class_name, _ = COLLECTION_REGISTRY[key]
    settings = get_settings()
    if not getattr(settings, "enable_jira_source", True):
        logger.warning(
            "Jira ingestion skipped: ENABLE_JIRA_SOURCE is false. Set ENABLE_JIRA_SOURCE=true in .env to ingest Jira."
        )
        sys.exit(0)
    max_tickets = getattr(settings, "jira_ingest_max_tickets", 0) or 0
    past_months = getattr(settings, "jira_ingest_past_months", 0) or 0
    statuses = getattr(settings, "jira_ingest_statuses", "") or "Resolved,Closed"
    logger.info("Jira ingestion started. Source: Jira API | Collection: %s (%s) | Statuses: %s | Past months: %s | Max: %s", key, class_name, statuses, past_months, max_tickets or "all")
    logger.info("Logs also written to: %s", _log_file)

    total_chunks = 0
    ticket_num = 0
    skipped_unchanged = 0
    reindexed = 0
    new_ingested = 0
    ingested_records: list[dict] = []
    phase2_logged = False

    weaviate_client = get_weaviate_client()
    try:
        logger.info("=== Phase 1: Fetching tickets from Jira API ===")
        for ticket in fetch_jira_tickets_from_api():
            ticket_num += 1
            if max_tickets > 0 and ticket_num > max_tickets:
                logger.info("Reached max tickets to consider (%s), stopping.", max_tickets)
                break
            ticket_key = ticket.get("key") or ""
            jira_updated = (ticket.get("updated") or "").strip()
            was_reindex = False

            if doc_exists_in_collection(class_name, ticket_key, client=weaviate_client):
                stored_updated = get_doc_updated(class_name, ticket_key, client=weaviate_client) or ""
                # Re-ingest if Jira ticket was updated after our stored version (incremental sync)
                if (not stored_updated) or (jira_updated and jira_updated > stored_updated):
                    if max_tickets > 0 and (new_ingested + reindexed) >= max_tickets:
                        logger.info("[%s] Reached max tickets this run (%s), stopping.", ticket_num, max_tickets)
                        break
                    deleted = delete_chunks_by_doc_id(class_name, ticket_key, client=weaviate_client)
                    was_reindex = True
                    logger.info("[%s] Re-ingest %s (Jira updated %s > stored %s), deleted %s chunks", ticket_num, ticket_key, jira_updated or "?", stored_updated or "?", deleted)
                else:
                    skipped_unchanged += 1
                    logger.info("[%s] Skip %s (unchanged)", ticket_num, ticket_key)
                    continue
            else:
                if max_tickets > 0 and (new_ingested + reindexed) >= max_tickets:
                    logger.info("[%s] Reached max tickets this run (%s), stopping.", ticket_num, max_tickets)
                    break
                logger.info("[%s] Processing ticket: %s (new)", ticket_num, ticket_key)

            if not phase2_logged:
                logger.info("=== Phase 2: Processing tickets (chunk, summary from chunks, embed, write) ===")
                phase2_logged = True
            chunks = chunk_jira_ticket(ticket)
            if not chunks:
                logger.warning("[%s] No chunks for ticket %s, skipping.", ticket_num, ticket_key)
                continue
            summary_context = build_summary_context(chunks)
            llm_summary = generate_summary_from_context(summary_context, ticket_key=ticket_key) if summary_context else ""
            if llm_summary:
                ticket["summary"] = llm_summary
                ticket["doc_title"] = llm_summary
                new_summary_content = build_summary_chunk_content(ticket)
                chunks[0] = (new_summary_content, chunks[0][1])
                logger.info("[%s] Using LLM summary from chunks for %s", ticket_num, ticket_key)
            logger.info("[%s] Chunked into %s chunks, embedding ...", ticket_num, len(chunks))
            texts = [c[0] for c in chunks]
            vectors = embed_texts(texts)
            if len(vectors) != len(chunks):
                logger.error("Embedding count mismatch for ticket %s: %d vs %d", ticket_key, len(vectors), len(chunks))
                continue
            triples = [(text, meta, vec) for (text, meta), vec in zip(chunks, vectors)]
            logger.info("[%s] Writing %s chunks to Weaviate ...", ticket_num, len(triples))
            write_chunks(class_name, triples, client=weaviate_client)
            total_chunks += len(chunks)
            if was_reindex:
                reindexed += 1
            else:
                new_ingested += 1
            ingested_records.append({
                "ticket_key": ticket_key,
                "summary": (ticket.get("summary") or ticket.get("doc_title") or "")[:500],
                "updated": ticket.get("updated"),
                "combination": ticket.get("combination"),
                "status": ticket.get("status"),
                "chunk_count": len(chunks),
                "ingest_type": "reindexed" if was_reindex else "new",
            })
            logger.info(
                "[%s] Ingested %s (%s chunks). Processed: %s | Skipped: %s | Re-ingested: %s | New: %s",
                ticket_num, ticket_key, len(chunks), ticket_num, skipped_unchanged, reindexed, new_ingested,
            )
    finally:
        weaviate_client.close()

    if new_ingested == 0 and reindexed == 0:
        logger.warning("Jira ingestion finished with 0 new/reindexed tickets. Check .env and filters.")
    logger.info(
        "Jira ingestion complete. Processed: %s | Skipped (unchanged): %s | Re-ingested (updated): %s | New: %s | Total chunks: %s",
        ticket_num, skipped_unchanged, reindexed, new_ingested, total_chunks,
    )

    logger.info("=== Phase 3: Writing manifest ===")
    run_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "total_processed": ticket_num,
        "skipped_unchanged": skipped_unchanged,
        "reindexed": reindexed,
        "new_ingested": new_ingested,
        "total_chunks": total_chunks,
    }
    repo_root = Path(__file__).resolve().parent.parent
    _write_ingest_manifest(repo_root, run_at, summary, ingested_records)

    sys.exit(0)


if __name__ == "__main__":
    main()
