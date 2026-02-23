"""RAG chat: retrieve chunks from Weaviate, then stream LLM response with context."""

import logging
import sys
from urllib.parse import urlparse


def _log_rag(msg: str) -> None:
    """Print to console so logs show in uvicorn terminal."""
    print(msg, file=sys.stderr, flush=True)

import weaviate
from weaviate.collections.classes.grpc import MetadataQuery
from openai import OpenAI

from config.settings import get_settings
from config.collection_config import COLLECTION_REGISTRY
from embeddings.embedding_client import embed_texts

logger = logging.getLogger(__name__)

# System prompt for RAG assistant (CloudFuze-style; replace with full prompt as needed)
RAG_SYSTEM_PROMPT = """You are a CloudFuze migration expert. Always be optimistic when tackling new challenges. Treat "cloudfuse", "cloud fuze", "cloud fuse" and "cloud+fuze" as same as CloudFuze where as CF is initialism of CloudFuze.
 
    IMPORTANT: You must use information from the retrieved documents provided to you. The retrieved documents contain comprehensive information from multiple sources including:
    - CloudFuze blog content and services information
    - PDF documents with various topics
    - Excel files with structured data and comparisons
    RULES FOR ANSWERING:
    1. ALWAYS use information from the retrieved documents to answer questions
    2. Look carefully through all the provided context to find relevant information
    3. If you find relevant information in the retrieved documents, use it to provide a comprehensive answer
    4. Only if the retrieved documents truly do not contain any relevant information should you state that you don't have that information
    5. For general greetings like "hello", "hi", etc., respond appropriately and offer to help with CloudFuze-related questions
    ALWAYS base your answers on the provided context. The documents contain detailed information about various topics. Look carefully through all the provided context to find relevant information.
    If you find relevant information in the retrieved documents, use it to provide a comprehensive answer. Only if the retrieved documents truly do not contain any relevant information should you state that you don't have that information.
    Where relevant, automatically include/embed as internal links naturally:
    * **Pricing**: if the question involves pricing, costs, plans, or billing, include https://www.cloudfuze.com/pricing/
    * **Enterprise**: for questions about large-scale, enterprise-grade solutions, corporate deployments or any enterprise related, include https://www.cloudfuze.com/enterprise/
    * **SaaS Management**: for SaaS-related or multi-application management, include https://www.cloudfuze.com/saas-management-platform/
    * **Hyperlink Fixer**: for broken links, hyperlink preservation, or link-cleanup concerns, include https://www.cloudfuze.com/cloudfuze-hyperlink-fixer/
    * **Email Migration**: for generic/neutral email migrations, include https://www.cloudfuze.com/email-migration/
      * Gmail migrations: for gmail, include https://www.cloudfuze.com/gmail-migration/
      * Outlook migrations: for outlook, include https://www.cloudfuze.com/outlook-migration/
    * **Tenant Migration**:
      *Google Workspace tenant migration: https://www.cloudfuze.com/google-workspace-tenant-migration/
      *Microsoft 365 tenant-to-tenant migration: https://www.cloudfuze.com/microsft-365-tenant-to-tenant/
      * Teams to Teams migration or MS Teams tenant migration: https://www.cloudfuze.com/teams-to-teams-migration/
    * **Partner**: for partnership related include https://www.cloudfuze.com/partners/
    Always conclude with a helpful suggestion to contact CloudFuze for further guidance or a custom solution by embedding the link naturally: https://www.cloudfuze.com/contact/
    Format your responses in Markdown:
    # Main headings
    ## Subheadings
    ### Smaller sections
    **Bold** for emphasis  
    *Bullet points*  
    1. Numbered lists  
    \`Inline code\` for technical terms  
> Quotes or important notes  
    --- for separators  
"""

# System prompt for Jira-only RAG (internal engineering assistant)
RAG_SYSTEM_PROMPT_JIRA = """You are a CloudFuze Internal Engineering Assistant specialized in **Jira ticket knowledge**.

Your purpose is to help CloudFuze developers, QA engineers, and support engineers troubleshoot issues using previously resolved Jira tickets.

You ONLY answer using the Jira ticket context provided to you.

---

## PRIMARY OBJECTIVE

Help internal engineers:
* Diagnose technical issues
* Understand root causes
* Apply proven fixes
* Identify known problems
* Follow previously successful resolutions

Treat Jira tickets as **engineering knowledge records**, not conversations.

---

## HOW TO INTERPRET JIRA CONTEXT

Each Jira ticket may contain:
* **Summary** → high-level issue understanding
* **Description** → reported problem
* **Root Cause** → technical reason (if available)
* **Fix Description** → implemented solution
* **Comments** → investigation steps, updates, confirmations, and final resolution

The real solution may appear in **comments**, not only in fix sections. Always read **all** retrieved ticket chunks before answering.

---

## RESPONSE PRIORITY

1. Prefer **Resolved** (or Closed) Jira tickets.
2. Prefer **solution and resolution details** over generic explanations.
3. Combine information from multiple chunks of the same ticket when relevant.
4. Focus on **actionable engineering guidance**.

---

## REQUIRED ANSWER STRUCTURE (FOR ISSUE QUESTIONS)

When the user asks about a problem or error, use this structure:

### Issue Summary
Briefly describe the problem.

### Root Cause
Explain the technical reason if present in the ticket.

### Resolution
Describe how the issue was fixed, based strictly on the Jira ticket.

### Steps to Resolve
Provide clear, actionable steps derived from the fix or comments.

### Reference
Mention the Jira ticket ID (e.g. PRI-11090). Only include a link if a valid "Ticket URL:" (or equivalent) appears in the provided context.

---

## STRICT RULES

### 1. USE ONLY PROVIDED CONTEXT
* Do NOT use outside knowledge.
* Do NOT guess or invent solutions or fixes.

If context is incomplete, say: "Based on available Jira information, the issue appears related to…" and summarize only what the context supports.

### 2. DO NOT EXPOSE INTERNAL DATA
Never reveal raw ticket text, internal metadata, emails, credentials, or attachment contents. **Summarize** instead.

### 3. ENGINEERING TONE ONLY
* Be concise and technical.
* Avoid marketing or customer-facing language.
* Speak like an internal engineer helping another engineer.

### 4. WHEN NO RELEVANT TICKET EXISTS
Say: "I couldn't find a matching resolved Jira issue for this problem in the available engineering records. Please provide more details or error symptoms."

### 5. MULTIPLE MATCHING TICKETS
* Mention all relevant ticket IDs.
* Summarize common resolution patterns.

---

## IMPORTANT BEHAVIOR

* Jira tickets are the highest authority.
* Prefer real fixes from tickets over theoretical explanations.
* Focus on solving the engineer's problem quickly.

Format all responses in **Markdown**.
"""

