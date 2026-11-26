# 33. Cycle-based analysis pair and the engine model (amends ADR-0029, ADR-0031)

Status: Accepted (2026-11-26)

## Context

ADR-0031 made notebooks 11 and 12 the coupled constraint and mission analysis repeated on the
off-design cycle results of notebook 10. ADR-0029 wrote the solver around an algebraic lapse and a
constant TSFC held directly in `AnalysisInputs`. Running the same solver on cycle tables needs a
seam, and some rules for what happens where the tables end.

## Decision

- **One solver, two engine models.** `AnalysisInputs.engine` holds the engine model; `constraints.py`
  and `mission.py` call only `alpha(...)` and `sfc_kg_N_s(...)` on it. `AlgebraicEngine` reproduces
  ADR-0029 exactly (the preliminary handoffs are byte-identical). `CycleEngine`
  (`engine_model.py`) reads `out/off_design.yaml`. `solve_design_point()` stays the single call site.
- **Lapse:** interpolated linearly in Mach number, altitude and day temperature from the
  maximum-power grid. **SFC:** the full-power SFC from the grid times a part-throttle penalty
  curve (SFC at fraction f over SFC at full power). Hover (launch, landing) uses the sea-level-static
  curve; flight uses the mean of the non-sea-level curves.
- **No extrapolation.** Outside the grid, or at a thrust fraction outside the valid throttle range,
  the engine model raises `OutsideEngineModel`; the sweep reports such masses as infeasible. Rows
  the off-design study flagged invalid are refused at load time.
- **Mission fuel at part throttle:** level flight and loiter burn `SFC(f) * D * dt` at
  `f = D / available thrust`; climb and acceleration burn at full-power SFC; hover segments are
  integrated at `f = m g / (alpha T_SL)`.
- **Idle fraction** for the landing floor stays the catalogue median; the cycle does not derive it.
- **Comparison is part of the handoff:** each handoff of notebooks 11 and 12 carries the
  preliminary result beside the cycle one, per constraint and per segment.
- **Handoffs:** `out/constraints.yaml`, `out/mission.yaml`; both read `out/off_design.yaml`.

## Consequences

- The cycle-based nominal point (85 kg) is still launch-bound (T_SL/W_TO 1.469) but needs
  19.9 kg of mission fuel against 12.8 kg: the constant TSFC understated the loiter.
- Combustion efficiency constant with throttle, generic maps and uninstalled thrust remain standing
  findings; the fuel is, if anything, understated.
- A grid or throttle limit now stops a run visibly instead of extrapolating silently.
