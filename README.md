# GenCAD-AI v0.2.4 — Safety-First Engineering Intent for Generative CAD

![tests](https://github.com/nuvazic-pixel/GenCAD-AI/actions/workflows/tests.yml/badge.svg)

GenCAD-AI is an engineering prototype for converting natural-language design requests into a typed, validated engineering intent before any CAD geometry is generated.

The project focuses on the safety boundary between probabilistic language-model interpretation and deterministic engineering logic.

> **Current scope:** engineering-intent extraction, normalization, terminology resolution, validation and reproducible evaluation.  
> Production CAD/CAE generation is a later stage; this repository does not claim that an LLM directly produces engineering-safe CAD.

## Core principle

**The LLM interprets. Deterministic code decides engineering truth.**

```text
Natural language
      ↓
EngineeringParser
      ↓
ParsedEngineeringIntent          probabilistic boundary
      ↓
Normalizer
      ↓
TerminologyResolver
      ↓
EngineeringSpec                  deterministic boundary
      ↓
Validator / Release Gate
      ↓
future CAD / CAE generation
```

The model is not allowed to create `DERIVED` engineering evidence. Missing information remains unknown until an explicit deterministic resolver, standard, or calculation supplies it.

## Evidence model

Engineering values distinguish:

- `CONFIRMED` — explicitly supported by the source
- `DERIVED` — deterministically calculated or resolved downstream
- `HYPOTHESIS` — uncertain interpretation; never CAD-ready by itself
- `UNKNOWN` — missing information

For parser output, `UNKNOWN` enforces:

```text
raw_value = null
raw_unit = null
confidence = 0
```

## v0.2.4 — Hole / assembly semantics

A major calibration finding was that a phrase such as `M6 hole` does not assert that a physical M6 screw exists.

The schema therefore separates:

```text
fastener_designation
fastener_count

associated_fastener_designation
hole_count
hole_diameter
hole_semantics
```

Examples:

```text
"two M6 screws"
→ physical fastener designation + physical fastener count

"two M6 mounting holes"
→ associated fastener designation + hole count

"6.6 mm hole diameter"
→ explicit hole geometry

"M6 clearance holes"
→ M6 association + clearance semantics
→ no hole diameter is silently derived
```

CAD readiness is geometry-driven. A fully specified hole does not require the user to also claim that a physical fastener is present.

## Safety invariants

GenCAD-AI intentionally rejects common unsafe shortcuts:

```text
DN50 ≠ Ø50 mm
M6 ≠ automatic clearance-hole diameter
threaded hole ≠ clearance hole
missing unit ≠ mm
two holes ≠ two fasteners
qualitative "strong" ≠ engineering load
steel ≠ automatic steel grade
```

## Evaluation framework

The repository includes a deterministic evaluation-control layer:

- `FailureClassifier`
- `BenchmarkComparator`
- `ReleaseGate`
- experiment fingerprinting
- per-case audit traces
- regression protection
- GitHub Actions CI on Python 3.11 and 3.12

Failure classification is deterministic; an LLM is not used to judge another LLM.

### Hard gates

All must remain zero:

```text
Unsafe Proceed
Critical Hallucinations
Critical Semantic Errors
Positive-Control Regressions
```

### Soft targets

```text
Explicit Fact Recall       >= 95%
Uncertainty Preservation   >= 95%
Correct READY Rate         >= 90%
Hallucinated Field Rate    <= 1%
```

## Experiment history

The same system prompt, `prompt_v1`, was preserved across all three live runs.

| Run | System version | Recall | Hallucination | Semantic confusion | Unsafe proceed | Correct READY | Gate |
|---|---|---:|---:|---:|---:|---:|---|
| baseline_001 | v0.2.2 | 85.39% | 3.43% | 3.23% | 0% | 40% | FAIL |
| baseline_002 | v0.2.3 | 94.38% | 0.39% | 0% | 0% | 80% | PASS |
| baseline_003 | v0.2.4 | 100% | 0% | 0% | 0% | 100% | PASS |

These numbers are **calibration results on the known 25-case development benchmark**, not evidence that the model itself improved and not proof of generalization.

The prompt SHA-256 remained:

```text
ca2dab42a10ad69812dcc30ac565f2830d76fc55fb4ba5e2c66faad9119a3e4d
```

Experiment evidence is preserved under [reports/](reports/).

See:

- [Evaluation Playbook](docs/EVALUATION_PLAYBOOK.md)
- [baseline_001 evidence](reports/baseline_001/)
- [baseline_002 evidence](reports/baseline_002/)
- [baseline_003 evidence](reports/baseline_003/)
- [001 → 002 calibration](reports/CALIBRATION_001_TO_002.md)
- [002 → 003 calibration](reports/CALIBRATION_002_TO_003.md)

## Benchmark

The development benchmark contains:

```text
20 adversarial / ambiguity cases
 5 positive controls
25 total
```

Historical benchmark versions remain frozen:

```text
v0.2.2  original benchmark
v0.2.3  normalization / uncertainty calibration
v0.2.4  hole / assembly semantics calibration
```

## Run deterministic tests

```bash
python -m pip install -r requirements.txt
pytest -q
```

## Run a live benchmark

Set an OpenAI API key locally:

```bash
export OPENAI_API_KEY="..."
python -m scripts.run_llm_benchmark
```

Configuration is environment-based; the provider interface remains replaceable.

GitHub Actions workflows use repository secrets. `OPENAI_API_KEY` is the recommended secret name; the repository owner setup also supports the legacy `GENCAD` secret.

## Reproducibility

Every live run records:

```text
run ID
provider
model
prompt version + SHA-256
benchmark version + SHA-256
schema version + SHA-256
git commit
Python version
UTC timestamp
fingerprint ID
```

Per-case traces record:

```text
source prompt
ParsedEngineeringIntent
EngineeringSpec
ValidationReport
failure classification
case metrics
```

## Current status

v0.2.4 achieves a perfect score on the **known development benchmark** while preserving all hard safety gates.

That is the end of the known-benchmark calibration phase.

### Next validation

Before `prompt_v2` or any generalization claim, the next step is a **frozen holdout benchmark with unseen wording and combinations**.

If the holdout exposes genuine parser failures, prompt changes will be minimal and evidence-driven.

---

GenCAD-AI is deliberately built as an engineering-control system around probabilistic AI rather than as a demo that assumes model output is engineering truth.
