from app.cad.models import CADReleaseStatus
from app.cad.release_gate import evaluate_cad_release
from app.domain.intent import ParsedEngineeringIntent
from app.pipeline.builder import build_engineering_spec
from app.pipeline.evidence_guard import apply_source_evidence_guard
from app.pipeline.validation import validate_spec


def _unknown():
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _field(value, *, unit=None, text=None):
    return {
        "raw_value": value,
        "raw_unit": unit,
        "source_text": text,
        "state": "confirmed",
        "confidence": 1.0,
    }


def _intent(pipe_source: str):
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

    payload.update(
        {
            "component": _field("pipe bracket", text="pipe bracket"),
            "pipe_diameter": _field(42, unit="mm", text=pipe_source),
            "wall_thickness": _field(4, unit="mm", text="4 mm wall"),
            "bracket_width": _field(30, unit="mm", text="30 mm width"),
            "base_thickness": _field(6, unit="mm", text="6 mm base"),
            "hole_count": _field(2, text="two"),
            "hole_diameter": _field(
                6.6,
                unit="mm",
                text="two 6.6 mm holes",
            ),
            "material": _field("steel", text="steel"),
        }
    )
    return ParsedEngineeringIntent.model_validate(payload)


def _run(prompt: str, pipe_source: str):
    raw = _intent(pipe_source)
    guarded, guard_report = apply_source_evidence_guard(prompt, raw)
    spec = build_engineering_spec(prompt, guarded)
    validation = validate_spec(spec)
    release = evaluate_cad_release(spec, validation)
    return raw, guarded, guard_report, spec, validation, release


def test_cad_release_blocks_unsupported_pipe_unit():
    prompt = (
        "Create a steel pipe bracket for Ø42 pipe, "
        "4 mm wall, 30 mm width, 6 mm base, "
        "two 6.6 mm holes."
    )
    _, guarded, guard_report, spec, validation, release = _run(
        prompt,
        "Ø42 pipe",
    )

    assert guard_report.changed is True
    assert guarded.pipe_diameter.raw_unit is None
    assert spec.pipe_diameter.value is None
    assert validation.status.value == "needs_clarification"

    assert release.status == CADReleaseStatus.FAIL
    assert release.allowed is False
    assert "pipe_diameter" in release.blocking_fields
    assert release.accepted_parameters is None


def test_cad_release_passes_explicit_supported_geometry():
    prompt = (
        "Create a steel pipe bracket for Ø42 mm pipe, "
        "4 mm wall, 30 mm width, 6 mm base, "
        "two 6.6 mm holes."
    )
    _, guarded, guard_report, spec, validation, release = _run(
        prompt,
        "Ø42 mm pipe",
    )

    assert guard_report.changed is False
    assert guarded.pipe_diameter.raw_unit == "mm"
    assert validation.status.value == "ready"

    assert release.status == CADReleaseStatus.PASS
    assert release.allowed is True
    assert release.blocking_fields == []
    assert release.failed_rules == []

    params = release.accepted_parameters
    assert params is not None
    assert params.pipe_diameter_mm == 42.0
    assert params.wall_thickness_mm == 4.0
    assert params.bracket_width_mm == 30.0
    assert params.base_thickness_mm == 6.0
    assert params.hole_count == 2
    assert params.hole_diameter_mm == 6.6


def test_cad_release_rejects_generator_capability_mismatch():
    prompt = (
        "Create a steel pipe bracket for a 42 mm pipe, "
        "4 mm wall, 30 mm width, 6 mm base, "
        "three 6.6 mm holes."
    )
    raw = _intent("42 mm pipe")
    payload = raw.model_dump(mode="python")
    payload["hole_count"] = _field(3, text="three")
    intent = ParsedEngineeringIntent.model_validate(payload)

    guarded, _ = apply_source_evidence_guard(prompt, intent)
    spec = build_engineering_spec(prompt, guarded)
    validation = validate_spec(spec)
    release = evaluate_cad_release(spec, validation)

    assert validation.status.value == "ready"
    assert release.allowed is False
    assert "PIPE_SADDLE_V1_REQUIRES_TWO_HOLES" in release.failed_rules
