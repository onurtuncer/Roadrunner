# 12. Validate the method blind on a known engine before applying it

Status: Accepted (2026-11-26); amended by ADR-0023 and ADR-0024

## Context

There is no ground truth for Roadrunner, so the result can never be
checked directly. What *can* be checked is the method. If the same
pipeline, given only the kind of evidence we have for Roadrunner,
recovers the published performance of an engine whose datasheet we do
have, its error on that case is a defensible error bar for the real
study. Without this step the feasible family is unfalsifiable.

## Decision

- Choose one or two **validation engines** from the reference database
  (ADR-0010) with complete public datasheets. They are **held out** of
  the technology-level derivation so the test is not circular.
- Run the engine half of the pipeline **blind**: inputs restricted to
  what imagery would give (outer diameter, length) plus the class
  technology bounds. Predict static thrust, mass flow, fuel consumption
  and engine mass as intervals.
- Compare against the datasheet. Pass criterion: the published value
  lies inside the predicted interval, and the interval width is below a
  configured limit (a prediction of "between 0 and infinity" does not
  pass).
- The validation notebook runs **before** any Roadrunner cycle notebook
  in the pipeline (ADR-0013) and its handoff `out/validation.yaml`
  carries the observed errors, which the summary quotes alongside the
  Roadrunner results.
- Acceptance bands live in `config/validation.yaml`; a model change that
  breaks validation fails CI.

## Consequences

- The study can state how wrong the method was on a known case, which is
  the only honest accuracy statement available.
- One or two engines are sacrificed from the technology database.
- Validation covers the engine model only. The vehicle model (mass,
  drag) remains unvalidated and is flagged as such in the summary.
