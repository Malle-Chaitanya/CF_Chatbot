"""
Token-based chunking with tiktoken (OpenAI tokenizer).
Output: list of (chunk_text, metadata_dict) with doc_id, chunk_index, start_char, end_char, etc.
"""

import logging

import tiktoken

from config.settings import get_settings

logger = logging.getLogger(__name__)


def chunk_document(
    text: str,
    doc_id: str,
    *,
    doc_title: str | None = None,
    source_type: str = "document",
) -> list[tuple[str, dict]]:
    """
    Split document text into token-sized chunks with overlap.
    Returns list of (chunk_text, metadata) where metadata is a dict with at least
    doc_id, chunk_index; also start_char, end_char, doc_title, source_type, content, token_count.
    """
    if not text or not text.strip():
        return []
    settings = get_settings()
    if source_type == "blog":
        target = settings.blog_chunk_target_tokens
        overlap = settings.blog_chunk_overlap_tokens
    else:
        target = settings.chunk_target_tokens
        overlap = settings.chunk_overlap_tokens
    if overlap >= target:
        logger.warning(
            "chunk_overlap_tokens (%s) >= target (%s); clamping overlap to target-1 to avoid infinite loop.",
            overlap,
            target,
        )
        overlap = max(0, target - 1)
    logger.info("Loading tokenizer (%s) ...", getattr(settings, "embedding_model", "?"))
    enc = _get_encoding()
    logger.info("Tokenizing %s chars ...", len(text))
    tokens = enc.encode(text)
    if not tokens:
        return []

    chunks: list[tuple[str, dict]] = []
    start = 0
    chunk_index = 0
    while start < len(tokens):
        end = min(start + target, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        # Prefer breaking at whitespace: find last space in chunk and trim end if we're mid-word
        if end < len(tokens) and chunk_text and not chunk_text[-1].isspace():
            last_space = chunk_text.rfind(" ")
            if last_space > target // 2:
                chunk_text = chunk_text[: last_space + 1].rstrip()
                chunk_tokens = enc.encode(chunk_text)
                end = start + len(chunk_tokens)
        # Character offsets in original text
        start_char = enc.decode(tokens[:start]).__len__() if start > 0 else 0
        end_char = len(enc.decode(tokens[:end]))
        meta = {
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "content": chunk_text,
            "start_char": start_char,
            "end_char": end_char,
            "doc_title": doc_title,
            "source_type": source_type,
            "token_count": len(chunk_tokens),
        }
        chunks.append((chunk_text, meta))
        chunk_index += 1

        if end >= len(tokens):
            break

        new_start = end - overlap
        if new_start <= start:
            break
        start = new_start
    return chunks


def _get_encoding():
    """Encoding for embedding model; uses tiktoken.encoding_for_model so model changes don't break chunk sizing."""
    settings = get_settings()
    try:
        return tiktoken.encoding_for_model(settings.embedding_model)
    except KeyError:
        # Fallback if embedding model name isn't in tiktoken's map (e.g. new OpenAI model)
        return tiktoken.get_encoding("cl100k_base")
