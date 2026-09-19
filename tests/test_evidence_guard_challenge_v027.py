from hashlib import sha256

from app.domain.intent import ParsedEngineeringIntent
from app.evaluation.evidence_guard_challenge import (
    score_evidence_guard_case,
    summarize_evidence_guard_challenge,
)
from app.pipeline.builder import build_engineering_spec
from app.pipeline.evidence_guard import apply_source_evidence_guard
from app.pipeline.validation import validate_spec
from app.providers.prompt import SYSTEM_PROMPT
from benchmarks import (
    BENCHMARK_V024,
    HOLDOUT_V025,
    HOLDOUT_V026,
    EVIDENCE_GUARD_CHALLENGE_V027,
)


PROMPT_V1_HASH = "ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d"


def _case(case_id: str):
    return next(
        case
        for case in EVIDENCE_GUARD_CHALLENGE_V027
        if case["id"] == case_id
    )


def test_v027_has_eight_focused_cases():
    assert len(EVIDENCE_GUARD_CHALLENGE_V027) == 8
    assert [case["id"] for case in EVIDENCE_GUARD_CHALLENGE_V027] == [
        f"EG{i:02d}" for i in range(1, 9)
    ]


def test_v027_is_disjoint_from_all_previous_live_sets():
    prior = {
        case["prompt"]
        for case in [
            *BENCHMARK_V024,
            *HOLDOUT_V025,
            *HOLDOUT_V026,
        ]
    }
    current = {
        case["prompt"]
        for case in EVIDENCE_GUARD_CHALLENGE_V027
    }

    assert len(current) == 8
    assert prior.isdisjoint(current)


def test_prompt_v1_remains_frozen_for_v027():
    assert sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest() == PROMPT_V1_HASH


def test_v027_ground_truth_is_internally_consistent():
    for case in EVIDENCE_GUARD_CHALLENGE_V027:
        raw = ParsedEngineeringIntent.model_validate(case["parsed_intent"])
        guarded, guard_report = apply_source_evidence_guard(
            case["prompt"],
            raw,
        )
        spec = build_engineering_spec(case["prompt"], guarded)
        report = validate_spec(spec)

        assert guard_report.findings == []
        assert report.status.value == case["expected_status"]
        assert report.expected_stage == case["expected_stage"]


def test_live_intervention_metrics_capture_supported_guard_action():
    case = _case("EG01")
    payload = dict(case["parsed_intent"])
    payload["pipe_diameter"] = dict(payload["pipe_diameter"])
    payload["pipe_diameter"]["raw_unit"] = "mm"

    raw = ParsedEngineeringIntent.model_validate(payload)
    guarded, guard_report = apply_source_evidence_guard(
        case["prompt"],
        raw,
    )
    spec = build_engineering_spec(case["prompt"], guarded)
    report = validate_spec(spec)

    metrics = score_evidence_guard_case(
        case=case,
        raw_intent=raw,
        guarded_intent=guarded,
        guard_report=guard_report,
        spec=spec,
        actual_status=report.status.value,
    )
    summary = summarize_evidence_guard_challenge([metrics])

    assert metrics.raw_unsupported_unit_fields == ["pipe_diameter"]
    assert metrics.caught_fields == ["pipe_diameter"]
    assert metrics.missed_fields == []
    assert metrics.downstream_exposed_fields == []
    assert summary.live_guard_exercised is True
    assert summary.catch_rate == 1.0
    assert summary.safety_passed is True
    assert summary.outcome == "PASS_WITH_LIVE_INTERVENTION"


def test_challenge_detects_source_text_scope_bypass():
    case = _case("EG01")
    payload = dict(case["parsed_intent"])
    payload["pipe_diameter"] = dict(payload["pipe_diameter"])
    payload["pipe_diameter"]["raw_unit"] = "mm"
    payload["pipe_diameter"]["source_text"] = "Ø42 pipe; wall 4 mm"

    raw = ParsedEngineeringIntent.model_validate(payload)
    guarded, guard_report = apply_source_evidence_guard(
        case["prompt"],
        raw,
    )
    spec = build_engineering_spec(case["prompt"], guarded)
    report = validate_spec(spec)

    metrics = score_evidence_guard_case(
        case=case,
        raw_intent=raw,
        guarded_intent=guarded,
        guard_report=guard_report,
        spec=spec,
        actual_status=report.status.value,
    )
    summary = summarize_evidence_guard_challenge([metrics])

    assert guard_report.findings == []
    assert metrics.raw_unsupported_unit_fields == ["pipe_diameter"]
    assert metrics.caught_fields == []
    assert metrics.missed_fields == ["pipe_diameter"]
    assert metrics.downstream_exposed_fields == ["pipe_diameter"]
    assert summary.safety_passed is False
    assert summary.outcome == "FAIL"


def test_controls_have_no_guard_targets():
    assert _case("EG07")["guard_targets"] == []
    assert _case("EG08")["guard_targets"] == []
