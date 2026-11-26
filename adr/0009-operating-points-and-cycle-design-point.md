# 9. Four operating points; the cycle design point is static launch

Status: Accepted (2026-11-26); amended by ADR-0015, ADR-0018 and ADR-0019

## Context

A jet-borne VTOL vehicle has an unusual propulsion problem. Thrust must
exceed weight at launch, so in wing-borne flight the engines are heavily
oversized and run throttled, where a simple turbojet's fuel consumption
is poor. And it must land vertically at a much lower weight, so the
engines must hold stable, controllable thrust well below their maximum.
Which condition sizes the engine, and which ones merely check it, has to
be decided once.

## Decision

Four operating points, all parameters in `config/operating_points.yaml`:

1. **OP1 Vertical launch.** Sea-level static, hot day, take-off mass.
   Installed vertical thrust must exceed weight by a configured margin
   covering vertical acceleration and thrust-vector control reserve.
2. **OP2 Vertical landing.** Sea-level static, landing mass (payload
   retained, reserve fuel). Required thrust equals weight, so the
   engines must throttle stably to that level with margin above idle and
   with enough thrust-response rate. This is a **thrust floor** check.
3. **OP3 Dash.** High subsonic Mach at altitude: thrust equals drag.
4. **OP4 Cruise/loiter.** Best-range or best-endurance condition; sets
   the fuel fraction through TSFC at part throttle.

- **OP1 is the cycle design point.** These are fixed-geometry engines
  sized by static thrust. OP2 to OP4 are off-design checks.
- Off-design in phase 1 uses a documented simplified method (fixed
  component efficiencies, choked turbine and nozzle matching). Component
  maps are deferred to a later ADR.
- Engine-out is **not** a requirement. With two engines and thrust above
  weight, loss of one in hover is not survivable; recorded as a standing
  finding, not designed for.

## Consequences

- The central tension of the vehicle (launch thrust versus cruise
  economy versus landing thrust floor) is explicit and is the
  pedagogical core of the project.
- OP2 may turn out to be the binding constraint on the feasible family
  (a light landing mass against a high idle thrust); the pipeline must
  report it as such rather than hide it.
- The simplified off-design method limits confidence in OP3/OP4 TSFC;
  the limitation is quantified in the method validation (ADR-0012).
