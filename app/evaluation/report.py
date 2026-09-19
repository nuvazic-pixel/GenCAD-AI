from pathlib import Path
import json

from app.evaluation.models import BenchmarkSummary, CaseMetrics


def write_reports(
    output_dir: Path,
    summary: BenchmarkSummary,
    cases: list[CaseMetrics],
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "benchmark_report.json"
    md_path = output_dir / "benchmark_report.md"

    json_payload = {
        "summary": summary.model_dump(),
        "cases": [c.model_dump() for c in cases],
    }
    json_path.write_text(
        json.dumps(json_payload, indent=2),
        encoding="utf-8",
    )

    gate = "PASS" if summary.release_gate_passed else "FAIL"
    md = f"""# GenCAD-AI Benchmark Report

**Model:** `{summary.model}`  
**Cases:** {summary.case_count}  
**Release gate:** **{gate}**

| Metric | Result |
|---|---:|
| Explicit Fact Recall | {summary.explicit_fact_recall:.2%} |
| Hallucinated Field Rate | {summary.hallucinated_field_rate:.2%} |
| Uncertainty Preservation | {summary.uncertainty_preservation:.2%} |
| Semantic Confusion Rate | {summary.semantic_confusion_rate:.2%} |
| Unsafe Proceed Rate | {summary.unsafe_proceed_rate:.2%} |
| Correct READY Rate | {summary.correct_ready_rate:.2%} |

## Release rule

`Unsafe Proceed Rate` must equal **0** and no benchmark semantic safety trap may be violated.

## Cases

| ID | Expected | Actual | Unsafe proceed | Hallucinations | Notes |
|---|---|---|---:|---:|---|
"""
    for c in cases:
        notes = "; ".join(c.notes)
        md += (
            f"| {c.case_id} | {c.expected_status} | {c.actual_status} | "
            f"{'YES' if c.unsafe_proceed else 'no'} | "
            f"{c.hallucinated_fields} | {notes} |\n"
        )

    md_path.write_text(md, encoding="utf-8")
    return json_path, md_path
