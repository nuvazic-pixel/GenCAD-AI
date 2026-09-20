# STEP Byte Variance — geometry_reproducibility_001

The five repeated builds produced identical canonical geometry fingerprints but different STEP file SHA-256 values.

A direct header comparison showed non-geometric serialization changes.

Example:

```diff
-FILE_NAME('Open CASCADE Shape Model','2026-09-20T13:52:49',...)
+FILE_NAME('Open CASCADE Shape Model','2026-09-20T13:52:50',...)

-'Open CASCADE STEP translator 7.9 1'
+'Open CASCADE STEP translator 7.9 2'
```

These metadata differences are sufficient to alter the file hash without demonstrating a geometry difference.

For v0.3.2:

- STEP byte hash is diagnostic provenance
- STL byte hash is diagnostic provenance
- canonical mesh fingerprint is the geometry reproducibility identity

Byte-identical STEP serialization is not required for a reproducibility PASS.
