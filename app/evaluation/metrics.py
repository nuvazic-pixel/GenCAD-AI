from __future__ import annotations

from app.domain.evidence import EvidenceState
from app.domain.intent import ParsedEngineeringIntent, ParsedField
from app.domain.spec import EngineeringSpec
from app.evaluation.models import BenchmarkSummary, CaseMetrics
from app.pipeline.evidence_guard import unexpected_association_is_supported
from app.pipeline.normalizer import canonical_field
from app.pipeline.validation import ValidationReport


INTENT_FIELDS = [
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


def _unknown_expected() -> dict:
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _fields_match(
    field_name: str,
    expected: ParsedField,
    actual: ParsedField,
) -> bool:
    return canonical_field(field_name, expected) == canonical_field(field_name, actual)


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
        expected_payload = expected_intent.get(field_name, _unknown_expected())
        expected = ParsedField.model_validate(expected_payload)
        actual = getattr(actual_intent, field_name)

        if expected.state == "confirmed":
            metrics.explicit_fact_total += 1
            if actual.state == "confirmed" and _fields_match(field_name, expected, actual):
                metrics.explicit_fact_correct += 1

        if expected.state == "unknown":
            metrics.hallucination_opportunities += 1
            if actual.state != "unknown":
                supported_association = (
                    field_name == "associated_fastener_designation"
                    and unexpected_association_is_supported(
                        case["prompt"],
                        actual_intent,
                    )
                )
                if not supported_association:
                    metrics.hallucinated_fields += 1

        if expected.state == "hypothesis":
            metrics.uncertainty_total += 1
            if actual.state == "hypothesis":
                metrics.uncertainty_preserved += 1

    forbidden = case.get("forbidden_inferences", [])
    metrics.semantic_traps = len(forbidden)

    for trap in forbidden:
        confused = False

        if trap == "pipe_diameter":
            confused = spec.pipe_diameter.state != EvidenceState.UNKNOWN
        elif trap == "clearance_hole_diameter":
            confused = spec.hole_diameter.state != EvidenceState.UNKNOWN
        elif trap == "fastener_designation":
            confused = spec.fastener_designation.state != EvidenceState.UNKNOWN
        elif trap == "fastener_count":
            confused = spec.fastener_count.state != EvidenceState.UNKNOWN
        elif trap == "associated_fastener_designation":
            confused = spec.associated_fastener_designation.state != EvidenceState.UNKNOWN
        elif trap == "hole_count":
            confused = spec.hole_count.state != EvidenceState.UNKNOWN
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
