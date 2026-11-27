# 35. Figures are written to `out/figures/` beside the handoffs (amends ADR-0028)

Status: Accepted (2026-11-27)

## Context

ADR-0028 publishes the figures the notebooks write, taking them from `notebooks/figures/`.
The handoffs live in `out/`. The notebooks' results are thus split over two places: the
pipeline's `design-outputs` artifact (`out/`) carries the handoffs but not the figures, and
the notebook directory holds generated files beside the sources. The owner wants the
figures in `out/figures/`.

## Decision

- `nb_setup()` points `paths.figures` at `out/figures/` and creates it. Every notebook writes
  its figures through `paths.figures`, so no notebook changes.
- `scripts/build_site.py` publishes `img/*.png` from `out/figures/`. The rest of ADR-0028
  stands.
- Figures stay generated, not committed: `/out/figures/` is ignored, as `/notebooks/figures/`
  was. The handoffs in `out/*.yaml` are unaffected.

## Consequences

- The `design-outputs` artifact now holds the figures with the handoffs.
- A local `notebooks/figures/` left over from earlier runs is stale and can be deleted.
- No handoff value changes; the figures and the rendered notebooks are unchanged apart from
  where the image files sit.
