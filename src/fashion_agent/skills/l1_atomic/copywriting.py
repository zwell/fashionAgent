"""L1 Skill: Copywriting — generate product descriptions and marketing copy."""

from __future__ import annotations

from fashion_agent.core.data_loader import get_article_by_id
from fashion_agent.skills.base import skill

_COPY_TEMPLATES = {
    "product_description": (
        "【{prod_name}】\n\n"
        "{detail_desc}\n\n"
        "颜色：{colour} | 版型：{style} | 品类：{category}\n\n"
        "这款{prod_name}以{colour}色呈现，{style}风格设计，"
        "适合日常穿搭。{material_hint}"
    ),
    "promotion": (
        "🔥 限时特惠 | {prod_name}\n\n"
        "原价 ¥{price} → 特惠价 ¥{sale_price}\n\n"
        "{detail_desc}\n\n"
        "经典{colour}色，{style}剪裁，百搭不挑人。\n"
        "数量有限，手慢无！"
    ),
    "social_media": (
        "✨ 新品上线 ✨\n\n"
        "{prod_name} | {colour}\n\n"
        "{detail_desc}\n\n"
        "#{category} #{colour} #{style} #新品推荐 #穿搭灵感"
    ),
}


@skill(
    name="文案生成",
    description="根据商品信息生成产品描述、促销文案或社交媒体文案",
    tags=["文案", "营销", "内容"],
    examples=[
        "给这款连衣裙写一段产品描述",
        "生成一条促销文案",
        "写一条小红书风格的推荐文案",
    ],
)
async def generate_copywriting(
    article_id: str,
    style: str = "product_description",
    price: float | None = None,
    discount_pct: float = 0.2,
) -> dict:
    article = get_article_by_id(article_id)
    if article is None:
        return {"success": False, "message": f"Article {article_id} not found"}

    if style not in _COPY_TEMPLATES:
        style = "product_description"

    material_hint = ""
    desc_lower = article.detail_desc.lower()
    if "cotton" in desc_lower:
        material_hint = "优质棉面料，亲肤透气，四季百搭之选。"
    elif "wool" in desc_lower:
        material_hint = "羊毛混纺面料，保暖舒适，秋冬必备。"
    elif "linen" in desc_lower:
        material_hint = "亚麻混纺面料，轻盈透气，夏日首选。"
    elif "jersey" in desc_lower:
        material_hint = "柔软针织面料，弹性舒适，日常必备。"
    elif "satin" in desc_lower:
        material_hint = "缎面材质，光泽优雅，适合出席各种场合。"
    else:
        material_hint = "精选面料，品质之选。"

    base_price = price or 199.0
    sale_price = round(base_price * (1 - discount_pct), 2)

    copy = _COPY_TEMPLATES[style].format(
        prod_name=article.prod_name,
        detail_desc=article.detail_desc,
        colour=article.colour_group_name,
        style=article.graphical_appearance_name,
        category=article.product_type_name,
        material_hint=material_hint,
        price=base_price,
        sale_price=sale_price,
    )

    return {
        "success": True,
        "article_id": article_id,
        "copy_style": style,
        "copy_text": copy,
        "word_count": len(copy),
    }
