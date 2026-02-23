"""OpenAI embeddings: list of texts -> list of vectors. Used by ingestion and search."""

import logging
import time

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Default batch size to stay within API limits
EMBEDDING_BATCH_SIZE = 100
MAX_RETRIES = 4
INITIAL_BACKOFF = 2.0
# text-embedding-3-small (and similar) max 8192 tokens per input
EMBEDDING_MAX_TOKENS_PER_INPUT = 8191


def _truncate_to_max_tokens(text: str, max_tokens: int = EMBEDDING_MAX_TOKENS_PER_INPUT) -> str:
    """Truncate text to at most max_tokens so embedding API does not return 400."""
    if not text or max_tokens <= 0:
        return text
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        logger.warning(
            "Truncated embedding input from %s → %s tokens (retrieval may miss tail content)",
            len(tokens), max_tokens,
        )
        return enc.decode(tokens[:max_tokens])
    except Exception:
        # Fallback: ~4 chars per token
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        logger.warning(
            "Truncated embedding input from %s chars → %s chars (retrieval may miss tail content)",
            len(text), max_chars,
        )
        return text[:max_chars]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using OpenAI. Batches requests (e.g. up to 100 per request).
    Each text is truncated to EMBEDDING_MAX_TOKENS_PER_INPUT (8191) to avoid 400 errors.
    Returns one vector per text, each vector a list of floats.
    Uses retry with exponential backoff for 429 (rate limit) and 500 errors.
    """
    if not texts:
        return []
    settings = get_settings()
    client = __get_client()
    model = settings.embedding_model
    # Truncate each text to stay within model's per-input token limit
    truncated = [_truncate_to_max_tokens(t) for t in texts]
    all_vectors: list[list[float]] = []
    for i in range(0, len(truncated), EMBEDDING_BATCH_SIZE):
        batch = truncated[i : i + EMBEDDING_BATCH_SIZE]
        resp = _create_embeddings_with_retry(client, batch, model)
        # Preserve order by index
        ordered = [None] * len(batch)
        for e in resp.data:
            ordered[e.index] = e.embedding
        all_vectors.extend(ordered)
    return all_vectors


def _create_embeddings_with_retry(client, batch: list[str], model: str):
    """Call OpenAI embeddings with exponential backoff on 429 and 5xx."""
    from openai import APIStatusError

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return client.embeddings.create(input=batch, model=model)
        except APIStatusError as e:
            last_error = e
            status = getattr(e, "status_code", None) or getattr(e.response, "status_code", None)
            if status in (429, 500, 502, 503) and attempt < MAX_RETRIES - 1:
                backoff = INITIAL_BACKOFF ** attempt
                logger.warning("Embeddings API %s, retry %s/%s in %.1fs", status, attempt + 1, MAX_RETRIES, backoff)
                time.sleep(backoff)
            else:
                raise
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                backoff = INITIAL_BACKOFF ** attempt
                logger.warning("Embeddings error %s, retry %s/%s in %.1fs", e, attempt + 1, MAX_RETRIES, backoff)
                time.sleep(backoff)
            else:
                raise last_error or e
    raise last_error or RuntimeError("Embeddings failed after retries")


def __get_client():
    from openai import OpenAI
    return OpenAI(api_key=get_settings().openai_api_key)
