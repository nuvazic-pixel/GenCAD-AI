from enum import Enum
from pydantic import BaseModel,Field
from app.domain.evidence import EvidenceState
from app.domain.spec import EngineeringSpec
class ValidationStatus(str,Enum): READY="ready"; NEEDS_CLARIFICATION="needs_clarification"; REJECTED="rejected"
class ValidationReport(BaseModel):
    status: ValidationStatus
    expected_stage: str
    blocking_fields: list[str]=Field(default_factory=list)
    failed_rules: list[str]=Field(default_factory=list)
    warnings: list[str]=Field(default_factory=list)
def validate_spec(spec:EngineeringSpec)->ValidationReport:
    blocking=[]; failed=[]; warnings=list(spec.warnings)
    fields={"component":spec.component,"pipe_diameter":spec.pipe_diameter,"wall_thickness":spec.wall_thickness,"bracket_width":spec.bracket_width,"base_thickness":spec.base_thickness,"fastener_designation":spec.fastener_designation,"fastener_count":spec.fastener_count,"material":spec.material}
    for path,v in fields.items():
      if v.state in {EvidenceState.UNKNOWN,EvidenceState.HYPOTHESIS}: blocking.append(path)
    if spec.pipe_diameter.value is not None and spec.wall_thickness.value is not None and spec.wall_thickness.value.value_mm>=spec.pipe_diameter.value.value_mm/2:
      failed.append("BRACKET_WALL_LT_PIPE_RADIUS")
    if failed:
      return ValidationReport(status=ValidationStatus.REJECTED,expected_stage="engineering_validation",blocking_fields=blocking,failed_rules=failed,warnings=warnings)
    if blocking:
      stage="terminology_resolution" if spec.nominal_pipe_size.state!=EvidenceState.UNKNOWN and spec.pipe_diameter.state==EvidenceState.UNKNOWN else "readiness_validation"
      return ValidationReport(status=ValidationStatus.NEEDS_CLARIFICATION,expected_stage=stage,blocking_fields=blocking,warnings=warnings)
    return ValidationReport(status=ValidationStatus.READY,expected_stage="ready",warnings=warnings)
