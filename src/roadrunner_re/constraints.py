"""Constraint analysis: thrust loading required by each requirement (ADR-0019, ADR-0029).

Mattingly's master equation (UCK 474E Lecture 2), with the parabolic polar
C_D = K1 C_L^2 + K2 C_L + C_D0 + C_DR:

    T_SL / W_TO = (beta / alpha) [ K1 n^2 (beta/q) x + K2 n
                                   + (C_D0 + C_DR) / ((beta/q) x) + Ps / V ],   x = W_TO g / S_ref

``alpha`` is the installed thrust lapse and ``beta`` the weight fraction at
the start of the segment the requirement belongs to. Vertical launch and
landing replace the ground-roll cases. The weight is the mass times g, so
thrust loading is dimensionless and wing loading is in Pa.
"""
from __future__ import annotations

from dataclasses import dataclass

from roadrunner_re.analysis_inputs import AnalysisInputs
from roadrunner_re.constraint_inputs import Constraint

_LEVEL_TYPES = ("level_flight", "sustained_load_factor", "climb", "ceiling")


@dataclass(frozen=True)
class ConstraintResult:
    id: str
    type: str
    sense: str
    weight_at: str
    beta: float
    thrust_loading: float          # T_SL / W_TO required (lower bound) or allowed (upper bound)
    lapse: float | None
    mach: float | None
    altitude_m: float | None


def _value(inputs: AnalysisInputs, c: Constraint, name: str, default: float | None = None) -> float:
    if name not in c.params:
        if default is None:
            raise KeyError(f"constraint {c.id!r} has no {name!r}")
        return default
    return inputs.requirements.resolve(c.id, name).value


def constraint_thrust_loading(inputs: AnalysisInputs, c: Constraint, wing_loading_Pa: float, beta: float) -> ConstraintResult:
    """Thrust loading for one requirement at one wing loading ``W_TO g / S_ref``."""
    atm, dT = inputs.atmosphere, inputs.mission.dT_isa_K.value

    def make(value, lapse=None, mach=None, altitude=None):
        return ConstraintResult(c.id, c.type, c.sense, c.weight_at, beta, float(value), lapse, mach, altitude)

    if c.type == "vertical_launch":
        h = _value(inputs, c, "altitude_m")
        alpha = inputs.engine.alpha(atm, h, 0.0, dT)
        return make(_value(inputs, c, "thrust_to_weight_margin") / alpha, alpha, 0.0, h)
    if c.type == "vertical_landing_floor":
        floor = _value(inputs, c, "max_floor_to_landing_weight")
        return make(floor * beta / inputs.idle_thrust_fraction, None, 0.0, _value(inputs, c, "altitude_m"))

    h, mach = _value(inputs, c, "altitude_m"), _value(inputs, c, "mach")
    n = _value(inputs, c, "load_factor", 1.0)
    roc = _value(inputs, c, "rate_of_climb_m_s", 0.0)
    q = float(atm.dynamic_pressure_Pa(h, mach, dT))
    V = float(atm.true_airspeed_m_s(h, mach, dT))
    alpha = inputs.engine.alpha(atm, h, mach, dT)
    p = inputs.polar
    bx_q = beta * wing_loading_Pa / q
    value = beta / alpha * (p.k1 * n**2 * bx_q + p.k2 * n + (p.cd0 + p.cdr) / bx_q + roc / V)
    return make(value, alpha, mach, h)


def evaluate_constraints(inputs: AnalysisInputs, wing_loading_Pa: float, betas: dict[str, float]) -> list[ConstraintResult]:
    return [constraint_thrust_loading(inputs, c, wing_loading_Pa, betas[c.weight_at])
            for c in inputs.requirements.constraints]


def thrust_loading_curve(inputs: AnalysisInputs, c: Constraint, wing_loadings_Pa, beta: float) -> list[float]:
    return [constraint_thrust_loading(inputs, c, float(x), beta).thrust_loading for x in wing_loadings_Pa]
