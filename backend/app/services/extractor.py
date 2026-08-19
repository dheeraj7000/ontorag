"""
Schema-Guided Extractor — uses LLM to extract entities and relations
from text chunks, guided by the domain ontology.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.app.core.llm_router import LLMRouter
from backend.app.core.ontology import load_ontology, validate_entity, validate_relation

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """An entity extracted from text."""

    entity_type: str
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    source_chunk_index: int = 0


@dataclass
class ExtractedRelation:
    """A relation extracted from text."""

    relation_type: str
    source_name: str
    source_type: str
    target_name: str
    target_type: str
    confidence: float = 0.0
    source_chunk_index: int = 0


@dataclass
class ExtractionResult:
    """Result of extracting entities and relations from a chunk."""

    entities: List[ExtractedEntity] = field(default_factory=list)
    relations: List[ExtractedRelation] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    provider: str = ""
    chunk_index: int = 0


EXTRACTION_SYSTEM_PROMPT = """You are an ontology-guided information extraction system.
Your job is to extract entities and relations from text according to a strict schema.

RULES:
1. Only extract entities whose type matches one of the entity_classes in the schema.
2. Only extract relations whose type matches one of the relation_types in the schema.
3. Ensure each relation's source/target types match the valid_source_target_pairs.
4. Assign a confidence score (0.0 to 1.0) based on how explicitly the information is stated.
5. Extract ALL relevant entities and relations, but do NOT hallucinate — only extract what's in the text.

Respond ONLY in valid JSON with this exact structure:
{
  "entities": [
    {"entity_type": "...", "name": "...", "properties": {...}, "confidence": 0.9}
  ],
  "relations": [
    {"relation_type": "...", "source_name": "...", "source_type": "...", "target_name": "...", "target_type": "...", "confidence": 0.85}
  ]
}"""


class OntologyGuidedExtractor:
    """Extracts entities and relations from text using LLM + ontology schema."""

    def __init__(self, llm_router: Optional[LLMRouter] = None):
        self.llm = llm_router or LLMRouter()
        self.ontology = load_ontology()
        self._rate_limit_delay = 13.0  # seconds between API calls (5 req/min limit)

    async def extract_from_chunk(
        self, text: str, chunk_index: int, source_document: str
    ) -> ExtractionResult:
        """
        Extract entities and relations from a single text chunk.

        Uses the ontology schema to guide the LLM extraction.
        """
        prompt = f"""Ontology Schema:
{json.dumps(self.ontology, indent=2)}

Text to extract from:
---
{text}
---

Extract all entities and relations following the schema rules strictly.
Only extract information that is explicitly stated or strongly implied in the text."""

        try:
            result = await self.llm.generate(
                prompt=prompt,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                temperature=0.1,
                json_mode=True,
                tier="fast",  # Extraction is high-volume, use cheap model
            )

            return self._parse_extraction_result(
                result["response"], chunk_index, result["provider"]
            )
        except Exception as e:
            logger.error(f"Extraction failed for chunk {chunk_index}: {e}")
            return ExtractionResult(
                chunk_index=chunk_index,
                violations=[f"Extraction error: {str(e)}"],
            )

    def _parse_extraction_result(
        self, raw_response: Any, chunk_index: int, provider: str
    ) -> ExtractionResult:
        """Parse and validate the LLM's extraction response."""
        result = ExtractionResult(chunk_index=chunk_index, provider=provider)

        if isinstance(raw_response, str):
            try:
                raw_response = json.loads(raw_response)
            except json.JSONDecodeError:
                result.violations.append("LLM returned invalid JSON")
                return result

        # Parse entities
        for raw_entity in raw_response.get("entities", []):
            entity = ExtractedEntity(
                entity_type=raw_entity.get("entity_type", ""),
                name=raw_entity.get("name", ""),
                properties=raw_entity.get("properties", {}),
                confidence=float(raw_entity.get("confidence", 0.5)),
                source_chunk_index=chunk_index,
            )

            # Validate against ontology
            violations = validate_entity(entity.entity_type, {"name": entity.name, **entity.properties})
            if violations:
                result.violations.extend(violations)
            else:
                result.entities.append(entity)

        # Parse relations
        for raw_rel in raw_response.get("relations", []):
            relation = ExtractedRelation(
                relation_type=raw_rel.get("relation_type", ""),
                source_name=raw_rel.get("source_name", ""),
                source_type=raw_rel.get("source_type", ""),
                target_name=raw_rel.get("target_name", ""),
                target_type=raw_rel.get("target_type", ""),
                confidence=float(raw_rel.get("confidence", 0.5)),
                source_chunk_index=chunk_index,
            )

            # Validate against ontology
            violations = validate_relation(
                relation.relation_type, relation.source_type, relation.target_type
            )
            if violations:
                result.violations.extend(violations)
            else:
                result.relations.append(relation)

        logger.info(
            f"Chunk {chunk_index}: extracted {len(result.entities)} entities, "
            f"{len(result.relations)} relations, {len(result.violations)} violations"
        )
        return result

    async def extract_from_chunks(
        self, chunks: List[Any], source_document: str
    ) -> List[ExtractionResult]:
        """
        Extract from multiple chunks sequentially (respects rate limits).

        Processes chunks one at a time with a delay between requests.
        """
        results = []

        for chunk in chunks:
            result = await self.extract_from_chunk(
                text=chunk.text,
                chunk_index=chunk.chunk_index,
                source_document=source_document,
            )
            results.append(result)

            # Rate limiting delay between API calls
            await asyncio.sleep(self._rate_limit_delay)

        total_entities = sum(len(r.entities) for r in results)
        total_relations = sum(len(r.relations) for r in results)
        total_violations = sum(len(r.violations) for r in results)

        logger.info(
            f"Extraction complete for '{source_document}': "
            f"{total_entities} entities, {total_relations} relations, "
            f"{total_violations} violations across {len(chunks)} chunks"
        )
        return results
