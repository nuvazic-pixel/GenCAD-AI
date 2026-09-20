from app.cad.reproducibility import (
    canonical_payload_hash,
    evaluate_geometry_reproducibility,
)
from app.cad.reproducibility_models import GeometryBuildRecord
from app.cad.verification import canonical_triangle_fingerprint


def _build(build_id: str, fingerprint: str):
    return GeometryBuildRecord(
        build_id=build_id,
        geometry_fingerprint=fingerprint,
        stl_sha256=f"stl-{build_id}",
        step_sha256=f"step-{build_id}",
        verification_passed=True,
        artifact_releasable=True,
        volume_mm3=100.0,
        bbox_mm=[10.0, 20.0, 30.0],
    )


def test_canonical_triangle_fingerprint_ignores_triangle_order():
    triangles_a = [
        [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
        [(0, 0, 1), (1, 0, 1), (0, 1, 1)],
    ]
    triangles_b = list(reversed(triangles_a))

    assert (
        canonical_triangle_fingerprint(triangles_a)
        == canonical_triangle_fingerprint(triangles_b)
    )


def test_canonical_triangle_fingerprint_ignores_vertex_order():
    triangles_a = [
        [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
    ]
    triangles_b = [
        [(0, 1, 0), (0, 0, 0), (1, 0, 0)],
    ]

    assert (
        canonical_triangle_fingerprint(triangles_a)
        == canonical_triangle_fingerprint(triangles_b)
    )


def test_reproducibility_passes_for_identical_geometry_fingerprints():
    fp = "sha256:same"
    report = evaluate_geometry_reproducibility(
        generator_id="pipe_saddle_bracket_v1",
        repeat_count=3,
        released_parameters_hash=canonical_payload_hash({"pipe": 42}),
        layout_hash=canonical_payload_hash({"base": 76.4}),
        builds=[
            _build("build_01", fp),
            _build("build_02", fp),
            _build("build_03", fp),
        ],
        sensitivity_control_fingerprint="sha256:different",
    )

    assert report.passed is True
    assert report.fingerprints_match is True
    assert report.all_verified is True
    assert report.all_releasable is True
    assert report.sensitivity_control_differs is True
    assert report.failed_rules == []


def test_reproducibility_fails_on_one_geometry_mismatch():
    report = evaluate_geometry_reproducibility(
        generator_id="pipe_saddle_bracket_v1",
        repeat_count=3,
        released_parameters_hash="sha256:params",
        layout_hash="sha256:layout",
        builds=[
            _build("build_01", "sha256:a"),
            _build("build_02", "sha256:a"),
            _build("build_03", "sha256:b"),
        ],
        sensitivity_control_fingerprint="sha256:c",
    )

    assert report.passed is False
    assert report.fingerprints_match is False
    assert "REPRODUCIBILITY_FINGERPRINT_MISMATCH" in report.failed_rules


def test_reproducibility_fails_if_sensitivity_control_collides():
    fp = "sha256:same"
    report = evaluate_geometry_reproducibility(
        generator_id="pipe_saddle_bracket_v1",
        repeat_count=2,
        released_parameters_hash="sha256:params",
        layout_hash="sha256:layout",
        builds=[
            _build("build_01", fp),
            _build("build_02", fp),
        ],
        sensitivity_control_fingerprint=fp,
    )

    assert report.passed is False
    assert report.sensitivity_control_differs is False
    assert "REPRODUCIBILITY_SENSITIVITY_COLLISION" in report.failed_rules
