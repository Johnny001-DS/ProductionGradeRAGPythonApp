"""
RAG Evaluation Module using RAGAS

Provides on-demand evaluation of RAG system outputs using RAGAS metrics:
- Faithfulness: How factually consistent is the answer with the context?
- Answer Relevance: How well does the answer address the question?
- Context Relevance: How relevant are the retrieved contexts to the question?
- Context Recall: What fraction of the expected information is in the context?
"""

import logging
from typing import Optional
from ragas.metrics import (
    faithfulness,
    answer_relevance,
    context_relevance,
    context_recall,
)
from ragas.evaluation import evaluate
from datasets import Dataset
from custom_types import RAGEvaluationMetrics

logger = logging.getLogger(__name__)


def evaluate_query(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: Optional[str] = None,
) -> RAGEvaluationMetrics:
    """
    Evaluate a single RAG query output against its retrieved contexts.

    Args:
        question: The user's question
        answer: The LLM-generated answer
        contexts: List of retrieved context chunks
        ground_truth: Optional ground truth answer for additional metrics

    Returns:
        RAGEvaluationMetrics with computed scores
    """
    try:
        # Create a dataset with a single sample
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }

        if ground_truth:
            data["ground_truth"] = [ground_truth]

        dataset = Dataset.from_dict(data)

        # Select metrics to evaluate
        metrics = [
            faithfulness,
            answer_relevance,
            context_relevance,
        ]

        # Only add context_recall if ground_truth is provided
        if ground_truth:
            metrics.append(context_recall)

        # Run evaluation
        results = evaluate(dataset, metrics=metrics)

        # Extract scores
        scores = RAGEvaluationMetrics(
            faithfulness=float(results["faithfulness"][0])
            if "faithfulness" in results
            else None,
            answer_relevance=float(results["answer_relevance"][0])
            if "answer_relevance" in results
            else None,
            context_relevance=float(results["context_relevance"][0])
            if "context_relevance" in results
            else None,
            context_recall=float(results["context_recall"][0])
            if "context_recall" in results and ground_truth
            else None,
        )

        logger.info(f"Evaluation complete - Scores: {scores.model_dump()}")
        return scores

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return RAGEvaluationMetrics()


def evaluate_batch(
    queries: list[dict],
) -> dict:
    """
    Evaluate multiple RAG query outputs in batch.

    Args:
        queries: List of dicts with 'question', 'answer', 'contexts', optional 'ground_truth'

    Returns:
        Dictionary with aggregate metrics and per-query scores
    """
    try:
        questions = [q["question"] for q in queries]
        answers = [q["answer"] for q in queries]
        contexts = [q["contexts"] for q in queries]
        ground_truths = [q.get("ground_truth") for q in queries]
        has_ground_truth = any(gt is not None for gt in ground_truths)

        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
        }

        if has_ground_truth:
            data["ground_truth"] = ground_truths

        dataset = Dataset.from_dict(data)

        metrics = [
            faithfulness,
            answer_relevance,
            context_relevance,
        ]

        if has_ground_truth:
            metrics.append(context_recall)

        results = evaluate(dataset, metrics=metrics)

        # Calculate aggregates
        aggregate_scores = {}
        for metric_name in ["faithfulness", "answer_relevance", "context_relevance", "context_recall"]:
            if metric_name in results:
                scores = [float(s) for s in results[metric_name]]
                aggregate_scores[metric_name] = {
                    "mean": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "scores": scores,
                }

        logger.info(f"Batch evaluation complete - {len(queries)} samples evaluated")
        return {
            "num_samples": len(queries),
            "aggregate_scores": aggregate_scores,
            "per_query_results": results,
        }

    except Exception as e:
        logger.error(f"Batch evaluation failed: {str(e)}")
        return {"error": str(e), "num_samples": len(queries)}


def generate_evaluation_report(evaluation_metrics: RAGEvaluationMetrics) -> str:
    """
    Generate a human-readable evaluation report.

    Args:
        evaluation_metrics: RAGEvaluationMetrics object

    Returns:
        Formatted report string
    """
    report_lines = ["=" * 50, "RAG Evaluation Report", "=" * 50]

    if evaluation_metrics.faithfulness is not None:
        score = evaluation_metrics.faithfulness
        status = "✓ Excellent" if score > 0.8 else "⚠ Good" if score > 0.6 else "✗ Needs Improvement"
        report_lines.append(f"Faithfulness:     {score:.3f} {status}")

    if evaluation_metrics.answer_relevance is not None:
        score = evaluation_metrics.answer_relevance
        status = "✓ Excellent" if score > 0.8 else "⚠ Good" if score > 0.6 else "✗ Needs Improvement"
        report_lines.append(f"Answer Relevance: {score:.3f} {status}")

    if evaluation_metrics.context_relevance is not None:
        score = evaluation_metrics.context_relevance
        status = "✓ Excellent" if score > 0.8 else "⚠ Good" if score > 0.6 else "✗ Needs Improvement"
        report_lines.append(f"Context Relevance: {score:.3f} {status}")

    if evaluation_metrics.context_recall is not None:
        score = evaluation_metrics.context_recall
        status = "✓ Excellent" if score > 0.8 else "⚠ Good" if score > 0.6 else "✗ Needs Improvement"
        report_lines.append(f"Context Recall:   {score:.3f} {status}")

    report_lines.extend(["=" * 50, ""])
    return "\n".join(report_lines)
