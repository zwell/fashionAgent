"""Seed all memory layers with data from the seed JSON files.

Usage:
    python scripts/seed_memory.py
"""

from __future__ import annotations

import asyncio

from fashion_agent.core.data_loader import load_articles, load_suppliers
from fashion_agent.core.logging import setup_logging
from fashion_agent.memory.entity import EntityMemory
from fashion_agent.memory.manager import MemoryManager
from fashion_agent.skills.loader import register_all_skills


async def main() -> None:
    setup_logging()
    register_all_skills()

    mm = MemoryManager()
    await mm.initialize()
    entity = EntityMemory(mm)

    articles = load_articles()
    suppliers = load_suppliers()

    print(f"Seeding {len(articles)} articles into memory layers...")

    for sup in suppliers:
        await mm.long_term.add_node(sup.supplier_id, "Supplier", {
            "name": sup.name,
            "region": sup.region,
            "specialties": sup.specialties,
            "lead_time_days": sup.lead_time_days,
        })

    for i, article in enumerate(articles, 1):
        result = await entity.build_sku_profile(article.article_id)
        status = "OK" if result.get("success") else "FAIL"
        print(f"  [{i}/{len(articles)}] {article.article_id} {article.prod_name} — {status}")

    stats = await mm.get_memory_stats()
    print(f"\nMemory stats:")
    print(f"  Vectors: {stats['mid_term']['vectors_stored']}")
    print(f"  Graph nodes: {stats['long_term']['total_nodes']}")
    print(f"  Graph edges: {stats['long_term']['total_edges']}")

    await mm.shutdown()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
