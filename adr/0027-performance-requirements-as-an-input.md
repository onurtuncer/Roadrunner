# 27. Performance requirements are an input beside the mission (amends ADR-0019, ADR-0026)

Status: Accepted (2026-11-26)

## Context

ADR-0019 lists the constraints on the thrust loading and says their
parameters live in `config/constraints.yaml`, but the file did not exist.
The owner wants the mission and its constraints defined as an input first,
and the coupled mission and constraint analysis done afterwards.

## Decision

- **`config/constraints.yaml` is written and loaded** by
  `roadrunner_re.constraint_inputs`, with the provenance rule of ADR-0005:
  every requirement carries a `basis` of ledger evidence and/or a stated
  assumption, and every number it owns has bounds.
- It holds the six constraints of ADR-0019: vertical launch, vertical
  landing thrust floor (the only `upper_bound`), dash, climb, sustained
  load factor and loiter ceiling.
- **A requirement does not repeat its flight condition.** Where it belongs
  to a mission segment it names it (`from_segment`), so Mach number,
  altitude and the day stay single-sourced in the mission. `weight_at`
  names the segment at whose start the weight fraction beta is taken, so
  the constraint analysis needs no weights of its own.
- **Notebook 14 (`mission_profile`) also quotes and tabulates the
  requirements** and adds them to `out/mission_profile.yaml`. It still
  draws no constraint curves and flies no weights; those belong to the
  coupled analysis (ADR-0019, `solve_design_point()`).
- **The requirement types follow UCK 474E Lecture 2**: cruise and dash
  (case I), climb (II), sustained turn (III) and service ceiling (VIII).
  The ground-roll cases (V, VI, VII, IX) do not apply to a vertical
  vehicle and are replaced by the launch and landing requirements.
  Horizontal acceleration (IV) is left out because the mission has no
  acceleration requirement; it can be added with its own ADR if wanted.
- The constraint-owned numbers are assumptions: launch margin, landing
  floor fraction, climb rate, sustained load factor, loiter climb rate.
  They join the uncertain inputs of ADR-0020.

## Consequences

- The mission and its requirements can be reviewed, argued with and
  changed in two YAML files before any analysis exists.
- The launch margin is the number that will size the engine and has no
  source at all; it is expected to rank first in the sensitivity analysis.
- The lecture's constraint forms need a drag polar (K1, K2, C_D0, C_DR)
  referred to the same area as the wing loading. The owner's hand
  estimate (ADR-0026) is referred to the body cross-section, not a wing,
  so the constraint analysis must say which area it uses and convert.
  The lecture's algebraic turbojet thrust lapse is available as a quick
  check on the pyCycle engine deck.
- Static installation (ADR-0011) is not a constraint input and is not
  represented here.
