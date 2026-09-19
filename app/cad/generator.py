from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.cad.models import ReleasedBracketParameters


GENERATOR_ID = "pipe_saddle_bracket_v1"
LAYOUT_RULE_ID = "PIPE_SADDLE_LAYOUT_V1"


@dataclass(frozen=True)
class BracketLayout:
    base_length_mm: float
    base_depth_mm: float
    ring_inner_radius_mm: float
    ring_outer_radius_mm: float
    ring_center_z_mm: float
    left_hole_x_mm: float
    right_hole_x_mm: float


def derive_layout(params: ReleasedBracketParameters) -> BracketLayout:
    if not isinstance(params, ReleasedBracketParameters):
        raise TypeError(
            "CAD generator accepts ReleasedBracketParameters only. "
            "Raw parser output and EngineeringSpec are forbidden at this boundary."
        )

    if params.hole_count != 2:
        raise ValueError("pipe_saddle_bracket_v1 supports exactly two mounting holes")

    inner_radius = params.pipe_diameter_mm / 2.0
    outer_radius = inner_radius + params.wall_thickness_mm

    # Deterministic layout rule, not a standard:
    # keep each mounting-hole center one hole diameter outside the ring envelope,
    # and retain another hole diameter from that center to the base edge.
    hole_offset = outer_radius + params.hole_diameter_mm
    base_half_length = hole_offset + params.hole_diameter_mm

    return BracketLayout(
        base_length_mm=2.0 * base_half_length,
        base_depth_mm=params.bracket_width_mm,
        ring_inner_radius_mm=inner_radius,
        ring_outer_radius_mm=outer_radius,
        ring_center_z_mm=params.base_thickness_mm + inner_radius,
        left_hole_x_mm=-hole_offset,
        right_hole_x_mm=hole_offset,
    )


def build_pipe_saddle_bracket(params: ReleasedBracketParameters):
    if not isinstance(params, ReleasedBracketParameters):
        raise TypeError(
            "CAD generator accepts ReleasedBracketParameters only. "
            "Raw parser output and EngineeringSpec are forbidden at this boundary."
        )

    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError(
            "CadQuery is required for geometry generation. "
            "Install the optional CAD dependency."
        ) from exc

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

    holes = (
        cq.Workplane("XY")
        .pushPoints(
            [
                (layout.left_hole_x_mm, 0),
                (layout.right_hole_x_mm, 0),
            ]
        )
        .circle(params.hole_diameter_mm / 2.0)
        .extrude(params.base_thickness_mm + 2.0)
        .translate((0, 0, -1.0))
    )

    return solid.cut(holes)


def export_bracket(
    params: ReleasedBracketParameters,
    output_dir: str | Path,
    *,
    stem: str = "pipe_saddle_bracket",
) -> tuple[Path, Path, BracketLayout]:
    if not isinstance(params, ReleasedBracketParameters):
        raise TypeError(
            "CAD generator accepts ReleasedBracketParameters only. "
            "Raw parser output and EngineeringSpec are forbidden at this boundary."
        )

    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError(
            "CadQuery is required for geometry export. "
            "Install the optional CAD dependency."
        ) from exc

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    shape = build_pipe_saddle_bracket(params)
    layout = derive_layout(params)

    step_path = output / f"{stem}.step"
    stl_path = output / f"{stem}.stl"

    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(shape, str(stl_path), tolerance=0.05)

    return step_path, stl_path, layout
