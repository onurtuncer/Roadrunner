"""Design-regression pins on the out/ handoffs (ADR-0014).

Run in the design pipeline against freshly generated handoffs. An
intentional change to results updates these pins in the same commit.
"""
import pytest
import yaml

from roadrunner_re import load_claims
from roadrunner_re.config import REPO_ROOT
from roadrunner_re.evidence import evidence_handoff

OUT = REPO_ROOT / "out"


def test_evidence_handoff_matches_the_ledger():
    handoff = yaml.safe_load((OUT / "evidence.yaml").read_text(encoding="utf-8"))
    assert handoff == evidence_handoff(load_claims())


def test_evidence_pins():
    handoff = yaml.safe_load((OUT / "evidence.yaml").read_text(encoding="utf-8"))
    assert handoff["counts_by_tier"] == {"A": 9, "B": 9, "C": 0, "X": 2}
    assert handoff["quantities"]["length_overall_m"]["value"] == pytest.approx(1.5)
    assert set(handoff["quantities"]) == {"length_overall_m", "takeoff_mass_kg", "speed_max_m_s"}
    assert handoff["hypotheses_not_inputs"] == ["engines_most_power_dense", "range_ten_times_comparators"]


def test_technology_pins():
    """Catalogue-derived technology levels (notebook 4). Vendor data in, so these move only with the catalogue."""
    t = yaml.safe_load((OUT / "technology.yaml").read_text(encoding="utf-8"))
    assert t["engines"] == 12 and len(t["vendors"]) == 3
    b = t["bounds"]
    assert "thrust_per_frontal_area_N_m2" not in b  # ADR-0024
    assert (b["specific_thrust_N_s_kg"]["low"], b["specific_thrust_N_s_kg"]["high"], b["specific_thrust_N_s_kg"]["n"]) == \
        pytest.approx((506.41, 634.328, 8), rel=1e-5)
    assert (b["thrust_to_weight"]["low"], b["thrust_to_weight"]["high"]) == pytest.approx((6.23756, 11.8467), rel=1e-5)
    assert (b["sfc_kg_N_s"]["low"], b["sfc_kg_N_s"]["high"]) == pytest.approx((3.22222e-05, 4.38889e-05), rel=1e-5)
    assert (b["idle_thrust_fraction"]["low"], b["idle_thrust_fraction"]["high"]) == \
        pytest.approx((0.0329412, 0.0510204), rel=1e-5)
    c = t["mass_correlation"]
    assert (c["coefficient"], c["exponent"], c["n"]) == pytest.approx((0.00232506, 1.24446, 12), rel=1e-5)


def test_datasheets_imply_the_configured_fuel_density_within_one_percent():
    t = yaml.safe_load((OUT / "technology.yaml").read_text(encoding="utf-8"))
    used = t["fuel_density_kg_m3"]["used"]
    implied = t["fuel_density_kg_m3"]["implied_by_datasheets"]
    assert len(implied) == 5
    assert all(abs(rho / used - 1.0) < 0.01 for rho in implied.values())


def test_validation_pins():
    """Anchored cycle model and leave-one-out blind test (notebook 5). Solver results: pinned to 0.1 %."""
    v = yaml.safe_load((OUT / "validation.yaml").read_text(encoding="utf-8"))
    assert v["pass_counts"] == {"specific_thrust_N_s_kg": {"passed": 5, "of": 8}, "sfc_kg_N_s": {"passed": 6, "of": 6}}
    t = v["anchored_technology"]
    assert (t["Tt4_K"]["low"], t["Tt4_K"]["high"], t["Tt4_K"]["n"]) == pytest.approx((1088.3, 1301.3, 8), rel=1e-3)
    assert (t["combustion_efficiency"]["low"], t["combustion_efficiency"]["high"]) == \
        pytest.approx((0.74911, 0.98707), rel=1e-3)
    assert (t["egt_residual_K"]["low"], t["egt_residual_K"]["high"], t["egt_residual_K"]["n"]) == \
        pytest.approx((-121.4, 134.0, 4), abs=1.0)
    assert (t["specific_thrust_N_s_kg"]["low"], t["specific_thrust_N_s_kg"]["high"]) == \
        pytest.approx((506.41, 634.33), rel=1e-3)
    p1000 = v["leave_one_out"]["jetcat_p1000_pro"]["specific_thrust_N_s_kg"]
    assert (p1000["published"], p1000["value"], p1000["inside"]) == pytest.approx((611.11, 597.2, True), rel=2e-3)
