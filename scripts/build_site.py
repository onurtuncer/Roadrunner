"""Build the GitHub Pages site in the tailsitter design-report format (ADR-0022, ADR-0028).

The site is a design report generated from the same list that runs the
pipeline:

* ``index.html``: the README's opening text, then the notebooks in run
  order (title taken from each notebook's first markdown heading, so the
  list cannot go stale), the figures the notebooks wrote, the YAML
  handoffs, and links to the decision records and the source.
* ``<notebook>.html``: each executed notebook, rendered, at the site root.
* ``out/*.yaml`` and ``img/*.png``: the handoffs and figures themselves.
* ``adr/``: the decision records. ``readme.html``: the full README.

The notebook order is read from the ``NOTEBOOK_ORDER`` environment
variable (the one the pipeline executes); without it, the rendered
notebooks are listed alphabetically.

Usage: python scripts/build_site.py SITE_DIR [RENDERED_NOTEBOOK_DIR]
"""
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/onurtuncer/Roadrunner"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 50rem;
         margin: 2.5rem auto; padding: 0 1rem; line-height: 1.6; }}
  nav {{ border-bottom: 1px solid #ccc; padding-bottom: .6rem; margin-bottom: 1.5rem; }}
  nav a {{ margin-right: 1.2rem; }}
  li {{ margin: .4rem 0; }}
  table {{ border-collapse: collapse; font-size: .92rem; }}
  th, td {{ border: 1px solid #ccc; padding: .3rem .6rem; text-align: left; }}
  th {{ background: #f0f2f5; }}
  pre {{ background: #f6f8fa; padding: .8rem; overflow-x: auto; }}
  code {{ background: #f6f8fa; }}
  img {{ max-width: 100%; border: 1px solid #ccc; border-radius: 6px; }}
  figure {{ margin: 1.2rem 0; }}
  figcaption {{ font-size: .85rem; color: #555; }}
</style>
</head>
<body>
<nav><a href="{root}index.html">Design report</a><a href="{root}adr/index.html">Decision records</a><a href="{root}readme.html">README</a><a href="{repo}">Source</a></nav>
{body}
</body>
</html>
"""


def _md(text: str, to_html: bool = True) -> str:
    # Links between markdown files must point at the rendered pages.
    text = re.sub(r"\]\(([^)#:]*?)README\.md\)", r"](\1index.html)", text)
    text = re.sub(r"\]\(([^)#:]+?)\.md\)", r"](\1.html)", text)
    return markdown.markdown(text, extensions=["tables", "fenced_code"]) if to_html else text


def render(src: Path, dst: Path, root: str) -> None:
    text = src.read_text(encoding="utf-8")
    first = text.lstrip().splitlines()[0].lstrip("# ").strip()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(PAGE.format(title=first, root=root, repo=REPO_URL, body=_md(text)), encoding="utf-8")


def notebook_title(name: str) -> str:
    """First markdown heading of a notebook; the file name if it has none."""
    path = REPO / "notebooks" / f"{name}.ipynb"
    if path.exists():
        for cell in json.loads(path.read_text(encoding="utf-8"))["cells"]:
            if cell["cell_type"] == "markdown":
                source = "".join(cell["source"]).strip()
                if source.startswith("#"):
                    return source.splitlines()[0].lstrip("#").strip()
    return name.replace("_", " ")


def readme_lead() -> tuple[str, str]:
    """README title and its opening text (up to the first second-level heading), without badges."""
    lines = (REPO / "README.md").read_text(encoding="utf-8").splitlines()
    title = lines[0].lstrip("# ").strip()
    lead = []
    for line in lines[1:]:
        if line.startswith("## "):
            break
        if line.startswith("[![") or line.startswith("**Documentation:**"):
            continue
        lead.append(line)
    return title, "\n".join(lead).strip()


def notebook_order(rendered: Path | None) -> list[str]:
    available = {p.stem for p in rendered.glob("*.html")} if rendered and rendered.is_dir() else set()
    ordered = os.environ.get("NOTEBOOK_ORDER", "").split()
    return [n for n in ordered if n in available] + sorted(available - set(ordered))


def build_index(site: Path, notebooks: list[str]) -> None:
    title, lead = readme_lead()
    parts = [f"<h1>{html.escape(title)}: Design Report</h1>", _md(lead),
             "<p>Generated end-to-end from <code>config/</code> by CI on every push to <code>main</code>.</p>"]

    if notebooks:
        items = "\n".join(f'  <li><a href="{n}.html">{html.escape(notebook_title(n))}</a></li>' for n in notebooks)
        parts.append(f"<h2>Design notebooks (run order)</h2>\n<ol>\n{items}\n</ol>")

    figures = sorted((REPO / "out" / "figures").glob("*.png"))
    if figures:
        (site / "img").mkdir(parents=True, exist_ok=True)
        shots = []
        for fig in figures:
            shutil.copy(fig, site / "img" / fig.name)
            caption = fig.stem.replace("_", " ")
            shots.append(f'<figure><a href="img/{fig.name}"><img src="img/{fig.name}" alt="{caption}"></a>'
                         f"<figcaption>{caption}</figcaption></figure>")
        parts.append("<h2>Figures</h2>\n" + "\n".join(shots))

    handoffs = sorted((REPO / "out").glob("*.yaml"))
    if handoffs:
        (site / "out").mkdir(parents=True, exist_ok=True)
        for h in handoffs:
            shutil.copy(h, site / "out" / h.name)
        links = "\n".join(f'  <li><a href="out/{h.name}">{h.name}</a></li>' for h in handoffs)
        parts.append(f"<h2>Handoffs</h2>\n<p>The YAML files the notebooks hand to each other.</p>\n<ul>\n{links}\n</ul>")

    parts.append(f'<h2>Decisions</h2>\n<p><a href="adr/index.html">Architecture decision records</a> ·'
                 f' <a href="{REPO_URL}">Source repository</a></p>')
    (site / "index.html").write_text(
        PAGE.format(title=f"{title}: Design Report", root="", repo=REPO_URL, body="\n".join(parts)), encoding="utf-8")


def main() -> None:
    site = Path(sys.argv[1])
    rendered = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    site.mkdir(parents=True, exist_ok=True)

    notebooks = notebook_order(rendered)
    for name in notebooks:
        shutil.copy(rendered / f"{name}.html", site / f"{name}.html")

    build_index(site, notebooks)
    render(REPO / "README.md", site / "readme.html", "")
    shutil.copy(REPO / "LICENSE", site / "LICENSE")  # the README links to it
    for src in sorted((REPO / "adr").glob("*.md")):
        name = "index.html" if src.name == "README.md" else src.with_suffix(".html").name
        render(src, site / "adr" / name, "../")
    print(f"site built in {site}: {len(list(site.rglob('*.html')))} pages, {len(notebooks)} notebooks")


if __name__ == "__main__":
    main()
