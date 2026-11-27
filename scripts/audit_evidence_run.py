"""Audit the evidence notebook handoff and write its source manifest."""
import hashlib
import json
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from roadrunner_re.evidence import load_claims

# Reviewed SI names in the evidence handoff. New quantities need a unit review.
UNITS = {
    "length_overall_m": "m",
    "speed_max_m_s": "m/s",
    "takeoff_mass_kg": "kg",
}


def main():
    claims = load_claims()
    handoff = yaml.safe_load(Path("out/evidence.yaml").read_text(encoding="utf-8"))
    records = {}
    for claim in claims.values():
        urls = (claim.source, *claim.corroboration)
        for url in urls:
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError(f"{claim.id}: invalid source URL {url!r}")
        record = {
            "source": claim.source,
            "accessed": date.fromisoformat(claim.accessed).isoformat(),
            "corroboration": claim.corroboration,
        }
        if claim.is_quantified:
            unit = UNITS.get(claim.quantity)
            if unit is None:
                raise ValueError(f"{claim.id}: unreviewed quantity or unit {claim.quantity!r}")
            if handoff["quantities"][claim.quantity]["evidence"] != claim.id:
                raise ValueError(f"{claim.id}: handoff cites a different claim")
            record.update(quantity=claim.quantity, unit=unit)
        records[claim.id] = record

    inputs = [Path("notebooks/01_evidence_ledger.ipynb"), *sorted(Path("config/evidence").glob("*.yaml"))]
    manifest = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "python": platform.python_version(),
        "sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
        "claims": records,
    }
    Path(sys.argv[1]).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
