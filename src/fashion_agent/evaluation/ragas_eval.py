"""Ragas integration for LLM-based evaluation.

When an OpenAI-compatible API key is configured (OpenAI / DeepSeek / Qwen
compatible mode, etc.), uses Ragas metrics (faithfulness, answer relevancy,
etc.) for deep quality evaluation.

When no LLM is available, falls back to the heuristic scorer.
"""

from __future__ import annotations

from typing import Any

from fashion_agent.core.config import get_settings
from fashion_agent.core.logging import get_logger
from fashion_agent.evaluation.scorer import AgentEvaluator, EvalReport

logger = get_logger(__name__)


def _ragas_available() -> bool:
    settings = get_settings()
    if not settings.has_llm:
        return False
    try:
        import ragas  # noqa: F401
        return True
    except ImportError:
        return False


async def ragas_evaluate_copywriting(
    instruction: str,
    generated_copy: str,
    article_context: str,
) -> dict[str, Any]:
    """Evaluate copywriting output using Ragas metrics.

    Metrics:
      - faithfulness: does the copy stay faithful to the product info?
      - answer_relevancy: is the copy relevant to the instruction?
    """
    if not _ragas_available():
        logger.info("ragas_not_available", reason="no LLM key or ragas not installed")
        return _heuristic_copy_eval(instruction, generated_copy, article_context)

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.llms import llm_factory
        from ragas.metrics import answer_relevancy, faithfulness

        from fashion_agent.core.llm import get_openai_compatible_client

        dataset = Dataset.from_dict({
            "question": [instruction],
            "answer": [generated_copy],
            "contexts": [[article_context]],
        })

        settings = get_settings()
        client = get_openai_compatible_client()
        if client is None:
            return _heuristic_copy_eval(instruction, generated_copy, article_context)

        ragas_llm = llm_factory(
            settings.openai_model,
            provider="openai",
            client=client,
        )
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=ragas_llm,
        )
        scores = result.to_pandas().iloc[0].to_dict()

        return {
            "backend": "ragas",
            "faithfulness": round(scores.get("faithfulness", 0), 3),
            "answer_relevancy": round(scores.get("answer_relevancy", 0), 3),
            "overall": round(
                (scores.get("faithfulness", 0) + scores.get("answer_relevancy", 0)) / 2,
                3,
            ),
        }
    except Exception as e:
        logger.warning("ragas_eval_failed", error=str(e))
        return _heuristic_copy_eval(instruction, generated_copy, article_context)


def _heuristic_copy_eval(
    instruction: str, generated_copy: str, article_context: str
) -> dict[str, Any]:
    """Fallback heuristic evaluation when Ragas/LLM not available."""
    instruction_words = set(instruction.lower().split())
    copy_words = set(generated_copy.lower().split())
    context_words = set(article_context.lower().split())

    relevancy = len(instruction_words & copy_words) / max(len(instruction_words), 1)
    faithfulness = len(context_words & copy_words) / max(len(context_words), 1)

    relevancy = min(relevancy * 2, 1.0)
    faithfulness = min(faithfulness * 3, 1.0)

    return {
        "backend": "heuristic",
        "faithfulness": round(faithfulness, 3),
        "answer_relevancy": round(relevancy, 3),
        "overall": round((faithfulness + relevancy) / 2, 3),
    }


async def ragas_evaluate_task(
    task_type: str, result: dict[str, Any]
) -> dict[str, Any]:
    """Unified evaluation entry point — Ragas when possible, heuristic otherwise.

    Returns both the heuristic AgentEvaluator report AND the Ragas scores
    (when available) so the caller always gets a complete picture.
    """
    evaluator = AgentEvaluator()
    heuristic_report: EvalReport = evaluator.evaluate(task_type, result)
    output: dict[str, Any] = {
        "heuristic": heuristic_report.to_dict(),
    }

    if task_type == "copywriting":
        results = result.get("results", [])
        if results:
            agent_out = results[0]
            copy = agent_out.get("selected_copy", "")
            instruction = result.get("instruction", "Generate copy")
            context = agent_out.get("article_id", "")
            ragas_scores = await ragas_evaluate_copywriting(
                instruction=instruction,
                generated_copy=copy,
                article_context=context,
            )
            output["ragas"] = ragas_scores

    return output
