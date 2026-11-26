"""Installed thrust lapse of a turbojet at maximum power (ADR-0029).

The algebraic model of UCK 474E Lecture 2 (after Mattingly, Heiser and
Pratt): thrust as a fraction of the installed sea-level static thrust, as
a function of altitude, Mach number and day. A rough first-iteration
stand-in for the engine deck that the cycle analysis will generate.
"""
from __future__ import annotations

from dataclasses import dataclass

from roadrunner_re.atmosphere import IsaAtmosphere


@dataclass(frozen=True)
class TurbojetLapse:
    c_theta: float
    c_mach: float
    c_break: float
    throttle_ratio: float

    def alpha(self, atmosphere: IsaAtmosphere, altitude_m: float, mach: float, dT_isa_K: float = 0.0) -> float:
        """Installed thrust over installed sea-level static thrust."""
        air, standard_sea_level = atmosphere.at(altitude_m, dT_isa_K), atmosphere.at(0.0)
        gamma = atmosphere.gamma
        ram = 1.0 + 0.5 * (gamma - 1.0) * mach**2
        theta_0 = air.temperature_K / standard_sea_level.temperature_K * ram
        delta_0 = air.pressure_Pa / standard_sea_level.pressure_Pa * ram ** (gamma / (gamma - 1.0))
        factor = 1.0 - self.c_theta * (theta_0 - 1.0) - self.c_mach * mach**0.5
        if theta_0 > self.throttle_ratio:
            factor -= self.c_break * (theta_0 - self.throttle_ratio) / theta_0
        return float(delta_0 * factor)
