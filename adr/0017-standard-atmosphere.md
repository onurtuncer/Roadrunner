# 17. One standard atmosphere model for everything

Status: Accepted (2026-11-26)

## Context

Atmosphere properties enter the drag model, the constraint analysis,
the mission analysis and the engine. If each takes them from a different
place the same flight condition means different things in different
modules, and the error is invisible.

## Decision

- The atmosphere is the **International Standard Atmosphere** (ICAO /
  US Standard Atmosphere 1976; identical over the altitude range of
  interest), implemented once in `src/roadrunner_re/atmosphere.py` as a
  pure function of geopotential altitude returning temperature,
  pressure, density, speed of sound and viscosity. Troposphere and lower
  stratosphere only; calling it outside that range raises.
- **Non-standard days** are a temperature offset `dT_isa_K` applied at
  constant pressure altitude. The hot day of OP1/OP2 is such an offset,
  a config value.
- pyCycle carries its own standard-atmosphere element with a
  temperature-offset input. It is given the same altitude, Mach number
  and offset, and a test asserts that its ambient static temperature and
  pressure agree with `atmosphere.py` to a stated tolerance over the
  flight envelope.
- Altitudes in config and handoffs are geopotential metres above mean
  sea level. No humidity, no wind.

## Consequences

- A flight condition is fully specified by `(altitude_m, mach,
  dT_isa_K)` everywhere in the repo.
- The atmosphere is tested against published table values; it is one of
  the few places with exact reference data.
- Wind and humidity effects on range and hot-day thrust are ignored;
  this is recorded as a limitation, not an uncertainty input.
