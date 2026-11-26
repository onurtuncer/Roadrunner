# 5. Evidence ledger: every external number carries provenance and a tier

Status: Accepted (2026-11-26)

## Context

In the tailsitter study the inputs were our own choices, so "rationale in
a YAML comment" (ADR-0002) was enough. Here the inputs are *claims about
someone else's vehicle*, and the manufacturer has withheld speed, range,
mass and dimensions. What exists is thin and uneven: a few stated facts,
marketing comparatives, press estimates, and imagery. Mixing these
silently is the standard way reverse-engineering studies go wrong.

## Decision

All external evidence lives in `config/evidence/*.yaml`, one entry per
datum, never inline in other config files. Each entry has:

```yaml
- id: length_overall
  quantity: length_overall_m
  value: 1.5            # nominal
  low: 1.4              # bounds actually used downstream
  high: 1.7
  tier: B
  source: <URL or citation>
  accessed: 2026-11-26
  note: secondary source; executive remark "shorter than he is"
```

Tiers:

- **A** Stated by the manufacturer (release, on-record quote).
- **B** Reported by a secondary source, or measured by us from
  imagery (ADR-0007).
- **C** Inferred by analogy from the reference-engine class (ADR-0010)
  or engineering judgement.
- **X** Marketing comparative with no stated baseline ("most
  power-dense", "10x range"). Recorded, **never used as an input**;
  tested as a hypothesis at the end.

Other config files reference evidence by `id`. A loader test fails if any
physical input in `config/` has neither an evidence `id` nor an explicit
`assumption:` rationale.

Seed entries known today: twin turbojets with thrust vectoring, engines
built in-house (A); VTOL launch and recovery on three landing legs (A);
"high subsonic" (A, qualitative); length about 1.5 m (B); "Group 3"
class (B, must be reconciled with "high subsonic" before use).

## Consequences

- A reader can trace any result to what is known versus what is assumed.
- Bounds, not just nominal values, are first-class and feed ADR-0006.
- Adding a datum costs a ledger entry; updating one when better evidence
  appears is a reviewed config diff that re-converges the pipeline.
