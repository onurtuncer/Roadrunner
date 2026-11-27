"""Engine models for the coupled constraint and mission analysis (ADR-0029, ADR-0033).

Two interchangeable models answer the same three questions: installed thrust
over the standard-day sea-level static thrust (``alpha``), real SFC at a
flight condition and throttle (``sfc_kg_N_s``), and a description for the
handoff. ``AlgebraicEngine`` is the preliminary model (lecture lapse, one
constant TSFC); ``CycleEngine`` interpolates the tables of ``out/off_design.yaml``
(pyCycle, ADR-0032). Size enters only through the air flow, so both are
used in specific, relative terms (ADR-0024).
"""
from __future__ import annotations

import numpy as np

from roadrunner_re.atmosphere import IsaAtmosphere
from roadrunner_re.lapse import PreliminaryLapseEstimate

REGIMES = ("flight", "hover")


class OutsideEngineModel(ValueError):
    """A condition or throttle outside what the off-design tables cover (never extrapolated)."""


class AlgebraicEngine:
    """Lecture turbojet lapse and one constant TSFC at every condition and throttle."""

    def __init__(self, lapse: PreliminaryLapseEstimate, tsfc_kg_N_s: float):
        self.lapse, self._tsfc = lapse, tsfc_kg_N_s

    def alpha(self, atmosphere: IsaAtmosphere, altitude_m: float, mach: float, dT_isa_K: float = 0.0) -> float:
        return self.lapse.alpha(atmosphere, altitude_m, mach, dT_isa_K)

    def sfc_kg_N_s(self, altitude_m: float, mach: float, dT_isa_K: float, thrust_fraction: float, regime: str) -> float:
        return self._tsfc

    def describe(self) -> dict:
        return {"lapse": "turbojet_max_power", "throttle_ratio": self.lapse.throttle_ratio,
                "tsfc_kg_N_s": round(self._tsfc, 9)}


class CycleEngine:
    """Interpolation of the off-design handoff: maximum-power lapse and SFC grids, part-throttle SFC curves."""

    def __init__(self, handoff: dict):
        rows = handoff["lapse_grid"]
        if not all(r["valid"] for r in rows):
            raise ValueError("the off-design lapse grid holds invalid points; refusing to use it")
        self._days = sorted({r["dT_isa_K"] for r in rows})
        self._alts = sorted({r["altitude_m"] for r in rows})
        self._machs = sorted({r["mach"] for r in rows})
        lookup = {(r["dT_isa_K"], r["altitude_m"], r["mach"]): r for r in rows}
        shape = (len(self._days), len(self._alts), len(self._machs))
        self._lapse, self._sfc = np.empty(shape), np.empty(shape)
        for i, d in enumerate(self._days):
            for j, h in enumerate(self._alts):
                for k, m in enumerate(self._machs):
                    self._lapse[i, j, k], self._sfc[i, j, k] = lookup[(d, h, m)]["lapse"], lookup[(d, h, m)]["sfc_kg_N_s"]
        self._penalty = self._penalty_curves(handoff["part_throttle"])
        self._source = {"min_speed_fraction": handoff["min_speed_fraction"],
                        "combustion_efficiency": handoff["combustion_efficiency"]}

    @staticmethod
    def _penalty_curves(rows: list[dict]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        """SFC over SFC at full power against thrust fraction: the sea-level-static curve for hover, the mean of the flight curves otherwise."""
        curves = {}
        for label in dict.fromkeys(r["condition"] for r in rows):
            valid = sorted((r for r in rows if r["condition"] == label and r["valid"]), key=lambda r: r["thrust_fraction"])
            full = next(r for r in valid if r["thrust_fraction"] == 1.0)
            curves[label] = {r["thrust_fraction"]: r["sfc_kg_N_s"] / full["sfc_kg_N_s"] for r in valid}
        flight = [c for label, c in curves.items() if label != "sea_level_static"]
        common = sorted(set.intersection(*(set(c) for c in flight)))
        mean = [sum(c[f] for c in flight) / len(flight) for f in common]
        hover = curves["sea_level_static"]
        hover_f = sorted(hover)
        return {"flight": (np.array(common), np.array(mean)), "hover": (np.array(hover_f), np.array([hover[f] for f in hover_f]))}

    def _interpolate(self, table: np.ndarray, altitude_m: float, mach: float, dT_isa_K: float) -> float:
        for value, axis, name in ((altitude_m, self._alts, "altitude"), (mach, self._machs, "Mach number"),
                                  (dT_isa_K, self._days, "ISA offset")):
            if not axis[0] - 1e-9 <= value <= axis[-1] + 1e-9:
                raise OutsideEngineModel(f"{name} {value} outside the off-design grid {axis[0]} to {axis[-1]}")
        by_mach = np.array([[np.interp(mach, self._machs, table[i, j]) for j in range(len(self._alts))]
                            for i in range(len(self._days))])
        by_alt = np.array([np.interp(altitude_m, self._alts, by_mach[i]) for i in range(len(self._days))])
        return float(np.interp(dT_isa_K, self._days, by_alt))

    def alpha(self, atmosphere: IsaAtmosphere, altitude_m: float, mach: float, dT_isa_K: float = 0.0) -> float:
        return self._interpolate(self._lapse, altitude_m, mach, dT_isa_K)

    def sfc_kg_N_s(self, altitude_m: float, mach: float, dT_isa_K: float, thrust_fraction: float, regime: str) -> float:
        if regime not in REGIMES:
            raise ValueError(f"regime must be one of {REGIMES}")
        f, penalty = self._penalty[regime]
        if not f[0] - 1e-9 <= thrust_fraction <= 1.0 + 1e-9:
            raise OutsideEngineModel(f"thrust fraction {thrust_fraction:.3f} outside the valid throttle range {f[0]} to 1.0 ({regime})")
        return self._interpolate(self._sfc, altitude_m, mach, dT_isa_K) * float(np.interp(thrust_fraction, f, penalty))

    def describe(self) -> dict:
        return {"model": "pyCycle off-design tables, out/off_design.yaml (ADR-0032, ADR-0033)", **self._source}
