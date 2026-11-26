"""Build the GitHub Pages site (ADR-0022).

Renders README.md to index.html and every adr/*.md to adr/*.html, and
copies any rendered notebooks found in the given directory.

Usage: python scripts/build_site.py SITE_DIR [RENDERED_NOTEBOOK_DIR]
"""
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
  table {{ border-collapse: collapse; font-size: .92rem; }}
  th, td {{ border: 1px solid #ccc; padding: .3rem .6rem; text-align: left; }}
  th {{ background: #f0f2f5; }}
  pre {{ background: #f6f8fa; padding: .8rem; overflow-x: auto; }}
  code {{ background: #f6f8fa; }}
</style>
</head>
<body>
<nav><a href="{root}index.html">Home</a><a href="{root}adr/index.html">Decision records</a>{nb_link}<a href="{repo}">Source</a></nav>
{body}
</body>
</html>
"""


def render(src: Path, dst: Path, root: str, nb_link: str) -> None:
    text = src.read_text(encoding="utf-8")
    # Links between markdown files must point at the rendered pages.
    text = re.sub(r"\]\(([^)#:]*?)README\.md\)", r"](\1index.html)", text)
    text = re.sub(r"\]\(([^)#:]+?)\.md\)", r"](\1.html)", text)
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    first = text.lstrip().splitlines()[0].lstrip("# ").strip()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(PAGE.format(title=first, root=root, repo=REPO_URL,
                               nb_link=nb_link, body=body), encoding="utf-8")


def main() -> None:
    site = Path(sys.argv[1])
    notebooks = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    pages = sorted(notebooks.glob("*.html")) if notebooks and notebooks.is_dir() else []

    nb_link = ""
    if pages:
        (site / "notebooks").mkdir(parents=True, exist_ok=True)
        for page in pages:
            shutil.copy(page, site / "notebooks" / page.name)
        items = "\n".join(f'<li><a href="{p.name}">{p.stem.replace("_", " ")}</a></li>' for p in pages)
        (site / "notebooks" / "index.html").write_text(
            PAGE.format(title="Notebooks", root="../", repo=REPO_URL,
                        nb_link='<a href="index.html">Notebooks</a>',
                        body=f"<h1>Notebooks</h1>\n<ul>\n{items}\n</ul>"), encoding="utf-8")
        nb_link = '<a href="{root}notebooks/index.html">Notebooks</a>'

    render(REPO / "README.md", site / "index.html", "", nb_link.format(root=""))
    shutil.copy(REPO / "LICENSE", site / "LICENSE")  # the README links to it
    for src in sorted((REPO / "adr").glob("*.md")):
        name = "index.html" if src.name == "README.md" else src.with_suffix(".html").name
        render(src, site / "adr" / name, "../", nb_link.format(root="../"))
    print(f"site built in {site}: {len(list(site.rglob('*.html')))} pages")


if __name__ == "__main__":
    main()
