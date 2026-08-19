"""Trust scoring endpoint — trigger GNN trust score computation."""

import logging

from fastapi import APIRouter

from backend.app.core.database import db
from backend.app.services.gnn_trust import TrustScoringPipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/compute")
async def compute_trust_scores():
    """
    Trigger GNN trust score computation.

    Fetches the full graph from Neo4j, trains the GAT model on pseudo-labels,
    predicts trust scores, and updates all nodes in Neo4j.
    """
    try:
        await db.connect()
    except Exception as e:
        return {"status": "error", "message": f"Neo4j not available: {e}"}

    pipeline = TrustScoringPipeline()
    result = await pipeline.update_trust_scores(db)
    return result


@router.get("/status")
async def trust_scoring_status():
    """Get the current trust scoring status and model info."""
    from pathlib import Path

    model_path = Path("models/trust_gnn.pt")

    return {
        "model_exists": model_path.exists(),
        "model_path": str(model_path),
        "model_size_bytes": model_path.stat().st_size if model_path.exists() else 0,
    }
