from copy import deepcopy

from .cases import BENCHMARK as FROZEN_V022


def _unknown():
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _field(value=None, unit=None, text=None, state="confirmed", confidence=1.0):
    if state == "unknown":
        return _unknown()
    return {
        "raw_value": value,
        "raw_unit": unit,
        "source_text": text,
        "state": state,
        "confidence": confidence,
    }


BENCHMARK = deepcopy(FROZEN_V022)
BY_ID = {case["id"]: case for case in BENCHMARK}

# New schema field exists for every case and is independent from fastener_count.
for case in BENCHMARK:
    parsed = case["parsed_intent"]
    parsed["hole_count"] = _unknown()
    parsed["qualitative_requirements"] = []
    parsed["unmapped_phrases"] = []


def _move_count_to_holes(case_id: str, count: int, source_text: str):
    parsed = BY_ID[case_id]["parsed_intent"]
    parsed["fastener_count"] = _unknown()
    parsed["hole_count"] = _field(count, text=source_text)


for case_id, count, source_text in [
    ("B02", 2, "two"),
    ("B05", 2, "zwei"),
    ("B11", 2, "two"),
    ("B15", 2, "two"),
    ("B16", 2, "Two"),
    ("P01", 2, "two"),
    ("P02", 2, "two"),
    ("P03", 2, "two"),
    ("P04", 2, "two"),
    ("P05", 2, "zwei"),
]:
    _move_count_to_holes(case_id, count, source_text)

# Ø50 states a numeric diameter but the prompt does not explicitly state a unit.
BY_ID["B02"]["parsed_intent"]["pipe_diameter"] = _field(
    50,
    unit=None,
    text="Ø50 pipe",
)

# Qualitative requirements are preserved separately and never promoted into loads/materials.
BY_ID["B07"]["parsed_intent"]["qualitative_requirements"] = [
    {
        "text": "Strong",
        "category": "strength",
        "source_text": "Strong",
        "confidence": 1.0,
    }
]
BY_ID["B20"]["parsed_intent"]["qualitative_requirements"] = [
    {
        "text": "lightweight",
        "category": "weight",
        "source_text": "lightweight",
        "confidence": 1.0,
    },
    {
        "text": "strong",
        "category": "strength",
        "source_text": "strong",
        "confidence": 1.0,
    },
]
