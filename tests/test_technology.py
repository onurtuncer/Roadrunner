"""Datasheet arithmetic for the engine catalogue (ADR-0010, ADR-0023)."""
import pytest

from roadrunner_re import ConfigError, load_engine_catalogue
from roadrunner_re.engine_catalogue import Engine
from roadrunner_re.technology import (
    EngineMetrics, catalogue_metrics, engine_metrics, fit_mass_correlation, implied_fuel_densities,
    load_fuel_density, load_gravity, technology_bounds,
)

G = 9.80665
RHO = 800.0


def engine(**kw):
    base = dict(id="e", vendor="v", model="m", thrust_max_N=1000.0, thrust_max_low_N=1000.0,
                diameter_m=0.2, tier="A", source="https://example.org")
    return Engine(**{**base, **kw})


def test_published_sfc_is_converted_to_si():
    m = engine_metrics(engine(sfc_kg_N_h=0.126), RHO, G)
    assert m.sfc_kg_N_s == pytest.approx(3.5e-5) and m.sfc_basis == "published"


def test_sfc_from_mass_flow_and_from_volume_flow():
    by_mass = engine_metrics(engine(fuel_flow_max=(1800.0, "g_min")), RHO, G)
    assert by_mass.sfc_kg_N_s == pytest.approx(0.030 / 1000.0) and by_mass.sfc_basis == "mass_flow"
    by_volume = engine_metrics(engine(fuel_flow_max=(2250.0, "ml_min")), RHO, G)
    assert by_volume.sfc_kg_N_s == pytest.approx(0.030 / 1000.0) and by_volume.sfc_basis == "volume_flow"


def test_implied_density_recovers_the_density_behind_a_consistent_datasheet():
    sfc_kg_N_h = 2250e-6 / 60.0 * 815.0 / 1000.0 * 3600.0
    m = engine_metrics(engine(sfc_kg_N_h=sfc_kg_N_h, fuel_flow_max=(2250.0, "ml_min")), RHO, G)
    assert m.implied_fuel_density_kg_m3 == pytest.approx(815.0)


def test_system_mass_is_preferred_and_the_basis_is_recorded():
    m = engine_metrics(engine(mass_engine_kg=9.0, mass_system_kg=10.0), RHO, G)
    assert m.mass_basis == "system" and m.thrust_to_weight == pytest.approx(1000.0 / (10.0 * G))
    assert engine_metrics(engine(mass_engine_kg=9.0), RHO, G).mass_basis == "engine"
    assert engine_metrics(engine(), RHO, G).thrust_to_weight is None


def test_specific_thrust_and_idle_fraction():
    m = engine_metrics(engine(air_mass_flow_kg_s=1.6, thrust_idle_N=40.0), RHO, G)
    assert m.specific_thrust_N_s_kg == pytest.approx(625.0)
    assert m.idle_thrust_fraction == pytest.approx(0.04)


def test_mass_correlation_recovers_an_exact_power_law():
    metrics = {}
    for i, thrust in enumerate((400.0, 800.0, 1600.0)):
        metrics[str(i)] = engine_metrics(engine(id=str(i), thrust_max_N=thrust, mass_system_kg=0.01 * thrust**1.2), RHO, G)
    c = fit_mass_correlation(metrics)
    assert (c.coefficient, c.exponent, c.n) == pytest.approx((0.01, 1.2, 3))
    assert c.max_abs_relative_residual == pytest.approx(0.0, abs=1e-9)
    assert c.mass_kg(1000.0) == pytest.approx(0.01 * 1000.0**1.2)


def test_mass_correlation_needs_enough_engines():
    one = {"a": engine_metrics(engine(mass_system_kg=10.0), RHO, G)}
    with pytest.raises(ConfigError):
        fit_mass_correlation(one)


def test_bounds_ignore_missing_values_and_report_the_sample_size():
    metrics = {"a": engine_metrics(engine(id="a", sfc_kg_N_h=0.12), RHO, G),
               "b": engine_metrics(engine(id="b", sfc_kg_N_h=0.15), RHO, G),
               "c": engine_metrics(engine(id="c"), RHO, G)}
    b = technology_bounds(metrics)
    assert b["sfc_kg_N_s"]["n"] == 2 and b["sfc_kg_N_s"]["low"] == pytest.approx(0.12 / 3600.0)
    assert "specific_thrust_N_s_kg" not in b


def test_nothing_is_scaled_with_frontal_area():
    """ADR-0024: engines are characterised by specific thrust and SFC; diameter is a fit check only."""
    m = engine_metrics(engine(air_mass_flow_kg_s=1.6), RHO, G)
    assert not any("area" in name for name in m.__dataclass_fields__)
    assert not any("area" in name for name in technology_bounds({"a": m}))


def test_repo_catalogue_is_internally_consistent():
    """Vendors' own SFC and volume flow must imply a fuel density inside the specification range."""
    density = load_fuel_density()
    metrics = catalogue_metrics(load_engine_catalogue(), density.value, load_gravity())
    implied = implied_fuel_densities(metrics)
    assert len(implied) >= 3
    assert all(density.low <= rho <= density.high for rho in implied.values())
    assert all(isinstance(m, EngineMetrics) for m in metrics.values())
