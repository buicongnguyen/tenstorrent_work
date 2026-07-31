<!-- rewrite-status: seed -->
# Tenstorrent `tt-metal`: Integral Image (Summed-Area Table) Kernels — High-Level Guide (Axis Spec: **[B, W, H, C]**)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md"><code>tech_reports/ttnn_operators/intimg.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn_operators/intimg.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 403 |
| Section headings | 29 |
| Fenced code examples | 9 |
| Markdown images | 0 |

### Section outline

- 0) TL;DR — mental model (with **[B, W, H, C]**)
- 1) What the kernel computes (the math)
- 2) Key vocabulary (TT-metal essentials)
- 3) Global tiling layout
- 4) Reader kernel — orchestrating input & initializing state
  - 4.1 Functions and intent
  - 4.2 Control flow
- 5) Compute kernel — turning tiles into an integral image
  - 5.1 W cumulative sum: `cumsum_cube_axis_2(...)`
  - 5.2 W propagation across blocks: `propagate_tile_into_cube(...)`
  - 5.3 H cumulative sum within tile: `cumsum_cube_axis_3(...)`
  - 5.4 H propagation (add from the upper block): `get_and_propagate_adder_cube(...)`
  - 5.5 Putting it together: `perform_intimg_along_row_chunk(...)`
- 6) Writer kernel — exporting results and feeding back vertical context
  - 6.1 Basic export: `output_block(...)`
  - 6.2 Import the upper block & broadcast last row (H propagation)
- 7) Axis mapping cheat-sheet (coherent with **[B, W, H, C]**)
- 8) Correctness sketch vs. classic formula (with **[1, W, H, C]**)
- 9) Performance & robustness notes
- 10) Walk‑through on a tiny example
- 11) Signals & buffers (by role)
- 12) Diagrams
  - a) 📐 What’s an Integral Image (toy 4×4)
  - b) ↕️↔️ Two-Pass View (cumsum over height then width)
- … 5 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Define the integral-image recurrence and `[B, W, H, C]` axis
   mapping, then assign tile/core wavefront work and the exact horizontal/vertical prefix
   state that must cross every boundary.

2. **Flow to make explicit.** Draw `X[B=1,W,H,C]` tiles through reader initialization,
   `cumsum_cube_axis_2`/`cumsum_cube_axis_3`, local scan, incoming edge-state addition,
   output writer, feedback of row/column context, and dependent tile release.

3. **Invariant to prove.** Prove each output equals the origin-to-position rectangle sum and
   that boundary state belongs to the same batch/channel and immediately preceding
   row/column tile; no dependent tile may read incomplete context.

4. **TT-Metal evidence to connect.** Connect the plan to `ttnn.cumsum(ttnn.cumsum(x,
   dim=-2), dim=-3)`, `cumsum_cube_axis_2`, `cumsum_cube_axis_3`, `column_block_i`,
   `row_chunk_i`, signals, CBs, and feedback buffers.

5. **Experiment and expected observation.** Use a small increasing-value tensor spanning
   multiple tiles/cores and compare every boundary with a host summed-area table; expected
   result: exact recurrence and a timeline exposing whether wavefront waits or local scan
   compute dominates.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
