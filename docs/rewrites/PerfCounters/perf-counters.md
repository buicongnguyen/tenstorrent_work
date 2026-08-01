<!-- rewrite-status: improved-draft -->
# Hardware Performance Counters

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md"><code>tech_reports/PerfCounters/perf-counters.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned counter system is built to observe a pipeline without turning every internal
signal into a software-visible register. Each Tensix core groups events into five banks:
FPU, `TDMA_UNPACK`, `TDMA_PACK`, `INSTRN_THREAD`, and L1. The reusable RTL block
`tt_perf_cnt` records three compatible quantities for an event: cycles requested
(`req_cnt`), cycles granted/ready (`grant_cnt`), and elapsed cycles (`ref_cnt`). That
triplet supports two different questions. `req/ref` measures utilization or demand;
`(req-grant)/req` measures denied demand. A derived percentage is meaningful only after
choosing which question and signal semantics match the suspected bottleneck.

Software capture is intentionally staged across RISC roles. TRISC1 brackets the compute
interval because it owns the compute-kernel lifecycle. BRISC performs readout only after
NCRISC/TRISC completion because BRISC has the NoC access needed to flush profiler data
to DRAM; the report explicitly says TRISCs cannot perform that flush. This separation
keeps measurement synchronized with compute while assigning transport to a processor
that can actually export it.

### How work and data move

At kernel entry, TRISC1 calls `start_perf_counter()`. A rising start bit clears and
starts all enabled counters, so events within a bank accumulate concurrently rather than
being time-multiplexed during the measured interval. At exit, `stop_perf_counter()`
latches them. BRISC executes `wait_ncrisc_trisc()`, then `read_perf_counters()` walks
the selected counter groups and their `counter_sel` values. For every selector, software
must read both request and grant forms: control register
`RISCV_DEBUG_REG_PERF_CNT_<X>1` uses bits `[12:8]` for bank selection and bit `[16]` for
req versus grant; `<X>2` bits 0 and 1 are edge-triggered start and stop. The low output
register carries `ref_cnt`, while the high register carries the selected req/grant
count. `read_single_group()` polls a readback between mux writes and samples, because a
`volatile` access alone does not establish MMIO ordering on RISC-V.

Each value is packed into a 64-bit profiler marker in BRISC's profiler buffer. Before
groups after the first, `perf_counter_flush()` drains that buffer to DRAM so one group
cannot overrun or contaminate another. Host decoding reconstructs counter type, value,
and reference interval; `perf_counter_analysis.py` aggregates per-core operation data,
and `process_ops_logs.py` computes CSV metrics.

Capture scope is itself a hardware constraint. `TT_METAL_PROFILE_PERF_COUNTERS` is a
bitfield: FPU=1, PACK=2, UNPACK=4, L1_0=8, L1_1=16, INSTRN=32, with Blackhole-only
L1_2/3/4 at 64/128/256. All L1 groups share one `MUX_CTRL`, so only one L1 bank can be
selected in a run; the CLI's multi-bank request works by making multiple profiler runs
and merging them, not by observing all L1 mux positions simultaneously. The report's
broad value 47 therefore selects FPU, PACK, UNPACK, L1_0, and INSTRN without violating
that exclusion.

### What must never break

Every numerator and denominator in a metric must refer to the same core and compatible
start/stop interval. Request and grant names are not interchangeable: on Blackhole an
L1 unpacker grant may exceed its request because the signals have different semantics,
so the implementation suppresses the resulting backpressure value. A zero can mean the
workload did not exercise a live signal, not that the counter is dead; conversely,
hardwired and aliased signals are omitted from the architecture-specific arrays rather
than repaired after capture. Wormhole's four packer engines and Blackhole's
`PACK_COUNT=1` require different interpretations. Never compare two L1 banks as if they
were captured in one execution, or subtract counts from separately timed operations.

The counter lifecycle must also remain single-owner: start exactly once before work,
stop after the intended work, wait for participating RISCs, and do not overwrite or
flush a group before every marker is exported. Losing the MMIO readback fence can attach
a value to the previous selector while still producing plausible-looking numbers.

### Where the report makes it concrete

Use counter chains, not isolated percentages. If math is starved, high
`WAITING_FOR_SRCA_VALID/ref_cnt` should coincide with low math activity and evidence on
the unpack path. If math cannot release srcA, high overwrite-blocked rate
`(SRCA_WRITE_AVAILABLE-SRCA_WRITE_NOT_BLOCKED_OVR)/SRCA_WRITE_AVAILABLE` should agree
with source-register clear waits. If Pack is the consumer bottleneck,
`AVAILABLE_MATH/PACKER_BUSY` can exceed 100%, while destination-read backpressure
explains the blocked handoff. For L1, demand (`sum(req)/(8*ref)`) and contention
(`req-grant`) answer different questions; high unpacker-port backpressure is actionable
only when thread-0 stalls or low unpacker write efficiency show that it delays the
operation.

Architecture-specific filters prevent false precision. The report falls back from
`PACKER_DEST_READ_AVAILABLE/PACKER_BUSY` when `PACKER_BUSY` is zero, omits the Blackhole
math-destination stall metric when its supporting signal is zero for the entire op, and
derives inaccessible Blackhole `stall_cnt` as req minus grant. Those rules are part of
the measurement model, not cosmetic CSV cleanup.

### How the decision is tested

Begin with one causal hypothesis—compute saturation, source starvation, Pack
backpressure, semaphore wait, or NoC/L1 contention—and capture only the necessary
groups. Run a baseline and one controlled perturbation such as reducing input-buffer
readiness, increasing math fidelity, or adding producer/consumer pressure. Confirm that
raw req, grant, and ref counts change in the predicted direction before accepting a
derived metric. Cross-check with operation latency and a timeline: a large stall ratio
that does not lengthen or overlap the critical interval is correlation, not the cause.
Repeat per architecture and per core, retaining distributions so one slow core is not
hidden by aggregation. For multiple L1 mux positions, rerun an identical deterministic
workload and label the result as cross-run evidence. Finally, verify selector readback
and marker counts; malformed ordering or missing groups invalidates the analysis even
when the formulas execute successfully.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
