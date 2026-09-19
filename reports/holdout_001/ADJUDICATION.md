# Human Adjudication — holdout_001

This document records post-run human root-cause review. It does **not** modify the frozen holdout, raw model outputs, or official release-gate result.

## Summary

Five holdout cases contained classified failures: H02, H04, H06, H11 and H15.

### H02 — system terminology gap

Model output:
- component = `Halter`
- material = `Aluminium`

The facts were extracted correctly from the German wording. The deterministic terminology resolver lacks the German alias `Halter → pipe_bracket`.

Resulting effect:
- component became UNKNOWN downstream
- complete geometry was overblocked

Root cause: **TerminologyResolver coverage**, not missing source evidence.

### H04 — genuine evidence-boundary failure

Source:
`Create a bracket for a Ø42 pipe with 4 mm wall thickness.`

Model output:
- pipe_diameter = 42
- raw_unit = `mm`

The source does not explicitly state a diameter unit. GenCAD-AI's safety invariant is:

`missing unit != mm`

Root cause: **parser/evidence-boundary behavior**.

Recommended remediation is deterministic first: add a source-evidence guard that rejects a unit not supported by the extracted source phrase. Prompt changes should remain secondary.

### H06 — system terminology gap

Model output:
- component = `Pipe clamp bracket`

The intent is correct, but the resolver does not normalize this phrase to `pipe_bracket`.

Root cause: **TerminologyResolver coverage**.

### H11 — multilingual terminology gaps

Model output:
- component = `Rohrhalter`
- material = `Stahl`

Both are explicit and correctly extracted. The deterministic resolver lacks:
- `Rohrhalter → pipe_bracket`
- `Stahl → steel`

Resulting effect:
- complete positive control was overblocked

Root cause: **TerminologyResolver coverage**.

### H15 — benchmark adjudication issue

Source:
`Mount it with two M6 screws through two 6.6 mm clearance holes.`

Model output contained both:
- physical fastener designation = `M6`
- associated fastener designation = `M6`

The frozen ground truth expected the physical fastener field but left the associated designation UNKNOWN, causing a critical hallucination label.

Human review finds the model output defensible: the text explicitly associates M6 screws with the stated clearance holes. Therefore H15 is **not a clear unsupported engineering invention**.

Root cause: **holdout ground-truth ambiguity / ontology adjudication**, not a clear model hallucination.

The official raw release gate remains FAIL and is not retroactively changed.

## Decision after holdout_001

Do **not** tune prompt_v1 yet.

The strongest next intervention is system-level:

1. multilingual / phrase-level terminology aliases
2. deterministic source-evidence guard for inferred units
3. explicit ontology rule for when a physical fastener also establishes a hole association
4. rerun only on a new post-remediation benchmark/version; never overwrite holdout_001
