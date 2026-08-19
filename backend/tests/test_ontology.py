"""Tests for ontology validation."""

from backend.app.core.ontology import (
    load_ontology,
    validate_entity,
    validate_relation,
)


def test_load_ontology_returns_dict():
    """Ontology loads as a dictionary with expected keys."""
    ontology = load_ontology()
    assert "entity_classes" in ontology
    assert "relation_types" in ontology
    assert len(ontology["entity_classes"]) > 0
    assert len(ontology["relation_types"]) > 0


def test_valid_entity_passes():
    """A valid entity should produce no violations."""
    violations = validate_entity("System", {"name": "FastAPI"})
    assert violations == []


def test_valid_entity_all_types():
    """All defined entity types should pass validation."""
    valid_types = ["System", "Component", "API", "Concept", "Technology",
                   "Configuration", "DataModel", "Process"]
    for entity_type in valid_types:
        violations = validate_entity(entity_type, {"name": f"Test {entity_type}"})
        assert violations == [], f"Failed for type: {entity_type}"


def test_invalid_entity_type():
    """Unknown entity type should produce a violation."""
    violations = validate_entity("UnknownType", {"name": "Test"})
    assert len(violations) == 1
    assert "Unknown entity type" in violations[0]


def test_entity_without_name():
    """Entity without a name should produce a violation."""
    violations = validate_entity("System", {"description": "No name"})
    assert len(violations) == 1
    assert "must have a 'name' property" in violations[0]


def test_valid_relation_passes():
    """A valid relation should produce no violations."""
    violations = validate_relation("DEPENDS_ON", "System", "Technology")
    assert violations == []


def test_invalid_relation_type():
    """Unknown relation type should produce a violation."""
    violations = validate_relation("UNKNOWN_REL", "System", "System")
    assert len(violations) == 1
    assert "Unknown relation type" in violations[0]


def test_invalid_relation_pair():
    """A relation with invalid source/target types should fail."""
    # DEPENDS_ON is not valid between API and Concept
    violations = validate_relation("DEPENDS_ON", "API", "Concept")
    assert len(violations) == 1
    assert "not valid between" in violations[0]


def test_all_relation_valid_pairs():
    """All documented valid pairs should pass validation."""
    from backend.app.core.ontology import RELATION_TYPES

    for rel_type, rel_info in RELATION_TYPES.items():
        for source, target in rel_info["valid_pairs"]:
            violations = validate_relation(rel_type, source, target)
            assert violations == [], (
                f"Failed for {rel_type}: {source} -> {target}"
            )
