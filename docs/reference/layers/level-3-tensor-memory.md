# Level 3 — Solve tensor representation and memory problems

<p class="source-note">
<strong>Source class:</strong> Atlas architecture synthesis ·
<strong>Report set:</strong>
<a href="../report-catalog.md#level-3-tensor-memory">Level 3 catalog</a> ·
<strong>Use this page for:</strong> predicting where every byte lives and how it is addressed
</p>

Level 3 turns a logical tensor into pages distributed across memory and cores.
An expert treats format, layout, buffer type, sharding, allocation, and address
generation as one design decision because each constrains the others.

![Tensor-to-address reasoning flow](../../assets/diagrams/layer3-memory-address-flow.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/layer3-memory-address-flow.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/layer3-memory-address-flow.mmd)</small>

## The architecture contract

For every tensor, be able to state:

- logical and padded shape;
- scalar format and bytes per tile/page;
- row-major or tiled physical layout;
- DRAM or L1 placement and allocation lifetime;
- interleaved or sharded distribution;
- mapping from logical coordinates to page ID, bank/core, and local address;
- producer/consumer agreement on all of the above.

A “tensor” is not just values and shape. Kernels consume a physical contract.

## Architecture reasoning loop

1. Start from the producer/consumer access pattern, not a favorite layout.
2. Quantify useful bytes, padding bytes, reuse count, and working-set size.
3. Choose tile/page shape and data format from engine compatibility and accuracy.
4. Choose DRAM/L1 and interleaved/sharded placement from capacity, locality,
   parallelism, and communication.
5. Derive the address formula for one representative element or tile.
6. Test edge shapes, bank/core balance, and lifetime overlap.
7. Measure bytes moved and stall time; revise the representation if movement,
   not compute, is limiting.

## Worked problem — choose a layout for multicore MatMul

### Step 1: identify reuse

For `C = A × B`, blocks of A are reused across output columns and blocks of B
across output rows. The chosen shard orientation should make the more valuable
reuse local or multicastable.

### Step 2: check capacity before locality

Compute bytes per tile, tiles per block, double-buffer space, circular-buffer
space, output accumulation, and other resident tensors. A theoretically ideal
shard that does not fit in L1 is not an implementation.

### Step 3: map work and ownership

Assign each output block to one core or core group. Then name who owns each A/B
block, which operands are read from DRAM, which are multicast, and where C is
packed. Avoid two cores writing the same output unless a reduction protocol is
explicit.

### Step 4: derive—not guess—the address path

`logical tile → shard coordinate → core/bank → page offset → byte address`

Test first, last, padded, and shard-boundary tiles. TensorAccessor should encode
the contract; it cannot repair an incorrect layout decision.

### Step 5: compare alternatives with a movement model

Estimate DRAM bytes, NoC bytes, multicast fanout, per-core work balance, and L1
footprint. Confirm with profiler data. Choose the representation that minimizes
the dominant scarce resource while meeting capacity and accuracy.

## Tradeoffs an architect tracks

| Choice | Gain | Cost |
|---|---|---|
| Tiled layout | aligns with matrix engines and tile kernels | padding and conversion for irregular shapes |
| Row-major layout | natural for host and some elementwise access | may require tilization before matrix work |
| Interleaved DRAM | spreads traffic across banks | repeated remote access and less explicit locality |
| L1 sharding | parallel ownership and local reuse | capacity pressure and redistribution cost |
| Lower-bit format | less storage and bandwidth | precision, range, and conversion behavior |
| Larger blocks | more reuse and fewer control operations | less load balance and higher L1 footprint |

## Questions and expert answers

### 1. Why are data format and layout separate decisions?

???+ note "Expert answer — reasoning"
    Data format defines how scalar values are encoded and therefore precision,
    range, and bytes. Layout defines how those encoded values are grouped and
    ordered physically. Two tensors can share bf16 yet use row-major versus
    tiled storage; the engines and address formulas see different contracts.
    Optimize format from accuracy/bandwidth and layout from access/engine shape,
    then account for conversion between choices.

### 2. When does sharding help rather than merely redistribute cost?

???+ note "Expert answer — reasoning"
    Sharding helps when consumers repeatedly access local data, parallel cores
    own disjoint useful work, and the cost of creating or redistributing shards
    is amortized. It hurts when operations require frequent cross-shard exchange,
    shards are imbalanced, or L1 pressure forces spills. Evaluate the entire
    producer–consumer chain; a locally fast operator can impose an expensive
    reshard on its neighbors.

### 3. How should an architect choose between DRAM and L1?

???+ note "Expert answer — reasoning"
    First satisfy capacity and lifetime. Then compare reuse: data read once may
    not justify staging, while data reused many times often should live close
    to compute. Include opportunity cost—L1 occupied by one tensor cannot
    double-buffer another. The optimal policy maximizes avoided external bytes
    per scarce L1 byte while keeping enough buffering to overlap stages.

### 4. Why can a correct address formula still perform badly?

???+ note "Expert answer — reasoning"
    Correctness only proves each logical page reaches the right bytes. The
    mapping may concentrate traffic on a bank, create noncontiguous bursts,
    force many small NoC transactions, or assign unequal pages per core. Add
    performance properties to the address proof: contiguity, bank balance,
    burst size, reuse, and per-core page count.

## Evidence checklist

- A table of logical shape, padded shape, format, layout, and placement.
- Exact L1/DRAM footprint including double buffers and padding.
- Address derivation for normal and boundary tiles.
- Per-core work and per-bank traffic balance.
- Bytes moved and conversion count across the whole operator chain.

## Continue

Read the improved [tensor/layout](../../rewrites/tensor_layouts/tensor_layouts.md),
[data-format](../../rewrites/data_formats/data_formats.md),
[allocator](../../rewrites/memory/allocator.md), and
[TensorAccessor](../../rewrites/tensor_accessor/tensor_accessor.md) guides.
Continue to [Level 4 — kernel dataflow reasoning](level-4-kernels-dataflow.md)
when the physical tensor contract is explicit.
