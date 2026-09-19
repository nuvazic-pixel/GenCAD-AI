# GenCAD-AI Evaluation Playbook

The original v2.0 protocol was frozen for the v0.2.2 development benchmark. The rules below preserve that history and add the evidence-integrity and holdout discipline learned through v0.2.6.

Prompt changes are not accepted by intuition alone; they require evidence that a failure remains after deterministic controls have been examined.

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

- Unsafe Proceed
- Critical Hallucinations
- Critical Semantic Errors
- Positive-Control Regressions

If any hard gate is breached, the raw run fails. Human adjudication may explain the cause, but it does not retroactively change the official raw gate.

## 3. Soft targets

These guide optimization but do not override a hard-gate failure:

- Explicit Fact Recall >= 95%
- Uncertainty Preservation >= 95%
- Correct READY Rate >= 90%
- Hallucinated Field Rate <= 1%

## 4. Evidence Integrity boundary

From v0.2.6 onward, evaluation distinguishes **raw model behavior** from **engineering-safe accepted evidence**.

```text
Natural language
      ↓
LLM
      ↓
Raw ParsedEngineeringIntent
      ↓
SourceEvidenceGuard
      ↓
Guarded ParsedEngineeringIntent
      ↓
Normalizer / TerminologyResolver
      ↓
EngineeringSpec
      ↓
Validator
```

The raw parser output is immutable run evidence. Guard actions never erase it.

Each per-case trace should preserve:

```text
raw_parsed_intent
parsed_intent
source_evidence_guard
engineering_spec
validation_report
failures
metrics
```

### Field-level evidence rule

For engineering units, evidence is checked against the field's own `source_text`.

An unrelated unit elsewhere in the prompt must not justify a model-provided unit.

Example:

```text
prompt:
"Ø42 pipe with 4 mm wall thickness"

raw parser:
pipe_diameter = 42 mm
source_text = "Ø42 pipe"

guard:
"mm" is absent from this field-level source phrase
→ strip unsupported unit
→ no physical length can be produced
```

The full prompt may be retained for audit but is deliberately not sufficient evidence for that unit.

## 5. Deterministic derivation and provenance

The LLM must never produce `DERIVED`.

A downstream deterministic rule may produce a derived engineering value only when:

1. the input evidence is explicit and accepted,
2. the rule is deterministic,
3. the rule has a stable identifier,
4. provenance records the rule and supporting source.

Example:

```text
"M6 screws through two 6.6 mm clearance holes"

CONFIRMED physical fastener = M6
        ↓
ASSEMBLY_ASSOCIATION_V1
        ↓
DERIVED associated fastener designation = M6
```

This does not derive a hole diameter from M6.

## 6. Terminology normalization

Surface wording and engineering identity are separate concerns.

Examples of deterministic equivalence may include:

```text
pipe bracket
Halter
Rohrhalter
Pipe clamp bracket
    → pipe_bracket

steel
Stahl
    → steel
```

A terminology miss should not automatically be treated as a parser failure if the raw model correctly preserved the source term.

## 7. Root-cause precedence

Before changing a prompt, every observed failure should be adjudicated in this order:

1. **Ground-truth / evaluator question**  
   Is the expected label actually unambiguous and is the evaluator measuring the intended behavior?

2. **Deterministic system question**  
   Did normalization, terminology, evidence guarding, ontology, validation or a deterministic relation rule fail despite correct source extraction?

3. **Parser/model question**  
   Did the model miss explicit source evidence, promote uncertainty, invent unsupported evidence, or create a semantic confusion that survives deterministic protections?

Prompt changes belong only to category 3 after categories 1 and 2 have been ruled out.

## 8. Holdout discipline

A holdout is frozen before its live run.

After the run:

- do not modify its prompts or ground truth to improve the observed score;
- do not overwrite its raw artifact or release-gate result;
- record human adjudication in a separate document;
- fix the system in a new version;
- validate remediation on a **new** benchmark/run.

A failed holdout remains failed even when later review proves that one failure came from the evaluator itself.

This is intentional: the historical artifact records what the system and evaluator actually did at that time.

### No official rerun after inspection

Once a holdout has been inspected, rerunning the same set as the official proof of remediation is not considered independent validation.

Regression tests may reproduce individual cases deterministically, but generalization claims require new unseen cases.

## 9. Meaningful improvement

For small benchmarks, percentage changes alone are too coarse.

A candidate has meaningful improvement when:

1. at least one previously failing behavior is demonstrably fixed,
2. no new hard-gate failure is introduced,
3. no positive-control case regresses,
4. the change is causally attributable to the intended layer.

At 100+ cases, interval estimates and additional statistical analysis may be added.

## 10. Experiment fingerprint

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

## 11. Iteration workflow

```text
freeze benchmark / holdout
      ↓
freeze prompt
      ↓
run live evaluation
      ↓
preserve raw artifact + fingerprint
      ↓
FailureClassifier
      ↓
human root-cause adjudication
      ↓
minimal corrective change
      ↓
deterministic regression tests
      ↓
new unseen evaluation set
      ↓
ReleaseGate
      ↓
accept / investigate
```

## 12. Historical evidence

### Development calibration

- `baseline_001` — v0.2.2 — FAIL
- `baseline_002` — v0.2.3 — PASS
- `baseline_003` — v0.2.4 — PASS / 100% known development set

### Generalization evidence

- `holdout_001` — v0.2.5 — raw FAIL
- `holdout_002` — v0.2.6 — raw FAIL from one deterministic relation-parser coverage gap

Both holdout raw results remain immutable. Their human adjudications are stored beside the evidence under `reports/`.

## 13. Current stop / continuation rule

Do not create `prompt_v2` merely because a holdout fails.

Continue deterministic remediation while failures are attributable to evidence control, normalization, terminology, ontology or evaluator defects.

Create a prompt revision only when a genuine parser/model failure survives those controls.

For a future stabilization claim, require:

- all hard gates pass,
- utility targets are acceptable,
- a new unseen evaluation set passes,
- no known positive-control regression exists,
- evidence-integrity interventions are auditable,
- at least one live case has exercised critical guard behavior when that guard is part of the claimed safety story.
