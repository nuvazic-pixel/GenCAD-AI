from __future__ import annotations

from typing import Any


def _key(value: Any) -> str:
    text = str(value).strip().lower().replace("_", " ").replace("-", " ")
    return " ".join(text.split())


COMPONENT_ALIASES = {
    "bracket": "pipe_bracket",
    "pipe bracket": "pipe_bracket",
    "wall bracket": "pipe_bracket",
    "pipe clamp bracket": "pipe_bracket",
    "pipe clamp": "pipe_bracket",
    "halter": "pipe_bracket",
    "rohrhalter": "pipe_bracket",
    "rohr halter": "pipe_bracket",
    "aluminiumhalter": "pipe_bracket",
    "aluminium halter": "pipe_bracket",
    "stahl rohrhalter": "pipe_bracket",
}

MATERIAL_ALIASES = {
    "steel": "steel",
    "stahl": "steel",
    "aluminium": "aluminium",
    "aluminum": "aluminium",
    "polymer": "polymer",
    "kunststoff": "polymer",
}

HOLE_SEMANTIC_ALIASES = {
    "clearance": "clearance",
    "clearance hole": "clearance",
    "clearance holes": "clearance",
    "clearance-hole": "clearance",
    "durchgangsbohrung": "clearance",
    "durchgangsbohrungen": "clearance",
    "threaded": "threaded",
    "threaded hole": "threaded",
    "threaded holes": "threaded",
    "gewindebohrung": "threaded",
    "gewindebohrungen": "threaded",
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
