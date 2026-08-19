"""
Evaluation Metrics — measures RAG quality across multiple dimensions.

Metrics:
- Faithfulness: fraction of answer claims supported by context
- Answer Relevance: how well the answer addresses the question
- Context Precision: fraction of retrieved facts used in the answer
- Context Recall: fraction of ground truth covered by retrieved facts
- Hallucination F1: precision/recall of hallucination detection
- Trust Accuracy: correlation between GNN scores and manual labels
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    """Result of computing a single metric."""

    name: str
    value: float
    details: Dict[str, Any] = field(default_factory=dict)


def compute_faithfulness(
    answer_claims: List[str],
    supported_claims: List[bool],
) -> MetricResult:
    """
    Faithfulness = # supported claims / # total claims.

    Measures how many claims in the answer are backed by the KG.
    """
    if not answer_claims:
        return MetricResult(name="faithfulness", value=1.0)

    total = len(answer_claims)
    supported = sum(1 for s in supported_claims if s)
    score = supported / total

    return MetricResult(
        name="faithfulness",
        value=round(score, 4),
        details={"total_claims": total, "supported": supported, "unsupported": total - supported},
    )


def compute_answer_relevance(
    question: str,
    answer: str,
    ground_truth: str,
) -> MetricResult:
    """
    Answer Relevance — word overlap between answer and ground truth.

    Simple token-level F1 as a proxy (LLM-based scoring in production).
    """
    answer_tokens = set(answer.lower().split())
    truth_tokens = set(ground_truth.lower().split())

    if not truth_tokens:
        return MetricResult(name="answer_relevance", value=0.0)

    overlap = answer_tokens & truth_tokens
    precision = len(overlap) / len(answer_tokens) if answer_tokens else 0
    recall = len(overlap) / len(truth_tokens) if truth_tokens else 0

    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return MetricResult(
        name="answer_relevance",
        value=round(f1, 4),
        details={"precision": round(precision, 4), "recall": round(recall, 4)},
    )


def compute_context_precision(
    retrieved_facts: int,
    used_facts: int,
) -> MetricResult:
    """
    Context Precision = # facts used in answer / # facts retrieved.

    Measures retrieval efficiency — are we retrieving useful facts?
    """
    if retrieved_facts == 0:
        return MetricResult(name="context_precision", value=0.0)

    score = used_facts / retrieved_facts
    return MetricResult(
        name="context_precision",
        value=round(score, 4),
        details={"retrieved": retrieved_facts, "used": used_facts},
    )


def compute_context_recall(
    expected_entities: List[str],
    linked_entities: List[str],
) -> MetricResult:
    """
    Context Recall = # expected entities found / # expected entities.

    Measures whether retrieval finds the right entities.
    """
    if not expected_entities:
        return MetricResult(name="context_recall", value=1.0)

    found = 0
    linked_lower = [e.lower() for e in linked_entities]

    for expected in expected_entities:
        if any(expected.lower() in linked for linked in linked_lower):
            found += 1

    score = found / len(expected_entities)
    return MetricResult(
        name="context_recall",
        value=round(score, 4),
        details={"expected": expected_entities, "found": found},
    )


def compute_hallucination_f1(
    predictions: List[bool],  # True = hallucination detected
    ground_truth: List[bool],  # True = actually hallucinated
) -> MetricResult:
    """
    Hallucination Detection F1.

    precision = correctly detected hallucinations / all detected hallucinations
    recall = correctly detected hallucinations / all actual hallucinations
    """
    if not predictions or not ground_truth:
        return MetricResult(name="hallucination_f1", value=0.0)

    tp = sum(1 for p, g in zip(predictions, ground_truth) if p and g)
    fp = sum(1 for p, g in zip(predictions, ground_truth) if p and not g)
    fn = sum(1 for p, g in zip(predictions, ground_truth) if not p and g)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return MetricResult(
        name="hallucination_f1",
        value=round(f1, 4),
        details={
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
        },
    )


def compute_trust_accuracy(
    predicted_scores: List[float],
    threshold: float = 0.75,
    high_confidence_indices: List[int] = None,
) -> MetricResult:
    """
    Trust Accuracy — what fraction of high-confidence entities
    get trust scores above the threshold.
    """
    if not predicted_scores:
        return MetricResult(name="trust_accuracy", value=0.0)

    if high_confidence_indices is None:
        # Default: top 50% by score should be above threshold
        high_confidence_indices = list(range(len(predicted_scores) // 2))

    if not high_confidence_indices:
        return MetricResult(name="trust_accuracy", value=0.0)

    correct = sum(
        1
        for idx in high_confidence_indices
        if idx < len(predicted_scores) and predicted_scores[idx] >= threshold
    )
    accuracy = correct / len(high_confidence_indices)

    return MetricResult(
        name="trust_accuracy",
        value=round(accuracy, 4),
        details={"threshold": threshold, "correct": correct, "total": len(high_confidence_indices)},
    )
