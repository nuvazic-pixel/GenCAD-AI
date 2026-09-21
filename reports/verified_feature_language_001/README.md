# verified_feature_language_001 — v0.4.0

First end-to-end proof of an evidence-bound intermediate CAD feature language.

- System version: `0.4.0`
- GitHub Actions run: `35631825841`
- Git commit: `97508257b3688d49f8780ccdd6589c227eb1b3b5`
- Artifact ID: `10653549654`
- Artifact SHA-256: `d8ab3bab695ca6abd9c9a87348b728d60d07840964022ce44e31de2597429434`

## Trust chain

```text
SourceEvidenceGuard
      ↓
EngineeringSpec
      ↓
CADReleaseGate
      ↓
CADFeatureProgram
      ↓
FeatureProgramGate
      ↓
VerifiedCADFeatureProgram
      ↓
CadQuery compiler
      ↓
GeometryVerifier
      ↓
CADArtifactReleaseGate
```

## Released program

The released program contains four explicit CAD features:

```text
base_plate
pipe_saddle
mounting_hole_left
mounting_hole_right
```

Feature gate:

```text
passed              true
blocked_features    []
blocked_parameters  []
failed_rules        []
```

The compiled geometry passed the existing geometry verifier and artifact release gate.

Canonical geometry fingerprint:

```text
sha256:49da1af3e1ff71e08b47e1904117ad2b95e8852833ecfeeac9b3b438a2c14181
```

This matches the previously verified bracket geometry fingerprint, showing that the new feature-language path preserves the validated shape.

## Blocked proposal

A second program deliberately removes the evidence-backed diameter of the right mounting hole:

```text
mounting_hole_right.diameter_mm
state = UNKNOWN
value = null
```

FeatureProgramGate result:

```text
passed = false
blocked_features:
  - mounting_hole_right

blocked_parameters:
  - mounting_hole_right.diameter_mm

failed_rules:
  - UNTRUSTED_FEATURE_PARAMETER
```

No verified program is produced, therefore geometry compilation is not permitted.

## 3D Evidence Viewer

The artifact contains two standalone HTML viewers:

```text
released/viewer.html
blocked_proposal/viewer.html
```

Each viewer embeds the STL and feature-program JSON in the HTML artifact.

Feature/parameter evidence is displayed using:

```text
CONFIRMED   green
DERIVED     amber
HYPOTHESIS  purple
UNKNOWN     red
```

Selecting a feature shows its parameters, source fields, deterministic rule IDs and evidence notes.

The viewer uses Three.js from a public CDN; the CAD/evidence payload itself is embedded in the HTML.
