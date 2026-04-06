"""
Qdrant Cloud client wrapper.

Collection: "tools"
Vector size: dynamically determined from first embedding (text-embedding-3-small → 1536)
Distance: COSINE
"""

import logging
import os
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)

COLLECTION_NAME = "tools"


def get_client() -> QdrantClient:
    """Get the Qdrant client singleton from the DI container."""
    from infrastructure.container import get_container
    return get_container().get_qdrant_client()


# ── collection management ─────────────────────────────────────────────────────

def create_collection_if_not_exists(vector_size: int = 1536) -> None:
    """Create the 'tools' collection with COSINE distance if it doesn't exist."""
    client = get_client()
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME in existing:
        logger.debug(f"Collection '{COLLECTION_NAME}' already exists")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qmodels.VectorParams(
            size=vector_size,
            distance=qmodels.Distance.COSINE,
        ),
    )
    logger.info(f"Created Qdrant collection '{COLLECTION_NAME}' (dim={vector_size}, COSINE)")


# ── write ─────────────────────────────────────────────────────────────────────

def upsert_points(points: List[Dict[str, Any]]) -> None:
    """
    Upsert a batch of points into the 'tools' collection.

    Each point must have:
      id      : str  (deterministic, e.g. "github_create_pull_request")
      vector  : List[float]
      payload : dict  (tool metadata)
    """
    client = get_client()
    qdrant_points = [
        qmodels.PointStruct(
            id=_str_id_to_int(p["id"]),
            vector=p["vector"],
            payload=p["payload"],
        )
        for p in points
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=qdrant_points)
    logger.debug(f"Upserted {len(qdrant_points)} points into '{COLLECTION_NAME}'")


# ── read ──────────────────────────────────────────────────────────────────────

def search_points(
    query_vector: List[float],
    top_k: int = 20,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Vector search in Qdrant.

    Returns a list of payload dicts, each augmented with '_score' and '_id'.
    """
    client = get_client()

    qdrant_filter = None
    if filters:
        qdrant_filter = _build_filter(filters)

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=qdrant_filter,
    )

    out = []
    for hit in results:
        item = dict(hit.payload or {})
        item["_score"] = hit.score
        item["_id"] = hit.id
        out.append(item)
    return out


def point_exists(point_id: str) -> bool:
    """Check whether a point with the given string ID already exists."""
    client = get_client()
    int_id = _str_id_to_int(point_id)
    results = client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[int_id],
        with_payload=False,
        with_vectors=False,
    )
    return len(results) > 0


# ── helpers ───────────────────────────────────────────────────────────────────

def _str_id_to_int(str_id: str) -> int:
    """Convert deterministic string ID to a positive int Qdrant ID via hash."""
    import hashlib
    digest = hashlib.md5(str_id.encode()).hexdigest()
    return int(digest[:15], 16)  # 60-bit positive integer, collision risk negligible


def _build_filter(filters: Dict[str, Any]) -> qmodels.Filter:
    """Build a Qdrant Filter from a simple {field: value} dict."""
    conditions = []
    for field, value in filters.items():
        if isinstance(value, bool):
            conditions.append(
                qmodels.FieldCondition(
                    key=field,
                    match=qmodels.MatchValue(value=value),
                )
            )
        elif isinstance(value, list):
            conditions.append(
                qmodels.FieldCondition(
                    key=field,
                    match=qmodels.MatchAny(any=value),
                )
            )
        else:
            conditions.append(
                qmodels.FieldCondition(
                    key=field,
                    match=qmodels.MatchValue(value=value),
                )
            )
    return qmodels.Filter(must=conditions)
