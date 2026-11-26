"""An uncertain input: nominal value, bounds and distribution (ADR-0020)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from roadrunner_re.config import ConfigError

DISTRIBUTIONS = ("uniform", "triangular", "normal")


@dataclass(frozen=True)
class Uncertain:
    """A number with ``low <= value <= high`` and a named distribution."""

    value: float
    low: float
    high: float
    dist: str = "uniform"

    def __post_init__(self) -> None:
        if not (self.low <= self.value <= self.high):
            raise ConfigError(f"need low <= value <= high, got {self.low}, {self.value}, {self.high}")
        if self.dist not in DISTRIBUTIONS:
            raise ConfigError(f"unknown distribution {self.dist!r}; expected one of {DISTRIBUTIONS}")

    @property
    def is_fixed(self) -> bool:
        return self.low == self.high


def is_uncertain_mapping(obj: Any) -> bool:
    """True for a YAML mapping of the form ``{value, low, high[, dist]}``."""
    return isinstance(obj, dict) and "value" in obj and ("low" in obj or "high" in obj)


def parse_uncertain(obj: Any, where: str) -> Uncertain:
    """Build an :class:`Uncertain` from a ``{value, low, high}`` mapping or a bare number."""
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return Uncertain(float(obj), float(obj), float(obj))
    if not is_uncertain_mapping(obj):
        raise ConfigError(f"{where}: expected a number or a {{value, low, high}} mapping, got {obj!r}")
    missing = {"value", "low", "high"} - set(obj)
    if missing:
        raise ConfigError(f"{where}: uncertain value is missing {sorted(missing)}")
    try:
        return Uncertain(float(obj["value"]), float(obj["low"]), float(obj["high"]), obj.get("dist", "uniform"))
    except ConfigError as err:
        raise ConfigError(f"{where}: {err}") from None
