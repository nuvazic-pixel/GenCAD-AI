from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from app.cad.generator import BracketLayout, GENERATOR_ID, LAYOUT_RULE_ID
from app.cad.models import CADReleaseDecision
from app.domain.spec import EngineeringSpec
from app.pipeline.validation import ValidationReport


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_generation_manifest(
    *,
    spec: EngineeringSpec,
    validation: ValidationReport,
    release: CADReleaseDecision,
    layout: BracketLayout,
    step_path: Path,
    stl_path: Path,
    source_run_id: str,
    git_commit: str | None = None,
) -> dict:
    if not release.allowed or release.accepted_parameters is None:
        raise ValueError("A generation manifest can only be built for a passed CAD release")

    spec_payload = spec.model_dump(mode="json")
    release_payload = release.model_dump(mode="json")

    return {
        "generator": "GenCAD-AI",
        "system_version": "0.3.0",
        "generator_id": GENERATOR_ID,
        "layout_rule_id": LAYOUT_RULE_ID,
        "source_run_id": source_run_id,
        "git_commit": git_commit,
        "engineering_spec_hash": _canonical_hash(spec_payload),
        "cad_release_decision_hash": _canonical_hash(release_payload),
        "cad_release_gate": release.status.value,
        "validation_status": validation.status.value,
        "parameters": release.accepted_parameters.model_dump(mode="json"),
        "evidence_summary": release.evidence_summary,
        "derived_layout": {
            "base_length_mm": layout.base_length_mm,
            "base_depth_mm": layout.base_depth_mm,
            "ring_inner_radius_mm": layout.ring_inner_radius_mm,
            "ring_outer_radius_mm": layout.ring_outer_radius_mm,
            "ring_center_z_mm": layout.ring_center_z_mm,
            "left_hole_x_mm": layout.left_hole_x_mm,
            "right_hole_x_mm": layout.right_hole_x_mm,
        },
        "artifacts": {
            "step": {
                "file": step_path.name,
                "sha256": _file_sha256(step_path),
            },
            "stl": {
                "file": stl_path.name,
                "sha256": _file_sha256(stl_path),
            },
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_generation_manifest(
    path: str | Path,
    manifest: dict,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output
