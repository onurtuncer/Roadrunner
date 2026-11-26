"""The owner's hand estimate: provenance, bounds and the owner's own arithmetic."""
import math

import pytest

from roadrunner_re import IsaAtmosphere
from roadrunner_re.aero_estimate import load_aero_estimate
from roadrunner_re.config import ConfigError, load_yaml


@pytest.fixture(scope="module")
def est():
    return load_aero_estimate()


def test_estimate_is_tier_c_with_provenance(est):
    assert est.tier == "C" and est.assumption and len(est.sources) == 3


def test_bounds_are_thirty_percent_except_fixed_values(est):
    for section in ("geometry", "estimates"):
        for name, u in est[section].items():
            if u.is_fixed:
                assert name.endswith("_count")
            else:
                assert u.low == pytest.approx(0.7 * u.value, rel=2e-3) and u.high == pytest.approx(1.3 * u.value, rel=2e-3)
    assert all(u.is_fixed for u in est["reference_condition"].values())


def test_tier_x_or_missing_basis_is_rejected(tmp_path):
    raw = load_yaml("aero_estimate.yaml")
    raw["tier"] = "B"
    import yaml
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_aero_estimate(bad)


def test_reference_area_is_the_missile_convention(est):
    d = est["geometry"]["body_diameter_m"].value
    assert est["geometry"]["s_ref_m2"].value == pytest.approx(math.pi * d**2 / 4, rel=0.01)


def test_component_cn_alphas_sum_to_the_total(est):
    parts = sum(est["estimates"][f"cn_alpha_{c}_per_rad"].value for c in ("wing", "body", "tail"))
    assert parts == pytest.approx(est["estimates"]["cn_alpha_per_rad"].value, rel=0.03)


def test_dynamic_pressure_and_reynolds_follow_isa_sea_level(est):
    state = IsaAtmosphere.from_yaml().at(0.0)
    mach = est["reference_condition"]["mach"].value
    v = mach * state.speed_of_sound_m_s
    assert 0.5 * state.density_kg_m3 * v**2 == pytest.approx(est["reference_condition"]["dynamic_pressure_Pa"].value, rel=0.01)
    re = state.density_kg_m3 * v * est["geometry"]["length_m"].value / state.dynamic_viscosity_Pa_s
    assert re == pytest.approx(est["reference_condition"]["reynolds_length"].value, rel=0.02)


def test_owner_sanity_checks_reproduce(est):
    q, s = est["reference_condition"]["dynamic_pressure_Pa"].value, est["geometry"]["s_ref_m2"].value
    e = est["estimates"]
    c = est.sanity_checks["cruise_1g_mach_0_6"]
    cn = c["weight_N"] / (q * s)
    drag = q * s * (e["cd0"].value + e["induced_drag_factor_k"].value * cn**2)
    assert cn == pytest.approx(c["cn"], rel=0.02)
    assert math.degrees(cn / e["cn_alpha_per_rad"].value) == pytest.approx(c["alpha_deg"], rel=0.03)
    assert drag == pytest.approx(c["drag_N"], rel=0.02)
    assert cn * q * s / drag == pytest.approx(c["l_over_d"], rel=0.03)
    k, cd0 = e["induced_drag_factor_k"].value, e["cd0"].value
    assert math.sqrt(cd0 / k) / (2 * cd0) == pytest.approx(e["l_over_d_max"].value, rel=0.03)
    g = est.sanity_checks["g_limit_at_alpha_20_deg"]
    assert g["cn"] * q * s / c["weight_N"] == pytest.approx(g["g_at_mach_0_6"], rel=0.05)
    assert drag > 0 and e["drag_area_m2"].value == pytest.approx(cd0 * s, rel=0.06)
