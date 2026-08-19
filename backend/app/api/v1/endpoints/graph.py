"""Graph inspection endpoints — view KG stats, entities, and subgraphs."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from backend.app.core.database import db
from backend.app.services.kg_builder import KnowledgeGraphBuilder

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_graph_stats():
    """Get knowledge graph statistics."""
    try:
        await db.connect()
        kg_builder = KnowledgeGraphBuilder(db)
        return await kg_builder.get_stats()
    except Exception as e:
        logger.warning(f"Could not fetch graph stats: {e}")
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "entity_types": {},
            "relation_types": {},
            "avg_trust_score": 0.0,
            "error": str(e),
        }


@router.get("/entities")
async def list_entities(
    entity_type: Optional[str] = None,
    min_trust: float = 0.0,
    limit: int = 50,
):
    """List entities from the knowledge graph with optional filters."""
    try:
        await db.connect()

        where_clauses = ["n.trust_score >= $min_trust"]
        params = {"min_trust": min_trust, "limit": limit}

        if entity_type:
            where_clauses.append("n.entity_type = $entity_type")
            params["entity_type"] = entity_type

        where_str = " AND ".join(where_clauses)

        cypher = f"""
        MATCH (n:Entity)
        WHERE {where_str}
        RETURN n.name as name, n.entity_type as entity_type,
               n.trust_score as trust_score,
               n.extraction_confidence as confidence,
               n.source_document as source_document
        ORDER BY n.trust_score DESC
        LIMIT $limit
        """

        results = await db.execute_query(cypher, params)

        return {"entities": results, "total": len(results)}
    except Exception as e:
        logger.warning(f"Could not list entities: {e}")
        return {"entities": [], "total": 0, "error": str(e)}


@router.get("/subgraph/{entity_name}")
async def get_subgraph(entity_name: str, hops: int = 2):
    """
    Get a subgraph centered on an entity (for Cytoscape.js visualization).

    Returns nodes and edges within N hops of the specified entity.
    """
    try:
        await db.connect()

        # Get the subgraph within N hops
        cypher = """
        MATCH path = (center:Entity {name: $entity_name})-[*1..$hops]-(connected)
        WHERE connected:Entity
        WITH nodes(path) as ns, relationships(path) as rs
        UNWIND ns as n
        WITH COLLECT(DISTINCT n) as nodes,
             COLLECT(DISTINCT rs) as all_rels
        UNWIND nodes as node
        WITH nodes,
             all_rels,
             COLLECT({
                 id: elementId(node),
                 name: node.name,
                 entity_type: node.entity_type,
                 trust_score: node.trust_score
             }) as node_data
        UNWIND all_rels as rels
        UNWIND rels as rel
        RETURN node_data as nodes,
               COLLECT(DISTINCT {
                   source: elementId(startNode(rel)),
                   target: elementId(endNode(rel)),
                   type: type(rel),
                   trust_score: rel.trust_score
               }) as edges
        """

        results = await db.execute_query(
            cypher, {"entity_name": entity_name, "hops": hops}
        )

        if not results:
            raise HTTPException(
                status_code=404, detail=f"Entity '{entity_name}' not found"
            )

        return {
            "nodes": results[0]["nodes"] if results else [],
            "edges": results[0]["edges"] if results else [],
            "center": entity_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Could not get subgraph: {e}")
        return {"nodes": [], "edges": [], "center": entity_name, "error": str(e)}
