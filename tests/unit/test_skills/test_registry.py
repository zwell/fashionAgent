"""Tests for skill registry and discovery."""

from __future__ import annotations

import pytest

from fashion_agent.core.exceptions import SkillNotFoundError
from fashion_agent.skills.registry import get_registry


class TestSkillRegistry:
    def test_skills_are_registered(self):
        registry = get_registry()
        all_skills = registry.list_skills()
        assert len(all_skills) >= 10

    def test_filter_by_level(self):
        registry = get_registry()
        l1 = registry.list_skills(level="L1")
        l2 = registry.list_skills(level="L2")
        assert len(l1) >= 7
        assert len(l2) >= 3

    def test_filter_by_tag(self):
        registry = get_registry()
        inventory_skills = registry.list_skills(tag="库存")
        assert len(inventory_skills) >= 1

    def test_search_by_keyword(self):
        registry = get_registry()
        results = registry.search("库存")
        assert len(results) >= 1
        assert results[0].name == "查询库存"

    def test_search_copywriting(self):
        registry = get_registry()
        results = registry.search("文案")
        assert len(results) >= 1

    def test_get_nonexistent_skill(self):
        registry = get_registry()
        with pytest.raises(SkillNotFoundError):
            registry.get("不存在的技能")

    def test_tool_schemas(self):
        registry = get_registry()
        schemas = registry.to_tool_schemas()
        assert len(schemas) >= 10
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema

    async def test_invoke_skill(self):
        registry = get_registry()
        result = await registry.invoke("查询库存", article_id="0108775015")
        assert result["success"] is True
