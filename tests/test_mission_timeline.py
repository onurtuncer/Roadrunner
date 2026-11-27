import pytest

from roadrunner_re import IsaAtmosphere, load_mission
from roadrunner_re.mission_timeline import mission_timeline


@pytest.fixture(scope="module")
def views():
    return {v.id: v for v in mission_timeline(load_mission(), IsaAtmosphere.from_yaml())}


def test_dash_time_is_distance_over_true_airspeed(views):
    v = views["dash_out"]
    assert v.duration_s.value == pytest.approx(v.distance_m.value / v.true_airspeed_m_s.value, rel=1e-9)
    assert v.duration_s.low < v.duration_s.value < v.duration_s.high


def test_climb_duration_is_not_assumed(views):
    assert views["climb_out"].duration_s is None


def test_glide_time_is_altitude_over_sink_rate(views):
    """Nominal 3000 m at 10 m/s; bounds from 1000 m at 20 m/s to 6000 m at 5 m/s (ADR-0038)."""
    d = views["descent"].duration_s
    assert (d.value, d.low, d.high) == pytest.approx((300.0, 50.0, 1200.0))


def test_level_segments_follow_the_climb_altitude(views):
    assert views["loiter"].altitude_end_m == views["climb_out"].altitude_end_m
    assert views["descent"].altitude_start_m == views["climb_out"].altitude_end_m
    assert views["descent"].altitude_end_m.value == 0.0
