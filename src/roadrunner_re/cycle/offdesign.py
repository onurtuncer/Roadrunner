"""Off-design performance of the required turbojet in pyCycle (ADR-0030, ADR-0032).

One design point (the sized engine of ``cycle.design``) and any number of
off-design points in one multi-point problem. The design point fixes the
map scalars and the nozzle throat area; at each off-design point shaft
speed balances shaft power and air flow balances the throat area. The
throttle is either the turbine inlet temperature (``Tt4``) or the net
thrust (``thrust``). Thrust is uninstalled; fuel flow is the ideal,
complete-combustion value (ADR-0023). Native pyCycle units stay in here.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import openmdao.api as om
import pycycle.api as pyc

from roadrunner_re.cycle.design import DesignInputs
from roadrunner_re.cycle.turbojet import (NEWTON_MAX_ITERATIONS, NEWTON_TOLERANCE, NOMINAL_SHAFT_SPEED_RPM,
                                          STATIC_MACH_FLOOR, CycleResult, CycleSettings, FlightCondition)

THROTTLES = ("Tt4", "thrust")
#: Smallest air flow the off-design flow balance may reach, kg/s (a guard against a collapsed solve).
MIN_AIR_FLOW_KG_S = 0.01
#: Lowest shaft speed the speed balance may reach, rpm (a guard).
MIN_SHAFT_SPEED_RPM = 5000.0
FAR_GUARD = (1.0e-4, 0.06)


@dataclass(frozen=True)
class OffDesignRequest:
    condition: FlightCondition
    target: float                 # K for throttle "Tt4", N for throttle "thrust"


@dataclass(frozen=True)
class OffDesignResult:
    condition: FlightCondition
    throttle: str
    target: float
    converged: bool
    thrust_N: float = float("nan")            # uninstalled net thrust
    air_mass_flow_kg_s: float = float("nan")
    fuel_flow_kg_s: float = float("nan")      # ideal
    sfc_kg_N_s: float = float("nan")          # ideal
    speed_fraction: float = float("nan")      # shaft speed over design shaft speed
    Tt3_K: float = float("nan")
    Tt4_K: float = float("nan")
    Tt5_K: float = float("nan")
    pressure_ratio: float = float("nan")
    specific_thrust_N_s_kg: float = float("nan")


class _Engine(pyc.Cycle):
    def initialize(self):
        super().initialize()
        self.options.declare("throttle", values=THROTTLES, default="Tt4")

    def setup(self):
        self.options["thermo_method"] = "TABULAR"
        self.options["thermo_data"] = pyc.AIR_JETA_TAB_SPEC
        design = self.options["design"]
        self.add_subsystem("fc", pyc.FlightConditions())
        self.add_subsystem("inlet", pyc.Inlet())
        self.add_subsystem("comp", pyc.Compressor(map_data=pyc.AXI5, map_extrap=True), promotes_inputs=["Nmech"])
        self.add_subsystem("burner", pyc.Combustor(fuel_type="FAR"))
        self.add_subsystem("turb", pyc.Turbine(map_data=pyc.LPT2269), promotes_inputs=["Nmech"])
        self.add_subsystem("nozz", pyc.Nozzle(nozzType="CV", lossCoef="Cv"))
        self.add_subsystem("shaft", pyc.Shaft(num_ports=2), promotes_inputs=["Nmech"])
        self.add_subsystem("perf", pyc.Performance(num_nozzles=1, num_burners=1))
        self.pyc_connect_flow("fc.Fl_O", "inlet.Fl_I", connect_w=False)
        self.pyc_connect_flow("inlet.Fl_O", "comp.Fl_I")
        self.pyc_connect_flow("comp.Fl_O", "burner.Fl_I")
        self.pyc_connect_flow("burner.Fl_O", "turb.Fl_I")
        self.pyc_connect_flow("turb.Fl_O", "nozz.Fl_I")
        self.connect("comp.trq", "shaft.trq_0")
        self.connect("turb.trq", "shaft.trq_1")
        self.connect("fc.Fl_O:stat:P", "nozz.Ps_exhaust")
        self.connect("inlet.Fl_O:tot:P", "perf.Pt2")
        self.connect("comp.Fl_O:tot:P", "perf.Pt3")
        self.connect("burner.Wfuel", "perf.Wfuel_0")
        self.connect("inlet.F_ram", "perf.ram_drag")
        self.connect("nozz.Fg", "perf.Fg_0")

        far = dict(lower=FAR_GUARD[0], upper=FAR_GUARD[1], val=0.017)
        balance = self.add_subsystem("balance", om.BalanceComp())
        if design:
            balance.add_balance("FAR", eq_units="K", rhs_name="Tt4_target", **far)
            self.connect("burner.Fl_O:tot:T", "balance.lhs:FAR")
            balance.add_balance("turb_PR", val=1.5, lower=1.001, upper=8.0, eq_units="W", rhs_val=0.0)
            self.connect("balance.turb_PR", "turb.PR")
            self.connect("shaft.pwr_net", "balance.lhs:turb_PR")
            self.set_input_defaults("inlet.Fl_I:stat:W", 1.0, units="kg/s")
        else:
            if self.options["throttle"] == "Tt4":
                balance.add_balance("FAR", eq_units="K", rhs_name="Tt4_target", **far)
                self.connect("burner.Fl_O:tot:T", "balance.lhs:FAR")
            else:
                balance.add_balance("FAR", eq_units="N", rhs_name="Fn_target", **far)
                self.connect("perf.Fn", "balance.lhs:FAR")
            balance.add_balance("Nmech", val=NOMINAL_SHAFT_SPEED_RPM, units="rpm", lower=MIN_SHAFT_SPEED_RPM,
                                eq_units="W", rhs_val=0.0)
            self.connect("balance.Nmech", "Nmech")
            self.connect("shaft.pwr_net", "balance.lhs:Nmech")
            balance.add_balance("W", val=1.0, units="kg/s", lower=MIN_AIR_FLOW_KG_S, eq_units="m**2")
            self.connect("balance.W", "inlet.Fl_I:stat:W")
            self.connect("nozz.Throat:stat:area", "balance.lhs:W")
        self.connect("balance.FAR", "burner.Fl_I:FAR")

        newton = self.nonlinear_solver = om.NewtonSolver()
        newton.options.update({"atol": NEWTON_TOLERANCE, "rtol": NEWTON_TOLERANCE, "iprint": -1,
                               "maxiter": NEWTON_MAX_ITERATIONS, "solve_subsystems": True, "max_sub_solves": 100,
                               "err_on_non_converge": True})
        newton.linesearch = om.ArmijoGoldsteinLS()
        newton.linesearch.options["iprint"] = -1
        self.linear_solver = om.DirectSolver()
        super().setup()


class _MultiPoint(pyc.MPCycle):
    def initialize(self):
        super().initialize()
        self.options.declare("n_od", types=int)
        self.options.declare("throttle", values=THROTTLES)

    def setup(self):
        self.pyc_add_pnt("DESIGN", _Engine())
        self.set_input_defaults("DESIGN.Nmech", NOMINAL_SHAFT_SPEED_RPM, units="rpm")
        for station in ("inlet", "comp", "burner", "turb"):
            self.set_input_defaults(f"DESIGN.{station}.MN", 0.3)
        self.pyc_add_cycle_param("burner.dPqP", 0.05)
        self.pyc_add_cycle_param("nozz.Cv", 0.98)
        self.pyc_add_cycle_param("inlet.ram_recovery", 0.98)
        for i in range(self.options["n_od"]):
            self.pyc_add_pnt(f"OD{i}", _Engine(design=False, throttle=self.options["throttle"]))
        self.pyc_use_default_des_od_conns()
        self.pyc_connect_des_od("nozz.Throat:stat:area", "balance.rhs:W")
        super().setup()


def _setup(settings: CycleSettings, design_inputs: DesignInputs, design: CycleResult, n_od: int,
           throttle: str) -> om.Problem:
    problem = om.Problem(model=_MultiPoint(n_od=n_od, throttle=throttle), reports=None)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        problem.setup(check=False)
    problem.set_solver_print(-1)
    losses, mach = design_inputs.losses, settings.station_mach
    problem.set_val("burner.dPqP", losses["burner_pressure_loss"])
    problem.set_val("nozz.Cv", losses["nozzle_velocity_coefficient"])
    problem.set_val("inlet.ram_recovery", losses["inlet_recovery_static"])
    cond = design_inputs.condition
    problem.set_val("DESIGN.fc.alt", cond.altitude_m, units="m")
    problem.set_val("DESIGN.fc.MN", max(cond.mach, STATIC_MACH_FLOOR))
    problem.set_val("DESIGN.fc.dTs", cond.dT_isa_K, units="degK")
    problem.set_val("DESIGN.inlet.Fl_I:stat:W", design.air_mass_flow_kg_s, units="kg/s")
    problem.set_val("DESIGN.comp.PR", design_inputs.pressure_ratio)
    problem.set_val("DESIGN.comp.eff", losses["compressor_efficiency"])
    problem.set_val("DESIGN.turb.eff", losses["turbine_efficiency"])
    problem.set_val("DESIGN.balance.Tt4_target", design_inputs.Tt4_K, units="degK")
    problem.set_val("DESIGN.inlet.MN", mach["inlet_exit"])
    problem.set_val("DESIGN.comp.MN", mach["compressor_exit"])
    problem.set_val("DESIGN.burner.MN", mach["burner_exit"])
    problem.set_val("DESIGN.turb.MN", mach["turbine_exit"])
    return problem


def _seed(problem: om.Problem, design: CycleResult, i: int) -> None:
    problem.set_val(f"OD{i}.balance.W", design.air_mass_flow_kg_s, units="kg/s")
    problem.set_val(f"OD{i}.balance.FAR", design.fuel_air_ratio)
    problem.set_val(f"OD{i}.balance.Nmech", NOMINAL_SHAFT_SPEED_RPM, units="rpm")
    problem.set_val(f"OD{i}.turb.PR", design.turbine_pressure_ratio)


def _point_result(problem: om.Problem, i: int, throttle: str, request: OffDesignRequest) -> OffDesignResult:
    pt = f"OD{i}"

    def get(name: str, units: str | None = None) -> float:
        return float(problem.get_val(f"{pt}.{name}", units=units)[0])

    thrust, air, fuel = get("perf.Fn", "N"), get("inlet.Fl_O:stat:W", "kg/s"), get("burner.Wfuel", "kg/s")
    return OffDesignResult(
        request.condition, throttle, request.target, True, thrust, air, fuel, fuel / thrust,
        get("Nmech", "rpm") / NOMINAL_SHAFT_SPEED_RPM, get("comp.Fl_O:tot:T", "degK"),
        get("burner.Fl_O:tot:T", "degK"), get("turb.Fl_O:tot:T", "degK"), get("comp.PR"), thrust / air)


def _run_batch(settings, design_inputs, design, throttle, requests) -> list[OffDesignResult]:
    problem = _setup(settings, design_inputs, design, len(requests), throttle)
    for i, request in enumerate(requests):
        c, pt = request.condition, f"OD{i}"
        problem.set_val(f"{pt}.fc.alt", c.altitude_m, units="m")
        problem.set_val(f"{pt}.fc.MN", max(c.mach, STATIC_MACH_FLOOR))
        problem.set_val(f"{pt}.fc.dTs", c.dT_isa_K, units="degK")
        if throttle == "Tt4":
            problem.set_val(f"{pt}.balance.Tt4_target", request.target, units="degK")
        else:
            problem.set_val(f"{pt}.balance.Fn_target", request.target, units="N")
        _seed(problem, design, i)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        problem.run_model()
    return [_point_result(problem, i, throttle, r) for i, r in enumerate(requests)]


def run_off_design(settings: CycleSettings, design_inputs: DesignInputs, design: CycleResult, throttle: str,
                   requests: list[OffDesignRequest]) -> list[OffDesignResult]:
    """Run the requests in one problem; if it fails, run them one by one and mark the ones that do not converge."""
    if not requests:
        return []
    try:
        return _run_batch(settings, design_inputs, design, throttle, requests)
    except om.AnalysisError:
        pass
    results = []
    for request in requests:
        try:
            results.extend(_run_batch(settings, design_inputs, design, throttle, [request]))
        except om.AnalysisError:
            results.append(OffDesignResult(request.condition, throttle, request.target, False))
    return results
