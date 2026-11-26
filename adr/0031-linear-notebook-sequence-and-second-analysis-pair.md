# 31. Linear notebook sequence, preliminary analysis pair and a cycle-based pair (amends ADR-0021, ADR-0029, ADR-0030)

Status: Accepted (2026-11-26)

## Context

ADR-0021 numbered notebooks 1 to 13, a fourteenth was appended (ADR-0026), and ADR-0030 deferred
two of them, so the published numbers had gaps (1, 4, 5, 7, 8, 10, 14). The owner wants one
linear order. The coupled analysis of ADR-0029 runs on an algebraic lapse and a constant TSFC;
the owner wants it kept as the preliminary analysis and repeated on the off-design cycle results.

## Decision

Fifteen notebooks, numbered by position, no gaps. Each writes one handoff and reads only earlier
handoffs (ADR-0013 rules unchanged). Notebooks 3, 4, 10 to 15 are not built yet.

| # | Notebook | Job | Handoff |
|---|----------|-----|---------|
| 1 | `evidence_ledger` | Public evidence, tiers, distributions | `evidence.yaml` |
| 2 | `mission_profile` | The sample mission and its requirements, quoted and plotted (ADR-0026, ADR-0027) | `mission_profile.yaml` |
| 3 | `geometry_from_imagery` | Scaled measurements, engine envelope (blocked on measurement) | `geometry.yaml` |
| 4 | `aerodynamics` | Polar versus Mach, bounds (ADR-0016) | `aero.yaml` |
| 5 | `reference_engines` | Catalogue survey, technology bounds (ADR-0023) | `technology.yaml` |
| 6 | `method_validation` | Leave-one-out blind pyCycle test (ADR-0012) | `validation.yaml` |
| 7 | `constraint_analysis_preliminary` | Algebraic turbojet lapse, hand-estimate polar (ADR-0029) | `constraints_preliminary.yaml` |
| 8 | `mission_analysis_preliminary` | Same model, constant TSFC (ADR-0029) | `mission_preliminary.yaml` |
| 9 | `cycle_design_point` | Required engine at OP1 in pyCycle (ADR-0030) | `cycle.yaml` |
| 10 | `off_design` | Required engine over the mission's conditions and throttle: thrust lapse, part-throttle SFC | `off_design.yaml` |
| 11 | `constraint_analysis` | Constraint analysis with the lapse from notebook 10 | `constraints.yaml` |
| 12 | `mission_analysis` | Mission with thrust and fuel flow from notebook 10 | `mission.yaml` |
| 13 | `engine_selection` | Derived requirements against the catalogue (ADR-0023) | `engine_selection.yaml` |
| 14 | `uncertainty_and_sensitivity` | Propagation, feasible family, Morris, Sobol (ADR-0020) | `uq.yaml` |
| 15 | `design_summary` | Pure reader: results, intervals, standing findings | none |

- **Preliminary pair (7, 8)**: unchanged from ADR-0029 apart from names. Titles carry
  "(preliminary)"; files and handoffs carry `_preliminary`.
- **Second pair (11, 12)** takes the unqualified names. It solves the same coupling through
  `solve_design_point()` with the engine model replaced by the off-design cycle results, and
  reports its difference from the preliminary pair.
- `engine_deck` is no longer a notebook (ADR-0030); a deck for the sampler is built from notebook 10.
- Notebook titles carry their position ("notebook N of 15"); file names carry no number.

## Consequences

- ADR-0021's table is superseded by this one; its rules and the single call site stand.
- ADR-0029 and ADR-0030 name notebooks 7, 8 and 10 by their earlier numbers; read them with this ADR.
- Moving `mission_profile` to position 2 does not change its content: it reads only config.
- Notebook 9 keeps its name; its position moves from 10 to 9.
