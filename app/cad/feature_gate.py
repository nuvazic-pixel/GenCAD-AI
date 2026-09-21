from __future__ import annotations

from app.cad.feature_language import (
    CADFeatureProgram,
    FeatureProgramVerificationReport,
    VerifiedCADFeatureProgram,
)
from app.domain.evidence import EvidenceState


RULE_UNTRUSTED_FEATURE_PARAMETER = "UNTRUSTED_FEATURE_PARAMETER"


def verify_feature_program(
    program: CADFeatureProgram,
) -> tuple[FeatureProgramVerificationReport, VerifiedCADFeatureProgram | None]:
    blocked_features: set[str] = set()
    blocked_parameters: list[str] = []

    for feature in program.features:
        for name, parameter in feature.parameters.items():
            if parameter.state not in {
                EvidenceState.CONFIRMED,
                EvidenceState.DERIVED,
            }:
                blocked_features.add(feature.feature_id)
                blocked_parameters.append(f"{feature.feature_id}.{name}")

    failed_rules = (
        [RULE_UNTRUSTED_FEATURE_PARAMETER]
        if blocked_parameters
        else []
    )

    report = FeatureProgramVerificationReport(
        program_id=program.program_id,
        passed=not blocked_parameters,
        blocked_features=sorted(blocked_features),
        blocked_parameters=sorted(blocked_parameters),
        failed_rules=failed_rules,
    )

    if not report.passed:
        return report, None

    verified = VerifiedCADFeatureProgram.model_validate(
        {
            **program.model_dump(mode="python"),
            "verification_rule": "FEATURE_EVIDENCE_GATE_V1",
        }
    )
    return report, verified
