import pytest

from app.cad.generator import derive_layout
from app.cad.models import ReleasedBracketParameters
from app.domain.intent import ParsedEngineeringIntent


def _unknown():
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _intent():
    fields = [
        "component",
        "pipe_diameter",
        "nominal_pipe_size",
        "wall_thickness",
        "bracket_width",
        "base_thickness",
        "fastener_designation",
        "fastener_count",
        "associated_fastener_designation",
        "hole_count",
        "hole_diameter",
        "hole_semantics",
        "material",
        "manufacturing_process",
        "load_statement",
    ]
    payload = {name: _unknown() for name in fields}
    payload["qualitative_requirements"] = []
    payload["unmapped_phrases"] = []
    return ParsedEngineeringIntent.model_validate(payload)


def test_cad_generator_never_accepts_parsed_intent_directly():
    with pytest.raises(TypeError, match="ReleasedBracketParameters only"):
        derive_layout(_intent())


def test_layout_is_deterministic_from_released_parameters():
    params = ReleasedBracketParameters(
        pipe_diameter_mm=42.0,
        wall_thickness_mm=4.0,
        bracket_width_mm=30.0,
        base_thickness_mm=6.0,
        hole_count=2,
        hole_diameter_mm=6.6,
    )

    first = derive_layout(params)
    second = derive_layout(params)

    assert first == second
    assert first.ring_inner_radius_mm == 21.0
    assert first.ring_outer_radius_mm == 25.0
    assert first.left_hole_x_mm == -31.6
    assert first.right_hole_x_mm == 31.6
    assert first.base_length_mm == 76.4


def test_generator_layout_rejects_unsupported_hole_count():
    params = ReleasedBracketParameters(
        pipe_diameter_mm=42.0,
        wall_thickness_mm=4.0,
        bracket_width_mm=30.0,
        base_thickness_mm=6.0,
        hole_count=3,
        hole_diameter_mm=6.6,
    )

    with pytest.raises(ValueError, match="exactly two"):
        derive_layout(params)
