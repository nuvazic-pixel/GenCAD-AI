from copy import deepcopy

from .cases_v023 import BENCHMARK as FROZEN_V023


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


BENCHMARK = deepcopy(FROZEN_V023)
BY_ID = {case["id"]: case for case in BENCHMARK}

for case in BENCHMARK:
    case["parsed_intent"]["associated_fastener_designation"] = _unknown()


def _move_designation_to_hole_association(case_id: str, designation: str, source_text: str):
    parsed = BY_ID[case_id]["parsed_intent"]
    parsed["fastener_designation"] = _unknown()
    parsed["associated_fastener_designation"] = _field(
        designation,
        text=source_text,
    )


for case_id, designation, source_text in [
    ("B02", "M6", "M6 holes"),
    ("B05", "M6", "M6 Bohrungen"),
    ("B11", "M6", "M6 holes"),
    ("B14", "M6", "M6 clearance holes"),
    ("B16", "M6", "M6 threaded holes"),
    ("P01", "M6", "M6 mounting holes"),
    ("P02", "M8", "M8 mounting holes"),
    ("P03", "M6", "M6 holes"),
    ("P04", "M6", "M6 mounting holes"),
    ("P05", "M6", "M6 Befestigungsbohrungen"),
]:
    _move_designation_to_hole_association(case_id, designation, source_text)

# "bracket width" explicitly identifies the component as a bracket.
BY_ID["B17"]["parsed_intent"]["component"] = _field(
    "bracket",
    text="bracket width",
)
