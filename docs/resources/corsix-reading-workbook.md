# Corsix Wormhole Parts 1–7 reading workbook

<p class="source-note">
<strong>Source class:</strong> community analysis · verify · Wormhole-specific ·
<strong>Series pagination supplied by the user:</strong>
<a href="https://www.corsix.org/content/page3"><code>corsix.org/content/page3</code></a>
</p>

This workbook turns Peter Cawley's Wormhole series into an active lower-layer
curriculum. Read the original article first, answer the questions without
copying its wording, and then compare every important claim with official
documentation or current source.

!!! warning "Analysis is not specification"
    The articles combine public sources, hardware experiments, and reasoned
    inference. They are unusually useful for building a mental model, but they
    are not maintained Tenstorrent specifications. Record whether each claim
    is **official**, **observed**, **inferred**, or still **open**.

!!! danger "Do not begin by reproducing the hardware-poking experiments"
    Parts 2–4 deliberately bypass normal software layers and interact with
    drivers, PCIe mappings, firmware queues, reset state, and device address
    spaces. Study the address and evidence flow first. Reproduce an experiment
    only on hardware you control, with current documentation and a recovery
    plan.

## Where the series fits

| Reading block | Lower-layer focus | Atlas connection |
|---|---|---|
| Parts 1–2 | board → ASIC → tile grid → PCIe window → NoC address | Level 7 foundation |
| Parts 3–4 | NoC timing and Ethernet/multi-ASIC experiments | Level 7, with a Level 6 distributed-systems bridge |
| Part 5 | T-tile cores, instruction pipes, synchronization, and LLK shape | Level 7 hardware/TT-LLK core |
| Part 6 | SFPU/vector execution state and instruction families | Level 7 ISA deep dive |
| Part 7 | Unpack → Matrix/SFPU → Pack dataflow and fidelity | Level 7 compute pipeline |

Part 8 is a reference bridge rather than another narrative chapter. Use it
after this workbook through the [series map](corsix-wormhole-series.md) and
[official ISA route](isa-reference.md).

## Keep an evidence ledger

For every answer, record at least one row:

| Claim | Architecture | Evidence class | Exact source | Checked date or commit | Result |
|---|---|---|---|---|---|
| Example: data moves from L1 toward `SrcA` through an unpacker | Wormhole B0 | official | exact ISA file | date checked | confirmed / differs / open |

The goal is not to prove the article right or wrong as a whole. The goal is to
make each claim independently traceable.

## Part 1 — Physicalities

