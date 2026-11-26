"""pyCycle turbojet behind the SI boundary (ADR-0015, ADR-0017).

Needs the ``cycle`` extra; skipped where pyCycle is not installed. Runs in the design pipeline.
"""
import math

import pytest

pytest.importorskip("pycycle")

from roadrunner_re import IsaAtmosphere  # noqa: E402
from roadrunner_re.config import load_yaml  # noqa: E402
from roadrunner_re.cycle import FlightCondition, load_cycle_settings, match_thrust, run_design_point  # noqa: E402

FLOW, PRESSURE_RATIO, TT4 = 1.8, 4.0, 1250.0


@pytest.fixture(scope="module")
def settings():
    return load_cycle_settings()


@pytest.fixture(scope="module")
def reference(settings):
    return run_design_point(settings, air_mass_flow_kg_s=FLOW, pressure_ratio=PRESSURE_RATIO, Tt4_K=TT4)


def test_design_point_honours_its_inputs(reference):
    assert reference.Tt4_K == pytest.approx(TT4, rel=1e-6)
    assert reference.air_mass_flow_kg_s == pytest.approx(FLOW, rel=1e-6)
    assert reference.pressure_ratio == pytest.approx(PRESSURE_RATIO)
    assert reference.Tt3_K < reference.Tt5_K < reference.Tt4_K
    assert reference.sfc_kg_N_s == pytest.approx(reference.fuel_flow_kg_s / reference.thrust_N)


def test_matching_thrust_inverts_the_design_point(settings, reference):
    back = match_thrust(settings, thrust_N=reference.thrust_N, air_mass_flow_kg_s=FLOW, pressure_ratio=PRESSURE_RATIO)
    assert back.Tt4_K == pytest.approx(TT4, rel=1e-4)  # two Newton solves, each to its own tolerance
    assert back.fuel_flow_kg_s == pytest.approx(reference.fuel_flow_kg_s, rel=1e-4)


def test_thrust_scales_with_mass_flow_and_specific_figures_do_not(settings, reference):
    half = run_design_point(settings, air_mass_flow_kg_s=FLOW / 2, pressure_ratio=PRESSURE_RATIO, Tt4_K=TT4)
    assert half.thrust_N == pytest.approx(reference.thrust_N / 2, rel=1e-5)
    assert half.sfc_kg_N_s == pytest.approx(reference.sfc_kg_N_s, rel=1e-5)


def test_hot_day_at_fixed_turbine_temperature_costs_specific_thrust(settings, reference):
    hot = run_design_point(settings, air_mass_flow_kg_s=FLOW, pressure_ratio=PRESSURE_RATIO, Tt4_K=TT4,
                           condition=FlightCondition(dT_isa_K=20.0))
    assert hot.ambient_temperature_K == pytest.approx(reference.ambient_temperature_K + 20.0, abs=0.05)
    assert hot.specific_thrust_N_s_kg < reference.specific_thrust_N_s_kg


def test_real_cycle_sits_inside_a_band_below_the_ideal_cycle(reference):
    """Closed-form ideal turbojet at rest (perfect components, constant gamma) bounds the model from above."""
    gamma = float(load_yaml("atmosphere.yaml")["gamma"])
    gas_constant = float(load_yaml("atmosphere.yaml")["gas_constant_J_kg_K"])
    T0 = reference.ambient_temperature_K
    tau_c = PRESSURE_RATIO ** ((gamma - 1.0) / gamma)
    tau_lambda = TT4 / T0
    tau_t = 1.0 - (tau_c - 1.0) / tau_lambda
    ideal = math.sqrt(gamma * gas_constant * T0) * math.sqrt(2.0 / (gamma - 1.0) * tau_lambda / tau_c * (tau_c * tau_t - 1.0))
    assert 0.6 * ideal < reference.specific_thrust_N_s_kg < ideal


@pytest.mark.parametrize("altitude_m, dT_isa_K", [(0.0, 0.0), (3000.0, 0.0), (3000.0, 20.0), (11000.0, 0.0), (15000.0, 0.0)])
def test_pycycle_atmosphere_agrees_with_ours(settings, altitude_m, dT_isa_K):
    """ADR-0017: one atmosphere. pyCycle's ambient state must match atmosphere.py at the same condition."""
    ours = IsaAtmosphere.from_yaml().at(altitude_m, dT_isa_K)
    theirs = run_design_point(settings, air_mass_flow_kg_s=1.0, pressure_ratio=PRESSURE_RATIO, Tt4_K=TT4,
                              condition=FlightCondition(altitude_m, 0.5, dT_isa_K))
    assert theirs.ambient_temperature_K == pytest.approx(ours.temperature_K, rel=5e-4)
    assert theirs.ambient_pressure_Pa == pytest.approx(ours.pressure_Pa, rel=5e-4)


def test_design_point_sizing_closes_on_thrust_and_scales_with_it(settings):
    """Air flow follows thrust linearly at fixed Tt4 and pressure ratio (ADR-0030)."""
    from roadrunner_re.cycle.design import DesignInputs, size_design_point
    base = DesignInputs(500.0, 3.9, 1230.0, FlightCondition(0.0, 0.0, 20.0), settings.nominal_losses())
    r1 = size_design_point(settings, base)
    r2 = size_design_point(settings, DesignInputs(1000.0, 3.9, 1230.0, base.condition, base.losses))
    assert r1.thrust_N == pytest.approx(500.0, rel=1e-6)
    assert r2.air_mass_flow_kg_s == pytest.approx(2.0 * r1.air_mass_flow_kg_s, rel=1e-5)
    assert r2.specific_thrust_N_s_kg == pytest.approx(r1.specific_thrust_N_s_kg, rel=1e-5)


def test_design_point_stations_are_ordered_and_consistent(settings):
    from roadrunner_re.cycle.design import DesignInputs, size_design_point
    r = size_design_point(settings, DesignInputs(500.0, 3.9, 1230.0, FlightCondition(0.0, 0.0, 20.0), settings.nominal_losses()))
    t = {k: v[0] for k, v in r.stations.items()}
    p = {k: v[1] for k, v in r.stations.items()}
    assert t["2"] == pytest.approx(r.ambient_temperature_K, rel=1e-3)         # static, recovered
    assert t["2"] < t["3"] < t["5"] < t["4"]
    assert p["3"] > p["4"] > p["5"]                                            # burner loss, then turbine expansion
    assert r.stations["4"][2] > r.stations["3"][2]                             # fuel added
