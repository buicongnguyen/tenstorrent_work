<!-- rewrite-status: improved-draft -->
# Matmul (Multi Core Optimized)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md"><code>tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to start from disjoint C-output ownership across the
core grid, then derive each core's A/B ranges, K reduction, data reuse, multicast group,
buffer capacity, and edge/tail work.

### How work and data move

The complete path is host partition/runtime arguments through per-core readers, optional
shared-operand multicast, compute K loop and partial sums, Pack/writer, non-overlapping
output placement, and host recomposition/check.

### What must never break

The non-negotiable invariant is that complete non-overlapping C coverage and full K
accumulation for normal and edge cores; runtime arguments, CB sizes, multicast
participants, and writer ranges must encode the same partition.

### Where the report makes it concrete

The report makes the decision concrete by connecting the overview to the concrete
example build/run path and its reuse/multicast kernels, program configs,
core-grid/runtime arguments, CB creation, and validation code rather than leaving only a
conceptual matmul diagram.

### How the decision is tested

The controlled procedure is to sweep core-grid shape for one matrix including a tail.
**Expected observation:** throughput improves while per-core finish times remain
balanced, then degrades when smaller shards or communication/tail imbalance dominate.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md):

- **Host construction.** The example's program config, core grid, compile/runtime
  arguments, and circular-buffer allocation instantiate one concrete decomposition of M,
  N, and K. Review these alongside the build/run command so the documented kernel
  variant is the one actually executed.

- **Kernel composition.** Reuse kernels keep an operand local across multiple blocks;
  multicast kernels replace duplicate DRAM reads with one sender and many receivers.
  Validation code closes the chain by comparing the packed output with the same shapes,
  dtype, and accumulation assumptions.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
