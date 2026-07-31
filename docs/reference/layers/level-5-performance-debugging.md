# Level 5 — Diagnose performance and correctness with evidence

<p class="source-note">
<strong>Source class:</strong> Atlas architecture synthesis ·
<strong>Report set:</strong>
<a href="../report-catalog.md#level-5-performance-debugging">Level 5 catalog</a> ·
<strong>Use this page for:</strong> turning a symptom into a falsifiable bottleneck hypothesis
</p>

Level 5 is a scientific loop, not a bag of optimization tricks. An expert
defines the metric, builds a bound, measures where time or bytes go, changes
one mechanism, and checks both performance and correctness again.

![Performance investigation flow](../../assets/diagrams/layer5-performance-investigation.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/layer5-performance-investigation.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/layer5-performance-investigation.mmd)</small>

## The architecture contract

Every performance claim must specify:

- workload, shapes, formats, architecture, clocks, and software commit;
- cold/warm/replay state and synchronization boundaries;
- latency or throughput scope—kernel, operation, subgraph, or request;
- theoretical or measured bound and its assumptions;
- profiler/counter evidence linking the change to the result;
- numerical/correctness check after the change.

Without this contract, a number is not reproducible evidence.

## Architecture reasoning loop

1. Define one end-to-end success metric and one correctness metric.
2. Establish bounds: PCIe bandwidth, DRAM/NoC bytes, compute FLOPs, and minimum
   launch/dispatch work.
3. Measure cold and steady state separately.
4. Partition time into host gaps, dispatch, movement, waits, compute, and sync.
5. Choose the dominant term and form at least one competing hypothesis.
6. Change one mechanism; predict which metric/counter should move.
7. Accept the optimization only when predicted evidence and end-to-end result
   agree without violating correctness.

## Worked problem — GEMM reaches only half the expected FLOP/s

### Step 1: challenge the denominator

Confirm logical M/N/K, operation count convention, fidelity phases, usable
cores, warm state, and timed interval. A wrong FLOP count can manufacture a
performance problem.

### Step 2: construct three ceilings

1. **Compute ceiling:** native engine rate adjusted for data format/fidelity.
2. **Memory ceiling:** available DRAM/NoC bandwidth divided by bytes per useful
   operation after measured reuse.
3. **Pipeline ceiling:** slowest reader, compute, or writer stage.

The achievable rate cannot exceed the smallest relevant ceiling.

### Step 3: distinguish symptoms

- Matrix active nearly continuously: compute/fidelity or operation shape is the
  ceiling.
- Matrix idle while input waits: memory, NoC, reader, layout, or imbalance.
- Device has gaps between programs: host dispatch, cache, trace, or queueing.
- Some cores finish early: partitioning or edge imbalance.

### Step 4: run one-variable experiments

Increase reuse without changing math, or replace input with resident data to
test movement. Hold dataflow constant and change fidelity to test compute.
Eliminate host gaps with trace to test dispatch. The response pattern selects
the correct architecture layer.

## Tradeoffs an architect tracks

| Optimization | Removes or hides | Risk |
|---|---|---|
| Program cache / trace | construction and host gaps | stale identity or replay constraints |
| More buffering/prefetch | movement latency | L1 pressure and lifetime hazards |
| More cores | wall-clock work per core | imbalance and communication |
| Lower format/fidelity | compute and movement cost | accuracy/special-value behavior |
| Fusion/reuse | intermediate bytes and dispatch | code/state complexity |
| Asynchronous overlap | serialized idle time | explicit ownership and harder debugging |

## Report-by-report architecture decisions

### Kernel debugging tips — why investigation follows causal boundaries

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md) ·
[learner analysis](../../rewrites/Debugging/Kernel_Debugging_Tips.md)

**Why this design exists.** A hang or wrong value can originate in host launch,
runtime arguments, NoC addresses, CB protocol, or compute. Random prints and
delays perturb timing without reducing that hypothesis space.

