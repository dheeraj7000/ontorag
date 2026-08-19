"""Tests for the ontology-guided extractor."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.extractor import (
    ExtractionResult,
    OntologyGuidedExtractor,
)


@pytest.fixture
def mock_llm_response():
    """A valid extraction response from the LLM."""
    return {
        "provider": "test",
        "response": {
            "entities": [
                {
                    "entity_type": "System",
                    "name": "FastAPI",
                    "properties": {"description": "A web framework"},
                    "confidence": 0.9,
                },
                {
                    "entity_type": "Technology",
                    "name": "Python",
                    "properties": {"type": "language", "version": "3.11"},
                    "confidence": 0.95,
                },
            ],
            "relations": [
                {
                    "relation_type": "USES",
                    "source_name": "FastAPI",
                    "source_type": "System",
                    "target_name": "Python",
                    "target_type": "Technology",
                    "confidence": 0.88,
                }
            ],
        },
    }


@pytest.mark.asyncio
async def test_extract_from_chunk_success(mock_llm_response):
    """Extractor parses a valid LLM response correctly."""
    extractor = OntologyGuidedExtractor()

    with patch.object(extractor.llm, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_response
        result = await extractor.extract_from_chunk(
            text="FastAPI is built with Python 3.11.",
            chunk_index=0,
            source_document="test.md",
        )

    assert isinstance(result, ExtractionResult)
    assert len(result.entities) == 2
    assert len(result.relations) == 1
    assert result.entities[0].name == "FastAPI"
    assert result.entities[0].entity_type == "System"
    assert result.relations[0].relation_type == "USES"
    assert result.violations == []


@pytest.mark.asyncio
async def test_extract_invalid_entity_type():
    """Extractor rejects entities with invalid types."""
    extractor = OntologyGuidedExtractor()

    bad_response = {
        "provider": "test",
        "response": {
            "entities": [
                {
                    "entity_type": "InvalidType",
                    "name": "Something",
                    "properties": {},
                    "confidence": 0.9,
                }
            ],
            "relations": [],
        },
    }

    with patch.object(extractor.llm, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = bad_response
        result = await extractor.extract_from_chunk(
            text="Some text",
            chunk_index=0,
            source_document="test.md",
        )

    assert len(result.entities) == 0
    assert len(result.violations) > 0
    assert "Unknown entity type" in result.violations[0]


@pytest.mark.asyncio
async def test_extract_invalid_relation_pair():
    """Extractor rejects relations with invalid source/target type pairs."""
    extractor = OntologyGuidedExtractor()

    bad_response = {
        "provider": "test",
        "response": {
            "entities": [],
            "relations": [
                {
                    "relation_type": "DEPENDS_ON",
                    "source_name": "SomeAPI",
                    "source_type": "API",
                    "target_name": "SomeConcept",
                    "target_type": "Concept",
                    "confidence": 0.8,
                }
            ],
        },
    }

    with patch.object(extractor.llm, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = bad_response
        result = await extractor.extract_from_chunk(
            text="Some text",
            chunk_index=0,
            source_document="test.md",
        )

    assert len(result.relations) == 0
    assert len(result.violations) > 0
    assert "not valid between" in result.violations[0]


@pytest.mark.asyncio
async def test_extract_handles_llm_error():
    """Extractor gracefully handles LLM failures."""
    extractor = OntologyGuidedExtractor()

    with patch.object(extractor.llm, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = RuntimeError("LLM unavailable")
        result = await extractor.extract_from_chunk(
            text="Some text",
            chunk_index=0,
            source_document="test.md",
        )

    assert result.entities == []
    assert result.relations == []
    assert len(result.violations) > 0
    assert "Extraction error" in result.violations[0]
