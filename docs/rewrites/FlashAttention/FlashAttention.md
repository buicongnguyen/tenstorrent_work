<!-- rewrite-status: improved-draft -->
# FlashAttention on Tenstorrent’s Wormhole Architecture

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md"><code>tech_reports/FlashAttention/FlashAttention.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to quantify the score-matrix bytes avoided by tiled
online attention for the report's batch, head, sequence, and head-dimension regime, and
identify whether DRAM movement or matrix/SFPU compute is the expected ceiling.

### How work and data move

The complete path is one Q block held locally while K/V blocks stream through QKᵀ,
causal masking, running maximum, exponential sum, weighted-value rescaling, final
normalization, and output pack/write.

### What must never break

The non-negotiable invariant is that after every K block that running `(max, sum,
weighted value)` represents all unmasked keys seen so far in one numerical frame and
that the final result matches reference softmax attention within tolerance.

### Where the report makes it concrete

The report makes the decision concrete by connecting each phase to the report's
parallelization and asynchronous-pipeline sections, concrete tensor dimensions,
reader/compute/writer CBs, matrix operations, SFPU exponential/reduction, and output
storage.

### How the decision is tested

The controlled procedure is to compare materialized attention with the tiled online path
at increasing sequence length. **Expected observation:** score-intermediate external
bytes stop growing quadratically while correctness remains stable and kernel gaps reveal
the next limiting stage.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md):

- **Mathematical state.** The tiled algorithm carries a running row maximum, exponential
  rescale, denominator, and weighted-value numerator across key/value blocks. Tensor
  dimensions and masking determine which tiles may contribute; those state updates must
  match the stable-softmax recurrence.

- **Asynchronous pipeline.** Reader circular buffers bring Q/K/V tiles, matrix
  operations form scores and value products, SFPU work performs exponentials and
  reductions, and writer buffers store normalized output. The source's pipeline overlap
  is valid only when CB ownership and partial-state dependencies remain ordered.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
