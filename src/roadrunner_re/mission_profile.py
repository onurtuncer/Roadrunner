"""The mission profile as an input (ADR-0018).

Loads ``config/missions/<name>.yaml`` and enforces the provenance rule
(ADR-0005): every block that carries a number must say where the number
comes from, as cited evidence, a stated assumption, or both. Evidence
that is cited must exist in the ledger and must be usable as an input.

This module only describes the mission. Flying it (weight fractions,
fuel) is the mission analysis, added with its own notebook stage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.evidence import Claim, load_claims
from roadrunner_re.uncertain import Uncertain, is_uncertain_mapping, parse_uncertain

SEGMENT_TYPES = (
    "vertical_launch", "transition", "climb", "cruise", "dash", "loiter",
    "descent", "hover", "vertical_landing",
)


@dataclass(frozen=True)
class Basis:
    """Where a block's numbers come from."""

    evidence: tuple[str, ...] = ()
    assumption: str = ""


@dataclass(frozen=True)
class Segment:
    id: str
    type: str
    #: Parameter name -> uncertain value, or the id of the segment it is taken from.
    params: dict[str, Uncertain | str] = field(default_factory=dict)
    basis: Basis = Basis()


@dataclass(frozen=True)
class MissionProfile:
    name: str
    dT_isa_K: Uncertain
    payload_mass_kg: Uncertain
    segments: tuple[Segment, ...]
    reserve_fraction: Uncertain

    def segment(self, segment_id: str) -> Segment:
        for seg in self.segments:
            if seg.id == segment_id:
                return seg
        raise KeyError(segment_id)

    def resolve(self, segment_id: str, param: str) -> Uncertain:
        """Value of a parameter, following ``from_segment`` references."""
        value = self.segment(segment_id).params[param]
        if isinstance(value, str):
            source = self.segment(value)
            for name in (param, f"to_{param}"):
                if name in source.params:
                    return self.resolve(value, name)
            raise ConfigError(f"segment {segment_id!r}: {param} refers to {value!r}, which has no such value")
        return value

    def uncertain_inputs(self) -> dict[str, Uncertain]:
        """Every non-fixed number in the mission, by dotted name (for ADR-0020)."""
        out = {"day.dT_isa_K": self.dT_isa_K, "payload.mass_kg": self.payload_mass_kg,
               "reserve.fraction_of_mission_fuel": self.reserve_fraction}
        for seg in self.segments:
            for name, value in seg.params.items():
                if isinstance(value, Uncertain):
                    out[f"{seg.id}.{name}"] = value
        return {k: v for k, v in out.items() if not v.is_fixed}


def _parse_basis(raw: Any, where: str, claims: dict[str, Claim]) -> Basis:
    if not isinstance(raw, dict) or not (raw.get("evidence") or raw.get("assumption")):
        raise ConfigError(f"{where}: numbers need a `basis` with `evidence` and/or `assumption` (ADR-0005)")
    cited = raw.get("evidence") or ()
    cited = (cited,) if isinstance(cited, str) else tuple(cited)
    for claim_id in cited:
        if claim_id not in claims:
            raise ConfigError(f"{where}: cites unknown evidence id {claim_id!r}")
        if not claims[claim_id].usable_as_input:
            raise ConfigError(f"{where}: cites {claim_id!r}, a tier-{claims[claim_id].tier} claim that is never an input")
    return Basis(cited, str(raw.get("assumption") or ""))


def _parse_param(raw: Any, where: str) -> Uncertain | str:
    if isinstance(raw, dict) and "from_segment" in raw:
        return str(raw["from_segment"])
    return parse_uncertain(raw, where)


def load_mission(path: str | Path = "missions/sample.yaml",
                 claims: dict[str, Claim] | None = None) -> MissionProfile:
    """Load and validate one mission profile."""
    claims = load_claims() if claims is None else claims
    raw = load_yaml(path)
    for key in ("name", "day", "payload", "segments", "reserve"):
        if key not in raw:
            raise ConfigError(f"{path}: missing top-level key {key!r}")

    for block in ("day", "payload", "reserve"):
        _parse_basis(raw[block].get("basis"), f"{path}:{block}", claims)

    segments = []
    for i, seg in enumerate(raw["segments"]):
        where = f"{path}:segments[{i}]"
        for key in ("id", "type"):
            if key not in seg:
                raise ConfigError(f"{where}: missing {key!r}")
        where = f"{path}:{seg['id']}"
        if seg["type"] not in SEGMENT_TYPES:
            raise ConfigError(f"{where}: unknown segment type {seg['type']!r}")
        basis = _parse_basis(seg.get("basis"), where, claims)
        params = {k: _parse_param(v, f"{where}.{k}") for k, v in seg.items() if k not in ("id", "type", "basis")}
        segments.append(Segment(seg["id"], seg["type"], params, basis))

    ids = [s.id for s in segments]
    if len(set(ids)) != len(ids):
        raise ConfigError(f"{path}: duplicate segment ids")
    mission = MissionProfile(
        name=raw["name"],
        dT_isa_K=parse_uncertain(raw["day"]["dT_isa_K"], f"{path}:day.dT_isa_K"),
        payload_mass_kg=parse_uncertain(raw["payload"]["mass_kg"], f"{path}:payload.mass_kg"),
        segments=tuple(segments),
        reserve_fraction=parse_uncertain(raw["reserve"]["fraction_of_mission_fuel"], f"{path}:reserve"),
    )
    for seg in mission.segments:  # every from_segment reference must resolve
        for name, value in seg.params.items():
            if isinstance(value, str):
                if value not in ids:
                    raise ConfigError(f"{path}:{seg.id}.{name}: refers to unknown segment {value!r}")
                mission.resolve(seg.id, name)
    return mission


__all__ = ["Basis", "MissionProfile", "Segment", "load_mission", "is_uncertain_mapping"]
