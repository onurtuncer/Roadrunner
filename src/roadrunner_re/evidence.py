"""The evidence ledger (ADR-0005): what is publicly claimed, by whom, how firmly."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from roadrunner_re.config import CONFIG_DIR, ConfigError, load_yaml
from roadrunner_re.uncertain import Uncertain, parse_uncertain
from roadrunner_re.notebook import handoff_header

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
    quantity: str | None = None
    value: Uncertain | None = None
    corroboration: tuple[str, ...] = ()
    note: str = ""

    @property
    def usable_as_input(self) -> bool:
        return self.tier not in NON_INPUT_TIERS

    @property
    def is_quantified(self) -> bool:
        return self.value is not None


def _is_url(text: object) -> bool:
    return str(text).startswith(("http://", "https://"))


def _load_file(path: Path, claims: dict[str, Claim]) -> None:
    for i, raw in enumerate(load_yaml(path) or []):
        where = f"{path.name}[{i}]"
        missing = [k for k in _REQUIRED if not raw.get(k)]
        if missing:
            raise ConfigError(f"{where}: evidence entry is missing {missing}")
        where = f"{path.name}:{raw['id']}"
        if raw["tier"] not in TIERS:
            raise ConfigError(f"{where}: tier {raw['tier']!r} is not one of {TIERS}")
        corroboration = tuple(raw.get("corroboration") or ())
        if not _is_url(raw["source"]) or not all(_is_url(u) for u in corroboration):
            raise ConfigError(f"{where}: source and corroboration must be URLs")
        if raw["id"] in claims:
            raise ConfigError(f"{where}: duplicate evidence id")
        quantity, value = raw.get("quantity"), raw.get("value")
        if (quantity is None) != (value is None):
            raise ConfigError(f"{where}: `quantity` and `value` go together")
        if value is not None and raw["tier"] in NON_INPUT_TIERS:
            raise ConfigError(f"{where}: a tier-{raw['tier']} claim cannot carry a usable value")
        claims[raw["id"]] = Claim(
            id=raw["id"], statement=" ".join(str(raw["statement"]).split()), tier=raw["tier"],
            source=raw["source"], accessed=str(raw["accessed"]), quantity=quantity,
            value=None if value is None else parse_uncertain(value, where),
            corroboration=corroboration, note=" ".join(str(raw.get("note") or "").split()),
        )


def load_claims(path: str | Path = "evidence") -> dict[str, Claim]:
    """Load and validate the ledger, keyed by claim id.

    ``path`` is one YAML file or a directory; a directory is read in file-name
    order.
    """
    path = Path(path)
    if not path.is_absolute():
        path = CONFIG_DIR / path
    files = sorted(path.glob("*.yaml")) if path.is_dir() else [path]
    claims: dict[str, Claim] = {}
    for file in files:
        _load_file(file, claims)
    return claims


def quantified(claims: dict[str, Claim]) -> dict[str, Uncertain]:
    """Quantity name -> value with bounds, for every usable quantified claim."""
    out: dict[str, Uncertain] = {}
    for claim in claims.values():
        if claim.is_quantified and claim.usable_as_input:
            if claim.quantity in out:
                raise ConfigError(f"quantity {claim.quantity!r} is given by more than one ledger entry")
            out[claim.quantity] = claim.value
    return out


def evidence_handoff(claims: dict[str, Claim]) -> dict:
    """The ``out/evidence.yaml`` handoff as plain data (ADR-0021)."""
    return {
        "counts_by_tier": {t: sum(c.tier == t for c in claims.values()) for t in TIERS},
        "quantities": {
            name: {"value": u.value, "low": u.low, "high": u.high, "dist": u.dist,
                   "evidence": next(c.id for c in claims.values() if c.quantity == name)}
            for name, u in sorted(quantified(claims).items())
        },
        "qualitative_inputs": sorted(c.id for c in claims.values() if c.usable_as_input and not c.is_quantified),
        "hypotheses_not_inputs": sorted(c.id for c in claims.values() if not c.usable_as_input),
    }


def write_evidence_handoff(claims: dict[str, Claim], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = handoff_header("evidence_ledger")
    path.write_text(header + yaml.safe_dump(evidence_handoff(claims), sort_keys=False), encoding="utf-8")
    return path
