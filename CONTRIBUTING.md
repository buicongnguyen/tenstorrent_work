# Contributing to the TT-Metal Learning Atlas

Contributor workflow belongs in the repository, not in the published learning
curriculum. Preserve a one-to-one path from
`upstream/tt-metal/tech_reports/<path>.md` to `docs/rewrites/<path>.md` and keep
the upstream snapshot unchanged.

Before changing a learner page:

1. compare it with the commit-pinned original report;
2. keep every numeric claim within the report's architecture and revision scope;
3. distinguish durable ownership/dataflow reasoning from API, register, and
   device-specific details;
4. follow one concrete tensor, tile, command, packet, or instruction end to end;
5. verify named implementation symbols against the pinned source or an explicitly
   labeled living official source;
6. give every verification question an expanded answer and every experiment an
   expected observation;
7. ensure diagrams explain structure, flow, ordering, ownership, or a trade-off;
8. run `python scripts/check_docs.py`, `mkdocs build --strict`, and
   `python scripts/check_site.py`; and
9. review the rendered page in both themes.

Run the complete repository workflow before opening a change:

```console
python scripts/seed_rewrites.py
python scripts/build_catalog.py
python scripts/check_docs.py
mkdocs build --strict
python scripts/check_site.py
```

Do not edit `upstream/tt-metal/` by hand. A source update must be a mechanical
snapshot replacement tied to one exact upstream commit.

Use `improved-draft` when a source-grounded explanation has passed repository
logic and rendering checks but has not been reproduced on the stated hardware.
Use `improved` only when the page has also passed its architecture-sensitive
implementation or hardware verification. Do not promote a page merely because
its prose is complete.

The public
[architecture claim review](docs/contributing/rewrite-playbook.md) teaches the
reasoning behind this process without exposing repository status or editing
tasks as curriculum.
