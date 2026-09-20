from __future__ import annotations

from pydantic import BaseModel, Field


class GeometryBuildRecord(BaseModel):
    build_id: str
    geometry_fingerprint: str
    stl_sha256: str
    step_sha256: str
    verification_passed: bool
    artifact_releasable: bool
    volume_mm3: float
    bbox_mm: list[float]


class GeometryReproducibilityReport(BaseModel):
    reproducibility_version: str = "0.3.2"
    generator_id: str
    repeat_count: int
    released_parameters_hash: str
    layout_hash: str

    builds: list[GeometryBuildRecord] = Field(default_factory=list)
    unique_geometry_fingerprints: list[str] = Field(default_factory=list)
    unique_stl_sha256: list[str] = Field(default_factory=list)
    unique_step_sha256: list[str] = Field(default_factory=list)
    stl_bytes_identical: bool
    step_bytes_identical: bool

    all_verified: bool
    all_releasable: bool
    fingerprints_match: bool

    sensitivity_control_fingerprint: str | None = None
    sensitivity_control_differs: bool | None = None

    failed_rules: list[str] = Field(default_factory=list)
    passed: bool
