"""
Tool indexer: enriches tools with LLM metadata, generates embeddings,
and upserts into Qdrant Cloud.

Key design decisions:
  - Deterministic point ID: "{server}_{tool_name}" (hashed to int internally)
  - Skips already-indexed tools to stay idempotent
  - Batch upsert (size 50) to reduce round-trips
"""

import logging
from typing import List, Optional

from .embeddings import get_embeddings_batch, EMBEDDING_DIM
from .llm_enricher import enrich_tool
from .qdrant_store import (
    create_collection_if_not_exists,
    upsert_points,
    point_exists,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def _make_point_id(server: str, tool_name: str) -> str:
    return f"{server}_{tool_name}"


def _build_embedding_text(tool: dict, enriched: dict) -> str:
    tags_str = ", ".join(enriched.get("tags", []))
    examples = enriched.get("examples", [])
    examples_str = "\n".join(f"* {ex}" for ex in examples)
    return (
        f"Tool Name: {tool.get('name', '')}\n"
        f"Summary: {enriched.get('summary', '')}\n"
        f"Description: {tool.get('description', '')}\n"
        f"Tags: {tags_str}\n"
        f"Examples:\n{examples_str}"
    ).strip()


def index_tools(tools: List[dict], skip_existing: bool = True) -> int:
    """
    Enrich, embed, and upsert *tools* into Qdrant.

    Args:
        tools:          List of tool dicts (must have 'name', 'description', 'server').
        skip_existing:  If True, tools already in Qdrant are skipped (idempotent).

    Returns:
        Number of tools actually indexed (new or re-indexed).
    """
    create_collection_if_not_exists(vector_size=EMBEDDING_DIM)

    to_index: List[dict] = []
    enrichments: List[dict] = []

    for tool in tools:
        name = tool.get("name", "")
        server = tool.get("server", "unknown")
        point_id = _make_point_id(server, name)

        if skip_existing and point_exists(point_id):
            logger.debug(f"Skipping already-indexed tool: {point_id}")
            continue

        enriched = enrich_tool(tool)
        to_index.append(tool)
        enrichments.append(enriched)

    if not to_index:
        logger.info("No new tools to index")
        return 0

    # Build embedding texts
    embed_texts = [
        _build_embedding_text(tool, enriched)
        for tool, enriched in zip(to_index, enrichments)
    ]

    # Batch-embed
    vectors = get_embeddings_batch(embed_texts)

    # Build Qdrant point dicts and batch-upsert
    total_indexed = 0
    for batch_start in range(0, len(to_index), BATCH_SIZE):
        batch_tools = to_index[batch_start: batch_start + BATCH_SIZE]
        batch_enrichments = enrichments[batch_start: batch_start + BATCH_SIZE]
        batch_vectors = vectors[batch_start: batch_start + BATCH_SIZE]

        points = []
        for tool, enriched, vector in zip(batch_tools, batch_enrichments, batch_vectors):
            name = tool.get("name", "")
            server = tool.get("server", "unknown")
            point_id = _make_point_id(server, name)
            payload = {
                "tool_name": name,
                "server": server,
                "description": tool.get("description", ""),
                "summary": enriched["summary"],
                "tags": enriched["tags"],
                "examples": enriched["examples"],
                "pack_id": tool.get("pack_id"),
                "is_public": tool.get("is_public", True),
            }
            points.append({"id": point_id, "vector": vector, "payload": payload})

        upsert_points(points)
        total_indexed += len(points)
        logger.info(
            f"Indexed batch {batch_start // BATCH_SIZE + 1}: "
            f"{len(points)} tools (total so far: {total_indexed})"
        )

    logger.info(f"Indexing complete. {total_indexed} tools indexed.")
    return total_indexed
