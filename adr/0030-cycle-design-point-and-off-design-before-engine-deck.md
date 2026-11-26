# 30. On-design cycle point and off-design performance come before a stand-alone engine deck (amends ADR-0021, ADR-0015)

Status: Accepted (2026-11-26)

## Context

ADR-0021 puts an `engine_deck` notebook (6) before the constraint and mission analysis. The
first-iteration analysis (ADR-0029) has since been built on an algebraic lapse. The owner wants
the next stage to be an on-design pyCycle point, then a performance (off-design) cycle analysis,
and not an engine deck as a stage of its own.

## Decision

- **`cycle_design_point` (10) is built next**: pyCycle at OP1 (sea-level static, the mission's
  hot day) for the thrust each engine must give, taken from the launch constraint of the
  converged design point. The cycle is closed with the turbine inlet temperature and pressure
  ratio of the catalogue technology level (`out/validation.yaml`); air flow follows from thrust.
  The result is the *required* engine, with its ARP755 stations and one-at-a-time bounds on every
  assumed input. The catalogue is compared with it; the engine is still selected, not designed
  (ADR-0023).
- **`off_design` (11) follows**: the required engine run over the mission's conditions and
  throttle settings, producing the lapse and part-throttle SFC that replace the algebraic lapse
  and constant TSFC of ADR-0029. Any tabulated deck for the sampler (ADR-0015) is a by-product of
  this notebook, built when the uncertainty stage needs it, not a notebook of its own.
- **`engine_deck` (6) and `engine_selection` (9) are deferred**, not dropped; ADR-0021's table
  otherwise stands, and numbering is kept so file names and the index do not move.
- No number enters from memory: pressure ratio and losses are the assumptions of
  `config/cycle.yaml`, Tt4 is the anchored catalogue value.

## Consequences

- The design point is a function of the first-iteration launch thrust, so it moves when the
  constraint analysis is revised; it is a view of `solve_design_point()` (ADR-0021).
- Installed and uninstalled thrust are equal until installation losses exist (ADR-0011); the
  handoff says so.
- pyCycle is run in the notebook and the pipeline, never in a sampling loop (ADR-0015).
