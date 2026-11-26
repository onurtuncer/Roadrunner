# 10. In-house SI cycle model; technology levels from a reference-engine database

Status: Accepted (2026-11-26); cycle-model half amended by ADR-0015, engine choice by ADR-0023 (both proposed)

## Context

Two choices determine the engine results: the cycle tool and the
component technology levels fed to it. Candidate tools are GasTurb
(commercial, closed, not scriptable in CI), pyCycle/OpenMDAO (open,
capable, but a heavy dependency whose internals hide the thermodynamics
from students) and an in-house station-by-station model. Technology
levels cannot come from Roadrunner itself; they must come from the class
of engine it belongs to.

## Decision

**Cycle model**

- In-house Python in `src/roadrunner_re/cycle/`: single-spool turbojet,
  inlet, compressor, combustor, turbine, nozzle.
- ARP755 station numbering. SI units, no `g_c`.
- Thermally perfect gas: `cp(T)` for air and for kerosene combustion
  products as a function of fuel-air ratio, from published polynomial
  fits committed as data with their source. No constant-gamma shortcuts
  in the delivered results (a constant-gamma mode may exist for teaching
  comparisons).
- Pure functions, vectorisable, no global state, so the inverse problem
  (ADR-0006) can call it thousands of times.
- pyCycle (and GasTurb where a licence is at hand) are **verification
  oracles**, used off-pipeline to cross-check the design point; their
  results are stored as pinned reference values in `tests/`, not imported
  at runtime.

**Technology levels**

- `config/reference_engines.yaml`: small and micro turbojets with public
  datasheets (thrust, mass, diameter, length, mass flow, pressure ratio,
  exhaust temperature, fuel consumption), each field with its source.
- From it derive **bounded** priors for compressor pressure ratio,
  turbine inlet temperature, component efficiencies, thrust per frontal
  area and engine thrust-to-weight, and an engine mass correlation.
- The manufacturer's "most power-dense" statement is Tier X (ADR-0005):
  not an input. The study asks instead what technology level the
  feasible family *requires*, and where that sits relative to the
  database.

## Consequences

- Students can read every line of thermodynamics that produced a number.
- We own a small cycle code and must verify it; the oracles and
  ADR-0012 carry that burden.
- Small-engine effects (low Reynolds number, large relative tip
  clearance, heat soak) enter only through database-derived efficiency
  bounds, not through first-principles models.
