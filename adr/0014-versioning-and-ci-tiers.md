# 14. Tag-driven versioning and tiered CI

Status: Accepted (2026-11-26); amended by ADR-0022

## Context

The tailsitter repo's versioning and CI scheme (its ADR-0006) worked. This
repo has no CadQuery or OpenFOAM stages, so the scheme simplifies, but it
gains one new thing to protect: a stochastic result (ADR-0006) that must
stay reproducible.

## Decision

- **Version from git tags via `setuptools-scm`**, never hand-edited. A
  `v*` tag is a frozen snapshot of the study; each tag gets a
  `CHANGELOG.md` entry.
- **`ci.yml`** on every push and PR: ruff, pytest. Tests include unit
  tests of the cycle model against pinned oracle values (ADR-0010), the
  config/evidence loader checks (ADR-0005), and the blind-validation
  bands (ADR-0012).
- **`design-pipeline.yml`**: executes all notebooks in order, runs the
  design-regression tests on `out/`, uploads `out/`; on `main` also
  deploys the rendered notebooks to GitHub Pages.
- **`release.yml`**: a `v*` tag re-runs the pipeline and attaches the
  snapshot to a GitHub Release.
- **Reproducibility of sampling:** seed and sample count are config
  values; CI runs the full configured sample count; regression pins
  cover the nominal point exactly and the family bounds to a stated
  tolerance.
- One Python environment for everything (no CAD split); supported
  versions declared in `pyproject.toml` and matched by the CI matrix.
- An intentional change to results updates the pins in the same commit.

## Consequences

- A tag regenerates the entire study from `config/` and proves it.
- The feasible-family run time is a CI cost; if it grows past a few
  minutes the forward model gets profiled before the sample count gets
  cut.
- `out/` is committed as a cache (tailsitter practice) and CI is the
  source of truth when they disagree.
