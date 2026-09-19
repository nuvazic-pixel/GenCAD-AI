from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from app.cad.generator import export_bracket
from app.cad.manifest import build_generation_manifest, write_generation_manifest
from app.cad.release_gate import evaluate_cad_release
from app.domain.intent import ParsedEngineeringIntent
from app.pipeline.builder import build_engineering_spec
from app.pipeline.evidence_guard import apply_source_evidence_guard
from app.pipeline.validation import validate_spec


OUTPUT_DIR = Path(os.getenv("GENCAD_GEOMETRY_OUTPUT", "reports/geometry_demo_001"))


def _unknown():
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _field(value, *, unit=None, text=None):
    return {
        "raw_value": value,
        "raw_unit": unit,
        "source_text": text,
        "state": "confirmed",
        "confidence": 1.0,
    }


def _intent(pipe_source: str) -> ParsedEngineeringIntent:
    fields = [
        "component",
        "pipe_diameter",
        "nominal_pipe_size",
        "wall_thickness",
        "bracket_width",
        "base_thickness",
        "fastener_designation",
        "fastener_count",
        "associated_fastener_designation",
        "hole_count",
        "hole_diameter",
        "hole_semantics",
        "material",
        "manufacturing_process",
        "load_statement",
    ]
    payload = {name: _unknown() for name in fields}
    payload["qualitative_requirements"] = []
    payload["unmapped_phrases"] = []
    payload.update(
        {
            "component": _field("pipe bracket", text="pipe bracket"),
            # Deliberately emulate the raw model behavior observed in
            # evidence_guard_live_001: the model supplies mm even when
            # source_text does not support it.
            "pipe_diameter": _field(42, unit="mm", text=pipe_source),
            "wall_thickness": _field(4, unit="mm", text="4 mm wall"),
            "bracket_width": _field(30, unit="mm", text="30 mm width"),
            "base_thickness": _field(6, unit="mm", text="6 mm base"),
            "hole_count": _field(2, text="two"),
            "hole_diameter": _field(
                6.6,
                unit="mm",
                text="two 6.6 mm holes",
            ),
            "material": _field("steel", text="steel"),
        }
    )
    return ParsedEngineeringIntent.model_validate(payload)


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


def run_scenario(
    *,
    scenario_id: str,
    prompt: str,
    pipe_source: str,
    allow_geometry: bool,
) -> dict:
    raw = _intent(pipe_source)
    guarded, guard_report = apply_source_evidence_guard(prompt, raw)
    spec = build_engineering_spec(prompt, guarded)
    validation = validate_spec(spec)
    release = evaluate_cad_release(spec, validation)

    scenario_dir = OUTPUT_DIR / scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)

    trace = {
        "scenario_id": scenario_id,
        "prompt": prompt,
        "raw_parsed_intent": raw.model_dump(mode="json"),
        "guarded_parsed_intent": guarded.model_dump(mode="json"),
        "source_evidence_guard": guard_report.model_dump(mode="json"),
        "engineering_spec": spec.model_dump(mode="json"),
        "validation_report": validation.model_dump(mode="json"),
        "cad_release_decision": release.model_dump(mode="json"),
        "geometry_generated": False,
        "artifacts": {},
    }

    if allow_geometry:
        if not release.allowed or release.accepted_parameters is None:
            raise RuntimeError(
                f"{scenario_id} was expected to release geometry but CADReleaseGate failed: "
                f"{release.reason}"
            )

        step_path, stl_path, layout = export_bracket(
            release.accepted_parameters,
            scenario_dir,
            stem="pipe_saddle_bracket",
        )

        manifest = build_generation_manifest(
            spec=spec,
            validation=validation,
            release=release,
            layout=layout,
            step_path=step_path,
            stl_path=stl_path,
            source_run_id="geometry_demo_001",
            git_commit=_git_commit(),
        )
        manifest_path = write_generation_manifest(
            scenario_dir / "generation_manifest.json",
            manifest,
        )

        trace["geometry_generated"] = True
        trace["artifacts"] = {
            "step": str(step_path),
            "stl": str(stl_path),
            "manifest": str(manifest_path),
        }
    else:
        if release.allowed:
            raise RuntimeError(
                f"{scenario_id} was expected to be blocked but CADReleaseGate passed"
            )

    _write_json(scenario_dir / "trace.json", trace)
    return trace


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scenario_a = run_scenario(
        scenario_id="scenario_A_blocked",
        prompt=(
            "Create a steel pipe bracket for Ø42 pipe, "
            "4 mm wall, 30 mm width, 6 mm base, "
            "two 6.6 mm holes."
        ),
        pipe_source="Ø42 pipe",
        allow_geometry=False,
    )

    scenario_b = run_scenario(
        scenario_id="scenario_B_generated",
        prompt=(
            "Create a steel pipe bracket for Ø42 mm pipe, "
            "4 mm wall, 30 mm width, 6 mm base, "
            "two 6.6 mm holes."
        ),
        pipe_source="Ø42 mm pipe",
        allow_geometry=True,
    )

    summary = {
        "demo": "GenCAD-AI v0.3.0 Proof-to-Geometry Bridge",
        "scenario_A": {
            "cad_release": scenario_a["cad_release_decision"]["status"],
            "geometry_generated": scenario_a["geometry_generated"],
            "blocking_fields": scenario_a["cad_release_decision"]["blocking_fields"],
        },
        "scenario_B": {
            "cad_release": scenario_b["cad_release_decision"]["status"],
            "geometry_generated": scenario_b["geometry_generated"],
            "artifacts": scenario_b["artifacts"],
        },
    }
    _write_json(OUTPUT_DIR / "demo_summary.json", summary)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
