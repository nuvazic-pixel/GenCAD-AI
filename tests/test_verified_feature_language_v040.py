import pytest

from app.cad.feature_builder import build_pipe_saddle_feature_program
from app.cad.feature_compiler import compile_feature_program
from app.cad.feature_gate import verify_feature_program
from app.cad.feature_language import CADFeatureProgram
from app.cad.models import (
    CADReleaseDecision,
    CADReleaseStatus,
    ReleasedBracketParameters,
)
from app.domain.evidence import EvidenceState


def _evidence(state="confirmed", text="explicit"):
    return {
        "state": state,
        "confidence": 1.0,
        "provenance": {
            "source_type": "user_prompt",
            "source_ref": None,
            "rule_id": None,
            "original_text": text,
        },
    }


def _release():
    return CADReleaseDecision(
        status=CADReleaseStatus.PASS,
        allowed=True,
        generator="pipe_saddle_bracket_v1",
        accepted_parameters=ReleasedBracketParameters(
            pipe_diameter_mm=42.0,
            wall_thickness_mm=4.0,
            bracket_width_mm=30.0,
            base_thickness_mm=6.0,
            hole_count=2,
            hole_diameter_mm=6.6,
        ),
        evidence_summary={
            "pipe_diameter": _evidence(text="Ø42 mm pipe"),
            "wall_thickness": _evidence(text="4 mm wall"),
            "bracket_width": _evidence(text="30 mm width"),
            "base_thickness": _evidence(text="6 mm base"),
            "hole_count": _evidence(text="two holes"),
            "hole_diameter": _evidence(text="6.6 mm holes"),
        },
        reason="fixture",
    )


def test_released_bracket_maps_to_four_feature_program():
    program = build_pipe_saddle_feature_program(_release())

    assert program.version == "0.4.0"
    assert [feature.feature_id for feature in program.features] == [
        "base_plate",
        "pipe_saddle",
        "mounting_hole_left",
        "mounting_hole_right",
    ]

    assert program.features[0].evidence_state == EvidenceState.DERIVED
    assert program.features[1].evidence_state == EvidenceState.DERIVED


def test_feature_gate_releases_only_confirmed_or_derived_parameters():
    program = build_pipe_saddle_feature_program(_release())

    report, verified = verify_feature_program(program)

    assert report.passed is True
    assert report.blocked_features == []
    assert report.blocked_parameters == []
    assert verified is not None


def test_unknown_feature_parameter_blocks_program():
    program = build_pipe_saddle_feature_program(_release())
    payload = program.model_dump(mode="python")

    right = next(
        feature
        for feature in payload["features"]
        if feature["feature_id"] == "mounting_hole_right"
    )
    right["parameters"]["diameter_mm"] = {
        "value": None,
        "unit": "mm",
        "state": "unknown",
        "source_fields": ["hole_diameter"],
        "rule_id": None,
        "source_ref": None,
        "note": "missing",
    }

    blocked = CADFeatureProgram.model_validate(payload)
    report, verified = verify_feature_program(blocked)

    assert report.passed is False
    assert verified is None
    assert "mounting_hole_right" in report.blocked_features
    assert (
        "mounting_hole_right.diameter_mm"
        in report.blocked_parameters
    )


def test_hypothesis_feature_parameter_blocks_program():
    program = build_pipe_saddle_feature_program(_release())
    payload = program.model_dump(mode="python")

    saddle = next(
        feature
        for feature in payload["features"]
        if feature["feature_id"] == "pipe_saddle"
    )
    saddle["parameters"]["depth_mm"] = {
        "value": 30.0,
        "unit": "mm",
        "state": "hypothesis",
        "source_fields": ["bracket_width"],
        "rule_id": None,
        "source_ref": None,
        "note": "model guess",
    }

    blocked = CADFeatureProgram.model_validate(payload)
    report, verified = verify_feature_program(blocked)

    assert report.passed is False
    assert verified is None
    assert "pipe_saddle.depth_mm" in report.blocked_parameters


def test_cad_compiler_refuses_unverified_program_type():
    program = build_pipe_saddle_feature_program(_release())

    with pytest.raises(TypeError, match="VerifiedCADFeatureProgram only"):
        compile_feature_program(program)


def test_all_derived_parameters_have_rule_provenance():
    program = build_pipe_saddle_feature_program(_release())

    for feature in program.features:
        for parameter in feature.parameters.values():
            if parameter.state == EvidenceState.DERIVED:
                assert parameter.rule_id
