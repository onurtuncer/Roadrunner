"""Engine model seam (ADR-0033): algebraic model equals the lapse; cycle model reproduces the handoff and refuses to extrapolate."""
from pathlib import Path

import pytest
import yaml

from roadrunner_re.analysis_inputs import load_analysis_inputs
from roadrunner_re.engine_model import PreliminaryEngineEstimate, CycleEngine, OutsideEngineModel

OUT = Path(__file__).resolve().parents[1] / "out"


@pytest.fixture(scope="module")
def handoff():
    return yaml.safe_load((OUT / "off_design.yaml").read_text(encoding="utf-8"))


def test_algebraic_engine_is_the_lapse():
    a = load_analysis_inputs()
    assert isinstance(a.engine, PreliminaryEngineEstimate)
    for h, m in ((0.0, 0.0), (3000.0, 0.6)):
        assert a.engine.alpha(a.atmosphere, h, m, 20.0) == a.lapse.alpha(a.atmosphere, h, m, 20.0)
    assert a.engine.sfc_kg_N_s(0.0, 0.0, 20.0, 0.3, "flight") == a.tsfc_kg_N_s


def test_cycle_engine_reproduces_grid_rows(handoff):
    a = load_analysis_inputs()
    e = CycleEngine(handoff)
    for r in handoff["lapse_grid"][:: max(1, len(handoff["lapse_grid"]) // 6)]:
        got = e.alpha(a.atmosphere, r["altitude_m"], r["mach"], r["dT_isa_K"])
        assert got == pytest.approx(r["lapse"], rel=1e-6)


def test_cycle_engine_refuses_to_extrapolate(handoff):
    a = load_analysis_inputs()
    e = CycleEngine(handoff)
    with pytest.raises(OutsideEngineModel):
        e.alpha(a.atmosphere, 9000.0, 0.5, 20.0)
    with pytest.raises(OutsideEngineModel):
        e.alpha(a.atmosphere, 0.0, 1.5, 20.0)
    with pytest.raises(OutsideEngineModel):
        e.sfc_kg_N_s(3000.0, 0.5, 20.0, 0.05, "flight")


def test_cycle_sfc_gets_worse_at_part_throttle(handoff):
    e = CycleEngine(handoff)
    assert e.sfc_kg_N_s(3000.0, 0.5, 20.0, 0.3, "flight") > e.sfc_kg_N_s(3000.0, 0.5, 20.0, 1.0, "flight")
