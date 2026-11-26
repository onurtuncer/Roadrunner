# 24. Engines are characterised by specific thrust and SFC; nothing is scaled with frontal area (amends ADR-0007, ADR-0010, ADR-0012)

Status: Accepted (2026-11-26)

## Context

The first version of the engine survey and of the blind validation used
thrust per frontal area, and air flow per frontal area, as the link
between a measured diameter and a thrust. The owner rejected this:
frontal-area scaling is an empirical packaging correlation, not a cycle
quantity, and it hides the physics the course is about. The standard
description of an engine's cycle is its **specific thrust** (thrust per
unit air mass flow) and its **specific fuel consumption** (fuel flow per
unit thrust).

## Decision

- Engines are characterised by specific thrust `F_s = F / m_dot_air` and
  specific fuel consumption `SFC = m_dot_fuel / F`. These are intensive:
  they belong to the cycle, not to the size of the engine.
- **Size enters only through air mass flow**: `F = F_s * m_dot_air`.
- **No quantity is scaled with frontal area.** Thrust per frontal area
  and air flow per frontal area are removed from the technology levels
  (amending ADR-0010), from the validation (amending ADR-0012) and from
  any route from geometry to thrust (amending ADR-0007).
- **Diameter and length are a fit check only**: a catalogue engine
  either fits the measured envelope or it does not (ADR-0023).
- The blind validation predicts specific thrust and SFC of each engine
  from the technology levels of the others. It does not predict size.
- The engine deck (ADR-0015) is expressed in specific terms: specific
  thrust and SFC as functions of flight condition and throttle, together
  with the air mass flow relative to its reference value.
- Reports and summaries lead with specific thrust and SFC.

## Consequences

- The measured nacelle diameter no longer yields a thrust estimate by
  itself. Required thrust comes from the constraint and mission
  analysis, and the engine is then chosen from the catalogue.
- If air mass flow is ever to be estimated from geometry, it must be
  from a flow area and a stated flow condition there (a mass-flow
  function at the compressor face), under its own ADR, not from a
  frontal-area correlation.
- Four catalogue engines publish no air mass flow; their specific thrust
  is unknown and they cannot be anchored until it is found.
- The validation is a cleaner test of the cycle model, and a harder one:
  it can no longer pass on compensating errors between size and cycle.