**Mechanism and benefit.** The report combines minimal reproductions with
TT-TRIAGE, Watcher, and scoped device printing. Investigation moves from launch
to producer to transport to consumer, checking one invariant at each boundary.
This localizes the first impossible state rather than the last visible symptom.

**Price and rejected shortcut.** Instrumentation consumes buffers/cycles and can
hide races. A large log is easier to produce than a causal explanation but is
harder to interpret and reproduce.

**Architect's evidence test.** Record the last completed iteration and blocking
primitive for every actor, identify the matching transition, and prove address,
count, ownership, and completion assumptions before changing timing.

### DEVICE_PRINT migration — why debugging output uses a defined transport

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md) ·
[learner analysis](../../rewrites/Debugging/DEVICE_PRINT_replaces_DPRINT.md)

**Why this design exists.** Device-side output crosses cores, RISCs, firmware,
buffers, and a host drain path. A legacy macro with inconsistent usage becomes a
maintenance and interpretation risk as architectures and tools evolve.

**Mechanism and benefit.** `DEVICE_PRINT` provides one supported diagnostic
interface and migration path, making producer identity, enablement, formatting,
and drain behavior explicit. A common transport improves tool compatibility and
lets deprecated behavior be removed coherently.

**Price and rejected shortcut.** Printing remains buffered, capacity-limited,
and perturbative; it is not a synchronization primitive. Keeping both interfaces
indefinitely appears compatible but doubles semantics and test surface.

**Architect's evidence test.** Scope to one core/RISC and hypothesis, verify the
record is drained before teardown, and repeat without printing. If correctness
depends on the print, the diagnostic changed the schedule rather than proving it.

### Kernel accuracy tips — why precision is budgeted by pipeline stage

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md) ·
[learner analysis](../../rewrites/op_kernel_dev/accuracy_tips/accuracy_tips.md)

**Why this design exists.** Error can enter during input quantization, unpack,
math fidelity, accumulation order/width, approximation, or output pack. Turning
every knob to maximum precision wastes performance and still does not identify
the sensitive boundary.

**Mechanism and benefit.** The design uses a precision ladder: compare the same
kernel while changing one format/fidelity/accumulation/pack decision at a time,
with a stable golden path and model-level tolerance. Precision is spent where it
changes the final accuracy metric.

**Price and rejected shortcut.** Controlled sweeps require adversarial inputs
and many configurations. PCC alone can hide localized large errors; maximum
precision everywhere avoids analysis but sacrifices bandwidth and throughput.

**Architect's evidence test.** Attribute error delta to one boundary, include
special values and cancellation, then report performance and task-level accuracy
together. Preserve identical operation semantics and padded lanes in the golden.

### Metal Profiler — why host and device time are correlated in one timeline

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md) ·
[learner analysis](../../rewrites/MetalProfiler/metal-profiler.md)

**Why this design exists.** Wall-clock latency cannot distinguish Python/host
construction, dispatch gaps, data-movement RISCs, compute, or synchronization.
Separate uncorrelated logs cannot establish which producer caused an idle period.

**Mechanism and benefit.** Tracy-backed host zones and device profiler records
are collected with core/RISC identity and correlated clocks, producing a causal
timeline across submission and kernel stages. The critical path and overlap are
visible rather than inferred from totals.

**Price and rejected shortcut.** Timestamps, buffers, transfers, and annotations
perturb execution and require clock-domain discipline. Summing independent kernel
durations is cheaper but loses gaps, overlap, and queue waits.

**Architect's evidence test.** Use identical profiler configuration on both A/B
runs, check zone pairing and clock alignment, and connect an end-to-end change to
the exact gap or stage predicted by the hypothesis.

### Real-time profiler — why events stream through callbacks

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/real_time_profiler/getting-started.md) ·
[learner analysis](../../rewrites/real_time_profiler/getting-started.md)

**Why this design exists.** Long-running services and interactive analysis
cannot wait for process exit to observe regressions, hangs, or phase changes.
The observation path must expose records while execution continues.

