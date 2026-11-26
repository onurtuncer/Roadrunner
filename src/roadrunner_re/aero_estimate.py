"""The owner's hand aerodynamic estimate (ADR-0016), loaded with its provenance.

``config/aero_estimate.yaml`` is a tier-C (inferred) input supplied by the
owner. This module only loads and validates it; nothing here estimates
aerodynamics. It does not replace the geometry stage or the aerodynamics
notebook, which need pixel measurements that do not exist yet.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.uncertain import Uncertain, parse_uncertain

SECTIONS = ("geometry", "reference_condition", "estimates")


@dataclass(frozen=True)
class AeroEstimate:
    name: str
    tier: str
    accessed: str
    assumption: str
    sources: tuple[str, ...]
    #: section -> name -> value (bare numbers become fixed Uncertain values)
    values: dict[str, dict[str, Uncertain]]
    sanity_checks: dict

    def __getitem__(self, section: str) -> dict[str, Uncertain]:
        return self.values[section]


def load_aero_estimate(path: str | Path = "aero_estimate.yaml") -> AeroEstimate:
    raw = load_yaml(path)
    where = str(path)
    if raw.get("tier") != "C":
        raise ConfigError(f"{where}: a hand estimate is tier C (inferred)")
    basis = (raw.get("basis") or {}).get("assumption")
    if not basis or not raw.get("accessed"):
        raise ConfigError(f"{where}: needs `basis.assumption` and `accessed` (ADR-0005)")
    sources = tuple(item["source"] for item in raw.get("public_data") or ())
    if not sources or not all(s.startswith("https://") for s in sources):
        raise ConfigError(f"{where}: public_data entries need https sources")
    values = {}
    for section in SECTIONS:
        if section not in raw:
            raise ConfigError(f"{where}: missing section {section!r}")
        values[section] = {k: parse_uncertain(v, f"{where}:{section}.{k}") for k, v in raw[section].items()}
    return AeroEstimate(raw["name"], raw["tier"], str(raw["accessed"]), " ".join(basis.split()), sources,
                        values, raw.get("sanity_checks") or {})


__all__ = ["AeroEstimate", "load_aero_estimate"]
