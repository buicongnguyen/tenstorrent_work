<!-- rewrite-status: seed -->
# Data Multicasting in [matmul_multicore_reuse_mcast]

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md"><code>tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 357 |
| Section headings | 7 |
| Fenced code examples | 25 |
| Markdown images | 0 |

### Section outline

- Additional Compile-Time Argument
- Configuring Core Ranges for Tile Distribution
- Circular Buffer Creation for CoreGrid
- Multicast Reader/Writer Kernel Setup
- New Compute Kernel: Fused Bias Addition and Activation Functions
- Semaphores
- Kernel Runtime Arguments

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    This stage removes redundant DRAM reads by having designated cores fetch a shared
    matmul operand once and multicast it to receiver cores, while retaining block reuse
    and optionally fusing bias/activation in the compute path.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every receiver must reserve the correct CB page and advertise readiness before
    multicast; all destinations must observe the same tile before compute consumes it,
    and the sender must not reuse its source page until the multicast protocol permits.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A source core reads an operand block from DRAM into its CB → receiver semaphores
    prove destination space is ready → one NoC multicast distributes the block across a
    core range → receivers publish local CB pages → compute combines them with each
    core's private operand/output block → writers store results.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Multicast rectangle rules, logical/physical coordinates,
    semaphore APIs, CB depths, block sizes, core roles, and fused-kernel arguments are
    TT-Metal and topology specific.

    **Durable model.** Read shared data once, fan it out near consumers, separate
    readiness from arrival, retain private data where it is reused, and include
    synchronization/fanout cost in the bandwidth saving.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
