"""Technology levels of the purchasable-engine catalogue (ADR-0010, ADR-0023).

Datasheet arithmetic only: no cycle model. For each catalogue engine it
derives the comparable figures of merit, led by the two intensive ones,
specific thrust (thrust per unit air mass flow) and specific fuel
consumption, then summarises the catalogue as bounds and a mass
correlation. Engine size enters only through air mass flow: nothing is
scaled with frontal area (ADR-0024). Every function takes the engines it should
use, so a caller can leave one out (leave-one-out validation, ADR-0023).
"""
from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.engine_catalogue import Engine
from roadrunner_re.uncertain import Uncertain, parse_uncertain

# Unit conversions (not physical parameters).
SECONDS_PER_HOUR = 3600.0
SECONDS_PER_MINUTE = 60.0
M3_PER_ML = 1.0e-6
KG_PER_G = 1.0e-3

METRICS = ("specific_thrust_N_s_kg", "sfc_kg_N_s", "thrust_to_weight", "idle_thrust_fraction", "pressure_ratio")


@dataclass(frozen=True)
class EngineMetrics:
    id: str
    thrust_N: float
    mass_kg: float | None
    mass_basis: str | None              # "system" (with accessories) or "engine" (bare)
    sfc_kg_N_s: float | None
    sfc_basis: str | None               # "published", "mass_flow" or "volume_flow"
    specific_thrust_N_s_kg: float | None
    thrust_to_weight: float | None
    idle_thrust_fraction: float | None
    pressure_ratio: float | None
    implied_fuel_density_kg_m3: float | None


def load_fuel_density(path: str | Path = "fuel.yaml") -> Uncertain:
    return parse_uncertain(load_yaml(path)["density_kg_m3"], f"{path}:density_kg_m3")


def load_gravity(path: str | Path = "atmosphere.yaml") -> float:
    return float(load_yaml(path)["gravity_m_s2"])


def _fuel_mass_flow_kg_s(engine: Engine, fuel_density_kg_m3: float) -> tuple[float, str] | None:
    if engine.fuel_flow_max is None:
        return None
    value, unit = engine.fuel_flow_max
    if unit == "g_min":
        return value * KG_PER_G / SECONDS_PER_MINUTE, "mass_flow"
    return value * M3_PER_ML * fuel_density_kg_m3 / SECONDS_PER_MINUTE, "volume_flow"


def engine_metrics(engine: Engine, fuel_density_kg_m3: float, gravity_m_s2: float) -> EngineMetrics:
    """Figures of merit of one engine at its maximum published thrust."""
    thrust = engine.thrust_max_N
    fuel = _fuel_mass_flow_kg_s(engine, fuel_density_kg_m3)

    if engine.sfc_kg_N_h is not None:
        sfc, sfc_basis = engine.sfc_kg_N_h / SECONDS_PER_HOUR, "published"
    elif fuel is not None:
        sfc, sfc_basis = fuel[0] / thrust, fuel[1]
    else:
        sfc, sfc_basis = None, None

    implied_density = None
    if engine.sfc_kg_N_h is not None and engine.fuel_flow_max is not None and engine.fuel_flow_max[1] == "ml_min":
        volume_flow_m3_s = engine.fuel_flow_max[0] * M3_PER_ML / SECONDS_PER_MINUTE
        implied_density = engine.sfc_kg_N_h / SECONDS_PER_HOUR * thrust / volume_flow_m3_s

    if engine.mass_system_kg is not None:
        mass, mass_basis = engine.mass_system_kg, "system"
    elif engine.mass_engine_kg is not None:
        mass, mass_basis = engine.mass_engine_kg, "engine"
    else:
        mass, mass_basis = None, None

    return EngineMetrics(
        id=engine.id, thrust_N=thrust, mass_kg=mass, mass_basis=mass_basis, sfc_kg_N_s=sfc, sfc_basis=sfc_basis,
        specific_thrust_N_s_kg=None if engine.air_mass_flow_kg_s is None else thrust / engine.air_mass_flow_kg_s,
        thrust_to_weight=None if mass is None else thrust / (mass * gravity_m_s2),
        idle_thrust_fraction=None if engine.thrust_idle_N is None else engine.thrust_idle_N / thrust,
        pressure_ratio=engine.pressure_ratio,
        implied_fuel_density_kg_m3=implied_density,
    )


