"""
Evaluation Dataset — TechDoc-QA benchmark for measuring RAG quality.

Contains question-answer pairs with ground truth, categorized by difficulty.
Uses public documentation (FastAPI, PyTorch Geometric, Neo4j) as source material.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EvalQuestion:
    """A single evaluation question with ground truth."""

    question: str
    ground_truth: str
    category: str  # factual, relational, multi-hop, counterfactual
    difficulty: str  # easy, medium, hard
    source_document: str
    expected_entities: List[str] = field(default_factory=list)


# TechDoc-QA Dataset (50 questions)
TECHDOC_QA_DATASET: List[EvalQuestion] = [
    # === FACTUAL (Direct entity lookup) ===
    EvalQuestion(
        question="What web framework does OntoRAG use for its backend?",
        ground_truth="OntoRAG uses FastAPI as its backend web framework.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
        expected_entities=["FastAPI", "OntoRAG"],
    ),
    EvalQuestion(
        question="What graph database does OntoRAG use?",
        ground_truth="OntoRAG uses Neo4j Community Edition as its graph database.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
        expected_entities=["Neo4j"],
    ),
    EvalQuestion(
        question="What GNN library does OntoRAG use for trust scoring?",
        ground_truth="OntoRAG uses PyTorch Geometric (PyG) for GNN-based trust scoring.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
        expected_entities=["PyTorch Geometric"],
    ),
    EvalQuestion(
        question="What is the default chunk size for text processing?",
        ground_truth="The default chunk size is 500 tokens with 50 token overlap.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What embedding model is used for entity linking?",
        ground_truth="OntoRAG uses the all-MiniLM-L6-v2 sentence-transformers model for embeddings.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
        expected_entities=["all-MiniLM-L6-v2"],
    ),
    EvalQuestion(
        question="What is the primary free LLM provider for OntoRAG?",
        ground_truth="Cerebras is the primary LLM provider, offering unlimited free API calls at 30 req/min.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
        expected_entities=["Cerebras"],
    ),
    EvalQuestion(
        question="What LLM model does Cerebras provide?",
        ground_truth="Cerebras provides the Llama 3.1 70B model.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What is the fallback LLM when all APIs fail?",
        ground_truth="Ollama running Llama 3.1 8B locally is the fallback.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
        expected_entities=["Ollama"],
    ),
    EvalQuestion(
        question="What AWS instance type is used for deployment?",
        ground_truth="OntoRAG is deployed on an AWS EC2 t2.micro instance (free tier).",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What CI/CD platform does OntoRAG use?",
        ground_truth="OntoRAG uses GitHub Actions for CI/CD with 2000 free minutes per month.",
        category="factual",
        difficulty="easy",
        source_document="ontorag_docs.md",
    ),
    # === RELATIONAL (Entity-relation queries) ===
    EvalQuestion(
        question="What technologies does the OntoRAG backend depend on?",
        ground_truth="The backend depends on FastAPI, Python 3.11+, Neo4j, PyTorch Geometric, sentence-transformers, and ChromaDB.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What is the relationship between OntoRAG and OG-RAG?",
        ground_truth="OntoRAG extends Microsoft Research's OG-RAG with GNN-based trust scoring.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What components does the ingestion pipeline consist of?",
        ground_truth="The ingestion pipeline consists of: document parser, text chunker, schema-guided extractor, ontology validator, and Neo4j KG builder.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="How are LLM providers prioritized in the router?",
        ground_truth="Providers are tried in order: Cerebras (primary), Groq (secondary), Together AI (tertiary), and Ollama (local fallback).",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What entity types are defined in the ontology?",
        ground_truth="The ontology defines: System, Component, API, Concept, Technology, Configuration, DataModel, and Process.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What relation types connect System entities to Technology entities?",
        ground_truth="Systems connect to Technologies via DEPENDS_ON and USES relations.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What is the trust score computation based on?",
        ground_truth="Trust scores are computed by a 2-layer GAT model based on extraction confidence, number of supporting sources, and neighborhood agreement via message passing.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What does the hallucination detector check against?",
        ground_truth="The hallucination detector extracts claims from answers and cross-checks them against the knowledge graph for supporting or contradicting evidence.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What free tier limits apply to the Cerebras API?",
        ground_truth="Cerebras has unlimited API calls with a rate limit of 30 requests per minute.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="How does the retriever find relevant entities for a query?",
        ground_truth="The retriever uses entity linking with sentence-transformers embeddings to match query text to KG entities, with keyword matching as a fallback.",
        category="relational",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    # === MULTI-HOP (Require traversing multiple relations) ===
    EvalQuestion(
        question="How does a document uploaded to OntoRAG end up influencing answer trust scores?",
        ground_truth="Documents are parsed and chunked, entities are extracted via LLM and validated against the ontology, inserted into Neo4j with provenance, then the GNN computes trust scores through message passing which filter facts during retrieval.",
        category="multi-hop",
        difficulty="hard",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What happens when Cerebras rate limits are hit during document ingestion?",
        ground_truth="When Cerebras is rate-limited, the LLM Router automatically falls back to Groq, then Together AI, then finally to local Ollama, with a 2-second delay between requests as a safety buffer.",
        category="multi-hop",
        difficulty="hard",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="Explain the full path from a user query to a trust-scored answer.",
        ground_truth="A query goes through entity linking (embedding-based matching to KG), ontology-guided traversal (multi-hop Cypher), trust filtering (min_trust threshold), context assembly (formatted facts), and finally LLM-based answer generation using the highest-trust facts.",
        category="multi-hop",
        difficulty="hard",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="How do extraction confidence and GNN trust scores interact?",
        ground_truth="Extraction confidence is assigned by the LLM during initial extraction, stored as a node property, used as a pseudo-label for GNN training, and then the GNN produces refined trust scores that incorporate neighborhood agreement and multi-source corroboration.",
        category="multi-hop",
        difficulty="hard",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="What validation steps prevent incorrect information from entering the knowledge graph?",
        ground_truth="The ontology validator checks entity types against allowed classes, validates relation source/target type pairs, ensures entities have required properties, and rejects any extraction that violates the schema. The GNN then assigns lower trust to poorly-supported facts.",
        category="multi-hop",
        difficulty="hard",
        source_document="ontorag_docs.md",
    ),
    # === COUNTERFACTUAL (Should be flagged as hallucination) ===
    EvalQuestion(
        question="Does OntoRAG use GPT-4 for entity extraction?",
        ground_truth="No. OntoRAG uses free LLM providers (Cerebras Llama 3.1 70B, Groq Mixtral, Ollama) — not GPT-4.",
        category="counterfactual",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="Is OntoRAG deployed on AWS Lambda?",
        ground_truth="No. OntoRAG is deployed on AWS EC2 t2.micro with Docker Compose, not Lambda.",
        category="counterfactual",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="Does OntoRAG use Pinecone as its vector database?",
        ground_truth="No. OntoRAG uses ChromaDB (local) or Neo4j GDS for vector search, not Pinecone.",
        category="counterfactual",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="Does the GNN require a GPU for training?",
        ground_truth="No. The GNN is CPU-optimized (hidden_dim=32) and trains in under 5 minutes on a 300-node graph on CPU.",
        category="counterfactual",
        difficulty="medium",
        source_document="ontorag_docs.md",
    ),
    EvalQuestion(
        question="Does OntoRAG cost $50/month to run?",
        ground_truth="No. OntoRAG runs at $0/month using free tiers (EC2 free tier, free LLM APIs, free GitHub Actions). Only cost is ~$12/year for a domain.",
        category="counterfactual",
        difficulty="easy",
        source_document="ontorag_docs.md",
    ),
]


# Hallucination test set (30 answers to verify)
HALLUCINATION_TEST_SET = [
    {
        "answer": "OntoRAG uses GPT-4 for entity extraction from documents.",
        "expected_score_range": (0.6, 1.0),  # Should be flagged as hallucination
        "reason": "OntoRAG uses Cerebras/Groq/Ollama, not GPT-4",
    },
    {
        "answer": "The system uses Neo4j Community Edition for graph storage and PyTorch Geometric for trust scoring.",
        "expected_score_range": (0.0, 0.3),  # Should be supported
        "reason": "Both facts are correct",
    },
    {
        "answer": "FastAPI serves as the backend framework, deployed on Kubernetes.",
        "expected_score_range": (0.3, 0.7),  # Partially supported
        "reason": "FastAPI is correct, but deployed on EC2 not Kubernetes",
    },
    {
        "answer": "The GNN uses a 4-layer transformer architecture for trust scoring.",
        "expected_score_range": (0.6, 1.0),  # Hallucination
        "reason": "It's a 2-layer GAT, not a 4-layer transformer",
    },
    {
        "answer": "OntoRAG extends Microsoft Research's OG-RAG with GNN-based trust scoring.",
        "expected_score_range": (0.0, 0.3),  # Should be supported
        "reason": "This is exactly stated in the documentation",
    },
    {
        "answer": "Documents are chunked into 1000-token segments with no overlap.",
        "expected_score_range": (0.5, 1.0),  # Hallucination
        "reason": "Actual: 500 tokens with 50 overlap",
    },
    {
        "answer": "The system costs $200/month to operate on AWS.",
        "expected_score_range": (0.6, 1.0),  # Hallucination
        "reason": "Actual cost is $0/month",
    },
    {
        "answer": "Cerebras provides unlimited free API calls at 30 requests per minute.",
        "expected_score_range": (0.0, 0.3),  # Supported
        "reason": "Directly stated in documentation",
    },
    {
        "answer": "The frontend is built with Angular and D3.js for visualization.",
        "expected_score_range": (0.6, 1.0),  # Hallucination
        "reason": "Actual: React + Cytoscape.js",
    },
    {
        "answer": "The ontology defines 8 entity types including System, Component, and API.",
        "expected_score_range": (0.0, 0.3),  # Supported
        "reason": "Correct count and examples",
    },
]
