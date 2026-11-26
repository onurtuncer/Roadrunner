# 22. Documentation on GitHub Pages (amends ADR-0014)

Status: Proposed (2026-11-26)

## Context

ADR-0014 says the design pipeline deploys rendered notebooks to GitHub
Pages. The owner wants the project *documentation* there, and the
project currently has no notebooks: what exists is the README and the
decision records. Students should be able to read both without
navigating the repository.

## Decision

- One GitHub Pages site, <https://onurtuncer.github.io/Roadrunner/>,
  deployed by GitHub Actions from `main` only.
- Contents: the README as the landing page, every ADR and the ADR
  index, and (once they exist) the executed notebooks rendered to HTML
  in pipeline order, with the design summary linked from the landing
  page.
- The site is built by `scripts/build_site.py`, a small script with one
  dependency (`markdown`). No documentation framework.
- The build runs on every pull request (so a broken page fails review)
  and deploys only on `main`. It lives in `design-pipeline.yml`, the
  only workflow allowed to deploy Pages.
- The main README carries status badges for `ci.yml` and
  `design-pipeline.yml` and a link to the site. Badges for release,
  Python version and DOI are added when those things exist.
- Nothing is written for the site only: it renders files that already
  live in the repo, so the repo and the site cannot disagree.

## Consequences

- Documentation is published from day one, before any code.
- The site is plain; if navigation or search becomes a real need, a
  framework is adopted by a later ADR.
- Pages must be set to deploy from GitHub Actions in the repository
  settings.
