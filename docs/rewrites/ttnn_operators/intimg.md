<!-- rewrite-status: improved-draft -->
# Tenstorrent `tt-metal`: Integral Image (Summed-Area Table) Kernels — High-Level Guide (Axis Spec: **[B, W, H, C]**)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md"><code>tech_reports/ttnn_operators/intimg.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define the integral-image recurrence and `[B, W, H,
C]` axis mapping, then assign tile/core wavefront work and the exact horizontal/vertical
prefix state that must cross every boundary.

### How work and data move

The complete path is `X[B=1,W,H,C]` tiles through reader initialization,
`cumsum_cube_axis_2`/`cumsum_cube_axis_3`, local scan, incoming edge-state addition,
output writer, feedback of row/column context, and dependent tile release.

### What must never break

The non-negotiable invariant is that each output equals the origin-to-position rectangle
sum and that boundary state belongs to the same batch/channel and immediately preceding
row/column tile; no dependent tile may read incomplete context.

### Where the report makes it concrete

The report makes the decision concrete by connecting the plan to
`ttnn.cumsum(ttnn.cumsum(x, dim=-2), dim=-3)`, `cumsum_cube_axis_2`,
`cumsum_cube_axis_3`, `column_block_i`, `row_chunk_i`, signals, CBs, and feedback
buffers.

### How the decision is tested

The controlled procedure is to use a small increasing-value tensor spanning multiple
tiles/cores and compare every boundary with a host summed-area table. **Expected observation:** exact recurrence and a timeline exposing whether wavefront waits or local
scan compute dominates.

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
