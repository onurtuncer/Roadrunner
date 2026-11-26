"""Off-design performance study of the required engine: lapse grid, part-throttle SFC, landing check (ADR-0032).

Runs ``cycle.offdesign`` over the conditions in ``config/off_design.yaml``
and the mission, and compares the cycle's thrust lapse with the algebraic
lapse of ADR-0029. Thrust is uninstalled (ADR-0011). Real fuel flow is the
ideal fuel flow over a constant lumped combustion efficiency.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from roadrunner_re.analysis_inputs import AnalysisInputs
from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.cycle.design import DesignInputs
from roadrunner_re.cycle.offdesign import OffDesignRequest, OffDesignResult, run_off_design
from roadrunner_re.cycle.turbojet import CycleResult, CycleSettings, FlightCondition
from roadrunner_re.design_point import DesignPoint
from roadrunner_re.mission import drag_N

SIMPLIFICATIONS = (
    "generic pyCycle maps (an axial compressor map for a centrifugal machine); shaft speed is a result, not a limit",
    "maximum power is the design turbine inlet temperature at every condition (flat rating)",
    "points below the validity speed fraction are flagged and are not to be used downstream",
    "fuel flow is ideal over one constant combustion efficiency: real part-load efficiency falls, so part-throttle SFC is understated",
    "thrust is uninstalled; no inlet or nozzle installation loss (ADR-0011)",
    "no transient response: the landing check is a steady thrust-floor check only",
)


@dataclass(frozen=True)
class OffDesignConfig:
    min_speed_fraction: float
    altitudes_m: tuple[float, ...]
    machs: tuple[float, ...]
    extra_dT_isa_K: tuple[float, ...]
    part_throttle_segments: tuple[str, ...]
    sea_level_static: bool
    thrust_fractions: tuple[float, ...]


def load_off_design_config(path: str | Path = "off_design.yaml") -> OffDesignConfig:
    raw = load_yaml(path)
    for block in ("rating", "validity", "fuel"):
        if not (raw[block].get("basis") or {}).get("assumption"):
            raise ConfigError(f"{path}: {block} needs a stated assumption (ADR-0005)")
    grid, part = raw["lapse_grid"], raw["part_throttle"]
    fractions = tuple(float(f) for f in part["thrust_fractions"])
    if fractions[0] != 1.0 or list(fractions) != sorted(fractions, reverse=True) or fractions[-1] <= 0.0:
        raise ConfigError(f"{path}: thrust_fractions must descend from 1.0 and stay positive")
    return OffDesignConfig(float(raw["validity"]["min_speed_fraction"]), tuple(map(float, grid["altitudes_m"])),
                           tuple(map(float, grid["machs"])), tuple(map(float, grid["extra_dT_isa_K"])),
                           tuple(part["segments"]), bool(part["sea_level_static"]), fractions)


@dataclass(frozen=True)
class OffDesignStudy:
    config: OffDesignConfig
    design_inputs: DesignInputs
    design: CycleResult
    combustion_efficiency: float
    reference: OffDesignResult                 # standard day, sea-level static, maximum power
    lapse_rows: list[dict] = field(default_factory=list)
    part_rows: list[dict] = field(default_factory=list)
    landing: dict = field(default_factory=dict)

    def lapse_at(self, altitude_m: float, mach: float, dT_isa_K: float) -> dict:
        return next(r for r in self.lapse_rows if (r["altitude_m"], r["mach"], r["dT_isa_K"]) == (altitude_m, mach, dT_isa_K))


def _row(analysis: AnalysisInputs, study_ref: OffDesignResult, r: OffDesignResult, eta: float, min_speed: float) -> dict:
    c = r.condition
    fuel = r.fuel_flow_kg_s / eta
    algebraic = analysis.lapse.alpha(analysis.atmosphere, c.altitude_m, c.mach, c.dT_isa_K)
    lapse = r.thrust_N / study_ref.thrust_N if r.converged else float("nan")
    return {"altitude_m": c.altitude_m, "mach": c.mach, "dT_isa_K": c.dT_isa_K, "throttle": r.throttle,
            "converged": r.converged, "valid": bool(r.converged and r.speed_fraction >= min_speed),
            "thrust_N": r.thrust_N, "air_mass_flow_kg_s": r.air_mass_flow_kg_s, "fuel_flow_kg_s": fuel,
            "sfc_kg_N_s": fuel / r.thrust_N if r.converged else float("nan"), "speed_fraction": r.speed_fraction,
            "Tt4_K": r.Tt4_K, "pressure_ratio": r.pressure_ratio, "lapse": lapse, "algebraic_lapse": float(algebraic)}


def _mission_conditions(analysis: AnalysisInputs, config: OffDesignConfig) -> list[tuple[str, float, float]]:
    mission = analysis.mission
    out = [("sea_level_static", 0.0, 0.0)] if config.sea_level_static else []
    for sid in config.part_throttle_segments:
        out.append((sid, mission.resolve(sid, "altitude_m").value, mission.resolve(sid, "mach").value))
    return out


def run_study(analysis: AnalysisInputs, settings: CycleSettings, config: OffDesignConfig, design_inputs: DesignInputs,
              design: CycleResult, design_point: DesignPoint, combustion_efficiency: float) -> OffDesignStudy:
    """Maximum-power lapse grid, part-throttle SFC at the mission's conditions, and the landing thrust floor."""
    hot = analysis.mission.dT_isa_K.value
    days = sorted({0.0, hot, *config.extra_dT_isa_K})
    Tt4 = design_inputs.Tt4_K
    max_requests = [OffDesignRequest(FlightCondition(h, m, dT), Tt4)
                    for dT in days for h in config.altitudes_m for m in config.machs]
    segment_conditions = _mission_conditions(analysis, config)
    extra = [OffDesignRequest(FlightCondition(h, m, hot), Tt4) for _, h, m in segment_conditions]
    known = {(r.condition.altitude_m, r.condition.mach, r.condition.dT_isa_K) for r in max_requests}
    extra = [r for r in extra if (r.condition.altitude_m, r.condition.mach, r.condition.dT_isa_K) not in known]
    results = run_off_design(settings, design_inputs, design, "Tt4", max_requests + extra)
    by_cond = {(r.condition.altitude_m, r.condition.mach, r.condition.dT_isa_K): r for r in results}
    reference = by_cond[(0.0, 0.0, 0.0)]
    if not reference.converged:
        raise RuntimeError("reference point (standard day, sea-level static, maximum power) did not converge")
    eta, vmin = combustion_efficiency, config.min_speed_fraction
    lapse_rows = [_row(analysis, reference, r, eta, vmin) for r in results]

    # Part throttle: thrust as a fraction of the maximum at the same condition.
    part_requests, labels = [], []
    for label, h, m in segment_conditions:
        tmax = by_cond[(h, m, hot)].thrust_N
        for f in config.thrust_fractions[1:]:
            part_requests.append(OffDesignRequest(FlightCondition(h, m, hot), f * tmax))
            labels.append((label, f))
    part_results = run_off_design(settings, design_inputs, design, "thrust", part_requests)
    part_rows = []
    for label, h, m in segment_conditions:
        full = _row(analysis, reference, by_cond[(h, m, hot)], eta, vmin)
        part_rows.append({"condition": label, "thrust_fraction": 1.0, **full})
    for (label, f), r in zip(labels, part_results):
        part_rows.append({"condition": label, "thrust_fraction": f, **_row(analysis, reference, r, eta, vmin)})

    # Landing thrust floor (OP2): hover thrust per engine at landing weight, sea level, mission day.
    landing_mass = design_point.mission.mass_at_start(next(s.id for s in design_point.mission.segments
                                                           if s.type == "vertical_landing"))
    target = landing_mass * analysis.gravity_m_s2 / analysis.engine_count
    land = run_off_design(settings, design_inputs, design, "thrust", [OffDesignRequest(FlightCondition(0.0, 0.0, hot), target)])[0]
    tmax_sls = by_cond[(0.0, 0.0, hot)].thrust_N
    landing = {**_row(analysis, reference, land, eta, vmin), "required_thrust_per_engine_N": target,
               "fraction_of_max_thrust": target / tmax_sls}
    return OffDesignStudy(config, design_inputs, design, eta, reference, lapse_rows, part_rows, landing)


