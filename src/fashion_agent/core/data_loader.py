"""Load seed data from JSON files into domain models."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fashion_agent.core.config import get_settings
from fashion_agent.core.models import (
    Article,
    Customer,
    InventoryRecord,
    Supplier,
    Transaction,
)


def _load_json(filename: str) -> list[dict]:
    path = Path(get_settings().seed_data_dir) / filename
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


@lru_cache
def load_articles() -> list[Article]:
    return [Article(**row) for row in _load_json("articles.json")]


@lru_cache
def load_inventory() -> list[InventoryRecord]:
    return [InventoryRecord(**row) for row in _load_json("inventory.json")]


@lru_cache
def load_transactions() -> list[Transaction]:
    return [Transaction(**row) for row in _load_json("transactions.json")]


@lru_cache
def load_customers() -> list[Customer]:
    return [Customer(**row) for row in _load_json("customers.json")]


@lru_cache
def load_suppliers() -> list[Supplier]:
    return [Supplier(**row) for row in _load_json("suppliers.json")]


def get_article_by_id(article_id: str) -> Article | None:
    for a in load_articles():
        if a.article_id == article_id:
            return a
    return None


def get_inventory_for_article(article_id: str) -> list[InventoryRecord]:
    return [inv for inv in load_inventory() if inv.article_id == article_id]


def get_transactions_for_article(article_id: str) -> list[Transaction]:
    return [t for t in load_transactions() if t.article_id == article_id]


def get_supplier_for_garment_group(garment_group_name: str) -> Supplier | None:
    for s in load_suppliers():
        if garment_group_name in s.specialties:
            return s
    return None


def get_low_stock_articles() -> list[tuple[Article, InventoryRecord]]:
    """Return articles where any warehouse is below min_stock."""
    results = []
    for inv in load_inventory():
        if inv.is_low_stock:
            article = get_article_by_id(inv.article_id)
            if article:
                results.append((article, inv))
    return results
