"""L1 Atomic Skills — individual capabilities that agents can invoke."""

from fashion_agent.skills.l1_atomic.competitor import competitor_analysis
from fashion_agent.skills.l1_atomic.copywriting import generate_copywriting
from fashion_agent.skills.l1_atomic.design_proposal import design_proposal
from fashion_agent.skills.l1_atomic.erp_inventory import erp_inventory_query
from fashion_agent.skills.l1_atomic.image_gen import image_generation
from fashion_agent.skills.l1_atomic.sales_forecast import sales_forecast
from fashion_agent.skills.l1_atomic.trend_analysis import trend_analysis

__all__ = [
    "competitor_analysis",
    "generate_copywriting",
    "design_proposal",
    "erp_inventory_query",
    "image_generation",
    "sales_forecast",
    "trend_analysis",
]
