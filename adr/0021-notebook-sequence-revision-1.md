# 21. Notebook sequence, revision 1 (supersedes ADR-0013)

Status: Proposed (2026-11-26)

## Context

ADR-0015 to ADR-0020 add an aerodynamics stage, an engine deck, a
constraint analysis, a mission analysis and an uncertainty and
sensitivity stage. The sequence of ADR-0013 no longer matches.

## Decision

Thirteen notebooks, in this order. The handoff rules of ADR-0013 (one
handoff each, read only earlier handoffs, no numbers in file names) are
unchanged.

| # | Notebook | Job | Handoff |
|---|----------|-----|---------|
| 1 | `evidence_ledger` | Public evidence, tiers, distributions | `evidence.yaml` |
| 2 | `geometry_from_imagery` | Scaled measurements, engine envelope, reference area | `geometry.yaml` |
| 3 | `aerodynamics` | Polar versus Mach by two methods, bounds (ADR-0016) | `aero.yaml` |
| 4 | `reference_engines` | Database survey, technology bounds, mass correlation | `technology.yaml` |
| 5 | `method_validation` | Blind pyCycle test on held-out engines (ADR-0012) | `validation.yaml` |
| 6 | `engine_deck` | pyCycle design and off-design runs, deck, interpolation error (ADR-0015) | `engine_deck.yaml` |
| 7 | `constraint_analysis` | Constraint diagram, active constraints (ADR-0019) | `constraints.yaml` |
| 8 | `mission_analysis` | Sample mission, weight by segment, weight check (ADR-0018) | `mission.yaml` |
| 9 | `cycle_design_point` | OP1 pyCycle solution, station walk-through, installed vs uninstalled | `cycle.yaml` |
| 10 | `engine_flowpath_sizing` | Flowpath sizing; fit in the measured envelope | `engine.yaml` |
| 11 | `off_design` | Thrust floor, dash, cruise; throttle line | `off_design.yaml` |
| 12 | `uncertainty_and_sensitivity` | Propagation, feasible family, Morris, Sobol (ADR-0006, ADR-0020) | `uq.yaml` |
| 13 | `design_summary` | Pure reader: results, intervals, ranking, standing findings | none |

Notebooks 7 to 11 are views of the one converged solution returned by
`solve_design_point()`; the constraint/mission iteration is not spread
across notebooks.

## Consequences

- The atmosphere (ADR-0017) has no notebook of its own; it is a tested
  module used everywhere.
- The engine deck is built once (6) and reused by 7, 8, 11 and 12.
- ADR-0013 is superseded and kept for history.