def catalogue_metrics(engines: dict[str, Engine], fuel_density_kg_m3: float,
                      gravity_m_s2: float) -> dict[str, EngineMetrics]:
    return {eid: engine_metrics(e, fuel_density_kg_m3, gravity_m_s2) for eid, e in engines.items()}


def technology_bounds(metrics: dict[str, EngineMetrics]) -> dict[str, dict]:
    """Lowest, median and highest value of each figure of merit, with the sample size."""
    out = {}
    for name in METRICS:
        values = sorted(getattr(m, name) for m in metrics.values() if getattr(m, name) is not None)
        if values:
            out[name] = {"low": values[0], "median": statistics.median(values), "high": values[-1], "n": len(values)}
    return out


@dataclass(frozen=True)
class MassCorrelation:
    """Engine mass as a power law of thrust, ``mass_kg = coefficient * thrust_N ** exponent``."""

    coefficient: float
    exponent: float
    n: int
    max_abs_relative_residual: float

    def mass_kg(self, thrust_N: float) -> float:
        return self.coefficient * thrust_N**self.exponent


def fit_mass_correlation(metrics: dict[str, EngineMetrics]) -> MassCorrelation:
    """Least-squares straight line through (ln thrust, ln mass)."""
    points = [(math.log(m.thrust_N), math.log(m.mass_kg)) for m in metrics.values() if m.mass_kg is not None]
    if len(points) < 3:
        raise ConfigError("need at least three engines with a published mass to fit a mass correlation")
    mean_x = statistics.fmean(x for x, _ in points)
    mean_y = statistics.fmean(y for _, y in points)
    sxx = sum((x - mean_x) ** 2 for x, _ in points)
    if sxx == 0.0:
        raise ConfigError("all engines have the same thrust; a mass correlation is undefined")
    exponent = sum((x - mean_x) * (y - mean_y) for x, y in points) / sxx
    coefficient = math.exp(mean_y - exponent * mean_x)
    residual = max(abs(math.exp(y) / (coefficient * math.exp(x) ** exponent) - 1.0) for x, y in points)
    return MassCorrelation(coefficient, exponent, len(points), residual)


def implied_fuel_densities(metrics: dict[str, EngineMetrics]) -> dict[str, float]:
    """Fuel density each vendor's own SFC and volume flow imply (a datasheet self-consistency check)."""
    return {eid: m.implied_fuel_density_kg_m3 for eid, m in metrics.items()
            if m.implied_fuel_density_kg_m3 is not None}


def technology_handoff(engines: dict[str, Engine], metrics: dict[str, EngineMetrics],
                       fuel_density: Uncertain) -> dict:
    """The ``out/technology.yaml`` handoff as plain data (ADR-0021)."""
    correlation = fit_mass_correlation(metrics)
    densities = implied_fuel_densities(metrics)

    def rounded(value):
        return None if value is None else float(f"{value:.6g}")

    return {
        "engines": len(engines),
        "vendors": sorted({e.vendor for e in engines.values()}),
        "fuel_density_kg_m3": {"used": fuel_density.value,
                               "implied_by_datasheets": {k: rounded(v) for k, v in sorted(densities.items())}},
        "bounds": {name: {k: (v if k == "n" else rounded(v)) for k, v in b.items()}
                   for name, b in technology_bounds(metrics).items()},
        "mass_correlation": {k: (v if k == "n" else rounded(v)) for k, v in asdict(correlation).items()},
        "metrics": {eid: {k: (rounded(v) if isinstance(v, float) else v) for k, v in asdict(m).items() if k != "id"}
                    for eid, m in sorted(metrics.items())},
        "missing_datasheet_fields": {eid: list(e.missing_fields) for eid, e in sorted(engines.items())
                                     if e.missing_fields},
    }


def write_technology_handoff(handoff: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "# Handoff of notebooks/reference_engines.ipynb. Generated; do not edit (ADR-0001).\n"
    path.write_text(header + yaml.safe_dump(handoff, sort_keys=False), encoding="utf-8")
    return path
