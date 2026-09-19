from typing import Literal, Optional, Union
from pydantic import BaseModel, Field
Scalar=Union[str,int,float]
class ParsedField(BaseModel):
    raw_value: Optional[Scalar]=None
    raw_unit: Optional[str]=None
    source_text: Optional[str]=None
    state: Literal["confirmed","unknown","hypothesis"]
    confidence: float=Field(default=1.0,ge=0.0,le=1.0)
class ParsedEngineeringIntent(BaseModel):
    component: ParsedField
    pipe_diameter: ParsedField
    nominal_pipe_size: ParsedField
    wall_thickness: ParsedField
    bracket_width: ParsedField
    base_thickness: ParsedField
    fastener_designation: ParsedField
    fastener_count: ParsedField
    hole_diameter: ParsedField
    hole_semantics: ParsedField
    material: ParsedField
    manufacturing_process: ParsedField
    load_statement: ParsedField
