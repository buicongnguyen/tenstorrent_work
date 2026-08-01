<!-- rewrite-status: improved-draft -->
# Tenstorrent `tt-metal`: Integral Image (Summed-Area Table) Kernels — High-Level Guide (Axis Spec: **[B, W, H, C]**)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md"><code>tech_reports/ttnn_operators/intimg.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

An integral image is a two-dimensional inclusive scan, but the pinned kernel cannot hold
an entire `[B,W,H,C]` image in one core's L1. It decomposes the recurrence into local
tile scans plus two compact carries. Along W, the last prefix tile of a column block is
enough to seed the next block; along H, the last row of the already completed upper
block is enough to seed every row of the block below. This is why the architecture has
separate reader, compute, and writer roles and several SRAM circular buffers: retain
only boundary state while streaming bulk tiles. The implementation supports `B=1`,
splits C across cores as `core_y * cores_x + core_x`, and uses blocks of at most
`block_depth` tiles (the report's default is 32).

### How work and data move

For each `row_chunk_i` and `column_block_i`, the reader calls
`prepare_start_tile_for_cumsum_axis_2` to publish one zero tile in `cb_start`, computes
the edge depth as `min(remaining_W, ctas.block_depth)`, and `send_block`s input tiles to
`cb_input` in W order. `cumsum_cube_axis_2` repeatedly adds `cb_input` to `cb_start` or
the rolling `cb_acc`, publishes within-block results in `cb_cumsum_stage_0`, and saves
the final prefix in `cb_axis_2_buffer` when another block follows. For non-first blocks,
`propagate_tile_into_cube` adds that left carry to every current prefix and optionally
replaces it with the new final tile.

`cumsum_cube_axis_3` then applies `cumsum_tile()` top-to-bottom within each tile. For
later row chunks, the writer has already used `receive_upper_block` to reload the
previous chunk's output from DRAM into `cb_axis_3_buffer_0`; it calls
`broadcast_last_row_to_all_rows_in_cube` and publishes the result in
`cb_axis_3_buffer_1`. Compute's `get_and_propagate_adder_cube` adds that vertical carry
to the local H prefix and emits `cb_output`, which `output_block` writes using the same
`get_tile_id` mapping as the reader.

### What must never break

Every output must equal `sum(X[0,0:x+1,0:y+1,c])`. The W carry must be the globally
propagated final tile of the immediately preceding column block—not merely that block's
local sum. The H carry must be the final row of the fully written upper row chunk for
the same column block and channel. Reader and writer `get_tile_id` calculations must
agree. `cb_wait_front`/`cb_reserve_back` and the report's `ReadCBGuard`/`WriteCBGuard`
must prevent a carry from being popped before its last consumer or overwritten before
publication. Edge `block_depth`, numeric range, and the B=1 constraint are correctness
conditions; overflow can satisfy all synchronization invariants while corrupting the
summed-area table.

### Where the report makes it concrete

The CB names encode ownership: `cb_input` is reader-to-compute traffic; `cb_acc` is a
rolling W accumulator; stages 0/1/2 distinguish local W, propagated W, and local H;
`cb_axis_2_buffer` carries left state; `cb_axis_3_buffer_0/1` hold raw upper output and
its broadcast row; `cb_output` is writer-owned final data. `zero_buffer` obtains zeros
through a NoC read from `MEM_ZEROS_BASE`, avoiding scalar initialization. The extra
DRAM read by the writer for vertical feedback is the key tradeoff: it bounds L1 state
and enables streaming, but adds bandwidth and makes row chunks causally sequential.

### How the decision is tested

Use coordinate-coded data spanning a short edge block, at least two W blocks, two H row
chunks, and multiple channel cores. Compare every element with a wide-precision host
reference and inspect the first element after each W/H boundary; those locations isolate
the two carry paths. Poison each CB before use to reveal missing waits or zeroing, and
run the largest values allowed by each input/output format to expose overflow. Profile
CB occupancy, DRAM feedback bytes, and stalls separately. A valid optimization may
overlap reader/writer with compute, but cannot begin a dependent W block without
`cb_axis_2_buffer` or a dependent H chunk before the upper result has been written and
rebroadcast.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md):

- **Reference recurrence.** `ttnn.cumsum(ttnn.cumsum(x, dim=-2), dim=-3)` is the
  semantic oracle for the integral image. `cumsum_cube_axis_2` and `cumsum_cube_axis_3`
  implement the two dependent scan axes on tiled/device data.

- **Wavefront state.** `column_block_i`, `row_chunk_i`, signals, circular buffers, and
  feedback buffers carry prefix state across tile/core boundaries. Release a dependent
  block only after its row/column context is complete, then compare boundary elements
  with the host recurrence.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report implements a 2D integral image (summed-area table) on tiled Tensix data.
    Parallel prefix computation must carry horizontal and vertical context across
    tile/core boundaries while respecting the stated `[B, W, H, C]` axis convention.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For every logical position, output must equal the sum of all input values in the
    rectangle from the origin through that position. Prefix state crossing a tile
    boundary must represent exactly the last completed row/column for the same
    batch/channel, not a neighboring tile's state.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The reader loads an input tile and initializes horizontal/vertical context → compute
    performs an in-tile prefix scan and adds incoming boundary state → the writer stores
    the completed output tile → it also feeds the required edge values into
    state/signals for the next horizontal or vertical tile → dependent tiles proceed.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Axis mapping, tile traversal, CB/semaphore IDs, core
    assignment, feedback buffers, kernel code, and assumptions about tile size/layout
    are implementation-specific.

    **Durable model.** Model scans as a dependency graph, define the carried state
    mathematically, choose a wavefront/partition that respects dependencies, separate
    payload from boundary metadata, and test tile/cross-core boundaries with small
    hand-computable inputs.

## Source and delta

- **Original source:** [`tech_reports/ttnn_operators/intimg.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn_operators/intimg.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
