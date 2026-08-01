<!-- rewrite-status: improved-draft -->
# Metal Profiler

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md"><code>tech_reports/MetalProfiler/metal-profiler.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define which latency terms require observation—host
construction, dispatch, device reader/compute/writer zones, NoC stalls, or
synchronization—and which clock domains must be correlated to establish causality.

### How work and data move

The complete path is instrumented events from host/device zone emission through per-RISC
buffers, runtime transfer/correlation, Tracy capture or CSV generation, and the final
critical-path interpretation.

### What must never break

The non-negotiable invariant is that every zone has paired start/end, stable
core/RISC/program identity, a known clock relationship, and identical instrumentation in
compared runs; profiling overhead must not be confused with workload cost.

### Where the report makes it concrete

The report makes the decision concrete by connecting setup to
`tt_metal/third_party/tracy/`, `./build_metal.sh`,
`build/tools/profiler/bin/tracy-capture`, the generated trace/output directories, and
the report's device-profiler integration flow.

### How the decision is tested

The controlled procedure is to profile a warm workload with one deliberate host sleep
and one reader delay. **Expected observation:** the correlated timeline separates the
host gap from device input starvation and attributes each to the inserted boundary.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md):

- **Instrumentation build.** The profiler path starts in `tt_metal/third_party/tracy/`
  and the options passed to `./build_metal.sh`; a binary built without the matching
  instrumentation cannot produce the expected host/device zones later.

- **Capture artifact.** `build/tools/profiler/bin/tracy-capture` collects the trace,
  while generated trace/output directories hold postprocessed device-profiler data.
  Record build, device clock, workload window, and capture file together so a timeline
  remains attributable and reproducible.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The profiler connects host-side submission and device-side execution so developers
    can tell whether latency comes from Python/C++, compilation, command dispatch,
    NoC/data-movement kernels, compute kernels, or synchronization rather than guessing
    from one wall-clock number.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every recorded zone must have a consistent clock domain, thread/core identity,
    start/end pairing, and workload configuration. Comparisons must use the same
    instrumentation because profiling consumes buffers and time and can perturb the
    schedule.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Instrumented host and device code emits timestamped zone events → device profiler
    buffers retain per-RISC records → the runtime transfers and correlates them with
    host events → Tracy/CSV processing reconstructs a timeline → the developer
    attributes gaps and overlaps to concrete producers and consumers.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Tracy integration, profiler macros, RISC buffers, timestamp
    synchronization, CSV fields, build flags, and supported devices evolve with
    TT-Metal.

    **Durable model.** Correlate host and accelerator timelines, preserve experiment
    controls, include profiler overhead, start from a bottleneck hypothesis, and confirm
    it with both duration and dependency evidence.

## Source and delta

- **Original source:** [`tech_reports/MetalProfiler/metal-profiler.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/MetalProfiler/metal-profiler.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
