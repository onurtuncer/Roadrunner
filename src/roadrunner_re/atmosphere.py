"""The one atmosphere model (ADR-0017): International Standard Atmosphere.

A flight condition anywhere in this repo is ``(altitude_m, mach,
dT_isa_K)``. Altitude is geopotential. A non-standard day is a
temperature offset applied at constant pressure altitude: pressure is
the standard pressure for that altitude, temperature is standard plus
the offset, density follows from the gas law.

The defining constants live in ``config/atmosphere.yaml``. Evaluation is
pure and accepts NumPy arrays.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np

from roadrunner_re.config import ConfigError, load_yaml


class AirState(NamedTuple):
    temperature_K: float | np.ndarray
    pressure_Pa: float | np.ndarray
    density_kg_m3: float | np.ndarray
    speed_of_sound_m_s: float | np.ndarray
    dynamic_viscosity_Pa_s: float | np.ndarray


@dataclass(frozen=True)
class _Layer:
    base_altitude_m: float
    lapse_rate_K_m: float
    base_temperature_K: float
    base_pressure_Pa: float


@dataclass(frozen=True)
class IsaAtmosphere:
    gravity_m_s2: float
    gas_constant_J_kg_K: float
    gamma: float
    floor_m: float
    ceiling_m: float
    sutherland_beta: float
    sutherland_S_K: float
    layers: tuple[_Layer, ...]

    @classmethod
    def from_yaml(cls, path: str | Path = "atmosphere.yaml") -> "IsaAtmosphere":
        cfg = load_yaml(path)
        g, R = float(cfg["gravity_m_s2"]), float(cfg["gas_constant_J_kg_K"])
        raw = cfg["layers"]
        bases = [float(layer["base_altitude_m"]) for layer in raw]
        if bases != sorted(bases) or len(set(bases)) != len(bases):
            raise ConfigError(f"{path}: layers must be listed bottom to top")
        if not (bases[0] <= float(cfg["floor_m"]) < float(cfg["ceiling_m"])):
            raise ConfigError(f"{path}: need first layer base <= floor_m < ceiling_m")

        layers: list[_Layer] = []
        T, p = float(cfg["sea_level"]["temperature_K"]), float(cfg["sea_level"]["pressure_Pa"])
        for i, layer in enumerate(raw):
            lapse = float(layer["lapse_rate_K_m"])
            layers.append(_Layer(bases[i], lapse, T, p))
            if i + 1 < len(raw):  # carry temperature and pressure up to the next base
                T, p = cls._within_layer(layers[-1], bases[i + 1], g, R)
        return cls(g, R, float(cfg["gamma"]), float(cfg["floor_m"]), float(cfg["ceiling_m"]),
                   float(cfg["sutherland"]["beta_kg_m_s_sqrtK"]), float(cfg["sutherland"]["S_K"]), tuple(layers))

    @staticmethod
    def _within_layer(layer: _Layer, altitude_m, g: float, R: float):
        dh = altitude_m - layer.base_altitude_m
        if layer.lapse_rate_K_m == 0.0:  # isothermal
            return layer.base_temperature_K + 0.0 * dh, layer.base_pressure_Pa * np.exp(-g * dh / (R * layer.base_temperature_K))
        T = layer.base_temperature_K + layer.lapse_rate_K_m * dh
        return T, layer.base_pressure_Pa * (T / layer.base_temperature_K) ** (-g / (layer.lapse_rate_K_m * R))

    def at(self, altitude_m, dT_isa_K=0.0) -> AirState:
        """Air properties at a geopotential altitude, with an optional ISA temperature offset."""
        h = np.asarray(altitude_m, dtype=float)
        if np.any(h < self.floor_m) or np.any(h > self.ceiling_m):
            raise ValueError(f"altitude outside the modelled range [{self.floor_m}, {self.ceiling_m}] m")

        T_std, p = self._within_layer(self.layers[0], h, self.gravity_m_s2, self.gas_constant_J_kg_K)
        for layer in self.layers[1:]:
            T_l, p_l = self._within_layer(layer, h, self.gravity_m_s2, self.gas_constant_J_kg_K)
            above = h >= layer.base_altitude_m
            T_std, p = np.where(above, T_l, T_std), np.where(above, p_l, p)

        T = T_std + np.asarray(dT_isa_K, dtype=float)
        if np.any(T <= 0.0):
            raise ValueError("temperature offset gives a non-positive absolute temperature")
        rho = p / (self.gas_constant_J_kg_K * T)
        a = np.sqrt(self.gamma * self.gas_constant_J_kg_K * T)
        mu = self.sutherland_beta * T**1.5 / (T + self.sutherland_S_K)
        state = AirState(T, p + 0.0 * T, rho, a, mu)
        if state.temperature_K.ndim == 0:
            return AirState(*(float(x) for x in state))
        return state

    def dynamic_pressure_Pa(self, altitude_m, mach, dT_isa_K=0.0):
        """q = (gamma / 2) p M^2."""
        return 0.5 * self.gamma * self.at(altitude_m, dT_isa_K).pressure_Pa * np.asarray(mach, dtype=float) ** 2

    def true_airspeed_m_s(self, altitude_m, mach, dT_isa_K=0.0):
        return self.at(altitude_m, dT_isa_K).speed_of_sound_m_s * np.asarray(mach, dtype=float)
