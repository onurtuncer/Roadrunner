# 8. The vehicle model is a requirements generator, no more

Status: Accepted (2026-11-26); amended by ADR-0016 and ADR-0018 (proposed)

## Context

Engine requirements (thrust at each operating point, fuel burn) depend on
vehicle mass and drag, and vehicle mass depends on fuel burn, hence on
the engine. Some vehicle model is unavoidable. The risk is building a
full conceptual-design study of the airframe when the course is about the
engine.

## Decision

The vehicle model has exactly three parts, all in `src/`:

- **Mass closure.** `m0 = m_payload + m_fuel + m_empty`, with `m_empty`
  built up from an engine mass (from the engine model, ADR-0010) plus
  configured structure/systems fractions with bounds. No statistical
  empty-weight regression: there is no population of comparable vehicles.
- **Drag.** Component build-up (body, nacelles, lifting and control
  surfaces, base and interference allowances) from the measured geometry,
  giving a parabolic polar with a compressibility correction valid to the
  dash Mach number. Coefficients carry bounds.
- **Mission fuel.** Segment-by-segment: thrust-times-TSFC integration for
  the vertical and hover segments, Breguet for cruise and loiter, a
  configured reserve. Segment durations and distances are *unknowns with
  priors*, not facts.

The coupled solve (mass closure with the engine in the loop) is one
function, `solve_design_point()`, per ADR-0003.

Explicitly excluded: stability and control, control allocation between
the two vectored nozzles, structures, aeroelasticity, CAD, CFD.

## Consequences

- The vehicle side stays small enough to review in one sitting.
- Drag is the weakest link at high subsonic speed; its bounds will be
  wide and will show up as width in the feasible family, which is honest.
- If a later phase wants CAD or CFD, it attaches downstream of `out/`
  under a new ADR without disturbing this model.
