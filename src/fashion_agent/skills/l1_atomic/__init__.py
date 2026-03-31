"""L1 Atomic Skills — individual capabilities that agents can invoke."""

from fashion_agent.skills.l1_atomic.competitor import competitor_analysis
from fashion_agent.skills.l1_atomic.copywriting import generate_copywriting
from fashion_agent.skills.l1_atomic.erp_inventory import erp_inventory_query
from fashion_agent.skills.l1_atomic.sales_forecast import sales_forecast
from fashion_agent.skills.l1_atomic.trend_analysis import trend_analysis

__all__ = [
    "erp_inventory_query",
    "sales_forecast",
    "competitor_analysis",
    "trend_analysis",
    "generate_copywriting",
]
