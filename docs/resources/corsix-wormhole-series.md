# Corsix Wormhole series

<p class="source-note">
<strong>Source class:</strong> community · verify ·
<strong>Original series index:</strong>
<a href="https://www.corsix.org/content/tt-wh-part8">Part 8: Reference</a>
</p>

Peter Cawley's series is a bottom-up tour of Wormhole based on code reading,
hardware experiments, and reasoned inference. It is excellent study material,
but it is not a substitute for Tenstorrent's maintained documentation.

The series belongs in **Level 7: Hardware, TT-LLK, and ISA**. Parts 1–4 build
the low-level system foundation; Parts 5–7 descend into the Tensix compute
pipeline. Part 4 also bridges to Level 6 because it studies multi-ASIC Ethernet
routing.

[Open the Parts 1–7 reading and questioning workbook →](corsix-reading-workbook.md){ .md-button .md-button--primary }

## Read in order

| Part | Original article | What to extract | Compare with |
|---:|---|---|---|
| 1 | [Physicalities](https://www.corsix.org/content/tt-wh-part1) | board, ASIC tile types, logical versus physical NoC placement | [Wormhole B0 overview](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0) |
| 2 | [Which disabled rows?](https://www.corsix.org/content/tt-wh-part2) | PCIe mappings, host TLB windows, harvesting discovery | [`tt-kmd`](https://github.com/tenstorrent/tt-kmd) and current device APIs |
| 3 | [NoC propagation delay](https://www.corsix.org/content/tt-wh-part3) | multicast experiment, tile counters, latency inference | [Wormhole NoC docs](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0/NoC) |
| 4 | [A touch of Ethernet](https://www.corsix.org/content/tt-wh-part4) | n300 multi-ASIC connectivity and routing | [`BasicEthernetGuide.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md) |
| 5 | [Taking apart T tiles](https://www.corsix.org/content/tt-wh-part5) | five Baby RISC-V cores, L1, Tensix front/back ends | [Tensix Tile overview](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0/TensixTile) |
| 6 | [Vector instruction set](https://www.corsix.org/content/tt-wh-part6) | SFPU state, lanes, flags, instruction families | [Tensix Coprocessor directory](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0/TensixTile/TensixCoprocessor) |
| 7 | [Bits of the MatMul](https://www.corsix.org/content/tt-wh-part7) | Unpack/Matrix/Pack data path, fidelity stages, throughput reasoning | [`MatrixUnit.md`](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md) |
| 8 | [Reference](https://www.corsix.org/content/tt-wh-part8) | bridge from the blog series to the comprehensive ISA repository | [`tt-isa-documentation`](https://github.com/tenstorrent/tt-isa-documentation) |

The pagination URL originally supplied—[`/content/page3`](https://www.corsix.org/content/page3)—contains
Parts 3–7 together. The table above uses stable per-article URLs so sidebar
links open exactly the chapter you intend.

## Recommended study rhythm

1. Read one original article and draw its actors, addresses, and data movement.
2. Answer that part's questions in the
   [workbook](corsix-reading-workbook.md) before reading a summary.
3. Classify important claims as official, observed, inferred, or open.
4. Compare with the exact official ISA/report links beside that part.
5. Record disagreements as architecture- and date-qualified research questions.

## A good first comparison exercise

For Part 7, make a three-column note:

1. what the article observes or infers;
2. what `tt-isa-documentation` specifies for Unpackers, Matrix Unit, and Packers;
3. what the pinned `tt-metal` `matrix_engine.md` exposes to software.

Any mismatch becomes a research question. First check architecture and source
date; then check current code; only then decide that one source is wrong.

