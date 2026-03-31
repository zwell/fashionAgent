"""LangSmith tracing integration.

When LANGCHAIN_TRACING_V2=true and LANGSMITH_API_KEY is set,
all LangChain/LangGraph calls are automatically traced via environment
variables. This module:
  1. Configures the env vars from our Settings on startup
  2. Provides a callback factory for LangGraph .ainvoke() calls
  3. Offers a trace_span context manager for custom instrumentation
"""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from fashion_agent.core.config import get_settings
from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)

_TRACING_ENABLED = False


def configure_tracing() -> None:
    """Set LangSmith env vars from Settings. Call once at startup."""
    global _TRACING_ENABLED
    settings = get_settings()

    if settings.has_langsmith:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        _TRACING_ENABLED = True
        logger.info(
            "langsmith_tracing_enabled", project=settings.langsmith_project
        )
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        _TRACING_ENABLED = False
        logger.info("langsmith_tracing_disabled", reason="no API key configured")


def is_tracing_enabled() -> bool:
    return _TRACING_ENABLED


def get_langsmith_callback() -> list:
    """Return a LangSmith callback handler list if tracing is enabled.

    Pass the return value as ``config={"callbacks": get_langsmith_callback()}``
    to any LangGraph ``.ainvoke()`` call.
    """
    if not _TRACING_ENABLED:
        return []
    try:
        from langchain_core.tracers import LangChainTracer
        from langsmith import Client

        client = Client()
        tracer = LangChainTracer(client=client)
        return [tracer]
    except Exception as e:
        logger.warning("langsmith_callback_failed", error=str(e))
        return []


@contextmanager
def trace_span(
    name: str, metadata: dict[str, Any] | None = None
) -> Generator[dict, None, None]:
    """Lightweight span logger.

    When LangSmith is active, LangGraph nodes are already traced
    automatically. This helper adds custom spans for non-LangGraph code.
    """
    span: dict[str, Any] = {"name": name, "metadata": metadata or {}}
    logger.info("span_start", **span)
    try:
        yield span
    except Exception:
        logger.error("span_error", **span)
        raise
    finally:
        logger.info("span_end", **span)
