from __future__ import annotations

from app.cad.verification_models import (
    CADArtifactReleaseDecision,
    CADArtifactReleaseStatus,
    GeometryVerificationReport,
)


def evaluate_cad_artifact_release(
    report: GeometryVerificationReport,
) -> CADArtifactReleaseDecision:
    if report.passed and not report.failed_rules and report.geometry_fingerprint:
        return CADArtifactReleaseDecision(
            status=CADArtifactReleaseStatus.PASS,
            releasable=True,
            geometry_fingerprint=report.geometry_fingerprint,
            failed_rules=[],
            reason="Generated geometry passed all verification rules.",
        )

    return CADArtifactReleaseDecision(
        status=CADArtifactReleaseStatus.FAIL,
        releasable=False,
        geometry_fingerprint=report.geometry_fingerprint,
        failed_rules=list(report.failed_rules),
        reason=(
            "Generated geometry is quarantined because verification failed: "
            + ", ".join(report.failed_rules)
        ),
    )
