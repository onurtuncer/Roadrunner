# 3. Inherit the tailsitter conventions; local amendments to ADR-0001/0002

Status: Accepted (2026-11-26)

## Context

ADR-0001 and ADR-0002 were copied verbatim from `tailsitter-uav-design`.
Their principles are what we want here, but their wording names things this
repo does not have: `src/conceptual_design/`, `run_sizing_loop`, "NB2–NB8",
a `cfd/` consumer stage. The tailsitter repo also learned two lessons late
that this repo can adopt on day one: thin notebooks (its ADR-0013, after
~4,000 lines of Python had leaked into notebooks) and a single
design-point call site.

## Decision

ADR-0001 and ADR-0002 stand, read with these substitutions:

- Package is `src/roadrunner_re/` (not `conceptual_design`).
- Pipeline is `config/ -> src/ -> notebooks/ -> out/`. There is no `cfd/`
  stage; if one is added later it gets its own ADR and stays a pure
  consumer of `out/`.
- The coupled solve is `roadrunner_re.design_point.solve_design_point()`,
  the **only** call site notebooks use to reconstruct the design point.
- **Thin notebooks from the first commit**: notebooks hold parameter
  blocks, module calls, narrative and short interpretive prints. Physics,
  plots (`plots/`), tables (`reports.py`) and the shared prelude
  (`notebook.nb_setup()`) live in `src/`.
- **SI units throughout**, no `g_c`; angles in radians inside `src/`,
  degrees only at the config/reporting boundary. Unit suffixes on every
  config key and dataclass field (`_m`, `_kg`, `_K`, `_Pa`, `_N`).
- ADR discipline as in the tailsitter repo: one file per decision,
  never rewritten, superseded or amended by a later ADR, indexed in
  `adr/README.md`.

## Consequences

- Anyone who knows the tailsitter repo can navigate this one unchanged.
- No extraction refactor later; the byte-diff discipline ("moving code
  must not move a number") applies from the start.
- ADR-0001/0002 keep stale tailsitter wording; this ADR is the
  authoritative reading of them.
