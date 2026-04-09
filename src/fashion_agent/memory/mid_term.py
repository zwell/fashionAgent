"""Mid-term memory backed by Milvus (with in-memory vector fallback).

Stores SKU vector embeddings for semantic similarity search.
When Milvus is unavailable, uses a simple cosine-similarity implementation
over an in-memory dict so the system works without external dependencies.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
from typing import Any
from urllib.parse import urlparse, urlunparse

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)

_LOOPBACK_NO_PROXY = "127.0.0.1,localhost,::1"


def _prepare_milvus_grpc_runtime(*, extend_no_proxy: bool) -> None:
    """Must run before ``import pymilvus`` / ``import grpc`` (first time in process).

    - Windows: default ``GRPC_POLL_STRATEGY=poll`` mitigates stuck ``channel_ready`` with
      some Docker/Desktop networking stacks (user may pre-set in env).
    - Optionally extend NO_PROXY so loopback gRPC is not sent through HTTP(S) proxies.
    """
    import os
    import sys

    if sys.platform == "win32":
        os.environ.setdefault("GRPC_POLL_STRATEGY", "poll")

    if extend_no_proxy:
        for key in ("NO_PROXY", "no_proxy"):
            cur = (os.environ.get(key) or "").strip()
            if not cur:
                os.environ[key] = _LOOPBACK_NO_PROXY
            elif "127.0.0.1" not in cur:
                os.environ[key] = f"{_LOOPBACK_NO_PROXY},{cur}"


# Docker Desktop on Windows often publishes 19530 only on IPv4; ``localhost`` may
# resolve to ::1 first and pymilvus then fails with "illegal connection params".
_LOCALHOST_ALIASES = frozenset({"localhost", "localhost."})


def _normalize_milvus_uri(host: str, port: int, explicit_uri: str | None) -> str:
    """Build ``http://...`` URI for MilvusClient, forcing IPv4 loopback when needed."""
    if explicit_uri and explicit_uri.strip():
        uri = explicit_uri.strip()
        if not uri.startswith(("http://", "https://")):
            uri = f"http://{uri}"
    else:
        h = (host or "").strip()
        if h.lower() in _LOCALHOST_ALIASES or h == "::1":
            h = "127.0.0.1"
        uri = f"http://{h}:{port}"

    parts = urlparse(uri)
    hn = (parts.hostname or "").lower().rstrip(".")
    if hn in _LOCALHOST_ALIASES or parts.hostname == "::1":
        netloc = f"127.0.0.1:{parts.port or port}"
        uri = urlunparse(
            (parts.scheme, netloc, parts.path or "", "", parts.query, parts.fragment)
        )
    return uri


def _tcp_target_from_uri(uri: str) -> tuple[str, int]:
    parts = urlparse(uri)
    host = parts.hostname or "127.0.0.1"
    prt = int(parts.port or 19530)
    if host.lower() in _LOCALHOST_ALIASES or host == "::1":
        host = "127.0.0.1"
    return host, prt


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


async def _port_open(host: str, port: int) -> bool:
    """Quick TCP check — avoids long gRPC timeouts when service is down."""
    try:
        _, w = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=1
        )
        w.close()
        await w.wait_closed()
        return True
    except Exception:
        return False


class MidTermMemory:
    """SKU vector embeddings for semantic search.

    Production: Milvus collection with IVF_FLAT index.
    Dev fallback: in-memory dict + brute-force cosine search.
    """

    COLLECTION = "sku_embeddings"
    DIM = 128

    def __init__(
        self,
        milvus_host: str = "localhost",
        milvus_port: int = 19530,
        milvus_uri: str | None = None,
        connect_timeout: float = 45.0,
        extend_no_proxy: bool = True,
    ):
        self._milvus = None
        self._host = milvus_host
        self._port = milvus_port
        self._uri_override = milvus_uri
        self._connect_timeout = connect_timeout
        self._extend_no_proxy = extend_no_proxy
        self._fallback: dict[str, dict[str, Any]] = {}

    async def connect(self) -> None:
        uri = _normalize_milvus_uri(self._host, self._port, self._uri_override)
        tcp_host, tcp_port = _tcp_target_from_uri(uri)
        if not await _port_open(tcp_host, tcp_port):
            logger.warning(
                "milvus_unavailable",
                error="port closed",
                tcp_host=tcp_host,
                tcp_port=tcp_port,
                msg="in-memory fallback",
            )
            return
        try:
            _prepare_milvus_grpc_runtime(extend_no_proxy=self._extend_no_proxy)
            from pymilvus import MilvusClient

            def _connect_and_probe(u: str, t: float) -> Any:
                # Single thread: gRPC channel + first RPC (pymilvus / grpcio are picky
                # about cross-thread use during handshake).
                c = MilvusClient(uri=u, timeout=t)
                c.list_collections()
                return c

            loop = asyncio.get_event_loop()
            budget = max(float(self._connect_timeout), 5.0)
            client = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    _connect_and_probe,
                    uri,
                    budget,
                ),
                timeout=budget + 30.0,
            )
            self._milvus = client
            logger.info("milvus_connected", uri=uri, timeout=budget)
        except Exception as e:
            logger.warning(
                "milvus_unavailable", error=str(e), msg="in-memory fallback"
            )
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
                    {
                        "article_id": r["id"],
                        "score": r["distance"],
                        "text": r.get("text", ""),
                    }
                    for r in results[0]
                ]
            except Exception:
                pass

        scored = []
        for aid, rec in self._fallback.items():
            sim = _cosine_similarity(query_vec, rec["vector"])
            scored.append(
                {"article_id": aid, "score": round(sim, 4), "text": rec["text"]}
            )
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
