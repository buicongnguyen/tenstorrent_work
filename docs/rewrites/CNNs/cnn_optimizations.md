<!-- rewrite-status: seed -->
# CNN Bring-up & Optimization in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md"><code>tech_reports/CNNs/cnn_optimizations.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/CNNs/cnn_optimizations.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 205 |
| Section headings | 11 |
| Fenced code examples | 6 |
| Markdown images | 1 |

### Section outline

- Contents
- Overview
- Model Bring-up
- Optimizations
  - Grouped Convolutions
  - Convolution Performance Tuning
  - Tracing and Multiple CQs
  - Data Parallel
  - Optimizing data transfers
- Performance Analysis
- Troubleshooting, Debugging, Pitfalls

## Improvement plan

1. **Architecture pressure.** Identify the concrete CNN subgraphs where convolution,
   pooling, concat, residuals, or layout conversion dominate warm latency. Choose
   optimization scope at the producer-consumer chain, not at an isolated operator benchmark.

2. **Flow to make explicit.** Trace an activation through preprocessing,
   `ttnn.conv2d`/`ttnn.maxpool2d`, sharded L1 residency, residual or `ttnn.concat`,
   subsequent convolution, and post-processing, marking every tilize, reshard, deallocation,
   and host boundary.

3. **Invariant to prove.** Preserve reference shapes, padding, stride, groups, channel
   order, residual pairing, and numerical tolerance across every layout or
   convolution-config change; a faster tensor with different branch meaning is not valid.

4. **TT-Metal evidence to connect.** Connect each proposed optimization to `ttnn.conv2d`,
   `ttnn.maxpool2d`, `ttnn.concat`, the `B×H×W×C → 1×H×W×BC` transformations, sharded memory
   configs, and the model's concrete module tests.

5. **Experiment and expected observation.** A/B one subgraph with and without a conversion
   or resharing while holding input and output contracts fixed; expected result: the removed
   boundary reduces total subgraph bytes/latency without increasing downstream conversion
   cost or lowering PCC.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report addresses the full CNN path from numerical bring-up to throughput: map
    convolution-heavy modules into TT-NN, then remove layout conversions, DRAM traffic,
    under-filled core grids, and poorly chosen sharding or convolution configurations
    without losing model accuracy.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    At every optimization checkpoint, the TT-NN module must implement the same logical
    tensor transform as the reference model: shapes, padding, stride, channel order,
    residual branches, and output interpretation must agree within the chosen numerical
    tolerance.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    One activation enters preprocessing → is converted to the required TT-NN
    dtype/layout → is distributed or sharded to the cores that run convolution →
    intermediate activations remain in a consumer-friendly layout where possible → later
    modules consume them → post-processing restores the host-visible
    detection/classification result for comparison.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Concrete convolution configs, core grids, shard shapes, data
    types, program-cache behavior, and measured device numbers depend on the TT-Metal
    revision and target chip.

    **Durable model.** Bring up bottom-up against a golden model, profile before tuning,
    follow the next consumer when selecting layout, keep reusable data local, fuse
    avoidable boundaries, and re-check correctness after every performance change.

## Source and delta

- **Original source:** [`tech_reports/CNNs/cnn_optimizations.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/CNNs/cnn_optimizations.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