**Mechanism and benefit.** Structured events flow to a registered callback,
append-only JSON lines, or Tracy. Producers remain separate from analysis, so
external tools can consume telemetry incrementally and failures leave partial
evidence.

**Price and rejected shortcut.** Slow callbacks create backpressure, buffering
pressure, or dropped/perturbed records; concurrent arrival requires ordering and
flush rules. Synchronous analysis in the producer is simpler but contaminates
the workload being measured.

**Architect's evidence test.** Deliberately slow or fail the consumer, measure
producer impact, validate event source/timestamp ordering, and confirm all
accepted records are flushed before shutdown.

### Hardware performance counters — why raw events are tied to a causal question

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md) ·
[learner analysis](../../rewrites/PerfCounters/perf-counters.md)

**Why this design exists.** A timeline shows when a core is idle or active but
may not expose the underlying event—issue, stall, traffic, or hazard. Counters
provide mechanism-level evidence only when the event and measurement window are
well defined.

**Mechanism and benefit.** Hardware registers count selected events; runtime
sampling exports them and derives metrics using cycles/operations from the same
interval. This can discriminate hypotheses that produce similar elapsed time.

**Price and rejected shortcut.** Event selectors, widths, overflow, reset, and
meaning are architecture-specific, and a ratio can look precise while combining
incompatible windows. Reading many counters without a question invites false
correlation.

**Architect's evidence test.** Predict which counter changes and by how much,
reset and bracket the exact region, account for overflow/multiplexing, and pair
the result with a timeline plus a controlled perturbation.

### PCIe bandwidth — why host-side and device-side tests are separated

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md) ·
[learner analysis](../../rewrites/PCIe_bandwidth/PCIe_bandwidth.md)

**Why this design exists.** End-to-end transfer includes host memory, PCIe DMA,
device DRAM/L1 placement, NoC redistribution, synchronization, and API overhead.
One throughput number cannot identify which boundary limited it.

**Mechanism and benefit.** Host-side write/read shard tests measure application
transfer paths, while device-side NoC tests isolate redistribution after bytes
arrive. Direction and transfer-size sweeps expose startup- versus
bandwidth-dominated regimes.

**Price and rejected shortcut.** Results depend on host platform, negotiated
link, pinning, buffer placement, and synchronization. Timing an asynchronous API
return is easy but measures enqueue, not completed payload movement.

**Architect's evidence test.** Report payload bytes, direction, completion
boundary, link properties, placement, and correctness. Compare link ceiling,
host path, and device redistribution rather than assigning every shortfall to PCIe.

### Saturating DRAM bandwidth — why readers are distributed per bank

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md) ·
[learner analysis](../../rewrites/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md)

**Why this design exists.** Aggregate DRAM bandwidth comes from independent
banks/channels and enough outstanding transfers. A single reader/bank or short
serialized reads cannot exercise the device roofline.

**Mechanism and benefit.** Pages are placed across banks and reader kernels are
assigned to issue aligned asynchronous reads per bank into reserved L1/CB space.
Concurrent bursts expose bank parallelism and keep the NoC path supplied.

**Price and rejected shortcut.** More readers consume cores/L1, can create NoC
hotspots, and need balanced placement. Merely adding cores that target the same
bank increases contention, not bandwidth.

**Architect's evidence test.** Measure per-bank and aggregate rates, outstanding
depth, burst size, NoC routes, and compute wait. A resident-data control separates
memory supply from downstream consumption.

### GEMM FLOPS — why peak is derived from native work and fidelity

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md) ·
[learner analysis](../../rewrites/GEMM_FLOPS/GEMM_FLOPS.md)

**Why this design exists.** Marketing peak or logical FLOP counts can overstate
achievable work when matrix-native rows are under-filled, fidelity requires
multiple passes, or the timed region includes non-compute work.

