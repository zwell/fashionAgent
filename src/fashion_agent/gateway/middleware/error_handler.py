"""Global error handling middleware — catches exceptions and returns structured JSON."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from fashion_agent.core.exceptions import (
    AgentError,
    FashionAgentError,
    SkillExecutionError,
    SkillNotFoundError,
    TaskError,
)
from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except SkillNotFoundError as e:
            logger.warning("skill_not_found", skill=e.skill_name, path=request.url.path)
            return JSONResponse(
                status_code=404,
                content={"error": "skill_not_found", "detail": str(e)},
            )
        except SkillExecutionError as e:
            logger.error("skill_failed", skill=e.skill_name, reason=e.reason)
            return JSONResponse(
                status_code=500,
                content={"error": "skill_execution_error", "detail": str(e)},
            )
        except AgentError as e:
            logger.error("agent_error", agent=e.agent_name, reason=e.reason)
            return JSONResponse(
                status_code=500,
                content={"error": "agent_error", "detail": str(e)},
            )
        except TaskError as e:
            logger.error("task_error", task_id=e.task_id, reason=e.reason)
            return JSONResponse(
                status_code=500,
                content={"error": "task_error", "detail": str(e)},
            )
        except FashionAgentError as e:
            logger.error("fashion_agent_error", error=str(e))
            return JSONResponse(
                status_code=500,
                content={"error": "internal_error", "detail": str(e)},
            )
        except Exception as e:
            logger.error("unhandled_exception", error=str(e), type=type(e).__name__)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "detail": str(e),
                    "type": type(e).__name__,
                },
            )
