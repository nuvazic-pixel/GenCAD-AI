import pytest

from app.cad.artifact_gate import evaluate_cad_artifact_release
from app.cad.generator import derive_layout
from app.cad.models import ReleasedBracketParameters
from app.cad.verification import verify_bracket_stl
from app.cad.verification_models import (
    CADArtifactReleaseStatus,
    GeometryVerificationReport,
)


def _params():
    return ReleasedBracketParameters(
        pipe_diameter_mm=42.0,
        wall_thickness_mm=4.0,
        bracket_width_mm=30.0,
        base_thickness_mm=6.0,
        hole_count=2,
        hole_diameter_mm=6.6,
    )


def _report(*, passed: bool, failed_rules: list[str]):
    return GeometryVerificationReport(
        artifact_file="fixture.stl",
        solid_valid=passed,
        watertight=passed,
        positive_volume=passed,
        volume_mm3=1000.0 if passed else 0.0,
        expected_hole_count=2,
        detected_hole_count=2 if passed else 1,
        hole_count_match=passed,
        expected_bbox_mm=[76.4, 30.0, 52.0],
        measured_bbox_mm=[76.4, 30.0, 52.0],
        bbox_delta_mm=[0.0, 0.0, 0.0],
        dimensions_match=True,
        expected_pipe_diameter_mm=42.0,
        measured_pipe_diameter_mm=42.0,
        pipe_diameter_delta_mm=0.0,
        pipe_opening_match=True,
        expected_wall_mm=4.0,
        measured_wall_mm=4.0,
        wall_delta_mm=0.0,
        wall_check_passed=True,
        geometry_fingerprint="sha256:fixture",
        failed_rules=failed_rules,
        passed=passed,
    )


def test_geometry_verifier_requires_released_parameters():
    params = _params()
    layout = derive_layout(params)

    with pytest.raises(TypeError, match="ReleasedBracketParameters"):
        verify_bracket_stl("does-not-matter.stl", object(), layout)


def test_artifact_release_gate_passes_verified_geometry():
    decision = evaluate_cad_artifact_release(
        _report(passed=True, failed_rules=[])
    )

    assert decision.status == CADArtifactReleaseStatus.PASS
    assert decision.releasable is True
    assert decision.failed_rules == []
    assert decision.geometry_fingerprint == "sha256:fixture"


def test_artifact_release_gate_quarantines_failed_geometry():
    decision = evaluate_cad_artifact_release(
        _report(
            passed=False,
            failed_rules=["HOLE_COUNT_MISMATCH"],
        )
    )

    assert decision.status == CADArtifactReleaseStatus.FAIL
    assert decision.releasable is False
    assert decision.failed_rules == ["HOLE_COUNT_MISMATCH"]


def test_same_released_parameters_have_same_expected_layout():
    params = _params()
    first = derive_layout(params)
    second = derive_layout(params)

    assert first == second
