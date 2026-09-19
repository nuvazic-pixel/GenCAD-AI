# Calibration Delta — baseline_002 → baseline_003

This is a **system/schema calibration delta**, not a claim that the model itself improved.

The model and system prompt remained unchanged. The schema, ontology, benchmark ground truth and CAD-readiness semantics were calibrated.

| Metric | baseline_002 | baseline_003 | Delta |
|---|---:|---:|---:|
| Explicit Fact Recall | 94.38% | 100.00% | +5.62 pp |
| Hallucinated Field Rate | 0.39% | 0.00% | -0.39 pp |
| Uncertainty Preservation | 100.00% | 100.00% | 0.00 pp |
| Semantic Confusion Rate | 0.00% | 0.00% | 0.00 pp |
| Unsafe Proceed Rate | 0.00% | 0.00% | 0.00 pp |
| Correct READY Rate | 80.00% | 100.00% | +20.00 pp |

## What changed

v0.2.4 separates:

- physical fastener designation/count
- fastener-size designation associated with a hole
- hole count
- explicit hole diameter
- hole semantics

CAD readiness is now based on explicit geometry and material rather than requiring a physical fastener specification.

The B17 ground truth was also corrected because the phrase `bracket width` explicitly identifies the component as a bracket.

## Result

All 25 known development cases pass without a prompt change.

This closes the known-benchmark calibration phase. The next validation must use unseen holdout cases before any claim of generalization or before deciding whether prompt_v2 is necessary.
