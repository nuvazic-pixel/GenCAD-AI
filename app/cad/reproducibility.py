from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from app.cad.reproducibility_models import (
    GeometryBuildRecord,
    GeometryReproducibilityReport,
)


RULE_BUILD_COUNT = "REPRODUCIBILITY_BUILD_COUNT_MISMATCH"
RULE_VERIFICATION = "REPRODUCIBILITY_VERIFICATION_FAILURE"
RULE_ARTIFACT_RELEASE = "REPRODUCIBILITY_ARTIFACT_RELEASE_FAILURE"
RULE_FINGERPRINT_MISMATCH = "REPRODUCIBILITY_FINGERPRINT_MISMATCH"
RULE_SENSITIVITY_COLLISION = "REPRODUCIBILITY_SENSITIVITY_COLLISION"


def canonical_payload_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + sha256(encoded).hexdigest()


def evaluate_geometry_reproducibility(
    *,
    generator_id: str,
    repeat_count: int,
    released_parameters_hash: str,
    layout_hash: str,
    builds: list[GeometryBuildRecord],
    sensitivity_control_fingerprint: str | None = None,
) -> GeometryReproducibilityReport:
    fingerprints = sorted(
        {build.geometry_fingerprint for build in builds}
    )

    all_verified = all(build.verification_passed for build in builds)
    all_releasable = all(build.artifact_releasable for build in builds)
    fingerprints_match = len(fingerprints) == 1 and len(builds) > 0

    sensitivity_differs = None
    if sensitivity_control_fingerprint is not None and fingerprints:
        sensitivity_differs = (
            sensitivity_control_fingerprint != fingerprints[0]
        )

    failed_rules: list[str] = []

    if len(builds) != repeat_count:
        failed_rules.append(RULE_BUILD_COUNT)
    if not all_verified:
        failed_rules.append(RULE_VERIFICATION)
    if not all_releasable:
        failed_rules.append(RULE_ARTIFACT_RELEASE)
    if not fingerprints_match:
        failed_rules.append(RULE_FINGERPRINT_MISMATCH)
    if sensitivity_differs is False:
        failed_rules.append(RULE_SENSITIVITY_COLLISION)

    return GeometryReproducibilityReport(
        generator_id=generator_id,
        repeat_count=repeat_count,
        released_parameters_hash=released_parameters_hash,
        layout_hash=layout_hash,
        builds=builds,
        unique_geometry_fingerprints=fingerprints,
        all_verified=all_verified,
        all_releasable=all_releasable,
        fingerprints_match=fingerprints_match,
        sensitivity_control_fingerprint=sensitivity_control_fingerprint,
        sensitivity_control_differs=sensitivity_differs,
        failed_rules=failed_rules,
        passed=not failed_rules,
    )
