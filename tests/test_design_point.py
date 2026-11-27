"""First-iteration coupled constraint and mission analysis (ADR-0029)."""
import math

import pytest

from roadrunner_re.analysis_inputs import load_analysis_inputs
from roadrunner_re.constraints import constraint_thrust_loading
from roadrunner_re.design_point import solve_design_point
from roadrunner_re.mission import fly_mission


@pytest.fixture(scope="module")
def inputs():
    return load_analysis_inputs()


@pytest.fixture(scope="module")
def design(inputs):
    return solve_design_point(inputs)


def test_lapse_is_one_at_standard_sea_level_static(inputs):
    assert inputs.lapse.alpha(inputs.atmosphere, 0.0, 0.0, 0.0) == pytest.approx(1.0)


def test_lapse_falls_with_altitude_and_hot_day(inputs):
    a = inputs.lapse
    assert a.alpha(inputs.atmosphere, 3000.0, 0.5, 20.0) < a.alpha(inputs.atmosphere, 0.0, 0.5, 20.0)
    assert a.alpha(inputs.atmosphere, 0.0, 0.0, 20.0) < 1.0


def test_lapse_matches_the_closed_form_below_the_throttle_break(inputs):
    atm, h, mach, dT = inputs.atmosphere, 3000.0, 0.5, 20.0
    air, sl = atm.at(h, dT), atm.at(0.0)
    ram = 1 + 0.2 * mach**2
    theta0, delta0 = air.temperature_K / sl.temperature_K * ram, air.pressure_Pa / sl.pressure_Pa * ram**3.5
    expected = delta0 * (1 - 0.3 * (theta0 - 1) - 0.1 * math.sqrt(mach)
                         - (1.5 * (theta0 - 1.0) / theta0 if theta0 > 1.0 else 0.0))
    assert inputs.lapse.alpha(atm, h, mach, dT) == pytest.approx(expected, rel=1e-9)


def test_level_flight_constraint_is_the_drag_to_weight_ratio(inputs, design):
    c = inputs.requirements.constraint("dash")
    r = next(r for r in design.constraints if r.id == "dash")
    q = float(inputs.atmosphere.dynamic_pressure_Pa(r.altitude_m, r.mach, inputs.mission.dT_isa_K.value))
    cl = r.beta * design.wing_loading_Pa / q
    drag_over_weight = inputs.polar.drag_coefficient(cl) / cl
    assert r.thrust_loading == pytest.approx(r.beta / r.lapse * drag_over_weight, rel=1e-9)
    assert constraint_thrust_loading(inputs, c, design.wing_loading_Pa, r.beta).thrust_loading == pytest.approx(r.thrust_loading)


def test_vertical_launch_is_margin_over_lapse(inputs, design):
    r = next(r for r in design.constraints if r.id == "vertical_launch")
    assert r.thrust_loading == pytest.approx(1.30 / r.lapse)
    assert design.binding_constraint == "vertical_launch"
    assert design.thrust_loading == pytest.approx(r.thrust_loading)


def test_coupling_is_a_fixed_point(inputs, design):
    again = fly_mission(inputs, design.takeoff_mass_kg, design.thrust_SL_N)
    for k, v in design.mission.betas().items():
        assert again.betas()[k] == pytest.approx(v, abs=1e-8)
    for r in design.constraints:
        assert r.beta == pytest.approx(design.mission.betas()[r.weight_at], abs=1e-8)


def test_mass_balance(design):
    m = design.mission
    assert sum(s.fuel_kg for s in m.segments) == pytest.approx(m.mission_fuel_kg)
    assert m.implied_empty_mass_kg == pytest.approx(m.takeoff_mass_kg - m.payload_mass_kg - m.total_fuel_kg)
    for a, b in zip(m.segments[:-1], m.segments[1:]):
        assert a.mass_end_kg == pytest.approx(b.mass_start_kg)


def test_hover_fuel_is_exponential_in_time(inputs, design):
    launch = design.mission.segments[0]
    expected = launch.mass_start_kg * (1 - math.exp(-inputs.gravity_m_s2 * inputs.tsfc_kg_N_s * launch.duration_s))
    assert launch.fuel_kg == pytest.approx(expected, rel=1e-6)


def test_impulse_is_fuel_over_tsfc_where_thrust_is_integrated_directly(inputs, design):
    """Constant TSFC: hover and level flight burn C * T * dt, so impulse = fuel / C there.

    An energy step burns m (1 - exp(-C T dt / m)) <= C T dt, so impulse >= fuel / C everywhere.
    """
    m, c = design.mission, inputs.tsfc_kg_N_s
    for s in m.segments:
        if s.type in ("vertical_launch", "vertical_landing"):
            assert s.impulse_N_s == pytest.approx(s.fuel_kg / c, rel=1e-12)
        elif s.type == "descent":
            assert s.impulse_N_s == 0.0
        else:
            assert s.impulse_N_s >= s.fuel_kg / c * (1 - 1e-12) > 0.0
    assert m.total_impulse_N_s == pytest.approx(sum(s.impulse_N_s for s in m.segments))


def test_loiter_fuel_matches_the_integral_of_drag(inputs, design):
    """With the polar and weight known, fuel = C * mean drag * time, to the accuracy of the step count."""
    s = next(s for s in design.mission.segments if s.id == "loiter")
    h = inputs.mission.resolve("loiter", "altitude_m").value
    mach, dT = inputs.mission.resolve("loiter", "mach").value, inputs.mission.dT_isa_K.value
    q = float(inputs.atmosphere.dynamic_pressure_Pa(h, mach, dT))
    drag = lambda mass: q * inputs.polar.area_m2 * inputs.polar.drag_coefficient(mass * inputs.gravity_m_s2 / (q * inputs.polar.area_m2))  # noqa: E731
    lo, hi = drag(s.mass_end_kg), drag(s.mass_start_kg)
    bound = sorted((lo, hi))
    fuel_bounds = [inputs.tsfc_kg_N_s * b * s.duration_s for b in bound]
    assert fuel_bounds[0] <= s.fuel_kg <= fuel_bounds[1]


def test_thrust_loading_is_not_lower_at_lower_mass_for_dash(inputs):
    light, heavy = solve_design_point(inputs, 40.0), solve_design_point(inputs, 150.0)
    assert light.thrust_loading >= heavy.thrust_loading


def test_loaders_refuse_missing_provenance(tmp_path, inputs):
    import yaml

    from roadrunner_re.analysis_inputs import ConfigError
    from roadrunner_re.config import CONFIG_DIR
    raw = yaml.safe_load((CONFIG_DIR / "analysis.yaml").read_text())
    raw["descent"].pop("basis")
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ConfigError):
        load_analysis_inputs(path)
