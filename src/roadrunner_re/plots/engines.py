"""Figures for the reference_engines notebook."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from roadrunner_re.engine_catalogue import Engine
from roadrunner_re.technology import SECONDS_PER_HOUR, EngineMetrics, MassCorrelation

VENDOR_MARKERS = {"PBS Velka Bites": "o", "JetCat": "s", "AMT Netherlands": "^"}


def catalogue_overview(engines: dict[str, Engine], metrics: dict[str, EngineMetrics],
                       correlation: MassCorrelation, save_path: str | Path | None = None):
    """Specific thrust, SFC and mass against thrust, one marker per vendor."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    panels = (
        (axes[0], lambda m: m.specific_thrust_N_s_kg, "Specific thrust [N s/kg]"),
        (axes[1], lambda m: None if m.sfc_kg_N_s is None else m.sfc_kg_N_s * SECONDS_PER_HOUR, "SFC [kg/(N h)]"),
        (axes[2], lambda m: m.mass_kg, "Mass with accessories [kg]"),
    )
    for ax, pick, label in panels:
        for vendor, marker in VENDOR_MARKERS.items():
            pts = [(m.thrust_N, pick(m)) for eid, m in metrics.items()
                   if engines[eid].vendor == vendor and pick(m) is not None]
            if pts:
                ax.scatter(*zip(*pts), marker=marker, s=55, label=vendor, zorder=3)
        ax.set_xlabel("Maximum thrust [N]")
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
    thrust = np.linspace(min(m.thrust_N for m in metrics.values()), max(m.thrust_N for m in metrics.values()), 50)
    axes[2].plot(thrust, correlation.coefficient * thrust**correlation.exponent, "k--", lw=1,
                 label=f"fit: m = {correlation.coefficient:.2e} F$^{{{correlation.exponent:.2f}}}$")
    axes[2].legend(fontsize=8)
    axes[0].set_ylim(bottom=0)
    fig.suptitle("Purchasable small turbojets: vendor sea-level static data")
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=130)
    return fig
