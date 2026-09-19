from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.domain.evidence import EngineeringValue


class ComponentType(str, Enum):
    PIPE_BRACKET = "pipe_bracket"
    UNKNOWN = "unknown"


class MaterialFamily(str, Enum):
    STEEL = "steel"
    ALUMINIUM = "aluminium"
    POLYMER = "polymer"
    UNKNOWN = "unknown"


class LengthValue(BaseModel):
    value_mm: float = Field(gt=0)
    source_value: Optional[float] = None
    source_unit: Optional[str] = None


class EngineeringSpec(BaseModel):
    schema_version: Literal["0.2.3"] = "0.2.3"
    component: EngineeringValue[ComponentType]
    pipe_diameter: EngineeringValue[LengthValue]
    nominal_pipe_size: EngineeringValue[str]
    wall_thickness: EngineeringValue[LengthValue]
    bracket_width: EngineeringValue[LengthValue]
    base_thickness: EngineeringValue[LengthValue]
    fastener_designation: EngineeringValue[str]
    fastener_count: EngineeringValue[int]
    hole_count: EngineeringValue[int]
    clearance_hole_diameter: EngineeringValue[LengthValue]
    hole_semantics: EngineeringValue[str]
    material: EngineeringValue[MaterialFamily]
    manufacturing_process: EngineeringValue[str]
    load_statement: EngineeringValue[str]
    unresolved_questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_prompt: str
