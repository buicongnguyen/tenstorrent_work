<!-- rewrite-status: seed -->
# Matmul (Multi Core Optimized)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md"><code>tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 16 |
| Section headings | 1 |
| Fenced code examples | 1 |
| Markdown images | 0 |

### Section outline

- Building and Running the Examples

## Improvement plan

1. **Architecture pressure.** Start from disjoint C-output ownership across the core grid,
   then derive each core's A/B ranges, K reduction, data reuse, multicast group, buffer
   capacity, and edge/tail work.

2. **Flow to make explicit.** Draw host partition/runtime arguments through per-core
   readers, optional shared-operand multicast, compute K loop and partial sums, Pack/writer,
   non-overlapping output placement, and host recomposition/check.

3. **Invariant to prove.** Prove complete non-overlapping C coverage and full K accumulation
   for normal and edge cores; runtime arguments, CB sizes, multicast participants, and
   writer ranges must encode the same partition.

4. **TT-Metal evidence to connect.** Connect the overview to the concrete example build/run
   path and its reuse/multicast kernels, program configs, core-grid/runtime arguments, CB
   creation, and validation code rather than leaving only a conceptual matmul diagram.

5. **Experiment and expected observation.** Sweep core-grid shape for one matrix including a
   tail; expected result: throughput improves while per-core finish times remain balanced,
   then degrades when smaller shards or communication/tail imbalance dominate.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The examples build an optimized multi-core matmul by partitioning output work,
    controlling blocks, reusing operands, and multicasting shared data so compute scales
    without multiplying DRAM traffic by the number of cores.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The core partition must cover every output tile exactly once, while each output
    accumulates the complete K dimension. Runtime arguments, CB capacities, and writer
    ranges must agree with the same partition.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host tiles and partitions the output grid → runtime arguments assign A/B/output
    ranges to cores → readers fetch or multicast operand blocks → compute reuses blocks
    across output tiles and accumulates K → writers store each core's non-overlapping
    output region → host validation recomposes the matrix.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Core-grid shape, tile/block sizes, CB identifiers, multicast
    topology, kernel arguments, fidelity, and measured scaling are
    implementation-specific.

    **Durable model.** Partition from output ownership, derive input needs, keep hot
    operands local or shared once, overlap readers/compute/writers, and measure load
    balance plus memory traffic as core count grows.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
