import argparse
import json
from pathlib import Path

from app.evaluation.comparator import compare_benchmarks
from app.evaluation.failures import CaseClassification
from app.evaluation.models import BenchmarkSummary, CaseMetrics
from app.evaluation.release_gate import ReleaseGateDecision


def _load_run(path: Path):
    report = json.loads((path / "benchmark_report.json").read_text(encoding="utf-8"))
    failures = json.loads((path / "failures.json").read_text(encoding="utf-8"))
    gate = json.loads((path / "release_gate.json").read_text(encoding="utf-8"))

    return (
        BenchmarkSummary.model_validate(report["summary"]),
        [CaseMetrics.model_validate(item) for item in report["cases"]],
        [CaseClassification.model_validate(item) for item in failures],
        ReleaseGateDecision.model_validate(gate),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    base_summary, base_metrics, base_classes, _ = _load_run(args.baseline)
    cand_summary, cand_metrics, cand_classes, cand_gate = _load_run(args.candidate)

    comparison = compare_benchmarks(
        base_summary,
        base_metrics,
        base_classes,
        cand_summary,
        cand_metrics,
        cand_classes,
    )

    accepted = (
        cand_gate.passed
        and comparison.meaningful_improvement
        and comparison.no_positive_control_regression
    )

    payload = {
        "accepted": accepted,
        "candidate_release_gate_passed": cand_gate.passed,
        "comparison": comparison.model_dump(mode="json"),
    }

    output = args.candidate / "comparison_to_baseline.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Wrote {output}")

    if not accepted:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
