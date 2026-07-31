# Provenance and update policy

## What was copied

The repository includes unchanged copies of:

- `tt-metal/tech_reports/`
- `tt-metal/METALIUM_GUIDE.md`

They came from official commit
[`992f3ca634aac8733c70e48da395aab5361b4166`](https://github.com/tenstorrent/tt-metal/tree/992f3ca634aac8733c70e48da395aab5361b4166)
dated 2026-07-31.

The snapshot contains 57 technical-report Markdown files plus their diagrams,
scripts, and media. `METALIUM_GUIDE.md` is tracked as an additional foundation
document.

## Why the source is not edited in place

![Upstream snapshot update workflow](../assets/diagrams/provenance-update.svg){ .atlas-diagram }

<small>[Open full-size diagram](../assets/diagrams/provenance-update.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/provenance-update.mmd)</small>

Editing copied files directly would make it hard to tell which statements are
official and which are interpretation. Instead:

- `upstream/` remains a source snapshot;
- `docs/rewrites/` holds one-to-one learner editions;
- synthesis pages may combine several reports but list their sources.

## Source classes and trust labels

| Label | Meaning | How this site uses it |
|---|---|---|
| **Official · pinned** | Tenstorrent material at an exact commit | basis for one-to-one rewrites and comparison links |
| **Official · living** | Tenstorrent documentation linked at `main` | low-level/ISA reference; re-check before relying on details |
| **Community · verify** | independent analysis such as Corsix | intuition and experiments; compare with official docs and code |
| **Atlas synthesis** | explanation written in this repository | teaching aid whose sources and added interpretation are explicit |

Every one-to-one learner rewrite must show its exact **Original source** link
at the top and repeat the comparison links in its **Source and delta** section.
The generated report catalog links every original report even when a rewrite
does not exist yet.

## Update checklist

1. Record the new upstream commit and date.
2. Replace the snapshot mechanically—never merge prose by hand.
3. Regenerate the manifest and catalog.
4. Diff every changed Markdown report.
5. Mark affected rewrites as `review-needed`.
6. Revalidate code symbols, diagrams, numbers, and architecture claims.
7. Build with `mkdocs build --strict`.

## Independence and trademarks

This is an unofficial educational companion. It is not affiliated with or
endorsed by Tenstorrent. Tenstorrent, TT-Metalium, TT-NN, Tensix, Wormhole,
Blackhole, and other names may be trademarks of their respective owners.
