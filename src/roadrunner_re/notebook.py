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
    """Repo paths for a notebook; creates ``out/`` and the figure directory."""
    paths = NotebookPaths(REPO_ROOT, CONFIG_DIR, REPO_ROOT / "out", REPO_ROOT / "notebooks" / "figures")
    paths.out.mkdir(exist_ok=True)
    paths.figures.mkdir(parents=True, exist_ok=True)
    return paths
