from app.domain.evidence import EvidenceState,EngineeringValue,Provenance
from app.domain.intent import ParsedEngineeringIntent,ParsedField
from app.domain.spec import ComponentType,EngineeringSpec,LengthValue,MaterialFamily
UNIT_TO_MM={"mm":1.0,"cm":10.0,"m":1000.0}
def _unknown():
    return EngineeringValue(value=None,state=EvidenceState.UNKNOWN,confidence=0.0,provenance=Provenance(source_type="unknown"))
def _state(f):
    return EvidenceState.CONFIRMED if f.state=="confirmed" else EvidenceState.HYPOTHESIS if f.state=="hypothesis" else EvidenceState.UNKNOWN
def _prov(f):
    if f.state=="hypothesis": return Provenance(source_type="model_hypothesis",original_text=f.source_text)
    if f.state=="confirmed": return Provenance(source_type="user_prompt",original_text=f.source_text)
    return Provenance(source_type="unknown")
def _length(f:ParsedField):
    if f.state=="unknown" or f.raw_value is None or not isinstance(f.raw_value,(int,float)): return _unknown()
    unit=(f.raw_unit or "mm").lower(); factor=UNIT_TO_MM.get(unit)
    if factor is None: return _unknown()
    return EngineeringValue(value=LengthValue(value_mm=float(f.raw_value)*factor,source_value=float(f.raw_value),source_unit=unit),state=_state(f),confidence=f.confidence,provenance=_prov(f))
def _string(f):
    if f.state=="unknown" or f.raw_value is None: return _unknown()
    return EngineeringValue(value=str(f.raw_value),state=_state(f),confidence=f.confidence,provenance=_prov(f))
def _integer(f):
    if f.state=="unknown" or f.raw_value is None or not isinstance(f.raw_value,(int,float)): return _unknown()
    return EngineeringValue(value=int(f.raw_value),state=_state(f),confidence=f.confidence,provenance=_prov(f))
def _component(f):
    if f.state=="unknown" or f.raw_value is None: return _unknown()
    m={"bracket":ComponentType.PIPE_BRACKET,"pipe_bracket":ComponentType.PIPE_BRACKET,"wall bracket":ComponentType.PIPE_BRACKET}
    v=m.get(str(f.raw_value).lower().strip())
    if v is None: return _unknown()
    return EngineeringValue(value=v,state=_state(f),confidence=f.confidence,provenance=_prov(f))
def _material(f):
    if f.state=="unknown" or f.raw_value is None: return _unknown()
    m={"steel":MaterialFamily.STEEL,"aluminium":MaterialFamily.ALUMINIUM,"aluminum":MaterialFamily.ALUMINIUM,"polymer":MaterialFamily.POLYMER}
    v=m.get(str(f.raw_value).lower().strip())
    if v is None: return _unknown()
    return EngineeringValue(value=v,state=_state(f),confidence=f.confidence,provenance=_prov(f))
def build_engineering_spec(prompt:str,intent:ParsedEngineeringIntent)->EngineeringSpec:
    spec=EngineeringSpec(
      component=_component(intent.component),pipe_diameter=_length(intent.pipe_diameter),nominal_pipe_size=_string(intent.nominal_pipe_size),
      wall_thickness=_length(intent.wall_thickness),bracket_width=_length(intent.bracket_width),base_thickness=_length(intent.base_thickness),
      fastener_designation=_string(intent.fastener_designation),fastener_count=_integer(intent.fastener_count),clearance_hole_diameter=_length(intent.hole_diameter),
      hole_semantics=_string(intent.hole_semantics),material=_material(intent.material),manufacturing_process=_string(intent.manufacturing_process),
      load_statement=_string(intent.load_statement),source_prompt=prompt)
    required={"component":spec.component,"pipe_diameter":spec.pipe_diameter,"wall_thickness":spec.wall_thickness,"bracket_width":spec.bracket_width,"base_thickness":spec.base_thickness,"fastener_designation":spec.fastener_designation,"fastener_count":spec.fastener_count,"material":spec.material}
    for path,val in required.items():
      if val.state in {EvidenceState.UNKNOWN,EvidenceState.HYPOTHESIS}: spec.unresolved_questions.append(f"Clarify {path}")
    if spec.nominal_pipe_size.state!=EvidenceState.UNKNOWN and spec.pipe_diameter.state==EvidenceState.UNKNOWN:
      spec.warnings.append("Nominal pipe size detected; physical diameter must not be inferred without a resolver.")
    return spec
