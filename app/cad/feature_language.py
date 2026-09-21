from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domain.evidence import EvidenceState


class FeatureOperation(str, Enum):
    ADD = "add"
    CUT = "cut"


class FeatureKind(str, Enum):
    BOX = "box"
    ANNULAR_EXTRUDE = "annular_extrude"
    CYLINDER = "cylinder"


class FeatureParameter(BaseModel):
    value: float | int | str | None
    unit: str | None = None
    state: EvidenceState
    source_fields: list[str] = Field(default_factory=list)
    rule_id: str | None = None
    source_ref: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def validate_state_value(self):
        if self.state == EvidenceState.UNKNOWN and self.value is not None:
            raise ValueError("UNKNOWN feature parameters must not contain a value")
        if self.state != EvidenceState.UNKNOWN and self.value is None:
            raise ValueError("Known feature parameters require a value")
        if self.state == EvidenceState.DERIVED and not self.rule_id:
            raise ValueError("DERIVED feature parameters require rule_id provenance")
        return self


class CADFeature(BaseModel):
    feature_id: str
    label: str
    kind: FeatureKind
    operation: FeatureOperation
    parameters: dict[str, FeatureParameter]
    description: str | None = None

    @property
    def evidence_state(self) -> EvidenceState:
        states = {parameter.state for parameter in self.parameters.values()}
        if EvidenceState.UNKNOWN in states:
            return EvidenceState.UNKNOWN
        if EvidenceState.HYPOTHESIS in states:
            return EvidenceState.HYPOTHESIS
        if EvidenceState.DERIVED in states:
            return EvidenceState.DERIVED
        return EvidenceState.CONFIRMED


class CADFeatureProgram(BaseModel):
    program_id: str
    version: str = "0.4.0"
    generator_id: str
    source_parameter_hash: str
    features: list[CADFeature]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_feature_ids(self):
        ids = [feature.feature_id for feature in self.features]
        if len(ids) != len(set(ids)):
            raise ValueError("feature_id values must be unique")
        return self


class FeatureProgramVerificationReport(BaseModel):
    program_id: str
    passed: bool
    blocked_features: list[str] = Field(default_factory=list)
    blocked_parameters: list[str] = Field(default_factory=list)
    failed_rules: list[str] = Field(default_factory=list)


class VerifiedCADFeatureProgram(CADFeatureProgram):
    verification_rule: str = "FEATURE_EVIDENCE_GATE_V1"

    @model_validator(mode="after")
    def all_parameters_are_releasable(self):
        forbidden = []
        for feature in self.features:
            for name, parameter in feature.parameters.items():
                if parameter.state not in {
                    EvidenceState.CONFIRMED,
                    EvidenceState.DERIVED,
                }:
                    forbidden.append(f"{feature.feature_id}.{name}")

        if forbidden:
            raise ValueError(
                "VerifiedCADFeatureProgram cannot contain UNKNOWN/HYPOTHESIS: "
                + ", ".join(forbidden)
            )
        return self
