# 34. Notebook file names carry their position (amends ADR-0031)

Status: Accepted (2026-11-27)

## Context

ADR-0031 numbered the fifteen notebooks by position in their titles ("notebook N of 15") and
kept the number out of the file names. In a file browser and on the published site the
notebooks then sort alphabetically, not in run order. The owner wants the run order visible in
the file names.

## Decision

- Notebook files are `notebooks/NN_<name>.ipynb`, `NN` being the two-digit position of ADR-0031
  (`01_evidence_ledger.ipynb` to `15_design_summary.ipynb`). The rendered pages follow them
  (`10_off_design.html`).
- The **logical name** stays unnumbered (`off_design`): it is what handoffs record in their
  `notebook` field, what handoff files are named after (`out/off_design.yaml`) and what code and
  prose use. `roadrunner_re.notebook.notebook_file()` maps a logical name to its file;
  handoff headers are written through it.
- `NOTEBOOK_ORDER` in `design-pipeline.yml` lists the numbered names. A test checks that it equals
  the notebook files in prefix order, that the prefixes are 01 to N without gaps, and that each
  title states the same position as its prefix.
- The rest of ADR-0031 stands. Inserting a notebook means renumbering the files after it, the
  same renumbering ADR-0031 already implies for titles.

## Consequences

- Only the comment line at the top of each handoff changes; no handoff value moves.
- Links to the old site pages (`off_design.html`) break once; the index is regenerated and is
  the entry point.
- ADRs written before this one name notebooks without the prefix; read those names as logical
  names.
