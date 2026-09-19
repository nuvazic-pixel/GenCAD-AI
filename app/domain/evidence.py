from enum import Enum
from typing import Generic, Literal, Optional, TypeVar
from pydantic import BaseModel, Field, model_validator
T=TypeVar("T")
class EvidenceState(str,Enum):
    CONFIRMED="confirmed"; DERIVED="derived"; HYPOTHESIS="hypothesis"; UNKNOWN="unknown"
class Provenance(BaseModel):
    source_type: Literal["user_prompt","standard","calculation","system_default","model_hypothesis","unknown"]
    source_ref: Optional[str]=None
    rule_id: Optional[str]=None
    original_text: Optional[str]=None
class EngineeringValue(BaseModel,Generic[T]):
    value: Optional[T]=None
    state: EvidenceState
    confidence: float=Field(default=1.0,ge=0.0,le=1.0)
    provenance: Provenance
    @model_validator(mode="after")
    def validate_consistency(self):
        if self.state==EvidenceState.UNKNOWN:
            if self.value is not None: raise ValueError("UNKNOWN values must not contain a value")
            if self.confidence!=0.0: raise ValueError("UNKNOWN values must use confidence=0.0")
        elif self.value is None:
            raise ValueError("Known values require a value")
        if self.state==EvidenceState.HYPOTHESIS and self.provenance.source_type!="model_hypothesis":
            raise ValueError("HYPOTHESIS values must use source_type=model_hypothesis")
        return self
