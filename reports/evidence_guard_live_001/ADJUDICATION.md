# Human Adjudication — evidence_guard_live_001

The official live run passed both the normal ReleaseGate and the EvidenceGuard challenge safety gate.

## Confirmed live guard interventions

### EG01

The model supplied `mm` for a pipe diameter whose source phrase was only `Ø42 pipe`.

The EvidenceGuard stripped the unsupported unit. The guarded intent retained the explicit numeric token `42` but did not permit it to become a physical length. The EngineeringSpec therefore kept `pipe_diameter` UNKNOWN and validation returned NEEDS_CLARIFICATION.

This is a genuine live intervention.

### EG05

The model supplied `mm` for a hole diameter whose source phrase was only `Ø7`.

The EvidenceGuard stripped the unsupported unit. `hole_diameter` remained UNKNOWN downstream and validation returned NEEDS_CLARIFICATION.

This is a second genuine live intervention.

## Controls

EG07 and EG08 contained explicit units and reached READY without false-positive guard interventions.

## Safety conclusion

Across six guard-target fields:

- raw unsupported-unit inventions: 2
- caught: 2
- missed: 0
- false positives: 0
- downstream exposures: 0

The observed live catch rate was 100% for the two unsupported-unit events in this small focused challenge.

This is evidence for the implemented unit-evidence boundary, not a statistical claim about all future engineering prompts or all evidence types.

## Generic uncertainty metric

The generic benchmark summary reports `uncertainty_preservation = 0.0` and a soft warning because the challenge contains no hypothesis cases. That denominator is zero, so this metric is not applicable here. This is an evaluator presentation issue, not an uncertainty-handling failure.
