from __future__ import annotations

from app.domain.evidence import EvidenceState, EngineeringValue
from app.domain.spec import EngineeringSpec
from app.cad.models import (
    CADReleaseDecision,
    CADReleaseStatus,
    ReleasedBracketParameters,
)
from app.pipeline.validation import ValidationReport, ValidationStatus


ALLOWED_CAD_STATES = {
    EvidenceState.CONFIRMED,
    EvidenceState.DERIVED,
}

GENERATOR_ID = "pipe_saddle_bracket_v1"


def _evidence_snapshot(value: EngineeringValue) -> dict:
    return {
        "state": value.state.value,
        "confidence": value.confidence,
        "provenance": value.provenance.model_dump(mode="json"),
    }


def evaluate_cad_release(
    spec: EngineeringSpec,
    validation: ValidationReport,
) -> CADReleaseDecision:
    geometry_fields = {
        "pipe_diameter": spec.pipe_diameter,
        "wall_thickness": spec.wall_thickness,
        "bracket_width": spec.bracket_width,
        "base_thickness": spec.base_thickness,
        "hole_count": spec.hole_count,
        "hole_diameter": spec.hole_diameter,
    }

    evidence_summary = {
        name: _evidence_snapshot(value)
        for name, value in geometry_fields.items()
    }

    blocking_fields = [
        name
        for name, value in geometry_fields.items()
        if value.state not in ALLOWED_CAD_STATES or value.value is None
    ]

    failed_rules: list[str] = []

    if validation.status != ValidationStatus.READY:
        failed_rules.append("ENGINEERING_SPEC_NOT_READY")

    if spec.component.value is None or spec.component.value.value != "pipe_bracket":
        failed_rules.append("GENERATOR_COMPONENT_UNSUPPORTED")

    if spec.hole_count.value is not None and spec.hole_count.value != 2:
        failed_rules.append("PIPE_SADDLE_V1_REQUIRES_TWO_HOLES")

    if blocking_fields or failed_rules:
        reasons = []
        if blocking_fields:
            reasons.append(
                "CAD boundary rejected non-confirmed/non-derived geometry fields: "
                + ", ".join(blocking_fields)
            )
        if failed_rules:
            reasons.append("Failed CAD rules: " + ", ".join(failed_rules))

        return CADReleaseDecision(
            status=CADReleaseStatus.FAIL,
            allowed=False,
            generator=GENERATOR_ID,
            blocking_fields=blocking_fields,
            failed_rules=failed_rules,
            accepted_parameters=None,
            evidence_summary=evidence_summary,
            reason="; ".join(reasons),
        )

    params = ReleasedBracketParameters(
        pipe_diameter_mm=spec.pipe_diameter.value.value_mm,
        wall_thickness_mm=spec.wall_thickness.value.value_mm,
        bracket_width_mm=spec.bracket_width.value.value_mm,
        base_thickness_mm=spec.base_thickness.value.value_mm,
        hole_count=spec.hole_count.value,
        hole_diameter_mm=spec.hole_diameter.value.value_mm,
    )

    return CADReleaseDecision(
        status=CADReleaseStatus.PASS,
        allowed=True,
        generator=GENERATOR_ID,
        accepted_parameters=params,
        evidence_summary=evidence_summary,
        reason="All CAD geometry inputs are CONFIRMED or deterministically DERIVED and the engineering spec is READY.",
    )
