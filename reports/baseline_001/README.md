# baseline_001

Official first live GenCAD-AI model benchmark.

- Provider: OpenAI
- Model: `gpt-5.6-sol`
- Prompt: `v1`
- Benchmark: `v0.2.2`
- Schema: `v0.2.1`
- Cases: 25
- Git commit: `f0ec89a9212cf3f73114334bf812e7e86d163ba4`
- GitHub Actions run: `35431736966`
- Artifact ID: `10580314617`
- Artifact SHA-256: `343dc098ec703ca60cb31cff72dfc6282e8e22f23b5d413cb2bc123c27bf6f55`

## Result

| Metric | Result |
|---|---:|
| Explicit Fact Recall | 85.39% |
| Hallucinated Field Rate | 3.43% |
| Uncertainty Preservation | 100.00% |
| Semantic Confusion Rate | 3.23% |
| Unsafe Proceed Rate | 0.00% |
| Correct READY Rate | 40.00% |

Release gate: **FAIL**

Hard-gate findings:

- Critical Hallucinations: 1
- Critical Semantic Errors: 1
- Unsafe Proceed: 0
- Positive-Control Regressions: 0

The complete raw artifact is preserved by GitHub Actions. This directory is a permanent repository-side evidence pointer for the frozen run.
