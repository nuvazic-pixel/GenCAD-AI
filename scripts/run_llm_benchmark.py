import json
import os
from pathlib import Path
import subprocess

from app.config import LLMConfig
from app.domain.intent import ParsedEngineeringIntent
from app.evaluation.failures import classify_case
from app.evaluation.fingerprint import create_fingerprint
from app.evaluation.metrics import score_case, summarize
from app.evaluation.release_gate import evaluate_release_gate
from app.evaluation.report import write_reports
from app.pipeline.builder import build_engineering_spec
from app.pipeline.validation import validate_spec
from app.providers.factory import build_parser
from app.providers.prompt import SYSTEM_PROMPT
from benchmarks import BENCHMARK


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
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main():
    config = LLMConfig()
    parser = build_parser(config)

    run_id = os.getenv("GENCAD_RUN_ID", "baseline_001")
    prompt_version = os.getenv("GENCAD_PROMPT_VERSION", "v1")
    output_dir = Path("reports") / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    case_metrics = []
    classifications = []

    for case in BENCHMARK:
        parsed: ParsedEngineeringIntent = parser.parse(case["prompt"])
        spec = build_engineering_spec(case["prompt"], parsed)
        report = validate_spec(spec)

        case_metrics.append(
            score_case(
                case=case,
                actual_intent=parsed,
                spec=spec,
                report=report,
            )
        )
        classifications.append(
            classify_case(
                case=case,
                actual_intent=parsed,
                spec=spec,
                report=report,
            )
        )

    summary = summarize(config.model, case_metrics)
    gate = evaluate_release_gate(summary, case_metrics, classifications)

    # One authoritative definition of PASS in every generated report.
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

    fingerprint = create_fingerprint(
        run_id=run_id,
        provider=config.provider,
        model=config.model,
        prompt_version=prompt_version,
        benchmark_version="0.2.2",
        schema_version="0.2.1",
        prompt=SYSTEM_PROMPT,
        benchmark=BENCHMARK,
        schema=ParsedEngineeringIntent.model_json_schema(),
        git_commit=_git_commit(),
    )
    _write_json(
        output_dir / "fingerprint.json",
        fingerprint.model_dump(mode="json"),
    )

    print(summary.model_dump_json(indent=2))
    print(gate.model_dump_json(indent=2))
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {output_dir / 'failures.json'}")
    print(f"Wrote {output_dir / 'release_gate.json'}")
    print(f"Wrote {output_dir / 'fingerprint.json'}")

    if not gate.passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
