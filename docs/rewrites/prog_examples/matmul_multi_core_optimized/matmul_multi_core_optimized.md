<!-- rewrite-status: improved-draft -->
# Matmul (Multi Core Optimized)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md"><code>tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

This pinned page is an index, not a complete kernel specification. Its architectural
claim is that multi-core matmul performance comes from explicit control of three
different costs: reuse of blocks within a core, multicast of blocks reused by multiple
cores, and eventually a multidimensional systolic organization. The first two are
implemented by the linked executables; the page labels the systolic-array step “coming
soon.” Treating that third item as implemented would go beyond the source.

The sequence is deliberate. Local reuse establishes how A/B blocks feed multiple output
tiles and how partial C subblocks spill/reload when registers must be reused. Multicast
then changes who fetches shared A/B blocks from DRAM and who receives them over the NoC.
Applying multicast
before establishing correct per-core C ownership and partial accumulation would make
communication look faster while leaving no reliable consumer contract.

### How work and data move

In `matmul_multi_core_reuse`, host partitioning assigns each core a C region, readers
bring its A and B K blocks into circular buffers, and the compute kernel accumulates a
destination-register-sized subblock. Non-final partials can be packed to an intermediate
CB and reloaded for the next K block; only the complete reduction reaches the output
writer. `matmul_multi_core_reuse_mcast` retains that local lifecycle but assigns the
left edge and top edge additional sender roles. A row-shared A block and column-shared B
block are fetched once at their origin and distributed to receivers before the same K
accumulation proceeds.

Thus the optimization boundary is not “matmul becomes distributed.” It is a change in
operand ownership around an unchanged mathematical contract: each output tile has one
writer and contains the complete dot product. The two build targets named by the report
are executable evidence for those separate mechanisms.

### What must never break

Across both stages, C ownership must be complete and non-overlapping, and every owner
must accumulate all K blocks exactly once. Reader start/stride arguments, CB page counts,
compute subblock dimensions, writer ranges, and—when enabled—multicast membership must
encode the same partition. A shared operand cannot be reclaimed before every required
receiver has acquired it, and a partial C tile cannot be exposed as final. Those
invariants matter more than the particular core grid because they survive a retuning of
block size or fanout.

### Where the report makes it concrete

The page's concrete scope is exactly two binaries:
`./build/programming_examples/matmul_multi_core_reuse` and
`./build/programming_examples/matmul_multi_core_reuse_mcast`. The linked reuse report
defines `get_large_matmul_params`, intermediate CB 24, and
`bmm_large_block_zm.cpp`; the multicast report defines four edge/interior dataflow roles,
semaphores, and `bmm_large_block_zm_fused_bias_activation.cpp`. Details beyond those
links—including the promised multidimensional systolic array—need another pinned source.

### How the decision is tested

Build and run both named examples with identical matrices and math configuration. First
prove output equivalence to a host matmul, including a case with multiple K blocks.
Then measure DRAM operand bytes, intermediate partial traffic, NoC bytes, and slowest-core
completion. Compare the reuse binary with a non-reuse baseline by traffic class; count
intermediate-C spills separately instead of assuming they fall with reused A/B reads.
The multicast binary should additionally reduce duplicated external reads while
increasing on-chip traffic and synchronization. Sweep grid aspect ratio and block width
separately. A speedup without matching byte/cycle evidence is not enough to identify
which mechanism caused it.

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
