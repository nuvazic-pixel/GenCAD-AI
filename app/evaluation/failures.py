from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.domain.evidence import EvidenceState
from app.domain.intent import ParsedEngineeringIntent, ParsedField
from app.domain.spec import EngineeringSpec
from app.pipeline.normalizer import canonical_field
from app.pipeline.validation import ValidationReport


class FailureType(str, Enum):
    EXTRACTION = "extraction_failure"
    UNCERTAINTY = "uncertainty_failure"
    SEMANTIC = "semantic_confusion"
    HALLUCINATION = "hallucination"
    OVERBLOCKING = "overblocking"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FailureEvent(BaseModel):
    type: FailureType
    severity: Severity
    field: str | None = None
    expected: Any = None
    actual: Any = None
    details: str


class CaseClassification(BaseModel):
    case_id: str
    failures: list[FailureEvent] = Field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.failures)


CRITICAL_HALLUCINATION_FIELDS = {
    "pipe_diameter",
    "nominal_pipe_size",
    "wall_thickness",
    "bracket_width",
    "base_thickness",
    "fastener_designation",
    "fastener_count",
    "hole_count",
    "hole_diameter",
    "load_statement",
}

HIGH_HALLUCINATION_FIELDS = {
    "material",
    "manufacturing_process",
    "hole_semantics",
}


def _unknown_expected() -> dict:
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _hallucination_severity(field_name: str) -> Severity:
    if field_name in CRITICAL_HALLUCINATION_FIELDS:
        return Severity.CRITICAL
    if field_name in HIGH_HALLUCINATION_FIELDS:
        return Severity.HIGH
    return Severity.MEDIUM


def _semantic_trap_triggered(trap: str, spec: EngineeringSpec) -> bool:
    if trap == "pipe_diameter":
        return spec.pipe_diameter.state != EvidenceState.UNKNOWN
    if trap == "clearance_hole_diameter":
        return spec.clearance_hole_diameter.state != EvidenceState.UNKNOWN
    if trap == "fastener_designation":
        return spec.fastener_designation.state != EvidenceState.UNKNOWN
    if trap == "fastener_count":
        return spec.fastener_count.state != EvidenceState.UNKNOWN
    if trap == "hole_count":
        return spec.hole_count.state != EvidenceState.UNKNOWN
    if trap == "material":
        return spec.material.state != EvidenceState.UNKNOWN
    if trap == "confirmed_material":
        return spec.material.state == EvidenceState.CONFIRMED
    if trap == "confirmed_fastener":
        return (
            spec.fastener_designation.state == EvidenceState.CONFIRMED
            or spec.fastener_count.state == EvidenceState.CONFIRMED
        )
    if trap in {"wall_thickness", "bracket_width", "base_thickness"}:
        return getattr(spec, trap).state != EvidenceState.UNKNOWN
    if trap in {"manufacturing_process", "load_statement"}:
        return getattr(spec, trap).state != EvidenceState.UNKNOWN
    if trap in {"force_newton", "safety_factor", "steel_grade", "alloy", "geometry"}:
        return False
    return False


def _field_snapshot(field: ParsedField) -> dict:
    return {
        "value": field.raw_value,
        "unit": field.raw_unit,
        "state": field.state,
    }


def classify_case(
    case: dict,
    actual_intent: ParsedEngineeringIntent,
    spec: EngineeringSpec,
    report: ValidationReport,
) -> CaseClassification:
    failures: list[FailureEvent] = []
    expected_intent = case["parsed_intent"]

    for field_name in [
        "component",
        "pipe_diameter",
        "nominal_pipe_size",
        "wall_thickness",
        "bracket_width",
        "base_thickness",
        "fastener_designation",
        "fastener_count",
        "hole_count",
        "hole_diameter",
        "hole_semantics",
        "material",
        "manufacturing_process",
        "load_statement",
    ]:
        expected = ParsedField.model_validate(
            expected_intent.get(field_name, _unknown_expected())
        )
        actual = getattr(actual_intent, field_name)

        if expected.state == "confirmed":
            matches = (
                actual.state == "confirmed"
                and canonical_field(field_name, actual)
                == canonical_field(field_name, expected)
            )
            if not matches:
                failures.append(
                    FailureEvent(
                        type=FailureType.EXTRACTION,
                        severity=Severity.MEDIUM,
                        field=field_name,
                        expected=_field_snapshot(expected),
                        actual=_field_snapshot(actual),
                        details="Explicit fact was missed or extracted incorrectly after deterministic normalization.",
                    )
                )

        elif expected.state == "hypothesis":
            if actual.state != "hypothesis":
                failures.append(
                    FailureEvent(
                        type=FailureType.UNCERTAINTY,
                        severity=Severity.HIGH,
                        field=field_name,
                        expected="hypothesis",
                        actual=actual.state,
                        details="Uncertain source language was not preserved as hypothesis.",
                    )
                )
            elif canonical_field(field_name, actual) != canonical_field(field_name, expected):
                failures.append(
                    FailureEvent(
                        type=FailureType.EXTRACTION,
                        severity=Severity.MEDIUM,
                        field=field_name,
                        expected=_field_snapshot(expected),
                        actual=_field_snapshot(actual),
                        details="Hypothesis state was preserved but the extracted value was incorrect.",
                    )
                )

        elif expected.state == "unknown" and actual.state != "unknown":
            failures.append(
                FailureEvent(
                    type=FailureType.HALLUCINATION,
                    severity=_hallucination_severity(field_name),
                    field=field_name,
                    expected="unknown",
                    actual=_field_snapshot(actual),
                    details="Model populated a field absent from calibrated benchmark ground truth.",
                )
            )

    for trap in case.get("forbidden_inferences", []):
        if _semantic_trap_triggered(trap, spec):
            failures.append(
                FailureEvent(
                    type=FailureType.SEMANTIC,
                    severity=Severity.CRITICAL,
                    field=trap,
                    expected="forbidden inference not triggered",
                    actual="triggered",
                    details=f"Encoded semantic safety trap triggered: {trap}",
                )
            )

    if case["expected_status"] == "ready" and report.status.value != "ready":
        failures.append(
            FailureEvent(
                type=FailureType.OVERBLOCKING,
                severity=Severity.MEDIUM,
                field="validation_status",
                expected="ready",
                actual=report.status.value,
                details="Complete positive-control case did not reach READY.",
            )
        )

    return CaseClassification(case_id=case["id"], failures=failures)
