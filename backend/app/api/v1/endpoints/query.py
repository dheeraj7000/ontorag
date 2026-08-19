"""Query endpoint — ontology-guided retrieval and answer generation."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.core.database import db
from backend.app.services.answer_generator import AnswerGenerator
from backend.app.services.retriever import OntologyGuidedRetriever

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Query request schema."""

    question: str = Field(..., min_length=3, description="Natural language question")
    min_trust: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum trust score for facts"
    )
    max_hops: int = Field(
        default=3, ge=1, le=5, description="Max graph traversal hops"
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of facts to retrieve"
    )


class QueryResponse(BaseModel):
    """Query response schema."""

    answer: str
    confidence: float
    provider: str
    used_facts: list
    provenance: list
    linked_entities: list = []
    reasoning: str = ""


@router.post("/", response_model=QueryResponse)
async def query_knowledge_graph(request: QueryRequest):
    """
    Query the knowledge graph with ontology-guided retrieval.

    Pipeline:
    1. Entity linking (embed query → match KG entities)
    2. Ontology-guided subgraph traversal
    3. Trust-filtered context assembly
    4. Answer generation via LLM Router
    """
    try:
        await db.connect()
    except Exception as e:
        logger.warning(f"Neo4j not available: {e}")
        return QueryResponse(
            answer="Knowledge graph is not available. Please ensure Neo4j is running.",
            confidence=0.0,
            provider="none",
            used_facts=[],
            provenance=[],
        )

    # Retrieve relevant facts
    retriever = OntologyGuidedRetriever(db)
    retrieval_result = await retriever.retrieve(
        query=request.question,
        min_trust=request.min_trust,
        max_hops=request.max_hops,
        top_k=request.top_k,
    )

    # Generate answer from facts
    generator = AnswerGenerator()
    answer_result = await generator.generate(
        query=request.question,
        facts=retrieval_result.facts,
    )

    return QueryResponse(
        answer=answer_result.answer,
        confidence=answer_result.confidence,
        provider=answer_result.provider,
        used_facts=answer_result.used_facts,
        provenance=answer_result.provenance,
        linked_entities=retrieval_result.linked_entities,
        reasoning=answer_result.reasoning,
    )
