# baseline_002 — Evaluation Calibration

Official GenCAD-AI calibration run.

- Provider: OpenAI
- Model: `gpt-5.6-sol`
- Prompt: `v1` — unchanged from baseline_001
- Prompt SHA-256: `ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d`
- Benchmark: `v0.2.3`
- Schema: `v0.2.3`
- Cases: 25
- Git commit: `1fc73f3c4b4be3b6878300c3da75cab221224698`
- GitHub Actions run: `35433167063`
- Artifact ID: `10581616283`
- Artifact SHA-256: `d7ea9e179b763578de612afb3eccfa1939d91148ef41617cc92da66a6be9cfee`

## Result

| Metric | Result |
|---|---:|
| Explicit Fact Recall | 94.38% |
| Hallucinated Field Rate | 0.39% |
| Uncertainty Preservation | 100.00% |
| Semantic Confusion Rate | 0.00% |
| Unsafe Proceed Rate | 0.00% |
| Correct READY Rate | 80.00% |

Release gate: **PASS**

Hard-gate findings:

- Critical Hallucinations: 0
- Critical Semantic Errors: 0
- Unsafe Proceed: 0
- Positive-Control Regressions: 0

The raw GitHub Actions artifact includes 25 per-case traces containing ParsedEngineeringIntent, EngineeringSpec, ValidationReport, failures and metrics.
