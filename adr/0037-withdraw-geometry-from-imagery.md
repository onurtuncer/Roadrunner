# 37. Geometry from imagery is withdrawn (withdraws ADR-0007, amends ADR-0036)

Status: Accepted (2026-11-27)

## Context

ADR-0007 planned to measure the vehicle's diameters and engine envelope from public
photographs, scaled by the overall length. No measurement was ever taken:
`config/evidence/imagery.yaml` listed five sources and no pixel coordinates. ADR-0036 removed
the geometry and aerodynamics notebooks but kept `geometry.py` and the imagery config for a
later measurement. The owner has decided the study does not need them.

## Decision

- ADR-0007 is withdrawn. The study measures no geometry from imagery.
- Removed: `src/roadrunner_re/geometry.py`, `tests/test_geometry.py`, `config/geometry.yaml`
  and `config/evidence/imagery.yaml`. The evidence loader reads every file in
  `config/evidence/` as a claim list.
- The part of ADR-0036 that kept those files is replaced by this ADR.
- Vehicle imagery is still not committed to the repository (copyright).
- Overall length stays in the evidence ledger (`length_overall`) as evidence about the vehicle.
  It no longer scales anything.

## Consequences

- Aerodynamic size rests on the owner's hand estimate (ADR-0026), whose dimensions are
  photo-scaled assumptions at +/-30 %, not measurements.
- The engine fit check of ADR-0024 (diameter and length) has no measured envelope. Engine
  selection reports engine dimensions beside the hand estimate's body diameter and states that
  the comparison is not a measured constraint.
- ADRs that cite ADR-0007 (0005, 0006, 0013, 0016, 0019, 0023, 0024, 0026) are read with this
  withdrawal in mind.
