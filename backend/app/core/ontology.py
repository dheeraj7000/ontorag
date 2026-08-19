"""
Domain Ontology Schema — defines valid entity types, relation types,
and validation rules for the knowledge graph.
"""

from typing import Any, Dict, List

# Entity classes in the ontology
ENTITY_CLASSES = {
    "System": {
        "description": "A software system or application",
        "properties": ["name", "version", "description", "language"],
    },
    "Component": {
        "description": "A module, package, or subsystem",
        "properties": ["name", "type", "description"],
    },
    "API": {
        "description": "An API endpoint or interface",
        "properties": ["name", "method", "path", "description"],
    },
    "Concept": {
        "description": "A technical concept or pattern",
        "properties": ["name", "definition", "category"],
    },
    "Technology": {
        "description": "A programming language, framework, or tool",
        "properties": ["name", "type", "version"],
    },
    "Configuration": {
        "description": "A configuration setting or parameter",
        "properties": ["name", "value", "default", "description"],
    },
    "DataModel": {
        "description": "A data structure, schema, or model",
        "properties": ["name", "fields", "description"],
    },
    "Process": {
        "description": "A workflow, pipeline, or procedure",
        "properties": ["name", "steps", "description"],
    },
}

# Valid relation types between entity classes
RELATION_TYPES = {
    "DEPENDS_ON": {
        "description": "Source depends on target",
        "valid_pairs": [
            ("System", "System"),
            ("System", "Technology"),
            ("Component", "Component"),
            ("Component", "Technology"),
        ],
    },
    "HAS_COMPONENT": {
        "description": "System contains a component",
        "valid_pairs": [("System", "Component")],
    },
    "HAS_API": {
        "description": "System or component exposes an API",
        "valid_pairs": [("System", "API"), ("Component", "API")],
    },
    "USES": {
        "description": "Entity uses another entity",
        "valid_pairs": [
            ("System", "Technology"),
            ("Component", "Technology"),
            ("API", "DataModel"),
            ("Process", "Technology"),
        ],
    },
    "IMPLEMENTS": {
        "description": "Entity implements a concept or pattern",
        "valid_pairs": [
            ("System", "Concept"),
            ("Component", "Concept"),
            ("Process", "Concept"),
        ],
    },
    "CONFIGURED_BY": {
        "description": "Entity is configured by a setting",
        "valid_pairs": [
            ("System", "Configuration"),
            ("Component", "Configuration"),
        ],
    },
    "PRODUCES": {
        "description": "Process produces a data model or output",
        "valid_pairs": [
            ("Process", "DataModel"),
            ("API", "DataModel"),
        ],
    },
    "CONSUMES": {
        "description": "Entity consumes data",
        "valid_pairs": [
            ("Process", "DataModel"),
            ("API", "DataModel"),
            ("Component", "DataModel"),
        ],
    },
    "PART_OF": {
        "description": "Entity is part of another",
        "valid_pairs": [
            ("Component", "System"),
            ("API", "Component"),
            ("Configuration", "System"),
        ],
    },
    "RELATED_TO": {
        "description": "General semantic relationship",
        "valid_pairs": [
            ("Concept", "Concept"),
            ("Technology", "Technology"),
            ("System", "System"),
        ],
    },
}


def load_ontology() -> Dict[str, Any]:
    """Load the full ontology schema as a dictionary (for LLM prompts)."""
    return {
        "entity_classes": {
            name: {
                "description": cls["description"],
                "properties": cls["properties"],
            }
            for name, cls in ENTITY_CLASSES.items()
        },
        "relation_types": {
            name: {
                "description": rel["description"],
                "valid_source_target_pairs": [
                    {"source": src, "target": tgt}
                    for src, tgt in rel["valid_pairs"]
                ],
            }
            for name, rel in RELATION_TYPES.items()
        },
    }


def validate_entity(entity_type: str, properties: Dict[str, Any]) -> List[str]:
    """
    Validate an entity against the ontology schema.

    Returns a list of violation messages (empty = valid).
    """
    violations = []

    if entity_type not in ENTITY_CLASSES:
        violations.append(
            f"Unknown entity type: '{entity_type}'. "
            f"Valid types: {list(ENTITY_CLASSES.keys())}"
        )
        return violations

    if "name" not in properties or not properties["name"]:
        violations.append(f"Entity of type '{entity_type}' must have a 'name' property.")

    return violations


def validate_relation(
    relation_type: str, source_type: str, target_type: str
) -> List[str]:
    """
    Validate a relation against the ontology schema.

    Returns a list of violation messages (empty = valid).
    """
    violations = []

    if relation_type not in RELATION_TYPES:
        violations.append(
            f"Unknown relation type: '{relation_type}'. "
            f"Valid types: {list(RELATION_TYPES.keys())}"
        )
        return violations

    valid_pairs = RELATION_TYPES[relation_type]["valid_pairs"]
    if (source_type, target_type) not in valid_pairs:
        violations.append(
            f"Relation '{relation_type}' is not valid between "
            f"'{source_type}' → '{target_type}'. "
            f"Valid pairs: {valid_pairs}"
        )

    return violations
