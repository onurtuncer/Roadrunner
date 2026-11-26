# 6. Reverse engineering is an inverse problem: report a feasible family

Status: Accepted (2026-11-26)

## Context

The tailsitter study was forward design: requirements in, one converged
design point out. Here the vehicle exists and the unknowns are its
parameters. The evidence (ADR-0005) under-determines them: many
combinations of take-off mass, fuel fraction, engine thrust and cycle
are consistent with what is public. A single "answer" would be false
precision and would teach the wrong lesson.

## Decision

- Formulate the study as a constrained inverse problem.
  - **Unknowns:** take-off mass, fuel fraction, payload mass, installed
    thrust per engine, cycle parameters (pressure ratio, turbine inlet
    temperature, component efficiencies), drag polar coefficients.
  - **Priors:** the `low`/`high` bounds of the evidence ledger and the
    technology-level bounds of ADR-0010.
  - **Constraints:** the forward model must close (ADR-0008) and satisfy
    every operating point (ADR-0009) and the measured geometric envelope
    (ADR-0007).
- Solve by **sampling the priors and rejecting infeasible samples**
  (fixed seed, sample count in config). The surviving set is the
  *feasible family*. It is simple, transparent and teachable; no
  optimiser, no likelihood model.
- Report **intervals and correlations** (e.g. thrust per engine versus
  take-off mass), plus which constraints are active.
- Also carry one **nominal point** (a designated member of the family,
  chosen by a rule stated in config) for narrative, plots and
  regression pins.
- Regression tests pin the nominal point *and* the family's interval
  bounds.

## Consequences

- Headline results read "thrust per engine is between A and B; C if the
  vehicle weighs D", which is what the evidence supports.
- The forward model must be fast (thousands of evaluations) and
  side-effect free; this shapes the code structure from the start.
- New evidence narrows the family visibly, which is a result in itself.
- Tier-X marketing claims can be tested: is the claim true anywhere in
  the feasible family?
