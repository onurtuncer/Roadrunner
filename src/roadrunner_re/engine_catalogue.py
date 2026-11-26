"""The purchasable-engine catalogue (ADR-0010, ADR-0023).

Loads ``config/reference_engines.yaml``. Vendor numbers are kept exactly
as published; ``None`` means "not yet retrieved from a citable source".
Nothing is filled in, derived or converted here: fuel-flow units differ
between vendors and are normalised by the engine stages that need them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.evidence import TIERS

_REQUIRED = ("id", "vendor", "model", "thrust_max_N", "diameter_m", "tier", "source")
_POSITIVE = ("thrust_idle_N", "mass_engine_kg", "mass_system_kg", "diameter_m", "length_m",
             "air_mass_flow_kg_s", "pressure_ratio", "sfc_kg_N_h", "egt_max_K", "rpm_max")
FUEL_FLOW_UNITS = ("ml_min", "g_min")


@dataclass(frozen=True)
class Engine:
    id: str
    vendor: str
    model: str
    thrust_max_N: float          # upper value where the vendor gives a range by version
    thrust_max_low_N: float      # equals thrust_max_N unless a range is published
    diameter_m: float
    tier: str
    source: str
    thrust_idle_N: float | None = None
    mass_engine_kg: float | None = None
    mass_system_kg: float | None = None
    length_m: float | None = None
    air_mass_flow_kg_s: float | None = None
    pressure_ratio: float | None = None
    fuel_flow_max: tuple[float, str] | None = None   # (value, unit) as published
    sfc_kg_N_h: float | None = None
    egt_max_K: float | None = None
    rpm_max: float | None = None
    note: str = ""

    @property
    def missing_fields(self) -> tuple[str, ...]:
        """Datasheet fields still to be retrieved."""
        return tuple(k for k in _POSITIVE + ("fuel_flow_max",) if getattr(self, k) is None)


def _number(raw: Any, where: str) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or raw <= 0:
        raise ConfigError(f"{where}: expected a positive number or null, got {raw!r}")
    return float(raw)


def load_engine_catalogue(path: str | Path = "reference_engines.yaml") -> dict[str, Engine]:
    """Load and validate the catalogue, keyed by engine id."""
    engines: dict[str, Engine] = {}
    for i, raw in enumerate(load_yaml(path) or []):
        where = f"{path}[{i}]"
        missing = [k for k in _REQUIRED if raw.get(k) is None]
        if missing:
            raise ConfigError(f"{where}: catalogue entry is missing {missing}")
        where = f"{path}:{raw['id']}"
        if raw["id"] in engines:
            raise ConfigError(f"{where}: duplicate engine id")
        if raw["tier"] not in TIERS:
            raise ConfigError(f"{where}: tier {raw['tier']!r} is not one of {TIERS}")
        if not str(raw["source"]).startswith(("http://", "https://")):
            raise ConfigError(f"{where}: source must be a URL")

        thrust = raw["thrust_max_N"]
        if isinstance(thrust, dict):
            low, high = _number(thrust.get("low"), where), _number(thrust.get("high"), where)
            if low is None or high is None or low > high:
                raise ConfigError(f"{where}: thrust range needs low <= high")
        else:
            low = high = _number(thrust, f"{where}.thrust_max_N")

        fuel = raw.get("fuel_flow_max")
        if fuel is not None:
            if not isinstance(fuel, dict) or fuel.get("unit") not in FUEL_FLOW_UNITS:
                raise ConfigError(f"{where}: fuel_flow_max needs a unit, one of {FUEL_FLOW_UNITS}")
            fuel = (_number(fuel.get("value"), f"{where}.fuel_flow_max"), fuel["unit"])

        engines[raw["id"]] = Engine(
            id=raw["id"], vendor=raw["vendor"], model=raw["model"],
            thrust_max_N=high, thrust_max_low_N=low, tier=raw["tier"], source=raw["source"],
            fuel_flow_max=fuel, note=str(raw.get("note") or ""),
            **{k: _number(raw.get(k), f"{where}.{k}") for k in _POSITIVE},
        )
    return engines
