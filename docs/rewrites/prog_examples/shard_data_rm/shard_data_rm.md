<!-- rewrite-status: improved-draft -->
# Data Sharding (Multicore)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md"><code>tech_reports/prog_examples/shard_data_rm/shard_data_rm.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned example separates *logical elements* from *transport pages*. Its source tensor
has shape `(16,1)` and bfloat16 elements, but a DRAM page is one 4-byte `uint32_t`, so
each page carries two elements. Height sharding over four cores therefore assigns four
bfloat16 values—or two pages—to each core. The reader stages those pages from an
interleaved global buffer into a local CB with an L1-aligned stride. This is the smallest
case that exposes the architectural reason for sharding: convert a globally addressed
stream into explicit per-core ownership that later kernels can consume locally.

The mechanism is worthwhile only when that local ownership is reused. This report does
not include a downstream compute or gather kernel; it proves distribution and prints the
shards. Any performance claim about an end-to-end sharded operator therefore requires a
separate consumer measurement.

### How work and data move

The host creates values `{2,4,...,32}` and an interleaved DRAM buffer whose size is
`sizeof(uint32_t) * num_values / sizeof(bfloat16)` with a 4-byte page. CB `c_0` is
created on logical cores `{0,0}` through `{0,3}` with `Float16_b` format, two pages of
capacity per core, and a 4-byte page size. `TensorAccessorArgs(*src_buffer)` is appended
to the reader's compile-time arguments so the kernel's address calculation matches the
interleaved buffer configuration.

Per-core runtime arguments carry `src_addr`, `input_unit_size=4`, `shard_height=2`,
`shard_width_bytes=2`, the L1 `padded_offset_bytes`, `curr_idx_h`, and the core index.
Because `curr_idx_w` reaches `num_units_per_row` after every core assignment in this
one-column example, `curr_idx_h` advances by two pages: core 0 starts at page 0, then
cores 1, 2, and 3 start at pages 2, 4, and 6.

`reader_sharded_rm.cpp` constructs a `TensorAccessor`, reserves two pages with
`cb_reserve_back(c_0, shard_height)`, and obtains the local write pointer. For each page,
`s0.get_noc_addr(stick_id)` resolves its DRAM bank/address, `noc_async_read` transfers
four bytes, and the destination pointer advances by `padded_offset_bytes`, not merely
four. After both requests, `noc_async_read_barrier()` establishes data completion and
`cb_push_back(c_0, shard_height)` publishes the complete local shard. There is an
important defect in the report's displayed kernel, however: it dereferences the L1
destination for DPRINT immediately after each `noc_async_read`, before the read barrier.
That print is not ordered after DMA completion and can observe old or partially arrived
data. It expresses the intended diagnostic, but it is not valid proof of the transfer;
a corrected kernel must inspect the destination only after the barrier (or through a
consumer that waits on the pushed CB pages).

### What must never break

The four start-page ranges `[0,2)`, `[2,4)`, `[4,6)`, and `[6,8)` must cover every DRAM
page exactly once. Page size and `TensorAccessor` configuration must agree, while the L1
pointer must advance by allocator alignment so adjacent local pages do not alias. A core
cannot publish until both asynchronous reads finish, and a future consumer cannot pop
until it has consumed all two pages. Element count, page count, and byte count must never
be interchanged: `shard_height=2` here means pages, but each core owns four bfloat16
values. The same completion rule applies to diagnostics: reading the destination from
the issuing RISC before `noc_async_read_barrier()` is a race even if small transfers
usually arrive before DPRINT executes.

### Where the report makes it concrete

The numeric example makes the ownership auditable without a diagram. Core 0 should print
`2,4,6,8`; core 1 `10,12,14,16`; core 2 `18,20,22,24`; and core 3
`26,28,30,32`, modulo the raw bfloat16 representation, **only after** completion has
been established. The pinned pre-barrier DPRINT cannot guarantee those values. The
snippet also contains a naming inconsistency (`s0_args` is declared but `s1_args` is
passed to `TensorAccessor`); use it as architecture pseudocode unless the corresponding
pinned source file is checked for both the compiling symbol and corrected print order.

### How the decision is tested

Encode each element with its global index, capture each core's two page IDs, and
recompose the four shards on the host. Assert exact equality with the 16-element source,
no duplicates, and no gaps. Add canaries at each aligned L1 slot to detect a mistaken
4-byte pointer stride. Move the DPRINT loop after `noc_async_read_barrier()` (or add a
CB-waiting validation consumer) and stress repeated launches so the test cannot pass by
accidental short-transfer timing. Then attach a local consumer and compare repeated
interleaved reads with one shard stage plus N local reuses, measuring NoC bytes and CB
waits. The initial sharding cost is fixed; benefit should emerge only when downstream
reuse avoids enough remote traffic to pay for staging and any eventual recomposition.

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
