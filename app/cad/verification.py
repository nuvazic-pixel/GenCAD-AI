from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path

from app.cad.generator import BracketLayout
from app.cad.models import ReleasedBracketParameters
from app.cad.verification_models import GeometryVerificationReport


RULE_SOLID_INVALID = "SOLID_INVALID"
RULE_NOT_WATERTIGHT = "MESH_NOT_WATERTIGHT"
RULE_NON_POSITIVE_VOLUME = "NON_POSITIVE_VOLUME"
RULE_HOLE_COUNT = "HOLE_COUNT_MISMATCH"
RULE_BBOX = "BOUNDING_BOX_MISMATCH"
RULE_PIPE_DIAMETER = "PIPE_OPENING_DIAMETER_MISMATCH"
RULE_WALL = "WALL_THICKNESS_MISMATCH"
RULE_FINGERPRINT = "GEOMETRY_FINGERPRINT_MISSING"


def _require_trimesh():
    try:
        import trimesh
    except ImportError as exc:
        raise RuntimeError(
            "trimesh is required for geometry verification. "
            "Install the optional CAD dependency."
        ) from exc
    return trimesh


def _canonical_mesh_fingerprint(mesh, *, decimals: int = 6) -> str:
    triangle_rows: list[str] = []

    for triangle in mesh.triangles:
        vertices = sorted(
            tuple(round(float(coord), decimals) for coord in vertex)
            for vertex in triangle
        )
        triangle_rows.append(
            ";".join(
                ",".join(f"{coord:.{decimals}f}" for coord in vertex)
                for vertex in vertices
            )
        )

    canonical = "\n".join(sorted(triangle_rows)).encode("utf-8")
    return "sha256:" + sha256(canonical).hexdigest()


def _closed_loop_lengths(path) -> list[float]:
    if path is None:
        return []

    lengths: list[float] = []
    for entity in path.entities:
        if getattr(entity, "closed", False):
            lengths.append(float(entity.length(path.vertices)))
    return lengths


def _detect_mounting_holes(mesh, params: ReleasedBracketParameters) -> int:
    section = mesh.section(
        plane_origin=[0.0, 0.0, params.base_thickness_mm / 2.0],
        plane_normal=[0.0, 0.0, 1.0],
    )
    loops = _closed_loop_lengths(section)

    # For pipe_saddle_bracket_v1 at mid-base, one loop is the exterior
    # perimeter and every additional closed loop is a through-hole.
    return max(0, len(loops) - 1)


def _measure_pipe_opening_diameter(
    mesh,
    params: ReleasedBracketParameters,
) -> float | None:
    section = mesh.section(
        plane_origin=[0.0, 0.0, 0.0],
        plane_normal=[0.0, 1.0, 0.0],
    )
    loops = _closed_loop_lengths(section)
    if not loops:
        return None

    expected_circumference = math.pi * params.pipe_diameter_mm
    best = min(loops, key=lambda length: abs(length - expected_circumference))
    return best / math.pi


def verify_bracket_stl(
    stl_path: str | Path,
    params: ReleasedBracketParameters,
    layout: BracketLayout,
    *,
    bbox_tolerance_mm: float = 0.15,
    pipe_tolerance_mm: float = 0.15,
    wall_tolerance_mm: float = 0.15,
) -> GeometryVerificationReport:
    if not isinstance(params, ReleasedBracketParameters):
        raise TypeError("GeometryVerifier requires ReleasedBracketParameters")
    if not isinstance(layout, BracketLayout):
        raise TypeError("GeometryVerifier requires BracketLayout")

    trimesh = _require_trimesh()
    path = Path(stl_path)
    loaded = trimesh.load_mesh(path, process=True)

    if isinstance(loaded, trimesh.Scene):
        if not loaded.geometry:
            raise ValueError("Geometry artifact contains no mesh geometry")
        mesh = trimesh.util.concatenate(tuple(loaded.geometry.values()))
    else:
        mesh = loaded

    solid_valid = bool(mesh.is_volume)
    watertight = bool(mesh.is_watertight)
    volume = float(mesh.volume)
    positive_volume = volume > 0.0

    measured_bbox = [float(value) for value in mesh.extents]
    expected_bbox = [
        float(layout.base_length_mm),
        float(layout.base_depth_mm),
        float(layout.ring_center_z_mm + layout.ring_outer_radius_mm),
    ]
    bbox_delta = [
        measured - expected
        for measured, expected in zip(measured_bbox, expected_bbox)
    ]
    dimensions_match = all(
        abs(delta) <= bbox_tolerance_mm
        for delta in bbox_delta
    )

    detected_holes = _detect_mounting_holes(mesh, params)
    hole_count_match = detected_holes == params.hole_count

    measured_pipe = _measure_pipe_opening_diameter(mesh, params)
    pipe_delta = (
        None
        if measured_pipe is None
        else measured_pipe - params.pipe_diameter_mm
    )
    pipe_opening_match = (
        pipe_delta is not None
        and abs(pipe_delta) <= pipe_tolerance_mm
    )

    measured_wall = None
    wall_delta = None
    wall_check_passed = False
    if measured_pipe is not None:
        measured_outer_radius = (
            float(mesh.bounds[1][2]) - layout.ring_center_z_mm
        )
        measured_wall = measured_outer_radius - measured_pipe / 2.0
        wall_delta = measured_wall - params.wall_thickness_mm
        wall_check_passed = (
            measured_wall > 0.0
            and abs(wall_delta) <= wall_tolerance_mm
        )

    fingerprint = _canonical_mesh_fingerprint(mesh)
    failed_rules: list[str] = []

    if not solid_valid:
        failed_rules.append(RULE_SOLID_INVALID)
    if not watertight:
        failed_rules.append(RULE_NOT_WATERTIGHT)
    if not positive_volume:
        failed_rules.append(RULE_NON_POSITIVE_VOLUME)
    if not hole_count_match:
        failed_rules.append(RULE_HOLE_COUNT)
    if not dimensions_match:
        failed_rules.append(RULE_BBOX)
    if not pipe_opening_match:
        failed_rules.append(RULE_PIPE_DIAMETER)
    if not wall_check_passed:
        failed_rules.append(RULE_WALL)
    if not fingerprint:
        failed_rules.append(RULE_FINGERPRINT)

    return GeometryVerificationReport(
        artifact_file=path.name,
        solid_valid=solid_valid,
        watertight=watertight,
        positive_volume=positive_volume,
        volume_mm3=volume,
        expected_hole_count=params.hole_count,
        detected_hole_count=detected_holes,
        hole_count_match=hole_count_match,
        expected_bbox_mm=expected_bbox,
        measured_bbox_mm=measured_bbox,
        bbox_delta_mm=bbox_delta,
        dimensions_match=dimensions_match,
        expected_pipe_diameter_mm=params.pipe_diameter_mm,
        measured_pipe_diameter_mm=measured_pipe,
        pipe_diameter_delta_mm=pipe_delta,
        pipe_opening_match=pipe_opening_match,
        expected_wall_mm=params.wall_thickness_mm,
        measured_wall_mm=measured_wall,
        wall_delta_mm=wall_delta,
        wall_check_passed=wall_check_passed,
        geometry_fingerprint=fingerprint,
        failed_rules=failed_rules,
        passed=not failed_rules,
    )
