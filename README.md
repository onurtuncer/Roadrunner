# Roadrunner: Propulsion Reverse-Engineering Study

[![CI](https://github.com/onurtuncer/Roadrunner/actions/workflows/ci.yml/badge.svg)](https://github.com/onurtuncer/Roadrunner/actions/workflows/ci.yml)
[![Design Pipeline](https://github.com/onurtuncer/Roadrunner/actions/workflows/design-pipeline.yml/badge.svg)](https://github.com/onurtuncer/Roadrunner/actions/workflows/design-pipeline.yml)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://onurtuncer.github.io/Roadrunner/)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-green.svg)](LICENSE)

**Documentation:** <https://onurtuncer.github.io/Roadrunner/>

A course project in aircraft propulsion: estimate, from public
information only, what the propulsion system of the Anduril Roadrunner
(a small twin-turbojet, thrust-vectored, vertical take-off and landing
air vehicle) must look like.

The manufacturer has published almost no figures. The study therefore
does not produce "the answer". It produces the range of engine and
vehicle parameters that are consistent with the public evidence, how
uncertain each one is, and which missing fact matters most.

## Status

Planning stage. The architecture decision records are written; code,
configuration and notebooks follow. See [`adr/`](adr/README.md).

## Method

1. Collect public evidence in a ledger, each item with a source and bounds.
2. Measure geometry from scaled public imagery.
3. Estimate aerodynamics from that geometry.
4. Define a sample mission; run constraint analysis and mission analysis
   on a standard atmosphere.
5. Choose the engine pair from a catalogue of purchasable turbojets
   (PBS, JetCat, AMT), with [pyCycle](https://github.com/OpenMDAO/pyCycle)
   models anchored to each vendor datasheet for hot-day, altitude and
   part-throttle performance.
6. Propagate the input uncertainty and rank the inputs by sensitivity.

## Repository layout

```
adr/         architecture decision records (start here)
config/      inputs, evidence ledger, mission profiles     (planned)
src/         all physics, as the roadrunner_re package     (planned)
notebooks/   thin Jupyter notebooks, run in a fixed order  (planned)
out/         handoff files written by the notebooks        (planned)
tests/       unit tests and regression pins                (planned)
```

## Scope

Propulsion of the baseline vehicle only, for teaching. Payload is
treated as a mass and a volume. Weapon, seeker and guidance topics are
out of scope. All results are estimates, not specifications.

## License

Public domain ([Unlicense](LICENSE)).
