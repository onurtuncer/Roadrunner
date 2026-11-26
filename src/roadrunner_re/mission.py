"""Mission fuel and weight fractions for the sample mission (ADR-0018, ADR-0029).

Rough first iteration: constant TSFC, constant polar, maximum-power thrust
from the algebraic lapse. Climb and acceleration use the energy-height
method (fuel independent of the thrust margin), level flight and loiter
integrate dm = C D dt, hover burns C W g dt. Transition is not modelled
beyond starting the climb at its climb Mach number.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from roadrunner_re.analysis_inputs import AnalysisInputs


class InfeasibleMission(RuntimeError):
    """The engine cannot hold the segment: thrust available is below drag."""


@dataclass(frozen=True)
class SegmentResult:
    id: str
    type: str
    mass_start_kg: float
    mass_end_kg: float
    duration_s: float
    distance_m: float

    @property
    def fuel_kg(self) -> float:
        return self.mass_start_kg - self.mass_end_kg

    @property
    def weight_fraction(self) -> float:
        return self.mass_end_kg / self.mass_start_kg


@dataclass(frozen=True)
class MissionResult:
    takeoff_mass_kg: float
    segments: tuple[SegmentResult, ...]
    reserve_fraction: float
    payload_mass_kg: float

    @property
    def mission_fuel_kg(self) -> float:
        return self.takeoff_mass_kg - self.segments[-1].mass_end_kg

    @property
    def reserve_fuel_kg(self) -> float:
        return self.reserve_fraction * self.mission_fuel_kg

    @property
    def total_fuel_kg(self) -> float:
        return self.mission_fuel_kg + self.reserve_fuel_kg

    @property
    def implied_empty_mass_kg(self) -> float:
        return self.takeoff_mass_kg - self.payload_mass_kg - self.total_fuel_kg

    def mass_at_start(self, segment_id: str) -> float:
        return next(s.mass_start_kg for s in self.segments if s.id == segment_id)

    def betas(self) -> dict[str, float]:
        return {s.id: s.mass_start_kg / self.takeoff_mass_kg for s in self.segments}


def _drag_N(inputs: AnalysisInputs, mass_kg: float, h: float, mach: float, dT: float) -> float:
    q = float(inputs.atmosphere.dynamic_pressure_Pa(h, mach, dT))
    cl = mass_kg * inputs.gravity_m_s2 / (q * inputs.polar.area_m2)
    return q * inputs.polar.area_m2 * inputs.polar.drag_coefficient(cl)


def _energy_step(inputs, mass, thrust_SL, h0, m0, h1, m1, dT):
    """One energy-height step: returns (new mass, time s, ground distance m)."""
    atm, g, C = inputs.atmosphere, inputs.gravity_m_s2, inputs.tsfc_kg_N_s
    V0, V1 = (float(atm.true_airspeed_m_s(h, m, dT)) for h, m in ((h0, m0), (h1, m1)))
    hm, mm = 0.5 * (h0 + h1), 0.5 * (m0 + m1)
    V = float(atm.true_airspeed_m_s(hm, mm, dT))
    dz = (h1 - h0) + (V1**2 - V0**2) / (2.0 * g)
    T = inputs.lapse.alpha(atm, hm, mm, dT) * thrust_SL
    D = _drag_N(inputs, mass, hm, mm, dT)
    if T <= D:
        raise InfeasibleMission(f"thrust {T:.0f} N below drag {D:.0f} N at h={hm:.0f} m, M={mm:.2f}")
    dt = dz * mass * g / ((T - D) * V)
    return mass * math.exp(-g * C * dz / (V * (1.0 - D / T))), dt, V * dt


def _level(inputs, mass, thrust_SL, h, mach, dT, steps, *, duration_s=None, distance_m=None):
    atm, C = inputs.atmosphere, inputs.tsfc_kg_N_s
    V = float(atm.true_airspeed_m_s(h, mach, dT))
    total_t = duration_s if duration_s is not None else distance_m / V
    dt = total_t / steps
    available = inputs.lapse.alpha(atm, h, mach, dT) * thrust_SL
    for _ in range(steps):
        D = _drag_N(inputs, mass, h, mach, dT)
        if D > available:
            raise InfeasibleMission(f"drag {D:.0f} N above thrust {available:.0f} N at h={h:.0f} m, M={mach:.2f}")
        mass -= C * D * dt
    return mass, total_t, V * total_t


def fly_mission(inputs: AnalysisInputs, takeoff_mass_kg: float, thrust_SL_N: float) -> MissionResult:
    """Integrate the sample mission; ``thrust_SL_N`` is the installed sea-level static thrust of the pair."""
    m, g, C = takeoff_mass_kg, inputs.gravity_m_s2, inputs.tsfc_kg_N_s
    mission, dT = inputs.mission, inputs.mission.dT_isa_K.value
    steps = inputs.settings["integration"]
    val = lambda sid, name: mission.resolve(sid, name).value  # noqa: E731
    results, h, mach = [], 0.0, 0.0

    def add(seg, start, end, t, d):
        results.append(SegmentResult(seg.id, seg.type, start, end, t, d))
        return end

    for seg in mission.segments:
        start, t, d = m, 0.0, 0.0
        if seg.type == "vertical_launch":
            t = val(seg.id, "duration_s")
            m *= math.exp(-g * C * t)                   # hover thrust, T = W
        elif seg.type in ("climb", "dash", "cruise", "loiter"):
            tgt_mach = val(seg.id, "mach")
            if tgt_mach > mach and (seg.type != "climb"):   # accelerate at constant altitude
                m, t, d = _accelerate(inputs, m, thrust_SL_N, h, mach, tgt_mach, dT, steps["level_steps"])
            if seg.type == "climb":
                h1, n = val(seg.id, "to_altitude_m"), steps["climb_steps"]
                hs = [h1 * i / n for i in range(n + 1)]
                for a, b in zip(hs[:-1], hs[1:]):
                    m, dt_, dd = _energy_step(inputs, m, thrust_SL_N, a, tgt_mach, b, tgt_mach, dT)
                    t, d = t + dt_, d + dd
                h = h1
            else:
                h = val(seg.id, "altitude_m")
                m, dt_, dd = _level(inputs, m, thrust_SL_N, h, tgt_mach, dT, steps["level_steps"],
                                    duration_s=val(seg.id, "duration_s") if seg.type == "loiter" else None,
                                    distance_m=val(seg.id, "distance_m") if seg.type in ("dash", "cruise") else None)
                t, d = t + dt_, d + dd
            mach = tgt_mach
        elif seg.type == "descent":
            m *= inputs.descent_weight_fraction.value
            h, mach = 0.0, 0.0
        elif seg.type == "vertical_landing":
            t = val(seg.id, "duration_s")
            m *= math.exp(-g * C * t)
        else:
            raise ValueError(f"unknown segment type {seg.type!r}")
        add(seg, start, m, t, d)

    return MissionResult(takeoff_mass_kg, tuple(results), mission.reserve_fraction.value, mission.payload_mass_kg.value)


def _accelerate(inputs, mass, thrust_SL, h, m0, m1, dT, steps):
    t = d = 0.0
    for i in range(steps):
        a, b = m0 + (m1 - m0) * i / steps, m0 + (m1 - m0) * (i + 1) / steps
        mass, dt_, dd = _energy_step(inputs, mass, thrust_SL, h, a, h, b, dT)
        t, d = t + dt_, d + dd
    return mass, t, d
