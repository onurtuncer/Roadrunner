# CLAUDE.md

Reverse-engineering study of the propulsion system of the Anduril
Roadrunner (a ~1.5 m, twin-turbojet, thrust-vectored, reusable VTOL air
vehicle), done as a propulsion course project. Python physics package +
Jupyter notebooks, wired into CI. Conventions are inherited from
`onurtuncer/tailsitter-uav-design`; when in doubt, do it the way that
repo does.

## Current state (update this section as it changes)

- Only the ADRs exist. No `config/`, `src/`, `notebooks/`, `tests/` or
  `pyproject.toml` yet.
- ADR-0001 to 0014 are Accepted (0003 to 0014 on 2026-11-26). They are
  the basis for all work; a change of direction needs a new ADR that
  amends or supersedes, not an edit.
- Next step is the repo skeleton (`pyproject.toml`, `config/`,
  `src/roadrunner_re/`, `tests/`, CI) and then the notebooks in
  ADR-0013 order.
- Everything below the next heading describes the *intended* structure
  per the ADRs.

## What kind of study this is

This is an **inverse problem**, not a forward design (ADR-0006). The
vehicle exists; its mass, thrust, speed and range are unpublished. The
output is a *feasible family* of parameter sets consistent with public
evidence, reported as intervals, plus one designated nominal point.
Never present a result as "Roadrunner has X". Say "X is consistent with
the public evidence, within these bounds".

## Scope boundary (ADR-0004)

- In: the propulsion system, and only as much vehicle (mass, drag,
  mission fuel) as is needed to generate propulsion requirements.
- Subject is the baseline vehicle. Payload is a mass and a volume.
- Out, permanently: warhead, fuzing, seeker, guidance, engagement
  kinematics, signature, countermeasures, command-and-control. Do not
  add these even if asked in passing; raise it with the owner instead.
- Public sources only. No export-controlled or proprietary material.

## Architecture: the pipeline

```
config/*.yaml  ->  src/roadrunner_re/  ->  notebooks/  ->  out/
(inputs+evidence)  (ALL physics)           (orchestrate)   (handoffs)
```

Notebook order is load-bearing (ADR-0013). Each writes one YAML handoff
to `out/` and reads only earlier handoffs:

1. `evidence_ledger` -> `out/evidence.yaml`
2. `geometry_from_imagery` -> `out/geometry.yaml`
3. `reference_engines` -> `out/technology.yaml`
4. `method_validation` -> `out/validation.yaml`
5. `vehicle_requirements` -> `out/requirements.yaml`
6. `mission_mass_closure` -> `out/vehicle.yaml`
7. `cycle_design_point` -> `out/cycle.yaml`
8. `engine_flowpath_sizing` -> `out/engine.yaml`
9. `off_design` -> `out/off_design.yaml`
10. `feasible_family` -> `out/feasible_family.yaml`
11. `design_summary` (pure reader, writes nothing)

The mass/engine coupling is resolved inside
`roadrunner_re.design_point.solve_design_point()`, the **single call
site** every notebook uses to reconstruct the design point. No
back-edges: a downstream discovery is fed back by changing
`config/`/`src/` and re-running, never by editing an `out/` file.

Intended `src/roadrunner_re/` layout: `notebook.py` (`nb_setup()`),
`design_point.py`, `evidence.py`, `geometry.py`, `vehicle/` (mass
closure, drag, mission fuel), `cycle/` (gas model, components, design
point, off-design), `installation.py`, `flowpath.py`, `inverse.py`
(sampling and rejection), `plots/`, `reports.py`, `design_summary.py`.

## Hard rules

- **No magic numbers in Python** (ADR-0002). Every physical parameter
  lives in `config/*.yaml`. Only numerical tolerances and documented
  guard limits may be named module constants.
- **No external number without provenance** (ADR-0005). Anything about
  the real vehicle or a real engine goes in `config/evidence/` or
  `config/reference_engines.yaml` with source, access date, tier
  (A stated / B reported or measured / C inferred / X marketing) and
  `low`/`high` bounds. Other config refers to it by `id`. Do not supply
  such numbers from memory; look them up and cite, or mark them as an
  explicit `assumption:` with rationale.
- **Tier-X claims are never inputs.** They are hypotheses tested against
  the feasible family at the end.
- **All physics lives in `src/`; notebooks are thin** (ADR-0003):
  parameter blocks, module calls, narrative, short prints. Plots and
  tables live in `src/` too. Moving code between a notebook and `src/`
  must not change a byte of the `out/` handoffs.
- **SI units, no `g_c`.** Unit suffix on every config key and field
  (`_m`, `_kg`, `_K`, `_Pa`, `_N`, `_kg_s`). Radians inside `src/`,
  degrees only at the config/report boundary.
- **Station numbering is ARP755** in code, handoffs and text.
- **Installed and uninstalled thrust are different quantities** and are
  always named as such (ADR-0011).
- **The forward model is pure and fast**: no global state, no file I/O,
  no plotting inside anything the inverse problem calls (ADR-0006).
- **Sampling is seeded.** Seed and sample count are config values.
- **Images of the vehicle are not committed**; record URL, access date
  and pixel measurements instead (ADR-0007).
- **Validation engines stay held out** of the technology-level
  derivation (ADR-0012).
- **ADRs**: architectural decisions go in `adr/`, one file each, never
  rewritten; amend or supersede with a new ADR and update
  `adr/README.md`.
- **Changelog**: when a version is tagged, write a `CHANGELOG.md` entry.

## Operating points (ADR-0009)

- OP1 vertical launch: sea-level static, hot day, take-off mass. This
  is the **cycle design point**.
- OP2 vertical landing: thrust equals landing weight; a thrust-floor
  and thrust-response check.
- OP3 dash: high subsonic at altitude.
- OP4 cruise/loiter: sets the fuel fraction via part-throttle TSFC.

The tension between OP1 (thrust above weight), OP4 (throttled, poor
TSFC) and OP2 (stable low thrust) is the pedagogical core. Keep it
visible in notebooks and summaries.

## Tools

- The cycle model is in-house (ADR-0010). pyCycle and GasTurb are
  verification oracles only: their numbers are pinned in `tests/`, they
  are never runtime dependencies.
- CI (ADR-0014): `ci.yml` (ruff, pytest), `design-pipeline.yml`
  (execute all notebooks, regression pins, Pages on `main`),
  `release.yml` (on `v*` tags). Version comes from git tags via
  setuptools-scm; never edit a version number by hand.

## Tests and regression pins

- Unit tests pin the cycle model against oracle values.
- Loader tests enforce the provenance rule.
- Blind-validation bands (ADR-0012) are tests; breaking them fails CI.
- Design-regression tests pin the nominal point exactly and the
  feasible-family bounds to a stated tolerance. **An intentional change
  to results updates the pins in the same commit.** A failing pin you
  did not expect means the study drifted.

## Working agreements

- Decisions before code: if a task needs an architectural choice that no
  ADR covers, draft the ADR first.
- Report margins and standing findings honestly (a constraint that
  barely closes, a crude model such as the scalar re-ingestion term);
  collect them programmatically in `design_summary`.
- Run tests with `pip install -e ".[dev]"` then `pytest`; lint with
  `ruff check src tests`.
