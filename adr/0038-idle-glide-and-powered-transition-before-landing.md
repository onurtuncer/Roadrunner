# 38. The return to the ground is an idle glide and a powered transition (amends ADR-0018, ADR-0029)

Status: Accepted (2026-11-27)

## Context

The sample mission (ADR-0018) ended with a `descent` segment that the first-iteration analysis
(ADR-0029) did not fly: it burned an assumed weight fraction, had no duration and no thrust, and
by its own comment included the transition back to thrust-borne flight. When the mission's
total impulse was added, that segment counted zero. For a vehicle that lands softly on its
engines this is wrong: slowing from wing-borne flight onto the engines takes thrust close to
weight, and that phase was hidden inside a fraction. The owner asked for the soft landing to be
broken down.

## Decision

- **`descent` is an idle glide** from the last cruise altitude to the ground, at the Mach number
  of the preceding segment (`mach: {from_segment: cruise_back}`).
  - Its duration is altitude over an assumed sink rate, `sink_rate_m_s` in the mission file, an
    uncertain input with bounds like every other mission number.
  - Its thrust is the catalogue median idle fraction times the maximum-power lapse at the
    glide's mid altitude and Mach times the sea-level static thrust of the pair. It gives the
    glide's impulse.
  - Its fuel stays the assumed weight fraction of `config/analysis.yaml`. Idle is far below the
    lowest throttle the off-design tables cover, and the cycle engine model never extrapolates
    (ADR-0033), so fuel cannot follow from thrust here. Fuel and impulse are therefore not tied
    by an SFC in this segment, and the handoff says so.
- **A new `transition` segment** sits between `descent` and `landing`: thrust-borne deceleration
  from wing-borne flight to hover, for an assumed `duration_s` with bounds. It is flown like
  hover (thrust equals weight at sea level, hover SFC). That overstates thrust while the wing
  still carries part of the weight, so its fuel and impulse are upper estimates.
- `landing` is unchanged: hover and touchdown at landing weight, the OP2 thrust-floor condition
  (ADR-0009).
- The climb keeps the launch-side transition inside its energy-height steps, as before.

## Consequences

- Mission fuel rises by the transition's hover fuel, and the landing weight falls slightly.
  The regression pins move in the same commit.
- Mission time is complete: the glide is timed, and only the climb duration is left to the
  thrust margin.
- The glide's idle thrust ignores ram drag, which at speed can bring net idle thrust near
  zero. Its impulse is small next to the hover segments either way.
- The sink rate and the transition duration are new uncertain inputs for the uncertainty
  analysis (ADR-0020). No public source gives either.
