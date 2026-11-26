"""Figures for the method_validation notebook."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from roadrunner_re.technology import SECONDS_PER_HOUR


def blind_predictions(predictions: dict, save_path: str | Path | None = None):
    """Predicted interval against the published value, per engine, for thrust, air flow and SFC."""
    panels = (("thrust_N", 1.0, "Thrust [N]"), ("air_mass_flow_kg_s", 1.0, "Air mass flow [kg/s]"),
              ("sfc_kg_N_s", SECONDS_PER_HOUR, "SFC [kg/(N h)]"))
    names = list(predictions)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    for ax, (quantity, scale, label) in zip(axes, panels):
        for row, name in enumerate(names):
            p = predictions[name]
            u = p.predicted[quantity]
            ax.plot([u.low * scale, u.high * scale], [row, row], color="0.55", lw=5, solid_capstyle="butt", zorder=1)
            ax.plot(u.value * scale, row, "|", color="k", ms=14, zorder=2)
            if p.published[quantity] is not None:
                good = p.passed[quantity]
                ax.plot(p.published[quantity] * scale, row, "o" if good else "X", ms=8,
                        color="tab:green" if good else "tab:red", zorder=3)
        ax.set_xlabel(label)
        ax.grid(axis="x", alpha=0.3)
    axes[0].set_yticks(range(len(names)))
    axes[0].set_yticklabels(names)
    axes[0].invert_yaxis()
    fig.suptitle("Leave-one-out blind prediction: grey bar = predicted interval, tick = nominal, "
                 "dot = published (green pass, red fail)", fontsize=10)
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=130)
    return fig
