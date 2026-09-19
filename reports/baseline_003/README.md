# baseline_003 — Hole/Assembly Semantics Calibration

Official GenCAD-AI v0.2.4 calibration run.

- Provider: OpenAI
- Model: `gpt-5.6-sol`
- Prompt: `v1` — unchanged from baseline_001 and baseline_002
- Prompt SHA-256: `ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d`
- Benchmark: `v0.2.4`
- Schema: `v0.2.4`
- Cases: 25
- Git commit: `e3e2db149a5d2a81ce29e0e33b6dbc8039616a4e`
- GitHub Actions run: `35433651759`
- Artifact ID: `10582231180`
- Artifact SHA-256: `be9eeebd40267c2aa949dc19690e81c36d1d690c59cf7a2d91b07f2829462ff3`

## Result

| Metric | Result |
|---|---:|
| Explicit Fact Recall | 100.00% |
| Hallucinated Field Rate | 0.00% |
| Uncertainty Preservation | 100.00% |
| Semantic Confusion Rate | 0.00% |
| Unsafe Proceed Rate | 0.00% |
| Correct READY Rate | 100.00% |

Release gate: **PASS**

Hard-gate findings:

- Critical Hallucinations: 0
- Critical Semantic Errors: 0
- Unsafe Proceed: 0
- Positive-Control Regressions: 0

## Interpretation

This is a perfect score on the **known 25-case development benchmark** after system calibration.

It is **not** evidence of generalization or a claim that the model is solved. The next required validation step is a frozen holdout benchmark containing unseen wording and combinations.

The complete raw GitHub Actions artifact contains all 25 per-case traces:
ParsedEngineeringIntent, EngineeringSpec, ValidationReport, failures, metrics and runner log.
