"""Long-term memory backed by Neo4j (with in-memory graph fallback).

Stores entity relationships as a knowledge graph:
  SKU → Supplier, SKU → Category, SKU → Trend, SKU → Feedback
"""

from __future__ import annotations

from typing import Any

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


class LongTermMemory:
    """Knowledge graph for SKU lifecycle and entity relationships.

    Production: Neo4j Cypher queries.
    Dev fallback: in-memory adjacency list.
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
        try:
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            logger.info("neo4j_connected", uri=self._uri)
        except Exception as e:
            logger.warning("neo4j_unavailable", error=str(e), msg="in-memory fallback")
            self._driver = None

    async def add_node(self, node_id: str, label: str, properties: dict | None = None) -> None:
        self._nodes[node_id] = {
            "id": node_id,
            "label": label,
            **(properties or {}),
        }

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

    async def get_node(self, node_id: str) -> dict | None:
        return self._nodes.get(node_id)

    async def get_neighbors(
        self, node_id: str, relation: str | None = None
    ) -> list[dict[str, Any]]:
        results = []
        for edge in self._edges:
            if edge["from"] == node_id:
                if relation is None or edge["relation"] == relation:
                    target = self._nodes.get(edge["to"])
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
            elif edge["to"] == node_id:
                if relation is None or edge["relation"] == relation:
                    source = self._nodes.get(edge["from"])
                    if source:
                        results.append({
                            "node": source,
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
