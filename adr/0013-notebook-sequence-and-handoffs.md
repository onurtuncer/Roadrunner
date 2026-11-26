# 13. Notebook sequence and handoffs

Status: Superseded by ADR-0021 (accepted 2026-11-26, superseded the same day)

## Context

ADR-0001 makes notebook order load-bearing. The order should be fixed
before the first notebook is written, so that each has one job, one
handoff, and a known set of upstream readers.

## Decision

Eleven notebooks, executed in this order. Each writes exactly one YAML
handoff to `out/` (plus figures) and reads only earlier handoffs.

| # | Notebook | Job | Handoff |
|---|----------|-----|---------|
| 1 | `evidence_ledger` | Present and sanity-check the public evidence and its tiers | `evidence.yaml` |
| 2 | `geometry_from_imagery` | Scaled measurements, engine envelope (ADR-0007) | `geometry.yaml` |
| 3 | `reference_engines` | Database survey, technology bounds, mass correlation (ADR-0010) | `technology.yaml` |
| 4 | `method_validation` | Blind test on held-out engines (ADR-0012) | `validation.yaml` |
| 5 | `vehicle_requirements` | Drag build-up, operating points, thrust constraints (ADR-0008/0009) | `requirements.yaml` |
| 6 | `mission_mass_closure` | Coupled mass/fuel/engine closure, nominal point | `vehicle.yaml` |
| 7 | `cycle_design_point` | OP1 cycle, station table, installed vs uninstalled (ADR-0010/0011) | `cycle.yaml` |
| 8 | `engine_flowpath_sizing` | Compressor, combustor, turbine, nozzle sizing; fit in the envelope | `engine.yaml` |
| 9 | `off_design` | OP2 thrust floor, OP3 dash, OP4 cruise; throttle line | `off_design.yaml` |
| 10 | `feasible_family` | Sampling, rejection, intervals, active constraints (ADR-0006) | `feasible_family.yaml` |
| 11 | `design_summary` | Pure reader: results, validation error, standing findings | none |

- The mass/engine coupling is resolved inside `solve_design_point()`, so
  notebooks 6 to 9 are views of one converged solution, not successive
  approximations. No back-edges.
- Notebook 8 uses a centrifugal compressor and single-stage turbine
  layout as the working assumption for this engine class; the layout
  itself is an evidence-ledger entry (Tier C) and can be overturned.
- Notebooks are numbered in the README and CLAUDE.md, not in file names
  (tailsitter practice), so inserting one does not rename the rest.

## Consequences

- Students can be assigned notebooks as work packages with clear inputs
  and outputs.
- The method is validated (4) before it is trusted (7 onward).
- Adding a notebook means choosing its place in this table and amending
  this ADR's index entry by a follow-up ADR.
