<!-- rewrite-status: improved-draft -->
# Matrix Multiply FLOPS

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md"><code>tech_reports/GEMM_FLOPS/GEMM_FLOPS.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define the precise GEMM roofline under test: M/N/K,
useful native lanes, fidelity, clock, cores, FLOP convention, residency, warm state, and
timed boundary. Do not compare application FLOPs with a microbenchmark denominator.

### How work and data move

The complete path is input tiles through reader/Unpack, matrix issue and K accumulation,
destination state, Pack/writer, device timing zone, CSV aggregation, and host
correctness check.

### What must never break

The non-negotiable invariant is that the benchmark executes the declared arithmetic
exactly once, excludes compile/setup from steady timing, synchronizes before stopping
measurement, and verifies output independently of the FLOP calculation.

### Where the report makes it concrete

The report makes the decision concrete by connecting evidence to
`TTNN_RUN_GEMM_FLOPS_BENCHMARK=1`, `test_matmul_2d_host_perf`,
`generated/matmul_benchmark_report.csv`, and configurations such as `tuned_2d_l1`,
`tuned_2d_dram`, and the architecture YAML.

### How the decision is tested

The controlled procedure is to run resident-input and DRAM-input variants at the same
shape/fidelity. **Expected observation:** resident data approaches the
phase/lane-adjusted compute ceiling, while a large gap only in DRAM mode identifies
movement or reader supply.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md):

- **Benchmark selection.** `TTNN_RUN_GEMM_FLOPS_BENCHMARK=1` enables
  `test_matmul_2d_host_perf`, whose named configurations such as `tuned_2d_l1` and
  `tuned_2d_dram` select different placement and program choices. Compare only rows with
  identical shape, dtype, fidelity, and architecture clocks.

- **Evidence artifact.** `generated/matmul_benchmark_report.csv` is the measurement
  record, while the architecture YAML supplies the peak-rate assumptions used for
  utilization. Recompute FLOPs and elapsed-time units from those two inputs rather than
  treating the reported percentage as a hardware constant.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report establishes a defensible GEMM throughput ceiling and a microbenchmark
    method that distinguishes matrix-engine issue capacity from losses due to shapes,
    data movement, synchronization, compilation, or profiling. It turns a vague “slow
    GEMM” claim into separable utilization hypotheses.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The FLOP count, dimensions, fidelity, clock assumption, iteration window, and timing
    boundaries must describe the same work, while output correctness is checked
    independently. Cold compilation and host setup must not be counted as steady-state
    device GEMM time.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Input tiles are read and unpacked → the matrix engine issues multiply-accumulate
    work across the K dimension → destination state accumulates → pack emits output
    tiles → a device profiler measures the steady kernel interval → host code converts
    the known operation count and elapsed time to FLOP/s.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Native matrix shape, clock, fidelity passes, destination
    capacity, per-core peak, and measured TFLOPS are generation- and
    configuration-specific.

    **Durable model.** State the arithmetic convention, build a compute-saturating
    microbenchmark, separate useful-lane utilization from hardware issue rate, validate
    results, warm the runtime, and compare observed throughput with a clearly derived
    roofline.

## Source and delta

- **Original source:** [`tech_reports/GEMM_FLOPS/GEMM_FLOPS.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
