from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CADReleaseStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class ReleasedBracketParameters(BaseModel):
    pipe_diameter_mm: float = Field(gt=0)
    wall_thickness_mm: float = Field(gt=0)
    bracket_width_mm: float = Field(gt=0)
    base_thickness_mm: float = Field(gt=0)
    hole_count: int = Field(ge=1)
    hole_diameter_mm: float = Field(gt=0)


class CADReleaseDecision(BaseModel):
    status: CADReleaseStatus
    allowed: bool
    generator: str
    blocking_fields: list[str] = Field(default_factory=list)
    failed_rules: list[str] = Field(default_factory=list)
    accepted_parameters: ReleasedBracketParameters | None = None
    evidence_summary: dict[str, dict[str, Any]] = Field(default_factory=dict)
    reason: str
