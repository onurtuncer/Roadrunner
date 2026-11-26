# 16. Aerodynamics estimated from open-source evidence (amends ADR-0008)

Status: Accepted (2026-11-26)

## Context

No aerodynamic data for the vehicle is published. ADR-0008 allowed a
bare component drag build-up. Constraint and mission analysis
(ADR-0018, ADR-0019) need more than that: a drag polar that is a
function of Mach number up to the dash condition, a maximum lift
coefficient, and stated uncertainty on all of it. The only basis is
open-source material: public imagery (ADR-0007), open literature on
comparable body-dominated configurations, and open semi-empirical
methods.

## Decision

- Aerodynamics are **estimated, from open-source evidence only**, by
  `src/roadrunner_re/aero/` from the measured geometry
  (`out/geometry.yaml`).
- Deliverable is a polar `CD = CD0(M) + K1(M) CL^2` (Mattingly's `K2`
  term kept in the interface, zero by default), `CL_max`, and the
  lift-curve slope, on one declared reference area `S_ref_m2` taken from
  the geometry handoff. Body lift is included; the vehicle is not
  treated as a wing with a fuselage attached.
- Two independent estimates are made and compared:
  1. a documented semi-empirical component build-up (skin friction with
     form factors, base drag, interference, wave-drag rise near the dash
     Mach number), every correlation cited;
  2. an open-source aerodynamic build-up code run on the same geometry.
- The spread between the two, combined with the geometry bounds, sets
  the `low`/`high` bounds of each coefficient. The coefficients are
  written to `out/aero.yaml` as Tier-C evidence.
- Nozzle-on effects (base drag change with the jet, vectoring) and the
  hover/transition regime are **not** modelled aerodynamically; vertical
  segments are thrust-borne.
- No CFD and no wind-tunnel data in this phase.

## Consequences

- The aerodynamic model is the least certain element of the study and
  is expected to dominate the sensitivity ranking for dash and range.
- Two methods give a defensible bound rather than a single unchecked
  number.
- The choice of open-source code is a dependency decision recorded in
  `pyproject.toml`; AeroSandbox is the working candidate (pure Python,
  runs in CI). Swapping it does not need a new ADR.
