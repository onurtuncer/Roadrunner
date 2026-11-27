# 4. Scope: propulsion of the baseline vehicle, public sources only

Status: Accepted (2026-11-26)

## Context

The subject is the Anduril Roadrunner: a ~1.5 m, twin-turbojet,
thrust-vectored, reusable VTOL air vehicle with a modular payload. This
is a propulsion course project. Without a written boundary the study will
drift into areas that are neither propulsion nor appropriate for an open
university repository.

## Decision

- **In scope:** the propulsion system and exactly as much of the vehicle
  as is needed to generate propulsion requirements: mass, drag, thrust
  constraints, fuel, engine cycle, engine flowpath sizing, installation
  and thrust-vectoring losses, off-design behaviour.
- **Subject is the baseline Roadrunner.** Payload is a mass and a volume
  (`config/payload.yaml`), nothing else.
- **Out of scope:** everything except the propulsion system and the
  payload mass and volume. The mission is an energy-accounting profile
  (launch, climb, dash, loiter, return, vertical landing), not a tactical one.
- **Public sources only**: manufacturer releases, press reporting,
  published imagery and video, open literature, COTS engine datasheets.
  No export-controlled or proprietary material enters the repo.
- **Every result is labelled an estimate.** The repo never states
  "Roadrunner has X"; it states "X is consistent with the public
  evidence, within these bounds" (ADR-0006).

## Consequences

- The work stays a propulsion exercise that students can do and publish.
- Stability, control allocation, structures and CAD are out unless a
  later ADR admits them as requirement generators.
- Results cannot be mistaken for leaked or authoritative specifications.
