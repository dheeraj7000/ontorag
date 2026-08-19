"""
Answer Generator — produces answers grounded in KG facts using the LLM Router.

The answer is generated from trust-filtered context with provenance tracking.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from backend.app.core.llm_router import LLMRouter
from backend.app.services.retriever import RetrievedFact, format_context

logger = logging.getLogger(__name__)


ANSWER_SYSTEM_PROMPT = """You are a knowledge-grounded question answering system.
Answer based ONLY on the provided facts from the knowledge graph.
Each fact has a trust score — prioritize high-trust facts.

Rules:
1. Only use information from the provided facts.
2. If the facts don't contain enough information, say so clearly.
3. Be concise and accurate.
4. Do NOT make up information beyond what's in the facts.

Respond in JSON with this structure:
{
  "answer": "Your answer here",
  "confidence": 0.85,
  "used_fact_indices": [1, 3, 5],
  "reasoning": "Brief explanation of how you derived the answer"
}"""


@dataclass
class AnswerResult:
    """Result of answer generation."""

    answer: str
    confidence: float
    provider: str
    used_facts: List[Dict[str, Any]] = field(default_factory=list)
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""


class AnswerGenerator:
    """Generates answers from KG context using the LLM Router."""

    def __init__(self, llm_router: LLMRouter = None):
        self.llm = llm_router or LLMRouter()

    async def generate(
        self, query: str, facts: List[RetrievedFact]
    ) -> AnswerResult:
        """
        Generate an answer from the retrieved facts.

        Uses the LLM to synthesize facts into a coherent answer.
        """
        if not facts:
            return AnswerResult(
                answer="I couldn't find relevant information in the knowledge graph to answer this question.",
                confidence=0.0,
                provider="none",
            )

        context = format_context(facts)

        prompt = f"""Knowledge Graph Facts:
{context}

Question: {query}

Generate an answer using ONLY the facts above."""

        try:
            result = await self.llm.generate(
                prompt=prompt,
                system_prompt=ANSWER_SYSTEM_PROMPT,
                temperature=0.3,
                json_mode=True,
                tier="smart",  # Answer generation needs reasoning
            )

            return self._parse_answer(result, facts)
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return AnswerResult(
                answer=f"Error generating answer: {str(e)}",
                confidence=0.0,
                provider="error",
            )

    def _parse_answer(
        self, llm_result: Dict[str, Any], facts: List[RetrievedFact]
    ) -> AnswerResult:
        """Parse the LLM's answer response."""
        response = llm_result["response"]
        provider = llm_result["provider"]

        if isinstance(response, str):
            return AnswerResult(answer=response, confidence=0.5, provider=provider)

        answer = response.get("answer", "No answer generated.")
        confidence = float(response.get("confidence", 0.5))
        used_indices = response.get("used_fact_indices", [])
        reasoning = response.get("reasoning", "")

        # Build used_facts and provenance from the indices
        used_facts = []
        provenance = []

        for idx in used_indices:
            if 1 <= idx <= len(facts):
                fact = facts[idx - 1]  # 1-indexed
                used_facts.append({
                    "subject": fact.subject,
                    "relation": fact.relation,
                    "object": fact.object,
                    "trust_score": fact.trust_score,
                })
                provenance.append({
                    "fact_index": idx,
                    "source_document": fact.source_document,
                    "trust_score": fact.trust_score,
                })

        return AnswerResult(
            answer=answer,
            confidence=confidence,
            provider=provider,
            used_facts=used_facts,
            provenance=provenance,
            reasoning=reasoning,
        )
