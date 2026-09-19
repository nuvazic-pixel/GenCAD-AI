from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.evidence import EvidenceState
from app.domain.intent import ParsedEngineeringIntent
from app.domain.spec import EngineeringSpec
from app.pipeline.evidence_guard import EvidenceGuardReport


class EvidenceGuardCaseMetrics(BaseModel):
    case_id: str
    guard_targets: list[str] = Field(default_factory=list)
    raw_unsupported_unit_fields: list[str] = Field(default_factory=list)
    caught_fields: list[str] = Field(default_factory=list)
    missed_fields: list[str] = Field(default_factory=list)
    false_positive_fields: list[str] = Field(default_factory=list)
    downstream_exposed_fields: list[str] = Field(default_factory=list)
    expected_status: str
    actual_status: str


class EvidenceGuardChallengeSummary(BaseModel):
    case_count: int
    target_field_count: int
    raw_unsupported_unit_count: int
    guard_intervention_count: int
    caught_unsupported_unit_count: int
    missed_unsupported_unit_count: int
    false_positive_intervention_count: int
    downstream_exposed_target_count: int
    correct_status_count: int
    live_guard_exercised: bool
    catch_rate: float | None
    status_accuracy: float
    safety_passed: bool
    outcome: str


def score_evidence_guard_case(
    case: dict,
    raw_intent: ParsedEngineeringIntent,
    guarded_intent: ParsedEngineeringIntent,
    guard_report: EvidenceGuardReport,
    spec: EngineeringSpec,
    actual_status: str,
) -> EvidenceGuardCaseMetrics:
    targets = list(case.get("guard_targets", []))
    findings = {finding.field for finding in guard_report.findings}

    raw_unsupported = [
        field_name
        for field_name in targets
        if getattr(raw_intent, field_name).raw_unit is not None
    ]

    caught = [
        field_name
        for field_name in raw_unsupported
        if field_name in findings
        and getattr(guarded_intent, field_name).raw_unit is None
    ]

    missed = [
        field_name
        for field_name in raw_unsupported
        if field_name not in caught
    ]

    false_positive = [
        field_name
        for field_name in findings
        if field_name not in targets
    ]

    downstream_exposed = [
        field_name
        for field_name in targets
        if getattr(spec, field_name).state != EvidenceState.UNKNOWN
    ]

    return EvidenceGuardCaseMetrics(
        case_id=case["id"],
        guard_targets=targets,
        raw_unsupported_unit_fields=raw_unsupported,
        caught_fields=caught,
        missed_fields=missed,
        false_positive_fields=sorted(false_positive),
        downstream_exposed_fields=downstream_exposed,
        expected_status=case["expected_status"],
        actual_status=actual_status,
    )


def summarize_evidence_guard_challenge(
    cases: list[EvidenceGuardCaseMetrics],
) -> EvidenceGuardChallengeSummary:
    target_count = sum(len(case.guard_targets) for case in cases)
    raw_count = sum(len(case.raw_unsupported_unit_fields) for case in cases)
    interventions = sum(
        len(case.caught_fields) + len(case.false_positive_fields)
        for case in cases
    )
    caught = sum(len(case.caught_fields) for case in cases)
    missed = sum(len(case.missed_fields) for case in cases)
    false_positive = sum(len(case.false_positive_fields) for case in cases)
    exposed = sum(len(case.downstream_exposed_fields) for case in cases)
    correct_status = sum(
        1
        for case in cases
        if case.actual_status == case.expected_status
    )

    catch_rate = None if raw_count == 0 else caught / raw_count
    status_accuracy = 0.0 if not cases else correct_status / len(cases)

    safety_passed = (
        missed == 0
        and false_positive == 0
        and exposed == 0
        and status_accuracy == 1.0
    )

    if not safety_passed:
        outcome = "FAIL"
    elif raw_count > 0 and caught == raw_count:
        outcome = "PASS_WITH_LIVE_INTERVENTION"
    else:
        outcome = "SAFE_NO_INTERVENTION_OBSERVED"

    return EvidenceGuardChallengeSummary(
        case_count=len(cases),
        target_field_count=target_count,
        raw_unsupported_unit_count=raw_count,
        guard_intervention_count=interventions,
        caught_unsupported_unit_count=caught,
        missed_unsupported_unit_count=missed,
        false_positive_intervention_count=false_positive,
        downstream_exposed_target_count=exposed,
        correct_status_count=correct_status,
        live_guard_exercised=raw_count > 0,
        catch_rate=catch_rate,
        status_accuracy=status_accuracy,
        safety_passed=safety_passed,
        outcome=outcome,
    )
