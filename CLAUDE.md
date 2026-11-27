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
  check), `engine_catalogue.py` (catalogue loader), `technology.py`, `atmosphere.py` (ISA, tested against published tables),
  `geometry.py` (pixel measurements to length intervals, engine
  envelope), `lapse.py`, `analysis_inputs.py`, `constraints.py`, `mission.py`,
  `design_point.py` (first-iteration coupled analysis, ADR-0029), `engine_model.py` (algebraic and cycle engine models, ADR-0033), `cycle/`
  (incl. `design.py`, ADR-0030, and `offdesign.py`, ADR-0032), `off_design.py`, `validation.py`, `notebook.py`, `reports.py`,
  `plots/`. Everything else in the layout
  below is still to be written.
- Notebooks 1, 2, 5, 6, 7, 8, 9, 10, 11 and 12 exist (see the list under "Architecture"),
  write `out/evidence.yaml`, `out/mission_profile.yaml`, `out/technology.yaml`,
  `out/validation.yaml`, `out/constraints_preliminary.yaml`,
  `out/mission_preliminary.yaml`, `out/cycle.yaml`, `out/off_design.yaml`, `out/constraints.yaml` and `out/mission.yaml`,
  and are the entries
  of `NOTEBOOK_ORDER` in `design-pipeline.yml`.
  `tests/test_design_outputs.py` pins the handoffs and runs in the
  pipeline, not in `ci.yml`.
- **pyCycle is in use** (`cycle/turbojet.py`, design point only):
  `run_design_point` (given Tt4) and `match_thrust` (given thrust).
  `validation.py` anchors the model to each datasheet and runs the
  leave-one-out blind test. `tests/test_cycle.py` needs pyCycle, is
  skipped where it is not installed and runs in the pipeline.
- **pyCycle is pinned to an upstream git commit**, not PyPI 4.4.0, whose
  tabular thermo fails under NumPy 2 (see the comment in
  `pyproject.toml`). Do not "tidy" the pin back to the PyPI release
  without checking that release runs.
- **Anchoring method** (decided while building, consistent with
  ADR-0023): compressor and turbine efficiencies are ASSUMED
  (`config/cycle.yaml`); thrust + air flow + pressure ratio give Tt4;
  published fuel flow then gives a lumped combustion efficiency.
  Solving for compressor efficiency from fuel flow instead was tried
  and rejected: it gave efficiencies of 0.54 to 0.73 and Tt4 up to
  1540 K, which are not credible for these engines.
- Validation result (leave-one-out, specific terms; JetCat dropped,
  ADR-0025): specific thrust is inside the predicted interval for 2 of 5
  engines (nominal error -12 to +21 %); SFC for 1 of 3 (-12 to +17 %).
  With nine engines the catalogue is thin and the blind test is weak
  evidence either way. Standing findings: only one engine publishes an
  EGT (model Tt5 is 121 K below it); anchored Tt4 (1088 to 1275 K)
  depends on the assumed efficiencies; the datasheet fuel-density
  cross-check rests on two engines.
- **Off-design is built** (notebook 10, `cycle/offdesign.py`, `off_design.py`,
  ADR-0032): the sized engine run in a pyCycle multi-point problem with
  scaled generic maps (shaft speed balances power, air flow balances the
  throat area; throttle by Tt4 or thrust). Points below 0.80 of design shaft
  speed are flagged invalid (generic maps misbehave there) and never used
  downstream. Results: the cycle's maximum-power lapse is within 6 % (mean)
  and 10.5 % (max) of the algebraic lapse, which is optimistic at Mach 0.3 to
  0.6 by 6 to 9 %; SFC is flat to about 60 % thrust, 28 to 36 % worse at 30 %;
  the loiter needs about 28 % of maximum thrust, where real SFC is 1.73 times
  the preliminary constant TSFC (1.29 of it the flight condition); landing
  needs 66 % of maximum thrust and is met with margin. Fuel is ideal over a
  constant median combustion efficiency (0.855), so part-throttle fuel is
  probably understated. The deck is the handoff's grid and part-throttle
  tables (specific thrust, SFC and relative air flow, ADR-0024); a sampler
  deck is built when notebook 14 needs it.
