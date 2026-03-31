"""Mid-term memory backed by Milvus (with in-memory vector fallback).

Stores SKU vector embeddings for semantic similarity search.
When Milvus is unavailable, uses a simple cosine-similarity implementation
over an in-memory dict so the system works without external dependencies.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


def _text_to_vector(text: str, dim: int = 128) -> list[float]:
    """Deterministic pseudo-embedding from text (no ML model needed)."""
    h = hashlib.sha512(text.encode()).digest()
    raw = [b / 255.0 for b in h]
    while len(raw) < dim:
        h = hashlib.sha512(h).digest()
        raw.extend(b / 255.0 for b in h)
    raw = raw[:dim]
    norm = math.sqrt(sum(x * x for x in raw)) or 1.0
    return [x / norm for x in raw]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class MidTermMemory:
    """SKU vector embeddings for semantic search.

    Production: Milvus collection with IVF_FLAT index.
    Dev fallback: in-memory dict + brute-force cosine search.
    """

    COLLECTION = "sku_embeddings"
    DIM = 128

    def __init__(self, milvus_host: str = "localhost", milvus_port: int = 19530):
        self._milvus = None
        self._host = milvus_host
        self._port = milvus_port
        self._fallback: dict[str, dict[str, Any]] = {}

    async def connect(self) -> None:
        try:
            from pymilvus import MilvusClient

            uri = f"http://{self._host}:{self._port}"
            self._milvus = MilvusClient(uri=uri)
            self._milvus.list_collections()
            logger.info("milvus_connected", host=self._host, port=self._port)
        except Exception as e:
            logger.warning("milvus_unavailable", error=str(e), msg="in-memory fallback")
            self._milvus = None

    async def upsert_sku(
        self,
        article_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        vector = _text_to_vector(text, self.DIM)
        record = {
            "article_id": article_id,
            "text": text,
            "vector": vector,
            **(metadata or {}),
        }
        if self._milvus:
            try:
                self._milvus.upsert(
                    collection_name=self.COLLECTION,
                    data=[{"id": article_id, "vector": vector, "text": text}],
                )
            except Exception:
                self._fallback[article_id] = record
        else:
            self._fallback[article_id] = record

    async def search_similar(
        self, query_text: str, top_k: int = 5
    ) -> list[dict[str, Any]]:
        query_vec = _text_to_vector(query_text, self.DIM)

        if self._milvus:
            try:
                results = self._milvus.search(
                    collection_name=self.COLLECTION,
                    data=[query_vec],
                    limit=top_k,
                    output_fields=["text"],
                )
                return [
                    {"article_id": r["id"], "score": r["distance"], "text": r.get("text", "")}
                    for r in results[0]
                ]
            except Exception:
                pass

        scored = []
        for aid, rec in self._fallback.items():
            sim = _cosine_similarity(query_vec, rec["vector"])
            scored.append({"article_id": aid, "score": round(sim, 4), "text": rec["text"]})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def get_sku_vector(self, article_id: str) -> dict | None:
        if article_id in self._fallback:
            rec = self._fallback[article_id]
            return {"article_id": article_id, "text": rec["text"]}
        return None

    async def count(self) -> int:
        return len(self._fallback)

    async def close(self) -> None:
        self._milvus = None
