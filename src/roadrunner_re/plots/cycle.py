"""Figures for the cycle_design_point notebook."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from roadrunner_re.cycle.turbojet import CycleResult

_ORDER = ("2", "3", "4", "5", "8")


def station_figure(result: CycleResult, save_path: str | Path | None = None):
    """Total temperature and pressure through the engine, ARP755 stations."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(9.5, 4))
    a.plot(_ORDER, [result.stations[s][0] for s in _ORDER], "o-", color="tab:red")
    a.set(xlabel="ARP755 station", ylabel="total temperature [K]", title="Total temperature")
    b.plot(_ORDER, [result.stations[s][1] / 1e3 for s in _ORDER], "o-", color="tab:blue")
    b.set(xlabel="ARP755 station", ylabel="total pressure [kPa]", title="Total pressure")
    for ax in (a, b):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=150)
    return fig


def tornado_figure(rows: list[dict], nominal: CycleResult, save_path: str | Path | None = None):
    """Change of air flow and SFC when each assumed input moves to its bounds, one at a time."""
    names = list(dict.fromkeys(r["input"] for r in rows))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, key, ref, title in ((axes[0], "air_mass_flow_kg_s", nominal.air_mass_flow_kg_s, "air flow"),
                                (axes[1], "sfc_kg_N_s", nominal.sfc_kg_N_s, "ideal SFC")):
        for i, name in enumerate(names):
            vals = [100.0 * (r[key] / ref - 1.0) for r in rows if r["input"] == name]
            ax.barh(i, max(vals) - min(vals), left=min(vals), color="tab:blue")
        ax.axvline(0, color="k", lw=0.8)
        ax.set_yticks(range(len(names)), names)
        ax.set(xlabel="change from nominal [%]", title=title)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=150)
    return fig
