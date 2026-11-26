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
