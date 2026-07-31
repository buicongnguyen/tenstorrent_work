# Learning path

The reports become much easier when studied by dependency rather than by
folder name. Use this order as a curriculum; jump ahead only when you can
explain the checkpoint for the current stage.

![Recommended TT-Metal learning sequence](../assets/diagrams/learning-path.svg){ .atlas-diagram }

<small>[Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/learning-path.mmd)</small>

## Stage 0 — orient yourself

**Goal:** distinguish TT-NN, TT-Metalium, host code, device kernels, and
hardware engines.

Read:

1. [Architecture mental model](architecture-mental-model.md)
2. Upstream `METALIUM_GUIDE.md`
3. Upstream `tech_reports/ttnn/ttnn.md`

Checkpoint: draw the host-to-device call path for one tensor operation without
looking at the diagram.

## Stage 1 — representation before execution

**Goal:** understand why a tensor's shape, tile layout, data format, memory
layout, and storage location are separate decisions.

Read:

1. [Improved: Tensor and memory layouts](../rewrites/tensor_layouts/tensor_layouts.md)
2. Upstream `data_formats/data_formats.md`
3. Upstream `tensor_sharding/tensor_sharding.md`
4. Upstream `memory/allocator.md`

Checkpoint: given a `[1, 4, 64, 96]` BF16 tensor, state its flattened 2D
shape, tile grid, tile count, and tile payload size before discussing where it
is stored.

## Stage 2 — movement and synchronization

**Goal:** follow pages and tiles across DRAM, L1, cores, and circular buffers.

Read:

1. `prog_examples/NoC_tile_transfer/NoC_tile_transfer.md`
2. `Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md`
3. `prog_examples/multicast/multicast.md`
4. `tensor_accessor/tensor_accessor.md`

Checkpoint: explain why an asynchronous NoC read needs both an address
calculation and a barrier, and why a circular buffer has reserve/push and
wait/pop pairs.

## Stage 3 — write and reason about kernels

**Goal:** separate data-movement work from compute work and identify compile-
time versus runtime configuration.

Read:

1. `prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md`
2. `matrix_engine/matrix_engine.md`
3. `NamedKernelArgs/kernel_args_as_parameters.md`
4. `code-indexing/kernel-code-indexing.md`

Checkpoint: label every argument in a small kernel launch as host-only,
compile-time, or runtime.

## Stage 3½ — descend from kernels to the ISA

**Goal:** connect TT-Metal kernel behavior to TT-LLK and then to the units,
registers, and instructions described by the architecture ISA.

Use:

1. [Resource guide and trust labels](../resources/index.md)
2. [Corsix Wormhole series](../resources/corsix-wormhole-series.md), especially
   Parts 5–7 for the T tile, SFPU, and matrix engine
3. [Official ISA deep dive](../resources/isa-reference.md), beginning with the
   Tensix Tile and Coprocessor overviews before Unpackers and Packers

Checkpoint: trace one tile from L1 through Unpack → `SrcA`/`SrcB` → Matrix or
SFPU → `Dst` → Pack → L1, and identify which claims are architecture-specific.

!!! warning "Do not mix abstraction levels accidentally"
    TT-Metalium APIs are designed to hide many ISA details. Descend only when
    you are explaining behavior, debugging a lower-level kernel, validating a
    performance assumption, or learning the hardware itself.

## Stage 4 — measure before optimizing

**Goal:** connect Tracy traces and device-profiler measurements to a concrete
bottleneck.

Read:

1. `MetalProfiler/metal-profiler.md`
2. `PerfCounters/perf-counters.md`
3. `AdvancedPerformanceOptimizationsForModels/`
4. `GEMM_FLOPS/GEMM_FLOPS.md`

Checkpoint: decide whether a low-utilization operator is host-bound, dispatch-
bound, DRAM-bound, NoC-bound, or compute-bound, and name the evidence.

## Stage 5 — scale the same reasoning

**Goal:** extend ownership, addressing, routing, and synchronization from one
core to many devices and hosts.

Read:

1. `Programming_Mesh_of_Devices/`
2. `EthernetMultichip/BasicEthernetGuide.md`
3. `TT-Fabric/TT-Fabric-Architecture.md`
4. `TT-Distributed/TT-Distributed-Architecture-1219.md`

Checkpoint: distinguish scale-up from scale-out and explain which layer owns
routing in each example.

## How to use a report

For every report, make three passes:

1. **Map:** identify actors, memory locations, and boundaries.
2. **Trace:** follow one tile/page/message through the complete flow.
3. **Test:** locate the matching code and predict one observable result before
   running it.
