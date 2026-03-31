"""Data browsing endpoints — view seed data (articles, inventory, etc.)."""

from __future__ import annotations

from fastapi import APIRouter

from fashion_agent.core.data_loader import (
    get_article_by_id,
    get_inventory_for_article,
    get_low_stock_articles,
    get_transactions_for_article,
    load_articles,
    load_customers,
    load_inventory,
    load_suppliers,
    load_transactions,
)

router = APIRouter()


@router.get("/data/articles")
async def list_articles():
    articles = load_articles()
    return {
        "total": len(articles),
        "articles": [a.model_dump() for a in articles],
    }


@router.get("/data/articles/{article_id}")
async def get_article(article_id: str):
    article = get_article_by_id(article_id)
    if article is None:
        return {"error": f"Article {article_id} not found"}
    inventory = get_inventory_for_article(article_id)
    transactions = get_transactions_for_article(article_id)
    return {
        "article": article.model_dump(),
        "inventory": [i.model_dump() for i in inventory],
        "transactions": [t.model_dump() for t in transactions],
    }


@router.get("/data/inventory")
async def list_inventory():
    inventory = load_inventory()
    return {
        "total": len(inventory),
        "records": [i.model_dump() for i in inventory],
    }


@router.get("/data/inventory/low-stock")
async def list_low_stock():
    items = get_low_stock_articles()
    return {
        "total": len(items),
        "items": [
            {"article": a.model_dump(), "inventory": inv.model_dump()}
            for a, inv in items
        ],
    }


@router.get("/data/transactions")
async def list_transactions():
    txns = load_transactions()
    return {
        "total": len(txns),
        "transactions": [t.model_dump() for t in txns],
    }


@router.get("/data/customers")
async def list_customers():
    customers = load_customers()
    return {
        "total": len(customers),
        "customers": [c.model_dump() for c in customers],
    }


@router.get("/data/suppliers")
async def list_suppliers():
    suppliers = load_suppliers()
    return {
        "total": len(suppliers),
        "suppliers": [s.model_dump() for s in suppliers],
    }
