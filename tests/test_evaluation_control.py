from copy import deepcopy

from app.domain.intent import ParsedEngineeringIntent
from app.evaluation.comparator import compare_benchmarks
from app.evaluation.failures import (
    CaseClassification,
    FailureEvent,
    FailureType,
    Severity,
    classify_case,
)
from app.evaluation.fingerprint import create_fingerprint
from app.evaluation.metrics import score_case, summarize
from app.evaluation.models import BenchmarkSummary, CaseMetrics
from app.evaluation.release_gate import evaluate_release_gate
from app.pipeline.builder import build_engineering_spec
from app.pipeline.validation import validate_spec
from app.providers.prompt import SYSTEM_PROMPT
from benchmarks import BENCHMARK


def _case(case_id):
    return next(case for case in BENCHMARK if case["id"] == case_id)


def _evaluate(case, intent):
    spec = build_engineering_spec(case["prompt"], intent)
    report = validate_spec(spec)
    metrics = score_case(case, intent, spec, report)
    classification = classify_case(case, intent, spec, report)
    return spec, report, metrics, classification


def test_perfect_fixture_has_no_classified_failures():
    for case in BENCHMARK:
        intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])
        _, _, _, classification = _evaluate(case, intent)
        assert classification.failures == []


def test_invented_engineering_dimension_is_critical_hallucination():
    case = _case("B01")
    payload = deepcopy(case["parsed_intent"])
    payload["wall_thickness"] = {
        "raw_value": 4,
        "raw_unit": "mm",
        "source_text": None,
        "state": "confirmed",
        "confidence": 1.0,
    }
    intent = ParsedEngineeringIntent.model_validate(payload)
    _, _, metrics, classification = _evaluate(case, intent)

    hallucinations = [
        f for f in classification.failures
        if f.type == FailureType.HALLUCINATION
        and f.field == "wall_thickness"
    ]
    assert hallucinations
    assert hallucinations[0].severity == Severity.CRITICAL

    summary = summarize("fixture", [metrics])
    gate = evaluate_release_gate(summary, [metrics], [classification])
    assert gate.passed is False
    assert gate.critical_hallucinations >= 1


def test_uncertainty_promotion_is_high_failure():
    case = _case("B09")
    payload = deepcopy(case["parsed_intent"])
    payload["material"]["state"] = "confirmed"
    payload["material"]["confidence"] = 1.0
    intent = ParsedEngineeringIntent.model_validate(payload)
    _, _, _, classification = _evaluate(case, intent)

    failures = [
        f for f in classification.failures
        if f.type == FailureType.UNCERTAINTY
    ]
    assert failures
    assert failures[0].severity == Severity.HIGH


def test_overblocking_is_detected_for_positive_control():
    case = _case("P01")
    payload = deepcopy(case["parsed_intent"])
    payload["material"] = {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }
    intent = ParsedEngineeringIntent.model_validate(payload)
    _, report, _, classification = _evaluate(case, intent)

    assert report.status.value != "ready"
    assert any(
        f.type == FailureType.OVERBLOCKING
        for f in classification.failures
    )


def _summary(**overrides):
    data = dict(
        model="fixture",
        case_count=25,
        explicit_fact_recall=0.90,
        hallucinated_field_rate=0.02,
        uncertainty_preservation=0.90,
        semantic_confusion_rate=0.0,
        unsafe_proceed_rate=0.0,
        expected_ready_cases=5,
        correct_ready_cases=4,
        correct_ready_rate=0.80,
        release_gate_passed=True,
    )
    data.update(overrides)
    return BenchmarkSummary(**data)


def test_comparator_requires_case_level_fix_and_no_positive_regression():
    baseline_metrics = [
        CaseMetrics(
            case_id="B01",
            expected_status="needs_clarification",
            actual_status="needs_clarification",
        ),
        CaseMetrics(
            case_id="P01",
            expected_status="ready",
            actual_status="ready",
            correct_ready=True,
        ),
    ]
    candidate_metrics = [
        CaseMetrics(
            case_id="B01",
            expected_status="needs_clarification",
            actual_status="needs_clarification",
        ),
        CaseMetrics(
            case_id="P01",
            expected_status="ready",
            actual_status="ready",
            correct_ready=True,
        ),
    ]

    baseline_classes = [
        CaseClassification(
            case_id="B01",
            failures=[
                FailureEvent(
                    type=FailureType.EXTRACTION,
                    severity=Severity.MEDIUM,
                    field="pipe_diameter",
                    details="fixture",
                )
            ],
        ),
        CaseClassification(case_id="P01"),
    ]
    candidate_classes = [
        CaseClassification(case_id="B01"),
        CaseClassification(case_id="P01"),
    ]

    result = compare_benchmarks(
        _summary(),
        baseline_metrics,
        baseline_classes,
        _summary(explicit_fact_recall=0.95),
        candidate_metrics,
        candidate_classes,
    )

    assert result.fixed_failing_cases == ["B01"]
    assert result.positive_control_regressions == []
    assert result.meaningful_improvement is True


def test_fingerprint_identity_is_stable_for_same_inputs():
    kwargs = dict(
        run_id="baseline_001",
        provider="openai",
        model="fixture",
        prompt_version="v1",
        benchmark_version="0.2.2",
        schema_version="0.2.1",
        prompt=SYSTEM_PROMPT,
        benchmark=BENCHMARK,
        schema=ParsedEngineeringIntent.model_json_schema(),
        git_commit="abc123",
    )
    first = create_fingerprint(**kwargs)
    second = create_fingerprint(**kwargs)

    assert first.prompt_hash == second.prompt_hash
    assert first.benchmark_hash == second.benchmark_hash
    assert first.schema_hash == second.schema_hash
    assert first.fingerprint_id == second.fingerprint_id
