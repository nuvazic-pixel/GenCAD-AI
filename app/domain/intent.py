from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


Scalar = Union[str, int, float]


class ParsedField(BaseModel):
    raw_value: Optional[Scalar] = Field(
        default=None,
        description="Raw explicit value. Must be null when state=unknown. Never invent a missing value.",
    )
    raw_unit: Optional[str] = Field(
        default=None,
        description="Raw explicit unit. Must be null when state=unknown. Never infer a missing unit.",
    )
    source_text: Optional[str] = Field(
        default=None,
        description="Exact source phrase when available.",
    )
    state: Literal["confirmed", "unknown", "hypothesis"]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="before")
    @classmethod
    def enforce_unknown_invariant(cls, data):
        if isinstance(data, dict) and data.get("state") == "unknown":
            data = dict(data)
            data["raw_value"] = None
            data["raw_unit"] = None
            data["confidence"] = 0.0
        return data

    @model_validator(mode="after")
    def validate_known_value(self):
        if self.state in {"confirmed", "hypothesis"} and self.raw_value is None:
            raise ValueError("confirmed/hypothesis fields require an explicit raw_value")
        return self


class QualitativeRequirement(BaseModel):
    text: str = Field(description="Qualitative requirement preserved verbatim or near-verbatim.")
    category: Literal["strength", "weight", "manufacturability", "size", "other"]
    source_text: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ParsedEngineeringIntent(BaseModel):
    component: ParsedField = Field(description="Requested design component. Do not use referenced objects such as the pipe itself as the component.")
    pipe_diameter: ParsedField
    nominal_pipe_size: ParsedField
    wall_thickness: ParsedField
    bracket_width: ParsedField
    base_thickness: ParsedField
    fastener_designation: ParsedField
    fastener_count: ParsedField = Field(
        description="Count of explicitly stated fasteners such as screws or bolts. Never use a hole count here."
    )
    hole_count: ParsedField = Field(
        default_factory=lambda: ParsedField(state="unknown"),
        description="Count of explicitly stated holes. Never infer a fastener count from this field."
    )
    hole_diameter: ParsedField
    hole_semantics: ParsedField = Field(description="Physical hole semantics such as clearance or threaded. Generic roles such as mounting hole do not imply clearance/threaded semantics.")
    material: ParsedField
    manufacturing_process: ParsedField
    load_statement: ParsedField = Field(
        description="Explicit quantitative or otherwise explicit load statement. Qualitative words such as strong belong in qualitative_requirements."
    )
    qualitative_requirements: list[QualitativeRequirement] = Field(
        default_factory=list,
        description="Qualitative requirements such as strong, lightweight, compact, or easy to manufacture. Do not convert them into engineering quantities."
    )
    unmapped_phrases: list[str] = Field(
        default_factory=list,
        description="Relevant source phrases that do not safely map to a structured engineering field."
    )
