"""API v1 router — aggregates all route modules."""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    admin,
    evaluation,
    graph,
    hallucination,
    ingest,
    query,
    trust,
)

api_router = APIRouter()

api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(query.router, prefix="/query", tags=["Query"])
api_router.include_router(
    hallucination.router, prefix="/hallucination", tags=["Hallucination"]
)
api_router.include_router(graph.router, prefix="/graph", tags=["Graph"])
api_router.include_router(trust.router, prefix="/trust", tags=["Trust Scoring"])
api_router.include_router(evaluation.router, prefix="/eval", tags=["Evaluation"])
