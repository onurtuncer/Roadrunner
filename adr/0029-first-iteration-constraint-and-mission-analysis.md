# 29. First-iteration coupled constraint and mission analysis (amends ADR-0015, ADR-0019)

Status: Accepted (2026-11-26)

## Context

The performance requirements (ADR-0027) and the mission (ADR-0018) are inputs. The next step is
the coupled constraint and mission analysis in the manner of UCK 474E Lectures 2 and 5. The
engine deck that ADR-0015 describes is not built, and the owner asked for a rough first iteration
with a turbojet lapse, closed by the cycle analysis at the end.

## Decision

- **Engine model for this iteration:** the lecture's algebraic installed-thrust lapse for a
  turbojet at maximum power, throttle ratio 1.00 (bounds 1.00 to 1.08), and one constant TSFC
  and idle thrust fraction, the medians of the catalogue (`config/analysis.yaml`, source cited
  there). The cycle analysis (pyCycle, ADR-0015) supersedes both when the engine deck exists.
- **Constraints:** Mattingly's master equation for level flight, climb, sustained turn and
  ceiling; vertical launch (margin over weight divided by the hot-day sea-level lapse) and the
  landing thrust floor (upper bound) replace the ground-roll cases (ADR-0019, ADR-0027).
- **Mission:** energy-height method for climb and acceleration, `dm = C D dt` for level flight
  and loiter, hover at `T = W` for launch and landing, an assumed weight fraction for descent.
- **Coupling:** `design_point.solve_design_point()` iterates constraints (which need the weight
  fraction at their segment) and mission (which needs the thrust) to a fixed point. It is the
  single call site every notebook uses. Take-off mass is an input, swept over its evidence
  bounds; it is not solved for, because no structural build-up (ADR-0008) exists.
- **Reference area:** the polar is the owner's estimate referred to the body cross-section, so
  wing loading is `W_TO g / S_ref` on that area and the polar is constant with Mach number.
- **Two notebooks, `constraint_analysis` (7) and `mission_analysis` (8)**, write
  `out/constraints.yaml` and `out/mission.yaml`; both call the same solver.

## Consequences

- Every result is labelled first iteration and lists its simplifications in the handoff: no
  part-throttle TSFC (loiter fuel understated), no drag rise, no transition, no installation
  loss, no empty-mass closure.
- Changing the lapse for the engine deck changes `lapse.py` only; the interfaces stay.
- Results are regression-pinned (`tests/test_design_outputs.py`); the pins move with the cycle
  analysis in the same commit.
