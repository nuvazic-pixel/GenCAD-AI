from types import SimpleNamespace
import math

import pytest

from app.cad.artifact_gate import evaluate_cad_artifact_release
from app.cad.generator import derive_layout
from app.cad.models import ReleasedBracketParameters
from app.cad.verification import verify_bracket_stl


def _params():
    return ReleasedBracketParameters(
        pipe_diameter_mm=42.0, wall_thickness_mm=4.0,
        bracket_width_mm=30.0, base_thickness_mm=6.0,
        hole_count=2, hole_diameter_mm=6.6,
    )


class _Loop:
    closed = True

    def __init__(self, points):
        self.points = points

    def discrete(self, vertices):
        return self.points

    def length(self, vertices):
        return sum(math.dist(a, b) for a, b in zip(self.points, self.points[1:]))


def _circle(x, y, radius, *, z=3.0, samples=96):
    points = [
        (x + radius * math.cos(2 * math.pi * i / samples),
         y + radius * math.sin(2 * math.pi * i / samples), z)
        for i in range(samples)
    ]
    return points + points[:1]


class _SectionMesh:
    is_volume = True
    is_watertight = True
    volume = 1000.0
    triangles = [[(0, 0, 0), (1, 0, 0), (0, 1, 0)]]

    def __init__(self, params, layout, *, diameter=None, offset_y=0.0):
        self.params, self.layout = params, layout
        self.diameter = diameter or params.hole_diameter_mm
        self.offset_y = offset_y
        self.extents = [layout.base_length_mm, layout.base_depth_mm,
                        layout.ring_center_z_mm + layout.ring_outer_radius_mm]
        self.bounds = [[-layout.base_length_mm / 2, -layout.base_depth_mm / 2, 0],
                       [layout.base_length_mm / 2, layout.base_depth_mm / 2, self.extents[2]]]

    def section(self, *, plane_origin, plane_normal):
        if plane_normal == [0.0, 1.0, 0.0]:
            return SimpleNamespace(
                entities=[_Loop(_circle(0, 0, self.params.pipe_diameter_mm / 2))],
                vertices=[],
            )
        x, y = self.layout.base_length_mm / 2, self.layout.base_depth_mm / 2
        exterior = [(-x, -y, 3), (x, -y, 3), (x, y, 3), (-x, y, 3), (-x, -y, 3)]
        # Exterior is deliberately not the first entity.
        return SimpleNamespace(entities=[
            _Loop(_circle(self.layout.right_hole_x_mm, self.offset_y, self.diameter / 2)),
            _Loop(exterior),
            _Loop(_circle(self.layout.left_hole_x_mm, self.offset_y, self.diameter / 2)),
        ], vertices=[])


def _section_report(monkeypatch, *, diameter=None, offset_y=0.0):
    import app.cad.verification as verification
    params = _params()
    layout = derive_layout(params)
    mesh = _SectionMesh(params, layout, diameter=diameter, offset_y=offset_y)
    fake_trimesh = SimpleNamespace(
        load_mesh=lambda *args, **kwargs: mesh, Scene=type("Scene", (), {}),
    )
    monkeypatch.setattr(verification, "_require_trimesh", lambda: fake_trimesh)
    return verify_bracket_stl("section-fixture.stl", params, layout)


def test_nominal_mounting_holes_pass_with_shuffled_section_loops(monkeypatch):
    report = _section_report(monkeypatch)
    assert report.passed, report.failed_rules
    assert report.hole_diameters_match
    assert report.hole_positions_match
    assert report.measured_hole_diameters_mm == pytest.approx([6.6, 6.6], abs=0.01)


def test_same_hole_count_with_wrong_diameter_is_quarantined(monkeypatch):
    report = _section_report(monkeypatch, diameter=4.0)
    assert report.hole_count_match
    assert not report.passed
    assert "MOUNTING_HOLE_DIAMETER_MISMATCH" in report.failed_rules
    assert not evaluate_cad_artifact_release(report).releasable


def test_same_hole_count_with_wrong_position_is_quarantined(monkeypatch):
    report = _section_report(monkeypatch, offset_y=1.0)
    assert report.hole_count_match
    assert not report.passed
    assert "MOUNTING_HOLE_POSITION_MISMATCH" in report.failed_rules
    assert not evaluate_cad_artifact_release(report).releasable



def test_non_circular_holes_with_matching_perimeter_are_quarantined(monkeypatch):
    circle = _circle

    def square_hole(x, y, radius, **kwargs):
        if radius != _params().hole_diameter_mm / 2:
            return circle(x, y, radius, **kwargs)
        half_side = math.pi * radius / 4
        return [(x - half_side, y - half_side, 3),
                (x + half_side, y - half_side, 3),
                (x + half_side, y + half_side, 3),
                (x - half_side, y + half_side, 3),
                (x - half_side, y - half_side, 3)]

    monkeypatch.setitem(globals(), "_circle", square_hole)
    report = _section_report(monkeypatch)
    assert report.hole_count_match
    assert report.hole_positions_match
    assert report.measured_hole_diameters_mm == pytest.approx([6.6, 6.6])
    assert "MOUNTING_HOLE_DIAMETER_MISMATCH" in report.failed_rules
    assert not evaluate_cad_artifact_release(report).releasable


@pytest.mark.parametrize("diameter,offset_y,failed_rule", [
    (6.6, 0.0, None),
    (4.0, 0.0, "MOUNTING_HOLE_DIAMETER_MISMATCH"),
    (6.6, 1.0, "MOUNTING_HOLE_POSITION_MISMATCH"),
])
def test_real_stl_mounting_hole_geometry(tmp_path, diameter, offset_y, failed_rule):
    cq = pytest.importorskip("cadquery")
    pytest.importorskip("trimesh")
    params = _params()
    layout = derive_layout(params)
    # Keep the outer solid and hole count unchanged while independently
    # injecting a manufacturing defect at the artifact boundary.
    base = cq.Workplane("XY").box(
        layout.base_length_mm, layout.base_depth_mm, params.base_thickness_mm,
        centered=(True, True, False),
    )
    ring = (cq.Workplane("XZ").circle(layout.ring_outer_radius_mm)
            .circle(layout.ring_inner_radius_mm)
            .extrude(params.bracket_width_mm / 2, both=True)
            .translate((0, 0, layout.ring_center_z_mm)))
    holes = (cq.Workplane("XY")
             .pushPoints([(layout.left_hole_x_mm, offset_y), (layout.right_hole_x_mm, offset_y)])
             .circle(diameter / 2).extrude(params.base_thickness_mm + 2)
             .translate((0, 0, -1)))
    path = tmp_path / "mounting-holes.stl"
    cq.exporters.export(base.union(ring).cut(holes), str(path), tolerance=0.05)
    report = verify_bracket_stl(path, params, layout)
    assert report.hole_count_match
    assert report.dimensions_match
    assert report.pipe_opening_match
    if failed_rule is None:
        assert report.passed, report.failed_rules
    else:
        assert not report.passed
        assert failed_rule in report.failed_rules
        assert not evaluate_cad_artifact_release(report).releasable
