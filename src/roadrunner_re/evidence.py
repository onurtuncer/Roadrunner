"""The evidence ledger (ADR-0005): what is publicly claimed, by whom, how firmly."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from roadrunner_re.config import ConfigError, load_yaml

TIERS = ("A", "B", "C", "X")
#: Tier X is a marketing comparative with no stated baseline: never an input.
NON_INPUT_TIERS = ("X",)

_REQUIRED = ("id", "statement", "tier", "source", "accessed")


@dataclass(frozen=True)
class Claim:
    id: str
    statement: str
    tier: str
    source: str
    accessed: str

    @property
    def usable_as_input(self) -> bool:
        return self.tier not in NON_INPUT_TIERS


def load_claims(path: str | Path = "evidence/claims.yaml") -> dict[str, Claim]:
    """Load and validate the ledger, keyed by claim id."""
    claims: dict[str, Claim] = {}
    for i, raw in enumerate(load_yaml(path) or []):
        where = f"{path}[{i}]"
        missing = [k for k in _REQUIRED if not raw.get(k)]
        if missing:
            raise ConfigError(f"{where}: evidence entry is missing {missing}")
        if raw["tier"] not in TIERS:
            raise ConfigError(f"{where}: tier {raw['tier']!r} is not one of {TIERS}")
        if not str(raw["source"]).startswith(("http://", "https://")):
            raise ConfigError(f"{where}: source must be a URL, got {raw['source']!r}")
        if raw["id"] in claims:
            raise ConfigError(f"{where}: duplicate evidence id {raw['id']!r}")
        claims[raw["id"]] = Claim(raw["id"], raw["statement"], raw["tier"], raw["source"], str(raw["accessed"]))
    return claims
