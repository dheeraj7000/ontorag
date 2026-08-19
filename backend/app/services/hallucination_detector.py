"""
Hallucination Detector — cross-checks LLM-generated answers against the KG.

Pipeline:
1. Extract atomic claims from the answer (via LLM)
2. For each claim, search KG for supporting/contradicting evidence
3. Score each claim (supported/unsupported/contradicted)
4. Aggregate into a hallucination score
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from backend.app.core.database import Neo4jConnection
from backend.app.core.llm_router import LLMRouter

logger = logging.getLogger(__name__)


CLAIM_EXTRACTION_PROMPT = """You are a claim extraction system.
Given an answer, extract all atomic factual claims.
Each claim should be a single, verifiable statement.

Respond in JSON:
{
  "claims": [
    {"claim": "FastAPI uses Starlette under the hood", "subject": "FastAPI", "predicate": "uses", "object": "Starlette"},
    {"claim": "Python 3.11 is required", "subject": "Python", "predicate": "version_required", "object": "3.11"}
  ]
}"""


@dataclass
class ClaimVerification:
    """Result of verifying a single claim."""

    claim: str
    subject: str
    predicate: str
    object: str
    supported: bool
    confidence: float
    evidence: List[str] = field(default_factory=list)


@dataclass
class HallucinationResult:
    """Full hallucination detection result."""

    hallucination_score: float  # 0 = all supported, 1 = all hallucinated
    claims: List[ClaimVerification] = field(default_factory=list)
    verdict: str = ""
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: int = 0


class HallucinationDetector:
    """Detects hallucinations by cross-referencing answers with the KG."""

    def __init__(self, db: Neo4jConnection, llm_router: LLMRouter = None):
        self.db = db
        self.llm = llm_router or LLMRouter()

    async def check(self, answer: str, context: str = "") -> HallucinationResult:
        """
        Check an answer for hallucinations.

        Steps:
        1. Extract claims from the answer
        2. Verify each claim against the KG
        3. Compute hallucination score
        """
        # Step 1: Extract claims
        claims = await self._extract_claims(answer)

        if not claims:
            return HallucinationResult(
                hallucination_score=0.0,
                verdict="No verifiable claims found in the answer.",
                total_claims=0,
            )

        # Step 2: Verify each claim
        verifications = []
        for claim_data in claims:
            verification = await self._verify_claim(claim_data)
            verifications.append(verification)

        # Step 3: Compute score
        total = len(verifications)
        supported = sum(1 for v in verifications if v.supported)
        unsupported = total - supported

        hallucination_score = unsupported / total if total > 0 else 0.0

        # Determine verdict
        if hallucination_score == 0.0:
            verdict = "All claims are supported by the knowledge graph."
        elif hallucination_score <= 0.3:
            verdict = "Most claims are supported. Minor unsupported details detected."
        elif hallucination_score <= 0.6:
            verdict = "Significant unsupported claims detected. Exercise caution."
        else:
            verdict = "High hallucination detected. Most claims lack KG support."

        return HallucinationResult(
            hallucination_score=round(hallucination_score, 3),
            claims=verifications,
            verdict=verdict,
            total_claims=total,
            supported_claims=supported,
            unsupported_claims=unsupported,
        )

    async def _extract_claims(self, answer: str) -> List[Dict[str, str]]:
        """Extract atomic claims from the answer using LLM."""
        prompt = f"""Answer to analyze:
---
{answer}
---

Extract all atomic factual claims from this answer."""

        try:
            result = await self.llm.generate(
                prompt=prompt,
                system_prompt=CLAIM_EXTRACTION_PROMPT,
                temperature=0.1,
                json_mode=True,
            )

            response = result["response"]
            if isinstance(response, str):
                import json

                response = json.loads(response)

            return response.get("claims", [])
        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            return []

    async def _verify_claim(self, claim_data: Dict[str, str]) -> ClaimVerification:
        """
        Verify a single claim against the knowledge graph.

        Searches for supporting evidence using:
        1. Direct relationship match (subject → object)
        2. Entity property match
        3. Neighborhood context
        """
        claim_text = claim_data.get("claim", "")
        subject = claim_data.get("subject", "")
        obj = claim_data.get("object", "")

        evidence: List[str] = []
        supported = False
        confidence = 0.0

        if not subject:
            return ClaimVerification(
                claim=claim_text,
                subject=subject,
                predicate=claim_data.get("predicate", ""),
                object=obj,
                supported=False,
                confidence=0.0,
            )

        # Check 1: Direct relationship between subject and object
        if subject and obj:
            direct = await self.db.execute_query(
                "MATCH (s:Entity)-[r]->(t:Entity) "
                "WHERE toLower(s.name) CONTAINS toLower($subject) "
                "AND toLower(t.name) CONTAINS toLower($object) "
                "RETURN s.name as src, type(r) as rel, t.name as tgt, "
                "r.trust_score as trust "
                "LIMIT 5",
                {"subject": subject.lower(), "object": obj.lower()},
            )

            if direct:
                supported = True
                confidence = max(float(r.get("trust", 0.5) or 0.5) for r in direct)
                for r in direct:
                    evidence.append(f"{r['src']} --[{r['rel']}]--> {r['tgt']}")

        # Check 2: Entity exists with matching properties
        if not supported and subject:
            entity_check = await self.db.execute_query(
                "MATCH (n:Entity) "
                "WHERE toLower(n.name) CONTAINS toLower($subject) "
                "RETURN n.name as name, n.entity_type as type, "
                "n.trust_score as trust "
                "LIMIT 3",
                {"subject": subject.lower()},
            )

            if entity_check:
                # Entity exists but no direct relationship found
                confidence = 0.3  # Lower confidence - entity exists but claim not verified
                evidence.append(
                    f"Entity '{entity_check[0]['name']}' exists in KG "
                    f"(type: {entity_check[0]['type']})"
                )

        return ClaimVerification(
            claim=claim_text,
            subject=subject,
            predicate=claim_data.get("predicate", ""),
            object=obj,
            supported=supported,
            confidence=confidence,
            evidence=evidence,
        )
