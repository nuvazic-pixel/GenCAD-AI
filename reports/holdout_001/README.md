# holdout_001 — Frozen v0.2.5 Holdout Evaluation

This is the first live evaluation on the separate 15-case holdout benchmark.

- Provider: OpenAI
- Model: `gpt-5.6-sol`
- Prompt: `v1` — unchanged from baseline_001/002/003
- Prompt SHA-256: `ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d`
- Benchmark: `0.2.5-holdout`
- Schema: `0.2.4`
- Cases: 15
- Git commit: `7f57c84dbd88cbbf0f4ea22d651f7171c57b8fb1`
- GitHub Actions run: `35434282541`
- Artifact ID: `10581606946`
- Artifact SHA-256: `de2ec536a0111a7f5c8b6ecf127f270bb6ae166154b0cf59bf2f2a03955b1591`

## Raw result

| Metric | Result |
|---|---:|
| Explicit Fact Recall | 94.32% |
| Hallucinated Field Rate | 0.74% |
| Uncertainty Preservation | 100.00% |
| Semantic Confusion Rate | 0.00% |
| Unsafe Proceed Rate | 0.00% |
| Correct READY Rate | 66.67% |

Official raw release gate: **FAIL**

Hard-gate counts:

- Unsafe Proceed: 0
- Critical Hallucinations: 1
- Critical Semantic Errors: 0
- Positive-Control Regressions: 0

## Important interpretation

The holdout did its job: the perfect score on the known development benchmark did **not** generalize perfectly.

The raw run is preserved unchanged. Human adjudication is documented separately in `ADJUDICATION.md`; the benchmark and raw gate are not rewritten after observing the results.

This holdout was internally authored and frozen before the live run. It was unseen by the parser during prior calibration, but it is not an independently curated external benchmark.
