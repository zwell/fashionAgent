"""Memory layer endpoints — query entity profiles, similar SKUs, graph, reflection."""

from __future__ import annotations

from fastapi import APIRouter

from fashion_agent.gateway.dependencies import get_entity_memory, get_memory, get_reflection

router = APIRouter()


@router.get("/memory/stats")
async def memory_stats():
    """Get statistics for all memory layers."""
    mm = get_memory()
    return await mm.get_memory_stats()


@router.get("/memory/sku/{article_id}/profile")
async def sku_profile(article_id: str):
    """Build or retrieve the unified profile for a SKU."""
    entity = get_entity_memory()
    profile = await entity.get_profile(article_id)
    if profile is None:
        return {"success": False, "message": f"Article {article_id} not found"}
    return {"success": True, "profile": profile}


@router.get("/memory/sku/{article_id}/similar")
async def similar_skus(article_id: str, top_k: int = 5):
    """Find SKUs with similar vector embeddings."""
    entity = get_entity_memory()
    results = await entity.find_similar_skus(article_id, top_k=top_k)
    return {"article_id": article_id, "similar": results}


@router.get("/memory/sku/{article_id}/graph")
async def sku_graph(article_id: str):
    """Get knowledge graph relationships for a SKU."""
    entity = get_entity_memory()
    return await entity.get_sku_relationships(article_id)


@router.post("/memory/sku/{article_id}/feedback")
async def add_feedback(article_id: str, feedback_type: str, content: str):
    """Add feedback (e.g. return reason, rating) to a SKU."""
    entity = get_entity_memory()
    await entity.add_feedback(article_id, feedback_type, content)
    return {"success": True, "article_id": article_id, "feedback_type": feedback_type}


@router.get("/memory/search")
async def semantic_search(q: str, top_k: int = 5):
    """Semantic vector search across all SKU embeddings."""
    mm = get_memory()
    results = await mm.find_similar(q, top_k=top_k)
    return {"query": q, "results": results}


@router.post("/memory/reflection")
async def run_reflection(target_date: str | None = None):
    """Trigger the reflection engine for a given date (defaults to today)."""
    engine = get_reflection()
    result = await engine.reflect(target_date=target_date)
    return result


@router.get("/memory/reflection/recent")
async def recent_insights(days: int = 7):
    """Get recent reflection insights."""
    engine = get_reflection()
    insights = await engine.get_recent_insights(days=days)
    return {"days": days, "insights": insights}


@router.get("/memory/graph/stats")
async def graph_stats():
    """Get knowledge graph node/edge statistics."""
    mm = get_memory()
    return await mm.long_term.stats()
