"""Everything the first-iteration coupled analysis needs, loaded in one place (ADR-0029)."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from roadrunner_re.aero_estimate import AeroEstimate, load_aero_estimate
from roadrunner_re.atmosphere import IsaAtmosphere
from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.constraint_inputs import ConstraintSet, load_constraints
from roadrunner_re.engine_catalogue import load_engine_catalogue
from roadrunner_re.evidence import load_claims, quantified
from roadrunner_re.engine_model import AlgebraicEngine
from roadrunner_re.lapse import PreliminaryLapseEstimate
from roadrunner_re.technology import (MassCorrelation, catalogue_metrics, fit_mass_correlation, load_fuel_density,
                                      load_gravity)
from roadrunner_re.uncertain import Uncertain, parse_uncertain


@dataclass(frozen=True)
class Polar:
    """Parabolic drag polar C_D = K1 C_L^2 + K2 C_L + C_D0 + C_DR, referred to ``area_m2``."""

    area_m2: float
    k1: float
    k2: float
    cd0: float
    cdr: float

    def drag_coefficient(self, cl: float) -> float:
        return self.k1 * cl**2 + self.k2 * cl + self.cd0 + self.cdr


@dataclass(frozen=True)
class AnalysisInputs:
    atmosphere: IsaAtmosphere
    requirements: ConstraintSet
    aero: AeroEstimate
    polar: Polar
    lapse: PreliminaryLapseEstimate
    throttle_ratio: Uncertain
    tsfc_kg_N_s: float
    idle_thrust_fraction: float
    mass_law: MassCorrelation
    takeoff_mass_kg: Uncertain
    descent_weight_fraction: Uncertain
    engine_count: int
    settings: dict
    gravity_m_s2: float
    engine: object = None      # AlgebraicEngine (preliminary) or CycleEngine (ADR-0033)

    def with_engine(self, engine) -> "AnalysisInputs":
        return replace(self, engine=engine)

    @property
    def mission(self):
        return self.requirements.mission


def load_analysis_inputs(path: str | Path = "analysis.yaml") -> AnalysisInputs:
    raw = load_yaml(path)
    claims = load_claims()
    atmosphere = IsaAtmosphere.from_yaml()
    requirements = load_constraints(claims=claims)
    aero = load_aero_estimate()

    for key in ("lapse", "polar", "propulsion", "tsfc", "idle", "descent", "integration", "coupling", "diagram", "sweep"):
        if key not in raw:
            raise ConfigError(f"{path}: missing {key!r}")
    for block in ("lapse", "descent"):
        if not (raw[block].get("basis") or {}).get("assumption") and not raw[block].get("source"):
            raise ConfigError(f"{path}: {block} needs a source or a stated assumption (ADR-0005)")

    if raw["tsfc"]["source"] != "catalogue_median" or raw["idle"]["source"] != "catalogue_median":
        raise ConfigError(f"{path}: tsfc and idle sources must be 'catalogue_median' in this iteration")
    gravity = load_gravity()
    metrics = catalogue_metrics(load_engine_catalogue(), load_fuel_density().value, gravity)
    tsfc = statistics.median(m.sfc_kg_N_s for m in metrics.values() if m.sfc_kg_N_s is not None)
    idle = statistics.median(m.idle_thrust_fraction for m in metrics.values() if m.idle_thrust_fraction is not None)

    throttle_ratio = parse_uncertain(raw["lapse"]["throttle_ratio"], f"{path}:lapse.throttle_ratio")
    coefficients = raw["lapse"]["coefficients"]
    lapse = PreliminaryLapseEstimate(float(coefficients["c_theta"]), float(coefficients["c_mach"]),
                          float(coefficients["c_break"]), throttle_ratio.value)
    est, geom = aero["estimates"], aero["geometry"]
    polar = Polar(geom["s_ref_m2"].value, est["induced_drag_factor_k"].value, float(raw["polar"]["k2"]),
                  est["cd0"].value, float(raw["polar"]["cdr"]))
    return AnalysisInputs(
        atmosphere, requirements, aero, polar, lapse, throttle_ratio, tsfc, idle, fit_mass_correlation(metrics),
        quantified(claims)["takeoff_mass_kg"], parse_uncertain(raw["descent"]["weight_fraction"], f"{path}:descent"),
        int(raw["propulsion"]["engine_count"]), {k: raw[k] for k in ("integration", "coupling", "diagram", "sweep")}, gravity,
        AlgebraicEngine(lapse, tsfc))
