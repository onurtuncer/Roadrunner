"""Config loaders and the provenance rule (ADR-0005, ADR-0018, ADR-0023)."""
import copy

import pytest
import yaml

from roadrunner_re import ConfigError, load_claims, load_engine_catalogue, load_mission
from roadrunner_re.config import CONFIG_DIR, load_yaml
from roadrunner_re.uncertain import Uncertain, parse_uncertain


@pytest.fixture(scope="module")
def claims():
    return load_claims()


@pytest.fixture(scope="module")
def mission(claims):
    return load_mission(claims=claims)


def _write(tmp_path, data, name="mission.yaml"):
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


# --- evidence ledger ---------------------------------------------------

def test_claims_load_with_sources_and_tiers(claims):
    assert claims, "ledger is empty"
    for claim in claims.values():
        assert claim.source.startswith("https://")
        assert claim.tier in ("A", "B", "C", "X")


def test_marketing_comparative_is_not_an_input(claims):
    assert not claims["range_ten_times_comparators"].usable_as_input


def test_claim_without_source_is_rejected(tmp_path):
    path = _write(tmp_path, [{"id": "x", "statement": "s", "tier": "A", "accessed": "2026-11-26"}], "claims.yaml")
    with pytest.raises(ConfigError, match="source"):
        load_claims(path)


# --- mission profile ---------------------------------------------------

def test_sample_mission_shape(mission):
    assert mission.name == "sample"
    assert [s.type for s in mission.segments] == [
        "vertical_launch", "climb", "dash", "loiter", "cruise", "descent", "vertical_landing"]


def test_every_segment_states_where_its_numbers_come_from(mission, claims):
    for seg in mission.segments:
        assert seg.basis.evidence or seg.basis.assumption, seg.id
        assert set(seg.basis.evidence) <= set(claims)


def test_segment_references_resolve(mission):
    assert mission.resolve("dash_out", "altitude_m") == mission.resolve("climb_out", "to_altitude_m")
    assert mission.resolve("cruise_back", "distance_m") == mission.resolve("dash_out", "distance_m")


def test_uncertain_inputs_are_exposed_for_the_uncertainty_analysis(mission):
    inputs = mission.uncertain_inputs()
    assert "dash_out.mach" in inputs and "payload.mass_kg" in inputs
    assert all(u.low < u.high for u in inputs.values())
    assert "launch.altitude_m" not in inputs  # fixed values are not uncertain inputs


def test_mission_citing_a_tier_x_claim_is_rejected(tmp_path, claims):
    raw = copy.deepcopy(load_yaml("missions/sample.yaml"))
    raw["segments"][2]["basis"]["evidence"] = ["range_ten_times_comparators"]
    with pytest.raises(ConfigError, match="never an input"):
        load_mission(_write(tmp_path, raw), claims)


def test_mission_citing_unknown_evidence_is_rejected(tmp_path, claims):
    raw = copy.deepcopy(load_yaml("missions/sample.yaml"))
    raw["segments"][0]["basis"] = {"evidence": "no_such_claim"}
    with pytest.raises(ConfigError, match="unknown evidence"):
        load_mission(_write(tmp_path, raw), claims)


def test_numbers_without_a_basis_are_rejected(tmp_path, claims):
    raw = copy.deepcopy(load_yaml("missions/sample.yaml"))
    del raw["segments"][3]["basis"]
    with pytest.raises(ConfigError, match="basis"):
        load_mission(_write(tmp_path, raw), claims)


def test_uncertain_value_must_lie_within_its_bounds():
    with pytest.raises(ConfigError):
        parse_uncertain({"value": 2.0, "low": 0.0, "high": 1.0}, "x")
    assert parse_uncertain(3, "x") == Uncertain(3.0, 3.0, 3.0)


# --- engine catalogue --------------------------------------------------

def test_catalogue_loads_with_sources():
    engines = load_engine_catalogue()
    assert len(engines) >= 10
    assert {e.vendor for e in engines.values()} >= {"PBS Velka Bites", "JetCat", "AMT Netherlands"}
    for engine in engines.values():
        assert engine.source.startswith("https://")
        assert engine.thrust_max_low_N <= engine.thrust_max_N


def test_thrust_range_and_missing_fields_are_kept_honest():
    engines = load_engine_catalogue()
    assert engines["pbs_tj100"].thrust_max_low_N < engines["pbs_tj100"].thrust_max_N
    assert "mass_engine_kg" in engines["pbs_tj100"].missing_fields
    assert engines["jetcat_p1000_pro"].thrust_idle_N == 45


def test_catalogue_entry_with_a_non_positive_number_is_rejected(tmp_path):
    raw = copy.deepcopy(load_yaml("reference_engines.yaml"))
    raw[0]["diameter_m"] = 0
    with pytest.raises(ConfigError):
        load_engine_catalogue(_write(tmp_path, raw, "engines.yaml"))


def test_config_directory_is_where_the_adrs_say():
    assert (CONFIG_DIR / "atmosphere.yaml").is_file()
