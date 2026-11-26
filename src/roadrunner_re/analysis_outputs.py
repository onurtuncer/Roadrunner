"""Sweeps and handoffs of the coupled constraint and mission analysis (ADR-0029)."""
from __future__ import annotations

from pathlib import Path

import yaml

from roadrunner_re.analysis_inputs import AnalysisInputs
from roadrunner_re.design_point import DesignPoint, solve_design_point
from roadrunner_re.engine_model import OutsideEngineModel
from roadrunner_re.mission import InfeasibleMission

CYCLE_SIMPLIFICATIONS = (
    "thrust lapse and SFC are interpolated from the pyCycle off-design tables; outside their grid the analysis refuses to run",
    "part-throttle SFC curve is the mean of the three flight conditions (hover: sea-level static); combustion efficiency is constant, so part-throttle fuel is probably understated",
    "thrust is uninstalled and equals installed thrust (ADR-0011); no structural mass build-up (ADR-0008): implied empty mass is reported, not closed",
    "drag polar is the hand estimate, constant with Mach number, referred to the body cross-section",
    "launch and landing are hover at T = W; transition acceleration is not flown; descent burns an assumed weight fraction",
)

SIMPLIFICATIONS = (
    "thrust lapse is the algebraic turbojet model, not an engine deck; the cycle analysis replaces it",
    "TSFC is one catalogue median at every condition: no part-throttle penalty, loiter fuel is understated",
    "drag polar is the hand estimate, constant with Mach number, referred to the body cross-section",
    "launch and landing are hover at T = W; transition acceleration to the climb Mach number is not flown",
    "descent burns an assumed weight fraction; climb at maximum power by the energy-height method",
    "installation losses are not applied (ADR-0011); engine mass is the catalogue power law at datasheet thrust",
    "no structural mass build-up (ADR-0008): implied empty mass is reported, not closed",
)


def _r(x, digits=6):
    return None if x is None else round(float(x), digits)


def takeoff_mass_sweep(inputs: AnalysisInputs, masses_kg) -> list[dict]:
    rows = []
    for m in masses_kg:
        try:
            dp = solve_design_point(inputs, float(m))
        except (InfeasibleMission, OutsideEngineModel) as err:
            rows.append({"takeoff_mass_kg": _r(m), "feasible": False, "reason": str(err)})
            continue
        rows.append({"takeoff_mass_kg": _r(m), "feasible": True, "wing_loading_Pa": _r(dp.wing_loading_Pa, 3),
                     "thrust_loading": _r(dp.thrust_loading), "binding_constraint": dp.binding_constraint,
                     "thrust_SL_N": _r(dp.thrust_SL_N, 3), "thrust_per_engine_N": _r(dp.thrust_per_engine_N, 3),
                     "total_fuel_kg": _r(dp.mission.total_fuel_kg), "implied_empty_mass_kg": _r(dp.mission.implied_empty_mass_kg),
                     "propulsion_mass_kg": _r(dp.propulsion_mass_kg),
                     "propulsion_fraction_of_empty": _r(dp.propulsion_fraction_of_empty)})
    return rows


def sweep_masses(inputs: AnalysisInputs) -> list[float]:
    u, n = inputs.takeoff_mass_kg, int(inputs.settings["sweep"]["takeoff_mass_points"])
    return [u.low + (u.high - u.low) * i / (n - 1) for i in range(n)]


def _design_block(dp: DesignPoint, inputs: AnalysisInputs) -> dict:
    return {"takeoff_mass_kg": _r(dp.takeoff_mass_kg), "wing_loading_Pa": _r(dp.wing_loading_Pa, 3),
            "reference_area_m2": inputs.polar.area_m2, "thrust_loading": _r(dp.thrust_loading),
            "thrust_SL_N_installed_pair": _r(dp.thrust_SL_N, 3), "thrust_per_engine_N": _r(dp.thrust_per_engine_N, 3),
            "binding_constraint": dp.binding_constraint, "landing_floor_window_margin": _r(dp.window_margin, 4),
            "iterations": dp.iterations}


def _common(inputs: AnalysisInputs, notebook: str) -> dict:
    status = ("first iteration, rough by intent (ADR-0029)" if notebook.endswith("_preliminary")
              else "on the off-design cycle results (ADR-0032, ADR-0033)")
    simplifications = SIMPLIFICATIONS if notebook.endswith("_preliminary") else CYCLE_SIMPLIFICATIONS
    return {"notebook": notebook, "status": status, "simplifications": list(simplifications),
            "engine_model": {**inputs.engine.describe(), "idle_thrust_fraction": _r(inputs.idle_thrust_fraction),
                             "engine_count": inputs.engine_count}}


