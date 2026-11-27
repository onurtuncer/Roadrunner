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
    """Catalogue-derived technology levels (reference_engines). Vendor data in, so these move only with the catalogue."""
    t = yaml.safe_load((OUT / "technology.yaml").read_text(encoding="utf-8"))
    assert t["engines"] == 9 and len(t["vendors"]) == 2
    b = t["bounds"]
    assert "thrust_per_frontal_area_N_m2" not in b  # ADR-0024
    assert (b["specific_thrust_N_s_kg"]["low"], b["specific_thrust_N_s_kg"]["high"], b["specific_thrust_N_s_kg"]["n"]) == \
        pytest.approx((506.41, 627.2, 5), rel=1e-5)
    assert (b["thrust_to_weight"]["low"], b["thrust_to_weight"]["high"]) == pytest.approx((6.23756, 11.8467), rel=1e-5)
    assert (b["sfc_kg_N_s"]["low"], b["sfc_kg_N_s"]["high"]) == pytest.approx((3.22222e-05, 4.1519e-05), rel=1e-5)
    assert (b["idle_thrust_fraction"]["low"], b["idle_thrust_fraction"]["high"]) == \
        pytest.approx((0.0331633, 0.0510204), rel=1e-5)
    c = t["mass_correlation"]
    assert (c["coefficient"], c["exponent"], c["n"]) == pytest.approx((0.00283757, 1.2225, 9), rel=1e-5)


def test_datasheets_imply_the_configured_fuel_density_within_one_percent():
    t = yaml.safe_load((OUT / "technology.yaml").read_text(encoding="utf-8"))
    used = t["fuel_density_kg_m3"]["used"]
    implied = t["fuel_density_kg_m3"]["implied_by_datasheets"]
    assert len(implied) == 2
    assert all(abs(rho / used - 1.0) < 0.01 for rho in implied.values())


def test_validation_pins():
    """Anchored cycle model and leave-one-out blind test (method_validation). Solver results: pinned to 0.1 %."""
    v = yaml.safe_load((OUT / "validation.yaml").read_text(encoding="utf-8"))
    assert v["pass_counts"] == {"specific_thrust_N_s_kg": {"passed": 2, "of": 5}, "sfc_kg_N_s": {"passed": 1, "of": 3}}
    t = v["anchored_technology"]
    assert (t["Tt4_K"]["low"], t["Tt4_K"]["high"], t["Tt4_K"]["n"]) == pytest.approx((1088.0, 1274.8, 5), rel=1e-3)
    assert (t["combustion_efficiency"]["low"], t["combustion_efficiency"]["high"]) == \
        pytest.approx((0.74921, 0.98692), rel=1e-3)
    assert (t["egt_residual_K"]["low"], t["egt_residual_K"]["high"], t["egt_residual_K"]["n"]) == \
        pytest.approx((-120.7, -120.7, 1), abs=1.0)
    assert (t["specific_thrust_N_s_kg"]["low"], t["specific_thrust_N_s_kg"]["high"]) == \
        pytest.approx((506.41, 627.2), rel=1e-3)
    titan = v["leave_one_out"]["amt_titan"]["specific_thrust_N_s_kg"]
    assert (titan["published"], titan["value"], titan["inside"]) == pytest.approx((593.94, 561.3, True), rel=2e-3)


def test_mission_profile_pins():
    """Mission profile laid out in time (mission_profile). Inputs in, so these move only with config/missions."""
    m = yaml.safe_load((OUT / "mission_profile.yaml").read_text(encoding="utf-8"))
    ids = [s["id"] for s in m["segments"]]
    assert ids == ["launch", "climb_out", "dash_out", "loiter", "cruise_back", "descent", "landing"]
    seg = {s["id"]: s for s in m["segments"]}
    assert m["duration_not_fixed_by_profile"] == ["climb_out", "descent"]
    assert seg["loiter"]["duration_s"] == {"value": 900.0, "low": 300.0, "high": 1800.0}
    dash = seg["dash_out"]
    assert (dash["true_airspeed_m_s"]["value"], dash["duration_s"]["value"]) == pytest.approx((272.0, 110.0), rel=0.01)
    assert dash["distance_m"] == seg["cruise_back"]["distance_m"]  # return flies the outbound distance


def test_mission_profile_requirements_pins():
    m = yaml.safe_load((OUT / "mission_profile.yaml").read_text(encoding="utf-8"))
    req = {c["id"]: c for c in m["constraints"]}
    assert list(req) == ["vertical_launch", "landing_floor", "dash", "initial_climb", "manoeuvre", "loiter_ceiling"]
    assert req["vertical_launch"]["parameters"]["thrust_to_weight_margin"] == {"value": 1.3, "low": 1.15, "high": 1.6}
    assert req["dash"]["taken_from_mission"] == ["altitude_m", "mach"]
    assert "constraint.vertical_launch.thrust_to_weight_margin" in m["uncertain_inputs"]


