"""Domain models shared across the system."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

# ── Article / SKU ──────────────────────────────────────────────

class Article(BaseModel):
    article_id: str
    product_code: str
    prod_name: str
    product_type_name: str
    product_group_name: str
    graphical_appearance_name: str
    colour_group_name: str
    perceived_colour_value_name: str
    perceived_colour_master_name: str
    department_name: str
    index_name: str
    index_group_name: str
    section_name: str
    garment_group_name: str
    detail_desc: str


# ── Inventory ──────────────────────────────────────────────────

class InventoryRecord(BaseModel):
    article_id: str
    warehouse: str
    quantity: int
    min_stock: int
    reorder_point: int
    unit_cost: float
    retail_price: float

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.min_stock

    @property
    def needs_reorder(self) -> bool:
        return self.quantity <= self.reorder_point


# ── Transaction ────────────────────────────────────────────────

class Transaction(BaseModel):
    t_dat: date
    customer_id: str
    article_id: str
    price: float
    sales_channel_id: int


# ── Customer ───────────────────────────────────────────────────

class ClubStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PRE_CREATE = "PRE-CREATE"
    LEFT_CLUB = "LEFT CLUB"


class Customer(BaseModel):
    customer_id: str
    age: int
    club_member_status: ClubStatus
    fashion_news_frequency: str


# ── Supplier ───────────────────────────────────────────────────

class Supplier(BaseModel):
    supplier_id: str
    name: str
    region: str
    specialties: list[str]
    lead_time_days: int
    min_order_quantity: int
    reliability_score: float = Field(ge=0.0, le=1.0)


# ── Task System ────────────────────────────────────────────────

class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(StrEnum):
    NEW_PRODUCT_LAUNCH = "new_product_launch"
    RESTOCK = "restock"
    CLEARANCE = "clearance"
    COPYWRITING = "copywriting"
    INVENTORY_CHECK = "inventory_check"
    TREND_ANALYSIS = "trend_analysis"
    GENERAL = "general"


class TaskRequest(BaseModel):
    task_type: TaskType
    instruction: str
    params: dict = Field(default_factory=dict)


class TaskResult(BaseModel):
    task_id: str
    task_type: TaskType
    status: TaskStatus
    result: dict = Field(default_factory=dict)
    error: str | None = None
