from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class GeometryVerificationReport(BaseModel):
    verifier_version: str = "0.3.1"
    artifact_file: str

    solid_valid: bool
    watertight: bool
    positive_volume: bool
    volume_mm3: float

    expected_hole_count: int
    detected_hole_count: int
    hole_count_match: bool

    expected_bbox_mm: list[float]
    measured_bbox_mm: list[float]
    bbox_delta_mm: list[float]
    dimensions_match: bool

    expected_pipe_diameter_mm: float
    measured_pipe_diameter_mm: float | None = None
    pipe_diameter_delta_mm: float | None = None
    pipe_opening_match: bool

    expected_wall_mm: float
    measured_wall_mm: float | None = None
    wall_delta_mm: float | None = None
    wall_check_passed: bool

    geometry_fingerprint: str | None = None
    failed_rules: list[str] = Field(default_factory=list)
    passed: bool


class CADArtifactReleaseStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class CADArtifactReleaseDecision(BaseModel):
    status: CADArtifactReleaseStatus
    releasable: bool
    geometry_fingerprint: str | None = None
    failed_rules: list[str] = Field(default_factory=list)
    reason: str
