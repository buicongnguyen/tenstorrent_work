<!-- rewrite-status: improved-draft -->
# Tensor Sharding

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_sharding/tensor_sharding.md"><code>tech_reports/tensor_sharding/tensor_sharding.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Interleaving pages round-robin across banks is general, but it gives no operator a
contiguous region to own. The pinned sharding API trades that generality for locality:
`HEIGHT_SHARDED` gives a core consecutive rows, `WIDTH_SHARDED` gives it consecutive
columns, and `BLOCK_SHARDED` maps rectangular height-width blocks one-to-one onto a
2-D core grid. Those are not interchangeable decorations. Height sharding fits
row-wise work because each shard spans the full tensor width; width sharding fits
column-wise work because each shard spans the collapsed height; block sharding exposes
parallelism on both axes but may require operand multicast or reduction across one grid
dimension. The experimental ND form exists because collapsing all leading dimensions
into height destroys useful batch/sequence/channel structure and because the number of
logical shards may exceed the number of banks.

### How work and data move

For the convenience API, a `ttnn.TensorSpec` fixes `shape`, `dtype`, `layout`, and
`buffer_type`, then `.height_sharded(core_ranges)`, `.width_sharded(core_ranges)`,
`.block_sharded(core_ranges)`, or `.sharded_across_dims(dims, core_ranges)` derives the
distribution. `ttnn.from_torch(..., spec=tensor_spec, device=device)` materializes the
logical tensor according to that contract. The advanced path constructs
`ttnn.MemoryConfig(layout, ttnn.BufferType.L1, ttnn.ShardSpec(...))`; `grid`,
`shard_shape`, and `ttnn.ShardOrientation.ROW_MAJOR` define which rectangular payload
each bank owns and in which core order. A consumer kernel reads its local shard and
communicates only for dependencies outside that region; a subsequent operator either
accepts the same `memory_config` or pays an explicit redistribution.

ND sharding keeps the original rank. For example,
`.sharded_across_dims([0, 1], core_ranges)` partitions batch and sequence but preserves
features, while `[2]` partitions only features. `NdShardSpec(shard_shape,
core_ranges)` can produce more shards than cores; the report maps those shards
round-robin, so a bank can own multiple disjoint ND regions. If an ND pattern is
equivalent to legacy height, width, or block sharding, the tensor retains the legacy
`TensorMemoryLayout`; `ND_SHARDED` is reserved for a distribution those 2-D forms
cannot express.

### What must never break

The logical tensor must be covered exactly once by the declared shards, while physical
padding must never become a logical element. In legacy 2-D forms, all leading
dimensions are collapsed into height: a height shard's width must equal tensor width,
and a width shard's height must equal collapsed height. For block sharding, core-grid
coordinates and `ShardOrientation` must agree with the block-to-bank mapping. For ND,
each `shard_shape` dimension and chosen split dimension must be compatible with the
logical shape, and every producer, accessor, kernel, and consumer must use the same
rank-preserving map. A tensor can allocate successfully yet still produce wrong output
if the next operator assumes a different core order or interprets multiple shards per
bank as one contiguous legacy shard.

### Where the report makes it concrete

The examples make capacity arithmetic inspectable. Shape `(2,128,256)` height-sharded
over eight cores yields `32 x 256` logical elements per core after batch and height are
collapsed. Shape `(1,64,512)` width-sharded over four cores yields `64 x 128`; a
`256 x 256` tensor block-sharded across a `4 x 4` grid yields `64 x 64`. The ND
`(4,4,4)` / `(2,2,2)` example creates eight shards for four banks, two per bank, while
`(4,4,3)` / `(2,2,3)` over three banks produces four shards and therefore an uneven
`2,1,1` ownership count. These examples expose both the benefit—local coherent
regions—and the tradeoff—load imbalance or a reshard when the next operation wants a
different partition.

### How the decision is tested

Construct tensors with unique coordinate-derived values, move them through each
`TensorSpec`, and compose them back to host order. Verify exact coverage, core
ownership, and boundary values for the concrete shard arithmetic above, including an
ND case with more shards than banks. Then test a complete producer-consumer chain under
two legal layouts. Measure local L1 bytes, cross-core bytes, explicit reshard bytes,
kernel time, and peak L1—not just the consumer kernel. The expected result is conditional:
a consumer-aligned shard layout should reduce remote movement enough to offset
materialization and any later redistribution. Because the source marks ND sharding
experimental and notes that some operations may not support it, unsupported consumers
must reject the configuration rather than silently flattening it into a different
legacy map.

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
