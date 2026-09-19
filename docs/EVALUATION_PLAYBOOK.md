# GenCAD-AI Evaluation Playbook v2.0

Status: **FROZEN for v0.2.2**

This document defines the operational evaluation protocol for the engineering-intent parser.
Prompt changes are not accepted by intuition alone; they must be supported by benchmark evidence.

## 1. Failure classification

`FailureClassifier` is deterministic. It does not use an LLM to judge another LLM.

A case may produce multiple failure classes:

- `extraction_failure`
- `uncertainty_failure`
- `semantic_confusion`
- `hallucination`
- `overblocking`

Each event records:

- failure type
- severity
- affected field
- expected value/state
- actual value/state
- diagnostic detail

Root-cause analysis remains a human-review step.

## 2. Hard release gates

All must remain zero:

- Unsafe Proceed Rate
- Critical Hallucinations
- Critical Semantic Errors
- Positive-Control Regressions

If any hard gate is breached, the candidate is rejected.

## 3. Soft targets

These guide optimization but do not override a hard-gate failure:

- Explicit Fact Recall >= 95%
- Uncertainty Preservation >= 95%
- Correct READY Rate >= 90%
- Hallucinated Field Rate <= 1%

## 4. Meaningful improvement

For the current 25-case benchmark, percentage changes alone are too granular to justify conclusions.

A candidate has meaningful improvement when:

1. at least one previously failing case is fully fixed,
2. no new hard-gate failure is introduced,
3. no positive-control case regresses.

At 100+ benchmark cases, metric deltas and interval estimates may be added.

## 5. Experiment fingerprint

Every live run records:

- run ID
- provider
- model
- prompt version
- benchmark version
- schema version
- git commit
- prompt SHA-256
- benchmark SHA-256
- schema SHA-256
- Python version
- UTC timestamp
- deterministic fingerprint ID

No API keys or secrets are stored in the fingerprint.

## 6. Iteration workflow

```text
freeze benchmark
      ↓
freeze prompt
      ↓
run baseline
      ↓
FailureClassifier
      ↓
human root-cause review
      ↓
minimal corrective change
      ↓
run candidate
      ↓
BenchmarkComparator
      ↓
ReleaseGate
      ↓
accept / reject
```

## 7. Stop rule

Prompt tuning stops when:

- all hard gates pass,
- utility targets are acceptable,
- the hidden benchmark passes, and
- two consecutive iterations produce no material case-level improvement.

The prompt is then frozen.

## 8. v0.2.2 baseline

Current public benchmark:

- 20 adversarial / ambiguity cases
- 5 positive controls
- 25 total cases

The first live model run is named `baseline_001`.

Outputs are stored under:

```text
reports/baseline_001/
├── benchmark_report.json
├── benchmark_report.md
├── failures.json
├── release_gate.json
└── fingerprint.json
```

Later candidates can be compared with:

```bash
python scripts/compare_runs.py reports/baseline_001 reports/baseline_002
```
