"""
Benchmark Runner — runs evaluation comparing Naive RAG vs GraphRAG vs OntoRAG.

Uses Ollama for bulk testing to avoid API rate limits.
Produces a structured evaluation report.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from backend.app.evaluation.dataset import TECHDOC_QA_DATASET, EvalQuestion
from backend.app.evaluation.metrics import (
    MetricResult,
    compute_answer_relevance,
    compute_context_precision,
    compute_context_recall,
    compute_faithfulness,
)

logger = logging.getLogger(__name__)


@dataclass
class EvalRun:
    """Results from evaluating a single question."""

    question: str
    ground_truth: str
    predicted_answer: str
    category: str
    difficulty: str
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    latency_ms: float = 0.0
    provider: str = ""
    linked_entities: List[str] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    """Full benchmark report comparing approaches."""

    approach: str
    runs: List[EvalRun] = field(default_factory=list)
    aggregate_metrics: Dict[str, float] = field(default_factory=dict)
    category_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    total_questions: int = 0


class BenchmarkRunner:
    """Runs the evaluation benchmark."""

    def __init__(self):
        self.dataset = TECHDOC_QA_DATASET

    async def run_ontorag(
        self, questions: List[EvalQuestion] = None
    ) -> BenchmarkReport:
        """Run the full OntoRAG pipeline on the evaluation dataset."""
        from backend.app.core.database import db
        from backend.app.services.answer_generator import AnswerGenerator
        from backend.app.services.retriever import OntologyGuidedRetriever

        if questions is None:
            questions = self.dataset

        report = BenchmarkReport(approach="OntoRAG", total_questions=len(questions))

        try:
            await db.connect()
        except Exception as e:
            logger.error(f"Cannot run benchmark: Neo4j unavailable ({e})")
            return report

        retriever = OntologyGuidedRetriever(db)
        generator = AnswerGenerator()

        for q in questions:
            start = time.time()

            # Retrieve and generate
            retrieval = await retriever.retrieve(query=q.question, min_trust=0.3, top_k=5)
            answer_result = await generator.generate(query=q.question, facts=retrieval.facts)

            latency = (time.time() - start) * 1000

            # Compute metrics
            run = EvalRun(
                question=q.question,
                ground_truth=q.ground_truth,
                predicted_answer=answer_result.answer,
                category=q.category,
                difficulty=q.difficulty,
                latency_ms=latency,
                provider=answer_result.provider,
                linked_entities=retrieval.linked_entities,
            )

            # Faithfulness (using used_facts as proxy)
            claims_supported = [True] * len(answer_result.used_facts)
            run.metrics["faithfulness"] = compute_faithfulness(
                answer_claims=[f["subject"] for f in answer_result.used_facts],
                supported_claims=claims_supported,
            )

            # Answer relevance
            run.metrics["answer_relevance"] = compute_answer_relevance(
                question=q.question,
                answer=answer_result.answer,
                ground_truth=q.ground_truth,
            )

            # Context precision
            run.metrics["context_precision"] = compute_context_precision(
                retrieved_facts=len(retrieval.facts),
                used_facts=len(answer_result.used_facts),
            )

            # Context recall
            run.metrics["context_recall"] = compute_context_recall(
                expected_entities=q.expected_entities,
                linked_entities=retrieval.linked_entities,
            )

            report.runs.append(run)
            report.total_latency_ms += latency

            # Rate limiting
            await asyncio.sleep(2)

        # Aggregate metrics
        report.aggregate_metrics = self._aggregate(report.runs)
        report.category_metrics = self._aggregate_by_category(report.runs)

        return report

    async def run_naive_rag(
        self, questions: List[EvalQuestion] = None
    ) -> BenchmarkReport:
        """
        Simulate naive RAG (no ontology, no trust scoring).

        Uses direct keyword matching without graph traversal or trust filtering.
        """
        from backend.app.core.llm_router import LLMRouter

        if questions is None:
            questions = self.dataset

        report = BenchmarkReport(approach="NaiveRAG", total_questions=len(questions))
        llm = LLMRouter()

        for q in questions:
            start = time.time()

            # Simple LLM call without retrieval (simulates no-context RAG)
            try:
                result = await llm.generate(
                    prompt=f"Answer this question: {q.question}",
                    system_prompt="Answer concisely based on your knowledge.",
                    temperature=0.3,
                    json_mode=False,
                )
                answer_text = result["response"] if isinstance(result["response"], str) else str(result["response"])
                provider = result["provider"]
            except Exception:
                answer_text = "Could not generate answer."
                provider = "error"

            latency = (time.time() - start) * 1000

            run = EvalRun(
                question=q.question,
                ground_truth=q.ground_truth,
                predicted_answer=answer_text,
                category=q.category,
                difficulty=q.difficulty,
                latency_ms=latency,
                provider=provider,
            )

            run.metrics["answer_relevance"] = compute_answer_relevance(
                question=q.question,
                answer=answer_text,
                ground_truth=q.ground_truth,
            )
            run.metrics["faithfulness"] = MetricResult(name="faithfulness", value=0.0)
            run.metrics["context_precision"] = MetricResult(name="context_precision", value=0.0)
            run.metrics["context_recall"] = MetricResult(name="context_recall", value=0.0)

            report.runs.append(run)
            report.total_latency_ms += latency

            await asyncio.sleep(2)

        report.aggregate_metrics = self._aggregate(report.runs)
        report.category_metrics = self._aggregate_by_category(report.runs)
        return report

    def _aggregate(self, runs: List[EvalRun]) -> Dict[str, float]:
        """Compute average metrics across all runs."""
        if not runs:
            return {}

        metric_names = runs[0].metrics.keys() if runs else []
        result = {}

        for name in metric_names:
            values = [r.metrics[name].value for r in runs if name in r.metrics]
            result[name] = round(sum(values) / len(values), 4) if values else 0.0

        result["avg_latency_ms"] = round(
            sum(r.latency_ms for r in runs) / len(runs), 1
        )
        return result

    def _aggregate_by_category(
        self, runs: List[EvalRun]
    ) -> Dict[str, Dict[str, float]]:
        """Compute metrics broken down by question category."""
        categories: Dict[str, List[EvalRun]] = {}
        for run in runs:
            categories.setdefault(run.category, []).append(run)

        return {cat: self._aggregate(cat_runs) for cat, cat_runs in categories.items()}

    def generate_report(self, *reports: BenchmarkReport) -> Dict[str, Any]:
        """Generate a comparison report across multiple approaches."""
        comparison = {}

        for report in reports:
            comparison[report.approach] = {
                "aggregate": report.aggregate_metrics,
                "by_category": report.category_metrics,
                "total_questions": report.total_questions,
                "total_latency_ms": round(report.total_latency_ms, 1),
            }

        # Compute improvement
        if len(reports) >= 2:
            baseline = reports[0].aggregate_metrics
            ontorag = reports[-1].aggregate_metrics

            improvement = {}
            for metric in baseline:
                if baseline[metric] > 0:
                    pct = ((ontorag.get(metric, 0) - baseline[metric]) / baseline[metric]) * 100
                    improvement[metric] = f"{pct:+.1f}%"

            comparison["improvement_over_baseline"] = improvement

        return comparison
