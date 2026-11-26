# 23. The engine is chosen from a purchasable catalogue (amends ADR-0010, ADR-0012, ADR-0015)

Status: Accepted (2026-11-26)

## Context

ADR-0010 and ADR-0015 treat the engine as a "rubber" cycle: pressure
ratio, turbine temperature and efficiencies are free unknowns, and the
answer is whatever engine the vehicle needs. The owner wants the engine
choice to be something that can actually be bought, from PBS or another
vendor. The real vehicle uses engines its manufacturer builds in-house,
which nobody else can buy; the useful course question is therefore
"which purchasable engine pair would do this job, and how far short does
the catalogue fall?". The tailsitter study took the same position for
its propulsor (its ADR-0003).

## Decision

- **The engine is selected, not designed.** Candidates are the entries
  of `config/reference_engines.yaml`: small turbojets with a public
  datasheet from a vendor that sells them (PBS, JetCat, AMT at present).
  Two identical engines.
- **Requirements are derived, not configured**, from the constraint and
  mission analysis: installed thrust per engine at vertical launch on
  the hot day, a minimum stable thrust low enough for vertical landing,
  thrust at dash, and the diameter and length that fit the measured
  nacelle (ADR-0007). Only margins are configured.
- **Selection is deterministic.** Infeasible candidates are rejected
  with the reason recorded. Among feasible ones the winner is the pair
  giving the lowest closed take-off mass for the sample mission (engine
  mass and fuel burn together); ties go to the lighter engine.
  Envelope fit is *reported*, and filtered on only when the geometry
  bounds exclude the engine outright.
- **pyCycle is anchored to each datasheet.** Vendors publish sea-level
  static standard-day numbers only. For each candidate the pyCycle model
  is calibrated to reproduce its published thrust, mass flow, pressure
  ratio and fuel consumption, and is then used for what the datasheet
  does not give: hot day, altitude and Mach lapse, part throttle. The
  engine deck of ADR-0015 is built per candidate.
- **Published idle thrust is the landing thrust floor** where the vendor
  gives it; otherwise it is an uncertain input.
- Validation (ADR-0012) becomes **leave-one-out** over the catalogue:
  predict each engine blind from the others.
- Engine flowpath sizing is dropped from this phase; there is nothing to
  size.
- If **no** catalogue engine is feasible, that is a result, reported
  with the shortfall. It is also the test of the manufacturer's
  "most power-dense" claim (Tier X, ADR-0005).
- **This is a paper exercise; nothing is being procured.** "Purchasable"
  means only that the engine is a catalogue product with a public
  datasheet. Price, lead time and export controls are not considered,
  not recorded and not used anywhere in the selection.

## Consequences

- The study ends with a part number, not a notional cycle.
- The cycle parameters stop being free unknowns, which removes most of
  the engine-side uncertainty; what remains is calibration residual and
  the generic-map error (ADR-0015).
- The catalogue is coarse (a handful of thrust classes), so the result
  jumps between engines as vehicle mass varies; the uncertainty analysis
  reports the probability of each engine being selected.
- Catalogue numbers are vendor claims; masses are not stated on a common
  basis across vendors, which the loader must normalise explicitly.
- Adding a vendor is a config edit that re-runs the selection.
