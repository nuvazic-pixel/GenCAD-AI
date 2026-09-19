from app.domain.intent import ParsedEngineeringIntent
from app.evaluation.metrics import score_case, summarize
from app.pipeline.builder import build_engineering_spec
from app.pipeline.validation import validate_spec
from benchmarks import BENCHMARK


def test_perfect_ground_truth_has_zero_unsafe_proceed_and_zero_hallucination():
    results = []

    for case in BENCHMARK:
        intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])
        spec = build_engineering_spec(case["prompt"], intent)
        report = validate_spec(spec)
        results.append(score_case(case, intent, spec, report))

    summary = summarize("perfect-fixture", results)

    assert summary.unsafe_proceed_rate == 0.0
    assert summary.hallucinated_field_rate == 0.0
    assert summary.semantic_confusion_rate == 0.0
    assert summary.explicit_fact_recall == 1.0
    assert summary.uncertainty_preservation == 1.0
    assert summary.correct_ready_rate == 1.0
    assert summary.release_gate_passed is True


def test_positive_controls_exist():
    positives = [c for c in BENCHMARK if c["expected_status"] == "ready"]
    assert len(positives) >= 5
