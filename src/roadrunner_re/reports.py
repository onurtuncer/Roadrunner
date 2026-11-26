"""Console tables for the notebooks (ADR-0003): presentation only, no physics."""
from __future__ import annotations

import textwrap

from roadrunner_re.engine_catalogue import Engine
from roadrunner_re.evidence import TIERS, Claim
from roadrunner_re.technology import SECONDS_PER_HOUR, EngineMetrics, MassCorrelation

TIER_MEANING = {
    "A": "stated by the manufacturer",
    "B": "secondary report or our measurement",
    "C": "inferred",
    "X": "marketing comparative, never an input",
}
_WIDTH = 78


def evidence_table(claims: dict[str, Claim]) -> str:
    """The ledger grouped by tier."""
    lines = []
    for tier in TIERS:
        group = [c for c in claims.values() if c.tier == tier]
        if not group:
            continue
        lines += ["", f"Tier {tier}: {TIER_MEANING[tier]} ({len(group)})", "-" * _WIDTH]
        for claim in group:
            lines += textwrap.wrap(f"{claim.id}: {claim.statement}", _WIDTH, subsequent_indent="    ")
    return "\n".join(lines).lstrip("\n")


def quantified_table(claims: dict[str, Claim]) -> str:
    """Quantified claims with their bounds, and the width of each bound."""
    rows = [f"{'quantity':24s}{'nominal':>10s}{'low':>10s}{'high':>10s}{'spread':>9s}  evidence", "-" * _WIDTH]
    for claim in claims.values():
        if claim.is_quantified:
            u = claim.value
            spread = (u.high - u.low) / u.value
            rows.append(f"{claim.quantity:24s}{u.value:10.4g}{u.low:10.4g}{u.high:10.4g}{spread:8.0%}  {claim.id}")
    return "\n".join(rows)


def cautions(claims: dict[str, Claim]) -> str:
    """Notes attached to ledger entries: conflicts, weak sources, open points."""
    lines = []
    for claim in claims.values():
        if claim.note:
            lines += textwrap.wrap(f"{claim.id}: {claim.note}", _WIDTH, subsequent_indent="    ") + [""]
    return "\n".join(lines).rstrip()


def _fmt(value, spec: str, width: int) -> str:
    return f"{'-':>{width}s}" if value is None else f"{format(value, spec):>{width}s}"


def catalogue_table(engines: dict[str, Engine]) -> str:
    """Vendor data as published. A dash means not yet retrieved."""
    rows = [f"{'engine':18s}{'thrust N':>10s}{'idle N':>8s}{'mass kg':>9s}{'dia mm':>8s}{'len mm':>8s}"
            f"{'air kg/s':>10s}{'PR':>6s}  tier", "-" * _WIDTH]
    for e in engines.values():
        thrust = f"{e.thrust_max_N:.0f}" if e.thrust_max_low_N == e.thrust_max_N else \
            f"{e.thrust_max_low_N:.0f}-{e.thrust_max_N:.0f}"
        mass = e.mass_system_kg if e.mass_system_kg is not None else e.mass_engine_kg
        rows.append(f"{e.id:18s}{thrust:>10s}{_fmt(e.thrust_idle_N, '.0f', 8)}{_fmt(mass, '.2f', 9)}"
                    f"{e.diameter_m * 1e3:8.0f}{_fmt(e.length_m and e.length_m * 1e3, '.0f', 8)}"
                    f"{_fmt(e.air_mass_flow_kg_s, '.2f', 10)}{_fmt(e.pressure_ratio, '.1f', 6)}  {e.tier}")
    return "\n".join(rows)


def metrics_table(metrics: dict[str, EngineMetrics]) -> str:
    """Derived figures of merit at maximum thrust."""
    rows = [f"{'engine':18s}{'Fs N s/kg':>11s}{'SFC kg/N/h':>12s}{'T/W':>7s}{'idle %':>8s}  SFC from", "-" * _WIDTH]
    for m in metrics.values():
        sfc = None if m.sfc_kg_N_s is None else m.sfc_kg_N_s * SECONDS_PER_HOUR
        idle = None if m.idle_thrust_fraction is None else 100.0 * m.idle_thrust_fraction
        rows.append(f"{m.id:18s}{_fmt(m.specific_thrust_N_s_kg, '.0f', 11)}{_fmt(sfc, '.3f', 12)}"
                    f"{_fmt(m.thrust_to_weight, '.1f', 7)}{_fmt(idle, '.1f', 8)}  {m.sfc_basis or '-'}")
    return "\n".join(rows)


