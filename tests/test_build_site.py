"""The Pages site: notebooks listed in run order with their own titles, figures and handoffs included."""
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("markdown")
REPO = Path(__file__).resolve().parent.parent


def _build(tmp_path, order):
    rendered = tmp_path / "rendered"
    rendered.mkdir()
    for name in ("evidence_ledger", "mission_profile", "stray"):
        (rendered / f"{name}.html").write_text(f"<html>{name}</html>", encoding="utf-8")
    site = tmp_path / "site"
    env = {"NOTEBOOK_ORDER": order, "PATH": "/usr/bin:/bin"}
    subprocess.run([sys.executable, str(REPO / "scripts" / "build_site.py"), str(site), str(rendered)],
                   check=True, env=env, capture_output=True)
    return site


def test_index_lists_notebooks_in_run_order_with_their_titles(tmp_path):
    site = _build(tmp_path, "mission_profile evidence_ledger")
    index = (site / "index.html").read_text(encoding="utf-8")
    assert index.index("mission_profile.html") < index.index("evidence_ledger.html") < index.index("stray.html")
    assert "Mission Profile" in index and "Evidence Ledger" in index  # first heading of each notebook
    assert (site / "evidence_ledger.html").exists() and (site / "adr" / "index.html").exists()
    assert "shields.io" not in index  # README badges stay out of the lead


def test_index_carries_handoffs_and_figures(tmp_path):
    site = _build(tmp_path, "evidence_ledger mission_profile")
    assert (site / "out" / "evidence.yaml").exists()
    index = (site / "index.html").read_text(encoding="utf-8")
    assert 'href="out/evidence.yaml"' in index
    if list((REPO / "notebooks" / "figures").glob("*.png")):
        assert "<h2>Figures</h2>" in index

