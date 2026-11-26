"""Console tables for the notebooks (ADR-0003): presentation only, no physics."""
from __future__ import annotations

import textwrap

from roadrunner_re.evidence import TIERS, Claim

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
