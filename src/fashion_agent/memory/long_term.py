"""Long-term memory backed by Neo4j (with in-memory graph fallback).

Stores entity relationships as a knowledge graph:
  SKU → Supplier, SKU → Category, SKU → Trend, SKU → Feedback

When Neo4j is connected, every write goes to BOTH the in-memory cache
AND Neo4j via Cypher. Reads always hit in-memory first (fast path),
falling back to Neo4j for data not yet cached.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


async def _port_open(host: str, port: int) -> bool:
    try:
        _, w = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=1
        )
        w.close()
        await w.wait_closed()
        return True
    except Exception:
        return False


class LongTermMemory:
    """Knowledge graph for SKU lifecycle and entity relationships.

    Production: writes go to Neo4j AND in-memory cache.
    Dev fallback: in-memory adjacency list only.
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
    ):
        self._driver = None
        self._uri = neo4j_uri
        self._user = neo4j_user
        self._password = neo4j_password
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []

    async def connect(self) -> None:
        host = self._uri.split("://")[-1].split(":")[0]
        port_str = self._uri.split(":")[-1].split("/")[0]
        port = int(port_str) if port_str.isdigit() else 7687

        if not await _port_open(host, port):
            logger.warning(
                "neo4j_unavailable", error="port closed", msg="in-memory fallback"
            )
            return
        try:
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
            async with self._driver.session() as session:
                await asyncio.wait_for(session.run("RETURN 1"), timeout=5)
            logger.info("neo4j_connected", uri=self._uri)
        except Exception as e:
            logger.warning(
                "neo4j_unavailable", error=str(e), msg="in-memory fallback"
            )
            if self._driver:
                await self._driver.close()
            self._driver = None

    @property
    def is_connected(self) -> bool:
        return self._driver is not None

    async def add_node(
        self, node_id: str, label: str, properties: dict | None = None
    ) -> None:
        props = properties or {}
        self._nodes[node_id] = {"id": node_id, "label": label, **props}

        if self._driver:
            safe_props = {
                k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                for k, v in props.items()
            }
            safe_props["id"] = node_id
            cypher = (
                f"MERGE (n:{label} {{id: $id}}) "
                f"SET n += $props"
            )
            try:
                async with self._driver.session() as session:
                    await session.run(cypher, id=node_id, props=safe_props)
            except Exception as e:
                logger.warning("neo4j_write_failed", op="add_node", error=str(e))

    async def add_edge(
        self,
        from_id: str,
        to_id: str,
        relation: str,
        properties: dict | None = None,
    ) -> None:
        self._edges.append({
            "from": from_id,
            "to": to_id,
            "relation": relation,
            **(properties or {}),
        })

        if self._driver:
            cypher = (
                "MATCH (a {id: $from_id}), (b {id: $to_id}) "
                f"MERGE (a)-[r:{relation}]->(b) "
                "SET r += $props"
            )
            try:
                async with self._driver.session() as session:
                    await session.run(
                        cypher,
                        from_id=from_id,
                        to_id=to_id,
                        props=properties or {},
                    )
            except Exception as e:
                logger.warning("neo4j_write_failed", op="add_edge", error=str(e))

    async def get_node(self, node_id: str) -> dict | None:
        if node_id in self._nodes:
            return self._nodes[node_id]

        if self._driver:
            try:
                async with self._driver.session() as session:
                    result = await session.run(
                        "MATCH (n {id: $id}) RETURN n, labels(n) as labels",
                        id=node_id,
                    )
                    record = await result.single()
                    if record:
                        node_data = dict(record["n"])
                        node_data["label"] = record["labels"][0] if record["labels"] else "Unknown"
                        self._nodes[node_id] = node_data
                        return node_data
            except Exception as e:
                logger.warning("neo4j_read_failed", op="get_node", error=str(e))

        return None

    async def get_neighbors(
        self, node_id: str, relation: str | None = None
    ) -> list[dict[str, Any]]:
        results = []
        for edge in self._edges:
            match_from = edge["from"] == node_id
            match_to = edge["to"] == node_id
            if not (match_from or match_to):
                continue
            if relation is not None and edge["relation"] != relation:
                continue

            other_id = edge["to"] if match_from else edge["from"]
            target = self._nodes.get(other_id)
            if target:
                results.append({
                    "node": target,
                    "relation": edge["relation"],
                    "edge_props": {
                        k: v
                        for k, v in edge.items()
                        if k not in ("from", "to", "relation")
                    },
                })
        return results

    async def get_sku_graph(self, article_id: str) -> dict:
        node = await self.get_node(article_id)
        neighbors = await self.get_neighbors(article_id)
        return {
            "sku": node,
            "relationships": neighbors,
            "total_connections": len(neighbors),
        }

    async def query_by_label(self, label: str) -> list[dict]:
        return [n for n in self._nodes.values() if n.get("label") == label]

    async def stats(self) -> dict:
        labels: dict[str, int] = {}
        for n in self._nodes.values():
            lbl = n.get("label", "unknown")
            labels[lbl] = labels.get(lbl, 0) + 1
        relations: dict[str, int] = {}
        for e in self._edges:
            rel = e["relation"]
            relations[rel] = relations.get(rel, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "node_labels": labels,
            "edge_relations": relations,
        }

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
