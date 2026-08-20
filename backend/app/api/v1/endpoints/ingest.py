"""Document ingestion endpoint — upload, parse, extract, build KG."""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from backend.app.core.config import settings
from backend.app.core.rate_limit import rate_limit
from backend.app.services.ingestion_pipeline import IngestionStats, ingestion_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory tracking of ingestion jobs (would be Redis/DB in production)
_ingestion_jobs: dict[str, IngestionStats] = {}


async def _run_ingestion(file_path: Path, file_id: str, filename: str) -> None:
    """Background task: run the full ingestion pipeline."""
    stats = await ingestion_pipeline.ingest(file_path, file_id, filename)
    _ingestion_jobs[file_id] = stats


@router.post("/", dependencies=[Depends(rate_limit("ingest"))])
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Ingest a document into the knowledge graph.

    Accepts PDF, Markdown, HTML, or TXT files. The document is saved,
    then processed asynchronously through the extraction pipeline:
    parse → chunk → extract (LLM) → validate (ontology) → insert (Neo4j).
    """
    # Validate file type
    allowed_extensions = {".pdf", ".md", ".html", ".txt"}

    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed_extensions}",
        )

    # Bound worst-case cost/memory on this small, unauthenticated instance —
    # read one byte past the limit rather than the whole body before checking.
    max_bytes = settings.max_upload_bytes
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max upload size is {max_bytes // (1024 * 1024)}MB.",
        )

    # Save uploaded file
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    file_path = upload_dir / filename

    file_path.write_bytes(content)
    logger.info(f"Saved upload: {filename} ({len(content)} bytes)")

    # Initialize status tracking
    _ingestion_jobs[file_id] = IngestionStats(
        file_id=file_id, filename=file.filename or filename, status="queued"
    )

    # Run ingestion in background
    background_tasks.add_task(_run_ingestion, file_path, file_id, file.filename or filename)

    return {
        "status": "accepted",
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": len(content),
        "message": "Document accepted for processing. Check /api/v1/ingest/status/{file_id} for progress.",
    }


@router.get("/status/{file_id}")
async def get_ingestion_status(file_id: str):
    """Check the status of a document ingestion job."""
    if file_id not in _ingestion_jobs:
        raise HTTPException(status_code=404, detail=f"Ingestion job '{file_id}' not found")

    stats = _ingestion_jobs[file_id]
    return {
        "file_id": stats.file_id,
        "filename": stats.filename,
        "status": stats.status,
        "total_chunks": stats.total_chunks,
        "entities_extracted": stats.entities_extracted,
        "relations_extracted": stats.relations_extracted,
        "violations": stats.violations,
        "entities_inserted": stats.entities_inserted,
        "relations_inserted": stats.relations_inserted,
        "errors": stats.errors,
    }
