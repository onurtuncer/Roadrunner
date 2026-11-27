"""Figures for the preliminary constraint and mission analysis notebooks (ADR-0029, ADR-0031)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from roadrunner_re.analysis_inputs import AnalysisInputs
from roadrunner_re.constraints import thrust_loading_curve
from roadrunner_re.design_point import DesignPoint


def _save(fig, save_path):
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=150)
    return fig


def constraint_diagram(inputs: AnalysisInputs, dp: DesignPoint, save_path: str | Path | None = None, *,
                       reference: tuple[AnalysisInputs, DesignPoint] | None = None):
    """Thrust loading against wing loading (W_TO g / S_ref), lecture style, with the feasible region.

    ``reference`` (inputs and design point of another engine model) is drawn dashed, same colours.
    """
    d = inputs.settings["diagram"]
    x = np.linspace(d["wing_loading_min_Pa"], d["wing_loading_max_Pa"], int(d["points"]))
    betas = dp.mission.betas()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    lower = []
    for c in inputs.requirements.constraints:
        y = np.array(thrust_loading_curve(inputs, c, x, betas[c.weight_at]))
        if c.sense == "lower_bound":
            lower.append(y)
            (line,) = ax.plot(x, y, label=c.id)
            if reference is not None:
                ref_inputs, ref_dp = reference
                ref_c = next(k for k in ref_inputs.requirements.constraints if k.id == c.id)
                ax.plot(x, thrust_loading_curve(ref_inputs, ref_c, x, ref_dp.mission.betas()[ref_c.weight_at]),
                        "--", color=line.get_color(), lw=1.0, alpha=0.8)
        else:
            ax.plot(x, y, "--", label=f"{c.id} (upper bound)")
    top = max(1.6 * dp.thrust_loading, 1.0)
    envelope = np.max(lower, axis=0)
    ax.fill_between(x, envelope, top, where=envelope < top, color="tab:green", alpha=0.12, label="feasible")
    ax.axvline(dp.wing_loading_Pa, color="k", lw=0.8, ls=":")
    ax.plot([dp.wing_loading_Pa], [dp.thrust_loading], "ko", label=f"design point ({dp.binding_constraint})")
    ax.set_ylim(0, top)
    ax.set_xlabel(r"wing loading $W_{TO}\,g / S_{ref}$ [Pa]  (S_ref = body cross-section)")
    ax.set_ylabel(r"installed thrust loading $T_{SL}/W_{TO}$ [-]")
    suffix = " (dashed: preliminary)" if reference is not None else " (first iteration)"
    ax.set_title(f"Constraint diagram, ISA +{inputs.mission.dT_isa_K.value:.0f} K{suffix}")
    sec = ax.secondary_xaxis("top", functions=(lambda p: p * inputs.polar.area_m2 / inputs.gravity_m_s2,
                                               lambda m: m * inputs.gravity_m_s2 / inputs.polar.area_m2))
    sec.set_xlabel("take-off mass [kg]")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)
    return _save(fig, save_path)


def thrust_sweep_figure(sweep: list[dict], save_path: str | Path | None = None):
    rows = [r for r in sweep if r["feasible"]]
    m = [r["takeoff_mass_kg"] for r in rows]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2))
    a.plot(m, [r["thrust_loading"] for r in rows], "o-")
    for r in rows:
        a.annotate(r["binding_constraint"], (r["takeoff_mass_kg"], r["thrust_loading"]), fontsize=6, rotation=45,
                   textcoords="offset points", xytext=(2, 4))
    a.set(xlabel="take-off mass [kg]", ylabel=r"required $T_{SL}/W_{TO}$ [-]", title="Thrust loading, binding constraint")
    b.plot(m, [r["thrust_per_engine_N"] for r in rows], "o-")
    b.set(xlabel="take-off mass [kg]", ylabel="installed thrust per engine [N]", title="Engine size (twin)")
    for ax in (a, b):
        ax.grid(alpha=0.3)
    return _save(fig, save_path)


def mission_weights_figure(dp: DesignPoint, save_path: str | Path | None = None):
    """Mass along the mission and fuel burned per segment."""
    segs = dp.mission.segments
    t, times, masses = 0.0, [0.0], [segs[0].mass_start_kg]
    for s in segs:
        t += s.duration_s
        times.append(t)
        masses.append(s.mass_end_kg)
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={"width_ratios": [1.2, 1]})
    a.plot(np.array(times) / 60.0, masses, "o-")
    a.set(xlabel="time [min]", ylabel="mass [kg]", title="Mass along the mission")
    b.barh([s.id for s in segs][::-1], [s.fuel_kg for s in segs][::-1], color="tab:orange")
    b.set(xlabel="fuel burned [kg]", title="Fuel per segment")
    for ax in (a, b):
        ax.grid(alpha=0.3)
    return _save(fig, save_path)


def mass_sweep_figure(sweep: list[dict], save_path: str | Path | None = None):
    rows = [r for r in sweep if r["feasible"]]
    m = [r["takeoff_mass_kg"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(m, [r["implied_empty_mass_kg"] for r in rows], "o-", label="implied empty mass")
    ax.plot(m, [r["propulsion_mass_kg"] for r in rows], "s-", label="propulsion (2 engines, mass law)")
    ax.plot(m, [r["total_fuel_kg"] for r in rows], "^-", label="fuel incl. reserve")
    ax.set(xlabel="take-off mass [kg]", ylabel="mass [kg]", title="What a take-off mass leaves for the vehicle")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    return _save(fig, save_path)


def fuel_comparison_figure(prelim: DesignPoint, cycle: DesignPoint, save_path: str | Path | None = None):
    """Fuel burned per segment, preliminary model against the cycle engine."""
    segs = [s.id for s in cycle.mission.segments]
    before = {s.id: s.fuel_kg for s in prelim.mission.segments}
    after = {s.id: s.fuel_kg for s in cycle.mission.segments}
    y = np.arange(len(segs))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(y + 0.2, [before[s] for s in segs], height=0.4, label="preliminary (constant TSFC)", color="tab:gray")
    ax.barh(y - 0.2, [after[s] for s in segs], height=0.4, label="cycle engine (part-throttle SFC)", color="tab:orange")
    ax.set_yticks(y, segs)
    ax.invert_yaxis()
    ax.set(xlabel="fuel burned [kg]", title="Fuel per segment")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    return _save(fig, save_path)
