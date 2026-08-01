<!-- rewrite-status: improved-draft -->
# Matrix Multiply FLOPS

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md"><code>tech_reports/GEMM_FLOPS/GEMM_FLOPS.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

GEMM throughput is meaningful only relative to the hardware work actually available.
The pinned report starts from one matrix-engine issue:
`8x16 * 16x16 -> 8x16`, or `2*8*16*16 = 4096` FLOPs per cycle under its multiply-plus-add
convention. At 1 GHz that gives about 4 TFLOP/s per Wormhole engine; at 1.35 GHz about
5.4 TFLOP/s per Blackhole engine. Inputs shorter than the native eight rows still occupy
the same engine operation—a `1x16` left operand therefore realizes one eighth of the
useful throughput. Math fidelity adds another denominator: the report models LoFi,
HiFi2, and HiFi4 as progressively lower peak rates. A measured number without shape,
fidelity, active grid, clock, and useful-lane adjustment can thus appear fast while
leaving most issued work empty.

The benchmark separates compute supply from movement and host supply. `tuned_2d_l1`
keeps in0 and output L1-sharded, `tuned_2d_dram` uses DRAM-interleaved in0/output, and
`oob` accepts automatic selection. Trace replay removes repeated host dispatch work. The
three modes answer different architectural questions and should not be collapsed into
one peak claim.

### How work and data move

`test_matmul_2d_host_perf` sweeps M, K, N, datatype, fidelity, storage, grid, and trace.
Reader work supplies tiles from L1 or DRAM; Unpack feeds the two operands to the matrix
engine; Math accumulates over K; Pack returns destination state; and the writer commits
the output to the configured memory. Device profiling establishes kernel time, while
the host benchmark also sees dispatch and synchronization. The runner writes all modes
to `generated/matmul_benchmark_report.csv`, preserving both host- and device-based
utilization so the timing boundary remains explicit.

The useful arithmetic numerator is `2*M*K*N`. Its ceiling is not simply per-engine peak
times all physical cores: it must use the selected grid and fidelity and account for
native-lane occupancy. Comparing host time with device time then identifies dispatch
loss. Comparing L1 and DRAM storage at identical arithmetic identifies supply loss. The
source reports that a one-L1/one-DRAM arrangement often incurs only a single-digit
penalty, while DRAM-only small matrices suffer most; larger problems amortize fixed
costs and use bandwidth more effectively.

### What must never break

Every CSV row must preserve its M/K/N, grid, storage, datatype, fidelity, trace state,
and timing domain. The FLOP numerator must not include padded or idle engine lanes while
the ceiling assumes useful lanes, nor may compile/setup contaminate steady-state device
time. Output must be checked independently; high TFLOP/s with wrong accumulation is not
a result. Trace and non-trace must execute the same matmul and residency. A utilization
above 100%, or a device value inexplicably below host value for the same interval, is a
signal to audit denominator, clock, grid, or synchronization rather than celebrate.

### Where the report makes it concrete

The reproducible entry point is `tech_reports/GEMM_FLOPS/run_bench.sh`; direct execution
requires `TTNN_RUN_GEMM_FLOPS_BENCHMARK=1`,
`TT_METAL_PROFILER_MID_RUN_DUMP=1`, and `TT_METAL_DEVICE_PROFILER=1`. Manual tuning
varies packer-L1 accumulation, input/output sharding, residency, and fidelity. The pinned
plots report roughly 190 TFLOP/s for Wormhole and 580 TFLOP/s for Blackhole in their
best tested cases, with peak utilization of about 93% and 96% respectively. BFLOAT8_B
HiFi2 is reported 1.5–1.8x faster than BFLOAT16 HiFi4, and BFLOAT4_B LoFi 2–3.5x faster
without trace. These are measured snapshot results over the documented matrices, not a
promise for arbitrary shapes. Rectangularity and small M expose native-shape waste;
trace helps small problems most because host overhead is a larger fraction of runtime.

### How the decision is tested

Run the single benchmark and group rows by identical M/K/N, grid, datatype, and fidelity.
Within each group compare `oob`, `tuned_2d_l1`, and `tuned_2d_dram`, then trace versus
non-trace using both timing domains. Add one square matrix, one narrow-M matrix, and one
large DRAM-resident matrix. Expected signatures differ: narrow M lowers lane-adjusted
useful throughput, trace mainly closes host/device gaps for short kernels, and L1 versus
DRAM separates compute from reader bandwidth. Recalculate `2*M*K*N/time` from raw CSV
times and the fidelity/grid ceiling before accepting utilization. Correct output and
repeatable warm timings are required for every peak row.

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