def loiter_comparison(analysis: AnalysisInputs, study: OffDesignStudy, design_point: DesignPoint) -> dict | None:
    """SFC at the loiter's own throttle against the constant TSFC of the preliminary analysis (OP4)."""
    seg = next((s for s in design_point.mission.segments if s.type == "loiter"), None)
    rows = sorted((r for r in study.part_rows if r["condition"] == seg.id), key=lambda r: r["thrust_fraction"]) if seg else []
    rows = [r for r in rows if r["valid"]]
    if not rows:
        return None
    mission, dT = analysis.mission, analysis.mission.dT_isa_K.value
    h, mach = mission.resolve(seg.id, "altitude_m").value, mission.resolve(seg.id, "mach").value
    mass = 0.5 * (seg.mass_start_kg + seg.mass_end_kg)
    full = rows[-1]
    fraction = drag_N(analysis, mass, h, mach, dT) / analysis.engine_count / full["thrust_N"]
    if not rows[0]["thrust_fraction"] <= fraction <= 1.0:
        return {"loiter_thrust_fraction": fraction, "inside_valid_throttle_range": False}
    hi = next(r for r in rows if r["thrust_fraction"] >= fraction)
    lo = rows[max(rows.index(hi) - 1, 0)]
    w = 0.0 if hi is lo else (fraction - lo["thrust_fraction"]) / (hi["thrust_fraction"] - lo["thrust_fraction"])
    sfc = lo["sfc_kg_N_s"] + w * (hi["sfc_kg_N_s"] - lo["sfc_kg_N_s"])
    return {"loiter_thrust_fraction": fraction, "inside_valid_throttle_range": True, "sfc_cycle_kg_N_s": sfc,
            "sfc_preliminary_kg_N_s": analysis.tsfc_kg_N_s, "ratio_cycle_to_preliminary": sfc / analysis.tsfc_kg_N_s}


