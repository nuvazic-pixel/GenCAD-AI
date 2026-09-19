from __future__ import annotations

from typing import Any


def _key(value: Any) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


COMPONENT_ALIASES = {
    "bracket": "pipe_bracket",
    "pipe bracket": "pipe_bracket",
    "wall bracket": "pipe_bracket",
}

MATERIAL_ALIASES = {
    "steel": "steel",
    "aluminium": "aluminium",
    "aluminum": "aluminium",
    "polymer": "polymer",
}

HOLE_SEMANTIC_ALIASES = {
    "clearance": "clearance",
    "clearance hole": "clearance",
    "clearance holes": "clearance",
    "clearance-hole": "clearance",
    "threaded": "threaded",
    "threaded hole": "threaded",
    "threaded holes": "threaded",
}


def normalize_component_term(value: Any) -> str:
    key = _key(value)
    return COMPONENT_ALIASES.get(key, key.replace(" ", "_"))


def normalize_material_term(value: Any) -> str:
    key = _key(value)
    return MATERIAL_ALIASES.get(key, key)


def normalize_hole_semantics(value: Any) -> str:
    key = _key(value)
    return HOLE_SEMANTIC_ALIASES.get(key, key)
