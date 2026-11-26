# 19. Constraint analysis in the thrust-loading / wing-loading plane (amends ADR-0009)

Status: Accepted (2026-11-26)

## Context

ADR-0009 listed four operating points but did not say how they combine
into a requirement on the engine. The standard instrument is a
constraint analysis: each performance requirement becomes a curve of
required sea-level thrust loading against wing loading, and the feasible
region is what lies above all of them.

## Decision

- Use the master equation of Mattingly, Heiser and Pratt,

  `T_SL/W_TO = (beta/alpha) * { (q S / (beta W_TO)) * [ K1 (n beta W_TO / (q S))^2 + CD0 ] + P_s / V }`

  with `alpha` the installed thrust lapse from the engine deck
  (ADR-0015), `beta` the instantaneous weight fraction from the mission
  analysis (ADR-0018), the polar from ADR-0016 and the atmosphere from
  ADR-0017.
- Constraints, all parameters in `config/constraints.yaml`:
  1. **Vertical launch**: `T_SL/W_TO` at least the launch margin divided
     by the static installation factor (ADR-0011), hot day. A horizontal
     line, and expected to dominate.
  2. **Vertical landing thrust floor**: an *upper* bound, minimum stable
     thrust not above landing weight.
  3. **Dash**: level flight at the dash Mach number and altitude.
  4. **Climb**: a specified rate of climb at a specified condition.
  5. **Sustained load factor**: a specified `n` at a specified Mach
     number and altitude (a generic manoeuvre requirement).
  6. **Cruise/loiter ceiling**: a residual climb rate at loiter altitude.
- In an inverse study the wing loading is not a free design choice: the
  reference area is measured (ADR-0007), so each candidate take-off mass
  is a vertical line on the diagram. The diagram is used to read off
  which constraint is active for a given mass and how much excess thrust
  the launch requirement leaves at every other condition.
- Constraint and mission analysis are coupled through `alpha`, `beta`
  and `T_SL/W_TO`; the iteration lives in `solve_design_point()`.

## Consequences

- The oversizing produced by the vertical-launch requirement is
  quantified at every flight condition, which is the central lesson of
  the vehicle.
- A two-sided constraint (launch from below, landing floor from above)
  can leave an empty region; the pipeline must report that outcome
  rather than fail obscurely.
- Requirement values in constraints 4 to 6 are assumptions, not
  evidence, and are uncertainty inputs (ADR-0020).
