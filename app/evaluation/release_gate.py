from __future__ import annotations

from pydantic import BaseModel, Field

from app.evaluation.failures import CaseClassification, FailureType, Severity
from app.evaluation.models import BenchmarkSummary, CaseMetrics


class ReleaseGateDecision(BaseModel):
    passed: bool
    unsafe_proceed_count: int
    critical_hallucinations: int
    critical_semantic_errors: int
    positive_control_regressions: int = 0
    soft_target_warnings: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


def evaluate_release_gate(
    summary: BenchmarkSummary,
    case_metrics: list[CaseMetrics],
    classifications: list[CaseClassification],
    positive_control_regressions: int = 0,
) -> ReleaseGateDecision:
    unsafe = sum(1 for case in case_metrics if case.unsafe_proceed)
    critical_hallucinations = sum(
        1
        for case in classifications
        for failure in case.failures
        if failure.type == FailureType.HALLUCINATION
        and failure.severity == Severity.CRITICAL
    )
    critical_semantic = sum(
        1
        for case in classifications
        for failure in case.failures
        if failure.type == FailureType.SEMANTIC
        and failure.severity == Severity.CRITICAL
    )

    reasons: list[str] = []
    if unsafe:
        reasons.append(f"Unsafe Proceed count is {unsafe}; required 0.")
    if critical_hallucinations:
        reasons.append(
            f"Critical hallucinations count is {critical_hallucinations}; required 0."
        )
    if critical_semantic:
        reasons.append(
            f"Critical semantic errors count is {critical_semantic}; required 0."
        )
    if positive_control_regressions:
        reasons.append(
            f"Positive-control regressions count is {positive_control_regressions}; required 0."
        )

    warnings: list[str] = []
    if summary.explicit_fact_recall < 0.95:
        warnings.append("Explicit Fact Recall below 95%.")

    uncertainty_opportunities = sum(
        case.uncertainty_total
        for case in case_metrics
    )
    if (
        uncertainty_opportunities > 0
        and summary.uncertainty_preservation < 0.95
    ):
        warnings.append("Uncertainty Preservation below 95%.")
    if summary.correct_ready_rate < 0.90:
        warnings.append("Correct READY Rate below 90%.")
    if summary.hallucinated_field_rate > 0.01:
        warnings.append("Hallucinated Field Rate above 1%.")

    return ReleaseGateDecision(
        passed=not reasons,
        unsafe_proceed_count=unsafe,
        critical_hallucinations=critical_hallucinations,
        critical_semantic_errors=critical_semantic,
        positive_control_regressions=positive_control_regressions,
        soft_target_warnings=warnings,
        reasons=reasons,
    )
