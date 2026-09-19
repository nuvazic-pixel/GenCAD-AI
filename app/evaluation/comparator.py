from __future__ import annotations

from pydantic import BaseModel, Field

from app.evaluation.failures import CaseClassification
from app.evaluation.models import BenchmarkSummary, CaseMetrics


class MetricDelta(BaseModel):
    baseline: float
    candidate: float
    delta: float


class BenchmarkComparison(BaseModel):
    fixed_failing_cases: list[str] = Field(default_factory=list)
    new_failing_cases: list[str] = Field(default_factory=list)
    positive_control_regressions: list[str] = Field(default_factory=list)
    metrics: dict[str, MetricDelta]
    meaningful_improvement: bool
    no_positive_control_regression: bool


def compare_benchmarks(
    baseline_summary: BenchmarkSummary,
    baseline_metrics: list[CaseMetrics],
    baseline_classifications: list[CaseClassification],
    candidate_summary: BenchmarkSummary,
    candidate_metrics: list[CaseMetrics],
    candidate_classifications: list[CaseClassification],
) -> BenchmarkComparison:
    base_classes = {c.case_id: c for c in baseline_classifications}
    cand_classes = {c.case_id: c for c in candidate_classifications}
    base_metrics = {c.case_id: c for c in baseline_metrics}
    cand_metrics = {c.case_id: c for c in candidate_metrics}

    fixed = sorted(
        case_id
        for case_id, base in base_classes.items()
        if base.has_failures
        and case_id in cand_classes
        and not cand_classes[case_id].has_failures
    )

    new_failures = sorted(
        case_id
        for case_id, candidate in cand_classes.items()
        if candidate.has_failures
        and case_id in base_classes
        and not base_classes[case_id].has_failures
    )

    regressions = sorted(
        case_id
        for case_id, base in base_metrics.items()
        if base.expected_status == "ready"
        and base.correct_ready
        and case_id in cand_metrics
        and not cand_metrics[case_id].correct_ready
    )

    names = [
        "explicit_fact_recall",
        "hallucinated_field_rate",
        "uncertainty_preservation",
        "semantic_confusion_rate",
        "unsafe_proceed_rate",
        "correct_ready_rate",
    ]
    deltas = {
        name: MetricDelta(
            baseline=getattr(baseline_summary, name),
            candidate=getattr(candidate_summary, name),
            delta=getattr(candidate_summary, name) - getattr(baseline_summary, name),
        )
        for name in names
    }

    return BenchmarkComparison(
        fixed_failing_cases=fixed,
        new_failing_cases=new_failures,
        positive_control_regressions=regressions,
        metrics=deltas,
        meaningful_improvement=bool(fixed) and not regressions,
        no_positive_control_regression=not regressions,
    )
