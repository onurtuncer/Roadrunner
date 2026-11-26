"""The performance requirements as an input (ADR-0019, ADR-0027).

Loads ``config/constraints.yaml`` and enforces the provenance rule
(ADR-0005), as :mod:`mission_profile` does for the mission. A constraint
refers to the mission's segments for its flight condition rather than
repeating Mach or altitude, so the mission stays the single source.

This module only describes the requirements. Turning them into curves
of thrust loading against wing loading is the constraint analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.evidence import Claim, load_claims
from roadrunner_re.mission_profile import Basis, MissionProfile, _parse_basis, load_mission
from roadrunner_re.uncertain import Uncertain, parse_uncertain

CONSTRAINT_TYPES = ("vertical_launch", "vertical_landing_floor", "level_flight", "climb",
                    "sustained_load_factor", "ceiling")
SENSES = ("lower_bound", "upper_bound")
_NOT_PARAMS = ("id", "type", "sense", "weight_at", "basis")


@dataclass(frozen=True)
class Constraint:
    id: str
    type: str
    sense: str
    #: Segment at whose start the weight fraction beta is evaluated.
    weight_at: str
    #: Parameter name -> uncertain value, or the id of the mission segment it is taken from.
    params: dict[str, Uncertain | str] = field(default_factory=dict)
    basis: Basis = Basis()


@dataclass(frozen=True)
class ConstraintSet:
    mission: MissionProfile
    constraints: tuple[Constraint, ...]

    def constraint(self, constraint_id: str) -> Constraint:
        for c in self.constraints:
            if c.id == constraint_id:
                return c
        raise KeyError(constraint_id)

    def resolve(self, constraint_id: str, param: str) -> Uncertain:
        """Value of a parameter, following ``from_segment`` into the mission."""
        value = self.constraint(constraint_id).params[param]
        if not isinstance(value, str):
            return value
        seg = self.mission.segment(value)
        for name in (param, f"to_{param}"):
            if name in seg.params:
                return self.mission.resolve(value, name)
        raise ConfigError(f"constraint {constraint_id!r}: {param} refers to segment {value!r}, which has no such value")

    def uncertain_inputs(self) -> dict[str, Uncertain]:
        """Every non-fixed number owned by a constraint, by dotted name (for ADR-0020)."""
        out = {}
        for c in self.constraints:
            for name, value in c.params.items():
                if isinstance(value, Uncertain) and not value.is_fixed:
                    out[f"constraint.{c.id}.{name}"] = value
        return out


def _parse_param(raw, where: str):
    if isinstance(raw, dict) and "from_segment" in raw:
        return str(raw["from_segment"])
    return parse_uncertain(raw, where)


def load_constraints(path: str | Path = "constraints.yaml", claims: dict[str, Claim] | None = None,
                     mission: MissionProfile | None = None) -> ConstraintSet:
    """Load and validate the requirements against their mission."""
    claims = load_claims() if claims is None else claims
    raw = load_yaml(path)
    for key in ("mission", "constraints"):
        if key not in raw:
            raise ConfigError(f"{path}: missing top-level key {key!r}")
    mission = load_mission(f"missions/{raw['mission']}.yaml", claims=claims) if mission is None else mission
    segment_ids = {s.id for s in mission.segments}

    constraints = []
    for i, item in enumerate(raw["constraints"]):
        where = f"{path}:constraints[{i}]"
        for key in ("id", "type", "sense", "weight_at"):
            if key not in item:
                raise ConfigError(f"{where}: missing {key!r}")
        where = f"{path}:{item['id']}"
        if item["type"] not in CONSTRAINT_TYPES:
            raise ConfigError(f"{where}: unknown constraint type {item['type']!r}")
        if item["sense"] not in SENSES:
            raise ConfigError(f"{where}: sense must be one of {SENSES}")
        if item["weight_at"] not in segment_ids:
            raise ConfigError(f"{where}: weight_at names unknown mission segment {item['weight_at']!r}")
        basis = _parse_basis(item.get("basis"), where, claims)
        params = {k: _parse_param(v, f"{where}.{k}") for k, v in item.items() if k not in _NOT_PARAMS}
        constraints.append(Constraint(item["id"], item["type"], item["sense"], item["weight_at"], params, basis))

    ids = [c.id for c in constraints]
    if len(set(ids)) != len(ids):
        raise ConfigError(f"{path}: duplicate constraint ids")
    result = ConstraintSet(mission, tuple(constraints))
    for c in constraints:  # every from_segment reference must resolve
        for name, value in c.params.items():
            if isinstance(value, str):
                if value not in segment_ids:
                    raise ConfigError(f"{path}:{c.id}.{name}: refers to unknown segment {value!r}")
                result.resolve(c.id, name)
    return result


def constraints_handoff(constraints: ConstraintSet) -> list[dict]:
    """Requirements as plain data, every value resolved, for ``out/mission_profile.yaml``."""
    def interval(u: Uncertain) -> dict:
        return {"value": u.value, "low": u.low, "high": u.high}

    return [
        {"id": c.id, "type": c.type, "sense": c.sense, "weight_at": c.weight_at,
         "parameters": {name: interval(constraints.resolve(c.id, name)) for name in c.params},
         "taken_from_mission": sorted(name for name, v in c.params.items() if isinstance(v, str)),
         "evidence": list(c.basis.evidence)}
        for c in constraints.constraints
    ]


__all__ = ["Constraint", "ConstraintSet", "constraints_handoff", "load_constraints"]
