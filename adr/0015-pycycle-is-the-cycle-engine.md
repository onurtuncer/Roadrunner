# 15. pyCycle is the cycle engine (amends ADR-0010)

Status: Proposed (2026-11-26)

## Context

ADR-0010 chose an in-house cycle code with pyCycle as a test oracle. On
review the owner prefers pyCycle as the engine itself: it is an
established, open, NPSS-style tool with real off-design capability, the
group already has experience with it, and writing and verifying our own
cycle code is effort that does not serve the course. The
technology-level half of ADR-0010 is unaffected.

## Decision

- **pyCycle (on OpenMDAO) is the cycle model** for design point and
  off-design. `om-pycycle` and `openmdao` are runtime dependencies,
  version-pinned in `pyproject.toml`.
- The engine is a single-spool turbojet pyCycle `Cycle` defined once in
  `src/roadrunner_re/cycle/`, with a design instance (OP1) and
  off-design instances for the other operating points.
- Thermodynamics: the tabular Jet-A package for pipeline runs, with the
  CEA package as a cross-check on the nominal point.
- **SI at the boundary.** pyCycle's native units stay inside the cycle
  wrapper; every value entering or leaving it is converted through
  OpenMDAO units, and all handoffs are SI (ADR-0003). ARP755 station
  names map one-to-one to the pyCycle element ports.
- Off-design uses pyCycle with scaled generic component maps. This
  replaces the "simplified off-design method" of ADR-0009.
- **pyCycle is never called inside a sampling loop.** It is run on a
  designed set of cycle parameters and flight conditions and the results
  are stored as a specific-performance **engine deck** (thrust per unit
  mass flow, TSFC, lapse versus Mach, altitude, temperature offset and
  throttle). Sampling (ADR-0006, ADR-0020) interpolates the deck. The
  nominal point and the corners of the feasible family are always
  re-run through pyCycle directly.
- Transparency for students is kept by a station-by-station walk-through
  of the pyCycle solution in the cycle notebook, plus a closed-form
  ideal-cycle sanity band in `tests/`. GasTurb remains an optional
  off-pipeline cross-check.

## Consequences

- No cycle code to write or verify; off-design is credible from day one.
- Students must learn enough OpenMDAO to read the model.
- The generic maps shipped with pyCycle are not maps of a micro-scale
  centrifugal compressor; part-throttle results carry that error. It is
  a standing finding and an uncertainty input (ADR-0020).
- The engine deck adds a surrogate between pyCycle and the sampler; its
  interpolation error must be measured on held-out pyCycle points and
  reported.
- ADR-0012 (blind validation) now validates the pyCycle model plus the
  technology bounds, not an in-house code.
