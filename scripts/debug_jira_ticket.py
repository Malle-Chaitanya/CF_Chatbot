"""List JiraChunk objects for one ticket. Usage: python scripts/debug_jira_ticket.py PRI-11092"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
backend_src = str(root / "backend" / "src")
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

from retrieval.weaviate_writer import get_weaviate_client
from weaviate.collections.classes.filters import Filter

ticket_key = sys.argv[1] if len(sys.argv) > 1 else "PRI-11092"
client = get_weaviate_client()
try:
    coll = client.collections.get("JiraChunk")
    r = coll.query.fetch_objects(filters=Filter.by_property("doc_id").equal(ticket_key), limit=50)
    for obj in sorted(r.objects, key=lambda o: (o.properties.get("chunk_index") or 0)):
        p = obj.properties
        print("--- chunk_index:", p.get("chunk_index"), "| section:", p.get("section"), "| type:", p.get("ticket_chunk_type"))
        print((p.get("content") or "")[:300])
        print()
finally:
    client.close()
