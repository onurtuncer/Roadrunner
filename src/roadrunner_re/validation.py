"""Anchoring the cycle model to datasheets and testing the method blind (ADR-0012, ADR-0023).

Needs the ``cycle`` extra. Two steps:

1. *Anchor*: for each catalogue engine that publishes its air mass flow,
   find the turbine inlet temperature that reproduces its thrust, and
   from its published fuel flow the lumped combustion efficiency. The
   model's turbine exit temperature is compared with the published
   exhaust gas temperature, which was not used.
2. *Leave one out*: predict each engine's specific thrust and specific
   fuel consumption with technology levels (turbine inlet temperature,
   combustion efficiency) taken from the other engines. Both are
   intensive: engine size, which enters only as air mass flow, is not
   predicted, and nothing is scaled with frontal area (ADR-0024).
"""
from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.cycle import CycleResult, CycleSettings, match_thrust, run_design_point
from roadrunner_re.engine_catalogue import Engine
from roadrunner_re.technology import EngineMetrics
from roadrunner_re.uncertain import Uncertain
from roadrunner_re.notebook import handoff_header

PREDICTED = ("specific_thrust_N_s_kg", "sfc_kg_N_s")


@dataclass(frozen=True)
class Anchor:
    """The cycle model matched to one datasheet at sea-level static, standard day."""

    engine_id: str
    pressure_ratio: float
    pressure_ratio_published: bool
    Tt4_K: float
    Tt5_K: float
    egt_published_K: float | None        # not used in the match
    specific_thrust_N_s_kg: float        # published thrust over published air flow; the model reproduces it
    ideal_sfc_kg_N_s: float              # model, complete combustion
    published_sfc_kg_N_s: float | None
    combustion_efficiency: float | None  # ideal / published SFC; None if no fuel data
    result: CycleResult

    @property
    def egt_residual_K(self) -> float | None:
        """Model turbine exit temperature minus published exhaust gas temperature."""
        return None if self.egt_published_K is None else self.Tt5_K - self.egt_published_K


def anchor_engine(engine: Engine, metrics: EngineMetrics, settings: CycleSettings) -> Anchor:
    if engine.air_mass_flow_kg_s is None:
        raise ConfigError(f"{engine.id}: cannot anchor an engine with no published air mass flow")
    published = engine.pressure_ratio is not None
    pressure_ratio = engine.pressure_ratio if published else settings.pressure_ratio_when_unpublished.value
    result = match_thrust(settings, thrust_N=engine.thrust_max_N, air_mass_flow_kg_s=engine.air_mass_flow_kg_s,
                          pressure_ratio=pressure_ratio)
    efficiency = None if metrics.sfc_kg_N_s is None else result.sfc_kg_N_s / metrics.sfc_kg_N_s
    return Anchor(
        engine_id=engine.id, pressure_ratio=pressure_ratio, pressure_ratio_published=published,
        Tt4_K=result.Tt4_K, Tt5_K=result.Tt5_K, egt_published_K=engine.egt_max_K,
        specific_thrust_N_s_kg=result.specific_thrust_N_s_kg, ideal_sfc_kg_N_s=result.sfc_kg_N_s,
        published_sfc_kg_N_s=metrics.sfc_kg_N_s, combustion_efficiency=efficiency, result=result,
    )


def anchor_catalogue(engines: dict[str, Engine], metrics: dict[str, EngineMetrics],
                     settings: CycleSettings) -> dict[str, Anchor]:
    """Anchors for every engine that publishes an air mass flow."""
    return {eid: anchor_engine(e, metrics[eid], settings) for eid, e in engines.items()
            if e.air_mass_flow_kg_s is not None}


def _range(values: list[float], what: str) -> Uncertain:
    if len(values) < 2:
        raise ConfigError(f"need at least two other engines to bound {what}")
    return Uncertain(statistics.median(values), min(values), max(values))


@dataclass(frozen=True)
class Prediction:
    """Blind prediction of one engine against its datasheet."""

    engine_id: str
    predicted: dict[str, Uncertain]
    published: dict[str, float | None]
    inside: dict[str, bool | None]         # None where nothing is published to compare with
    relative_width: dict[str, float]
    narrow_enough: dict[str, bool]

    @property
    def passed(self) -> dict[str, bool | None]:
        return {q: None if self.inside[q] is None else (self.inside[q] and self.narrow_enough[q]) for q in PREDICTED}


