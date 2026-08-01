<!-- rewrite-status: improved-draft -->
# Metal Profiler

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md"><code>tech_reports/MetalProfiler/metal-profiler.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Profiling crosses two ownership domains. Host code constructs and dispatches work;
device kernels expose lower-level timing that must be correlated back to operations. A
single printf-style log would serialize execution and lose nesting, thread identity,
and duration. TT-Metal instead links Tracy instrumentation into `tt_metal.so`, adds a
`profiler.o` layer under `tt_metal/impl/profiler`, captures structured events in a Tracy
server, and post-processes Metal's device logs. The architecture preserves raw events
for interactive causality while also producing CSV suitable for automated comparison.

Instrumentation is compile-time policy. Generic Tracy requires `TRACY_ENABLE=ON` for
the whole project; the pinned TT-Metal build enables its profiler by default and offers
`./build_metal.sh --disable-profiler`. This avoids a mixed binary where some translation
units emit zones that the linked client cannot consistently observe.

### How work and data move

Application scopes emit macros such as `ZoneScoped`, `TracyMessageL`, and
`FrameMarkNamed`. The linked Tracy client transports host events to either
`tracy-capture` or the live `tracy-profiler` server. In TT-Metal, low-level profiler APIs
in `profiler.o` add device-side records to the same analysis flow. The convenience entry
point `python -m tracy {test_script}.py` orchestrates capture/export for Python programs;
`tools/tracy/process_ops_logs.py` cleans Metal kernel records.

For an offline run, start
`build/tools/profiler/bin/tracy-capture -o test.tracy -f`, execute the instrumented
application, then open `test.tracy` in `tracy-profiler` or pass it to
`build/tools/profiler/bin/tracy-csvexport`. The `.tracy` file is the rich event source;
CSV is a projection for tables and scripts. Live GUI and command-line capture are
alternative servers, not two independent clocks to run indiscriminately. Remote GUI use
also requires the documented network/port-forwarding path.

### What must never break

Compared builds must use the same profiler enablement and the same zone boundaries.
Every duration must retain thread/core, operation, and nesting identity; otherwise
overlap becomes accidental addition. Capture must begin before the application connects
and end only after buffered events arrive. Raw `.tracy`, exported CSV, and processed
device logs must belong to the same execution. Profiling changes runtime, so an
optimization claim needs a control run and should not treat the instrumented wall clock
as unperturbed production latency. A missing zone can mean disabled instrumentation or
capture setup failure, not necessarily that code did not execute.

### Where the report makes it concrete

At the pinned snapshot, TT-Metal uses a Tenstorrent Tracy fork based on v0.10, vendored
at `tt_metal/third_party/tracy/`. `tt_metal.so` links Tracy conditionally through
`ENABLE_TRACY` and is itself used by `ttnn.so`; this places instrumentation below both
Metal and TT-NN entry points. `tools/tracy/__main__.py` hides capture/export mechanics,
while `process_ops_logs.py` turns device dumps into operator-visible records. External
applications can link the same Metal library, but must also add the Tracy client/include
path and compile definition consistently. This layered design distinguishes a reusable
instrumentation substrate from one model's performance-report script.

### How the decision is tested

First instrument a tiny application with nested `ZoneScoped`, one named frame, and one
message. Capture it, reopen the `.tracy`, export CSV, and verify that nesting, names, and
durations agree. Then profile a warm TT-NN operation with one deliberate host delay and
one device-side workload increase; the timeline should place the first between launches
and the second inside the device interval. Repeat with the profiler disabled to measure
observer overhead. Preserve the raw trace alongside processed CSV and the exact build
configuration. Only after this end-to-end sanity test should profiler gaps be used to
assign optimization work to host construction, dispatch, or device execution.

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
