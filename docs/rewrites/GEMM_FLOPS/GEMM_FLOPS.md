<!-- rewrite-status: seed -->
# Matrix Multiply FLOPS

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md"><code>tech_reports/GEMM_FLOPS/GEMM_FLOPS.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 927 |
| Section headings | 21 |
| Fenced code examples | 4 |
| Markdown images | 7 |

### Section outline

- Introduction
  - Running Benchmarks
- Design of Experiments
- MicroBenchmarks
  - Matrix Multiplication TFLOPS on Wormhole/Blackhole (WH/BH)
  - Manually Tuned Performance
    - Peak FLOPS
    - Performance scatter plot across all matrix sizes and configurations
    - Performance bar plot across all matrix sizes and configurations
  - Utilization
    - Utilization derivation formula
    - Utilization plot across all matrix sizes and configurations, based on the chip TFLOPS calculated per each Math Fidelity
  - Understanding Device Scaling: SRAM vs DRAM
  - Tracing
    - Tracing on P150
    - Tracing on N150
  - Rectangular Matrix
    - Rectangular Matrix on P150
    - Rectangular Matrix on N150
    - Out of Box Performance
  - All Data

## Improvement plan

1. **Architecture pressure.** Define the precise GEMM roofline under test: M/N/K, useful
   native lanes, fidelity, clock, cores, FLOP convention, residency, warm state, and timed
   boundary. Do not compare application FLOPs with a microbenchmark denominator.

2. **Flow to make explicit.** Draw input tiles through reader/Unpack, matrix issue and K
   accumulation, destination state, Pack/writer, device timing zone, CSV aggregation, and
   host correctness check.

3. **Invariant to prove.** Prove the benchmark executes the declared arithmetic exactly
   once, excludes compile/setup from steady timing, synchronizes before stopping
   measurement, and verifies output independently of the FLOP calculation.

4. **TT-Metal evidence to connect.** Connect evidence to `TTNN_RUN_GEMM_FLOPS_BENCHMARK=1`,
   `test_matmul_2d_host_perf`, `generated/matmul_benchmark_report.csv`, and configurations
   such as `tuned_2d_l1`, `tuned_2d_dram`, and the architecture YAML.

5. **Experiment and expected observation.** Run resident-input and DRAM-input variants at
   the same shape/fidelity; expected result: resident data approaches the
   phase/lane-adjusted compute ceiling, while a large gap only in DRAM mode identifies
   movement or reader supply.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
