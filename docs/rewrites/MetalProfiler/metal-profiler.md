<!-- rewrite-status: seed -->
# Metal Profiler

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md"><code>tech_reports/MetalProfiler/metal-profiler.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/MetalProfiler/metal-profiler.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 350 |
| Section headings | 41 |
| Fenced code examples | 33 |
| Markdown images | 0 |

### Section outline

- Quick Links
- Introduction
- Things built from Tracy that are needed in tt-metal
  - tracy-client
  - tracy-capture
  - tracy-profiler
  - tracy-csvexport
- Basic Tracy Application
  - 1. Add Tracy
  - 2. Build tracy-client
  - 3. Add Tracy includes
  - 4. Define compile options
  - 5. Insert macros
  - 6. Build tracy-capture
  - 7. Build tracy-csvexport
  - 8. Build tracy-profiler
- Developer Flow for using Tracy
  - 1. Start tracy-capture
  - 2. (Optional) Start tracy-profiler
  - 3. Start application
  - 4. (Only if did 1.) Feed .tracy into tracy-profiler
  - 5. (Only if did 1.) View .tracy contents
- Tracy Example
  - 1. Setup project directory structure
- … 17 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
