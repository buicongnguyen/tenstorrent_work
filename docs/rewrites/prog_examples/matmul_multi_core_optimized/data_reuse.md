<!-- rewrite-status: improved-draft -->
# Data Reuse in [matmul_multicore_reuse]

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md"><code>tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned example organizes the K reduction inside each core's output region. Output
work is divided first into per-core regions and then into destination-register-sized
subblocks. A subblock is the unit of accumulation; circular buffer 24 preserves its
partial C state when destination registers must be reused before the next K block. The
design therefore pays explicit Pack/L1/reload traffic for partials while reusing each
A/B block across several output tiles and keeping the writer-visible stream final-only.
The report does not provide a naïve baseline or prove that partial-C traffic itself is
reduced, so that component must be measured rather than assumed.

`bmm_op_utils::get_large_matmul_params(Mt, Nt, num_cores_y, num_cores_x,
in0_block_w)` couples that hierarchy: it returns `per_core_M`, `per_core_N`,
`out_subblock_h`, and `out_subblock_w`. The provided `SUBBLOCK_HW_CHOICES` prefers
shapes such as 4x2, 2x4, 8x1, down to 1x1 because the destination-register footprint
must remain legal. Picking block width, grid, and subblock independently can produce a
partition that fits mathematically but cannot be buffered or accumulated efficiently.

### How work and data move

For each core, `reader_bmm_tile_layout.cpp` runs as `RISCV_1` and reads the A range
starting at `Kt * per_core_M * output_idx_y` and the B range starting at
`per_core_N * output_idx_x`. Strides encode the tiled row-major matrices: A advances by
`Kt` per tile row and `in0_block_w` per K block; B advances by `Nt` per tile row and
`in0_block_w * Nt` per K block. The reader therefore publishes exactly the
`in0_block_w * per_core_M` A tiles and `per_core_N * in0_block_w` B tiles needed for one
K slice. `writer_bmm_tile_layout.cpp` runs as `RISCV_0`; its start tile and subblock
strides place each core's final C subblocks without overlap.

`bmm_large_block_zm.cpp` consumes those streams. Its compile-time tuple fixes input
block sizes, subblock counts, `num_blocks`, output subblock dimensions, and batch. For
each destination tile, the nested `h`, `w`, and `inner_dim` loops call
`matmul_tiles(c_0, c_1, in0_index, in1_index, dst_index)` across `in0_block_w`. The index
increments reuse an A row across output columns and a B column across output rows before
the input CB pages are reclaimed.

If this is not the last K block, the kernel calls
`cb_reserve_back(tt::CBIndex::c_24, out_subblock_num_tiles)`, packs each partial with
`pack_tile`, then `cb_push_back` publishes it. On a later block, `enable_reload` causes
`cb_wait_front(c_24, ...)`, `copy_tile(c_24, i, i)` into destination registers, and
`cb_pop_front` only after the reload has ownership. New products accumulate into that
state. The final K block is packed to the output stream for the writer rather than
cycled through the intermediate CB again.

### What must never break

Every C tile must receive every K-block contribution exactly once and in the intended
batch. `num_blocks` must agree with `Kt / in0_block_w`; reader strides, compute indices,
and writer coordinates must describe the same tiling. A partial in `c_24` is not an
output: it cannot be consumed by the writer, overwritten before `cb_wait_front`, or
discarded before `copy_tile`. Conversely, the producer cannot push a partial until all
of its packed pages are complete. CB capacity and page size must cover
`out_subblock_num_tiles`, and the destination footprint implied by
`out_subblock_h * out_subblock_w` must be legal for the selected kernel.

### Where the report makes it concrete

The intermediate and final streams deliberately share one
`CircularBufferConfig` data-format map with output index `CBIndex::c_16` and
`interm0_cb_index = 24`, but they have different ownership lifetimes. The runtime
arguments expose the architectural decomposition rather than hiding it in a library op:
`per_core_M/N` define output ownership, `in0_block_w` defines reduction granularity,
`out_subblock_h/w` define register working set, and start/stride fields map them back to
global DRAM. This makes the optimization tunable, but also makes a mismatch a silent
data-placement bug rather than a type error.

### How the decision is tested

Use matrices whose tile coordinates are encoded in their values, including dimensions
that exercise multiple K blocks and batches. Compare the full C tensor against a host
reference, then inspect one core: number of input publications must equal `num_blocks`,
intermediate push/reload pairs must equal all non-final transitions, and the writer must
emit each owned output tile once. For performance, hold `Mt`, `Nt`, grid, and math
fidelity fixed while sweeping `in0_block_w` and legal subblock shapes. Record DRAM
bytes, CB wait time, reload/Pack activity, and the slowest core. More reuse should reduce
operand traffic per useful MAC; intermediate spill traffic can move in the opposite
direction as K-blocking and subblock shape change. Larger buffers can also constrain
double buffering, register subblocks can reduce occupancy, and uneven work can make the
tail core critical.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md):

- **Block configuration.** `get_large_matmul_params` chooses block sizes that drive
  `bmm_tile_layout.cpp` movement and `bmm_large_block_zm.cpp` compute. The chosen tiles
  must fit circular-buffer and destination capacity while covering M, N, and K exactly.

- **Ownership loop.** `cb_reserve_back`, producer writes, push, `cb_wait_front`,
  `pack_tile`, and pop form the reuse protocol; `interm0_cb_index` carries intermediate
  state. Match loop counts and release points so a block is retained for all intended
  reuse and reclaimed immediately afterward.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The optimization blocks matmul so each A or B block is reused for several output
    sub-blocks before eviction, increasing arithmetic intensity and reducing DRAM/NoC
    demand relative to rereading operands for every output tile.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For every output tile, all K blocks must be accumulated exactly once in the correct
    pairings; an intermediate destination/CB cannot be packed, overwritten, or exposed
    as final output before its K reduction is complete.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Readers load a block of A and B into circular buffers → compute iterates output
    sub-blocks that reuse one resident operand → partial sums remain in destination or an
    intermediate CB across K blocks → the final K step packs completed output tiles →
    writers commit them to memory.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Block dimensions, stride arguments, destination capacity, CB
    allocation, fidelity, tile shape, and optimal reuse direction depend on architecture
    and tensor shape.

    **Durable model.** Choose blocking from local capacity, maximize reuse before
    eviction, make the reduction lifetime explicit, balance reuse against parallelism,
    and verify that reduced reads—not only changed loop structure—appear in profiling.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