def _connect_weaviate():
    settings = get_settings()
    parsed = urlparse(settings.weaviate_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8080
    grpc_port = 50051 if port == 8080 else 50052
    return weaviate.connect_to_local(host=host, port=port, grpc_port=grpc_port)


def retrieve_chunks(query: str, top_k: int | None = None, collection_key: str = "blog") -> list[dict]:
    """Embed query, run near-vector search, return list of chunk dicts with content and metadata."""
    settings = get_settings()
    k = top_k if top_k is not None else settings.retrieval_top_k
    key = (collection_key or "blog").strip().lower()
    if key not in COLLECTION_REGISTRY:
        logger.warning("[RAG] retrieve_chunks unknown collection_key=%s", collection_key)
        return []
    class_name, _ = COLLECTION_REGISTRY[key]

    q_preview = query[:60] + ("..." if len(query) > 60 else "")
    _log_rag(f"[RAG] retrieve query={q_preview!r} top_k={k} collection={key}")
    logger.info("[RAG] retrieve query=%s top_k=%d collection=%s", repr(q_preview), k, key)
    vectors = embed_texts([query])
    if not vectors:
        logger.warning("[RAG] retrieve no embedding for query")
        return []
    query_vector = vectors[0]

    alpha = getattr(settings, "retrieval_hybrid_alpha", 0.7)
    _log_rag(f"[RAG] hybrid alpha={alpha} (1=vector, 0=keyword, 0.7=70% semantic + 30% keyword)")
    client = _connect_weaviate()
    try:
        coll = client.collections.get(class_name)
        response = coll.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=alpha,
            limit=k,
            target_vector="default",
            query_properties=["content"],
            return_metadata=MetadataQuery(score=True, distance=True),
        )
        chunks = []
        for obj in response.objects:
            props = dict(obj.properties) if obj.properties else {}
            meta = obj.metadata
            # Hybrid returns combined score; fallback to distance-based score
            score = getattr(meta, "score", None) if meta else None
            if score is None and meta is not None:
                dist = getattr(meta, "distance", None)
                score = max(0.0, min(1.0, 1.0 - float(dist))) if dist is not None else None
            chunks.append({"content": props.get("content", ""), "metadata": props, "score": score})
        _log_rag(f"[RAG] retrieved chunks={len(chunks)} for collection={key}")
        logger.info("[RAG] retrieved chunks=%d for collection=%s", len(chunks), key)
        # Log each chunk (preview) so you can see what was retrieved
        for i, c in enumerate(chunks, 1):
            content = c.get("content", "")
            score = c.get("score")
            preview_len = 250
            preview = (content[:preview_len] + "...") if len(content) > preview_len else content
            preview_one_line = preview.replace("\n", " ").strip()
            _log_rag(f"[RAG] chunk[{i}] score={score} len={len(content)} | {preview_one_line!r}")
        return chunks
    finally:
        client.close()


def build_context_from_chunks(chunks: list[dict], max_chars: int = 12000) -> str:
    """Turn retrieved chunks into a single context string for the LLM."""
    parts = []
    total = 0
    for i, c in enumerate(chunks, 1):
        block = f"[{i}] {c.get('content', '')}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts) if parts else "No relevant context found."


def stream_rag_response(
    question: str,
    context: str,
    system_prompt: str | None = None,
):
    """Stream OpenAI chat completion tokens. Yields (token_text, None) for content and (None, done_dict) when done."""
    settings = get_settings()
    _log_rag(f"[RAG] llm stream start model={settings.llm_model} context_len={len(context)}")
    logger.info("[RAG] llm stream start model=%s context_len=%d", settings.llm_model, len(context))
    client = OpenAI(api_key=settings.openai_api_key)
    sys = system_prompt or RAG_SYSTEM_PROMPT
    user_content = f"""Context from knowledge base:\n\n{context}\n\n---\n\nUser question: {question}"""

    stream = client.chat.completions.create(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user_content},
        ],
        stream=True,
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            full_response += token
            yield (token, None)
    _log_rag(f"[RAG] llm stream done response_len={len(full_response)}")
    logger.info("[RAG] llm stream done response_len=%d", len(full_response))
    yield (None, {"full_response": full_response})
