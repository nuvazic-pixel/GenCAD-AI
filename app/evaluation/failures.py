from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.domain.evidence import EvidenceState
from app.domain.intent import ParsedEngineeringIntent
from app.domain.spec import EngineeringSpec
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
    "hole_diameter",
    "load_statement",
}

HIGH_HALLUCINATION_FIELDS = {
    "material",
    "manufacturing_process",
    "hole_semantics",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


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

    # These concepts are intentionally not represented by the current schema.
    # A future schema extension must add explicit detection before relying on them.
    if trap in {"force_newton", "safety_factor", "steel_grade", "alloy", "geometry"}:
        return False

    return False


def classify_case(
    case: dict,
    actual_intent: ParsedEngineeringIntent,
    spec: EngineeringSpec,
    report: ValidationReport,
) -> CaseClassification:
    failures: list[FailureEvent] = []
    expected_intent = case["parsed_intent"]

    for field_name, expected in expected_intent.items():
        actual = getattr(actual_intent, field_name)
        expected_state = expected["state"]

        if expected_state == "confirmed":
            matches = (
                actual.state == "confirmed"
                and _norm(actual.raw_value) == _norm(expected["raw_value"])
                and _norm(actual.raw_unit) == _norm(expected.get("raw_unit"))
            )
            if not matches:
                failures.append(
                    FailureEvent(
                        type=FailureType.EXTRACTION,
                        severity=Severity.MEDIUM,
                        field=field_name,
                        expected={
                            "value": expected["raw_value"],
                            "unit": expected.get("raw_unit"),
                            "state": "confirmed",
                        },
                        actual={
                            "value": actual.raw_value,
                            "unit": actual.raw_unit,
                            "state": actual.state,
                        },
                        details="Explicit fact was missed or extracted incorrectly.",
                    )
                )

        elif expected_state == "hypothesis":
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

        elif expected_state == "unknown":
            if actual.state != "unknown" or actual.raw_value is not None:
                failures.append(
                    FailureEvent(
                        type=FailureType.HALLUCINATION,
                        severity=_hallucination_severity(field_name),
                        field=field_name,
                        expected="unknown",
                        actual={
                            "value": actual.raw_value,
                            "unit": actual.raw_unit,
                            "state": actual.state,
                        },
                        details="Model populated a field absent from benchmark ground truth.",
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
