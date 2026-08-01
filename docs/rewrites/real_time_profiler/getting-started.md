<!-- rewrite-status: improved-draft -->
# Real-time profiler — getting started

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/real_time_profiler/getting-started.md"><code>tech_reports/real_time_profiler/getting-started.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned real-time profiler is a streaming observation path, not a post-run device
dump. Completed programs already return information over the fast-dispatch D2H socket,
so the profiler attaches per-program timing to that path and delivers batches to host
callbacks. This avoids a second polling/control channel and makes records available while
the workload runs. The tradeoff is bounded consumer capacity: callbacks are concurrent,
and a slow sink can lose records, which is why every callback receives `batch.dropped`
rather than an implied guarantee of lossless tracing.

The record schema is chosen so one timestamp interval remains attributable after it
leaves the runtime. `runtime_id` identifies the dispatched program, `chip_id` identifies
its clock domain, `kernel_sources` explains which kernels contributed, and raw
`start_timestamp`/`end_timestamp` preserve device cycles. `frequency` in cycles per
nanosecond supplies the conversion scale. Raw timestamps from different chips should not
be ordered as if they share one clock without an explicit calibration mechanism; the
pinned Tracy handler provides per-chip context and calibration for that visualization.

### How work and data move

A completed program produces a `ProgramRealtimeRecord`, and the runtime groups available
records into a callback batch delivered from the fast-dispatch D2H path. Registration is
additive: `ttnn.device.RegisterProgramRealtimeProfilerCallback(on_record_batch)` returns
a handle and does not replace Metal's `RealtimeProfilerTracyHandler`. Multiple user
callbacks and the Tracy handler can therefore consume the same stream concurrently.

The JSON-lines example increments a process-level `dropped_total`, serializes all six
record fields, writes one record per line, and calls `flush()` per batch. JSONL makes a
partially written run incrementally readable and keeps one malformed/truncated tail from
destroying earlier records. The callback owns thread-safety for shared state: if multiple
callbacks or meshes share a file, counter, or analysis object, they need a lock or
separate per-callback sink. Cleanup calls
`UnregisterProgramRealtimeProfilerCallback(handle)` in `finally` before closing the file,
preventing a concurrent invocation from writing through a dead resource.

Not every dispatch setup can activate the stream. The source names ETH dispatch and
remote chips lacking required resources as examples. Code must query
`ttnn.device.IsProgramRealtimeProfilerActive()` before asserting that program count and
record count match; inactivity is a capability state, distinct from dropped batches.

### What must never break

Within each accepted record, start/end/frequency/chip identity must remain together;
converting timestamps and discarding the source clock makes later audit impossible.
`end_timestamp` must not be interpreted before `start_timestamp`, and a duration must be
converted with that record's frequency. Shared callback resources must be synchronized.
The dropped count must be accumulated and reported, not silently ignored. Registration
handle lifetime must enclose callback resource lifetime: unregister first, then close the
sink. Inactive profiler, active profiler with zero completed programs, and active
profiler with dropped records are three different outcomes.

### Where the report makes it concrete

The C++ boundary is
`tt::tt_metal::experimental::RegisterProgramRealtimeProfilerCallback` in
`realtime_profiler.hpp`; `test_realtime_profiler_csv.cpp` demonstrates a disk sink.
Python's callback has the same ownership pattern. Tracy's built-in handler turns records
into per-chip device-timeline program zones and optional synchronization markers. A
custom JSON callback is therefore best for machine-readable online analysis, while
Tracy adds calibrated visual causality; registering one does not disable the other.

### How the decision is tested

Run a known number of synchronized programs after first checking active status. For each
record, assert nonnegative raw duration, known `chip_id`, nonempty/expected kernel paths,
and a duration conversion based on its own frequency. Compare a no-callback baseline,
Tracy-only capture, and JSONL callback to quantify workload perturbation. Then delay the
callback deliberately and confirm `batch.dropped` accounts for loss while surviving
JSON lines remain parseable. Register two callbacks writing separate sinks to exercise
concurrency, unregister one mid-run, and verify the other continues. Finally inspect the
Tracy per-chip zones against JSON durations; disagreement should trigger clock-domain,
calibration, or dropped-record investigation rather than timeline reordering by hand.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/real_time_profiler/getting-started.md):

- **Event identity.** `runtime_id`, `chip_id`, and `kernel_sources` identify which host
  operation and device kernels produced a record. Preserve them when converting the
  stream to JSON or Tracy so zones from different chips or launches are not merged
  accidentally.

- **Time conversion.** `start_timestamp`, `end_timestamp`, and `frequency` convert
  device ticks into duration. Use the frequency associated with that record/device and
  handle wrap or missing completion explicitly before comparing host and device
  timelines.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/real_time_profiler/getting-started.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The real-time profiler exposes events during execution through callbacks, JSON
    lines, or Tracy so long-running applications and live tools can observe latency and
    stalls without waiting for an end-of-run report.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Callback processing must preserve event identity and timestamp ordering without
    blocking the producer enough to distort the workload. Records must be flushed or
    durably written before shutdown, and consumers must tolerate concurrent arrival.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Runtime/device instrumentation emits a profiler record → the real-time collection
    path timestamps and queues it → a registered Python callback receives the structured
    event → the callback appends one complete JSON object or forwards it to Tracy → an
    external consumer incrementally analyzes the stream.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Callback APIs, event schemas, buffering, Tracy defaults,
    thread model, and supported event sources are revision-specific.

    **Durable model.** Use structured append-only telemetry, decouple producers from
    slow consumers, bound buffering/backpressure, include source and clock metadata, and
    quantify observability overhead under the same workload.

## Source and delta

- **Original source:** [`tech_reports/real_time_profiler/getting-started.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/real_time_profiler/getting-started.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/real_time_profiler/getting-started.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
