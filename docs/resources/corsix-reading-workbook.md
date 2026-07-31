# Corsix Wormhole Parts 1–7 guided course

<p class="source-note">
<strong>Source class:</strong> community analysis · verify · Wormhole-specific ·
<strong>Original series:</strong>
<a href="https://www.corsix.org/content/page3"><code>corsix.org/content/page3</code></a> ·
<strong>Course review:</strong> 2026-07-31
</p>

This course turns Peter Cawley's Wormhole series into seven short, connected
lessons. Each lesson keeps the original article beside the explanation, makes
the reasoning chain explicit, evaluates the design as an accelerator
architect would, and places a collapsible guided answer immediately after
every study question.

!!! warning "Analysis is not specification"
    The articles combine public sources, hardware experiments, code reading,
    and inference. Their mental models are valuable, but every page below
    distinguishes **official**, **observed**, **inferred**, and **open** claims.
    Architecture-sensitive facts must still be checked against the linked
    Tenstorrent documentation and current source.

!!! danger "Do not begin by reproducing the hardware-poking experiments"
    Parts 2–4 bypass normal software layers and touch drivers, PCIe mappings,
    firmware queues, reset state, and device address spaces. Study the flow
    and evidence first. Reproduce an experiment only on hardware you control,
    with current documentation and a recovery plan.

## Course map

| Part | Guided lesson | Main architecture question | Optimization lens |
|---:|---|---|---|
| 1 | [Physicalities](corsix-parts/part1-physicalities.md) | How do board, ASIC, tiles, and NoCs fit together? | locality, yield, topology abstraction |
| 2 | [Which disabled rows?](corsix-parts/part2-disabled-rows.md) | How does a host address become a tile-local access? | programmable windows, batching, portability |
| 3 | [NoC propagation delay](corsix-parts/part3-noc-latency.md) | How can an experiment separate observation from latency model? | hop count, route selection, measurement quality |
| 4 | [A touch of Ethernet](corsix-parts/part4-ethernet.md) | How does a request cross from PCIe-attached silicon to another ASIC? | single-writer queues, hierarchical routing, DMA |
| 5 | [Taking apart T tiles](corsix-parts/part5-tile-architecture.md) | Why combine small control cores with specialized execution engines? | overlap, instruction compression, configuration reuse |
| 6 | [Vector instruction set](corsix-parts/part6-vector-isa.md) | Why is a programmable vector engine placed beside the matrix path? | fusion, predication, LUT approximation, hazards |
| 7 | [Bits of the MatMul](corsix-parts/part7-matmul.md) | Why split movement, format conversion, matrix work, and packing? | pipeline balance, fidelity, roofline limits |

Parts 1–4 establish the system and communication substrate. Parts 5–7 zoom
into one Tensix tile and its compute pipeline. Part 4 also bridges to Atlas
Level 6 because it introduces multi-ASIC routing; Part 8 is a reference bridge
available through the [series map](corsix-wormhole-series.md).

## The reasoning method used on every page

1. **Observe:** What does the article measure, show in code, or take from a
   public source?
2. **Model:** What hidden structure would explain those observations?
3. **Identify the constraint:** Is the pressure latency, bandwidth, area,
   energy, yield, programmability, or correctness?
4. **Explain the choice:** Why is this mechanism a reasonable response to the
   constraint?
5. **Name the cost:** What complexity, precision, portability, or software
   burden did the choice introduce?
6. **Verify:** Which official page, current symbol, profiler result, or safe
   experiment can confirm or reject the model?

This is more useful than memorizing register names: it creates a transferable
method for evaluating another NPU.

## Keep an evidence ledger

For every answer, record at least one row:

| Claim | Architecture | Evidence class | Exact source | Checked date or commit | Result |
|---|---|---|---|---|---|
| Data reaches `SrcA` through an Unpacker | Wormhole B0 | official | exact ISA file | date checked | confirmed / differs / open |

The goal is not to prove the series right or wrong as a whole. Make each claim
independently traceable and record when a claim is only an architectural
interpretation.

## Capstone — one tile, end to end

After Part 7, explain this sequence without looking at a diagram and attach an
exact source to every arrow:

`host tensor → PCIe → device address → NoC → L1 → Unpack → SrcA/SrcB → Matrix or SFPU → Dst → Pack → L1 → NoC → host`

Then answer:

1. Which arrows are visible at TT-NN, TT-Metalium, TT-LLK, and ISA level?
2. Which steps are data movement, compute, synchronization, or configuration?
3. Which steps change format or layout?
4. Which assumptions apply only to Wormhole B0?
5. Which three claims have the weakest evidence, and what would strengthen
   each one?
6. Where would a profiler show the pipeline becoming movement-bound rather
   than compute-bound?

Finish with the [official ISA deep dive](isa-reference.md). A strong answer is
not one that sounds certain; it shows the evidence, uncertainty, and next
verification step.
