# 11. Installation and thrust vectoring enter as bounded loss terms

Status: Accepted (2026-11-26)

## Context

Uninstalled datasheet thrust is not what lifts the vehicle. Between the
cycle and the vehicle sit the inlet, the vectoring nozzle, power
extraction, and the launch environment (static inflow in a vertical
attitude, possible exhaust re-ingestion near the ground or the launch
container). None of these can be modelled from first principles with the
evidence available, yet ignoring them would bias engine thrust low by an
unknown amount.

## Decision

Each effect is one named, bounded coefficient in
`config/installation.yaml`, applied in `src/roadrunner_re/installation.py`:

- Inlet total-pressure recovery, separately for static (OP1/OP2) and
  forward flight (OP3/OP4).
- Nozzle velocity and discharge coefficients.
- Thrust vectoring: geometric loss from the vector angle held in reserve
  for control at OP1/OP2, plus a turning-loss coefficient.
- Shaft power extraction for electrical load.
- Inlet temperature rise from exhaust re-ingestion at launch and landing.

All carry `low`/`high` bounds and are sampled in the inverse problem
(ADR-0006). The vectoring *mechanism* (vanes, gimballed nozzle, other) is
recorded in the evidence ledger if imagery resolves it, but the model
does not depend on it.

Not modelled: nozzle actuation dynamics, control authority, plume
impingement loads, launch-container internal flow.

## Consequences

- Installed and uninstalled thrust are distinct quantities everywhere in
  code, handoffs and reports; conflating them is a test failure.
- The sensitivity study shows which installation term matters most and
  is therefore worth a better model or a CFD case later.
- Re-ingestion is a single scalar; that crude treatment is a standing
  finding to revisit, not a claim of accuracy.
