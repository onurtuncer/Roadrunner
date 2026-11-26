import copy

import pytest
import yaml

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.constraint_inputs import load_constraints


@pytest.fixture(scope="module")
def req():
    return load_constraints()


def test_every_adr_0019_requirement_is_present(req):
    assert {c.type for c in req.constraints} == {
        "vertical_launch", "vertical_landing_floor", "level_flight", "climb", "sustained_load_factor", "ceiling"}


def test_only_the_landing_floor_is_an_upper_bound(req):
    assert [c.id for c in req.constraints if c.sense == "upper_bound"] == ["landing_floor"]


def test_flight_conditions_come_from_the_mission(req):
    assert req.resolve("dash", "mach") == req.mission.resolve("dash_out", "mach")
    assert req.resolve("dash", "altitude_m") == req.mission.resolve("dash_out", "altitude_m")
    assert req.resolve("manoeuvre", "altitude_m") == req.mission.resolve("climb_out", "to_altitude_m")
    assert req.resolve("loiter_ceiling", "mach") == req.mission.resolve("loiter", "mach")


def test_weight_is_taken_at_a_real_segment(req):
    ids = {s.id for s in req.mission.segments}
    assert all(c.weight_at in ids for c in req.constraints)


def test_constraint_inputs_are_uncertain_inputs(req):
    names = set(req.uncertain_inputs())
    assert "constraint.vertical_launch.thrust_to_weight_margin" in names
    assert "constraint.manoeuvre.load_factor" in names
    assert not any(n.startswith("constraint.dash.") for n in names)  # dash adds no number of its own


def _write(tmp_path, raw):
    path = tmp_path / "c.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return path


@pytest.mark.parametrize("edit", [
    lambda r: r["constraints"][0].pop("basis"),
    lambda r: r["constraints"][0].update(weight_at="nonexistent"),
    lambda r: r["constraints"][2]["mach"].update(from_segment="nonexistent"),
    lambda r: r["constraints"][0].update(sense="sideways"),
    lambda r: r["constraints"][0].update(type="warhead"),
    lambda r: r["constraints"].append(copy.deepcopy(r["constraints"][0])),
])
def test_loader_rejects_bad_requirements(tmp_path, edit):
    raw = copy.deepcopy(load_yaml("constraints.yaml"))
    edit(raw)
    with pytest.raises(ConfigError):
        load_constraints(_write(tmp_path, raw))
