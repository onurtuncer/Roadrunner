"""Figures for the mission_profile notebook."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from roadrunner_re.mission_timeline import SegmentView

_SEGMENT_COLOURS = {
    "vertical_launch": "tab:red", "climb": "tab:orange", "dash": "tab:blue", "cruise": "tab:green",
    "loiter": "tab:purple", "descent": "tab:orange", "vertical_landing": "tab:red",
}


def mission_profile_figure(views: list[SegmentView], save_path: str | Path | None = None):
    """Altitude, Mach number and true airspeed along the mission.

    Segment widths are to scale where the profile fixes a duration. Climb and
    descent durations are set by the thrust margin, so they are drawn at the
    mean width of the other segments and hatched: not to scale.
    """
    known = [v.duration_s.value for v in views if v.duration_s is not None]
    unscaled_width = float(np.mean(known))
    edges, t = [], 0.0
    for v in views:
        width = v.duration_s.value if v.duration_s is not None else unscaled_width
        edges.append((t, t + width))
        t += width

    fig, (ax_h, ax_m) = plt.subplots(2, 1, figsize=(11, 6.4), sharex=True, height_ratios=(3, 2))
    for v, (t0, t1) in zip(views, edges):
        scaled = v.duration_s is not None
        colour = _SEGMENT_COLOURS[v.type]
        for ax in (ax_h, ax_m):
            ax.axvspan(t0, t1, color=colour, alpha=0.08, hatch=None if scaled else "//", lw=0)
        ax_h.plot([t0, t1], [v.altitude_start_m.value, v.altitude_end_m.value], color=colour, lw=2.5)
        lo = np.array([v.altitude_start_m.low, v.altitude_end_m.low])
        hi = np.array([v.altitude_start_m.high, v.altitude_end_m.high])
        ax_h.fill_between([t0, t1], lo, hi, color=colour, alpha=0.18, lw=0)
        ax_h.annotate(v.id, ((t0 + t1) / 2, hi.max()), xytext=(0, 6), textcoords="offset points",
                      ha="center", fontsize=8, rotation=0 if scaled and t1 - t0 > 0.06 * t else 90)
        if v.mach is not None and v.true_airspeed_m_s is not None:
            ax_m.plot([t0, t1], [v.mach.value] * 2, color=colour, lw=2.5)
            ax_m.fill_between([t0, t1], v.mach.low, v.mach.high, color=colour, alpha=0.18, lw=0)
    ax_h.set_ylabel("Altitude [m]  (band: input bounds)")
    ax_h.set_ylim(0, 1.18 * max(v.altitude_end_m.high for v in views))
    ax_m.set_ylabel("Mach  (band: input bounds)")
    ax_m.set_xlabel("Mission time [s]; hatched segments are not to scale (duration set by the mission analysis)")
    ax_m.set_ylim(0, 1)
    for ax in (ax_h, ax_m):
        ax.grid(alpha=0.3)
    ax_h.set_title("Sample mission profile (assumed numbers, hot day)")
    fig.tight_layout()
    if save_path is not None:
        fig.savefig(save_path, dpi=130)
    return fig
