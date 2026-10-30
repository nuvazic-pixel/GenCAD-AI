# Mounting-hole artifact verification

The STL verifier now checks mounting-hole geometry at the base mid-plane for
`pipe_saddle_bracket_v1`, in addition to the existing count, bounding-box,
pipe-opening, wall and volume checks.

For each closed section boundary, it measures polygon area, area centroid and
perimeter independently from the CAD feature metadata. The largest-area boundary
is the exterior; the remaining boundaries are mounting holes. Winding and entity
order do not identify a hole.

Each hole must:
- have a circular diameter within `hole_tolerance_mm` (default 0.15 mm);
- have vertex and edge-midpoint radial residuals within half that diameter tolerance;
- have its centroid within `hole_position_tolerance_mm` (default 0.15 mm)
  of its authorized layout center.

The report records expected and measured diameters and centers, with separate
`MOUNTING_HOLE_DIAMETER_MISMATCH` and `MOUNTING_HOLE_POSITION_MISMATCH` rules.
Historical reports lacking these new checks retain `None` for their results.

Regression tests keep the outer dimensions and hole count unchanged while
injecting a smaller hole diameter or shifted hole centers. The dedicated geometry
CI job installs CAD extras and verifies actual exported STL artifacts as well as
section fixtures. Run it locally with:

```bash
pip install -e ".[cad]" pytest
python -m pytest -q tests/test_mounting_hole_verification.py
```

This check covers one planar section of the supported bracket family. It does
not certify full-depth bore geometry, manufacturing tolerances, mechanical
strength, or general CAD models.
