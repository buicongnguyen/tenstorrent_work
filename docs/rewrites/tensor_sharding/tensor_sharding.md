<!-- rewrite-status: improved-draft -->
# Tensor Sharding

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_sharding/tensor_sharding.md"><code>tech_reports/tensor_sharding/tensor_sharding.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to choose sharding from the next consumer's output
ownership and input reuse, then specify logical/padded tensor, page layout, shard
shape/orientation, core order, L1 footprint, and reshard/halo requirements.

### How work and data move

The complete path is logical pages through `TensorMemoryLayout`/`ShardSpec` or
`NdShardSpec`, mapper/data movement, per-core L1 shard, local compute, cross-shard
dependency, and composition or next reshard.

### What must never break

The non-negotiable invariant is that shard regions cover the intended tensor without
unintended gaps/duplication and that allocation, TensorAccessor, reader, compute, and
writer interpret identical shape, orientation, padding, and core order.

### Where the report makes it concrete

The report makes the decision concrete by connecting 2D/ND cases to
`TensorMemoryLayout::INTERLEAVED`, `HEIGHT_SHARDED`, `WIDTH_SHARDED`, block layouts,
`ShardSpec`, `NdShardSpec`, and `memory_config`.

### How the decision is tested

The controlled procedure is to compare two legal shard orientations for one consumer
chain. **Expected observation:** the consumer-aligned choice reduces remote/reshard
bytes and wait time enough to justify L1 occupancy and shard-creation cost.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_sharding/tensor_sharding.md):

- **Layout choice.** `TensorMemoryLayout::INTERLEAVED`, `HEIGHT_SHARDED`,
  `WIDTH_SHARDED`, and block-sharded layouts select how pages map to cores/banks. Choose
  from the next consumer's ownership and reuse, not from tensor shape alone.

- **Shard description.** `ShardSpec`, `NdShardSpec`, and `memory_config` encode shard
  shape, orientation, core set, and storage. Allocation, TensorAccessor, reader,
  compute, and writer must interpret the same description; otherwise a legal allocation
  can still address the wrong logical region.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_sharding/tensor_sharding.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report explains 2D and experimental N-D sharding: map tensor regions/pages onto
    a core grid so kernels gain parallel local access, while choosing height, width, or
    block patterns that match downstream work.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The shard mapping must cover the intended logical tensor without gaps or unintended
    duplication; shard shape, core order/orientation, padded extent, and memory layout
    must be interpreted identically by allocation, data movement, and compute.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A logical tensor is converted to pages → a shard specification partitions the page
    grid → mapper/data movement assigns each shard to one core's L1 → local kernels
    consume their regions → collectives or resharding handle cross-shard dependencies →
    composition restores logical order if needed.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** `TensorMemoryLayout` values, ND-sharding support, core-grid
    syntax, shard orientation, valid shapes, and optimal layouts depend on TT-NN and
    hardware.

    **Durable model.** Partition from consumer access patterns, include padding and
    ownership in the physical contract, balance shard work/capacity, quantify
    resharding, and validate both per-shard contents and recomposed tensors.

## Source and delta

- **Original source:** [`tech_reports/tensor_sharding/tensor_sharding.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_sharding/tensor_sharding.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/tensor_sharding/tensor_sharding.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
