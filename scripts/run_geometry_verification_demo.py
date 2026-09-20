from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

from app.cad.artifact_gate import evaluate_cad_artifact_release
from app.cad.generator import derive_layout, export_bracket
from app.cad.models import ReleasedBracketParameters
from app.cad.verification import verify_bracket_stl


OUTPUT_DIR = Path(
    os.getenv("GENCAD_GEOMETRY_VERIFY_OUTPUT", "reports/geometry_verification_001")
)


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


def _build_faulty_missing_right_hole(params: ReleasedBracketParameters):
    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError("CadQuery is required for the fault-injection demo") from exc

    layout = derive_layout(params)

    base = (
        cq.Workplane("XY")
        .box(
            layout.base_length_mm,
            layout.base_depth_mm,
            params.base_thickness_mm,
            centered=(True, True, False),
        )
    )

    ring = (
        cq.Workplane("XZ")
        .circle(layout.ring_outer_radius_mm)
        .circle(layout.ring_inner_radius_mm)
        .extrude(params.bracket_width_mm / 2.0, both=True)
        .translate((0, 0, layout.ring_center_z_mm))
    )

    solid = base.union(ring)

    # Deliberate downstream generator fault:
    # only the left mounting hole is cut although released params require two.
    one_hole = (
        cq.Workplane("XY")
        .pushPoints([(layout.left_hole_x_mm, 0)])
        .circle(params.hole_diameter_mm / 2.0)
        .extrude(params.base_thickness_mm + 2.0)
        .translate((0, 0, -1.0))
    )

    return solid.cut(one_hole)


def _export_faulty_candidate(
    params: ReleasedBracketParameters,
    output_dir: Path,
) -> tuple[Path, Path]:
    import cadquery as cq

    output_dir.mkdir(parents=True, exist_ok=True)
    shape = _build_faulty_missing_right_hole(params)

    step_path = output_dir / "pipe_saddle_bracket_faulty.step"
    stl_path = output_dir / "pipe_saddle_bracket_faulty.stl"

    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(shape, str(stl_path), tolerance=0.05)

    return step_path, stl_path


def _route_artifacts(
    *,
    candidate_step: Path,
    candidate_stl: Path,
    report_path: Path,
    decision_path: Path,
    releasable: bool,
) -> dict:
    bucket = OUTPUT_DIR / ("released" if releasable else "quarantine")
    bucket.mkdir(parents=True, exist_ok=True)

    copied = {}
    for source in [
        candidate_step,
        candidate_stl,
        report_path,
        decision_path,
    ]:
        destination = bucket / source.name
        shutil.copy2(source, destination)
        copied[source.name] = str(destination)

    return copied


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    params = ReleasedBracketParameters(
        pipe_diameter_mm=42.0,
        wall_thickness_mm=4.0,
        bracket_width_mm=30.0,
        base_thickness_mm=6.0,
        hole_count=2,
        hole_diameter_mm=6.6,
    )
    layout = derive_layout(params)

    good_dir = OUTPUT_DIR / "candidate_good"
    good_step, good_stl, _ = export_bracket(
        params,
        good_dir,
        stem="pipe_saddle_bracket_good",
    )

    faulty_dir = OUTPUT_DIR / "candidate_faulty_missing_hole"
    faulty_step, faulty_stl = _export_faulty_candidate(
        params,
        faulty_dir,
    )

    good_report = verify_bracket_stl(good_stl, params, layout)
    faulty_report = verify_bracket_stl(faulty_stl, params, layout)

    good_decision = evaluate_cad_artifact_release(good_report)
    faulty_decision = evaluate_cad_artifact_release(faulty_report)

    good_report_path = _write_json(
        good_dir / "geometry_verification_report.json",
        good_report.model_dump(mode="json"),
    )
    good_decision_path = _write_json(
        good_dir / "cad_artifact_release_decision.json",
        good_decision.model_dump(mode="json"),
    )

    faulty_report_path = _write_json(
        faulty_dir / "geometry_verification_report.json",
        faulty_report.model_dump(mode="json"),
    )
    faulty_decision_path = _write_json(
        faulty_dir / "cad_artifact_release_decision.json",
        faulty_decision.model_dump(mode="json"),
    )

    if not good_decision.releasable:
        raise RuntimeError(
            "Known-good geometry failed CADArtifactReleaseGate: "
            + good_decision.reason
        )

    if faulty_decision.releasable:
        raise RuntimeError(
            "Injected faulty geometry incorrectly passed CADArtifactReleaseGate"
        )

    if "HOLE_COUNT_MISMATCH" not in faulty_report.failed_rules:
        raise RuntimeError(
            "Injected missing-hole fault was not detected as HOLE_COUNT_MISMATCH"
        )

    good_routed = _route_artifacts(
        candidate_step=good_step,
        candidate_stl=good_stl,
        report_path=good_report_path,
        decision_path=good_decision_path,
        releasable=True,
    )
    faulty_routed = _route_artifacts(
        candidate_step=faulty_step,
        candidate_stl=faulty_stl,
        report_path=faulty_report_path,
        decision_path=faulty_decision_path,
        releasable=False,
    )

    summary = {
        "demo": "GenCAD-AI v0.3.1 Geometry Verification",
        "git_commit": _git_commit(),
        "released_parameters": params.model_dump(mode="json"),
        "layout": {
            "base_length_mm": layout.base_length_mm,
            "base_depth_mm": layout.base_depth_mm,
            "ring_inner_radius_mm": layout.ring_inner_radius_mm,
            "ring_outer_radius_mm": layout.ring_outer_radius_mm,
            "ring_center_z_mm": layout.ring_center_z_mm,
            "left_hole_x_mm": layout.left_hole_x_mm,
            "right_hole_x_mm": layout.right_hole_x_mm,
        },
        "good": {
            "verification": good_report.model_dump(mode="json"),
            "artifact_release": good_decision.model_dump(mode="json"),
            "routed_to": "released",
            "artifacts": good_routed,
        },
        "faulty_missing_hole": {
            "verification": faulty_report.model_dump(mode="json"),
            "artifact_release": faulty_decision.model_dump(mode="json"),
            "routed_to": "quarantine",
            "artifacts": faulty_routed,
        },
    }

    _write_json(OUTPUT_DIR / "verification_demo_summary.json", summary)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