def constraint_comparison(prelim: DesignPoint, cycle: DesignPoint) -> dict:
    """The constraint analysis on the cycle engine against the preliminary one."""
    before = {c.id: c for c in prelim.constraints}
    return {"thrust_loading": {"preliminary": _r(prelim.thrust_loading), "cycle": _r(cycle.thrust_loading)},
            "binding_constraint": {"preliminary": prelim.binding_constraint, "cycle": cycle.binding_constraint},
            "thrust_per_engine_N": {"preliminary": _r(prelim.thrust_per_engine_N, 3), "cycle": _r(cycle.thrust_per_engine_N, 3)},
            "constraints": [{"id": c.id, "preliminary": _r(before[c.id].thrust_loading), "cycle": _r(c.thrust_loading),
                             "ratio": _r(c.thrust_loading / before[c.id].thrust_loading, 4)} for c in cycle.constraints]}


def mission_comparison(prelim: DesignPoint, cycle: DesignPoint) -> dict:
    """The mission on the cycle engine against the preliminary one."""
    before = {s.id: s for s in prelim.mission.segments}
    pm, cm = prelim.mission, cycle.mission
    return {"segments": [{"id": s.id, "fuel_preliminary_kg": _r(before[s.id].fuel_kg), "fuel_cycle_kg": _r(s.fuel_kg),
                          "ratio": _r(s.fuel_kg / before[s.id].fuel_kg, 4)} for s in cm.segments],
            "mission_fuel_kg": {"preliminary": _r(pm.mission_fuel_kg), "cycle": _r(cm.mission_fuel_kg),
                                "ratio": _r(cm.mission_fuel_kg / pm.mission_fuel_kg, 4)},
            "total_fuel_kg": {"preliminary": _r(pm.total_fuel_kg), "cycle": _r(cm.total_fuel_kg)},
            "implied_empty_kg": {"preliminary": _r(pm.implied_empty_mass_kg), "cycle": _r(cm.implied_empty_mass_kg)},
            "thrust_per_engine_N": {"preliminary": _r(prelim.thrust_per_engine_N, 3), "cycle": _r(cycle.thrust_per_engine_N, 3)}}


def constraints_out(inputs: AnalysisInputs, dp: DesignPoint, sweep: list[dict], *,
                    notebook: str = "constraint_analysis_preliminary", comparison: dict | None = None) -> dict:
    extra = {} if comparison is None else {"comparison_with_preliminary": comparison}
    return {**_common(inputs, notebook), **extra, "design_point": _design_block(dp, inputs),
            "constraints": [{"id": c.id, "type": c.type, "sense": c.sense, "weight_at": c.weight_at,
                             "beta": _r(c.beta), "thrust_loading": _r(c.thrust_loading), "lapse": _r(c.lapse),
                             "mach": c.mach, "altitude_m": c.altitude_m} for c in dp.constraints],
            "takeoff_mass_sweep": sweep}


def mission_out(inputs: AnalysisInputs, dp: DesignPoint, sweep: list[dict], *,
                notebook: str = "mission_analysis_preliminary", comparison: dict | None = None) -> dict:
    m = dp.mission
    extra = {} if comparison is None else {"comparison_with_preliminary": comparison}
    return {**_common(inputs, notebook), **extra, "design_point": _design_block(dp, inputs),
            "segments": [{"id": s.id, "type": s.type, "mass_start_kg": _r(s.mass_start_kg), "mass_end_kg": _r(s.mass_end_kg),
                          "fuel_kg": _r(s.fuel_kg), "weight_fraction": _r(s.weight_fraction, 8),
                          "duration_s": _r(s.duration_s, 3), "distance_m": _r(s.distance_m, 1)} for s in m.segments],
            "fuel": {"mission_kg": _r(m.mission_fuel_kg), "reserve_kg": _r(m.reserve_fuel_kg), "total_kg": _r(m.total_fuel_kg)},
            "masses": {"takeoff_kg": _r(m.takeoff_mass_kg), "payload_kg": _r(m.payload_mass_kg),
                       "implied_empty_kg": _r(m.implied_empty_mass_kg), "engine_each_kg": _r(dp.engine_mass_kg),
                       "propulsion_kg": _r(dp.propulsion_mass_kg),
                       "propulsion_fraction_of_empty": _r(dp.propulsion_fraction_of_empty, 4)},
            "takeoff_mass_sweep": sweep}


def write_handoff(handoff: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"# Handoff of notebooks/{handoff['notebook']}.ipynb. Generated; do not edit (ADR-0001).\n"
    path.write_text(header + yaml.safe_dump(handoff, sort_keys=False), encoding="utf-8")
    return path