def bounds_table(bounds: dict[str, dict]) -> str:
    """Catalogue-wide technology bounds."""
    scale = {"specific_thrust_N_s_kg": (1.0, "specific thrust [N s/kg]"), "sfc_kg_N_s": (SECONDS_PER_HOUR, "SFC [kg/(N h)]"),
             "thrust_to_weight": (1.0, "thrust-to-weight [-]"), "idle_thrust_fraction": (100.0, "idle thrust [% of max]"),
             "pressure_ratio": (1.0, "compressor pressure ratio [-]")}
    rows = [f"{'figure of merit':34s}{'low':>9s}{'median':>9s}{'high':>9s}{'n':>4s}", "-" * 65]
    for name, b in bounds.items():
        k, label = scale[name]
        rows.append(f"{label:34s}{b['low'] * k:9.3g}{b['median'] * k:9.3g}{b['high'] * k:9.3g}{b['n']:4d}")
    return "\n".join(rows)


def mass_correlation_line(c: MassCorrelation) -> str:
    return (f"mass_kg = {c.coefficient:.3e} * thrust_N ^ {c.exponent:.3f}   "
            f"(n = {c.n}, worst residual {c.max_abs_relative_residual:.0%})")


def implied_density_table(densities: dict[str, float], used: float) -> str:
    rows = [f"{'engine':18s}{'implied kg/m3':>15s}{'vs used':>9s}", "-" * 42]
    rows += [f"{eid:18s}{rho:15.0f}{rho / used - 1.0:+9.1%}" for eid, rho in densities.items()]
    return "\n".join(rows)


def missing_fields_table(engines: dict[str, Engine]) -> str:
    rows = []
    for e in engines.values():
        if e.missing_fields:
            rows += textwrap.wrap(f"{e.id}: {', '.join(e.missing_fields)}", _WIDTH, subsequent_indent="    ")
    return "\n".join(rows) or "every datasheet field is filled"


def anchor_table(anchors: dict) -> str:
    """Cycle model matched to each datasheet. An asterisk marks an assumed pressure ratio."""
    rows = [f"{'engine':18s}{'PR':>6s}{'Fs':>7s}{'Tt4 K':>7s}{'Tt5 K':>7s}{'EGT K':>7s}{'Tt5-EGT':>9s}"
            f"{'SFC ideal':>11s}{'SFC publ.':>11s}{'comb. eff':>11s}", "-" * 94]
    for a in anchors.values():
        pr = f"{a.pressure_ratio:.1f}{' ' if a.pressure_ratio_published else '*'}"
        published = None if a.published_sfc_kg_N_s is None else a.published_sfc_kg_N_s * SECONDS_PER_HOUR
        rows.append(f"{a.engine_id:18s}{pr:>6s}{a.specific_thrust_N_s_kg:7.0f}{a.Tt4_K:7.0f}{a.Tt5_K:7.0f}"
                    f"{_fmt(a.egt_published_K, '.0f', 7)}{_fmt(a.egt_residual_K, '+.0f', 9)}"
                    f"{a.ideal_sfc_kg_N_s * SECONDS_PER_HOUR:11.3f}{_fmt(published, '.3f', 11)}"
                    f"{_fmt(a.combustion_efficiency, '.2f', 11)}")
    return "\n".join(rows)


def blind_prediction_table(predictions: dict, quantity: str, scale: float = 1.0, unit: str = "") -> str:
    """Leave-one-out predictions of one quantity against the datasheets."""
    rows = [f"{quantity} {unit}".strip(),
            f"{'engine':18s}{'published':>11s}{'predicted':>11s}{'low':>9s}{'high':>9s}{'error':>8s}  verdict", "-" * _WIDTH]
    for p in predictions.values():
        u, pub = p.predicted[quantity], p.published[quantity]
        error = None if pub is None else u.value / pub - 1.0
        verdict = {None: "no published value", True: "pass"}.get(
            p.passed[quantity], "outside interval" if p.inside[quantity] is False else "interval too wide")
        rows.append(f"{p.engine_id:18s}{_fmt(pub and pub * scale, '.3g', 11)}{u.value * scale:11.3g}"
                    f"{u.low * scale:9.3g}{u.high * scale:9.3g}{_fmt(error, '+.0%', 8)}  {verdict}")
    return "\n".join(rows)


def mission_quotes(mission, claims: dict[str, Claim]) -> str:
    """Each segment with the ledger statements it rests on, quoted, and the stated assumption."""
    lines = []
    for seg in mission.segments:
        lines += [f"{seg.id}  ({seg.type})", "-" * _WIDTH]
        for claim_id in seg.basis.evidence:
            claim = claims[claim_id]
            lines += textwrap.wrap(f"[{claim.tier}] {claim.id}: \"{claim.statement}\"", _WIDTH,
                                   initial_indent="  ", subsequent_indent="      ")
        if seg.basis.assumption:
            lines += textwrap.wrap(f"assumption: {seg.basis.assumption}", _WIDTH,
                                   initial_indent="  ", subsequent_indent="      ")
        lines.append("")
    return "\n".join(lines).rstrip()


