"""ISA model against published standard-atmosphere table values (ADR-0017)."""
import numpy as np
import pytest

from roadrunner_re import IsaAtmosphere

# Geopotential altitude [m]: temperature [K], pressure [Pa], density [kg/m^3]
# ICAO Standard Atmosphere / US Standard Atmosphere 1976 tables.
TABLE = {
    0.0: (288.15, 101325.0, 1.22500),
    1000.0: (281.65, 89874.6, 1.11164),
    5000.0: (255.65, 54019.9, 0.736116),
    11000.0: (216.65, 22632.1, 0.363918),
    20000.0: (216.65, 5474.89, 0.0880349),
}
REL_TOL = 2e-5  # table values are printed to six significant figures


@pytest.fixture(scope="module")
def isa():
    return IsaAtmosphere.from_yaml()


@pytest.mark.parametrize("altitude_m", sorted(TABLE))
def test_matches_published_table(isa, altitude_m):
    T, p, rho = TABLE[altitude_m]
    state = isa.at(altitude_m)
    assert state.temperature_K == pytest.approx(T, rel=REL_TOL)
    assert state.pressure_Pa == pytest.approx(p, rel=REL_TOL)
    assert state.density_kg_m3 == pytest.approx(rho, rel=REL_TOL)


def test_sea_level_speed_of_sound_and_viscosity(isa):
    state = isa.at(0.0)
    assert state.speed_of_sound_m_s == pytest.approx(340.294, rel=REL_TOL)
    assert state.dynamic_viscosity_Pa_s == pytest.approx(1.7894e-5, rel=1e-4)


def test_continuous_across_the_tropopause(isa):
    below, above = isa.at(11000.0 - 1e-6), isa.at(11000.0 + 1e-6)
    assert below.pressure_Pa == pytest.approx(above.pressure_Pa, rel=1e-8)
    assert below.temperature_K == pytest.approx(above.temperature_K, rel=1e-8)


def test_temperature_offset_keeps_pressure_and_thins_the_air(isa):
    std, hot = isa.at(0.0), isa.at(0.0, dT_isa_K=20.0)
    assert hot.pressure_Pa == std.pressure_Pa
    assert hot.temperature_K == pytest.approx(std.temperature_K + 20.0)
    assert hot.density_kg_m3 == pytest.approx(std.density_kg_m3 * std.temperature_K / hot.temperature_K)
    assert hot.speed_of_sound_m_s > std.speed_of_sound_m_s


def test_arrays_agree_with_scalars(isa):
    altitudes = np.array([0.0, 3000.0, 11000.0, 15000.0])
    state = isa.at(altitudes, dT_isa_K=10.0)
    assert state.pressure_Pa.shape == altitudes.shape
    for i, h in enumerate(altitudes):
        assert state.density_kg_m3[i] == pytest.approx(isa.at(float(h), 10.0).density_kg_m3)


def test_scalar_in_gives_floats_out(isa):
    assert all(isinstance(x, float) for x in isa.at(3000.0))


def test_dynamic_pressure_is_half_rho_v_squared(isa):
    state = isa.at(3000.0)
    v = isa.true_airspeed_m_s(3000.0, 0.8)
    assert isa.dynamic_pressure_Pa(3000.0, 0.8) == pytest.approx(0.5 * state.density_kg_m3 * v**2)


@pytest.mark.parametrize("altitude_m", [-1.0, 20000.1])
def test_refuses_to_extrapolate(isa, altitude_m):
    with pytest.raises(ValueError):
        isa.at(altitude_m)
