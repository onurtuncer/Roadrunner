"""Notebook file names carry their position in the sequence (ADR-0034)."""
import json
import re
from pathlib import Path

import yaml

from roadrunner_re.notebook import handoff_header, notebook_file

REPO = Path(__file__).resolve().parent.parent


def _order() -> list[str]:
    workflow = yaml.safe_load((REPO / ".github" / "workflows" / "design-pipeline.yml").read_text(encoding="utf-8"))
    return workflow["env"]["NOTEBOOK_ORDER"].split()


def test_pipeline_order_is_the_numbered_files_in_prefix_order():
    order = _order()
    files = sorted(p.stem for p in (REPO / "notebooks").glob("*.ipynb"))
    assert order == files, "NOTEBOOK_ORDER and notebooks/*.ipynb disagree"
    assert [int(n[:2]) for n in order] == list(range(1, len(order) + 1))
    assert all(re.fullmatch(r"\d{2}_[a-z_]+", n) for n in order)


def test_title_states_the_same_position_as_the_prefix():
    total = len(_order())
    for name in _order():
        cells = json.loads((REPO / "notebooks" / f"{name}.ipynb").read_text(encoding="utf-8"))["cells"]
        first = "".join(cells[0]["source"])
        assert f"notebook {int(name[:2])} of {total}" in first, name


def test_logical_name_resolves_to_the_numbered_file():
    assert notebook_file("off_design") == "notebooks/10_off_design.ipynb"
    assert notebook_file("constraint_analysis") == "notebooks/11_constraint_analysis.ipynb"
    assert "notebooks/01_evidence_ledger.ipynb" in handoff_header("evidence_ledger")