def test_constraint_analysis_pins():
    """First-iteration coupled analysis (constraint_analysis_preliminary, ADR-0029): nominal point exact to 1e-4."""
    c = yaml.safe_load((OUT / "constraints_preliminary.yaml").read_text(encoding="utf-8"))
    d = c["design_point"]
    assert d["binding_constraint"] == "vertical_launch"
    assert (d["takeoff_mass_kg"], d["thrust_loading"], d["thrust_per_engine_N"]) == \
        pytest.approx((85.0, 1.47422, 614.43), rel=1e-4)
    assert {r["id"] for r in c["constraints"]} == {"vertical_launch", "landing_floor", "dash", "initial_climb",
                                                 "manoeuvre", "loiter_ceiling"}
    assert len(c["takeoff_mass_sweep"]) == 12 and c["takeoff_mass_sweep"][0]["binding_constraint"] == "dash"


def test_mission_analysis_pins():
    """Fuel and weight fractions of the sample mission (mission_analysis_preliminary, ADR-0029)."""
    m = yaml.safe_load((OUT / "mission_preliminary.yaml").read_text(encoding="utf-8"))
    assert [s["id"] for s in m["segments"]] == ["launch", "climb_out", "dash_out", "loiter", "cruise_back", "descent", "landing"]
    assert (m["fuel"]["mission_kg"], m["fuel"]["total_kg"]) == pytest.approx((12.8402, 14.1242), rel=1e-4)
    assert m["masses"]["implied_empty_kg"] == pytest.approx(60.8758, rel=1e-4)
    assert m["impulse"]["total_N_s"] == pytest.approx(345427.1, rel=1e-4)
    assert m["impulse"]["total_N_s"] == pytest.approx(sum(s["impulse_N_s"] for s in m["segments"]), abs=1.0)
    assert len(m["simplifications"]) == 7


def test_cycle_design_point_pins():
    """On-design pyCycle point at OP1 (cycle_design_point, ADR-0030). Solver results: pinned to 0.1 %."""
    c = yaml.safe_load((OUT / "cycle.yaml").read_text(encoding="utf-8"))
    assert c["requirement"]["thrust_per_engine_N"] == pytest.approx(541.82, rel=1e-3)
    e = c["engine"]
    assert (e["air_mass_flow_kg_s"], e["specific_thrust_N_s_kg"], e["Tt4_K"]) == pytest.approx((0.95332, 568.35, 1231.6), rel=1e-3)
    assert e["sfc_kg_N_s"] == pytest.approx(3.3618e-05, rel=1e-3)
    assert set(c["stations_ARP755"]) == {"2", "3", "4", "5", "8"}
    assert all(v["inside_catalogue_range"] for v in c["technology_comparison"].values())
    assert len(c["one_at_a_time"]) == 2 * 7


def test_off_design_pins():
    """Off-design performance of the required engine (off_design, ADR-0032). Solver results: pinned to 0.2 %."""
    h = yaml.safe_load((OUT / "off_design.yaml").read_text(encoding="utf-8"))
    assert h["reference"]["thrust_N"] == pytest.approx(612.17, rel=2e-3)
    assert len(h["lapse_grid"]) == 30 and all(r["valid"] for r in h["lapse_grid"])
    row = next(r for r in h["lapse_grid"] if (r["altitude_m"], r["mach"], r["dT_isa_K"]) == (3000.0, 0.5, 20.0))
    assert row["lapse"] == pytest.approx(0.629, rel=5e-3)
    assert h["comparison_with_algebraic_lapse"]["max_abs_relative_difference"] == pytest.approx(0.105, rel=2e-2)
    assert len(h["part_throttle"]) == 4 * 10
    loiter = h["loiter_against_preliminary"]
    assert loiter["loiter_thrust_fraction"] == pytest.approx(0.279, rel=1e-2)
    assert loiter["ratio_cycle_to_preliminary"] == pytest.approx(1.727, rel=1e-2)
    assert h["landing"]["valid"] and h["landing"]["fraction_of_max_thrust"] == pytest.approx(0.66, rel=1e-2)


def test_cycle_based_constraint_pins():
    """Constraint analysis on the cycle lapse (constraint_analysis, ADR-0033): nominal point to 1e-3."""
    c = yaml.safe_load((OUT / "constraints.yaml").read_text(encoding="utf-8"))
    d = c["design_point"]
    assert d["binding_constraint"] == "vertical_launch"
    assert (d["thrust_loading"], d["thrust_per_engine_N"]) == pytest.approx((1.4688, 612.17), rel=1e-3)
    cmp = c["comparison_with_preliminary"]
    ratios = {r["id"]: r["ratio"] for r in cmp["constraints"]}
    assert ratios["dash"] == pytest.approx(1.06, abs=0.02) and ratios["manoeuvre"] == pytest.approx(1.08, abs=0.02)


def test_cycle_based_mission_pins():
    """Mission on the cycle engine (mission_analysis, ADR-0033): fuel to 1e-3, ratio to the preliminary mission."""
    m = yaml.safe_load((OUT / "mission.yaml").read_text(encoding="utf-8"))
    assert (m["fuel"]["mission_kg"], m["fuel"]["total_kg"]) == pytest.approx((19.890, 21.879), rel=1e-3)
    assert m["masses"]["implied_empty_kg"] == pytest.approx(53.121, rel=1e-3)
    assert m["impulse"]["total_N_s"] == pytest.approx(340467.4, rel=1e-3)
    cmp = m["comparison_with_preliminary"]
    assert cmp["mission_fuel_kg"]["ratio"] == pytest.approx(1.549, rel=1e-2)
    assert {s["id"]: s["ratio"] for s in cmp["segments"]}["loiter"] == pytest.approx(1.71, rel=1e-2)
