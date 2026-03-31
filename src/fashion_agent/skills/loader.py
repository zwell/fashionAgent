"""Auto-discover and register all skills with the registry."""

from __future__ import annotations

from fashion_agent.skills.base import SkillDescriptor
from fashion_agent.skills.l1_atomic.competitor import competitor_analysis
from fashion_agent.skills.l1_atomic.copywriting import generate_copywriting
from fashion_agent.skills.l1_atomic.erp_inventory import erp_inventory_query
from fashion_agent.skills.l1_atomic.sales_forecast import sales_forecast
from fashion_agent.skills.l1_atomic.trend_analysis import trend_analysis
from fashion_agent.skills.l2_composite.clearance import clearance_workflow
from fashion_agent.skills.l2_composite.product_launch import product_launch_workflow
from fashion_agent.skills.l2_composite.restock import restock_workflow
from fashion_agent.skills.registry import get_registry

_ALL_SKILL_FUNCS = [
    erp_inventory_query,
    sales_forecast,
    competitor_analysis,
    trend_analysis,
    generate_copywriting,
    restock_workflow,
    clearance_workflow,
    product_launch_workflow,
]


def register_all_skills() -> None:
    registry = get_registry()
    for func in _ALL_SKILL_FUNCS:
        descriptor: SkillDescriptor | None = getattr(func, "_skill_descriptor", None)
        if descriptor is not None:
            registry.register(descriptor)