def predict_blind(engine: Engine, metrics: EngineMetrics, others: dict[str, Anchor], settings: CycleSettings,
                  max_relative_width: dict[str, float]) -> Prediction:
    """Predict an engine's specific thrust and SFC from the technology levels of ``others``."""
    if engine.id in others:
        raise ConfigError(f"{engine.id}: the engine being predicted must be left out of the technology levels")
    Tt4 = _range([a.Tt4_K for a in others.values()], "turbine inlet temperature")
    efficiency = _range([a.combustion_efficiency for a in others.values() if a.combustion_efficiency is not None],
                        "combustion efficiency")
    pressure_ratio = settings.pressure_ratio_when_unpublished

    def specific(tt4: float, pr: float) -> CycleResult:   # per unit mass flow, so the flow value is arbitrary
        return run_design_point(settings, air_mass_flow_kg_s=1.0, pressure_ratio=pr, Tt4_K=tt4)

    nominal = specific(Tt4.value, pressure_ratio.value)
    runs = [nominal] + [specific(t, p) for t in (Tt4.low, Tt4.high) for p in (pressure_ratio.low, pressure_ratio.high)]
    ideal_sfc_low, ideal_sfc_high = min(c.sfc_kg_N_s for c in runs), max(c.sfc_kg_N_s for c in runs)
    predicted = {
        "specific_thrust_N_s_kg": Uncertain(nominal.specific_thrust_N_s_kg,
                                            min(c.specific_thrust_N_s_kg for c in runs),
                                            max(c.specific_thrust_N_s_kg for c in runs)),
        "sfc_kg_N_s": Uncertain(nominal.sfc_kg_N_s / efficiency.value, ideal_sfc_low / efficiency.high,
                                ideal_sfc_high / efficiency.low),
    }
    published = {"specific_thrust_N_s_kg": metrics.specific_thrust_N_s_kg, "sfc_kg_N_s": metrics.sfc_kg_N_s}
    inside = {q: None if published[q] is None else predicted[q].low <= published[q] <= predicted[q].high
              for q in PREDICTED}
    width = {q: (predicted[q].high - predicted[q].low) / predicted[q].value for q in PREDICTED}
    return Prediction(engine.id, predicted, published, inside, width,
                      {q: width[q] <= max_relative_width[q] for q in PREDICTED})


def leave_one_out(engines: dict[str, Engine], metrics: dict[str, EngineMetrics], anchors: dict[str, Anchor],
                  settings: CycleSettings, max_relative_width: dict[str, float]) -> dict[str, Prediction]:
    """Blind prediction of every anchored engine from the others.

    Variants of one core (same vendor, diameter, air flow and thrust) are left out together:
    predicting an engine from its own twin would not be blind.
    """
    def same_core(a: Engine, b: Engine) -> bool:
        return (a.vendor, a.diameter_m, a.air_mass_flow_kg_s, a.thrust_max_N) == \
               (b.vendor, b.diameter_m, b.air_mass_flow_kg_s, b.thrust_max_N)

    return {eid: predict_blind(engines[eid], metrics[eid],
                               {k: a for k, a in anchors.items() if not same_core(engines[k], engines[eid])},
                               settings, max_relative_width)
            for eid in anchors}


def load_validation_limits(path: str | Path = "validation.yaml") -> dict[str, float]:
    limits = {k: float(v) for k, v in load_yaml(path)["max_relative_width"].items()}
    if set(limits) != set(PREDICTED):
        raise ConfigError(f"{path}: max_relative_width must give exactly {PREDICTED}")
    return limits


def pass_counts(predictions: dict[str, Prediction]) -> dict[str, dict[str, int]]:
    out = {}
    for q in PREDICTED:
        judged = [p.passed[q] for p in predictions.values() if p.passed[q] is not None]
        out[q] = {"passed": sum(judged), "of": len(judged)}
    return out


def validation_handoff(anchors: dict[str, Anchor], predictions: dict[str, Prediction]) -> dict:
    """The ``out/validation.yaml`` handoff as plain data (ADR-0021)."""
    def r(value):
        return None if value is None else float(f"{value:.5g}")

    def spread(values):
        values = [v for v in values if v is not None]
        return {"low": r(min(values)), "median": r(statistics.median(values)), "high": r(max(values)), "n": len(values)}

    return {
        "anchors": {
            eid: {"pressure_ratio": a.pressure_ratio, "pressure_ratio_published": a.pressure_ratio_published,
                  "Tt4_K": r(a.Tt4_K), "Tt5_K": r(a.Tt5_K), "egt_published_K": r(a.egt_published_K),
                  "egt_residual_K": r(a.egt_residual_K), "specific_thrust_N_s_kg": r(a.specific_thrust_N_s_kg),
                  "ideal_sfc_kg_N_s": r(a.ideal_sfc_kg_N_s), "published_sfc_kg_N_s": r(a.published_sfc_kg_N_s),
                  "combustion_efficiency": r(a.combustion_efficiency)}
            for eid, a in sorted(anchors.items())},
        "anchored_technology": {
            "Tt4_K": spread(a.Tt4_K for a in anchors.values()),
            "combustion_efficiency": spread(a.combustion_efficiency for a in anchors.values()),
            "specific_thrust_N_s_kg": spread(a.specific_thrust_N_s_kg for a in anchors.values()),
            "egt_residual_K": spread(a.egt_residual_K for a in anchors.values()),
        },
        "leave_one_out": {
            eid: {q: {"published": r(p.published[q]), **{k: r(v) for k, v in asdict(p.predicted[q]).items() if k != "dist"},
                      "inside": p.inside[q], "narrow_enough": p.narrow_enough[q]} for q in PREDICTED}
            for eid, p in sorted(predictions.items())},
        "pass_counts": pass_counts(predictions),
    }


def write_validation_handoff(handoff: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = handoff_header("method_validation")
    path.write_text(header + yaml.safe_dump(handoff, sort_keys=False), encoding="utf-8")
    return path
