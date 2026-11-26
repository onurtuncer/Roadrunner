# CLAUDE.md

Reverse-engineering study of the propulsion system of the Anduril
Roadrunner (a ~1.5 m, twin-turbojet, thrust-vectored, reusable VTOL air
vehicle), done as a propulsion course project. Python physics package +
Jupyter notebooks, wired into CI. Conventions are inherited from
`onurtuncer/tailsitter-uav-design`; when in doubt, do it the way that
repo does.

## Current state (update this section as it changes)

- Implemented modules: `config.py` (paths, YAML), `uncertain.py` (value
  with bounds and distribution), `evidence.py` (ledger loader and
  handoff), `mission_profile.py` (mission loader with the provenance
  check), `engine_catalogue.py` (catalogue loader, no unit conversion
  yet), `atmosphere.py` (ISA, tested against published tables),
  `geometry.py` (pixel measurements to length intervals, engine
  envelope), `notebook.py`, `reports.py`. Everything else in the layout
  below is still to be written.
- Notebook 1 (`evidence_ledger`) exists and writes `out/evidence.yaml`;
  it is the only entry in `NOTEBOOK_ORDER` in `design-pipeline.yml`.
  `tests/test_design_outputs.py` pins the handoffs and runs in the
  pipeline, not in `ci.yml`.
- **Geometry is blocked on measurement.** `config/evidence/imagery.yaml`
  lists five public image sources but holds NO pixel measurements, so
  notebook 2 (`geometry_from_imagery`) is not written and nothing
  downstream of it (aerodynamics, engine fit) can run on real numbers.
  The measurements must be taken by someone who can view the images
  (in a browser, or from images the owner attaches). Do not invent
  pixel coordinates or dimensions.
- `config/` holds `atmosphere.yaml`, `geometry.yaml`,
  `evidence/claims.yaml`, `evidence/vehicle.yaml`,
  `evidence/imagery.yaml`, `missions/sample.yaml` and
  `reference_engines.yaml` (eleven purchasable turbojets from PBS,
  JetCat and AMT; several fields still `null`, three PBS entries from a
  secondary source).
- The only quantified evidence is overall length (1.5 m, 1.4 to 1.8),
  a reported mass (85 kg) and a reported top speed (700 km/h); the last
  two come from one uncorroborated secondary source.
- Dependencies for later stages are optional extras in `pyproject.toml`
  (`cycle`, `aero`, `uq`); pyCycle is pinned there and is not yet
  imported anywhere.
- **ADR-0001 to 0023 are all Accepted** (0003 to 0023 on 2026-11-26).
  0013 is superseded by 0021; 0006, 0008, 0009, 0010, 0012, 0014 and
  0015 carry amendments (see `adr/README.md`). Read an amended ADR
  together with the ADRs that amend it.
- A change of direction needs a new ADR that amends or supersedes, not
  an edit of an accepted one.
- Next step is the pixel measurements, then `geometry_from_imagery`,
  then the remaining notebooks in ADR-0021 order. `reference_engines`
  (notebook 4) does not depend on geometry and can go ahead.
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

Notebook order is load-bearing (ADR-0021). Each writes one YAML handoff
to `out/` and reads only earlier handoffs:

1. `evidence_ledger` -> `out/evidence.yaml`
2. `geometry_from_imagery` -> `out/geometry.yaml`
3. `aerodynamics` -> `out/aero.yaml`
4. `reference_engines` -> `out/technology.yaml`
5. `method_validation` -> `out/validation.yaml`
6. `engine_deck` -> `out/engine_deck.yaml`
7. `constraint_analysis` -> `out/constraints.yaml`
8. `mission_analysis` -> `out/mission.yaml`
9. `engine_selection` -> `out/engine_selection.yaml`
10. `cycle_design_point` -> `out/cycle.yaml`
11. `off_design` -> `out/off_design.yaml`
12. `uncertainty_and_sensitivity` -> `out/uq.yaml`
13. `design_summary` (pure reader, writes nothing)

The constraint/mission/mass/engine coupling is resolved inside
`roadrunner_re.design_point.solve_design_point()`, the **single call
site** every notebook uses to reconstruct the design point. No
back-edges: a downstream discovery is fed back by changing
`config/`/`src/` and re-running, never by editing an `out/` file.

