# holdout_002 — v0.2.6 Evidence Integrity Evaluation

Second frozen 15-case holdout, fully disjoint from the development benchmark and holdout_001.

- Provider: OpenAI
- Model: `gpt-5.6-sol`
- Prompt: `v1` — unchanged
- Benchmark: `0.2.6-holdout2`
- Schema: `0.2.4`
- System package: `v0.2.6`
- Cases: 15
- Git commit: `684083bf99097e14838bca58db9201b0569e4245`
- GitHub Actions run: `35435018995`
- Artifact ID: `10581763764`
- Artifact SHA-256: `65dbb46c16cd7d4d9aac2ae0c4fca491f88d5675b5f48a67a5770c99090d3724`

## Raw result

| Metric | Result |
|---|---:|
| Explicit Fact Recall | 100.00% |
| Hallucinated Field Rate | 0.84% |
| Uncertainty Preservation | 100.00% |
| Semantic Confusion Rate | 0.00% |
| Unsafe Proceed Rate | 0.00% |
| Correct READY Rate | 100.00% |

Official raw release gate: **FAIL**

Hard-gate findings:

- Unsafe Proceed: 0
- Critical Hallucinations: 1
- Critical Semantic Errors: 0
- Positive-Control Regressions: 0

The sole classified failure is J06, involving a source-supported M6 hole association in German compound wording.

The raw result remains frozen. Human adjudication is recorded separately in `ADJUDICATION.md`.
