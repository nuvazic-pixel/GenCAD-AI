# GenCAD-AI v0.2.2 — Real LLM Evaluation

v0.2.2 connects a real model to the benchmark-first engineering pipeline.

## Hard boundary

The LLM produces only `ParsedEngineeringIntent`.

It does **not** produce `EngineeringSpec`, standards-derived dimensions, CAD geometry,
or `DERIVED` evidence.

```text
Natural language
    ↓
EngineeringParser
    ↓
ParsedEngineeringIntent       ← probabilistic boundary
    ↓
EngineeringSpecBuilder
    ↓
Normalizer
    ↓
EngineeringSpec               ← deterministic boundary
    ↓
Validation
```

## Reference provider

The initial reference adapter uses OpenAI's Responses API with strict JSON Schema
structured output. The provider interface remains replaceable.

Default reference model:

`gpt-5.6-sol`

This is an evaluation baseline, not a permanent vendor dependency.

## Benchmark

`benchmarks/cases.py`

- 20 adversarial / ambiguity cases
- 5 positive controls

Positive controls are essential: a parser that marks everything `UNKNOWN` is safe but useless.

## Metrics

- Explicit Fact Recall
- Hallucinated Field Rate
- Uncertainty Preservation
- Semantic Confusion Rate
- Unsafe Proceed Rate
- Correct READY Rate (secondary anti-overblocking metric)

## Release gate

v0.2.2 fails the release gate if:

- `Unsafe Proceed Rate > 0`, or
- any encoded semantic safety trap is violated.

## Run deterministic tests

```bash
pip install -r requirements.txt
pytest -q
```

## Run real LLM benchmark

Set `OPENAI_API_KEY`, then:

```bash
python scripts/run_llm_benchmark.py
```

Outputs:

- `reports/benchmark_report.json`
- `reports/benchmark_report.md`

The benchmark runner exits with code `2` if the safety release gate fails.

## Evaluation control layer

The v0.2.2 evaluation protocol is frozen and implemented in code:

- deterministic `FailureClassifier`
- `BenchmarkComparator`
- hard/soft `ReleaseGate`
- immutable experiment fingerprinting
- case-level regression protection

See [docs/EVALUATION_PLAYBOOK.md](docs/EVALUATION_PLAYBOOK.md).

Each live benchmark run is stored in a dedicated directory such as
`reports/baseline_001/`, including the benchmark report, classified failures,
release-gate decision, and experiment fingerprint.

## Run the official live baseline

The frozen first live experiment is executed through GitHub Actions:

1. Add a repository Actions secret named `OPENAI_API_KEY`.
2. Open **Actions → GenCAD-AI baseline_001 → Run workflow**.
3. Download the `gencad-ai-baseline-001` artifact after the run.

The workflow fixes:

- provider: `openai`
- model: `gpt-5.6-sol`
- prompt: `v1`
- benchmark: `v0.2.2`
- run ID: `baseline_001`

It uploads the benchmark report, classified failures, release-gate decision,
experiment fingerprint, and runner log even when the release gate fails.

Do not edit `prompt_v1` based on individual cases before preserving this baseline.

