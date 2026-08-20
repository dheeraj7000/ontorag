"""Admin endpoint — demo-mode knowledge graph reset.

There's no authentication or per-user isolation yet: every visitor shares
one Neo4j graph. Until that changes, the frontend calls this once on every
page load so each visit starts from a clean slate instead of showing
whatever a previous visitor ingested.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.app.core.config import settings
from backend.app.core.database import db
from backend.app.core.rate_limit import rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reset", dependencies=[Depends(rate_limit("admin_reset", per_minute=10))])
async def reset_demo():
    """Wipe the knowledge graph and uploaded files for a clean demo state."""
    if not settings.demo_reset_enabled:
        return {"status": "skipped", "reason": "demo_reset_enabled is false"}

    graph_cleared = False
    try:
        await db.connect()
        await db.execute_write("MATCH (n) DETACH DELETE n")
        graph_cleared = True
    except Exception as e:
        logger.warning(f"Demo reset: could not clear graph: {e}")

    uploads_cleared = 0
    upload_dir = Path(settings.upload_dir)
    if upload_dir.exists():
        for f in upload_dir.iterdir():
            if f.is_file() and f.name != ".gitkeep":
                try:
                    f.unlink()
                    uploads_cleared += 1
                except OSError as e:
                    logger.warning(f"Demo reset: could not remove {f}: {e}")

    # Also clear the in-memory ingestion-job tracker so old job ids don't
    # accumulate across resets (avoided import cycle: local import).
    from backend.app.api.v1.endpoints.ingest import _ingestion_jobs

    _ingestion_jobs.clear()

    logger.info(
        f"Demo reset: graph_cleared={graph_cleared}, uploads_removed={uploads_cleared}"
    )
    return {
        "status": "ok",
        "graph_cleared": graph_cleared,
        "uploads_removed": uploads_cleared,
    }
