# TT-Metal Learning Atlas

An unofficial, learner-first companion to Tenstorrent's
[`tt-metal`](https://github.com/tenstorrent/tt-metal) repository.

This repository has two deliberately separate layers:

- `upstream/tt-metal/` is an unchanged snapshot of the official
  `tech_reports/` collection plus `METALIUM_GUIDE.md`.
- `docs/` contains original explanations, learning paths, diagrams, and
  one-to-one rewrites that are easier to study.

It also indexes two complementary source classes without copying or presenting
them as equivalent:

- Tenstorrent's official `tt-isa-documentation` for work at or below TT-LLK;
- the independent Corsix Wormhole series as useful community field notes that
  must be cross-checked against official documentation and current code.

The separation matters: readers can always compare an explanation with the
official source, and upstream updates never silently overwrite learner notes.

## Current state

- 57 upstream Markdown reports copied at commit
  `992f3ca634aac8733c70e48da395aab5361b4166`
- 57 source-linked learner pages with architecture walkthroughs, concrete code
  boundaries, and 233 answered verification questions; no seed pages are public
- Eight source-grounded levels from models and runtime through memory, kernels,
  performance, distributed systems, TT-LLK, and ISA
- Architecture dependency, source-verification, and claim-review guides
- GitHub Pages-ready MkDocs Material site
- Automated link/content checks and deployment workflow
- Sidebar resource guides for the Corsix series and the official ISA hierarchy
- Static, offline SVG diagrams with versioned Mermaid source files

## Local preview

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000/tenstorrent_work/>.

## Validate

```powershell
python scripts/check_docs.py
mkdocs build --strict
```

## Guiding principle

Every improved report begins with a direct, commit-pinned **Original source**
link so the reader can compare both versions. It should then answer six
questions:

1. What problem does this feature solve?
2. Where does it sit in the TT software/hardware stack?
3. What data moves, from where, to where?
4. Which invariants must the programmer preserve?
5. Which performance trade-offs matter?
6. How can the reader verify the idea in code or on hardware?

See [CONTRIBUTING.md](CONTRIBUTING.md) before improving another report.

## Attribution and status

Tenstorrent's copied material remains attributed to Tenstorrent and is
included under the upstream Apache License 2.0. This project is independent,
unofficial, and is not endorsed by Tenstorrent. See
[`upstream/UPSTREAM.md`](upstream/UPSTREAM.md) for the exact source revision
and update policy.
