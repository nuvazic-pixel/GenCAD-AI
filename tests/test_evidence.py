import pytest
from pydantic import ValidationError
from app.domain.evidence import EvidenceState,EngineeringValue,Provenance

def test_unknown_constraints():
    with pytest.raises(ValidationError):
        EngineeringValue(value=10,state=EvidenceState.UNKNOWN,confidence=0.0,provenance=Provenance(source_type="unknown"))
    with pytest.raises(ValidationError):
        EngineeringValue(value=None,state=EvidenceState.UNKNOWN,confidence=0.4,provenance=Provenance(source_type="unknown"))

def test_hypothesis_provenance():
    with pytest.raises(ValidationError):
        EngineeringValue(value="steel",state=EvidenceState.HYPOTHESIS,confidence=0.6,provenance=Provenance(source_type="user_prompt"))
