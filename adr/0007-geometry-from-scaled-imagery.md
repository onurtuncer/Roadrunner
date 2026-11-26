# 7. Geometry from scaled public imagery, as measured intervals

Status: Accepted (2026-11-26); amended by ADR-0024

## Context

No dimensions are published beyond an approximate overall length.
Geometry is nevertheless the strongest constraint available on the
engines: nacelle and nozzle diameters bound the mass flow, and mass flow
times a plausible specific thrust bounds the thrust. Geometry also sets
wetted area and frontal area for drag.

## Decision

- Measure geometry from public photographs and video frames, scaled by
  the overall length (ledger entry `length_overall`).
- Images are **not committed** (copyright). `config/evidence/imagery.yaml`
  records, per measurement: source URL, access date, frame or image
  identifier, pixel coordinates of the endpoints, and the reference
  length used.
- `src/roadrunner_re/geometry.py` turns pixel measurements into lengths
  and propagates two error sources explicitly: pixel-picking uncertainty
  and perspective/foreshortening (bounded by repeating the measurement on
  at least two independent views where available).
- Outputs are **intervals**: body diameter, engine nacelle outer
  diameter, inlet capture diameter, nozzle exit diameter, engine bay
  length, lifting-surface planform. They are written to `out/geometry.yaml`
  as Tier-B evidence with bounds.
- Derived, not measured: the **engine envelope** (maximum engine diameter
  and length that fit the nacelle, with a configured wall and clearance
  allowance). This is a hard constraint on the engine flowpath sizing.

## Consequences

- The engine is boxed in by something observable rather than by analogy.
- Geometry inherits the uncertainty of the single length anchor; a
  better anchor (a published dimension, an object of known size in frame)
  rescales everything through one ledger edit.
- Students can audit and repeat every measurement from the recorded URLs.
