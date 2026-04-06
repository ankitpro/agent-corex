"""
LLM-based tool metadata enrichment using OpenAI Chat API.

Generates:
  - summary    : short optimised description for embedding
  - tags       : 3-5 categorical labels
  - examples   : 3-5 realistic developer query strings

Results are cached to avoid duplicate API calls.
"""

import hashlib
import json
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── caches ────────────────────────────────────────────────────────────────────
_mem_cache: dict = {}


def _get_redis():
    """Get Redis client (decode_responses=True) from the DI container."""
    from infrastructure.container import get_container
    return get_container().get_redis_str()


def _cache_key(tool_name: str, server: str) -> str:
    raw = f"{server}::{tool_name}"
    return "enrich_v2:" + hashlib.sha256(raw.encode()).hexdigest()


def _get_cached(tool_name: str, server: str) -> Optional[dict]:
    key = _cache_key(tool_name, server)
    r = _get_redis()
    if r:
        try:
            raw = r.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return _mem_cache.get(key)


def _set_cached(tool_name: str, server: str, result: dict) -> None:
    key = _cache_key(tool_name, server)
    r = _get_redis()
    if r:
        try:
            r.set(key, json.dumps(result), ex=86400 * 30)  # 30-day TTL
            return
        except Exception:
            pass
    _mem_cache[key] = result


# ── OpenAI client (lazy) ──────────────────────────────────────────────────────

def _get_openai():
    """Get OpenAI client from the DI container."""
    from infrastructure.container import get_container
    return get_container().get_openai_client()


_SYSTEM_PROMPT = """\
You are a developer-tools documentation expert. Given an MCP tool name and description,
return a JSON object with exactly these keys:
  "summary"  - one sentence, optimised for semantic search (≤20 words)
  "tags"     - array of 3–5 lowercase categorical tags (e.g. "git", "file-system", "docker")
  "examples" - array of 3–5 realistic developer queries that would match this tool

Respond ONLY with valid JSON. No markdown fences, no extra text.
"""

_USER_TEMPLATE = """\
Tool name: {name}
Server: {server}
Description: {description}
"""


def _parse_json_response(content: str) -> dict:
    """Extract JSON even if the model wrapped it in markdown fences."""
    content = content.strip()
    # Strip ```json ... ``` or ``` ... ```
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    return json.loads(content)


def enrich_tool(tool: dict) -> dict:
    """
    Return enriched metadata for *tool*.

    Input tool dict must have at least: name, description, server.
    Returns dict with: summary, tags (list), examples (list).
    Cached by (server, tool_name) pair.
    """
    name = tool.get("name", "")
    server = tool.get("server", "unknown")
    description = tool.get("description", "")

    cached = _get_cached(name, server)
    if cached is not None:
        return cached

    client = _get_openai()
    user_msg = _USER_TEMPLATE.format(name=name, server=server, description=description)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=512,
        )
        raw = resp.choices[0].message.content or "{}"
        enriched = _parse_json_response(raw)
    except Exception as e:
        logger.error(f"LLM enrichment failed for {server}/{name}: {e}")
        # Fallback: minimal enrichment from existing data
        enriched = {
            "summary": description[:120] if description else name,
            "tags": [],
            "examples": [],
        }

    # Normalise shape
    result = {
        "summary": str(enriched.get("summary", description or name)),
        "tags": list(enriched.get("tags", [])),
        "examples": list(enriched.get("examples", [])),
    }

    _set_cached(name, server, result)
    return result
