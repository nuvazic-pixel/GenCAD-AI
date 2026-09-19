from hashlib import sha256

from app.domain.evidence import EvidenceState
from app.domain.intent import ParsedEngineeringIntent, ParsedField
from app.pipeline.builder import build_engineering_spec
from app.pipeline.evidence_guard import (
    apply_source_evidence_guard,
    relation_supports_hole_association,
    unexpected_association_is_supported,
)
from app.pipeline.terminology import (
    normalize_component_term,
    normalize_material_term,
)
from app.providers.prompt import SYSTEM_PROMPT


PROMPT_V1_HASH = "ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d"


def _unknown():
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


def _field(value, *, unit=None, text=None, state="confirmed", confidence=1.0):
    return {
        "raw_value": value,
        "raw_unit": unit,
        "source_text": text,
        "state": state,
        "confidence": confidence,
    }


def _intent(**overrides):
    fields = [
        "component",
        "pipe_diameter",
        "nominal_pipe_size",
        "wall_thickness",
        "bracket_width",
        "base_thickness",
        "fastener_designation",
        "fastener_count",
        "associated_fastener_designation",
        "hole_count",
        "hole_diameter",
        "hole_semantics",
        "material",
        "manufacturing_process",
        "load_statement",
    ]
    payload = {name: _unknown() for name in fields}
    payload["qualitative_requirements"] = []
    payload["unmapped_phrases"] = []
    payload.update(overrides)
    return ParsedEngineeringIntent.model_validate(payload)


def test_prompt_v1_remains_frozen_in_v026():
    assert sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest() == PROMPT_V1_HASH


def test_source_evidence_guard_strips_unsupported_inferred_unit():
    intent = _intent(
        pipe_diameter=_field(
            42,
            unit="mm",
            text="Ø42 pipe",
        ),
        wall_thickness=_field(
            4,
            unit="mm",
            text="4 mm wall thickness",
        ),
    )

    guarded, report = apply_source_evidence_guard(
        "Create a bracket for a Ø42 pipe with 4 mm wall thickness.",
        intent,
    )

    assert guarded.pipe_diameter.raw_value == 42
    assert guarded.pipe_diameter.raw_unit is None
    assert guarded.wall_thickness.raw_unit == "mm"
    assert report.changed is True
    assert [finding.field for finding in report.findings] == ["pipe_diameter"]


def test_source_evidence_guard_accepts_unit_present_in_field_source_phrase():
    intent = _intent(
        pipe_diameter=_field(
            42,
            unit="mm",
            text="42 mm pipe",
        )
    )

    guarded, report = apply_source_evidence_guard(
        "Create a bracket for a 42 mm pipe.",
        intent,
    )

    assert guarded.pipe_diameter.raw_unit == "mm"
    assert report.findings == []


def test_multilingual_component_aliases():
    assert normalize_component_term("Halter") == "pipe_bracket"
    assert normalize_component_term("Rohrhalter") == "pipe_bracket"
    assert normalize_component_term("Stahl-Rohrhalter") == "pipe_bracket"
    assert normalize_component_term("Pipe clamp bracket") == "pipe_bracket"


def test_multilingual_material_aliases():
    assert normalize_material_term("Stahl") == "steel"
    assert normalize_material_term("Kunststoff") == "polymer"
    assert normalize_material_term("Aluminium") == "aluminium"


def test_explicit_fastener_through_holes_creates_only_deterministic_association():
    prompt = (
        "Mount it with two M6 screws through two 6.6 mm clearance holes."
    )
    intent = _intent(
        fastener_designation=_field("M6", text="M6 screws"),
        fastener_count=_field(2, text="two M6 screws"),
        hole_count=_field(2, text="two 6.6 mm clearance holes"),
        hole_diameter=_field(6.6, unit="mm", text="6.6 mm clearance holes"),
        hole_semantics=_field("clearance", text="clearance holes"),
    )

    spec = build_engineering_spec(prompt, intent)

    assert spec.fastener_designation.state == EvidenceState.CONFIRMED
    assert spec.associated_fastener_designation.value == "M6"
    assert spec.associated_fastener_designation.state == EvidenceState.DERIVED
    assert (
        spec.associated_fastener_designation.provenance.rule_id
        == "ASSEMBLY_ASSOCIATION_V1"
    )


def test_physical_fastener_without_explicit_hole_relation_is_not_associated():
    prompt = "Use two M6 screws to mount the bracket."
    intent = _intent(
        fastener_designation=_field("M6", text="M6 screws"),
        fastener_count=_field(2, text="two M6 screws"),
    )

    spec = build_engineering_spec(prompt, intent)

    assert spec.associated_fastener_designation.state == EvidenceState.UNKNOWN


def test_model_supplied_association_is_supported_only_by_explicit_relation():
    prompt = "Use two M6 screws through two 6.6 mm holes."
    intent = _intent(
        fastener_designation=_field("M6", text="M6 screws"),
        associated_fastener_designation=_field("M6", text="M6 screws"),
        hole_count=_field(2, text="two 6.6 mm holes"),
        hole_diameter=_field(6.6, unit="mm", text="6.6 mm holes"),
    )

    assert relation_supports_hole_association(prompt, "M6") is True
    assert unexpected_association_is_supported(prompt, intent) is True
