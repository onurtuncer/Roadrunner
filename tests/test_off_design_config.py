"""Loader for config/off_design.yaml (no pyCycle needed)."""
import copy

import pytest
import yaml

from roadrunner_re.config import CONFIG_DIR, ConfigError
from roadrunner_re.off_design import load_off_design_config


def _write(tmp_path, mutate):
    raw = copy.deepcopy(yaml.safe_load((CONFIG_DIR / "off_design.yaml").read_text()))
    mutate(raw)
    path = tmp_path / "off_design.yaml"
    path.write_text(yaml.safe_dump(raw))
    return path


def test_the_shipped_config_loads():
    c = load_off_design_config()
    assert c.min_speed_fraction == 0.8 and c.thrust_fractions[0] == 1.0 and "loiter" in c.part_throttle_segments


@pytest.mark.parametrize("block", ["rating", "validity", "fuel"])
def test_assumptions_need_a_stated_basis(tmp_path, block):
    with pytest.raises(ConfigError):
        load_off_design_config(_write(tmp_path, lambda r: r[block].pop("basis")))


def test_throttle_fractions_must_descend_from_one(tmp_path):
    with pytest.raises(ConfigError):
        load_off_design_config(_write(tmp_path, lambda r: r["part_throttle"].update(thrust_fractions=[0.5, 0.9])))