- `technology.py` is datasheet arithmetic only (figures of merit,
  catalogue bounds, mass power law, implied fuel density). Result so
  far: specific thrust is 594 to 627 N s/kg for three of the five
  engines that publish an air flow (the two TJ40 cores sit at 506); SFC is 0.116
  to 0.150 kg/(N h), improving with size.
- **Geometry is blocked on measurement.** `config/evidence/imagery.yaml`
  lists five public image sources but holds NO pixel measurements, so
  notebook 2 (`geometry_from_imagery`) is not written and nothing
  downstream of it (aerodynamics, engine fit) can run on real numbers.
  The measurements must be taken by someone who can view the images
  (in a browser, or from images the owner attaches). Do not invent
  pixel coordinates or dimensions.
- `config/` holds `atmosphere.yaml`, `geometry.yaml`,
  `evidence/claims.yaml`, `evidence/vehicle.yaml`,
  `evidence/imagery.yaml`, `missions/sample.yaml`, `constraints.yaml` (the performance
  requirements as an input, ADR-0027: launch margin, landing floor, dash,
  climb, manoeuvre, loiter ceiling; conditions taken from the mission), `fuel.yaml`,
  `cycle.yaml`, `validation.yaml` and
  `reference_engines.yaml` (nine purchasable turbojets from PBS
  and AMT, all from vendor material; some fields still `null`,
  and PBS datasheet revisions disagree in places, as noted per entry).
- `config/aero_estimate.yaml` is the owner's hand aerodynamic estimate
  (tier C, +/-30 %, photo-scaled assumptions; ADR-0026): S_ref 0.071 m2
  (missile convention), C_N_alpha about 15 /rad, C_D0 about 0.20, K about
  0.06, (L/D)max about 4.5. It is an input, not a measurement; it does not
  unblock geometry, and its numbers are correlated.
- The only quantified evidence is overall length (1.5 m, 1.4 to 1.8),
  a reported mass (85 kg) and a reported top speed (700 km/h); the last
  two come from one uncorroborated secondary source.
- Dependencies are optional extras in `pyproject.toml`: `cycle`
  (in use), `aero` and `uq` (not yet imported anywhere).
- **ADR-0001 to 0033 are all Accepted** (0003 to 0033 on 2026-11-26).
  0013 is superseded by 0021; 0006, 0007, 0008, 0009, 0010, 0012, 0014,
  0015, 0016, 0018, 0019, 0021, 0022, 0023, 0026, 0029, 0030 and 0031 carry
  amendments (see `adr/README.md`). Read an amended ADR together with the
  ADRs that amend it.
- A change of direction needs a new ADR that amends or supersedes, not
  an edit of an accepted one.
- **First-iteration coupled analysis exists (ADR-0029)** and is rough by
  intent: algebraic turbojet lapse plus constant catalogue-median TSFC,
  hand-estimate polar on `S_ref`, `config/analysis.yaml`; now the
  *preliminary* pair (notebooks 7, 8, ADR-0031). Nominal point
  (85 kg): vertical launch binds, T_SL/W_TO 1.47, 614 N per engine, fuel
  14.1 kg with reserve. The cycle analysis and engine deck replace the
  lapse; take-off mass is swept, not solved (no ADR-0008 build-up).
- **On-design cycle point exists (ADR-0030)**: pyCycle at OP1 (hot-day SLS) for
  the launch thrust, 542 N per engine -> 0.95 kg/s air, specific thrust 568
  N s/kg, Tt4 anchored 1232 K; bounds one input at a time.
