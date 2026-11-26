# 20. Uncertainty quantification and sensitivity analysis (amends ADR-0006)

Status: Accepted (2026-11-26)

## Context

Open-source data about this vehicle is unreliable: a secondary-source
length, marketing adjectives, pixel measurements, aerodynamic estimates,
assumed mission values. ADR-0006 already rejects the idea of a single
answer and produces a feasible family, but it does not say how input
uncertainty is characterised, how it is propagated, or which inputs are
responsible for the spread. Without that the study cannot say what would
have to be known better to narrow the answer.

## Decision

- **Every uncertain input declares a distribution**, not only bounds.
  Ledger entries and assumptions gain a `dist:` field (`uniform` between
  `low` and `high` by default; `triangular` or `normal` only with a
  stated reason). Tier sets the default width policy.
- **Forward propagation.** A space-filling sample (seeded, size in
  config) of all uncertain inputs is pushed through the forward model
  (aero, engine deck, mission, constraints, mass closure). Outputs are
  reported as medians with 5th to 95th percentile intervals, both
  unconditional and after feasibility rejection (ADR-0006).
- **Sensitivity analysis**, in three layers:
  1. *Local*: normalised derivatives (elasticities) at the nominal
     point, shown as tornado charts.
  2. *Screening*: Morris elementary effects over the full input set, to
     separate influential inputs from negligible ones.
  3. *Global*: variance-based Sobol first-order and total indices on the
     screened set, with bootstrap confidence intervals and a convergence
     check against sample size.
- Quantities of interest are fixed in config: thrust per engine, engine
  mass flow, take-off mass, fuel fraction, TSFC at cruise, dash Mach
  margin, landing thrust-floor margin, range.
- **Model-form uncertainty is carried explicitly** where it is known:
  engine-deck interpolation error (ADR-0015), the spread between the two
  aerodynamic methods (ADR-0016), and the blind-validation error
  (ADR-0012) enter as additional uncertain factors.
- The forward model stays pure and fast (ADR-0006); pyCycle is reached
  only through the engine deck. An open-source sensitivity library does
  the index estimation; SALib is the working candidate.
- The summary states, for each quantity of interest, **which evidence
  item contributes most to its uncertainty**.

## Consequences

- Results come with intervals that have a stated origin, and a ranked
  list of what to find out next.
- Sobol indices assume independent inputs; known dependencies (for
  example geometry items that all scale with the one length anchor) must
  be modelled through a shared parent variable, not sampled separately.
- Sample counts for global indices are large; this is the main CI cost
  and the reason the forward model must not call pyCycle directly.
- Distribution shapes are themselves judgement; the report shows how
  conclusions change under an alternative shape for the top-ranked
  inputs.