**Mechanism and benefit.** The benchmark derives per-engine ceiling from native
MAC shape, clock, FLOP convention, and fidelity passes, then builds a warmed,
correct, compute-saturating experiment. Observed utilization has a defensible
denominator.

**Price and rejected shortcut.** A microbenchmark may keep operands resident and
hide application movement or shape tails. Dividing model FLOPs by wall time is
simple but cannot explain the loss.

**Architect's evidence test.** State M/N/K, useful native-lane fraction,
fidelity, active cores, warm interval, and output check. Compare compute,
memory, and reader/compute/writer ceilings before naming the bottleneck.

### Advanced model optimization — why runtime mechanisms are applied in dependency order

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md) ·
[learner analysis](../../rewrites/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md)

**Why this design exists.** Program cache, Fast Dispatch, Metal Trace, multiple
command queues, and non-blocking execution remove different overheads. Treating
them as interchangeable switches produces invalid benchmarks and hidden races.

**Mechanism and benefit.** Warm/cache programs first, use Fast Dispatch for
asynchronous command delivery, capture/replay stable sequences when host gaps
remain, and add queues/events only when I/O can overlap compute. Each mechanism
targets one boundary with explicit prerequisites.

**Price and rejected shortcut.** Trace stabilizes addresses/lifetimes; multiple
queues remove implicit order; async code needs a later completion boundary.
Enabling everything together prevents causal attribution and can make stale data
look like speedup.

**Architect's evidence test.** Run cold, warm, replay, one-queue, and two-queue
experiments with one change each. The timeline must show the predicted gap or
overlap change while kernel work and numerical output remain equivalent.

## Questions and expert answers

### 1. Why can a faster kernel fail to improve end-to-end latency?

???+ note "Expert answer — reasoning"
    Amdahl's law: only the optimized fraction shrinks. The operation may be
    dominated by conversions, host gaps, other kernels, synchronization, or
    data movement. The kernel speedup can also move the bottleneck to its
    reader/writer. Measure the same request/subgraph boundary before and after,
    then verify that the profiler shows the predicted critical-path reduction.

### 2. Why must cold, warm, and replay measurements be separate?

???+ note "Expert answer — reasoning"
    They execute different work. Cold includes construction/compile and initial
    allocation; warm can reuse cached programs; replay can remove repeated host
    submission gaps. Mixing them produces a number that describes no real path.
    Report each distribution and choose the one matching deployment behavior.

### 3. What proves that DRAM bandwidth is the bottleneck?

???+ note "Expert answer — reasoning"
    High measured bandwidth alone is insufficient. Show that compute waits for
    input, expected bytes match observed traffic, and an experiment reducing
    bytes or increasing reuse improves throughput proportionally. If a
    resident-data experiment does not help, the limit is likely elsewhere—NoC,
    reader issue, layout, compute, or synchronization.

### 4. Why are correctness bugs and performance bugs often the same architecture problem?

???+ note "Expert answer — reasoning"
    Optimizations change ordering, reuse, buffering, formats, and lifetimes—the
    same mechanisms that define correctness. A missing event can produce stale
    data or intermittent stalls; wrong buffer counts can hang or underutilize;
    lower fidelity can speed compute while violating accuracy. Therefore every
    performance experiment keeps a numerical oracle and stress-tests timing.

## Evidence checklist

- Reproducible workload and environment metadata.
- Cold/warm/replay distributions and tail latency.
- Compute, memory, and pipeline ceilings with assumptions.
- Timeline/counters supporting the chosen bottleneck.
- One-variable experiment with predicted and observed response.
- Correctness/accuracy result after optimization.

## Continue

Use profiler, hardware-counter, PCIe/DRAM bandwidth, GEMM FLOPS, and
[runtime optimization](../../rewrites/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md)
reports as complementary evidence tools. Branch to
[Level 6 — distributed reasoning](level-6-distributed-systems.md) for scale-out
or descend to [Level 7](level-7-hardware-isa.md) only when engine-level evidence
requires it.
