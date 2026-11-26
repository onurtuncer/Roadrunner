"""The coupled constraint and mission solution: the single call site (ADR-0029).

The constraints need the weight fraction at the start of a segment, the
mission fuel needs the thrust the constraints demand, so the two are
iterated to a fixed point. At fixed take-off mass the wing loading is
``W_TO g / S_ref`` (the polar is referred to the body cross-section).
"""
from __future__ import annotations

from dataclasses import dataclass

from roadrunner_re.analysis_inputs import AnalysisInputs
from roadrunner_re.constraints import ConstraintResult, evaluate_constraints
from roadrunner_re.mission import MissionResult, fly_mission


class NoConvergence(RuntimeError):
    pass


@dataclass(frozen=True)
class DesignPoint:
    takeoff_mass_kg: float
    wing_loading_Pa: float
    thrust_loading: float                  # T_SL / W_TO, installed, pair
    thrust_SL_N: float                     # installed sea-level static thrust of the pair
    thrust_per_engine_N: float
    binding_constraint: str
    constraints: tuple[ConstraintResult, ...]
    mission: MissionResult
    engine_mass_kg: float                  # one engine, from the catalogue mass law
    propulsion_mass_kg: float              # all engines
    iterations: int

    @property
    def upper_bound(self) -> float | None:
        bounds = [c.thrust_loading for c in self.constraints if c.sense == "upper_bound"]
        return min(bounds) if bounds else None

    @property
    def window_margin(self) -> float | None:
        """Upper bound over required thrust loading; below 1 the requirements cannot be met together."""
        return None if self.upper_bound is None else self.upper_bound / self.thrust_loading

    @property
    def propulsion_fraction_of_empty(self) -> float:
        return self.propulsion_mass_kg / self.mission.implied_empty_mass_kg


def solve_design_point(inputs: AnalysisInputs, takeoff_mass_kg: float | None = None) -> DesignPoint:
    m_to = inputs.takeoff_mass_kg.value if takeoff_mass_kg is None else takeoff_mass_kg
    g = inputs.gravity_m_s2
    x = m_to * g / inputs.polar.area_m2
    tol, max_it = inputs.settings["coupling"]["tolerance"], int(inputs.settings["coupling"]["max_iterations"])
    betas = {s.id: 1.0 for s in inputs.mission.segments}
    tw_old = None
    for it in range(1, max_it + 1):
        results = evaluate_constraints(inputs, x, betas)
        lower = [r for r in results if r.sense == "lower_bound"]
        binding = max(lower, key=lambda r: r.thrust_loading)
        tw = binding.thrust_loading
        mission = fly_mission(inputs, m_to, tw * m_to * g)
        new_betas = mission.betas()
        done = tw_old is not None and abs(tw - tw_old) < tol * max(1.0, tw) and \
            max(abs(new_betas[k] - betas[k]) for k in betas) < tol
        betas, tw_old = new_betas, tw
        if done:
            break
    else:
        raise NoConvergence(f"no fixed point in {max_it} iterations")
    thrust = tw * m_to * g
    per_engine = thrust / inputs.engine_count
    engine_mass = inputs.mass_law.mass_kg(per_engine)
    return DesignPoint(m_to, x, tw, thrust, per_engine, binding.id, tuple(evaluate_constraints(inputs, x, betas)),
                       mission, engine_mass, engine_mass * inputs.engine_count, it)
