# Calibration Delta — baseline_001 → baseline_002

This comparison is an **evaluation calibration delta**, not a claim that the model improved.

The model and prompt remained the same. The deterministic schema, normalization, terminology and benchmark semantics changed.

| Metric | baseline_001 | baseline_002 | Delta |
|---|---:|---:|---:|
| Explicit Fact Recall | 85.39% | 94.38% | +8.99 pp |
| Hallucinated Field Rate | 3.43% | 0.39% | -3.04 pp |
| Uncertainty Preservation | 100.00% | 100.00% | 0.00 pp |
| Semantic Confusion Rate | 3.23% | 0.00% | -3.23 pp |
| Unsafe Proceed Rate | 0.00% | 0.00% | 0.00 pp |
| Correct READY Rate | 40.00% | 80.00% | +40.00 pp |

## Interpretation

The calibration removed evaluator noise caused by raw string equality, unit/number representation differences, qualitative requirements being forced into engineering fields, implicit millimetre assumptions, and conflation of hole count with fastener count.

Hard release gates changed from **FAIL** to **PASS** without changing prompt_v1.

Remaining soft failures are concentrated in four cases:

- B02 — `M6 holes` not mapped to `fastener_designation`
- B05 — German equivalent
- B17 — explicit values were downgraded to hypotheses; component ground truth is also debatable
- P04 — `M6 mounting holes` not mapped to `fastener_designation`, causing overblocking

These should be resolved by clarifying hole/fastener ontology and readiness semantics before prompt_v2.
