"""Scaling pixel measurements to lengths with intervals (ADR-0007)."""
import pytest

from roadrunner_re import ConfigError
from roadrunner_re.geometry import (
    Image, Measurement, engine_envelope_diameter, load_imagery, missing_quantities, reduce_measurements,
)
from roadrunner_re.uncertain import Uncertain

EXACT = Uncertain(1.0, 1.0, 1.0)
LENGTH = Uncertain(1.5, 1.4, 1.8)


def image(image_id, feature_px, foreshortening=EXACT, reference_px=1000.0):
    return Image(image_id, foreshortening, (
        Measurement(image_id, "length_overall_m", (0.0, 0.0), (reference_px, 0.0)),
        Measurement(image_id, "body_diameter_m", (500.0, 0.0), (500.0, feature_px)),
    ))


def test_exact_inputs_give_the_plain_ratio():
    out = reduce_measurements((image("a", 200.0),), pick_px=0.0, length=Uncertain(1.5, 1.5, 1.5))
    d = out["body_diameter_m"]
    assert (d.low, d.value, d.high) == pytest.approx((0.3, 0.3, 0.3))


def test_length_anchor_bounds_carry_through():
    d = reduce_measurements((image("a", 200.0),), pick_px=0.0, length=LENGTH)["body_diameter_m"]
    assert (d.low, d.value, d.high) == pytest.approx((0.28, 0.30, 0.36))


def test_pixel_picking_widens_the_interval_both_ways():
    exact = reduce_measurements((image("a", 200.0),), 0.0, LENGTH)["body_diameter_m"]
    picked = reduce_measurements((image("a", 200.0),), 3.0, LENGTH)["body_diameter_m"]
    assert picked.low < exact.low and picked.high > exact.high and picked.value == exact.value
    assert picked.low == pytest.approx((200 - 6) / (1000 + 6) * 1.4)


def test_foreshortening_can_only_make_the_true_size_larger():
    tilted = Uncertain(0.9, 0.8, 1.0)
    d = reduce_measurements((image("a", 200.0, tilted),), 0.0, LENGTH)["body_diameter_m"]
    assert d.low == pytest.approx(0.28) and d.high == pytest.approx(0.36 / 0.8)


def test_several_views_take_the_envelope_not_the_intersection():
    one = reduce_measurements((image("a", 200.0),), 0.0, LENGTH)["body_diameter_m"]
    two = reduce_measurements((image("a", 200.0), image("b", 240.0)), 0.0, LENGTH)["body_diameter_m"]
    assert two.low == one.low and two.high > one.high
    assert two.value == pytest.approx(0.5 * (0.30 + 0.36))


def test_segment_shorter_than_its_pick_uncertainty_is_rejected():
    with pytest.raises(ConfigError):
        reduce_measurements((image("a", 5.0),), 3.0, LENGTH)


def test_image_without_a_reference_length_is_rejected():
    bad = Image("a", EXACT, (Measurement("a", "body_diameter_m", (0.0, 0.0), (0.0, 10.0)),))
    with pytest.raises(ConfigError, match="length_overall_m"):
        reduce_measurements((bad,), 0.0, LENGTH)


def test_engine_envelope_uses_the_pessimistic_combination_for_its_lower_bound():
    nacelle = Uncertain(0.20, 0.18, 0.23)
    wall, gap = Uncertain(0.003, 0.002, 0.006), Uncertain(0.005, 0.003, 0.010)
    env = engine_envelope_diameter(nacelle, wall, gap)
    assert env.value == pytest.approx(0.184)
    assert env.low == pytest.approx(0.18 - 2 * 0.016) and env.high == pytest.approx(0.23 - 2 * 0.005)


def test_repo_imagery_is_honest_about_what_has_been_measured():
    """Sources are listed; until measurements exist every required quantity is reported missing."""
    pick_px, images = load_imagery()
    assert pick_px > 0
    measured = reduce_measurements(images, pick_px, LENGTH) if images else {}
    assert set(missing_quantities(measured)) | set(measured) >= {"nacelle_outer_diameter_m", "body_diameter_m"}