[Read the original article](https://www.corsix.org/content/tt-wh-part1)

### Read for

- the physical card, ASICs, GDDR6, PCIe, and Ethernet connections;
- ARC, DRAM, Ethernet, PCIe, and Tensix tile roles;
- logical NoC coordinates versus physical placement;
- harvested or disabled Tensix rows.

### Questions while reading

1. What is the difference between a board, an ASIC, and a tile?
2. Why can the host reach the first n300 ASIC directly but not the second?
3. Which diagram is logical, which is physical, and which view should normal
   software use?
4. Why do two directional NoCs exist, and what does wraparound mean?
5. Which numbers come from public product material, which come from code, and
   which appear to be the author's inference?
6. What does harvesting change for capacity, addressing, and DRAM adjacency?

### Verify after reading

- Compare the topology with the official
  [Wormhole B0 root](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0)
  and [NoC directory](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0/NoC).
- Redraw the path `host → PCIe → ASIC → NoC → Tensix tile` from memory.
- Mark every capacity or bandwidth number as Wormhole-specific until confirmed
  for another architecture.

## Part 2 — Which disabled rows?

[Read the original article](https://www.corsix.org/content/tt-wh-part2)

### Read for

- kernel-driver mappings and PCIe BARs;
- write-combining versus uncacheable host mappings;
- Tenstorrent “TLB” windows and NoC target selection;
- discovery of harvested rows from device-visible state.

### Questions while reading

1. Trace one host load or store through virtual memory, a PCIe mapping, the
   PCIe tile, a configured window, the NoC, and a tile-local address.
2. Why is this use of “TLB” different from a CPU translation lookaside buffer?
3. Which properties select unicast versus multicast, NoC 0 versus NoC 1, and
   the target address range?
4. Why does write-combining affect host behavior without changing how the
   device interprets the eventual PCIe transaction?
5. Which normal Tenstorrent software layers does the experiment bypass, and
   what safety or portability assumptions disappear as a result?
6. Does the observed disabled-row mask prove why a row was disabled?

### Verify after reading

- Compare the mapping structures and IOCTLs with current
  [`tt-kmd`](https://github.com/tenstorrent/tt-kmd) source.
- Find the current TT-Metalium code that configures host-to-NoC windows; note
  renamed fields or changed constants instead of forcing the article's names.
- Explain the address path on paper before considering any live device access.

## Part 3 — NoC propagation delay

[Read the original article](https://www.corsix.org/content/tt-wh-part3)

### Read for

- reset, multicast, tile-local cycle counters, and result collection;
- the difference between a measurement and the model inferred from it;
- request and response paths on the directional NoCs;
- correction for counters that did not start at exactly the same time.

### Questions while reading

1. What is the experiment's independent variable, measured value, and target
   quantity?
2. Why is multicast useful for launching the experiment but not sufficient for
   collecting per-tile results?
3. What assumptions connect the recorded counters to a per-hop latency?
4. Why can a raw result appear to reach a farther tile before a nearer tile?
5. For a read, which parts of the path occur twice?
6. Does the experiment isolate router propagation from injection, ejection,
   synchronization, and software overhead?

### Verify after reading

- Compare routing terminology with the official
  [Wormhole NoC documentation](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0/NoC).
- Connect the experiment to the learner
  [NoC tile-transfer chapter](../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md).
- Reproduce the latency derivation from the article's observations on paper;
  label every correction and assumption.

## Part 4 — A touch of Ethernet

[Read the original article](https://www.corsix.org/content/tt-wh-part4)

### Read for

- the host-to-second-ASIC path on an n300 board;
- Ethernet-tile firmware queues and request/response ownership;
- NoC, shelf, rack, and host addressing boundaries;
- forwarding between local NoC traffic and Ethernet traffic.

### Questions while reading

1. Trace a request from the host to a tile on the second ASIC and its response
   back to the host.
2. Who writes and who reads each submission/completion queue index?
3. What ordering or visibility mechanism prevents payload data from being
   observed after its queue index?
4. Which address fields select tile, ASIC, shelf, and rack?
5. Which behavior is documented in headers, which is observed from firmware,
   and which is inferred?
6. Where does this low-level mechanism meet the higher-level concepts of
   routing, transport, fabric, and collectives?

### Verify after reading

- Compare with the official pinned
  [Basic Ethernet guide](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md)
  and [TT-Fabric architecture](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md).
- Mark this chapter as a bridge to Atlas Level 6, not as a replacement for the
  maintained distributed runtime documentation.
- Draw queue ownership and request/response arrows separately.

## Part 5 — Taking apart T tiles

[Read the original article](https://www.corsix.org/content/tt-wh-part5)

### Read for

- the five Baby RISC-V cores and their conventional roles;
- RISC-V instructions versus separate Tensix instructions;
- instruction pipes, macro-op expansion, replay, and Tensix synchronization;
- L1, `SrcA`, `SrcB`, `Dst`, configuration state, and execution engines;
- the path from LLK initialization to runtime instruction issue.

### Questions while reading

1. Which work belongs to the BRISC/NCRISC cores and which to T0/T1/T2?
2. Why can RISC-V execution continue independently after issuing a Tensix
   instruction?
3. What does a macro-op or replay buffer save, and what state must be configured
   before it is useful?
4. What can stall an instruction pipe, and which synchronization state is
   shared between pipes?
5. Why are `L1`, `SrcA`, `SrcB`, and `Dst` not interchangeable kinds of memory?
6. Where does the article move from confident description into explicit
   uncertainty or best-guess language?
7. How does an LLK init/runtime split use the hardware mechanisms described?

### Verify after reading

- Compare with the official
  [Tensix Coprocessor overview](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/README.md),
  [MOP](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MOP.md), and
  [REPLAY](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/REPLAY.md) pages.
- Locate one mechanism first in [`tt-llk`](https://github.com/tenstorrent/tt-llk),
  then in a TT-Metalium compute-kernel API wrapper.
- Use the [kernel code-indexing chapter](../rewrites/code-indexing/kernel-code-indexing.md)
  to connect hardware nouns to current source symbols.

## Part 6 — Vector instruction set

[Read the original article](https://www.corsix.org/content/tt-wh-part6)

### Read for

- SFPU/vector registers, lanes, constants, flags, and the flag stack;
- movement between `Dst` and vector registers;
- instruction encodings, operand reuse, latency, and hazards;
- the boundary between raw hardware instructions and the SFPI toolchain.

### Questions while reading

1. Why can the vector unit operate on `Dst` but not directly on L1?
2. What is one vector register, how many lanes does it have, and when does a
   lane behave as integer versus floating-point state?
3. How do active flags and per-lane flags represent conditional execution?
4. Which instructions have read-after-write hazards, and who is responsible for
   inserting a delay on Wormhole?
5. Which instruction behaviors are architecture-specific and explicitly noted
   as different on Blackhole?
6. What abstraction does SFPI provide over the raw instruction set?
7. For one high-level operation such as `tanh`, which instruction families and
   data movements would you expect to participate?

### Verify after reading

- Start with official [`Dst` state](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Dst.md),
  [`SFPLOAD`](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/SFPLOAD.md), and
  [`SFPMAD`](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/SFPMAD.md).
- Find the corresponding SFPI intrinsic or compiler lowering for one raw
  instruction; record where names or semantics differ.
- Keep a separate Wormhole/Blackhole difference table.

## Part 7 — Bits of the MatMul

[Read the original article](https://www.corsix.org/content/tt-wh-part7)

### Read for

- the L1 → Unpack → `SrcA`/`SrcB` → Matrix → `Dst` → Pack → L1 path;
- primitive matrix shapes and composition into a 32×32 TT-Metal tile;
- floating-point decomposition and possible hardware simplifications;
- fidelity phases, data formats, throughput, and data-movement limits.

### Questions while reading

1. Why can the matrix unit not complete the L1-to-L1 operation by itself?
2. Which core conventionally drives Unpack, Matrix/SFPU, and Pack, and is that
   convention a hard hardware restriction?
3. How does the primitive matrix operation compose into work on a 32×32 tile?
4. Which precision work can occur in Unpack, Matrix, and Pack respectively?
5. Why do additional fidelity phases improve consumed mantissa precision while
   reducing peak operation rate?
6. Which advertised throughput result is used as a cross-check, and what
   alternative bottleneck could explain a mismatch?
7. Which statements are grounded in code or published specifications, and which
   are hypotheses about the internal implementation?

### Verify after reading

- Compare the complete path with official
  [Unpackers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/README.md),
  [Matrix Unit](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md), and
  [Packers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Packers/README.md) pages.
- Compare the software-facing view with the learner
  [Matrix engine chapter](../rewrites/matrix_engine/matrix_engine.md).
- Calculate the expected operation rate for one format/fidelity choice, then
  list every assumption required to scale it from one matrix unit to a board.

## Capstone — one tile, end to end

Without looking at a diagram, explain this sequence and attach an exact source
to every arrow:

`host tensor → PCIe → device address → NoC → L1 → Unpack → SrcA/SrcB → Matrix or SFPU → Dst → Pack → L1 → NoC → host`

Then answer:

1. Which arrows are visible at TT-NN, TT-Metalium, TT-LLK, and ISA level?
2. Which steps are data movement, compute, synchronization, or configuration?
3. Which steps change format or layout?
4. Which assumptions apply only to Wormhole B0?
5. Which three claims in your trace have the weakest evidence?
6. What code symbol, official page, simulator result, or safe hardware
   measurement would strengthen each weak claim?

Finish by checking the [official ISA deep dive](isa-reference.md). A complete
answer is not one that sounds certain; it is one that makes uncertainty visible
and provides the next verification step.
