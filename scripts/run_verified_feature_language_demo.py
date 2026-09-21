from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from app.cad.artifact_gate import evaluate_cad_artifact_release
from app.cad.evidence_viewer import write_evidence_viewer
from app.cad.feature_builder import build_pipe_saddle_feature_program
from app.cad.feature_compiler import export_verified_feature_program
from app.cad.feature_gate import verify_feature_program
from app.cad.feature_language import CADFeatureProgram
from app.cad.generator import derive_layout
from app.cad.release_gate import evaluate_cad_release
from app.cad.reproducibility import canonical_payload_hash
from app.cad.verification import verify_bracket_stl
from app.domain.intent import ParsedEngineeringIntent
from app.pipeline.builder import build_engineering_spec
from app.pipeline.evidence_guard import apply_source_evidence_guard
from app.pipeline.validation import validate_spec


OUTPUT_DIR = Path(
    os.getenv("GENCAD_FEATURE_OUTPUT", "reports/verified_feature_language_001")
)


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


def _intent() -> ParsedEngineeringIntent:
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
            "pipe_diameter": _field(42, unit="mm", text="Ø42 mm pipe"),
            "wall_thickness": _field(4, unit="mm", text="4 mm wall"),
            "bracket_width": _field(30, unit="mm", text="30 mm width"),
            "base_thickness": _field(6, unit="mm", text="6 mm base"),
            "hole_count": _field(2, text="two holes"),
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


def _write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prompt = (
        "Create a steel pipe bracket for Ø42 mm pipe, "
        "4 mm wall, 30 mm width, 6 mm base, "
        "two 6.6 mm holes."
    )

    raw = _intent()
    guarded, evidence_guard = apply_source_evidence_guard(prompt, raw)
    spec = build_engineering_spec(prompt, guarded)
    validation = validate_spec(spec)
    cad_release = evaluate_cad_release(spec, validation)

    if not cad_release.allowed or cad_release.accepted_parameters is None:
        raise RuntimeError("Fixture did not pass CADReleaseGate")

    proposal = build_pipe_saddle_feature_program(cad_release)
    feature_report, verified = verify_feature_program(proposal)

    if not feature_report.passed or verified is None:
        raise RuntimeError("Released feature proposal did not pass FeatureProgramGate")

    released_dir = OUTPUT_DIR / "released"
    step_path, stl_path = export_verified_feature_program(
        verified,
        released_dir,
        stem="pipe_saddle_feature_program",
    )

    layout = derive_layout(cad_release.accepted_parameters)
    geometry_report = verify_bracket_stl(
        stl_path,
        cad_release.accepted_parameters,
        layout,
    )
    artifact_release = evaluate_cad_artifact_release(geometry_report)

    if not artifact_release.releasable:
        raise RuntimeError(
            "Feature-program geometry failed artifact verification: "
            + artifact_release.reason
        )

    proposal_path = _write_json(
        released_dir / "feature_program.json",
        proposal.model_dump(mode="json"),
    )
    verified_path = _write_json(
        released_dir / "verified_feature_program.json",
        verified.model_dump(mode="json"),
    )
    feature_report_path = _write_json(
        released_dir / "feature_program_verification.json",
        feature_report.model_dump(mode="json"),
    )
    geometry_report_path = _write_json(
        released_dir / "geometry_verification.json",
        geometry_report.model_dump(mode="json"),
    )
    artifact_release_path = _write_json(
        released_dir / "cad_artifact_release.json",
        artifact_release.model_dump(mode="json"),
    )

    viewer_path = write_evidence_viewer(
        program=proposal,
        stl_path=stl_path,
        verification=feature_report,
        output_path=released_dir / "viewer.html",
        title="GenCAD-AI · Released Evidence View",
    )

    blocked_payload = proposal.model_dump(mode="python")
    right_hole = next(
        feature
        for feature in blocked_payload["features"]
        if feature["feature_id"] == "mounting_hole_right"
    )
    right_hole["parameters"]["diameter_mm"] = {
        "value": None,
        "unit": "mm",
        "state": "unknown",
        "source_fields": ["hole_diameter"],
        "rule_id": None,
        "source_ref": None,
        "note": "Dimension intentionally removed for blocked-proposal demo.",
    }

    blocked_program = CADFeatureProgram.model_validate(blocked_payload)
    blocked_report, blocked_verified = verify_feature_program(blocked_program)

    if blocked_report.passed or blocked_verified is not None:
        raise RuntimeError("UNKNOWN feature parameter incorrectly passed feature gate")

    blocked_dir = OUTPUT_DIR / "blocked_proposal"
    blocked_program_path = _write_json(
        blocked_dir / "feature_program.json",
        blocked_program.model_dump(mode="json"),
    )
    blocked_report_path = _write_json(
        blocked_dir / "feature_program_verification.json",
        blocked_report.model_dump(mode="json"),
    )
    blocked_viewer_path = write_evidence_viewer(
        program=blocked_program,
        stl_path=stl_path,
        verification=blocked_report,
        output_path=blocked_dir / "viewer.html",
        title="GenCAD-AI · BLOCKED Proposal · Reference Geometry",
    )

    summary = {
        "demo": "GenCAD-AI v0.4.0 Verified CAD Feature Language",
        "git_commit": _git_commit(),
        "prompt": prompt,
        "trust_chain": [
            "SourceEvidenceGuard",
            "EngineeringSpec",
            "CADReleaseGate",
            "CADFeatureProgram",
            "FeatureProgramGate",
            "VerifiedCADFeatureProgram",
            "CadQuery compiler",
            "GeometryVerifier",
            "CADArtifactReleaseGate",
        ],
        "released": {
            "program_hash": canonical_payload_hash(
                verified.model_dump(mode="json")
            ),
            "feature_count": len(verified.features),
            "feature_ids": [f.feature_id for f in verified.features],
            "feature_gate": feature_report.model_dump(mode="json"),
            "geometry_fingerprint": geometry_report.geometry_fingerprint,
            "geometry_verified": geometry_report.passed,
            "artifact_releasable": artifact_release.releasable,
            "artifacts": {
                "step": str(step_path),
                "stl": str(stl_path),
                "feature_program": str(proposal_path),
                "verified_feature_program": str(verified_path),
                "feature_verification": str(feature_report_path),
                "geometry_verification": str(geometry_report_path),
                "artifact_release": str(artifact_release_path),
                "viewer": str(viewer_path),
            },
        },
        "blocked_proposal": {
            "feature_gate": blocked_report.model_dump(mode="json"),
            "geometry_compilation_allowed": False,
            "artifacts": {
                "feature_program": str(blocked_program_path),
                "feature_verification": str(blocked_report_path),
                "viewer": str(blocked_viewer_path),
            },
        },
    }

    _write_json(OUTPUT_DIR / "feature_language_demo_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
