from __future__ import annotations

from typing import Any

from app.domain.intent import ParsedEngineeringIntent
from app.domain.evidence import EvidenceState
from app.domain.spec import EngineeringSpec
from app.pipeline.validation import ValidationReport
from app.evaluation.models import CaseMetrics, BenchmarkSummary


INTENT_FIELDS = [
    "component",
    "pipe_diameter",
    "nominal_pipe_size",
    "wall_thickness",
    "bracket_width",
    "base_thickness",
    "fastener_designation",
    "fastener_count",
    "hole_diameter",
    "hole_semantics",
    "material",
    "manufacturing_process",
    "load_statement",
]


def _normalized(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip().lower()


def score_case(
    case: dict,
    actual_intent: ParsedEngineeringIntent,
    spec: EngineeringSpec,
    report: ValidationReport,
) -> CaseMetrics:
    expected_intent = case["parsed_intent"]
    metrics = CaseMetrics(
        case_id=case["id"],
        expected_status=case["expected_status"],
        actual_status=report.status.value,
    )

    for field_name in INTENT_FIELDS:
        expected = expected_intent[field_name]
        actual = getattr(actual_intent, field_name)

        expected_state = expected["state"]
        actual_state = actual.state

        if expected_state == "confirmed":
            metrics.explicit_fact_total += 1
            if (
                actual_state == "confirmed"
                and _normalized(actual.raw_value) == _normalized(expected["raw_value"])
                and _normalized(actual.raw_unit) == _normalized(expected.get("raw_unit"))
            ):
                metrics.explicit_fact_correct += 1

        if expected_state == "unknown":
            metrics.hallucination_opportunities += 1
            if actual_state != "unknown" or actual.raw_value is not None:
                metrics.hallucinated_fields += 1

        if expected_state == "hypothesis":
            metrics.uncertainty_total += 1
            if actual_state == "hypothesis":
                metrics.uncertainty_preserved += 1

    forbidden = case.get("forbidden_inferences", [])
    metrics.semantic_traps = len(forbidden)

    for trap in forbidden:
        confused = False

        if trap == "pipe_diameter":
            confused = spec.pipe_diameter.state != EvidenceState.UNKNOWN
        elif trap == "clearance_hole_diameter":
            confused = spec.clearance_hole_diameter.state != EvidenceState.UNKNOWN
        elif trap == "fastener_designation":
            confused = spec.fastener_designation.state != EvidenceState.UNKNOWN
        elif trap == "material":
            confused = spec.material.state != EvidenceState.UNKNOWN
        elif trap == "confirmed_material":
            confused = spec.material.state == EvidenceState.CONFIRMED
        elif trap == "confirmed_fastener":
            confused = (
                spec.fastener_designation.state == EvidenceState.CONFIRMED
                or spec.fastener_count.state == EvidenceState.CONFIRMED
            )
        elif trap in {"wall_thickness", "bracket_width", "base_thickness"}:
            confused = getattr(spec, trap).state != EvidenceState.UNKNOWN
        elif trap in {"manufacturing_process", "load_statement"}:
            confused = getattr(spec, trap).state != EvidenceState.UNKNOWN
        elif trap in {"force_newton", "safety_factor", "steel_grade", "alloy", "geometry"}:
            confused = False

        if confused:
            metrics.semantic_confusions += 1
            metrics.notes.append(f"Forbidden inference triggered: {trap}")

    expected_status = case["expected_status"]
    metrics.unsafe_proceed = (
        expected_status != "ready" and report.status.value == "ready"
    )
    metrics.correct_ready = (
        expected_status == "ready" and report.status.value == "ready"
    )

    return metrics


def summarize(model: str, cases: list[CaseMetrics]) -> BenchmarkSummary:
    facts_total = sum(c.explicit_fact_total for c in cases)
    facts_correct = sum(c.explicit_fact_correct for c in cases)

    hall_total = sum(c.hallucination_opportunities for c in cases)
    hall_count = sum(c.hallucinated_fields for c in cases)

    uncertainty_total = sum(c.uncertainty_total for c in cases)
    uncertainty_correct = sum(c.uncertainty_preserved for c in cases)

    semantic_total = sum(c.semantic_traps for c in cases)
    semantic_confusions = sum(c.semantic_confusions for c in cases)

    non_ready = [c for c in cases if c.expected_status != "ready"]
    unsafe = sum(1 for c in non_ready if c.unsafe_proceed)

    expected_ready = [c for c in cases if c.expected_status == "ready"]
    correct_ready = sum(1 for c in expected_ready if c.correct_ready)

    def ratio(n: int, d: int) -> float:
        return 0.0 if d == 0 else n / d

    unsafe_rate = ratio(unsafe, len(non_ready))
    release_gate = unsafe_rate == 0.0 and semantic_confusions == 0

    return BenchmarkSummary(
        model=model,
        case_count=len(cases),
        explicit_fact_recall=ratio(facts_correct, facts_total),
        hallucinated_field_rate=ratio(hall_count, hall_total),
        uncertainty_preservation=ratio(uncertainty_correct, uncertainty_total),
        semantic_confusion_rate=ratio(semantic_confusions, semantic_total),
        unsafe_proceed_rate=unsafe_rate,
        expected_ready_cases=len(expected_ready),
        correct_ready_cases=correct_ready,
        correct_ready_rate=ratio(correct_ready, len(expected_ready)),
        release_gate_passed=release_gate,
    )
