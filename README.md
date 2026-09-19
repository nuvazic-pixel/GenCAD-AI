# GenCAD-AI v0.2.6 — Evidence Integrity Layer

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
Raw ParsedEngineeringIntent      probabilistic boundary
      ↓
SourceEvidenceGuard
      ↓
Guarded ParsedEngineeringIntent  evidence boundary
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

## v0.2.6 — Evidence Integrity Layer

The holdout evaluation exposed a failure mode that prompt instructions alone cannot safely control: the model may attach an engineering unit that is not supported by the cited source phrase.

v0.2.6 adds a deterministic `SourceEvidenceGuard` between parser output and engineering normalization.

```text
raw model output
    ↓
field-level evidence check
    ↓
unsupported unit?
    ├── yes → strip unit, preserve raw value, record finding
    └── no  → pass through unchanged
```

Example:

```text
source_text = "Ø42 pipe"
raw_value   = 42
raw_unit    = "mm"

SourceEvidenceGuard:
"mm" is not supported by source_text

        ↓

guarded raw_value = 42
guarded raw_unit  = null

        ↓

no physical LengthValue can be produced
        ↓
NEEDS_CLARIFICATION
```

The full prompt is deliberately **not** used as unit evidence. A separate phrase such as `4 mm wall` must not justify `Ø42 → 42 mm`.

Every live case trace now preserves both:

```text
raw_parsed_intent
parsed_intent             ← guarded intent
source_evidence_guard
engineering_spec
validation_report
failures
metrics
```

This keeps model behavior auditable while preventing unsupported evidence from reaching engineering truth.

### Multilingual deterministic terminology

v0.2.6 also expands deterministic terminology resolution for phrases observed outside the development benchmark, including examples such as:

```text
Halter / Rohrhalter / Pipe clamp bracket → pipe_bracket
Stahl                                  → steel
Kunststoff                             → polymer
Durchgangsbohrung(en)                  → clearance
Gewindebohrung(en)                     → threaded
```

### Explicit assembly association

When the source explicitly relates a physical fastener to a hole, the deterministic layer may create an associated designation using rule:

```text
ASSEMBLY_ASSOCIATION_V1
```

For example:

```text
"M6 screws through two 6.6 mm clearance holes"

physical fastener designation = CONFIRMED M6

        ↓ explicit source relation

associated fastener designation = DERIVED M6
```

The derived value carries deterministic provenance. The LLM itself is still prohibited from producing `DERIVED` evidence.

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

### Frozen holdout_001

v0.2.5 added a separate 15-case holdout that was not used during the previous calibration loop.

| Run | Cases | Recall | Hallucination | Semantic confusion | Unsafe proceed | Correct READY | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| holdout_001 | 15 | 94.32% | 0.74% | 0% | 0% | 66.67% | FAIL |

The holdout exposed real generalization gaps that were hidden by the perfect development-benchmark score.

Human adjudication found three distinct categories:

- terminology coverage gaps such as `Halter`, `Rohrhalter`, `Pipe clamp bracket`, and `Stahl`
- one genuine evidence-boundary issue where `Ø42` was assigned an unsupported `mm` unit
- one holdout ground-truth ambiguity involving simultaneous physical-fastener and hole-associated M6 semantics

The raw holdout remains frozen and the official gate remains FAIL. Human review is documented separately rather than rewriting the observed result.

### Frozen holdout_002

After the Evidence Integrity Layer was implemented, a second completely separate 15-case holdout was frozen and run.

| Run | Cases | Recall | Hallucination | Semantic confusion | Unsafe proceed | Correct READY | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| holdout_002 | 15 | **100%** | 0.84% | 0% | **0%** | **100%** | **FAIL** |

The raw hard-gate failure came from one case, J06:

```text
"M6 Schrauben durch ... Durchgangsbohrungen"
```

The model output was source-supported, but the deterministic relation recognizer did not yet understand the German compound noun `Durchgangsbohrungen`. The raw run therefore classified the associated M6 designation as a critical hallucination.

That result remains officially **FAIL**. Post-run human adjudication identified it as a deterministic evaluator coverage gap, and the recognizer was subsequently generalized to compound `*bohrung/*bohrungen` words. The frozen holdout itself was not modified or rerun as if the original result had passed.

Two additional points matter:

- multilingual terminology resolution worked on unseen wording such as `Rohrhalter`, `Stahl`, and `Kunststoff`;
- the SourceEvidenceGuard was **not triggered live** in holdout_002 because the model correctly left `Ø54` and `Ø48` unitless. Its interception behavior is covered by deterministic CI tests, but a future live evaluation should include a naturally occurring guard intervention before claiming live guard effectiveness.

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
- [holdout_001 evidence](reports/holdout_001/)
- [holdout_001 human adjudication](reports/holdout_001/ADJUDICATION.md)
- [holdout_002 evidence](reports/holdout_002/)
- [holdout_002 human adjudication](reports/holdout_002/ADJUDICATION.md)

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

The project now has three distinct layers of evidence:

```text
known development benchmark
    → 100% after calibration

holdout_001
    → exposed terminology, evidence-boundary and adjudication gaps

v0.2.6 Evidence Integrity Layer
    → deterministic remediation

holdout_002
    → 100% recall
    → 100% READY accuracy
    → 0% unsafe proceed
    → raw FAIL from one deterministic relation-parser coverage gap
```

That last gap has been patched and regression-tested without rewriting or retroactively passing the frozen holdout.

### Current decision

`prompt_v1` remains frozen.

There is still no strong evidence that prompt tuning is the highest-value intervention. The project has repeatedly shown that deterministic evidence controls, ontology and evaluation quality matter more than prompt changes.

The next live experiment should be a **new** frozen evaluation set, not a rerun of holdout_001 or holdout_002. It should specifically seek cases that can naturally trigger the SourceEvidenceGuard and new multilingual/assembly variants.

A prompt_v2 should be created only if a genuine parser failure survives those deterministic controls.

---

GenCAD-AI is deliberately built as an engineering-control system around probabilistic AI rather than as a demo that assumes model output is engineering truth.