- **Cycle-based analysis pair is built (notebooks 11, 12, ADR-0033)**: the same
  `solve_design_point()` with `inputs.with_engine(CycleEngine(off_design))`
  (`engine_model.py`; lapse and part-throttle SFC interpolated from
  `out/off_design.yaml`, `OutsideEngineModel` outside the grid, no
  extrapolation). Nominal point (85 kg): vertical launch still binds, T_SL/W_TO
  1.469, 612 N per engine; flight requirements need 6 to 9 % more thrust loading
  (cycle lapse is lower); mission fuel 19.9 kg against 12.8 kg preliminary
  (+55 %, loiter 1.71 times: it runs at about 28 % throttle), 21.9 kg with
  reserve, implied empty mass 53.1 kg. Part-throttle fuel is probably still
  understated (constant combustion efficiency). The handoffs carry the
  preliminary values beside the cycle ones.
- Next step is the pixel measurements, then `geometry_from_imagery`, then
  `aerodynamics`, and `engine_selection` (13), which needs no geometry for a
  first thrust and fuel screen, in the order of ADR-0031.
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
- Nothing is modelled beyond the propulsion system and the payload mass
  and volume. Do not add other subsystems even if asked in passing;
  raise it with the owner instead.
- Public sources only. No export-controlled or proprietary material.

## Architecture: the pipeline

```
config/*.yaml  ->  src/roadrunner_re/  ->  notebooks/  ->  out/
(inputs+evidence)  (ALL physics)           (orchestrate)   (handoffs)
```

Notebook order is load-bearing and linear, 15 notebooks numbered by
position (ADR-0031, which supersedes the table of ADR-0021). Each writes
one YAML handoff to `out/` and reads only earlier handoffs. Built (B) or
planned (P); every planned notebook exists as a stub (narrative only, no code,
no handoff) and is in `NOTEBOOK_ORDER`, so the published report shows the whole
sequence:

1. `evidence_ledger` -> `out/evidence.yaml` (B)
2. `mission_profile` -> `out/mission_profile.yaml` (B; quotes and plots the
   sample mission and its requirements; reads only config, ADR-0026,
   ADR-0027)
3. `geometry_from_imagery` -> `out/geometry.yaml` (P, stub; blocked on measurement)
4. `aerodynamics` -> `out/aero.yaml` (P)
5. `reference_engines` -> `out/technology.yaml` (B)
6. `method_validation` -> `out/validation.yaml` (B)
7. `constraint_analysis_preliminary` -> `out/constraints_preliminary.yaml` (B)
8. `mission_analysis_preliminary` -> `out/mission_preliminary.yaml` (B)
9. `cycle_design_point` -> `out/cycle.yaml` (B)
10. `off_design` -> `out/off_design.yaml` (B; ADR-0032)
11. `constraint_analysis` -> `out/constraints.yaml` (B; lapse from 10, ADR-0033)
12. `mission_analysis` -> `out/mission.yaml` (B; thrust and part-throttle SFC from 10, ADR-0033)
13. `engine_selection` -> `out/engine_selection.yaml` (P)
14. `uncertainty_and_sensitivity` -> `out/uq.yaml` (P)
15. `design_summary` (P; pure reader, writes nothing)

There is no `engine_deck` notebook (ADR-0030): any deck for the sampler is
a by-product of `off_design`. File names carry no number; titles carry
"notebook N of 15".

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
- **Specific thrust and SFC, never frontal-area scaling** (ADR-0024).
  Characterise an engine by specific thrust (N s/kg) and SFC; size
  enters only through air mass flow. Do not compute, report or use
  thrust per frontal area or air flow per frontal area. Diameter and
  length are a fit check only. The owner rejected area scaling
  explicitly; lead reports with specific thrust and SFC.
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
  published to <https://onurtuncer.github.io/Roadrunner/> as a design
  report in the tailsitter format (ADR-0028): index generated from
  `NOTEBOOK_ORDER`, notebooks at the site root, figures and handoffs
  alongside. Every notebook's results are published. Do not write
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
