# 36. The geometry and aerodynamics notebooks are dropped (amends ADR-0016, ADR-0031)

Status: Accepted (2026-11-27)

## Context

ADR-0031 placed two stubs early in the sequence: `geometry_from_imagery` (pixel measurements
from public imagery) and `aerodynamics` (two independent build-ups on that geometry, the spread
setting the bounds, ADR-0016). Neither can be built: `config/evidence/imagery.yaml` lists image
sources but holds no measurements, and the aerodynamic build-ups need that geometry. Since
ADR-0026 the study has run on the owner's hand aerodynamic estimate (`config/aero_estimate.yaml`,
tier C, +/-30 %). The two stubs only showed the report a stage it does not have. The owner
removed the geometry notebook on `main` (PR #14) and asked for the aerodynamics notebook to go
as well.

## Decision

- `geometry_from_imagery` and `aerodynamics` leave the sequence. The pipeline is 13 notebooks,
  `01_evidence_ledger` to `13_design_summary`, renumbered by position (ADR-0034); titles read
  "notebook N of 13".
- The hand estimate of ADR-0026 is the study's aerodynamics. The two build-ups of ADR-0016 are
  deferred, not rejected: if measured geometry ever exists, adding a geometry or aerodynamics
  notebook takes a new ADR that places it in the sequence.
- `out/geometry.yaml` and `out/aero.yaml` are not produced, and no notebook reads them.
- `geometry.py` and `config/evidence/imagery.yaml` stay; they hold the evidence and the
  conversion a later measurement would need.

## Consequences

- Every aerodynamic number downstream rests on a tier-C estimate with correlated inputs. The
  uncertainty analysis must carry its +/-30 % band, and the summary must report it as a standing
  finding.
- Notebook numbers in ADRs written before this one follow the older sequences; read them as
  logical names.
