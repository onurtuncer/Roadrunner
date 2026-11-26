"""On-design cycle point of the twin-engine pair at OP1 (ADR-0009, ADR-0030).

The requirement is thrust per engine at sea-level static on the mission's
hot day, taken from the launch constraint. The cycle is closed with the
turbine inlet temperature and pressure ratio of the technology level
(anchored to the catalogue, ADR-0023); air flow follows from thrust, since
at fixed Tt4 and pressure ratio thrust and fuel flow scale with air flow.
The result is the *required* engine: the catalogue is compared with it,
the engine is not designed from the flowpath (ADR-0023).
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from roadrunner_re.cycle.turbojet import (LOSS_NAMES, CycleResult, CycleSettings, FlightCondition, run_design_point)
from roadrunner_re.uncertain import Uncertain

#: Air flow of the unit-flow run the others are scaled from; any value works, the cycle is linear in it.
UNIT_AIR_FLOW_KG_S = 1.0
#: Agreement required between the scaled estimate and the verifying run.
THRUST_CLOSURE_TOLERANCE = 1.0e-6


@dataclass(frozen=True)
class DesignInputs:
    thrust_N: float                       # per engine, at ``condition``
    pressure_ratio: float
    Tt4_K: float
    condition: FlightCondition
    losses: dict[str, float]


def size_design_point(settings: CycleSettings, inputs: DesignInputs) -> CycleResult:
    """Air flow that gives the required thrust at the given Tt4 and pressure ratio, verified by a second run."""
    unit = run_design_point(settings, air_mass_flow_kg_s=UNIT_AIR_FLOW_KG_S, pressure_ratio=inputs.pressure_ratio,
                            Tt4_K=inputs.Tt4_K, condition=inputs.condition, losses=inputs.losses)
    air = UNIT_AIR_FLOW_KG_S * inputs.thrust_N / unit.thrust_N
    result = run_design_point(settings, air_mass_flow_kg_s=air, pressure_ratio=inputs.pressure_ratio,
                              Tt4_K=inputs.Tt4_K, condition=inputs.condition, losses=inputs.losses)
    if abs(result.thrust_N / inputs.thrust_N - 1.0) > THRUST_CLOSURE_TOLERANCE:
        raise RuntimeError(f"cycle does not scale linearly with air flow: {result.thrust_N} N for {inputs.thrust_N} N")
    return result


def one_at_a_time(settings: CycleSettings, nominal: DesignInputs, Tt4: Uncertain, pressure_ratio: Uncertain) -> list[dict]:
    """Move each uncertain input to its low and high bound with the others nominal (ADR-0015 corners)."""
    rows = []

    def run(name: str, bound: str, inputs: DesignInputs, value: float) -> None:
        r = size_design_point(settings, inputs)
        rows.append({"input": name, "bound": bound, "value": value, "air_mass_flow_kg_s": r.air_mass_flow_kg_s,
                     "specific_thrust_N_s_kg": r.specific_thrust_N_s_kg, "sfc_kg_N_s": r.sfc_kg_N_s,
                     "Tt3_K": r.Tt3_K, "Tt5_K": r.Tt5_K})

    for bound in ("low", "high"):
        run("Tt4_K", bound, replace(nominal, Tt4_K=getattr(Tt4, bound)), getattr(Tt4, bound))
        run("pressure_ratio", bound, replace(nominal, pressure_ratio=getattr(pressure_ratio, bound)),
            getattr(pressure_ratio, bound))
        for name in LOSS_NAMES:
            u = getattr(settings, name)
            run(name, bound, replace(nominal, losses={**nominal.losses, name: getattr(u, bound)}), getattr(u, bound))
    return rows
