<!-- rewrite-status: seed -->
# FlashAttention on Tenstorrent’s Wormhole Architecture

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md"><code>tech_reports/FlashAttention/FlashAttention.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/FlashAttention/FlashAttention.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 122 |
| Section headings | 11 |
| Fenced code examples | 0 |
| Markdown images | 1 |

### Section outline

- Abstract
- 1 Introduction
- 2 Background
  - 2.1 Algorithm
  - 2.2 Wormhole architecture
  - 2.3 TT-Metal Execution Model
- 3 Implementation Details
  - 3.1 Parallelization
  - 3.2 Asynchronous Execution and Pipelining
- 4 Performance Analysis
- 5 Future work

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The bottleneck is the quadratic memory traffic and storage created by materializing
    the full attention-score matrix. The implementation tiles the sequence and computes
    an exact, numerically stable softmax online so K/V blocks can be streamed through
    limited L1 while matrix units remain useful.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For every processed key block, the running maximum, normalization sum, and
    accumulated weighted value must represent all keys seen so far after rescaling into
    one common softmax frame. Masked entries must contribute neither probability mass
    nor output.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A query block is loaded and kept local → key and value blocks stream through
    circular buffers → QKᵀ produces a score tile → masking and the online maximum update
    rescale the old accumulator → exponentials update the running denominator and
    weighted-value numerator → the final normalized block is written.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Tile dimensions, L1 capacity, core partition, circular-buffer
    depths, math fidelity, Wormhole NoC behavior, and measured performance belong to the
    target implementation.

    **Durable model.** Use IO-aware tiling, fuse reductions with the consumer
    computation, maintain a stable online reduction state, double-buffer movement with
    compute, and choose parallelism from both capacity and reduction cost.

## Source and delta

- **Original source:** [`tech_reports/FlashAttention/FlashAttention.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/FlashAttention/FlashAttention.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
