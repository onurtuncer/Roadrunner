# Architecture Decision Records

This folder holds Architecture Decision Records (ADRs): short documents
capturing an architecturally significant decision, its context, and its
consequences. New ADRs are added when a decision is made; existing ADRs
are never rewritten (a superseding decision gets a new ADR that marks the
old one `Superseded`).

Format: one file per decision, `NNNN-kebab-title.md`, each with
**Status / Context / Decision / Consequences**.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-one-way-design-pipeline.md) | One-way design pipeline | Accepted (read with 0003) |
| [0002](0002-all-physics-in-src-no-magic-numbers.md) | All physics in `src/`; no magic numbers in Python | Accepted (read with 0003) |
| [0003](0003-inherit-tailsitter-conventions.md) | Inherit the tailsitter conventions; local amendments to 0001/0002 | Accepted |
| [0004](0004-scope-propulsion-of-the-baseline-vehicle.md) | Scope: propulsion of the baseline vehicle, public sources only | Accepted |
| [0005](0005-evidence-ledger-with-provenance.md) | Evidence ledger: provenance and a tier on every external number | Accepted |
| [0006](0006-inverse-problem-feasible-family.md) | Reverse engineering is an inverse problem: report a feasible family | Accepted |
| [0007](0007-geometry-from-scaled-imagery.md) | Geometry from scaled public imagery, as measured intervals | Accepted |
| [0008](0008-vehicle-model-as-requirements-generator.md) | The vehicle model is a requirements generator, no more | Accepted |
| [0009](0009-operating-points-and-cycle-design-point.md) | Four operating points; the cycle design point is static launch | Accepted |
| [0010](0010-in-house-cycle-model-and-technology-levels.md) | In-house SI cycle model; technology levels from a reference-engine database | Accepted |
| [0011](0011-installation-and-thrust-vectoring-as-losses.md) | Installation and thrust vectoring enter as bounded loss terms | Accepted |
| [0012](0012-blind-validation-on-a-known-engine.md) | Validate the method blind on a known engine before applying it | Accepted |
| [0013](0013-notebook-sequence-and-handoffs.md) | Notebook sequence and handoffs | Accepted |
| [0014](0014-versioning-and-ci-tiers.md) | Tag-driven versioning and tiered CI | Accepted |
