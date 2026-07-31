# Level 2 — Reason about runtime state and observability

<p class="source-note" markdown>
<strong>Source class:</strong> Atlas architecture synthesis ·
<strong>Report set:</strong>
[Level 2 catalog](../report-catalog.md#level-2-ttnn-runtime) ·
<strong>Use this page for:</strong> explaining when and why an operation executes
</p>

Level 2 owns the time dimension: device/sub-device ownership, program identity,
queue order, tracing, serialization, comparison, and the difference between a
cold construction path and a repeated execution path.

![Runtime state and evidence loop](../../assets/diagrams/layer2-runtime-control-loop.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/layer2-runtime-control-loop.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/layer2-runtime-control-loop.mmd)</small>

## The architecture contract

The runtime must preserve four forms of correctness:

1. **Identity:** cached or replayed work is valid for the current shapes,
   formats, layouts, addresses, and configuration.
2. **Lifetime:** buffers, programs, queues, and sub-devices remain alive and
   owned until all consumers finish.
3. **Order:** dependencies become visible before dependent commands execute.
4. **Observability:** tracing and comparison describe the execution being
   debugged without silently changing its meaning.

## Architecture reasoning loop

1. Split the run into construction/compile, enqueue/dispatch, device execution,
   and synchronization.
2. Label state as immutable, cache-key state, or runtime-updatable state.
3. Draw queue and sub-device ownership; place an event on every cross-owner
   dependency.
4. Compare cold, warm-cached, and replayed runs using the same workload.
5. Use graph/operation tracing to learn **what** ran; use a profiler to learn
   **when and how long** it ran.
6. Validate optimization paths with comparison mode or an external reference.

## Worked problem — warm runs are sometimes fast and sometimes slow

### Step 1: reject the average

An average mixes distinct paths. Classify samples by program-cache hit/miss,
shape/configuration, trace replay state, allocation state, and synchronization.

### Step 2: form competing hypotheses

- Cache identity is unstable because a shape, layout, or configuration changes.
- A cached program still updates runtime addresses and one update path is slow.
- Host submission is fast, but an implicit synchronization blocks periodically.
- Sub-device work overlaps in one path but serializes in another.

### Step 3: choose evidence that distinguishes them

Record operation parameters, cache-hit state, queue timestamps, and device
timeline for each sample. A cache miss explains construction time; it does not
explain a long device kernel. A host gap explains dispatch; it does not prove a
device stall.

### Step 4: fix the ownership rule

Stabilize cache-key inputs, make runtime updates explicit, or replace implicit
global synchronization with the correct event dependency. Re-run the original
distribution and report tail latency as well as median.

## Tradeoffs an architect tracks

| Mechanism | Removes | New invariant |
|---|---|---|
| Program cache | repeated construction/compile | cache identity must include every compile-time choice |
| Fast Dispatch | high host command-delivery overhead | queues and device command state must remain valid |
| Trace capture/replay | repeated host inter-operation gaps | captured sequence, buffers, and runtime inputs must be replay-compatible |
| Sub-devices / multiple queues | unnecessary global serialization | explicit ownership and event dependencies |
| Serialization | rebuild cost and reproducibility gaps | version, metadata, and architecture compatibility |
| Comparison mode | undetected numerical divergence | reference path and tolerance must match intended semantics |

## Report-by-report architecture decisions

### Sub-Devices — why one chip is divided into explicit ownership domains

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md) ·
[learner analysis](../../rewrites/SubDevices/SubDevices.md)

**Why this design exists.** Device-wide queues and synchronization make
independent workloads wait for resources and completion they do not share.
Concurrency needs a smaller unit of ownership than “the whole chip.”

**Mechanism and benefit.** Sub-devices assign disjoint core/resource sets to
independent command streams; global semaphores and circular buffers are opt-in
bridges when coordination is required. This narrows interference and allows one
partition to progress without a device-wide barrier.

**Price and rejected shortcut.** Isolation removes implicit ordering. Shared
data now needs named global objects, matching lifetimes, and explicit event
edges. Simply adding queues over the same unpartitioned resources creates races
rather than useful concurrency.

**Architect's evidence test.** Draw the core/resource ownership map and one
cross-sub-device buffer state machine. Show that independent timelines overlap
and that every shared object has one mutating owner, publication event, and
reclamation condition.

### Tensor serialization — why logical meaning is stored separately from device placement

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_serialization/tensor_serialization.md) ·
[learner analysis](../../rewrites/tensor_serialization/tensor_serialization.md)

**Why this design exists.** Raw tensor bytes are not self-describing, while
device addresses, L1 placement, and allocator state are not portable across
runs or hosts. A useful cache artifact must preserve semantics without
pretending a prior allocation still exists.

**Mechanism and benefit.** Serialization records payload with shape, dtype,
layout, padding, and version/compatibility metadata. Loading reconstructs the
logical tensor, after which current runtime policy chooses device placement.
This supports reproducible reuse and multi-host exchange.

**Price and rejected shortcut.** Metadata schemas require versioning, atomic
publication, and loud rejection of incompatible files. Dumping bytes alone is
smaller but can reload successfully with the wrong interpretation.

**Architect's evidence test.** Round-trip across processes and supported
versions, corrupt or alter each identity field, and verify the cache misses or
fails rather than silently reinterpreting data. Record that device addresses
are newly allocated after load.

