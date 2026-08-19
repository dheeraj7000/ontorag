"""Evaluation & Benchmark endpoints."""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
async def run_benchmark(approach: str = "ontorag"):
    """
    Run the evaluation benchmark.

    Approaches: 'ontorag', 'naive', 'both'
    """
    from backend.app.evaluation.benchmark import BenchmarkRunner

    runner = BenchmarkRunner()

    if approach == "naive":
        naive_report = await runner.run_naive_rag()
        return runner.generate_report(naive_report)
    elif approach == "both":
        naive_report = await runner.run_naive_rag()
        ontorag_report = await runner.run_ontorag()
        return runner.generate_report(naive_report, ontorag_report)
    else:
        ontorag_report = await runner.run_ontorag()
        return runner.generate_report(ontorag_report)


@router.get("/dataset")
async def get_dataset_info():
    """Get information about the evaluation dataset."""
    from backend.app.evaluation.dataset import TECHDOC_QA_DATASET

    categories = {}
    difficulties = {}

    for q in TECHDOC_QA_DATASET:
        categories[q.category] = categories.get(q.category, 0) + 1
        difficulties[q.difficulty] = difficulties.get(q.difficulty, 0) + 1

    return {
        "total_questions": len(TECHDOC_QA_DATASET),
        "categories": categories,
        "difficulties": difficulties,
        "sample_questions": [
            {"question": q.question, "category": q.category, "difficulty": q.difficulty}
            for q in TECHDOC_QA_DATASET[:5]
        ],
    }
