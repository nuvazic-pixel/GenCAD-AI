# geometry_demo_001 — v0.3.0 Proof-to-Geometry Bridge

First successful live geometry export controlled by the GenCAD-AI evidence and CAD release boundaries.

- System version: `0.3.0`
- Generator: `pipe_saddle_bracket_v1`
- Layout rule: `PIPE_SADDLE_LAYOUT_V1`
- GitHub Actions run: `35437102080`
- Git commit: `88d070f392fa4a2c841bbd952b03867226c13095`
- Artifact ID: `10583390015`
- Artifact SHA-256: `2e210e91dacc4ebd4c3b5e3ad9d8836551e6b211ff933b3b2b374e0e9ca9c25f`

## A/B result

### Scenario A — blocked

Source evidence:

```text
"Ø42 pipe"
```

The raw intent intentionally emulates the unsupported unit behavior observed in the live EvidenceGuard challenge:

```text
pipe_diameter = 42 mm
source_text = "Ø42 pipe"
```

Result:

```text
SourceEvidenceGuard
→ strip unsupported "mm"

EngineeringSpec
→ pipe_diameter = UNKNOWN

Validation
→ NEEDS_CLARIFICATION

CADReleaseGate
→ FAIL

STEP generated = NO
STL generated  = NO
```

### Scenario B — generated

Source evidence:

```text
"Ø42 mm pipe"
```

Result:

```text
SourceEvidenceGuard
→ no finding

EngineeringSpec
→ complete

Validation
→ READY

CADReleaseGate
→ PASS

STEP generated = YES
STL generated  = YES
```

Released geometry parameters:

```text
pipe_diameter_mm    42.0
wall_thickness_mm    4.0
bracket_width_mm    30.0
base_thickness_mm    6.0
hole_count            2
hole_diameter_mm      6.6
```

## Geometry sanity check

Independent STL inspection after the run:

```text
watertight     true
vertices       972
faces          1952
volume_mm3     28472.85
extents_mm     76.4 × 30.0 × 51.99
```

The 76.4 mm base length is deterministically produced by `PIPE_SADDLE_LAYOUT_V1`; it is not inferred by the LLM or claimed to come from an engineering standard.

## Provenance

The Actions artifact contains:

```text
demo_summary.json
scenario_A_blocked/trace.json
scenario_B_generated/trace.json
scenario_B_generated/pipe_saddle_bracket.step
scenario_B_generated/pipe_saddle_bracket.stl
scenario_B_generated/generation_manifest.json
```

The manifest hashes both the EngineeringSpec and CAD release decision, records the released parameters and evidence states, and includes SHA-256 hashes for the STEP and STL artifacts.

The binary geometry is kept in the GitHub Actions artifact rather than committed to the source tree.
