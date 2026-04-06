"""
OpenAI embedding generation with Redis (or in-memory) caching.

Model: text-embedding-3-small (1536 dimensions)
"""

import hashlib
import json
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── in-memory fallback cache ──────────────────────────────────────────────────
_mem_cache: dict = {}


# ── Redis client (optional) ───────────────────────────────────────────────────

def _get_redis():
    """Get Redis client (decode_responses=False) from the DI container."""
    from infrastructure.container import get_container
    return get_container().get_redis_bytes()


def _cache_key(text: str) -> str:
    return "emb_v2:" + hashlib.sha256(text.encode()).hexdigest()


def _get_cached(text: str) -> Optional[List[float]]:
    key = _cache_key(text)
    r = _get_redis()
    if r:
        try:
            raw = r.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _mem_cache.get(key)


def _set_cached(text: str, vector: List[float]) -> None:
    key = _cache_key(text)
    r = _get_redis()
    if r:
        try:
            r.set(key, json.dumps(vector), ex=86400 * 7)  # 7-day TTL
            return
        except Exception:
            pass
    _mem_cache[key] = vector


# ── OpenAI client (lazy) ──────────────────────────────────────────────────────

def _get_openai():
    """Get OpenAI client from the DI container."""
    from infrastructure.container import get_container
    return get_container().get_openai_client()


# ── Public API ────────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def get_embedding(text: str) -> List[float]:
    """
    Return the embedding vector for *text* using text-embedding-3-small.
    Results are cached in Redis (if available) or in-memory.
    """
    text = text.strip()
    if not text:
        raise ValueError("Cannot embed empty text")

    cached = _get_cached(text)
    if cached is not None:
        return cached

    client = _get_openai()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    vector = response.data[0].embedding
    _set_cached(text, vector)
    return vector


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Batch-embed a list of texts. Already-cached texts skip the API call.
    Sends a single OpenAI request for the uncached subset.
    """
    results: List[Optional[List[float]]] = [None] * len(texts)
    uncached_indices: List[int] = []
    uncached_texts: List[str] = []

    for i, text in enumerate(texts):
        text = text.strip()
        cached = _get_cached(text)
        if cached is not None:
            results[i] = cached
        else:
            uncached_indices.append(i)
            uncached_texts.append(text)

    if uncached_texts:
        client = _get_openai()
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=uncached_texts)
        for pos, data in enumerate(response.data):
            idx = uncached_indices[pos]
            vector = data.embedding
            _set_cached(texts[idx], vector)
            results[idx] = vector

    return results  # type: ignore[return-value]
