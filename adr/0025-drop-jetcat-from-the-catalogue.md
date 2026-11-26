# 25. JetCat engines are dropped from the catalogue (amends ADR-0023)

Status: Accepted (2026-11-26)

## Context

ADR-0023 names PBS, JetCat and AMT as the vendors of the candidate
catalogue. The owner has asked for the JetCat engines to be removed.

## Decision

- `jetcat_p400_pro`, `jetcat_p550_pro` and `jetcat_p1000_pro` are removed
  from `config/reference_engines.yaml`. The catalogue is nine engines
  from PBS and AMT.
- ADR-0023 is otherwise unchanged; "PBS, JetCat, AMT at present" now
  reads "PBS and AMT at present".
- The handoffs `out/technology.yaml` and `out/validation.yaml` are
  regenerated and the regression pins updated in the same commit.

## Consequences

- The technology bounds narrow and the mass power law is refitted to nine
  engines.
- The datasheet cross-check of the fuel density (ADR-0010) now rests on
  two engines instead of five; the test threshold is lowered to match.
- The leave-one-out blind test (ADR-0012) covers fewer engines (specific
  thrust 2 of 5 inside the predicted interval, SFC 1 of 3). The
  catalogue is thin, and the result is correspondingly weak evidence for
  or against the method.
