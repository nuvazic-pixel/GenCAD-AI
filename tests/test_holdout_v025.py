from hashlib import sha256

from app.domain.intent import ParsedEngineeringIntent
from app.evaluation.failures import classify_case
from app.evaluation.metrics import score_case, summarize
from app.evaluation.release_gate import evaluate_release_gate
from app.pipeline.builder import build_engineering_spec
from app.pipeline.validation import validate_spec
from app.providers.prompt import SYSTEM_PROMPT
from benchmarks import BENCHMARK_V024, HOLDOUT_V025


PROMPT_V1_HASH = "ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d"


def test_holdout_has_exactly_15_frozen_cases():
    assert len(HOLDOUT_V025) == 15
    assert [case["id"] for case in HOLDOUT_V025] == [
        f"H{i:02d}" for i in range(1, 16)
    ]


def test_holdout_prompts_are_disjoint_from_development_benchmark():
    dev_prompts = {case["prompt"] for case in BENCHMARK_V024}
    holdout_prompts = {case["prompt"] for case in HOLDOUT_V025}

    assert len(holdout_prompts) == 15
    assert dev_prompts.isdisjoint(holdout_prompts)


def test_prompt_v1_is_still_byte_for_byte_frozen():
    assert sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest() == PROMPT_V1_HASH


def test_holdout_ground_truth_fixture_is_internally_consistent():
    metrics = []
    classifications = []

    for case in HOLDOUT_V025:
        intent = ParsedEngineeringIntent.model_validate(case["parsed_intent"])
        spec = build_engineering_spec(case["prompt"], intent)
        report = validate_spec(spec)

        assert report.status.value == case["expected_status"]
        assert report.expected_stage == case["expected_stage"]

        case_metrics = score_case(case, intent, spec, report)
        classification = classify_case(case, intent, spec, report)

        metrics.append(case_metrics)
        classifications.append(classification)

        assert classification.failures == []

    summary = summarize("perfect-holdout-fixture", metrics)
    gate = evaluate_release_gate(summary, metrics, classifications)

    assert summary.case_count == 15
    assert summary.explicit_fact_recall == 1.0
    assert summary.hallucinated_field_rate == 0.0
    assert summary.uncertainty_preservation == 1.0
    assert summary.semantic_confusion_rate == 0.0
    assert summary.unsafe_proceed_rate == 0.0
    assert summary.correct_ready_rate == 1.0
    assert gate.passed is True


def test_holdout_contains_ready_rejected_and_clarification_cases():
    statuses = {case["expected_status"] for case in HOLDOUT_V025}

    assert statuses == {"ready", "rejected", "needs_clarification"}
    assert sum(case["expected_status"] == "ready" for case in HOLDOUT_V025) >= 5
