"""Single-spool turbojet in pyCycle, design point only for now.

Station numbering follows ARP755: 0 free stream, 2 compressor face,
3 compressor exit, 4 turbine inlet (combustor exit), 5 turbine exit,
8 nozzle throat (the exit, for a convergent nozzle).

Two ways to close the model, both solved by pyCycle's own Newton solver:

* ``run_design_point``: turbine inlet temperature is given; thrust and
  fuel flow come out.
* ``match_thrust``: thrust is given (a vendor datasheet); turbine inlet
  temperature and fuel flow come out.

Combustion is complete in the model, so its fuel flow is the *ideal*
fuel flow. The ratio of that to a published fuel flow is the lumped
combustion efficiency of ``roadrunner_re.validation``.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import openmdao.api as om
import pycycle.api as pyc

from roadrunner_re.config import load_yaml
from roadrunner_re.uncertain import Uncertain, parse_uncertain

#: pyCycle's flight-conditions element cannot be evaluated at exactly zero Mach number.
STATIC_MACH_FLOOR = 1.0e-6
#: Shaft speed is needed by pyCycle's map scaling but does not affect a design point.
NOMINAL_SHAFT_SPEED_RPM = 60000.0
NEWTON_TOLERANCE = 1.0e-8
NEWTON_MAX_ITERATIONS = 40


@dataclass(frozen=True)
class FlightCondition:
    """A flight condition as defined by ADR-0017."""

    altitude_m: float = 0.0
    mach: float = 0.0
    dT_isa_K: float = 0.0


@dataclass(frozen=True)
class CycleSettings:
    """What the model has to assume because no datasheet publishes it (config/cycle.yaml)."""

    inlet_recovery_static: Uncertain
    compressor_efficiency: Uncertain
    burner_pressure_loss: Uncertain
    turbine_efficiency: Uncertain
    nozzle_velocity_coefficient: Uncertain
    pressure_ratio_when_unpublished: Uncertain
    station_mach: dict[str, float]

    def nominal_losses(self) -> dict[str, float]:
        return {name: getattr(self, name).value for name in LOSS_NAMES}


LOSS_NAMES = ("inlet_recovery_static", "compressor_efficiency", "burner_pressure_loss", "turbine_efficiency",
              "nozzle_velocity_coefficient")


def load_cycle_settings(path: str | Path = "cycle.yaml") -> CycleSettings:
    cfg = load_yaml(path)
    return CycleSettings(
        **{name: parse_uncertain(cfg["losses"][name], f"{path}:losses.{name}") for name in LOSS_NAMES},
        pressure_ratio_when_unpublished=parse_uncertain(cfg["pressure_ratio_when_unpublished"], f"{path}"),
        station_mach={k: float(v) for k, v in cfg["station_mach"].items()},
    )


@dataclass(frozen=True)
class CycleResult:
    """A converged design point, SI units."""

    thrust_N: float                    # uninstalled net thrust
    air_mass_flow_kg_s: float
    fuel_flow_kg_s: float              # ideal: complete combustion
    sfc_kg_N_s: float                  # ideal: complete combustion
    specific_thrust_N_s_kg: float
    pressure_ratio: float
    compressor_efficiency: float
    fuel_air_ratio: float
    Tt3_K: float
    Tt4_K: float
    Tt5_K: float
    turbine_pressure_ratio: float
    nozzle_pressure_ratio: float
    exit_velocity_m_s: float
    ambient_temperature_K: float
    ambient_pressure_Pa: float


class _Turbojet(pyc.Cycle):
    """The pyCycle model. ``match_thrust`` selects what the fuel-air ratio is solved for."""

    def initialize(self):
        super().initialize()
        self.options.declare("match_thrust", types=bool, default=False)

    def setup(self):
        self.options["thermo_method"] = "TABULAR"
        self.options["thermo_data"] = pyc.AIR_JETA_TAB_SPEC

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

        balance = self.add_subsystem("balance", om.BalanceComp())
        # Turbine pressure ratio: whatever makes turbine power equal compressor power.
        balance.add_balance("turb_PR", val=1.5, lower=1.001, upper=8.0, eq_units="W", rhs_val=0.0)
        self.connect("balance.turb_PR", "turb.PR")
        self.connect("shaft.pwr_net", "balance.lhs:turb_PR")

        if self.options["match_thrust"]:
            # Fuel-air ratio moves until net thrust matches the target.
            balance.add_balance("FAR", val=0.017, lower=1e-4, upper=0.06, eq_units="N", rhs_name="thrust_target")
            self.connect("perf.Fn", "balance.lhs:FAR")
        else:
            # Fuel-air ratio moves until the turbine inlet temperature matches the target.
            balance.add_balance("FAR", val=0.017, lower=1e-4, upper=0.06, eq_units="K", rhs_name="Tt4_target")
            self.connect("burner.Fl_O:tot:T", "balance.lhs:FAR")
        self.connect("balance.FAR", "burner.Fl_I:FAR")

        newton = self.nonlinear_solver = om.NewtonSolver()
        newton.options["atol"] = NEWTON_TOLERANCE
        newton.options["rtol"] = NEWTON_TOLERANCE
        newton.options["iprint"] = -1
        newton.options["maxiter"] = NEWTON_MAX_ITERATIONS
        newton.options["solve_subsystems"] = True
        newton.options["max_sub_solves"] = 100
        newton.options["err_on_non_converge"] = True
        newton.linesearch = om.ArmijoGoldsteinLS()
        newton.linesearch.options["iprint"] = -1
        self.linear_solver = om.DirectSolver()

        self.set_input_defaults("inlet.Fl_I:stat:W", 1.0, units="kg/s")
        super().setup()


def _problem(match_thrust: bool) -> om.Problem:
    problem = om.Problem(model=_Turbojet(match_thrust=match_thrust), reports=None)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        problem.setup(check=False)
    problem.set_solver_print(-1)
    return problem


def _set_common(problem: om.Problem, condition: FlightCondition, air_mass_flow_kg_s: float, pressure_ratio: float,
                losses: dict[str, float], station_mach: dict[str, float]) -> None:
    problem.set_val("fc.alt", condition.altitude_m, units="m")
    problem.set_val("fc.MN", max(condition.mach, STATIC_MACH_FLOOR))
    problem.set_val("fc.dTs", condition.dT_isa_K, units="degK")
    problem.set_val("inlet.Fl_I:stat:W", air_mass_flow_kg_s, units="kg/s")
    problem.set_val("inlet.ram_recovery", losses["inlet_recovery_static"])
    problem.set_val("comp.PR", pressure_ratio)
    problem.set_val("comp.eff", losses["compressor_efficiency"])
    problem.set_val("burner.dPqP", losses["burner_pressure_loss"])
    problem.set_val("turb.eff", losses["turbine_efficiency"])
    problem.set_val("nozz.Cv", losses["nozzle_velocity_coefficient"])
    problem.set_val("Nmech", NOMINAL_SHAFT_SPEED_RPM, units="rpm")
    problem.set_val("inlet.MN", station_mach["inlet_exit"])
    problem.set_val("comp.MN", station_mach["compressor_exit"])
    problem.set_val("burner.MN", station_mach["burner_exit"])
    problem.set_val("turb.MN", station_mach["turbine_exit"])


def _result(problem: om.Problem) -> CycleResult:
    def get(name: str, units: str | None = None) -> float:
        return float(problem.get_val(name, units=units)[0])

    thrust, air, fuel = get("perf.Fn", "N"), get("inlet.Fl_O:stat:W", "kg/s"), get("burner.Wfuel", "kg/s")
    return CycleResult(
        thrust_N=thrust, air_mass_flow_kg_s=air, fuel_flow_kg_s=fuel, sfc_kg_N_s=fuel / thrust,
        specific_thrust_N_s_kg=thrust / air, pressure_ratio=get("comp.PR"), compressor_efficiency=get("comp.eff"),
        fuel_air_ratio=get("balance.FAR"), Tt3_K=get("comp.Fl_O:tot:T", "degK"),
        Tt4_K=get("burner.Fl_O:tot:T", "degK"), Tt5_K=get("turb.Fl_O:tot:T", "degK"),
        turbine_pressure_ratio=get("balance.turb_PR"), nozzle_pressure_ratio=get("nozz.PR"),
        exit_velocity_m_s=get("nozz.Fl_O:stat:V", "m/s"),
        ambient_temperature_K=get("fc.Fl_O:stat:T", "degK"), ambient_pressure_Pa=get("fc.Fl_O:stat:P", "Pa"),
    )


def _run(problem: om.Problem) -> CycleResult:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        problem.run_model()
    return _result(problem)


def run_design_point(settings: CycleSettings, *, air_mass_flow_kg_s: float, pressure_ratio: float, Tt4_K: float,
                     condition: FlightCondition = FlightCondition(),
                     losses: dict[str, float] | None = None) -> CycleResult:
    """Thrust and ideal fuel flow for a given turbine inlet temperature."""
    problem = _problem(match_thrust=False)
    _set_common(problem, condition, air_mass_flow_kg_s, pressure_ratio,
                losses or settings.nominal_losses(), settings.station_mach)
    problem.set_val("balance.Tt4_target", Tt4_K, units="degK")
    return _run(problem)


def match_thrust(settings: CycleSettings, *, thrust_N: float, air_mass_flow_kg_s: float, pressure_ratio: float,
                 condition: FlightCondition = FlightCondition(),
                 losses: dict[str, float] | None = None) -> CycleResult:
    """Turbine inlet temperature and ideal fuel flow that give a stated thrust."""
    problem = _problem(match_thrust=True)
    _set_common(problem, condition, air_mass_flow_kg_s, pressure_ratio,
                losses or settings.nominal_losses(), settings.station_mach)
    problem.set_val("balance.thrust_target", thrust_N, units="N")
    return _run(problem)
