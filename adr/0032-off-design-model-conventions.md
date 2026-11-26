# 32. Off-design model conventions (amends ADR-0030)

Status: Accepted (2026-11-26)

## Context

ADR-0030 made `off_design` (notebook 10) the stage that replaces the algebraic lapse and constant
TSFC of ADR-0029 with the engine's own. Building it needed conventions that no ADR fixed.

## Decision

- **Model:** the sized engine of `cycle_design_point` is the design point of a pyCycle
  multi-point problem; off-design points use the design's scaled generic maps and nozzle throat
  area. Shaft speed balances shaft power, air flow balances the throat area. The throttle is the
  turbine inlet temperature or the net thrust. Native pyCycle units stay inside `cycle/offdesign.py`.
- **Maximum power** holds the design turbine inlet temperature at every flight condition. The thrust
  lapse is thrust over the standard-day sea-level static thrust at that temperature, the same
  definition as the algebraic lapse, so the two compare point for point.
- **Validity guard:** points below a stated fraction of design shaft speed (0.80, a guard from a
  prototype that found the generic axial maps non-physical below about that speed) are flagged
  and never used downstream; points that do not converge are flagged the same way.
- **Fuel:** pyCycle fuel flow is ideal; real fuel flow is ideal over the median lumped combustion
  efficiency of the anchored technology level (`out/validation.yaml`), constant with throttle.
- **Studies** (`config/off_design.yaml`): a maximum-power grid over altitude, Mach number and
  the standard and hot day; part-throttle SFC at the mission's dash, loiter and return conditions
  and at sea-level static; a steady landing thrust-floor check at landing weight (OP2).
- **Comparison with the preliminary analysis** is part of the handoff: lapse differences, and
  the loiter's SFC at its own throttle against the constant TSFC.
- **Deck:** no tabulated deck is built here. The handoff's grid and part-throttle tables are what
  notebooks 11 and 12 interpolate; a sampler deck is built when notebook 14 needs it.

## Consequences

- The run takes about two minutes (about a hundred pyCycle points) and runs in the pipeline only.
- Generic axial maps for a centrifugal machine, constant combustion efficiency and uninstalled
  thrust are standing findings; part-throttle fuel flow is, if anything, understated.
- The throttle floor is the model's, not the engine's: the real minimum stable thrust is a
  datasheet matter (the catalogue idle fraction) and is not derived here.
