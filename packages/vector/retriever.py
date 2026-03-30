"""
V2 hybrid retriever.

Pipeline:
  1. Fetch user-installed tools from Supabase (user_tools table)
  2. Embed the query via OpenAI
  3. Vector search in Qdrant (top 20 candidates)
  4. Hybrid re-score: 0.7 * vector_score + 0.3 * keyword_score
  5. Filter to only user-installed (tool_name, server) pairs
  6. Return top_k results

Retrieval results are cached by (query, user_id) in Redis or memory.
"""

import hashlib
import json
import logging
import os
import re
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ── result cache ──────────────────────────────────────────────────────────────
_mem_cache: dict = {}
_redis_client = None

RESULT_CACHE_TTL = 300  # 5 minutes


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable for retrieval cache: {e}")
        return None


def _result_cache_key(query: str, user_id: str, top_k: int) -> str:
    raw = f"{query}::{user_id}::{top_k}"
    return "ret_v2:" + hashlib.sha256(raw.encode()).hexdigest()


def _get_cached_result(query: str, user_id: str, top_k: int) -> Optional[List[dict]]:
    key = _result_cache_key(query, user_id, top_k)
    r = _get_redis()
    if r:
        try:
            raw = r.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _mem_cache.get(key)


def _set_cached_result(query: str, user_id: str, top_k: int, results: List[dict]) -> None:
    key = _result_cache_key(query, user_id, top_k)
    r = _get_redis()
    if r:
        try:
            r.set(key, json.dumps(results), ex=RESULT_CACHE_TTL)
            return
        except Exception:
            pass
    _mem_cache[key] = results


# ── Supabase ──────────────────────────────────────────────────────────────────
_supabase_client = None


def _get_supabase():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    _supabase_client = create_client(url, key)
    return _supabase_client


def _get_user_installed_tools(user_id: str) -> Set[Tuple[str, str]]:
    """
    Return a set of (tool_name, server) tuples the user has installed.
    Returns empty set if user_id is blank (public/unauthenticated access).
    """
    if not user_id:
        return set()
    sb = _get_supabase()
    resp = (
        sb.table("user_tools")
        .select("tool_name, server")
        .eq("user_id", user_id)
        .execute()
    )
    return {(row["tool_name"], row["server"]) for row in (resp.data or [])}


# ── keyword scoring ───────────────────────────────────────────────────────────

def _tokenize(text: str) -> set:
    return set(re.findall(r"\w+", text.lower()))


def _keyword_score(query: str, item: dict) -> float:
    """Score based on token overlap between query and tool metadata."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    searchable = " ".join([
        item.get("tool_name", ""),
        item.get("description", ""),
        item.get("summary", ""),
        " ".join(item.get("tags", [])),
        " ".join(item.get("examples", [])),
    ])
    tool_tokens = _tokenize(searchable)
    if not tool_tokens:
        return 0.0

    overlap = query_tokens & tool_tokens
    return len(overlap) / len(query_tokens)


# ── public API ────────────────────────────────────────────────────────────────

def retrieve_tools(
    query: str,
    user_id: str,
    top_k: int = 5,
) -> List[Dict]:
    """
    Retrieve the most relevant tools available to *user_id* for *query*.

    Steps:
      1. Check result cache
      2. Get user-installed (tool_name, server) pairs from Supabase
      3. Embed query
      4. Qdrant vector search (top 20)
      5. Hybrid re-score (0.7 vector + 0.3 keyword)
      6. Filter to user-installed tools
      7. Return top_k

    Returns list of dicts: {tool_name, description, server, score}
    """
    cached = _get_cached_result(query, user_id, top_k)
    if cached is not None:
        logger.debug(f"Cache hit for query='{query}' user='{user_id}'")
        return cached

    # Step 1: user-installed tools
    user_tools = _get_user_installed_tools(user_id)

    # Step 2: embed query
    from .embeddings import get_embedding
    query_vector = get_embedding(query)

    # Step 3: vector search (fetch 20 candidates for re-ranking)
    from .qdrant_store import search_points
    candidates = search_points(query_vector, top_k=20)

    # Step 4: hybrid re-score
    scored = []
    for item in candidates:
        v_score = float(item.get("_score", 0.0))
        k_score = _keyword_score(query, item)
        final_score = 0.7 * v_score + 0.3 * k_score
        scored.append((item, final_score))

    # Sort by final score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Step 5: filter to user-installed tools
    results = []
    for item, score in scored:
        tool_name = item.get("tool_name", "")
        server = item.get("server", "")
        if (tool_name, server) not in user_tools:
            continue
        results.append({
            "tool_name": tool_name,
            "description": item.get("description", ""),
            "server": server,
            "score": round(score, 4),
        })
        if len(results) >= top_k:
            break

    _set_cached_result(query, user_id, top_k, results)
    return results


def track_installation(user_id: str, tool_name: str, server: str, pack_id: Optional[str] = None) -> None:
    """
    Record that *user_id* has installed *tool_name* from *server*.
    Upserts into Supabase user_tools table.
    """
    sb = _get_supabase()
    row = {
        "user_id": user_id,
        "tool_name": tool_name,
        "server": server,
        "pack_id": pack_id,
    }
    # upsert on (user_id, tool_name, server)
    sb.table("user_tools").upsert(row, on_conflict="user_id,tool_name,server").execute()
    logger.info(f"Tracked installation: {user_id} → {server}/{tool_name}")

    # Invalidate any cached results for this user
    _invalidate_user_cache(user_id)


def _invalidate_user_cache(user_id: str) -> None:
    """Remove in-memory cached retrieval results for a user (best-effort)."""
    prefix = "ret_v2:"
    keys_to_delete = [k for k in _mem_cache if k.startswith(prefix) and user_id in k]
    for k in keys_to_delete:
        _mem_cache.pop(k, None)
