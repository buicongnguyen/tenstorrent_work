# Contributing

Start with the [rewrite playbook](docs/contributing/rewrite-playbook.md).

Before opening a change:

```console
python scripts/build_catalog.py
python scripts/check_docs.py
mkdocs build --strict
```

Do not edit `upstream/tt-metal/` by hand. A source update must be a mechanical
snapshot replacement tied to one exact upstream commit.

