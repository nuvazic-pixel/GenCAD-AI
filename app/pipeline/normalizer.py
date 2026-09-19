from __future__ import annotations

import re
from typing import Any

from app.domain.intent import ParsedField


UNIT_ALIASES = {
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "millimetre": "mm",
    "millimetres": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "centimetre": "cm",
    "centimetres": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "kg": "kg",
}

UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0}

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "null": 0, "eins": 1, "ein": 1, "eine": 1, "zwei": 2, "drei": 3,
    "vier": 4, "fünf": 5, "funf": 5, "sechs": 6, "sieben": 7,
    "acht": 8, "neun": 9, "zehn": 10,
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def normalize_unit(unit: Any) -> str | None:
    text = normalize_text(unit)
    if not text:
        return None
    return UNIT_ALIASES.get(text, text)


def normalize_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_text(value)
    if not text:
        return None

    numeric = text.replace(",", ".")
    try:
        return float(numeric)
    except ValueError:
        pass

    if text in NUMBER_WORDS:
        return float(NUMBER_WORDS[text])

    tokens = re.split(r"[\s-]+", text)
    if tokens and all(token in NUMBER_WORDS for token in tokens):
        values = [NUMBER_WORDS[token] for token in tokens]
        if len(values) == 2 and values[0] >= 20 and values[1] < 10:
            return float(values[0] + values[1])

    return None


def normalize_integer(value: Any) -> int | None:
    number = normalize_number(value)
    if number is None or not float(number).is_integer():
        return None
    return int(number)


def normalize_length(field: ParsedField) -> tuple[float, str] | None:
    if field.state == "unknown":
        return None
    number = normalize_number(field.raw_value)
    unit = normalize_unit(field.raw_unit)
    if number is None or unit not in UNIT_TO_MM:
        return None
    return number * UNIT_TO_MM[unit], "mm"


def canonical_field(field_name: str, field: ParsedField) -> tuple[Any, Any]:
    if field.state == "unknown":
        return None, None

    if field_name in {
        "pipe_diameter",
        "wall_thickness",
        "bracket_width",
        "base_thickness",
        "hole_diameter",
    }:
        length = normalize_length(field)
        if length is not None:
            return round(length[0], 9), length[1]
        return normalize_number(field.raw_value) or normalize_text(field.raw_value), normalize_unit(field.raw_unit)

    if field_name in {"fastener_count", "hole_count"}:
        return normalize_integer(field.raw_value), None

    if field_name == "component":
        from app.pipeline.terminology import normalize_component_term
        return normalize_component_term(field.raw_value), None

    if field_name == "material":
        from app.pipeline.terminology import normalize_material_term
        return normalize_material_term(field.raw_value), None

    if field_name == "hole_semantics":
        from app.pipeline.terminology import normalize_hole_semantics
        return normalize_hole_semantics(field.raw_value), None

    if field_name == "load_statement":
        number = normalize_number(field.raw_value)
        unit = normalize_unit(field.raw_unit)
        if number is not None and unit:
            return (int(number) if number.is_integer() else number), unit

        text = normalize_text(field.raw_value)
        match = re.fullmatch(r"([0-9]+(?:[\.,][0-9]+)?)\s*([a-z]+)", text)
        if match:
            parsed = normalize_number(match.group(1))
            parsed_unit = normalize_unit(match.group(2))
            if parsed is not None:
                return (int(parsed) if parsed.is_integer() else parsed), parsed_unit
        return text, unit

    return normalize_text(field.raw_value), normalize_unit(field.raw_unit)
