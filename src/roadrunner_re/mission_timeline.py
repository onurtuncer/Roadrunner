"""The sample mission laid out in time (ADR-0026).

Reads a :class:`MissionProfile` and works out, for each segment, what the
profile itself fixes: altitude, Mach number, true airspeed, and the
duration or the distance. A duration given as a distance (dash, cruise)
is distance divided by true airspeed on the mission's hot day, with
bounds from the corners of the input bounds.

Climb and descent durations are NOT fixed by the profile: they follow
from the thrust margin and are found in the mission analysis. They are
reported as unknown (``None``), never assumed here.

No weights, no fuel, no engine: this is a description of the input.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path

import yaml

from roadrunner_re.atmosphere import IsaAtmosphere
from roadrunner_re.mission_profile import MissionProfile, Segment
from roadrunner_re.uncertain import Uncertain


@dataclass(frozen=True)
class Interval:
    """Nominal value with the bounds that follow from the input bounds."""

    value: float
    low: float
    high: float


@dataclass(frozen=True)
class SegmentView:
    id: str
    type: str
    altitude_start_m: Interval
    altitude_end_m: Interval
    mach: Interval | None
    true_airspeed_m_s: Interval | None
    duration_s: Interval | None
    distance_m: Interval | None
    evidence: tuple[str, ...]
    assumption: str


def _param(mission: MissionProfile, seg: Segment, *names: str) -> Uncertain | None:
    for name in names:
        if name in seg.params:
            return mission.resolve(seg.id, name)
    return None


def _fixed(u: Uncertain) -> Interval:
    return Interval(u.value, u.low, u.high)


def _over_corners(func, inputs: list[Uncertain]) -> Interval:
    """Evaluate ``func`` at the nominal point and at every corner of the input bounds."""
    nominal = func(*(u.value for u in inputs))
    corners = [func(*c) for c in product(*((u.low, u.high) for u in inputs))]
    return Interval(nominal, min(corners), max(corners))


def mission_timeline(mission: MissionProfile, atmosphere: IsaAtmosphere) -> list[SegmentView]:
    """One :class:`SegmentView` per segment, in flight order."""
    dT = mission.dT_isa_K
    views: list[SegmentView] = []
    altitude = Interval(0.0, 0.0, 0.0)  # the vehicle starts on the ground
    for seg in mission.segments:
        start = altitude
        to_alt = _param(mission, seg, "to_altitude_m")
        level = _param(mission, seg, "altitude_m")
        end = _fixed(to_alt) if to_alt is not None else (_fixed(level) if level is not None else start)
        if to_alt is None and level is not None:
            start = end
        mach = _param(mission, seg, "mach")
        distance = _param(mission, seg, "distance_m")
        duration = _param(mission, seg, "duration_s")

        speed = None
        if mach is not None and level is not None:
            speed = _over_corners(lambda h, m, d: float(atmosphere.true_airspeed_m_s(h, m, d)), [level, mach, dT])
        if duration is not None:
            duration_i = _fixed(duration)
            distance_i = None
            if speed is not None:
                distance_i = _over_corners(lambda h, m, d, t: float(atmosphere.true_airspeed_m_s(h, m, d)) * t,
                                           [level, mach, dT, duration])
        elif distance is not None and speed is not None:
            duration_i = _over_corners(lambda h, m, d, s: s / float(atmosphere.true_airspeed_m_s(h, m, d)),
                                       [level, mach, dT, distance])
            distance_i = _fixed(distance)
        else:
            duration_i, distance_i = None, None
        views.append(SegmentView(seg.id, seg.type, start, end, _fixed(mach) if mach else None, speed,
                                 duration_i, distance_i, seg.basis.evidence, seg.basis.assumption))
        altitude = end
    return views


def _interval(i: Interval | None) -> dict | None:
    return None if i is None else {"value": round(i.value, 3), "low": round(i.low, 3), "high": round(i.high, 3)}


def mission_profile_handoff(mission: MissionProfile, views: list[SegmentView]) -> dict:
    """The ``out/mission_profile.yaml`` handoff as plain data."""
    return {
        "name": mission.name,
        "day_dT_isa_K": _interval(_fixed(mission.dT_isa_K)),
        "payload_mass_kg": _interval(_fixed(mission.payload_mass_kg)),
        "reserve_fraction_of_mission_fuel": _interval(_fixed(mission.reserve_fraction)),
        "segments": [
            {"id": v.id, "type": v.type,
             "altitude_start_m": _interval(v.altitude_start_m), "altitude_end_m": _interval(v.altitude_end_m),
             "mach": _interval(v.mach), "true_airspeed_m_s": _interval(v.true_airspeed_m_s),
             "duration_s": _interval(v.duration_s), "distance_m": _interval(v.distance_m),
             "evidence": list(v.evidence)}
            for v in views
        ],
        "uncertain_inputs": sorted(mission.uncertain_inputs()),
        "duration_not_fixed_by_profile": [v.id for v in views if v.duration_s is None],
    }


def write_mission_profile_handoff(handoff: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "# Handoff of notebooks/mission_profile.ipynb. Generated; do not edit (ADR-0001).\n"
    path.write_text(header + yaml.safe_dump(handoff, sort_keys=False), encoding="utf-8")
    return path
