<!-- rewrite-status: improved-draft -->
# Data Sharding (Multicore)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md"><code>tech_reports/prog_examples/shard_data_rm/shard_data_rm.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define row-major page order, tensor/padded extents,
shard shape/orientation, core grid, per-core page range, and the downstream reuse that
justifies staging global pages into L1.

### How work and data move

The complete path is interleaved/global source pages through `MeshCommandQueue`,
`MeshWorkload`/`Program` runtime arguments, per-core NoC reads and
`padded_offset_bytes`, local shard ownership, downstream consumer or writer, and
recomposition.

### What must never break

The non-negotiable invariant is that shards cover each logical page once in promised
order, padded rows never alias real data, source bank/offset calculations match page
size, and recomposition restores the original tensor.

### Where the report makes it concrete

The report makes the decision concrete by connecting the example to `MeshCommandQueue`,
`mesh_device`, `Program`, `MeshWorkload`, the `(16, 1)` grid/shape data,
`padded_offset_bytes`, and its row-major `uint32_t` page handling.

### How the decision is tested

The controlled procedure is to compare repeated interleaved reads with one staging pass
plus multiple local consumers. **Expected observation:** staging pays off only when
avoided remote bytes exceed initial shard creation and later recomposition/reshard cost.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md):

- **Mesh launch.** `mesh_device`, `MeshCommandQueue`, `Program`, and `MeshWorkload` bind
  the example to a mesh execution context. The `(16, 1)` grid and shape metadata must
  agree with the workload's device/core mapping.

- **Row-major addressing.** The kernels handle row-major `uint32_t` pages and apply
  `padded_offset_bytes` when assigning shard storage. Trace first/last words for each
  shard through write, execution, and readback to prove padding is not mistaken for
  logical data.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The example distributes row-major tensor pages across several cores so later work
    can consume local L1 shards instead of repeatedly gathering an interleaved global
    buffer. Its task is both address mapping and ownership transfer.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The shard specification and per-core ranges must cover the logical tensor exactly
    once in the promised order. Page size, row stride, orientation, and writer
    reconstruction must agree so no row is skipped, duplicated, or assigned to the wrong
    core.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Row-major pages begin in an interleaved/global buffer → host runtime arguments
    assign page ranges to cores → readers calculate source bank/offset and move pages
    over NoC → each core fills its local shard → downstream work or writers consume
    those pages → optional recomposition restores logical order.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Core grid, shard shape/orientation, interleaving banks, page
    alignment, NoC coordinates, and buffer APIs depend on the example and architecture.

    **Durable model.** Define logical page order first, partition it deterministically,
    make placement metadata shared by producer and consumer, validate reconstruction,
    and choose sharding only when it improves the next consumer's locality.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/shard_data_rm/shard_data_rm.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
