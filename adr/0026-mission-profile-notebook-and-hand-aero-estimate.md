# 26. A mission-profile notebook, and the owner's hand aerodynamic estimate (amends ADR-0016, ADR-0018, ADR-0021)

Status: Accepted (2026-11-26)

## Context

The sample mission (ADR-0018) is an input, but nothing quotes the
evidence it rests on or draws it, and the mission analysis that would is
notebook 8, which needs the whole design-point solution. The owner wants
one notebook that quotes and plots the mission profile.

The owner has also supplied a hand aerodynamic estimate of the baseline
vehicle, built on photo-scaled assumptions, to be treated as +/-30 %.
ADR-0016 expects a semi-empirical build-up; this is the first, and the
photo measurements that geometry (ADR-0007) needs do not yet exist.

## Decision

- **Notebook 14, `mission_profile`**, reads only `config/` and writes
  `out/mission_profile.yaml`. It is appended to ADR-0021's sequence
  rather than inserted, so no existing notebook is renumbered; it needs
  nothing from other notebooks, so its position carries no load. It
  quotes each segment's cited ledger statements and stated assumptions,
  tabulates the numbers with bounds, and plots altitude and Mach over
  time. It flies nothing: no weights, fuel or engine. `mission.yaml`
  stays reserved for the mission analysis (notebook 8).
- **Climb and descent durations are not assumed.** The profile does not
  fix them; they are drawn hatched, not to scale, and reported as
  unknown until the mission analysis derives them. Dash and cruise
  durations are distance over true airspeed on the hot day, with bounds
  from the corners of the input bounds.
- **The owner's estimate lives in `config/aero_estimate.yaml`** as a
  tier-C input with its basis stated as an assumption, the three public
  sources it cites, and low/high bounds of +/-30 % on every uncertain
  number. It is not in the evidence ledger (it is not a public report)
  and not in `out/aero.yaml` (it is an input, not a result). It does not
  replace the geometry stage or the aerodynamics notebook.
- The estimate is referenced to the missile convention S_ref = pi d^2 / 4
  and to ISA sea level, not to wing area or to the mission's hot day.

## Consequences

- The hand estimate is the first of ADR-0016's two methods. The second,
  an open-source build-up on measured geometry, is still to come, and
  the spread between them sets the aerodynamic bounds.
- The estimate's length (1.7 m, +/-30 %) is wider than the ledger's
  length anchor (1.4 to 1.8 m); the ledger stays the single anchor.
- Its coefficients are not independent of each other or of S_ref, and the
  +/-30 % is per number, not joint. The uncertainty analysis must not
  sample them as independent without that being a decision.
- Tests re-derive the owner's own checks (S_ref, dynamic pressure,
  Reynolds number, 1-g cruise, L/D, g-limit) from the stored numbers.
