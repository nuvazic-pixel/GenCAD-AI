# geometry_reproducibility_001 — v0.3.2 Deterministic Geometry Reproducibility

First repeated-build proof that identical released engineering parameters produce one stable canonical geometry fingerprint.

- System version: `0.3.2`
- Generator: `pipe_saddle_bracket_v1`
- GitHub Actions run: `35514763762`
- Git commit: `c1adaa79278b1bdab3ada893d8a93f60097b1426`
- Artifact ID: `10606646618`
- Artifact SHA-256: `b4c2ab8f3951708705356a3c56dd5dab81b963d1ab8904ed1fbc52237624fb32`
- Independent repeated builds: `5`

## Released parameters

```text
pipe_diameter_mm      42.0
wall_thickness_mm      4.0
bracket_width_mm      30.0
base_thickness_mm      6.0
hole_count              2
hole_diameter_mm        6.6
```

Released-parameters hash:

```text
sha256:dfb57cd99095436fde91439f2eb229c07e3f34c01641d97c2c178d72102041a3
```

Deterministic layout hash:

```text
sha256:0dfcfd956b8e0e29680d556c4764f3158433db12f26d620f46c305c66174edd3
```

## Repeated-build result

All five independent CadQuery builds:

- passed GeometryVerifier
- passed CADArtifactReleaseGate
- measured the same volume
- measured the same bounding box
- produced the same canonical geometry fingerprint

Canonical geometry fingerprint:

```text
sha256:49da1af3e1ff71e08b47e1904117ad2b95e8852833ecfeeac9b3b438a2c14181
```

Result:

```text
repeat_count                 5
unique geometry fingerprints 1
all_verified                 true
all_releasable               true
fingerprints_match           true
failed_rules                 []
passed                       true
```

## Byte-level behavior

The STL exports were byte-identical across all five builds:

```text
STL SHA-256
sha256:dceb932b537ff89cbacae6b7aaba0d50cfeb96af8fdd12e36faf2939555cdd73

stl_bytes_identical = true
```

The STEP exports were **not** byte-identical:

```text
unique STEP SHA-256 values = 5
step_bytes_identical = false
```

Inspection of the STEP headers showed expected serialization metadata differences, including:

- `FILE_NAME` timestamps changing between exports
- Open CASCADE translator product labels incrementing between exports

Therefore STEP byte equality is deliberately **not** used as the geometry identity gate.

## Sensitivity control

A sixth build changed exactly one released geometry parameter:

```text
hole_diameter_mm
6.6 → 7.0
```

Sensitivity-control geometry fingerprint:

```text
sha256:795d0a9b7ca3029f660e27809add2a3627b7812380eb6f8436e4975d4117c2dc
```

It differs from the repeated-build fingerprint:

```text
sensitivity_control_differs = true
```

This checks that the canonical fingerprint is not simply insensitive to a meaningful geometry change.

## Interpretation

v0.3.2 demonstrates **intra-environment deterministic geometry reproducibility** for `pipe_saddle_bracket_v1` under the tested generator version, tessellation settings and dependency environment.

It does not yet claim cross-platform or cross-CAD-kernel fingerprint stability.

The release identity rule is:

```text
same released parameters
        ↓
same verified canonical geometry fingerprint
```

not:

```text
same STEP bytes
```

The complete artifact contains all five STEP/STL replica pairs, per-build traces, the sensitivity-control geometry, and the full reproducibility report.
