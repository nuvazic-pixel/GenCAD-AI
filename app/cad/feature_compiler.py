from __future__ import annotations

from pathlib import Path

from app.cad.feature_language import (
    FeatureKind,
    FeatureOperation,
    VerifiedCADFeatureProgram,
)


def _value(feature, name: str):
    return feature.parameters[name].value


def compile_feature_program(
    program: VerifiedCADFeatureProgram,
):
    if not isinstance(program, VerifiedCADFeatureProgram):
        raise TypeError(
            "CAD feature compiler accepts VerifiedCADFeatureProgram only"
        )

    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError(
            "CadQuery is required to compile verified CAD features"
        ) from exc

    solid = None

    for feature in program.features:
        if feature.kind == FeatureKind.BOX:
            shape = (
                cq.Workplane("XY")
                .box(
                    float(_value(feature, "length_mm")),
                    float(_value(feature, "depth_mm")),
                    float(_value(feature, "height_mm")),
                    centered=(True, True, False),
                )
            )

        elif feature.kind == FeatureKind.ANNULAR_EXTRUDE:
            if _value(feature, "axis") != "y":
                raise ValueError("annular_extrude currently supports axis='y'")
            shape = (
                cq.Workplane("XZ")
                .circle(float(_value(feature, "outer_radius_mm")))
                .circle(float(_value(feature, "inner_radius_mm")))
                .extrude(
                    float(_value(feature, "depth_mm")) / 2.0,
                    both=True,
                )
                .translate(
                    (0, 0, float(_value(feature, "center_z_mm")))
                )
            )

        elif feature.kind == FeatureKind.CYLINDER:
            if _value(feature, "axis") != "z":
                raise ValueError("cylinder currently supports axis='z'")
            shape = (
                cq.Workplane("XY")
                .center(
                    float(_value(feature, "x_mm")),
                    float(_value(feature, "y_mm")),
                )
                .circle(float(_value(feature, "diameter_mm")) / 2.0)
                .extrude(float(_value(feature, "depth_mm")))
                .translate(
                    (0, 0, float(_value(feature, "z_start_mm")))
                )
            )

        else:
            raise ValueError(f"Unsupported feature kind: {feature.kind}")

        if solid is None:
            if feature.operation != FeatureOperation.ADD:
                raise ValueError("First feature must be an ADD operation")
            solid = shape
            continue

        if feature.operation == FeatureOperation.ADD:
            solid = solid.union(shape)
        elif feature.operation == FeatureOperation.CUT:
            solid = solid.cut(shape)
        else:
            raise ValueError(
                f"Unsupported feature operation: {feature.operation}"
            )

    if solid is None:
        raise ValueError("VerifiedCADFeatureProgram contains no features")

    return solid


def export_verified_feature_program(
    program: VerifiedCADFeatureProgram,
    output_dir: str | Path,
    *,
    stem: str = "verified_feature_program",
) -> tuple[Path, Path]:
    if not isinstance(program, VerifiedCADFeatureProgram):
        raise TypeError(
            "CAD feature exporter accepts VerifiedCADFeatureProgram only"
        )

    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError(
            "CadQuery is required to export verified CAD features"
        ) from exc

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    shape = compile_feature_program(program)
    step_path = output / f"{stem}.step"
    stl_path = output / f"{stem}.stl"

    cq.exporters.export(shape, str(step_path))
    cq.exporters.export(shape, str(stl_path), tolerance=0.05)
    return step_path, stl_path