def _clean(x):
    if isinstance(x, float):
        return None if math.isnan(x) else float(f"{x:.7g}")
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


def off_design_handoff(study: OffDesignStudy, analysis: AnalysisInputs, design_point: DesignPoint) -> dict:
    d, ref = study.design, study.reference
    max_rows = [r for r in study.lapse_rows if r["valid"]]
    err = [abs(r["lapse"] / r["algebraic_lapse"] - 1.0) for r in max_rows]
    return _clean({
        "notebook": "off_design",
        "status": "off-design performance of the required engine, generic maps (ADR-0030, ADR-0032)",
        "simplifications": list(SIMPLIFICATIONS),
        "design_point": {"thrust_N_hot_day_sls": d.thrust_N, "air_mass_flow_kg_s": d.air_mass_flow_kg_s,
                         "Tt4_K": study.design_inputs.Tt4_K, "dT_isa_K": study.design_inputs.condition.dT_isa_K},
        "reference": {"label": "standard day, sea-level static, maximum power", "thrust_N": ref.thrust_N,
                      "sfc_ideal_kg_N_s": ref.sfc_kg_N_s, "speed_fraction": ref.speed_fraction},
        "combustion_efficiency": study.combustion_efficiency,
        "min_speed_fraction": study.config.min_speed_fraction,
        "lapse_grid": study.lapse_rows,
        "part_throttle": study.part_rows,
        "landing": study.landing,
        "loiter_against_preliminary": loiter_comparison(analysis, study, design_point),
        "comparison_with_algebraic_lapse": {"points": len(err), "max_abs_relative_difference": max(err) if err else None,
                                            "mean_abs_relative_difference": sum(err) / len(err) if err else None},
    })


def write_off_design_handoff(handoff: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "# Handoff of notebooks/off_design.ipynb. Generated; do not edit (ADR-0001).\n"
    path.write_text(header + yaml.safe_dump(handoff, sort_keys=False), encoding="utf-8")
    return path
