# 18. A sample mission profile is an input; mission analysis checks the weights (amends ADR-0008, ADR-0009)

Status: Proposed (2026-11-26)

## Context

ADR-0008 treated mission segment lengths as unknowns with priors and
reduced the mission to a fuel estimate. That leaves nothing concrete to
check a candidate vehicle against. The owner wants a defined mission
profile as an explicit input, and a proper mission analysis that tracks
weight through it.

## Decision

- **The mission is an input.** Named profiles live in
  `config/missions/*.yaml` as an ordered list of segments. One profile,
  `sample`, is the baseline for all results. The feasible family
  (ADR-0006) is therefore *conditional on the stated mission*.
- Segment types: `vertical_launch`, `transition`, `climb`, `cruise`
  (range or time at Mach and altitude), `dash`, `loiter`, `descent`,
  `hover`, `vertical_landing`, and a `reserve` fraction.
- The `sample` profile (energy accounting only, per ADR-0004):

  | # | Segment | Defining parameters |
  |---|---------|---------------------|
  | 1 | Vertical launch | time at launch thrust, hot day, sea level |
  | 2 | Transition and climb | to cruise altitude |
  | 3 | Dash out | Mach, altitude, distance |
  | 4 | Loiter | Mach, altitude, time |
  | 5 | Cruise back | Mach, altitude, distance |
  | 6 | Descent and transition | to hover |
  | 7 | Hover and vertical landing | time at landing weight |
  | 8 | Reserve | fraction of mission fuel |

  Numerical values are **assumptions** set by the owner in the YAML with
  rationale; where a value leans on evidence ("high subsonic" for the
  dash Mach number) it cites the ledger `id`.
- **Mission analysis** follows the weight-fraction method of Mattingly,
  Heiser and Pratt: each segment yields `W_final/W_initial` from the
  installed TSFC (engine deck, ADR-0015), the polar (ADR-0016) and the
  atmosphere (ADR-0017). Thrust-borne segments integrate
  thrust times TSFC over time; wing-borne segments use the appropriate
  Breguet or constant-speed climb form.
- Outputs per segment: weight in, weight out, fuel burned, thrust
  required and available, throttle setting, TSFC. Then the **weight
  check**: take-off mass = payload + fuel + empty, with the empty mass
  compared against the build-up of ADR-0008 and the fuel volume checked
  against the measured body volume.
- Payload stays in the vehicle for the whole mission (baseline vehicle,
  ADR-0004), so landing weight is take-off weight minus fuel burned.

## Consequences

- Every result can be traced to a concrete, reviewable mission.
- Changing the mission is a config edit that re-converges the pipeline;
  alternative profiles show how conclusions depend on it.
- The instantaneous weight fraction at each segment is available to the
  constraint analysis (ADR-0019), closing the usual loop between the two.
- The four operating points of ADR-0009 become the engine check points
  that this mission generates, rather than free-standing conditions.
