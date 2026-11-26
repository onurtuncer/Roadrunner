"""Geometry from scaled public imagery, as intervals (ADR-0007).

A feature is measured as a pair of pixel points in an image that also
contains the overall length. Its true size is

    size = (feature_px / reference_px) / foreshortening * length_overall

Three uncertainties are carried as intervals and multiplied through:
pixel picking (each endpoint is uncertain by a stated number of pixels),
foreshortening (the judged range of apparent/true length for that view)
and the length anchor itself. A quantity measured in several images
takes the envelope of the per-image intervals and the mean of the
nominals: views are evidence of how wrong one view can be, so they
widen the answer rather than narrow it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from roadrunner_re.config import ConfigError, load_yaml
from roadrunner_re.uncertain import Uncertain, parse_uncertain

REFERENCE_QUANTITY = "length_overall_m"
#: Each segment has two endpoints, each picked to within the stated uncertainty.
ENDPOINTS_PER_SEGMENT = 2


@dataclass(frozen=True)
class Measurement:
    image_id: str
    quantity: str
    p1_px: tuple[float, float]
    p2_px: tuple[float, float]

    @property
    def length_px(self) -> float:
        return math.dist(self.p1_px, self.p2_px)


@dataclass(frozen=True)
class Image:
    id: str
    foreshortening: Uncertain
    measurements: tuple[Measurement, ...]

    @property
    def reference(self) -> Measurement:
        refs = [m for m in self.measurements if m.quantity == REFERENCE_QUANTITY]
        if len(refs) != 1:
            raise ConfigError(f"image {self.id!r}: need exactly one {REFERENCE_QUANTITY} measurement, found {len(refs)}")
        return refs[0]


def load_imagery(path: str | Path = "evidence/imagery.yaml") -> tuple[float, tuple[Image, ...]]:
    """Pixel-pick uncertainty and the images that have measurements."""
    raw = load_yaml(path)
    images = []
    for img in raw.get("images") or []:
        if not img.get("measurements"):
            continue  # listed as a source, not yet measured
        where = f"{path}:{img['id']}"
        if not img.get("url") and not img.get("page"):
            raise ConfigError(f"{where}: a measured image needs a url or page")
        if img.get("foreshortening") is None:
            raise ConfigError(f"{where}: a measured image needs a foreshortening range")
        f = img["foreshortening"]
        foreshortening = parse_uncertain({"value": f.get("value", 0.5 * (f["low"] + f["high"])), **f}, where)
        if foreshortening.low <= 0 or foreshortening.high > 1.0:
            raise ConfigError(f"{where}: foreshortening is apparent/true length, in (0, 1]")
        measurements = tuple(
            Measurement(img["id"], m["quantity"], tuple(map(float, m["p1_px"])), tuple(map(float, m["p2_px"])))
            for m in img["measurements"])
        images.append(Image(img["id"], foreshortening, measurements))
    return float(raw["pixel_pick_uncertainty_px"]), tuple(images)


def _scaled(feature_px: float, reference_px: float, pick_px: float,
            foreshortening: Uncertain, length: Uncertain) -> Uncertain:
    slack = ENDPOINTS_PER_SEGMENT * pick_px
    if feature_px <= slack or reference_px <= slack:
        raise ConfigError("a measured segment is no longer than its own pixel-pick uncertainty")
    ratio = feature_px / reference_px
    ratio_low = (feature_px - slack) / (reference_px + slack)
    ratio_high = (feature_px + slack) / (reference_px - slack)
    return Uncertain(
        value=ratio / foreshortening.value * length.value,
        low=ratio_low * length.low,                         # feature seen at full length
        high=ratio_high / foreshortening.low * length.high,  # feature seen most foreshortened
    )


def reduce_measurements(images: tuple[Image, ...], pick_px: float, length: Uncertain) -> dict[str, Uncertain]:
    """Quantity name -> size interval in metres, over all images."""
    per_quantity: dict[str, list[Uncertain]] = {}
    for image in images:
        reference_px = image.reference.length_px
        for m in image.measurements:
            if m.quantity != REFERENCE_QUANTITY:
                per_quantity.setdefault(m.quantity, []).append(
                    _scaled(m.length_px, reference_px, pick_px, image.foreshortening, length))
    return {
        name: Uncertain(value=sum(v.value for v in views) / len(views),
                        low=min(v.low for v in views), high=max(v.high for v in views))
        for name, views in sorted(per_quantity.items())
    }


def engine_envelope_diameter(nacelle_outer_diameter: Uncertain, wall: Uncertain, clearance: Uncertain) -> Uncertain:
    """Largest engine diameter that fits the nacelle: outer diameter less wall and clearance on both sides."""
    def inside(d: float, w: float, c: float) -> float:
        return d - 2.0 * (w + c)
    low = inside(nacelle_outer_diameter.low, wall.high, clearance.high)
    if low <= 0:
        raise ConfigError("engine envelope closes to nothing at the lower geometry bound")
    return Uncertain(inside(nacelle_outer_diameter.value, wall.value, clearance.value), low,
                     inside(nacelle_outer_diameter.high, wall.low, clearance.low))


def missing_quantities(measured: dict[str, Uncertain], path: str | Path = "geometry.yaml") -> list[str]:
    """Required quantities (config/geometry.yaml) that no image has measured yet."""
    return [q for q in load_yaml(path)["required_quantities"] if q not in measured]
