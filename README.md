# Roadrunner: Propulsion Reverse-Engineering Study

[![CI](https://github.com/onurtuncer/Roadrunner/actions/workflows/ci.yml/badge.svg)](https://github.com/onurtuncer/Roadrunner/actions/workflows/ci.yml)
[![Design Pipeline](https://github.com/onurtuncer/Roadrunner/actions/workflows/design-pipeline.yml/badge.svg)](https://github.com/onurtuncer/Roadrunner/actions/workflows/design-pipeline.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://onurtuncer.github.io/Roadrunner/)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-green.svg)](LICENSE)

**Documentation:** <https://onurtuncer.github.io/Roadrunner/>

A course project in aircraft propulsion: estimate, from public
information only, what the propulsion system of a small twin-turbojet,
thrust-vectored, vertical take-off and landing air vehicle must look
like.

Almost no figures are published for this class of vehicle. The study
therefore does not produce "the answer". It produces the range of engine
and vehicle parameters that are consistent with the public evidence, how
uncertain each one is, and which missing fact matters most.

## Status

Early stage. The architecture decision records are written, the
package skeleton exists and the first notebook (the evidence ledger)
runs. No engineering results yet. See [`adr/`](adr/README.md).

## Method

1. Collect public evidence in a ledger, each item with a source and bounds.
2. Take the aerodynamics from the owner's hand estimate (no measured
   geometry exists, so there is no imagery or aerodynamics stage).
3. Define a sample mission; run constraint analysis and mission analysis
   on a standard atmosphere.
4. Choose the engine pair from a catalogue of purchasable turbojets
   (PBS, AMT), with [pyCycle](https://github.com/OpenMDAO/pyCycle)
   models anchored to each vendor datasheet for hot-day, altitude and
   part-throttle performance.
5. Propagate the input uncertainty and rank the inputs by sensitivity.

## Running it locally

Python 3.12 (what CI uses; 3.10 or later should work). From the repository root:

```
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux, macOS
python -m pip install --upgrade pip
pip install -r requirements.txt
```

That installs the package (editable), pyCycle, Jupyter and the test
tools; git is not needed. Then:

```
pytest                          # unit tests, cycle tests and regression pins
jupyter lab notebooks           # run 01_ ... 13_ in order
```

Each notebook reads only the `out/` handoffs of the notebooks before it,
so run them in prefix order after a change. `08_off_design` takes about
two minutes (pyCycle).

## Repository layout

```
adr/         architecture decision records (start here)
config/      inputs, evidence ledger, mission, engine catalogue
src/         all physics, as the roadrunner_re package
tests/       unit tests and regression pins
notebooks/   thin Jupyter notebooks, run in prefix order (01_ to 13_)
out/         handoff files written by the notebooks
```

## Scope

Propulsion of the baseline vehicle only, for teaching. Payload is
treated as a mass and a volume. All results are estimates, not
specifications.

## License

Public domain ([Unlicense](LICENSE)).
