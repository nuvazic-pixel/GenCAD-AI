# geometry_verification_001 — v0.3.1 Geometry Verification

First end-to-end proof that generated CAD is not releasable until the exported artifact itself passes deterministic verification.

- System version: `0.3.1`
- GitHub Actions run: `35510819675`
- Git commit: `338d21e8d060202b9f4051bab97a2b836fac66cb`
- Artifact ID: `10604949794`
- Artifact SHA-256: `bf09f1df468e380fee31091f1970809b7a3d4175573adf6ca89a94626eeef1f7`

## Verification boundary

```text
ReleasedBracketParameters
        ↓
CadQuery
        ↓
candidate STEP / STL
        ↓
GeometryVerifier
        ↓
CADArtifactReleaseGate
   ┌────────┴────────┐
 FAIL              PASS
   ↓                  ↓
quarantine/        released/
```

The verifier inspects the exported STL artifact rather than trusting CadQuery's internal object.

## Good candidate

Expected:

```text
hole_count = 2
pipe_diameter = 42.0 mm
wall = 4.0 mm
bbox = 76.4 × 30.0 × 52.0 mm
```

Measured:

```text
solid_valid             true
watertight              true
positive_volume         true
volume_mm3              28472.85298553525

detected_hole_count     2
hole_count_match        true

measured_bbox_mm        76.4000015 × 30.0 × 51.9922295
dimensions_match        true

measured_pipe_diameter  41.9956487 mm
pipe_delta              -0.0043513 mm
pipe_opening_match      true

measured_wall           3.9944051 mm
wall_delta              -0.0055949 mm
wall_check_passed       true
```

Geometry fingerprint:

```text
sha256:49da1af3e1ff71e08b47e1904117ad2b95e8852833ecfeeac9b3b438a2c14181
```

Artifact release:

```text
PASS
→ released/
```

File hashes:

```text
STEP  62e5347370ea13704b850abfa030c49d4299e9f0aad1963b6229e92f35247da6
STL   dceb932b537ff89cbacae6b7aaba0d50cfeb96af8fdd12e36faf2939555cdd73
```

## Fault-injected candidate

The same released parameters were used, but the generator fault intentionally omitted the right mounting hole.

The resulting artifact is still:

```text
solid_valid      true
watertight       true
positive_volume  true
```

and still passes:

- bounding dimensions
- pipe opening diameter
- wall geometry

But:

```text
expected_hole_count = 2
detected_hole_count = 1

failed_rules:
  HOLE_COUNT_MISMATCH
```

Geometry fingerprint:

```text
sha256:a31c46c184cab2f5a663ba5296c8f761ae582a12e635ffc1899957a621949dea
```

Artifact release:

```text
FAIL
→ quarantine/
```

File hashes:

```text
STEP  7c20163346f0a854ce6aaf34c04c40c0ddb03c0b3e653f8a7fea0c1d2c2f5a4b
STL   3bff44f9837af8a0bf3e47a5666bc26dd26fd8b1ebc62730f1325aca611274b2
```

## Result

The demo proves that **topological validity is not enough**.

A candidate can be watertight, have positive volume, correct outer dimensions, correct pipe opening and correct wall geometry, yet still be wrong relative to the released engineering parameters.

GenCAD-AI therefore treats:

```text
CadQuery output ≠ releasable CAD artifact
```

Only geometry that survives deterministic artifact verification may cross into `released/`.
