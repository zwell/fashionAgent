"""L1 Skill: Trend Analysis — identify fashion trends for a category/season."""

from __future__ import annotations

from fashion_agent.skills.base import skill

_TREND_DATA = {
    "spring": {
        "colors": ["Lavender", "Sage Green", "Soft Pink", "Sky Blue"],
        "materials": ["Linen", "Organic Cotton", "Recycled Polyester"],
        "styles": ["Oversized", "Layered", "Cropped", "Flowy"],
        "patterns": ["Floral", "Pastel Stripes", "Gingham"],
    },
    "summer": {
        "colors": ["Coral", "Turquoise", "Sunshine Yellow", "White"],
        "materials": ["Linen", "Cotton", "Rayon", "Mesh"],
        "styles": ["Cut-out", "Backless", "Mini", "Resort"],
        "patterns": ["Tropical", "Tie-dye", "Abstract"],
    },
    "autumn": {
        "colors": ["Burgundy", "Rust", "Olive", "Camel"],
        "materials": ["Wool", "Cashmere", "Leather", "Corduroy"],
        "styles": ["Tailored", "Layered", "Oversized", "Structured"],
        "patterns": ["Plaid", "Houndstooth", "Animal Print"],
    },
    "winter": {
        "colors": ["Deep Red", "Emerald", "Navy", "Cream"],
        "materials": ["Wool", "Faux Fur", "Velvet", "Down"],
        "styles": ["Cocooning", "Maxi", "Structured", "Minimal"],
        "patterns": ["Fair Isle", "Tartan", "Solid"],
    },
}


@skill(
    name="趋势分析",
    description="分析指定季节或品类的时尚趋势，包括流行色彩、材质、版型和图案",
    tags=["趋势", "时尚", "设计"],
    examples=[
        "今年春季流行什么颜色",
        "秋冬有什么面料趋势",
    ],
)
async def trend_analysis(season: str = "spring") -> dict:
    season_key = season.lower().strip()
    if season_key not in _TREND_DATA:
        return {
            "success": False,
            "message": f"Unknown season: {season}. Use: spring, summer, autumn, winter",
        }

    trends = _TREND_DATA[season_key]
    return {
        "success": True,
        "season": season_key,
        "trending_colors": trends["colors"],
        "trending_materials": trends["materials"],
        "trending_styles": trends["styles"],
        "trending_patterns": trends["patterns"],
        "summary": (
            f"{season_key.title()} trends emphasize {trends['colors'][0]} and "
            f"{trends['colors'][1]} tones, with {trends['materials'][0]} and "
            f"{trends['materials'][1]} as key fabrics. Expect {trends['styles'][0]} "
            f"and {trends['styles'][1]} silhouettes with {trends['patterns'][0]} prints."
        ),
    }
