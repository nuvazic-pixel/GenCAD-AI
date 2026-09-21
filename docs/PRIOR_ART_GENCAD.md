# Prior Art Note — GenCAD

GenCAD-AI's Verified CAD Feature Language was independently implemented after reviewing prior generative-CAD research, including:

- **GenCAD — Image-conditioned Computer-Aided Design Generation with Transformer-based Contrastive Representation and Diffusion Priors**
- Repository reviewed: `ferdous-alam/GenCAD`

The referenced project demonstrates a compact CAD command representation with concepts such as line, arc, circle, solid delimiters, extrusion operations and boolean feature composition.

GenCAD-AI uses that work as **conceptual prior art only**.

No source code from the referenced repository is copied into GenCAD-AI's feature-language implementation.

The design goal here is different:

```text
AI / upstream system proposes feature intent
        ↓
feature parameters retain evidence state
        ↓
FeatureProgramGate
        ↓
VerifiedCADFeatureProgram
        ↓
deterministic compiler
        ↓
geometry verification
```

The reviewed GitHub repository did not expose an explicit repository license through GitHub metadata at the time of review. For that reason, GenCAD-AI deliberately uses an independent implementation rather than importing its source.

GenCAD-AI's feature language currently defines its own typed primitives and evidence semantics and should continue to evolve independently.
