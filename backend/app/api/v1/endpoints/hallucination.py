"""Hallucination detection endpoint — cross-check claims against the KG."""

import logging
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.core.database import db
from backend.app.services.hallucination_detector import HallucinationDetector

logger = logging.getLogger(__name__)
router = APIRouter()


class HallucinationCheckRequest(BaseModel):
    """Request to check an answer for hallucinations."""

    answer: str = Field(..., description="The LLM-generated answer to check")
    context: str = Field(
        default="", description="Original context used to generate the answer"
    )


class ClaimVerificationResponse(BaseModel):
    """Result of verifying a single claim."""

    claim: str
    supported: bool
    confidence: float
    evidence: List[str] = []


class HallucinationCheckResponse(BaseModel):
    """Hallucination check results."""

    hallucination_score: float = Field(
        ..., ge=0.0, le=1.0, description="0 = fully supported, 1 = fully hallucinated"
    )
    claims: List[ClaimVerificationResponse]
    verdict: str
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: int = 0


@router.post("/check", response_model=HallucinationCheckResponse)
async def check_hallucination(request: HallucinationCheckRequest):
    """
    Check an answer for hallucinations by cross-referencing against the KG.

    Pipeline:
    1. Extract claims from the answer via LLM
    2. For each claim, search KG for supporting evidence
    3. Score each claim's support level
    4. Aggregate into hallucination score
    """
    try:
        await db.connect()
    except Exception as e:
        logger.warning(f"Neo4j not available for hallucination check: {e}")
        return HallucinationCheckResponse(
            hallucination_score=0.0,
            claims=[],
            verdict=f"Cannot verify: knowledge graph unavailable ({e})",
            total_claims=0,
            supported_claims=0,
            unsupported_claims=0,
        )

    detector = HallucinationDetector(db)
    result = await detector.check(answer=request.answer, context=request.context)

    # Convert to response model
    claims = [
        ClaimVerificationResponse(
            claim=c.claim,
            supported=c.supported,
            confidence=c.confidence,
            evidence=c.evidence,
        )
        for c in result.claims
    ]

    return HallucinationCheckResponse(
        hallucination_score=result.hallucination_score,
        claims=claims,
        verdict=result.verdict,
        total_claims=result.total_claims,
        supported_claims=result.supported_claims,
        unsupported_claims=result.unsupported_claims,
    )
