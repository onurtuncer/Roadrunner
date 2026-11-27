"""Shared notebook prelude (ADR-0003): one call instead of a copied block."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from roadrunner_re.config import CONFIG_DIR, REPO_ROOT


@dataclass(frozen=True)
class NotebookPaths:
    repo: Path
    config: Path
    out: Path
    figures: Path


def nb_setup() -> NotebookPaths:
    """Repo paths for a notebook; creates ``out/`` and ``out/figures/`` (ADR-0035)."""
    paths = NotebookPaths(REPO_ROOT, CONFIG_DIR, REPO_ROOT / "out", REPO_ROOT / "out" / "figures")
    paths.out.mkdir(exist_ok=True)
    paths.figures.mkdir(parents=True, exist_ok=True)
    return paths


def notebook_file(name: str) -> str:
    """Repo-relative path of the notebook whose logical name is ``name``.

    Notebook files carry their position in the sequence as a two-digit
    prefix (``08_off_design.ipynb``, ADR-0034); handoffs, titles and code
    use the logical name (``off_design``) only, so a renumbering touches
    the file names and ``NOTEBOOK_ORDER`` and nothing else.
    """
    matches = sorted((REPO_ROOT / "notebooks").glob(f"[0-9][0-9]_{name}.ipynb"))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one notebooks/NN_{name}.ipynb, found {len(matches)}")
    return matches[0].relative_to(REPO_ROOT).as_posix()


def handoff_header(name: str) -> str:
    """First line of every ``out/`` handoff written by notebook ``name``."""
    return f"# Handoff of {notebook_file(name)}. Generated; do not edit (ADR-0001).\n"
