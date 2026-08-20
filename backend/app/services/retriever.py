"""
Ontology-Guided Retriever — entity linking, subgraph traversal,
and trust-filtered context assembly.

Pipeline:
1. Entity linking: embed query → match KG entities
2. Ontology-guided traversal: Cypher multi-hop with type constraints
3. Trust filtering: only include facts above min_trust threshold
4. Context assembly: format subgraph as LLM context
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List

from backend.app.core.database import Neo4jConnection

logger = logging.getLogger(__name__)


@dataclass
class RetrievedFact:
    """A single fact retrieved from the knowledge graph."""

    subject: str
    relation: str
    object: str
    trust_score: float
    source_document: str
    subject_type: str = ""
    object_type: str = ""


@dataclass
class RetrievalResult:
    """Result of the retrieval pipeline."""

    facts: List[RetrievedFact] = field(default_factory=list)
    linked_entities: List[str] = field(default_factory=list)
    subgraph_nodes: int = 0
    subgraph_edges: int = 0


class OntologyGuidedRetriever:
    """
    Retrieves relevant facts from the KG using ontology-guided traversal.
    """

    def __init__(self, db: Neo4jConnection):
        self.db = db
        self._embedder = None

    def _get_embedder(self):
        """Lazy-load the sentence transformer for entity linking."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded sentence-transformers model for entity linking")
            except ImportError:
                logger.warning(
                    "sentence-transformers not available. "
                    "Using keyword matching for entity linking."
                )
        return self._embedder

    async def retrieve(
        self,
        query: str,
        min_trust: float = 0.5,
        max_hops: int = 3,
        top_k: int = 5,
    ) -> RetrievalResult:
        """
        Retrieve relevant facts from the KG.

        Steps:
        1. Link query to KG entities
        2. Traverse from linked entities (ontology-guided)
        3. Filter by trust score
        4. Return top_k facts
        """
        result = RetrievalResult()

        # Step 1: Entity linking
        linked_entities = await self._link_entities(query)
        result.linked_entities = linked_entities

        if not linked_entities:
            logger.info("No entities linked to query, using keyword search")
            linked_entities = await self._keyword_search(query)
            result.linked_entities = linked_entities

        if not linked_entities:
            return result

        # Step 2: Ontology-guided traversal
        facts = await self._traverse_subgraph(
            entity_names=linked_entities,
            max_hops=max_hops,
            min_trust=min_trust,
        )

        # Fallback: a linked entity with no qualifying relations (e.g. sparse
        # extraction from a short document) would otherwise return nothing
        # at all even though we know something about it. Surface its own
        # properties as a minimal fact so there's still something to answer
        # with, instead of "couldn't find relevant information".
        if not facts:
            facts = await self._entity_self_facts(linked_entities)

        # Step 3: Sort by trust score and take top_k
        facts.sort(key=lambda f: f.trust_score, reverse=True)
        result.facts = facts[:top_k]

        # Compute subgraph size
        result.subgraph_nodes = len(set(
            [f.subject for f in facts] + [f.object for f in facts]
        ))
        result.subgraph_edges = len(facts)

        logger.info(
            f"Retrieved {len(result.facts)} facts from {result.subgraph_nodes} nodes "
            f"(linked: {linked_entities})"
        )
        return result

    async def _link_entities(self, query: str) -> List[str]:
        """
        Link query text to KG entities using embedding similarity.

        Falls back to keyword matching if embeddings unavailable.
        """
        embedder = self._get_embedder()

        if embedder is None:
            return await self._keyword_search(query)

        # Get all entity names from KG
        entities = await self.db.execute_query(
            "MATCH (n:Entity) RETURN n.name as name, n.entity_type as type "
            "ORDER BY n.trust_score DESC LIMIT 200"
        )

        if not entities:
            return []

        # Embed query and entity names
        entity_names = [e["name"] for e in entities]
        query_embedding = embedder.encode(query, convert_to_tensor=True)
        entity_embeddings = embedder.encode(entity_names, convert_to_tensor=True)

        # Compute cosine similarity
        from sentence_transformers.util import cos_sim

        similarities = cos_sim(query_embedding, entity_embeddings)[0]

        # Take entities with similarity > threshold
        threshold = 0.3
        linked = []
        for i, sim in enumerate(similarities):
            if float(sim) > threshold:
                linked.append(entity_names[i])

        # Return top 5 most similar
        scored = list(zip(entity_names, similarities.tolist()))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored[:5]]

    async def _keyword_search(self, query: str) -> List[str]:
        """Fallback: simple keyword matching against entity names."""
        # Extract key terms from query (simple tokenization). Strip
        # punctuation first — otherwise a term like "GCAF-Net?" (trailing "?"
        # from a "What is X?" question) never CONTAINS-matches the actual
        # entity name "GCAF-Net", silently killing entity linking for any
        # question that ends right after the entity name.
        raw_terms = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-_]*", query)
        terms = [t.lower() for t in raw_terms if len(t) > 3]

        if not terms:
            return []

        # Match via a parameterized list instead of interpolating terms
        # directly into the query string — the old CONTAINS('{term}') form
        # broke (and was Cypher-injectable) for any term containing a quote.
        results = await self.db.execute_query(
            "MATCH (n:Entity) WHERE ANY(term IN $terms WHERE toLower(n.name) CONTAINS term) "
            "RETURN n.name as name ORDER BY n.trust_score DESC LIMIT 5",
            {"terms": terms[:5]},
        )

        return [r["name"] for r in results]

    async def _entity_self_facts(self, entity_names: List[str]) -> List[RetrievedFact]:
        """Describe linked entities via their own properties (type, source)
        when they have no qualifying relations to traverse."""
        results = await self.db.execute_query(
            "MATCH (n:Entity) WHERE n.name IN $entity_names "
            "RETURN n.name as name, n.entity_type as entity_type, "
            "n.trust_score as trust_score, n.source_document as source_document",
            {"entity_names": entity_names},
        )

        return [
            RetrievedFact(
                subject=r["name"],
                relation="IS_A",
                object=r.get("entity_type") or "Entity",
                trust_score=float(r.get("trust_score")) if r.get("trust_score") is not None else 0.5,
                source_document=r.get("source_document") or "unknown",
                subject_type=r.get("entity_type") or "",
                object_type="",
            )
            for r in results
        ]

    async def _traverse_subgraph(
        self,
        entity_names: List[str],
        max_hops: int,
        min_trust: float,
    ) -> List[RetrievedFact]:
        """
        Traverse the KG from linked entities, collecting trust-filtered facts.
        """
        facts: List[RetrievedFact] = []

        # Query for all relationships within N hops of the linked entities.
        # Undirected match — a linked entity is just as relevant as the
        # object of a fact ("OntoRAG USES Neo4j") as it is the subject, but
        # startNode/endNode still give the true direction for subject/object.
        cypher = """
        MATCH (a:Entity)-[r]-(b:Entity)
        WHERE (a.name IN $entity_names OR b.name IN $entity_names)
          AND (r.trust_score >= $min_trust OR r.trust_score IS NULL)
          AND (a.trust_score >= $min_trust OR a.trust_score IS NULL)
          AND (b.trust_score >= $min_trust OR b.trust_score IS NULL)
        WITH startNode(r) as src, endNode(r) as tgt, r
        RETURN DISTINCT src.name as subject, src.entity_type as subject_type,
               type(r) as relation, r.trust_score as rel_trust,
               r.source_document as source_document,
               tgt.name as object, tgt.entity_type as object_type,
               tgt.trust_score as obj_trust
        ORDER BY r.trust_score DESC
        LIMIT 50
        """

        results = await self.db.execute_query(
            cypher, {"entity_names": entity_names, "min_trust": min_trust}
        )

        for r in results:
            facts.append(
                RetrievedFact(
                    subject=r["subject"],
                    relation=r["relation"],
                    object=r["object"],
                    trust_score=float(r.get("rel_trust") or 0.5),
                    source_document=r.get("source_document") or "unknown",
                    subject_type=r.get("subject_type") or "",
                    object_type=r.get("object_type") or "",
                )
            )

        # If max_hops > 1, also get 2nd-hop neighbors
        if max_hops >= 2 and entity_names:
            cypher_2hop = """
            MATCH (src:Entity)-[r1]->(mid:Entity)-[r2]->(tgt:Entity)
            WHERE src.name IN $entity_names
              AND (r2.trust_score >= $min_trust OR r2.trust_score IS NULL)
              AND mid.name <> tgt.name
            RETURN mid.name as subject, mid.entity_type as subject_type,
                   type(r2) as relation, r2.trust_score as rel_trust,
                   r2.source_document as source_document,
                   tgt.name as object, tgt.entity_type as object_type,
                   tgt.trust_score as obj_trust
            ORDER BY r2.trust_score DESC
            LIMIT 30
            """

            results_2hop = await self.db.execute_query(
                cypher_2hop, {"entity_names": entity_names, "min_trust": min_trust}
            )

            for r in results_2hop:
                facts.append(
                    RetrievedFact(
                        subject=r["subject"],
                        relation=r["relation"],
                        object=r["object"],
                        trust_score=float(r.get("rel_trust") or 0.5),
                        source_document=r.get("source_document") or "unknown",
                        subject_type=r.get("subject_type") or "",
                        object_type=r.get("object_type") or "",
                    )
                )

        return facts


def format_context(facts: List[RetrievedFact]) -> str:
    """Format retrieved facts as a text context for the LLM."""
    if not facts:
        return "No relevant facts found in the knowledge graph."

    lines = []
    for i, fact in enumerate(facts, 1):
        trust_label = "HIGH" if fact.trust_score >= 0.75 else "MEDIUM" if fact.trust_score >= 0.5 else "LOW"
        lines.append(
            f"[Fact {i}] (Trust: {trust_label}, {fact.trust_score:.2f}) "
            f"{fact.subject} --[{fact.relation}]--> {fact.object}"
        )

    return "\n".join(lines)
