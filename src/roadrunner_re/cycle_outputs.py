"""Handoff of the cycle_design_point notebook (ADR-0030)."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import yaml

from roadrunner_re.cycle.design import DesignInputs
from roadrunner_re.cycle.turbojet import CycleResult
from roadrunner_re.uncertain import Uncertain
from roadrunner_re.notebook import handoff_header

NOTES = (
    "required engine at OP1 on the mission's hot day, not a catalogue engine (ADR-0023)",
    "Tt4 and the cycle losses are assumptions (config/cycle.yaml, anchored catalogue Tt4); the bounds are one input at a time",
    "installed thrust equals uninstalled thrust: no installation loss yet (ADR-0011)",
    "fuel flow is the ideal, complete-combustion value; a real engine burns more (lumped combustion efficiency, ADR-0023)",
    "generic pyCycle maps at design point only; off-design is the next notebook",
)


def _r(x, digits=6):
    return round(float(x), digits)


def within(value: float, bounds: dict | None) -> bool | None:
    return None if not bounds else bounds["low"] <= value <= bounds["high"]


def cycle_handoff(inputs: DesignInputs, result: CycleResult, *, engine_count: int, Tt4: Uncertain,
                  pressure_ratio: Uncertain, oat: list[dict], technology_bounds: dict) -> dict:
    fields = {k: float(f"{v:.7g}") for k, v in asdict(result).items() if k != "stations"}
    tech = {}
    for key, value in (("specific_thrust_N_s_kg", result.specific_thrust_N_s_kg), ("sfc_kg_N_s", result.sfc_kg_N_s)):
        b = technology_bounds.get(key)
        tech[key] = {"model": _r(value, 9), "catalogue_low": b and b["low"], "catalogue_high": b and b["high"],
                     "inside_catalogue_range": within(value, b)}
    return {
        "notebook": "cycle_design_point",
        "status": "on-design point at OP1, first iteration (ADR-0030)",
        "notes": list(NOTES),
        "requirement": {"thrust_per_engine_N": _r(inputs.thrust_N, 4), "engine_count": engine_count,
                        "altitude_m": inputs.condition.altitude_m, "mach": inputs.condition.mach,
                        "dT_isa_K": inputs.condition.dT_isa_K},
        "inputs": {"Tt4_K": {"value": Tt4.value, "low": Tt4.low, "high": Tt4.high},
                   "pressure_ratio": {"value": pressure_ratio.value, "low": pressure_ratio.low, "high": pressure_ratio.high},
                   "losses": inputs.losses},
        "engine": fields,
        "pair": {"air_mass_flow_kg_s": _r(result.air_mass_flow_kg_s * engine_count),
                 "fuel_flow_kg_s": _r(result.fuel_flow_kg_s * engine_count, 8),
                 "thrust_N": _r(result.thrust_N * engine_count, 4)},
        "stations_ARP755": {name: {"Tt_K": _r(t, 3), "Pt_Pa": _r(p, 1), "W_kg_s": _r(w, 6)}
                            for name, (t, p, w) in result.stations.items()},
        "technology_comparison": tech,
        "one_at_a_time": [{k: (_r(v, 9) if isinstance(v, float) else v) for k, v in row.items()} for row in oat],
    }


def write_cycle_handoff(handoff: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = handoff_header("cycle_design_point")
    path.write_text(header + yaml.safe_dump(handoff, sort_keys=False), encoding="utf-8")
    return path
