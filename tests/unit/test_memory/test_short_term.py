"""Tests for short-term memory (in-memory fallback mode)."""

from __future__ import annotations

import pytest

from fashion_agent.memory.short_term import ShortTermMemory


@pytest.fixture
async def mem():
    m = ShortTermMemory(redis_url=None)
    await m.connect()
    yield m
    await m.close()


class TestShortTermMemory:
    async def test_set_and_get(self, mem: ShortTermMemory):
        await mem.set("key1", {"hello": "world"})
        result = await mem.get("key1")
        assert result == {"hello": "world"}

    async def test_get_nonexistent(self, mem: ShortTermMemory):
        result = await mem.get("no_such_key")
        assert result is None

    async def test_delete(self, mem: ShortTermMemory):
        await mem.set("key2", "value")
        await mem.delete("key2")
        assert await mem.get("key2") is None

    async def test_exists(self, mem: ShortTermMemory):
        await mem.set("key3", 42)
        assert await mem.exists("key3") is True
        assert await mem.exists("nope") is False

    async def test_session_operations(self, mem: ShortTermMemory):
        await mem.set_session("sess1", {"user": "test"})
        session = await mem.get_session("sess1")
        assert session["user"] == "test"

    async def test_append_to_session(self, mem: ShortTermMemory):
        await mem.set_session("sess2", {})
        await mem.append_to_session("sess2", "events", {"action": "click"})
        await mem.append_to_session("sess2", "events", {"action": "scroll"})
        session = await mem.get_session("sess2")
        assert len(session["events"]) == 2
