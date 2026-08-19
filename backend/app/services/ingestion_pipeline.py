"""
Ingestion Pipeline — orchestrates the full document-to-KG flow.

Flow:
1. Parse document (PDF/MD/HTML/TXT → plain text)
2. Chunk text (500 tokens, 50 overlap)
3. Extract entities/relations via LLM (schema-guided)
4. Validate against ontology
5. Insert into Neo4j with provenance
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from backend.app.core.database import db
from backend.app.services.chunker import chunk_text
from backend.app.services.document_parser import parse_document
from backend.app.services.extractor import OntologyGuidedExtractor
from backend.app.services.kg_builder import KnowledgeGraphBuilder

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    """Statistics from a document ingestion run."""

    file_id: str
    filename: str
    status: str = "processing"
    total_chunks: int = 0
    entities_extracted: int = 0
    relations_extracted: int = 0
    violations: int = 0
    entities_inserted: int = 0
    relations_inserted: int = 0
    errors: List[str] = field(default_factory=list)


class IngestionPipeline:
    """Orchestrates the full document ingestion pipeline."""

    def __init__(self):
        self.extractor = OntologyGuidedExtractor()
        self.kg_builder = KnowledgeGraphBuilder(db)

    async def ingest(
        self,
        file_path: Path,
        file_id: str,
        filename: str,
    ) -> IngestionStats:
        """
        Run the full ingestion pipeline on a document.

        Steps: parse → chunk → extract → validate → insert to KG
        """
        stats = IngestionStats(file_id=file_id, filename=filename)

        try:
            # Step 1: Parse document to plain text
            logger.info(f"[{file_id}] Parsing document: {filename}")
            text = parse_document(file_path)

            if not text.strip():
                stats.status = "error"
                stats.errors.append("Document produced no extractable text")
                return stats

            # Step 2: Chunk text
            logger.info(f"[{file_id}] Chunking text ({len(text)} chars)")
            chunks = chunk_text(text)
            stats.total_chunks = len(chunks)

            if not chunks:
                stats.status = "error"
                stats.errors.append("Text chunking produced no chunks")
                return stats

            # Step 3: Connect to Neo4j and initialize schema
            try:
                await db.connect()
                await self.kg_builder.initialize_schema()
            except Exception as e:
                stats.status = "error"
                stats.errors.append(f"Neo4j connection failed: {str(e)}")
                return stats

            # Step 4: Extract entities and relations from each chunk
            logger.info(f"[{file_id}] Extracting from {len(chunks)} chunks")
            results = await self.extractor.extract_from_chunks(
                chunks=chunks,
                source_document=filename,
            )

            # Tally extraction results
            for result in results:
                stats.entities_extracted += len(result.entities)
                stats.relations_extracted += len(result.relations)
                stats.violations += len(result.violations)

            # Step 5: Insert into Neo4j
            logger.info(f"[{file_id}] Inserting into knowledge graph")
            insert_stats = await self.kg_builder.insert_extraction_results(
                results=results,
                source_document=filename,
            )
            stats.entities_inserted = insert_stats["entities_inserted"]
            stats.relations_inserted = insert_stats["relations_inserted"]

            if insert_stats["errors"] > 0:
                stats.errors.append(f"{insert_stats['errors']} insertion errors")

            stats.status = "completed"
            logger.info(
                f"[{file_id}] Ingestion complete: "
                f"{stats.entities_inserted} entities, "
                f"{stats.relations_inserted} relations inserted"
            )

        except Exception as e:
            stats.status = "error"
            stats.errors.append(str(e))
            logger.error(f"[{file_id}] Ingestion failed: {e}")

        return stats


# Singleton pipeline instance
ingestion_pipeline = IngestionPipeline()
