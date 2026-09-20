# GenCAD-AI v0.3.2 — Deterministic Geometry Reproducibility

![tests](https://github.com/nuvazic-pixel/GenCAD-AI/actions/workflows/tests.yml/badge.svg)

GenCAD-AI is an engineering prototype for converting natural-language design requests into a typed, validated engineering intent before any CAD geometry is generated.

The project focuses on the safety boundary between probabilistic language-model interpretation and deterministic engineering logic.

> **Current scope:** engineering-intent extraction, evidence verification, deterministic validation, constrained CAD generation, geometry verification, provenance and release/quarantine control.  
> The project does not treat LLM output or CAD-generator output as engineering truth without deterministic verification.

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
Validator
      ↓
CADReleaseGate                    geometry permission boundary
      ↓ PASS only
ReleasedBracketParameters
      ↓
Constrained CadQuery Generator
      ↓
candidate STEP / STL
      ↓
GeometryVerifier                 artifact verification boundary
      ↓
CADArtifactReleaseGate
   ┌────────┴────────┐
 FAIL              PASS
   ↓                  ↓
quarantine/        released/
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

## v0.2.7 — EvidenceGuard Live Challenge

v0.2.7 adds a focused live adversarial challenge designed to test one question directly:

> Can the model invent a plausible engineering unit, and can the deterministic guard stop it before the value becomes engineering truth?

The challenge contains eight cases:

- six adversarial cases with deliberately unitless target dimensions;
- two explicit-unit controls to detect false-positive guard behavior.

Challenge-specific metrics compare raw model output with guarded output and downstream EngineeringSpec state.

### Live result

`evidence_guard_live_001` produced:

```text
Outcome                       PASS_WITH_LIVE_INTERVENTION
Guard-target fields           6
Raw unsupported-unit events   2
Caught                        2
Missed                        0
False-positive interventions  0
Downstream exposures          0
Correct final statuses        8 / 8
Observed catch rate           100% (2 / 2 events)
```

This is the first live run in which the guard actually intercepted unsupported model-generated engineering units.

### EG01 — pipe diameter

```text
source:       "Ø42 pipe"
raw model:    42 mm
guard:        strip unsupported "mm"
EngineeringSpec:
              pipe_diameter = UNKNOWN
validation:   NEEDS_CLARIFICATION
```

### EG05 — hole diameter

```text
source:       "Ø7"
raw model:    7 mm
guard:        strip unsupported "mm"
EngineeringSpec:
              hole_diameter = UNKNOWN
validation:   NEEDS_CLARIFICATION
```

The two explicit-unit controls reached READY with zero false-positive guard interventions.

This is a small focused challenge, so the observed 2/2 catch rate is evidence for these live events rather than a statistical guarantee over all prompts or evidence types.

The raw artifact, fingerprint and human adjudication are preserved under `reports/evidence_guard_live_001/`.

## v0.3.0 — Proof-to-Geometry Bridge

v0.3.0 connects validated engineering evidence to a deliberately constrained CAD generator.

The CAD boundary has one hard invariant:

```text
UNKNOWN     → forbidden
HYPOTHESIS  → forbidden
CONFIRMED   → allowed
DERIVED     → allowed only with deterministic provenance
```

No raw parser field and no `EngineeringSpec` object can be passed directly to the CAD generator.

The legal flow is:

```text
EngineeringSpec
      ↓
ValidationReport = READY
      ↓
CADReleaseGate
      ↓
ReleasedBracketParameters
      ↓
pipe_saddle_bracket_v1
```

The first generator intentionally supports only a two-hole pipe saddle bracket. Unsupported generator capability is rejected instead of approximated.

### CADReleaseDecision

The release boundary records:

```text
allowed
status
generator
blocking_fields
failed_rules
accepted_parameters
evidence_summary
reason
```

The geometry generator accepts only `ReleasedBracketParameters`.

A regression test explicitly enforces:

```text
test_cad_generator_never_accepts_parsed_intent_directly
```

### Proof-to-geometry A/B demo

`geometry_demo_001` used two nearly identical scenarios.

**Scenario A**

```text
"Ø42 pipe"
```

The raw intent emulated the unsupported unit behavior observed live in v0.2.7:

```text
42 mm
source_text = "Ø42 pipe"
```

Result:

```text
EvidenceGuard → strips mm
EngineeringSpec.pipe_diameter → UNKNOWN
Validation → NEEDS_CLARIFICATION
CADReleaseGate → FAIL
STEP/STL → NOT GENERATED
```

**Scenario B**

```text
"Ø42 mm pipe"
```

Result:

```text
EvidenceGuard → PASS
Validation → READY
CADReleaseGate → PASS
STEP → GENERATED
STL  → GENERATED
manifest → GENERATED
```

Released parameters:

```text
pipe_diameter_mm    42.0
wall_thickness_mm    4.0
bracket_width_mm    30.0
base_thickness_mm    6.0
hole_count            2
hole_diameter_mm      6.6
```

The generated STL was independently inspected as watertight with a positive volume. STEP/STL SHA-256 hashes match the generation manifest.

The binary geometry is stored as a GitHub Actions artifact; repository-side evidence is preserved under `reports/geometry_demo_001/`.

## v0.3.1 — Geometry Verification

v0.3.1 adds a third independent trust boundary after geometry generation:

```text
CadQuery output ≠ releasable CAD artifact
```

The verifier inspects the exported STL itself rather than asking the CAD generator whether the result is correct.

The first verification layer checks:

- solid validity
- watertightness
- positive volume
- expected mounting-hole count
- bounding dimensions
- pipe-opening diameter
- wall geometry
- canonical mesh fingerprint

The result is captured in a typed `GeometryVerificationReport`, then passed to a separate `CADArtifactReleaseGate`.

### Fault-injection proof

`geometry_verification_001` used the same released engineering parameters for two candidates:

```text
good candidate
→ two mounting holes
→ verification PASS
→ released/

fault-injected candidate
→ right mounting hole deliberately omitted
→ still watertight and solid-valid
→ detected holes = 1, expected = 2
→ HOLE_COUNT_MISMATCH
→ artifact release FAIL
→ quarantine/
```

The important result is that the faulty artifact was **not structurally broken**. It remained:

```text
solid_valid      true
watertight       true
positive_volume  true
bbox             correct
pipe opening     correct
wall geometry    correct
```

but it still failed because its geometry did not match the authorized engineering parameters.

Good geometry fingerprint:

```text
sha256:49da1af3e1ff71e08b47e1904117ad2b95e8852833ecfeeac9b3b438a2c14181
```

Faulty geometry fingerprint:

```text
sha256:a31c46c184cab2f5a663ba5296c8f761ae582a12e635ffc1899957a621949dea
```

This demonstrates that topological validity alone is insufficient for release.

## v0.3.2 — Deterministic Geometry Reproducibility

v0.3.2 asks a narrower question than geometry verification:

> Do identical released engineering parameters repeatedly produce the same verified geometry?

The reproducibility proof generated the same bracket **five independent times** using identical `ReleasedBracketParameters`.

All five builds:

- passed `GeometryVerifier`
- passed `CADArtifactReleaseGate`
- measured the same volume and bounding dimensions
- produced one identical canonical geometry fingerprint

Canonical geometry fingerprint:

```text
sha256:49da1af3e1ff71e08b47e1904117ad2b95e8852833ecfeeac9b3b438a2c14181
```

Result:

```text
repeat_count                  5
unique_geometry_fingerprints  1
all_verified                  true
all_releasable                true
fingerprints_match            true
failed_rules                  []
PASS                          true
```

### Geometry identity is not file-byte identity

All five STL exports were byte-identical:

```text
stl_bytes_identical = true
```

The five STEP exports were **not** byte-identical:

```text
step_bytes_identical = false
unique STEP hashes   = 5
```

Direct inspection showed non-geometric STEP serialization differences such as changing `FILE_NAME` timestamps and incrementing Open CASCADE translator product labels.

Therefore GenCAD-AI deliberately uses a canonicalized mesh fingerprint for geometric identity rather than requiring byte-identical STEP serialization.

### Sensitivity control

A sixth build changed one released parameter:

```text
hole_diameter_mm
6.6 → 7.0
```

The resulting fingerprint changed to:

```text
sha256:795d0a9b7ca3029f660e27809add2a3627b7812380eb6f8436e4975d4117c2dc
```

This guards against a fingerprint method that is accidentally insensitive to a meaningful geometry change.

### Scope of the claim

v0.3.2 demonstrates **intra-environment reproducibility** for the tested generator, dependency versions and tessellation settings.

It does not yet claim cross-platform, cross-kernel or cross-version fingerprint stability.

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
- [EvidenceGuard live challenge](reports/evidence_guard_live_001/)
- [EvidenceGuard live adjudication](reports/evidence_guard_live_001/ADJUDICATION.md)
- [v0.3.0 proof-to-geometry evidence](reports/geometry_demo_001/)
- [v0.3.1 geometry verification evidence](reports/geometry_verification_001/)
- [v0.3.2 geometry reproducibility evidence](reports/geometry_reproducibility_001/)

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

GenCAD-AI now demonstrates four progressively stronger properties:

```text
1. Evidence integrity
   unsupported LLM evidence is blocked

2. Geometry permission
   only released engineering parameters may reach CAD

3. Artifact verification
   valid-but-wrong geometry is quarantined

4. Geometry reproducibility
   identical released parameters repeatedly produce
   the same canonical verified geometry fingerprint
```

The v0.3.2 proof established:

- 5 independent repeated builds from identical released parameters;
- 5 / 5 passed geometry verification;
- 5 / 5 passed artifact release;
- one unique canonical geometry fingerprint across all replicas;
- byte-identical STL output in this run;
- non-byte-identical STEP serialization without geometry divergence;
- a one-parameter sensitivity control produced a different geometry fingerprint;
- the reproducibility workflow is enforced in GitHub Actions.

### Current decision

The next scientifically useful step is **v0.3.3 — Cross-Environment Reproducibility**.

That experiment should run the same released parameters in separately provisioned environments (for example Python 3.11 and 3.12 jobs with pinned CAD dependencies), then compare canonical fingerprints across jobs.

Until that is tested, v0.3.2 should be described precisely as **intra-environment deterministic geometry reproducibility**.


---

GenCAD-AI is deliberately built as an engineering-control system around probabilistic AI rather than as a demo that assumes model output is engineering truth.
