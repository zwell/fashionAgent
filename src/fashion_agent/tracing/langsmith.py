"""LangSmith tracing integration.

When LANGCHAIN_TRACING_V2=true and LANGSMITH_API_KEY is set,
all LangChain/LangGraph calls are automatically traced.

This module provides additional helpers for custom span annotation.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from fashion_agent.core.config import get_settings
from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


def configure_tracing() -> None:
    """Set up LangSmith environment variables from our settings."""
    settings = get_settings()
    if settings.has_langsmith:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        logger.info("langsmith_tracing_enabled", project=settings.langsmith_project)
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("langsmith_tracing_disabled")


@contextmanager
def trace_span(name: str, metadata: dict[str, Any] | None = None) -> Generator[dict, None, None]:
    """Lightweight context manager that logs span-like events.

    When LangSmith is active, these are captured automatically via the
    LangChain callback system. This helper provides a consistent local log.
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