Intended `src/roadrunner_re/` layout: `notebook.py` (`nb_setup()`),
`design_point.py`, `evidence.py`, `geometry.py`, `atmosphere.py`,
`aero/`, `vehicle/` (mass build-up), `mission.py`, `constraints.py`,
`cycle/` (pyCycle model, datasheet calibration, unit boundary, engine
deck), `engine_selection.py`, `installation.py`, `inverse.py` (sampling and rejection), `uq.py`
(propagation, Morris, Sobol), `plots/`, `reports.py`,
`design_summary.py`.

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
  no plotting inside anything the sampler calls (ADR-0006).
- **pyCycle is never called inside a sampling loop.** Samplers read the
  engine deck; the nominal point and family corners are re-run through
  pyCycle directly (ADR-0015).
- **One atmosphere**: ISA from `atmosphere.py`; a flight condition is
  `(altitude_m, mach, dT_isa_K)`; pyCycle must agree with it (ADR-0017).
- **The mission is an input** (`config/missions/sample.yaml`). Its
  shape follows the manufacturer's qualitative claims; its numbers are
  assumptions with bounds, all sampled in the uncertainty analysis
  (ADR-0018). No public source gives any of those numbers.
- **The engine deck is generated here** by the repo's pyCycle model; no
  external deck exists or is used (ADR-0015).
- **Every uncertain input has a distribution**, and every headline
  result has an interval and a sensitivity ranking (ADR-0020).
- **SI at the pyCycle boundary**: native pyCycle units never leave the
  `cycle/` wrapper.
- **Sampling is seeded.** Seed and sample count are config values.
- **Images of the vehicle are not committed**; record URL, access date
  and pixel measurements instead (ADR-0007).
- **The engine is selected, not designed** (ADR-0023): two identical
  engines from `config/reference_engines.yaml`, requirements derived,
  lowest closed take-off mass wins, deterministically. "No catalogue
  engine fits" is a valid result to report, not an error to design
  around.
- **Paper exercise**: "purchasable" means a catalogue product with a
  public datasheet. Do not consider, record or filter on price, lead
  time or export controls (ADR-0023).
- **Catalogue numbers come from the vendor datasheet** with a source
  URL. `null` means not yet retrieved; never fill one from memory.
- **Validation is leave-one-out** over the catalogue: the engine being
  predicted is excluded from the technology-level derivation
  (ADR-0012, ADR-0023).
- **ADRs**: architectural decisions go in `adr/`, one file each, never
  rewritten; amend or supersede with a new ADR and update
  `adr/README.md` (CI fails if the index and the files disagree).
- **Docs** are the README, the ADRs and the rendered notebooks,
  published to <https://onurtuncer.github.io/Roadrunner/>. Do not write
  site-only content.
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

- The cycle model is pyCycle on OpenMDAO (`om-pycycle`, ADR-0015):
  tabular Jet-A thermo for pipeline runs, CEA as a cross-check on the
  nominal point, scaled generic maps off-design. GasTurb is an optional
  off-pipeline cross-check.
- Aerodynamics: a cited semi-empirical build-up plus an open-source
  build-up code on the same geometry (AeroSandbox is the working
  candidate); the spread sets the bounds (ADR-0016).
- Mission and constraint analysis follow Mattingly, Heiser and Pratt
  (ADR-0018, ADR-0019).
- Sensitivity indices from an open-source library (SALib is the working
  candidate) (ADR-0020).
- CI (ADR-0014, ADR-0022): `ci.yml` (ADR index check, ruff, pytest),
  `design-pipeline.yml` (execute all notebooks, regression pins, build
  the docs site with `scripts/build_site.py`, deploy Pages on `main`;
  it is the only workflow that deploys Pages),
  `release.yml` (on `v*` tags). Version comes from git tags via
  setuptools-scm; never edit a version number by hand.

## Tests and regression pins

- Unit tests: atmosphere against published tables and against pyCycle;
  a closed-form ideal-cycle sanity band on the pyCycle model; engine-deck
  interpolation error on held-out pyCycle points.
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
  `ruff check src tests scripts`.
