from __future__ import annotations

from dataclasses import dataclass
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
RULE_HOLE_DIAMETER = "MOUNTING_HOLE_DIAMETER_MISMATCH"
RULE_HOLE_POSITION = "MOUNTING_HOLE_POSITION_MISMATCH"
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


def canonical_triangle_fingerprint(
    triangles,
    *,
    decimals: int = 6,
) -> str:
    triangle_rows: list[str] = []

    for triangle in triangles:
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


def _canonical_mesh_fingerprint(mesh, *, decimals: int = 6) -> str:
    return canonical_triangle_fingerprint(
        mesh.triangles,
        decimals=decimals,
    )


def canonical_stl_fingerprint(
    stl_path: str | Path,
    *,
    decimals: int = 6,
) -> str:
    trimesh = _require_trimesh()
    loaded = trimesh.load_mesh(Path(stl_path), process=True)

    if isinstance(loaded, trimesh.Scene):
        if not loaded.geometry:
            raise ValueError("Geometry artifact contains no mesh geometry")
        mesh = trimesh.util.concatenate(tuple(loaded.geometry.values()))
    else:
        mesh = loaded

    return _canonical_mesh_fingerprint(
        mesh,
        decimals=decimals,
    )


def _closed_loop_lengths(path) -> list[float]:
    if path is None:
        return []

    lengths: list[float] = []
    for entity in path.entities:
        if getattr(entity, "closed", False):
            lengths.append(float(entity.length(path.vertices)))
    return lengths


@dataclass(frozen=True)
class _MountingHole:
    area_mm2: float
    center_mm: tuple[float, float] | None
    diameter_mm: float | None
    radial_deviation_mm: float | None


def _measure_planar_loop(points) -> _MountingHole:
    """Measure a polygonal XY boundary without trusting generator metadata.

    The area centroid is unchanged by collinear subdivision of STL section
    edges. Perimeter gives the circular diameter, while vertex and edge-midpoint
    radial residuals reject non-circular boundaries with the same perimeter.
    """
    xy = [(float(point[0]), float(point[1])) for point in points]
    if len(xy) > 1 and math.dist(xy[0], xy[-1]) <= 1e-9:
        xy.pop()
    if len(xy) < 3 or not all(math.isfinite(c) for point in xy for c in point):
        return _MountingHole(0.0, None, None, None)

    edges = list(zip(xy, xy[1:] + xy[:1]))
    crosses = [a[0] * b[1] - b[0] * a[1] for a, b in edges]
    twice_area = math.fsum(crosses)
    if abs(twice_area) <= 1e-9:
        return _MountingHole(0.0, None, None, None)

    center = tuple(
        math.fsum((a[axis] + b[axis]) * cross
                  for (a, b), cross in zip(edges, crosses)) / (3.0 * twice_area)
        for axis in (0, 1)
    )
    perimeter = math.fsum(math.dist(a, b) for a, b in edges)
    radius = perimeter / (2.0 * math.pi)
    samples = xy + [((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                    for a, b in edges]
    radial_deviation = max(abs(math.dist(point, center) - radius) for point in samples)
    return _MountingHole(abs(twice_area) / 2.0, center, radius * 2.0, radial_deviation)


def _measure_mounting_holes(mesh, params: ReleasedBracketParameters) -> list[_MountingHole]:
    section = mesh.section(
        plane_origin=[0.0, 0.0, params.base_thickness_mm / 2.0],
        plane_normal=[0.0, 0.0, 1.0],
    )
    if section is None:
        return []
    loops = [
        _measure_planar_loop(entity.discrete(section.vertices))
        for entity in section.entities if getattr(entity, "closed", False)
    ]
    if not loops:
        return []

    # At mid-base, the supported bracket has one exterior and two through-holes.
    # Identify the exterior geometrically, independent of entity winding/order.
    exterior = max(range(len(loops)), key=lambda index: loops[index].area_mm2)
    holes = [loop for index, loop in enumerate(loops) if index != exterior]
    return sorted(holes, key=lambda hole: hole.center_mm or (math.inf, math.inf))


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
    hole_tolerance_mm: float = 0.15,
    hole_position_tolerance_mm: float = 0.15,
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

    mounting_holes = _measure_mounting_holes(mesh, params)
    detected_holes = len(mounting_holes)
    hole_count_match = detected_holes == params.hole_count
    hole_diameters_match = hole_count_match and all(
        hole.diameter_mm is not None
        and abs(hole.diameter_mm - params.hole_diameter_mm) <= hole_tolerance_mm
        and hole.radial_deviation_mm is not None
        and hole.radial_deviation_mm <= hole_tolerance_mm / 2.0
        for hole in mounting_holes
    )
    expected_centers = sorted([
        (layout.left_hole_x_mm, 0.0),
        (layout.right_hole_x_mm, 0.0),
    ])
    hole_positions_match = (
        detected_holes == len(expected_centers)
        and all(
            hole.center_mm is not None
            and math.dist(hole.center_mm, expected) <= hole_position_tolerance_mm
            for hole, expected in zip(mounting_holes, expected_centers)
        )
    )

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
    if not hole_diameters_match:
        failed_rules.append(RULE_HOLE_DIAMETER)
    if not hole_positions_match:
        failed_rules.append(RULE_HOLE_POSITION)
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
        expected_hole_diameter_mm=params.hole_diameter_mm,
        measured_hole_diameters_mm=[hole.diameter_mm for hole in mounting_holes],
        hole_diameters_match=hole_diameters_match,
        expected_hole_centers_mm=[list(center) for center in expected_centers],
        measured_hole_centers_mm=[
            None if hole.center_mm is None else list(hole.center_mm)
            for hole in mounting_holes
        ],
        hole_positions_match=hole_positions_match,
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
