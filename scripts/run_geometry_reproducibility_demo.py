from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

from app.cad.artifact_gate import evaluate_cad_artifact_release
from app.cad.generator import GENERATOR_ID, derive_layout, export_bracket
from app.cad.models import ReleasedBracketParameters
from app.cad.reproducibility import (
    canonical_payload_hash,
    evaluate_geometry_reproducibility,
)
from app.cad.reproducibility_models import GeometryBuildRecord
from app.cad.verification import verify_bracket_stl


OUTPUT_DIR = Path(
    os.getenv(
        "GENCAD_REPRO_OUTPUT",
        "reports/geometry_reproducibility_001",
    )
)
REPEAT_COUNT = int(os.getenv("GENCAD_REPRO_REPEAT_COUNT", "5"))


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


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _layout_payload(layout) -> dict:
    return {
        "base_length_mm": layout.base_length_mm,
        "base_depth_mm": layout.base_depth_mm,
        "ring_inner_radius_mm": layout.ring_inner_radius_mm,
        "ring_outer_radius_mm": layout.ring_outer_radius_mm,
        "ring_center_z_mm": layout.ring_center_z_mm,
        "left_hole_x_mm": layout.left_hole_x_mm,
        "right_hole_x_mm": layout.right_hole_x_mm,
    }


def _build_once(
    *,
    build_id: str,
    params: ReleasedBracketParameters,
    root: Path,
) -> tuple[GeometryBuildRecord, dict]:
    build_dir = root / build_id
    step_path, stl_path, layout = export_bracket(
        params,
        build_dir,
        stem="pipe_saddle_bracket",
    )

    verification = verify_bracket_stl(
        stl_path,
        params,
        layout,
    )
    release = evaluate_cad_artifact_release(verification)

    if not verification.geometry_fingerprint:
        raise RuntimeError(f"{build_id}: missing geometry fingerprint")

    record = GeometryBuildRecord(
        build_id=build_id,
        geometry_fingerprint=verification.geometry_fingerprint,
        stl_sha256=_file_sha256(stl_path),
        step_sha256=_file_sha256(step_path),
        verification_passed=verification.passed,
        artifact_releasable=release.releasable,
        volume_mm3=verification.volume_mm3,
        bbox_mm=verification.measured_bbox_mm,
    )

    trace = {
        "build_id": build_id,
        "parameters": params.model_dump(mode="json"),
        "layout": _layout_payload(layout),
        "verification": verification.model_dump(mode="json"),
        "artifact_release": release.model_dump(mode="json"),
        "file_hashes": {
            "step": record.step_sha256,
            "stl": record.stl_sha256,
        },
    }
    _write_json(build_dir / "build_trace.json", trace)

    return record, trace


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

    builds: list[GeometryBuildRecord] = []
    for index in range(1, REPEAT_COUNT + 1):
        record, _ = _build_once(
            build_id=f"build_{index:02d}",
            params=params,
            root=OUTPUT_DIR / "replicas",
        )
        builds.append(record)

    sensitivity_params = params.model_copy(
        update={"hole_diameter_mm": 7.0}
    )
    sensitivity_record, sensitivity_trace = _build_once(
        build_id="sensitivity_hole_diameter_7mm",
        params=sensitivity_params,
        root=OUTPUT_DIR,
    )

    report = evaluate_geometry_reproducibility(
        generator_id=GENERATOR_ID,
        repeat_count=REPEAT_COUNT,
        released_parameters_hash=canonical_payload_hash(
            params.model_dump(mode="json")
        ),
        layout_hash=canonical_payload_hash(_layout_payload(layout)),
        builds=builds,
        sensitivity_control_fingerprint=(
            sensitivity_record.geometry_fingerprint
        ),
    )

    _write_json(
        OUTPUT_DIR / "geometry_reproducibility_report.json",
        report.model_dump(mode="json"),
    )

    summary = {
        "demo": "GenCAD-AI v0.3.2 Deterministic Geometry Reproducibility",
        "git_commit": _git_commit(),
        "repeat_count": REPEAT_COUNT,
        "released_parameters": params.model_dump(mode="json"),
        "layout": _layout_payload(layout),
        "reproducibility": report.model_dump(mode="json"),
        "sensitivity_control": sensitivity_trace,
        "interpretation": {
            "geometry_fingerprint_is_release_metric": True,
            "byte_identical_step_required": False,
            "byte_identical_stl_required": False,
        },
    }
    _write_json(
        OUTPUT_DIR / "reproducibility_demo_summary.json",
        summary,
    )

    if not report.passed:
        raise RuntimeError(
            "Geometry reproducibility failed: "
            + ", ".join(report.failed_rules)
        )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
