from __future__ import annotations

from app.cad.feature_language import (
    CADFeature,
    CADFeatureProgram,
    FeatureKind,
    FeatureOperation,
    FeatureParameter,
)
from app.cad.generator import (
    GENERATOR_ID,
    LAYOUT_RULE_ID,
    derive_layout,
)
from app.cad.models import CADReleaseDecision
from app.cad.reproducibility import canonical_payload_hash
from app.domain.evidence import EvidenceState


TOPOLOGY_RULE_ID = "PIPE_SADDLE_TOPOLOGY_V1"


def _direct_parameter(
    *,
    value,
    unit: str | None,
    source_field: str,
    evidence_summary: dict,
) -> FeatureParameter:
    evidence = evidence_summary[source_field]
    return FeatureParameter(
        value=value,
        unit=unit,
        state=EvidenceState(evidence["state"]),
        source_fields=[source_field],
        source_ref=evidence["provenance"].get("source_ref"),
        rule_id=evidence["provenance"].get("rule_id"),
        note=evidence["provenance"].get("original_text"),
    )


def _derived_parameter(
    *,
    value,
    unit: str | None,
    source_fields: list[str],
    rule_id: str,
    note: str,
) -> FeatureParameter:
    return FeatureParameter(
        value=value,
        unit=unit,
        state=EvidenceState.DERIVED,
        source_fields=source_fields,
        rule_id=rule_id,
        note=note,
    )


def build_pipe_saddle_feature_program(
    release: CADReleaseDecision,
) -> CADFeatureProgram:
    if not release.allowed or release.accepted_parameters is None:
        raise ValueError(
            "Feature program requires a passed CADReleaseDecision"
        )

    params = release.accepted_parameters
    layout = derive_layout(params)

    direct = release.evidence_summary

    base = CADFeature(
        feature_id="base_plate",
        label="Base plate",
        kind=FeatureKind.BOX,
        operation=FeatureOperation.ADD,
        description="Mounting base generated from released bracket parameters.",
        parameters={
            "length_mm": _derived_parameter(
                value=layout.base_length_mm,
                unit="mm",
                source_fields=[
                    "pipe_diameter",
                    "wall_thickness",
                    "hole_diameter",
                ],
                rule_id=LAYOUT_RULE_ID,
                note="Derived base length from deterministic saddle layout.",
            ),
            "depth_mm": _direct_parameter(
                value=params.bracket_width_mm,
                unit="mm",
                source_field="bracket_width",
                evidence_summary=direct,
            ),
            "height_mm": _direct_parameter(
                value=params.base_thickness_mm,
                unit="mm",
                source_field="base_thickness",
                evidence_summary=direct,
            ),
        },
    )

    ring = CADFeature(
        feature_id="pipe_saddle",
        label="Pipe saddle",
        kind=FeatureKind.ANNULAR_EXTRUDE,
        operation=FeatureOperation.ADD,
        description="Annular saddle feature around the confirmed pipe diameter.",
        parameters={
            "inner_radius_mm": _derived_parameter(
                value=layout.ring_inner_radius_mm,
                unit="mm",
                source_fields=["pipe_diameter"],
                rule_id=LAYOUT_RULE_ID,
                note="Pipe radius = released pipe diameter / 2.",
            ),
            "outer_radius_mm": _derived_parameter(
                value=layout.ring_outer_radius_mm,
                unit="mm",
                source_fields=["pipe_diameter", "wall_thickness"],
                rule_id=LAYOUT_RULE_ID,
                note="Outer radius = inner radius + released wall thickness.",
            ),
            "depth_mm": _direct_parameter(
                value=params.bracket_width_mm,
                unit="mm",
                source_field="bracket_width",
                evidence_summary=direct,
            ),
            "center_z_mm": _derived_parameter(
                value=layout.ring_center_z_mm,
                unit="mm",
                source_fields=["pipe_diameter", "base_thickness"],
                rule_id=LAYOUT_RULE_ID,
                note="Saddle center elevation from deterministic layout.",
            ),
            "axis": _derived_parameter(
                value="y",
                unit=None,
                source_fields=[],
                rule_id=TOPOLOGY_RULE_ID,
                note="pipe_saddle_bracket_v1 topology axis.",
            ),
        },
    )

    hole_features = []
    for feature_id, label, x_value in [
        ("mounting_hole_left", "Left mounting hole", layout.left_hole_x_mm),
        ("mounting_hole_right", "Right mounting hole", layout.right_hole_x_mm),
    ]:
        hole_features.append(
            CADFeature(
                feature_id=feature_id,
                label=label,
                kind=FeatureKind.CYLINDER,
                operation=FeatureOperation.CUT,
                description="Through-hole cut in the mounting base.",
                parameters={
                    "diameter_mm": _direct_parameter(
                        value=params.hole_diameter_mm,
                        unit="mm",
                        source_field="hole_diameter",
                        evidence_summary=direct,
                    ),
                    "depth_mm": _derived_parameter(
                        value=params.base_thickness_mm + 2.0,
                        unit="mm",
                        source_fields=["base_thickness"],
                        rule_id=TOPOLOGY_RULE_ID,
                        note="Cut depth extends 1 mm beyond each base face.",
                    ),
                    "x_mm": _derived_parameter(
                        value=x_value,
                        unit="mm",
                        source_fields=[
                            "pipe_diameter",
                            "wall_thickness",
                            "hole_diameter",
                        ],
                        rule_id=LAYOUT_RULE_ID,
                        note="Mounting-hole X position from deterministic layout.",
                    ),
                    "y_mm": _derived_parameter(
                        value=0.0,
                        unit="mm",
                        source_fields=[],
                        rule_id=TOPOLOGY_RULE_ID,
                        note="Centered on bracket depth.",
                    ),
                    "z_start_mm": _derived_parameter(
                        value=-1.0,
                        unit="mm",
                        source_fields=["base_thickness"],
                        rule_id=TOPOLOGY_RULE_ID,
                        note="Cut begins 1 mm below base for robust through-cut.",
                    ),
                    "axis": _derived_parameter(
                        value="z",
                        unit=None,
                        source_fields=[],
                        rule_id=TOPOLOGY_RULE_ID,
                        note="Mounting-hole topology axis.",
                    ),
                },
            )
        )

    program = CADFeatureProgram(
        program_id="pipe_saddle_bracket_program_v1",
        generator_id=GENERATOR_ID,
        source_parameter_hash=canonical_payload_hash(
            params.model_dump(mode="json")
        ),
        features=[base, ring, *hole_features],
        metadata={
            "topology_rule_id": TOPOLOGY_RULE_ID,
            "layout_rule_id": LAYOUT_RULE_ID,
            "feature_count": 4,
        },
    )
    return program
