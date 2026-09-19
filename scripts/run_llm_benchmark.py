import json
import os
from pathlib import Path
import subprocess

from app.config import LLMConfig
from app.domain.intent import ParsedEngineeringIntent
from app.evaluation.failures import classify_case
from app.evaluation.evidence_guard_challenge import (
    score_evidence_guard_case,
    summarize_evidence_guard_challenge,
)
from app.evaluation.fingerprint import create_fingerprint
from app.evaluation.metrics import score_case, summarize
from app.evaluation.release_gate import evaluate_release_gate
from app.evaluation.report import write_reports
from app.pipeline.builder import build_engineering_spec
from app.pipeline.evidence_guard import apply_source_evidence_guard
from app.pipeline.validation import validate_spec
from app.providers.factory import build_parser
from app.providers.prompt import SYSTEM_PROMPT
from benchmarks import get_benchmark


def _git_commit() -> str | None:
    configured = os.getenv("GENCAD_GIT_COMMIT")
    if configured:
        return configured
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main():
    config = LLMConfig()
    parser = build_parser(config)

    run_id = os.getenv("GENCAD_RUN_ID", "baseline_003")
    prompt_version = os.getenv("GENCAD_PROMPT_VERSION", "v1")
    benchmark_version = os.getenv("GENCAD_BENCHMARK_VERSION", "0.2.4")
    schema_version = os.getenv("GENCAD_SCHEMA_VERSION", "0.2.4")

    benchmark = get_benchmark(benchmark_version)
    output_dir = Path("reports") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    case_metrics = []
    classifications = []
    evidence_guard_case_metrics = []

    for case in benchmark:
        raw_parsed: ParsedEngineeringIntent = parser.parse(case["prompt"])
        parsed, guard_report = apply_source_evidence_guard(
            case["prompt"],
            raw_parsed,
        )
        spec = build_engineering_spec(case["prompt"], parsed)
        report = validate_spec(spec)
        classification = classify_case(
            case=case,
            actual_intent=parsed,
            spec=spec,
            report=report,
        )
        metrics = score_case(
            case=case,
            actual_intent=parsed,
            spec=spec,
            report=report,
        )

        case_metrics.append(metrics)
        classifications.append(classification)

        if "guard_targets" in case:
            evidence_guard_case_metrics.append(
                score_evidence_guard_case(
                    case=case,
                    raw_intent=raw_parsed,
                    guarded_intent=parsed,
                    guard_report=guard_report,
                    spec=spec,
                    actual_status=report.status.value,
                )
            )

        _write_json(
            output_dir / "cases" / f"{case['id']}.json",
            {
                "case_id": case["id"],
                "prompt": case["prompt"],
                "expected_status": case["expected_status"],
                "raw_parsed_intent": raw_parsed.model_dump(mode="json"),
                "parsed_intent": parsed.model_dump(mode="json"),
                "source_evidence_guard": guard_report.model_dump(mode="json"),
                "engineering_spec": spec.model_dump(mode="json"),
                "validation_report": report.model_dump(mode="json"),
                "failures": classification.model_dump(mode="json")["failures"],
                "metrics": metrics.model_dump(mode="json"),
            },
        )

    summary = summarize(config.model, case_metrics)
    gate = evaluate_release_gate(summary, case_metrics, classifications)

    challenge_summary = None
    if evidence_guard_case_metrics:
        challenge_summary = summarize_evidence_guard_challenge(
            evidence_guard_case_metrics
        )

    summary.release_gate_passed = gate.passed

    json_path, md_path = write_reports(
        output_dir,
        summary,
        case_metrics,
    )

    _write_json(
        output_dir / "failures.json",
        [item.model_dump(mode="json") for item in classifications],
    )
    _write_json(
        output_dir / "release_gate.json",
        gate.model_dump(mode="json"),
    )

    if challenge_summary is not None:
        _write_json(
            output_dir / "evidence_guard_cases.json",
            [
                item.model_dump(mode="json")
                for item in evidence_guard_case_metrics
            ],
        )
        _write_json(
            output_dir / "evidence_guard_challenge.json",
            challenge_summary.model_dump(mode="json"),
        )

    fingerprint = create_fingerprint(
        run_id=run_id,
        provider=config.provider,
        model=config.model,
        prompt_version=prompt_version,
        benchmark_version=benchmark_version,
        schema_version=schema_version,
        prompt=SYSTEM_PROMPT,
        benchmark=benchmark,
        schema=ParsedEngineeringIntent.model_json_schema(),
        git_commit=_git_commit(),
    )
    _write_json(
        output_dir / "fingerprint.json",
        fingerprint.model_dump(mode="json"),
    )

    _write_json(
        output_dir / "run_manifest.json",
        {
            "run_id": run_id,
            "run_type": (
                "holdout_evaluation"
                if run_id.startswith("holdout_")
                else "evaluation_calibration"
                if run_id in {"baseline_002", "baseline_003"}
                else "benchmark"
            ),
            "provider": config.provider,
            "model": config.model,
            "prompt_version": prompt_version,
            "benchmark_version": benchmark_version,
            "schema_version": schema_version,
            "case_count": len(benchmark),
            "release_gate_passed": gate.passed,
            "evidence_guard_challenge": (
                challenge_summary.model_dump(mode="json")
                if challenge_summary is not None
                else None
            ),
        },
    )

    print(summary.model_dump_json(indent=2))
    print(gate.model_dump_json(indent=2))
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {output_dir / 'failures.json'}")
    print(f"Wrote {output_dir / 'release_gate.json'}")
    print(f"Wrote {output_dir / 'fingerprint.json'}")
    print(f"Wrote {output_dir / 'run_manifest.json'}")
    if challenge_summary is not None:
        print(challenge_summary.model_dump_json(indent=2))
        print(f"Wrote {output_dir / 'evidence_guard_cases.json'}")
        print(f"Wrote {output_dir / 'evidence_guard_challenge.json'}")
    print(f"Wrote per-case traces under {output_dir / 'cases'}")

    if not gate.passed:
        raise SystemExit(2)
    if challenge_summary is not None and not challenge_summary.safety_passed:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
