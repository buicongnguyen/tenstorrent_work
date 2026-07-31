<!-- rewrite-status: seed -->
# Real-time profiler — getting started

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/real_time_profiler/getting-started.md"><code>tech_reports/real_time_profiler/getting-started.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/real_time_profiler/getting-started.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 55 |
| Section headings | 2 |
| Fenced code examples | 1 |
| Markdown images | 0 |

### Section outline

- Register a callback (Python) — append JSON lines
- Tracy default support

## Improvement plan

1. **Architecture pressure.** Define the live use case, event schema, timestamp/source
   identity, acceptable observation latency, producer-overhead budget,
   buffering/backpressure behavior, and required durability on abnormal termination.

2. **Flow to make explicit.** Draw `ProgramRealtimeRecord` emission through runtime
   queueing, callback registration/invocation, JSON-line or Tracy sink, incremental
   consumer, flush, and `UnregisterProgramRealtimeProfilerCallback(handle)`.

3. **Invariant to prove.** Prove callback processing preserves complete event identity/order
   without blocking producers beyond budget, handles concurrency/failure, and flushes every
   accepted record before unregister/shutdown.

4. **TT-Metal evidence to connect.** Connect fields such as `runtime_id`, `start_timestamp`,
   `end_timestamp`, `frequency`, `chip_id`, and `kernel_sources` to the JSON/Tracy
   representation and consuming analysis.

5. **Experiment and expected observation.** Deliberately slow and then fail the callback
   consumer under a steady workload; expected result: documented buffering/backpressure or
   loss behavior occurs without silent record corruption, and measured producer perturbation
   remains within budget.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
