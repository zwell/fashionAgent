"""OpenAI-compatible LLM clients (OpenAI / DeepSeek / Qwen DashScope 兼容模式).

All three use the same request shape; only ``base_url`` and model name differ.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fashion_agent.core.config import get_settings

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI
    from openai import OpenAI


def openai_compatible_client_kwargs() -> dict | None:
    """Keyword args for ``OpenAI(**kwargs)`` / LangChain, or ``None`` if no API key."""
    settings = get_settings()
    if not settings.has_llm:
        return None
    kw: dict = {"api_key": settings.openai_api_key}
    base = settings.resolved_openai_api_base
    if base:
        kw["base_url"] = base
    return kw


def get_openai_compatible_client() -> OpenAI | None:
    """Sync OpenAI SDK client pointing at the configured provider."""
    from openai import OpenAI

    kw = openai_compatible_client_kwargs()
    if kw is None:
        return None
    return OpenAI(**kw)


def get_chat_openai() -> ChatOpenAI | None:
    """LangChain ``ChatOpenAI`` for the configured provider (agents / tools)."""
    from langchain_openai import ChatOpenAI

    kw = openai_compatible_client_kwargs()
    if kw is None:
        return None
    settings = get_settings()
    lc_kw: dict = {
        "model": settings.openai_model,
        "openai_api_key": settings.openai_api_key,
    }
    if kw.get("base_url"):
        lc_kw["openai_api_base"] = kw["base_url"]
    return ChatOpenAI(**lc_kw)
