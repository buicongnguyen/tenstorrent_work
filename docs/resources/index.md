# External and ISA resource guide

The official `tt-metal` reports explain the programming stack. DeepWiki helps
map the changing codebase, while the Corsix series and official ISA material
make lower layers easier to study. These sources have different trust
properties and should not be blended silently.

![How the official and community sources relate](../assets/diagrams/source-map.svg){ .atlas-diagram }

<small>[Open full-size diagram](../assets/diagrams/source-map.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/source-map.mmd)</small>

## Choose the source for the question

| If you are asking… | Start with | Trust label |
|---|---|---|
| How do I build or optimize a TT-Metal/TT-NN operator? | [Pinned `tt-metal` reports](../reference/report-catalog.md) | Official · pinned |
| Which subsystem or source files should I inspect for a question? | [DeepWiki optimization research course](deepwiki-research-guide.md) | Discovery index · ten detailed lessons · verify |
| How do I diagnose and optimize a workload across layers? | [Performance optimization track](../start/optimization-path.md) | Atlas synthesis · source-linked |
| How does Wormhole appear experimentally from PCIe down to a T tile? | [Corsix Wormhole series](corsix-wormhole-series.md) | Community · verify |
| How should I actively study and question Corsix Parts 1–7? | [Seven-part Corsix guided course](corsix-reading-workbook.md) | Community · guided answers · verify against official |
| What exactly does an Unpacker, Packer, register, or instruction do? | [Tenstorrent ISA deep dive](isa-reference.md) | Official · living |
| How do I write at the low-level-kernel API? | [`tt-llk`](https://github.com/tenstorrent/tt-llk) | Official · living |

!!! info "Why Corsix is included"
    The series is unusually concrete and visually useful: it walks from a
    physical Wormhole board through NoC experiments, T-tile structure, the
    vector ISA, and matrix math. It is independent analysis, so treat measured
    values and inferred internals as hypotheses until official documentation,
    current source, or your own hardware confirms them.

!!! info "Why DeepWiki is included"
    DeepWiki is unusually useful for finding classes, tests, firmware, and
    subsystem relationships in a large repository. Its pages are generated and
    can be indexed at different commits, so the Atlas uses it for discovery—not
    authority. Record each page's own indexed commit, follow its source links,
    and compare the claim with official pinned and current material.

!!! warning "Architecture boundary"
    Wormhole B0 and Blackhole A0 share ideas but are not interchangeable. Mark
    every low-level note with its architecture, and do not transfer register
    layouts or instruction behavior without checking the matching directory.

## Comparison rule

Every Atlas rewrite links its original source at the top. When a chapter uses
one of these supporting sources, it also links the exact Corsix article or ISA
file—not merely the home page—so you can compare the explanation directly.

For a complete lower-layer route, use the
[Parts 1–7 guided course](corsix-reading-workbook.md). It places each article
inside Level 7 and pairs it with questions and official comparison sources.

For a complete performance route, use the
[optimization learning track](../start/optimization-path.md). For the research
method, mechanism-level investigations, answered architecture questions, and a
reusable source-ledger template, use the ten-lesson
[DeepWiki optimization research course](deepwiki-research-guide.md).
