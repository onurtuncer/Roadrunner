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
| [0006](0006-inverse-problem-feasible-family.md) | Reverse engineering is an inverse problem: report a feasible family | Accepted; amended by 0020 |
| [0007](0007-geometry-from-scaled-imagery.md) | Geometry from scaled public imagery, as measured intervals | Accepted; amended by 0024 |
| [0008](0008-vehicle-model-as-requirements-generator.md) | The vehicle model is a requirements generator, no more | Accepted; amended by 0016, 0018 |
| [0009](0009-operating-points-and-cycle-design-point.md) | Four operating points; the cycle design point is static launch | Accepted; amended by 0015, 0018, 0019 |
| [0010](0010-in-house-cycle-model-and-technology-levels.md) | In-house SI cycle model; technology levels from a reference-engine database | Accepted; amended by 0015, 0023, 0024 |
| [0011](0011-installation-and-thrust-vectoring-as-losses.md) | Installation and thrust vectoring enter as bounded loss terms | Accepted |
| [0012](0012-blind-validation-on-a-known-engine.md) | Validate the method blind on a known engine before applying it | Accepted; amended by 0023, 0024 |
| [0013](0013-notebook-sequence-and-handoffs.md) | Notebook sequence and handoffs | Superseded by 0021 |
| [0014](0014-versioning-and-ci-tiers.md) | Tag-driven versioning and tiered CI | Accepted; amended by 0022 |
| [0015](0015-pycycle-is-the-cycle-engine.md) | pyCycle is the cycle engine | Accepted; amended by 0023, 0029, 0030 |
| [0016](0016-aerodynamics-from-open-source-evidence.md) | Aerodynamics estimated from open-source evidence | Accepted; amended by 0026 |
| [0017](0017-standard-atmosphere.md) | One standard atmosphere model for everything | Accepted |
| [0018](0018-sample-mission-profile-and-mission-analysis.md) | A sample mission profile is an input; mission analysis checks the weights | Accepted; amended by 0026 |
| [0019](0019-constraint-analysis.md) | Constraint analysis in the thrust-loading / wing-loading plane | Accepted; amended by 0027, 0029 |
| [0020](0020-uncertainty-quantification-and-sensitivity.md) | Uncertainty quantification and sensitivity analysis | Accepted |
| [0021](0021-notebook-sequence-revision-1.md) | Notebook sequence, revision 1 | Accepted; amended by 0026, 0030, 0031 |
| [0022](0022-documentation-on-github-pages.md) | Documentation on GitHub Pages | Accepted; amended by 0028 |
| [0023](0023-engine-from-a-purchasable-catalogue.md) | The engine is chosen from a purchasable catalogue | Accepted; amended by 0025 |
| [0024](0024-specific-thrust-and-sfc-no-area-scaling.md) | Engines are characterised by specific thrust and SFC; nothing is scaled with frontal area | Accepted |
| [0025](0025-drop-jetcat-from-the-catalogue.md) | JetCat engines are dropped from the catalogue | Accepted |
| [0026](0026-mission-profile-notebook-and-hand-aero-estimate.md) | A mission-profile notebook, and the owner's hand aerodynamic estimate | Accepted; amended by 0027 |
| [0027](0027-performance-requirements-as-an-input.md) | Performance requirements are an input beside the mission | Accepted |
| [0028](0028-pages-site-in-the-design-report-format.md) | The Pages site is a design report in the tailsitter format | Accepted |
| [0029](0029-first-iteration-constraint-and-mission-analysis.md) | First-iteration coupled constraint and mission analysis | Accepted; amended by 0031 |
| [0030](0030-cycle-design-point-and-off-design-before-engine-deck.md) | On-design cycle point and off-design performance come before a stand-alone engine deck | Accepted; amended by 0031 |
| [0031](0031-linear-notebook-sequence-and-second-analysis-pair.md) | Linear notebook sequence, preliminary analysis pair and a cycle-based pair | Accepted |
