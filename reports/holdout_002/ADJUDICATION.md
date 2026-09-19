# Human Adjudication — holdout_002

This review does not modify the frozen benchmark, raw model output, or official FAIL result.

## J06

Source:

`zwei M6 Schrauben durch zwei 6,6 mm Durchgangsbohrungen`

Model output:

- physical fastener designation = `M6`
- physical fastener count = `2`
- associated fastener designation = `M6`
- hole count = `2`
- hole diameter = `6.6 mm`
- hole semantics = `Durchgangsbohrungen`

All values are supported by the source.

The evaluator nevertheless classified `associated_fastener_designation=M6` as a critical hallucination because the deterministic assembly-evidence rule recognized English `holes` and standalone German `Bohrungen`, but not the compound word `Durchgangsbohrungen`.

Root cause: **deterministic relation-parser coverage gap**, not unsupported model invention.

## Other findings

- J01/J02 prove the multilingual terminology aliases resolve `Rohrhalter`, `Stahl`, and `Kunststoff` correctly downstream.
- J03/J04 correctly preserve missing units for `Ø54` and `Ø48`; SourceEvidenceGuard made no intervention because the raw model output was already evidence-safe.
- All six READY cases reached READY.
- Unsafe Proceed remained 0%.
- Explicit Fact Recall was 100%.

## Decision

Keep holdout_002 frozen and official gate = FAIL.

Patch the deterministic assembly-evidence recognizer generically for German compound hole words such as:

- `Durchgangsbohrung(en)`
- `Gewindebohrung(en)`
- `Befestigungsbohrung(en)`

Do not change prompt_v1.
