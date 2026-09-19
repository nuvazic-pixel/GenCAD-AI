from app.domain.evidence import EvidenceState, EngineeringValue, Provenance
from app.domain.intent import ParsedEngineeringIntent, ParsedField
from app.domain.spec import ComponentType, EngineeringSpec, LengthValue, MaterialFamily
from app.pipeline.normalizer import normalize_integer, normalize_length, normalize_number, normalize_unit
from app.pipeline.terminology import (
    normalize_component_term,
    normalize_hole_semantics,
    normalize_material_term,
)


def _unknown():
    return EngineeringValue(
        value=None,
        state=EvidenceState.UNKNOWN,
        confidence=0.0,
        provenance=Provenance(source_type="unknown"),
    )


def _state(field: ParsedField):
    if field.state == "confirmed":
        return EvidenceState.CONFIRMED
    if field.state == "hypothesis":
        return EvidenceState.HYPOTHESIS
    return EvidenceState.UNKNOWN


def _prov(field: ParsedField):
    if field.state == "hypothesis":
        return Provenance(
            source_type="model_hypothesis",
            original_text=field.source_text,
        )
    if field.state == "confirmed":
        return Provenance(
            source_type="user_prompt",
            original_text=field.source_text,
        )
    return Provenance(source_type="unknown")


def _length(field: ParsedField):
    normalized = normalize_length(field)
    if normalized is None:
        return _unknown()

    value_mm, _ = normalized
    source_value = normalize_number(field.raw_value)
    source_unit = normalize_unit(field.raw_unit)
    return EngineeringValue(
        value=LengthValue(
            value_mm=value_mm,
            source_value=source_value,
            source_unit=source_unit,
        ),
        state=_state(field),
        confidence=field.confidence,
        provenance=_prov(field),
    )


def _string(field: ParsedField):
    if field.state == "unknown" or field.raw_value is None:
        return _unknown()
    return EngineeringValue(
        value=str(field.raw_value),
        state=_state(field),
        confidence=field.confidence,
        provenance=_prov(field),
    )


def _statement(field: ParsedField):
    if field.state == "unknown" or field.raw_value is None:
        return _unknown()

    value = str(field.raw_value)
    unit = normalize_unit(field.raw_unit)
    if unit:
        number = normalize_number(field.raw_value)
        if number is not None:
            value = f"{int(number) if number.is_integer() else number} {unit}"

    return EngineeringValue(
        value=value,
        state=_state(field),
        confidence=field.confidence,
        provenance=_prov(field),
    )


def _integer(field: ParsedField):
    if field.state == "unknown":
        return _unknown()
    value = normalize_integer(field.raw_value)
    if value is None:
        return _unknown()
    return EngineeringValue(
        value=value,
        state=_state(field),
        confidence=field.confidence,
        provenance=_prov(field),
    )


def _component(field: ParsedField):
    if field.state == "unknown" or field.raw_value is None:
        return _unknown()
    key = normalize_component_term(field.raw_value)
    mapping = {"pipe_bracket": ComponentType.PIPE_BRACKET}
    value = mapping.get(key)
    if value is None:
        return _unknown()
    return EngineeringValue(
        value=value,
        state=_state(field),
        confidence=field.confidence,
        provenance=_prov(field),
    )


def _material(field: ParsedField):
    if field.state == "unknown" or field.raw_value is None:
        return _unknown()
    key = normalize_material_term(field.raw_value)
    mapping = {
        "steel": MaterialFamily.STEEL,
        "aluminium": MaterialFamily.ALUMINIUM,
        "polymer": MaterialFamily.POLYMER,
    }
    value = mapping.get(key)
    if value is None:
        return _unknown()
    return EngineeringValue(
        value=value,
        state=_state(field),
        confidence=field.confidence,
        provenance=_prov(field),
    )


def _hole_semantics(field: ParsedField):
    if field.state == "unknown" or field.raw_value is None:
        return _unknown()
    return EngineeringValue(
        value=normalize_hole_semantics(field.raw_value),
        state=_state(field),
        confidence=field.confidence,
        provenance=_prov(field),
    )


def build_engineering_spec(
    prompt: str,
    intent: ParsedEngineeringIntent,
) -> EngineeringSpec:
    spec = EngineeringSpec(
        component=_component(intent.component),
        pipe_diameter=_length(intent.pipe_diameter),
        nominal_pipe_size=_string(intent.nominal_pipe_size),
        wall_thickness=_length(intent.wall_thickness),
        bracket_width=_length(intent.bracket_width),
        base_thickness=_length(intent.base_thickness),
        fastener_designation=_string(intent.fastener_designation),
        fastener_count=_integer(intent.fastener_count),
        hole_count=_integer(intent.hole_count),
        clearance_hole_diameter=_length(intent.hole_diameter),
        hole_semantics=_hole_semantics(intent.hole_semantics),
        material=_material(intent.material),
        manufacturing_process=_string(intent.manufacturing_process),
        load_statement=_statement(intent.load_statement),
        source_prompt=prompt,
    )

    required = {
        "component": spec.component,
        "pipe_diameter": spec.pipe_diameter,
        "wall_thickness": spec.wall_thickness,
        "bracket_width": spec.bracket_width,
        "base_thickness": spec.base_thickness,
        "fastener_designation": spec.fastener_designation,
        "hole_count": spec.hole_count,
        "material": spec.material,
    }
    for path, value in required.items():
        if value.state in {EvidenceState.UNKNOWN, EvidenceState.HYPOTHESIS}:
            spec.unresolved_questions.append(f"Clarify {path}")

    length_fields = {
        "pipe_diameter": intent.pipe_diameter,
        "wall_thickness": intent.wall_thickness,
        "bracket_width": intent.bracket_width,
        "base_thickness": intent.base_thickness,
        "hole_diameter": intent.hole_diameter,
    }
    for name, field in length_fields.items():
        if field.state != "unknown" and field.raw_value is not None and field.raw_unit is None:
            spec.warnings.append(
                f"{name} has an explicit value but no explicit unit; no unit was assumed."
            )

    if (
        spec.nominal_pipe_size.state != EvidenceState.UNKNOWN
        and spec.pipe_diameter.state == EvidenceState.UNKNOWN
    ):
        spec.warnings.append(
            "Nominal pipe size detected; physical diameter must not be inferred without a resolver."
        )

    for requirement in intent.qualitative_requirements:
        spec.warnings.append(
            f"Qualitative requirement preserved without engineering derivation: {requirement.text}"
        )

    for phrase in intent.unmapped_phrases:
        spec.warnings.append(
            f"Unmapped phrase preserved for review: {phrase}"
        )

    return spec
