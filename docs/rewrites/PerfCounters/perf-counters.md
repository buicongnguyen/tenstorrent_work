<!-- rewrite-status: seed -->
# Hardware Performance Counters

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md"><code>tech_reports/PerfCounters/perf-counters.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/PerfCounters/perf-counters.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1163 |
| Section headings | 27 |
| Fenced code examples | 49 |
| Markdown images | 0 |

### Section outline

- Quick Links
- Overview
- How It Works
  - How to Run
  - Environment Variable
  - Architecture Summary
- Derived Metrics Reference
  - Compute Utilization
  - Pipeline Efficiency
  - Thread Analysis
  - Pipeline Wait Metrics
  - Semaphore Waits
  - TDMA Stall Metrics
  - Instruction Availability Rates
  - Stall Breakdown
  - Write Port Analysis
  - Additional Idle Waits
  - L1 Memory Utilization
  - L1 Backpressure
  - L1 Composite Metrics
  - Additional Pipeline Metrics
- Hardware Register Reference
  - Control registers (`RISCV_DEBUG_REG_PERF_CNT_<X>0..2`)
  - Data registers
- … 3 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Choose counters only after stating a mechanism
   hypothesis—request/grant pressure, issue utilization, wait dependency, or another
   documented event—and define the exact core and interval the derived metric represents.

2. **Flow to make explicit.** Draw a hardware event increment through selected counter
   register, start/stop/reset lifecycle, RISC synchronization, readout, exported record, and
   formula such as request/reference or request/grant stall ratio.

3. **Invariant to prove.** Prove counter selection, width, reset, sampling window, core
   coverage, and formula use compatible events; account for overflow, unsupported selectors,
   and any multiplexing or instrumentation effect.

4. **TT-Metal evidence to connect.** Connect the workflow to `start_perf_counter()`,
   `stop_perf_counter()`, `wait_ncrisc_trisc()`, `read_perf_counters()`, `counter_sel`,
   `tt_perf_cnt`, and the report's derived expressions.

5. **Experiment and expected observation.** Create a baseline plus one controlled source of
   reader or arbitration pressure; expected result: the predicted counter/ratio changes in
   the measured interval and aligns with a matching timeline stall.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md):

- **Counter lifecycle.** `start_perf_counter()` and `stop_perf_counter()` delimit the
  measured device interval; `wait_ncrisc_trisc()` establishes that contributing
  processors reached the collection boundary before `read_perf_counters()` exports
  values.

- **Event interpretation.** `counter_sel` chooses the event and `tt_perf_cnt` stores the
  raw count used by the report's derived expressions. Check event availability, overflow
  width, processor scope, and normalization denominator before comparing kernels or
  architectures.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report explains how to configure and read hardware performance counters and turn
    raw event counts into metrics that answer whether a kernel is limited by compute
    issue, stalls, memory traffic, or another observable microarchitectural event.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Counters must be reset, enabled, sampled, and disabled around the intended region;
    event selection and derived formulas must match the same core and interval.
    Overflow, unsupported events, or multiplexing cannot be silently interpreted as real
    workload behavior.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A configured hardware event occurs during kernel execution → the corresponding
    register increments → runtime/profiler code snapshots the register → records are
    exported → a derived metric combines counts with cycles or operations → the result
    is correlated with the kernel timeline.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Register addresses, event selectors, counter widths, core
    coverage, reset behavior, and derived-metric definitions are architecture and
    firmware specific.

    **Durable model.** Start with a causal question, choose the smallest relevant event
    set, define the measurement window, account for overflow and observer effects, and
    combine counters with timelines and controlled experiments.

## Source and delta

- **Original source:** [`tech_reports/PerfCounters/perf-counters.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/PerfCounters/perf-counters.md`
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
