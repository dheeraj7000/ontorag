"""
Knowledge Graph Builder — persists extracted entities and relations to Neo4j
with provenance tracking (source document, chunk index, confidence).
"""

import logging
from typing import Any, Dict, List

from backend.app.core.database import Neo4jConnection
from backend.app.services.extractor import ExtractedEntity, ExtractedRelation, ExtractionResult

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """Builds the Neo4j knowledge graph from extraction results."""

    def __init__(self, db: Neo4jConnection):
        self.db = db

    async def initialize_schema(self) -> None:
        """Create indexes and constraints for the KG."""
        constraints = [
            # Unique constraint on entity name + type
            "CREATE CONSTRAINT entity_unique IF NOT EXISTS "
            "FOR (n:Entity) REQUIRE (n.name, n.entity_type) IS UNIQUE",
            # Index for fast lookup
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)",
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (n:Entity) ON (n.name)",
            "CREATE INDEX trust_score_idx IF NOT EXISTS FOR (n:Entity) ON (n.trust_score)",
        ]

        for cypher in constraints:
            try:
                await self.db.execute_write(cypher)
            except Exception as e:
                # Constraints may already exist
                logger.debug(f"Schema setup note: {e}")

        logger.info("KG schema initialized")

    async def insert_extraction_results(
        self,
        results: List[ExtractionResult],
        source_document: str,
    ) -> Dict[str, int]:
        """
        Insert all extraction results into Neo4j.

        Returns counts of inserted entities and relations.
        """
        entities_inserted = 0
        relations_inserted = 0
        errors = 0

        for result in results:
            # Insert entities
            for entity in result.entities:
                try:
                    await self._upsert_entity(entity, source_document)
                    entities_inserted += 1
                except Exception as e:
                    logger.error(f"Failed to insert entity '{entity.name}': {e}")
                    errors += 1

            # Insert relations
            for relation in result.relations:
                try:
                    await self._upsert_relation(relation, source_document)
                    relations_inserted += 1
                except Exception as e:
                    logger.error(
                        f"Failed to insert relation "
                        f"'{relation.source_name}'-[{relation.relation_type}]->'{relation.target_name}': {e}"
                    )
                    errors += 1

        logger.info(
            f"KG update for '{source_document}': "
            f"{entities_inserted} entities, {relations_inserted} relations, {errors} errors"
        )

        return {
            "entities_inserted": entities_inserted,
            "relations_inserted": relations_inserted,
            "errors": errors,
        }

    async def _upsert_entity(
        self, entity: ExtractedEntity, source_document: str
    ) -> None:
        """Insert or update an entity node in Neo4j."""
        # Build properties dict
        props: Dict[str, Any] = {
            "name": entity.name,
            "entity_type": entity.entity_type,
            "extraction_confidence": entity.confidence,
            "source_document": source_document,
            "chunk_index": entity.source_chunk_index,
            # Default trust score (will be updated by GNN later)
            "trust_score": entity.confidence * 0.8,
        }

        # Add all extracted properties
        for key, value in entity.properties.items():
            if isinstance(value, (str, int, float, bool)):
                props[f"prop_{key}"] = value

        # MERGE ensures no duplicates; ON CREATE/MATCH updates appropriately
        cypher = """
        MERGE (n:Entity {name: $name, entity_type: $entity_type})
        ON CREATE SET n += $props, n.created_at = datetime()
        ON MATCH SET
            n.extraction_confidence = CASE
                WHEN $confidence > n.extraction_confidence
                THEN $confidence ELSE n.extraction_confidence END,
            n.updated_at = datetime()
        """

        # Also add the entity_type as a label for easier querying
        cypher += f"\nSET n:{entity.entity_type}"

        await self.db.execute_write(
            cypher,
            {
                "name": entity.name,
                "entity_type": entity.entity_type,
                "props": props,
                "confidence": entity.confidence,
            },
        )

    async def _upsert_relation(
        self, relation: ExtractedRelation, source_document: str
    ) -> None:
        """Insert or update a relationship in Neo4j."""
        # Ensure both source and target nodes exist (MERGE)
        # Then create the relationship
        cypher = f"""
        MERGE (src:Entity {{name: $source_name, entity_type: $source_type}})
        ON CREATE SET src.trust_score = 0.5, src.created_at = datetime()
        MERGE (tgt:Entity {{name: $target_name, entity_type: $target_type}})
        ON CREATE SET tgt.trust_score = 0.5, tgt.created_at = datetime()
        MERGE (src)-[r:{relation.relation_type}]->(tgt)
        ON CREATE SET
            r.extraction_confidence = $confidence,
            r.source_document = $source_document,
            r.chunk_index = $chunk_index,
            r.trust_score = $confidence * 0.8,
            r.created_at = datetime()
        ON MATCH SET
            r.extraction_confidence = CASE
                WHEN $confidence > r.extraction_confidence
                THEN $confidence ELSE r.extraction_confidence END,
            r.updated_at = datetime()
        """

        await self.db.execute_write(
            cypher,
            {
                "source_name": relation.source_name,
                "source_type": relation.source_type,
                "target_name": relation.target_name,
                "target_type": relation.target_type,
                "confidence": relation.confidence,
                "source_document": source_document,
                "chunk_index": relation.source_chunk_index,
            },
        )

    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        node_count = await self.db.get_node_count()
        edge_count = await self.db.get_edge_count()

        # Entity type distribution
        type_result = await self.db.execute_query(
            "MATCH (n:Entity) RETURN n.entity_type as type, count(n) as count "
            "ORDER BY count DESC"
        )
        entity_types = {r["type"]: r["count"] for r in type_result}

        # Relation type distribution
        rel_result = await self.db.execute_query(
            "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count "
            "ORDER BY count DESC"
        )
        relation_types = {r["type"]: r["count"] for r in rel_result}

        # Average trust score
        trust_result = await self.db.execute_query(
            "MATCH (n:Entity) WHERE n.trust_score IS NOT NULL "
            "RETURN avg(n.trust_score) as avg_trust"
        )
        avg_trust = trust_result[0]["avg_trust"] if trust_result else 0.0

        return {
            "total_nodes": node_count,
            "total_edges": edge_count,
            "entity_types": entity_types,
            "relation_types": relation_types,
            "avg_trust_score": round(avg_trust or 0.0, 3),
        }