### Graph tracing — why structural capture is separate from time profiling

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md) ·
[learner analysis](../../rewrites/ttnn/graph-tracing.md)

**Why this design exists.** A timeline can show a slow interval but not always
which logical tensors and operations produced it. Conversely, an operation list
without stable tensor identity cannot reconstruct branches, reuse, or memory
lifetime.

**Mechanism and benefit.** The tracer records operation identity, parameters,
tensor producer-consumer edges, and optional memory/stack detail, then exports a
machine-readable graph. This makes unexpected conversions, graph breaks, and
lifetime chains inspectable and joinable to profiler events.

**Price and rejected shortcut.** Rich capture adds observer overhead and data
volume and still does not measure engine stalls. Treating graph duration fields
as a complete device profiler confuses host-visible structure with kernel time.

**Architect's evidence test.** Select one tensor with fan-out and prove its ID,
producer, consumers, allocation lifetime, and corresponding timeline zones.
Repeat with reduced capture and quantify instrumentation overhead.

### Operation tracing — why a lightweight parameter stream complements the graph

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md) ·
[learner analysis](../../rewrites/ttnn/operation-tracing.md)

**Why this design exists.** Many runtime questions require the exact shape,
layout, dtype, or program configuration that selected a variant, not a complete
graph and memory capture. Heavy tracing can be impractical for long workloads.

**Mechanism and benefit.** Operation wrappers serialize a structured invocation
record with stable identity and relevant parameters. The stream is cheap enough
for broad coverage and can expose rare configurations, cache-key churn, and the
input needed for a minimal reproducer.

**Price and rejected shortcut.** It may omit tensor connectivity and device
timing, and unsupported fields can make a record incomplete. Ad hoc text logs
look simpler but are hard to join, version, or replay reliably.

**Architect's evidence test.** From one record, reproduce the same program
variant and compare its cache key and output. Declare missing/unserializable
fields explicitly and join records to graph/profiler identity when causality or
time is required.

### Comparison mode — why the golden path is attached at operation boundaries

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md) ·
[learner analysis](../../rewrites/ttnn/comparison-mode.md)

**Why this design exists.** An incorrect final model result says little about
where divergence began. Optimized layouts, formats, and asynchronous paths can
introduce small or intermittent errors far before the visible failure.

**Mechanism and benefit.** Comparison mode intercepts supported operations,
runs or obtains a golden result for the same logical inputs/configuration, and
reports the numerical difference with operation identity. This turns the first
divergence into a local investigation boundary.

**Price and rejected shortcut.** The golden path costs execution and conversion
time, and a poorly chosen PCC/tolerance can hide or invent failures. Comparing
only the model output is cheaper but loses localization.

**Architect's evidence test.** Prove both paths receive identical semantics,
select tolerances from the format/error budget, and preserve the first failing
operation with its parameters. Disable comparison when collecting performance
numbers and quantify its perturbation.

## Questions and expert answers

### 1. Why is graph tracing not a performance profiler?

???+ note "Expert answer — reasoning"
    Graph tracing answers structural questions: which operations appeared,
    their parameters, and their relationships. A profiler answers temporal and
    resource questions: start/end time, gaps, overlap, stalls, and utilization.
    Structure can suggest a cause—such as an unexpected conversion—but only a
    timeline shows whether it dominates latency. Use both and join them by
    operation/program identity.

### 2. What must be part of a program-cache identity?

???+ note "Expert answer — reasoning"
    Include every property that changes generated kernels, buffer schema,
    compile-time arguments, core grid, formats, layouts, or synchronization.
    Exclude values designed to update safely at runtime, such as compatible
    buffer addresses. The reasoning test is counterfactual: if two calls share
    this key, can they execute the same compiled program with only documented
    runtime patches? If not, the key is incomplete.

### 3. Why can adding another command queue make execution incorrect?

???+ note "Expert answer — reasoning"
    A single queue supplies implicit order. Splitting producer and consumer
    across queues removes that guarantee. The consumer may observe an old
    buffer or reuse storage too early unless an event transfers visibility and
    lifetime ownership. The performance gain is overlap; the correctness cost
    is an explicit dependency graph. Add queues only after naming each buffer's
    producer, consumers, and reclamation point.

### 4. What makes serialized tensors or traces reproducible rather than merely reloadable?

???+ note "Expert answer — reasoning"
    Reproducibility requires semantic metadata: logical shape, padded shape,
    dtype/data format, layout, sharding, device/architecture assumptions,
    software version, and any runtime configuration that affects interpretation.
    Raw bytes can reload successfully while meaning something different. A
    robust artifact validates compatibility and fails loudly when its contract
    cannot be reconstructed.

## Evidence checklist

- Cold, warm-cache, and replayed latency distributions.
- Operation trace joined to host and device timelines.
- Explicit cache key versus runtime-update table.
- Queue/sub-device ownership diagram with events.
- Reference comparison for every optimized execution path.

## Continue

Use [Sub-Devices](../../rewrites/SubDevices/SubDevices.md), tracing,
serialization, and comparison-mode reports as different runtime-state cases.
Continue to [Level 3 — tensor and memory reasoning](level-3-tensor-memory.md)
when execution order is understood but byte placement is not.
