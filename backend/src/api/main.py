"""FastAPI RAG API: hybrid search (vector + BM25) and POST /chat/stream (RAG + SSE).
Also provides minimal auth for the CloudFuze-style frontend."""

import json
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field

from config.collection_config import COLLECTION_REGISTRY
from config.settings import get_settings
from api.chat_service import (
    retrieve_chunks,
    build_context_from_chunks,
    stream_rag_response,
    RAG_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT_JIRA,
)
from retrieval.weaviate_writer import get_weaviate_client

logging.basicConfig(level=logging.INFO)
# Ensure [CHAT]/[RAG] logs appear in console when running under uvicorn
_api_logger = logging.getLogger("api")
_api_logger.setLevel(logging.INFO)
if not _api_logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s:     %(name)s - %(message)s"))
    _api_logger.addHandler(_h)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Lifespan: run Weaviate startup log on start."""
    _log_weaviate_startup()
    yield
    # shutdown: nothing to do


app = FastAPI(title="RAG Search API", version="0.1.0", lifespan=_lifespan)

# CORS so frontend (e.g. localhost:3000) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _log_weaviate_startup():
    """On server start: log whether Weaviate is reachable and document count per collection."""
    settings = get_settings()
    logger.info("[STARTUP] Checking Weaviate at %s ...", settings.weaviate_url)
    print(f"[STARTUP] Weaviate URL: {settings.weaviate_url}", file=sys.stderr, flush=True)
    client = None
    try:
        client = get_weaviate_client()
        logger.info("[STARTUP] Weaviate: connected.")
        print("[STARTUP] Weaviate: connected.", file=sys.stderr, flush=True)
        total_docs = 0
        for key, (class_name, _) in COLLECTION_REGISTRY.items():
            try:
                coll = client.collections.get(class_name)
                result = coll.aggregate.over_all(total_count=True)
                count = result.total_count or 0
            except Exception as e:
                err_str = str(e).lower()
                # Collection not created yet in Weaviate schema — expected, not a warning
                if "could not find class" in err_str or "in schema" in err_str:
                    count = 0
                    logger.info("[STARTUP]   %s (%s): not in schema (0 documents)", key, class_name)
                    print(f"[STARTUP]   {key} ({class_name}): not in schema (0 documents)", file=sys.stderr, flush=True)
                else:
                    logger.warning("[STARTUP] Collection %s (%s): error: %s", key, class_name, e)
                    count = 0
                    print(f"[STARTUP]   {key} ({class_name}): 0 documents (error)", file=sys.stderr, flush=True)
                total_docs += count
                continue
            total_docs += count
            logger.info("[STARTUP]   %s (%s): %d documents", key, class_name, count)
            print(f"[STARTUP]   {key} ({class_name}): {count} documents", file=sys.stderr, flush=True)
        logger.info("[STARTUP] Total documents across all collections: %d", total_docs)
        print(f"[STARTUP] Total documents across all collections: {total_docs}", file=sys.stderr, flush=True)
    except Exception as e:
        logger.error("[STARTUP] Weaviate: NOT connected. %s", e)
        print(f"[STARTUP] Weaviate: NOT connected. {e}", file=sys.stderr, flush=True)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


class SearchRequest(BaseModel):
    query: str = Field(..., description="User question")
    top_k: int | None = Field(default=None, ge=1, le=100, description="Number of chunks to return")
    collection: str | None = Field(default=None, description="Collection key (e.g. blog). Default: blog")


class ChunkResult(BaseModel):
    content: str
    metadata: dict
    score: float | None = None


class SearchResponse(BaseModel):
    chunks: list[ChunkResult]


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    """Hybrid search: vector (semantic) + BM25 (keyword) on the collection, return top-k chunks with scores."""
    raw = retrieve_chunks(req.query, top_k=req.top_k, collection_key=req.collection or "blog")
    chunks = [ChunkResult(content=c["content"], metadata=c["metadata"], score=c.get("score")) for c in raw]
    return SearchResponse(chunks=chunks)


# --- Chat stream (SSE) for frontend ---

class ChatStreamRequest(BaseModel):
    question: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session id from frontend")
    ui_mode: str | None = None
    refine_action: str | None = None
    last_email_content: str | None = None
    debug_context: bool = Field(default=False, description="If True, log full RAG context to rag_context_debug.log for this request (Option B)")


def _sse_line(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _log_chat(msg: str) -> None:
    """Print to console so logs show in uvicorn terminal (logging can be suppressed in worker)."""
    print(msg, file=sys.stderr, flush=True)


def _write_context_for_grounding(context: str, question: str, session_id: str) -> None:
    """Write full context to rag_context_debug.log for manual grounding checks."""
    try:
        # Log file next to repo root (main.py is backend/src/api/main.py -> parents[3] = repo root)
        repo_root = Path(__file__).resolve().parents[3]
        log_file = repo_root / "rag_context_debug.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"session_id={session_id}\n")
            f.write(f"question={question!r}\n")
            f.write(f"context_len={len(context)}\n")
            f.write("-" * 80 + "\n")
            f.write(context)
            f.write("\n")
        _log_chat(f"[CHAT] full context written to {log_file} ({len(context)} chars)")
    except Exception as e:
        _log_chat(f"[CHAT] failed to write context log: {e}")


async def _chat_stream_generator(question: str, session_id: str, debug_context: bool = False):
    """Yield SSE events: status, thinking_complete, token, done."""
    try:
        q_preview = question[:80] + ("..." if len(question) > 80 else "")
        _log_chat(f"[CHAT] request session_id={session_id} question={q_preview!r}")
        logger.info("[CHAT] request session_id=%s question=%s", session_id, repr(q_preview))
        yield _sse_line({"type": "status", "status": "thinking", "message": "Searching knowledge base..."})
        chunks = retrieve_chunks(question, collection_key="jira")
        context = build_context_from_chunks(chunks)
        _log_chat(f"[CHAT] retrieved chunks={len(chunks)} context_len={len(context)}")
        logger.info("[CHAT] retrieved chunks=%d context_len=%d", len(chunks), len(context))
        # Option A: LOG_FULL_CONTEXT=true logs every request; Option B: debug_context=true logs this request
        if debug_context or get_settings().log_full_context:
            _write_context_for_grounding(context, question, session_id)
        yield _sse_line({"type": "status", "status": "thinking", "message": "Generating answer..."})
        yield _sse_line({"type": "thinking_complete"})

        full_response = ""
        for token, done_payload in stream_rag_response(question, context, RAG_SYSTEM_PROMPT_JIRA):
            if token:
                full_response += token
                yield _sse_line({"type": "token", "token": token})
            if done_payload is not None:
                trace_id = str(uuid.uuid4())
                final_text = done_payload.get("full_response", full_response)
                _log_chat(f"[CHAT] response session_id={session_id} trace_id={trace_id} response_len={len(final_text)}")
                logger.info("[CHAT] response session_id=%s trace_id=%s response_len=%d", session_id, trace_id, len(final_text))
                yield _sse_line({
                    "type": "done",
                    "full_response": final_text,
                    "trace_id": trace_id,
                    "intent": None,
                    "recommended_questions": [],
                })
                return
    except Exception as e:
        logger.exception("Chat stream error")
        yield _sse_line({"type": "error", "error": str(e)})


@app.post("/chat/stream")
async def chat_stream(req: ChatStreamRequest, request: Request):
    """RAG chat: retrieve chunks, then stream LLM response as SSE (frontend-compatible).
    Add ?debug_context=1 or body debug_context: true to log full context to rag_context_debug.log."""
    debug = req.debug_context or request.query_params.get("debug_context", "").lower() in ("1", "true", "yes")
    return StreamingResponse(
        _chat_stream_generator(req.question, req.session_id, debug_context=debug),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# --- Auth: Microsoft OAuth (uses MICROSOFT_* from .env) and dev-login fallback ---

@app.get("/auth/config")
def auth_config():
    """OAuth config for frontend. Returns Microsoft client_id and tenant from .env."""
    settings = get_settings()
    client_id = settings.microsoft_client_id or "rag-dev"
    tenant = settings.microsoft_tenant or "common"
    return {"client_id": client_id, "tenant": tenant}


class MicrosoftCallbackRequest(BaseModel):
    code: str
    redirect_uri: str
    code_verifier: str


@app.post("/auth/microsoft/callback")
async def auth_microsoft_callback(request: MicrosoftCallbackRequest, response: Response):
    """Exchange Microsoft OAuth code for tokens, get user from Graph, set session cookie."""
    import uuid
    import httpx
    settings = get_settings()
    if not settings.microsoft_client_id or not settings.microsoft_client_secret:
        raise HTTPException(status_code=503, detail="Microsoft OAuth not configured (set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET in .env)")
    tenant = settings.microsoft_tenant or "common"
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    token_data = {
        "client_id": settings.microsoft_client_id,
        "client_secret": settings.microsoft_client_secret,
        "code": request.code,
        "redirect_uri": request.redirect_uri,
        "code_verifier": request.code_verifier,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, data=token_data, timeout=30.0)
        if token_resp.status_code != 200:
            logger.warning("Microsoft token exchange failed: %s %s", token_resp.status_code, token_resp.text[:200])
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        token_info = token_resp.json()
        access_token = token_info.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        graph_resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        if graph_resp.status_code != 200:
            logger.warning("Microsoft Graph me failed: %s %s", graph_resp.status_code, graph_resp.text[:200])
            raise HTTPException(status_code=400, detail="Failed to get user information")
        user_info = graph_resp.json()
    user_email = (user_info.get("mail") or user_info.get("userPrincipalName") or "").strip()
    if not user_email:
        raise HTTPException(status_code=400, detail="Unable to retrieve user email from Microsoft")
    if settings.microsoft_allowed_domain:
        domain = settings.microsoft_allowed_domain.strip().lower()
        if not user_email.lower().endswith("@" + domain):
            raise HTTPException(status_code=403, detail=f"Only {domain} accounts are allowed")
    user_id = user_email.lower()
    user_name = (user_info.get("displayName") or "").strip() or user_email.split("@")[0].replace(".", " ").title()
    session_id = str(uuid.uuid4())
    response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="lax", max_age=86400 * 7, path="/")
    return {"user_id": user_id, "name": user_name, "email": user_email}


class DevLoginResponse(BaseModel):
    user_id: str
    name: str
    email: str


@app.post("/auth/dev-login")
def auth_dev_login(response: Response):
    """Set a session cookie and return user for dev. Use with frontend dev-login page."""
    user_id = "rag-dev-user"
    name = "RAG Dev User"
    email = "dev@rag.local"
    # Set cookie so frontend considers session valid (optional; frontend mainly uses localStorage user)
    response.set_cookie(key="session_id", value=user_id, httponly=True, samesite="lax", max_age=86400 * 7)
    return DevLoginResponse(user_id=user_id, name=name, email=email)


@app.post("/auth/logout")
def auth_logout(response: Response):
    """Clear session cookie."""
    response.delete_cookie("session_id")
    return {"ok": True}


# --- No-op / minimal endpoints so frontend does not 404 ---

class SessionSaveBody(BaseModel):
    session_id: str | None = None
    title: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    message_count: int | None = None
    messages: list | None = None


@app.post("/chat/sessions/save")
def chat_sessions_save(body: SessionSaveBody | None = None):
    """Frontend persists sessions in localStorage; backend no-op for RAG-only mode."""
    return {"ok": True}


@app.get("/api/suggested-questions/")
def suggested_questions(limit: int = 4):
    """Return suggested questions for empty state. Optional static list."""
    suggestions = [
        {"id": "1", "question_text": "What migration options does CloudFuze offer?"},
        {"id": "2", "question_text": "How do I migrate from Google Workspace to Microsoft 365?"},
        {"id": "3", "question_text": "What is cloud data migration?"},
        {"id": "4", "question_text": "How long does a typical migration take?"},
    ]
    return suggestions[: max(1, min(limit, 20))]


@app.get("/user/profile")
def user_profile():
    """Frontend checks onboarding; RAG mode needs no onboarding."""
    return {"needs_onboarding": False}


@app.get("/chat/sessions/all")
def chat_sessions_all(limit: int = 15):
    """No server-side session list in RAG mode; frontend uses localStorage."""
    return []


@app.get("/chat/history/{user_id}")
def chat_history(user_id: str):
    """No server-side history in RAG mode."""
    return {"messages": []}
