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

## Source and delta

- **Original source:** [`tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