def mission_table(views) -> str:
    """Segment numbers as nominal (low to high). A dash means the profile does not fix it."""
    def cell(i, scale=1.0, spec=".0f"):
        if i is None:
            return "-"
        if i.low == i.high:
            return f"{i.value * scale:{spec}}"
        return f"{i.value * scale:{spec}} ({i.low * scale:{spec}}-{i.high * scale:{spec}})"

    rows = [f"{'segment':12s}{'alt end m':>18s}{'Mach':>17s}{'TAS m/s':>17s}{'time s':>19s}{'dist km':>17s}", "-" * 100]
    for v in views:
        rows.append(f"{v.id:12s}{cell(v.altitude_end_m):>18s}{cell(v.mach, spec='.2f'):>17s}"
                    f"{cell(v.true_airspeed_m_s):>17s}{cell(v.duration_s):>19s}"
                    f"{cell(v.distance_m, 1e-3, '.1f'):>17s}")
    return "\n".join(rows)


def constraint_table(constraints) -> str:
    """Each requirement with its resolved parameters. `*` marks a value taken from the mission."""
    rows = [f"{'constraint':16s}{'sense':>13s}  {'weight at':12s}parameters", "-" * 100]
    for c in constraints.constraints:
        parts = []
        for name in c.params:
            u = constraints.resolve(c.id, name)
            star = "*" if isinstance(c.params[name], str) else ""
            text = f"{u.value:g}" if u.is_fixed else f"{u.value:g} ({u.low:g}-{u.high:g})"
            parts.append(f"{name}{star} = {text}")
        rows.append(f"{c.id:16s}{c.sense:>13s}  {c.weight_at:12s}" + "; ".join(parts))
    return "\n".join(rows)


def constraint_quotes(constraints, claims: dict[str, Claim]) -> str:
    """Each requirement with the ledger statements it cites and its stated assumption."""
    lines = []
    for c in constraints.constraints:
        lines += [f"{c.id}  ({c.type}, {c.sense})", "-" * _WIDTH]
        for claim_id in c.basis.evidence:
            claim = claims[claim_id]
            lines += textwrap.wrap(f"[{claim.tier}] {claim.id}: \"{claim.statement}\"", _WIDTH,
                                   initial_indent="  ", subsequent_indent="      ")
        lines += textwrap.wrap(f"assumption: {c.basis.assumption}", _WIDTH,
                               initial_indent="  ", subsequent_indent="      ")
        lines.append("")
    return "\n".join(lines).rstrip()


def lapse_table(inputs, conditions) -> str:
    """Installed thrust lapse alpha at (label, altitude_m, mach) conditions, on the mission's day."""
    dT = inputs.mission.dT_isa_K.value
    rows = [f"{'condition':22s}{'alt [m]':>9s}{'Mach':>7s}{'alpha':>8s}", "-" * 46]
    for label, h, mach in conditions:
        rows.append(f"{label:22s}{h:9.0f}{mach:7.2f}{inputs.lapse.alpha(inputs.atmosphere, h, mach, dT):8.3f}")
    return "\n".join(rows)


def design_constraint_table(dp) -> str:
    rows = [f"{'constraint':16s}{'sense':>13s}{'beta':>8s}{'alpha':>8s}{'T_SL/W_TO':>11s}", "-" * 56]
    for c in dp.constraints:
        mark = "  <- binds" if c.id == dp.binding_constraint else ""
        lapse = "-" if c.lapse is None else f"{c.lapse:.3f}"
        rows.append(f"{c.id:16s}{c.sense:>13s}{c.beta:8.4f}{lapse:>8s}{c.thrust_loading:11.3f}{mark}")
    return "\n".join(rows)


def weight_fraction_table(dp) -> str:
    """Segment weight fractions, in the manner of the lecture's mission table."""
    rows = [f"{'segment':14s}{'m_start [kg]':>13s}{'m_end/m_start':>14s}{'fuel [kg]':>10s}{'time [s]':>9s}{'dist [km]':>10s}", "-" * 70]
    for s in dp.mission.segments:
        rows.append(f"{s.id:14s}{s.mass_start_kg:13.3f}{s.weight_fraction:14.5f}{s.fuel_kg:10.3f}{s.duration_s:9.1f}{s.distance_m / 1000:10.1f}")
    m = dp.mission
    rows += ["-" * 70, f"{'mission':14s}{m.takeoff_mass_kg:13.3f}{m.segments[-1].mass_end_kg / m.takeoff_mass_kg:14.5f}{m.mission_fuel_kg:10.3f}",
             f"reserve {m.reserve_fraction:.0%}: {m.reserve_fuel_kg:.3f} kg; fuel loaded {m.total_fuel_kg:.3f} kg"]
    return "\n".join(rows)
