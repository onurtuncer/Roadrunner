"""Figures for the off_design notebook."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from roadrunner_re.off_design import OffDesignStudy


def _save(fig, save_path):
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=150)
    return fig


def lapse_figure(study: OffDesignStudy, save_path: str | Path | None = None):
    """Thrust at maximum power over standard-day sea-level static thrust, cycle against the algebraic lapse."""
    days = sorted({r["dT_isa_K"] for r in study.lapse_rows})
    fig, axes = plt.subplots(1, len(days), figsize=(5.2 * len(days), 4.2), sharey=True, squeeze=False)
    for ax, dT in zip(axes[0], days):
        for i, h in enumerate(study.config.altitudes_m):
            rows = sorted((r for r in study.lapse_rows if r["dT_isa_K"] == dT and r["altitude_m"] == h), key=lambda r: r["mach"])
            colour = f"C{i}"
            ax.plot([r["mach"] for r in rows], [r["lapse"] for r in rows], "o-", color=colour, label=f"cycle, {h:.0f} m")
            ax.plot([r["mach"] for r in rows], [r["algebraic_lapse"] for r in rows], "--", color=colour, alpha=0.7)
        ax.set(xlabel="Mach number", title=f"ISA {dT:+.0f} K (dashed: algebraic lapse of ADR-0029)")
        ax.grid(alpha=0.3)
    axes[0][0].set_ylabel(r"$T / T_{SLS,\,std}$ at maximum power [-]")
    axes[0][0].legend(fontsize=8)
    return _save(fig, save_path)


def part_throttle_figure(study: OffDesignStudy, save_path: str | Path | None = None):
    """SFC and shaft speed against thrust fraction, at the mission's conditions."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for label in dict.fromkeys(r["condition"] for r in study.part_rows):
        rows = sorted((r for r in study.part_rows if r["condition"] == label), key=lambda r: r["thrust_fraction"])
        f = [r["thrust_fraction"] for r in rows]
        a.plot(f, [r["sfc_kg_N_s"] * 3600.0 for r in rows], "o-", label=label)
        b.plot(f, [r["speed_fraction"] for r in rows], "o-", label=label)
    b.axhline(study.config.min_speed_fraction, color="k", ls=":", label="validity limit")
    a.set(xlabel="thrust / maximum thrust at the condition [-]", ylabel="SFC, real [kg/(N h)]", title="Part-throttle SFC")
    b.set(xlabel="thrust / maximum thrust at the condition [-]", ylabel="shaft speed / design speed [-]", title="Shaft speed")
    a.legend(fontsize=8)
    for ax in (a, b):
        ax.grid(alpha=0.3)
    return _save(fig, save_path)
