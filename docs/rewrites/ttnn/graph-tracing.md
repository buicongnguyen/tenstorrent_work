<!-- rewrite-status: improved-draft -->
# TT-NN Graph Tracing

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md"><code>tech_reports/ttnn/graph-tracing.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Graph tracing separates capture from analysis so SQLite and visualization work never
runs in the model's execution path. C++ `GraphProcessor` records operations, tensors,
buffers, lifetime events, wall-clock boundaries, and hierarchy in memory; Python
decorators optionally add call arguments and tensor IDs; a later importer turns JSON
into the visualizer database. This makes the trace a causal/ownership record rather
than a device-cycle profiler. Capture is configurable because evidence has cost:
Python stacks call `traceback.extract_stack`, detailed buffers snapshot pages, and slow
dispatch nests a sub-capture around every operation.
The two-phase design also lets new database queries reuse a recorded JSON report without
rerunning the device workload, provided the report retained the required fields.

### How work and data move

Python `begin_graph_capture(RunMode.NORMAL)` enables Python I/O recording, while a
C++-initiated capture such as `MemoryUsageTracker` leaves decorators transparent.
`FastOperation` and `Operation` both emit `function_start/end`, arguments, input IDs,
and fresh output IDs (`set_tensor_id(..., force=True)`), but only `Operation` captures
per-op C++ subgraphs. `full_graph_capture(path)` defaults to `slow_dispatch=True`,
temporarily setting `enable_fast_runtime_mode=False`, enabling Python stacks and buffer
pages, then restoring settings. With `slow_dispatch=False`, the importer synthesizes
subgraphs from flat `FastOperation` records. `end_graph_capture_to_file` publishes JSON;
`python -m ttnn.graph_report report.json db/` performs offline import.

### What must never break

Every output receives a fresh ID even for in-place operations, and a consumer's
`python_io.input_tensor_ids` must match the producer's output ID. Every
`function_start` must pair with a `function_end`; the importer classifies an orphan as
`incomplete_operation`. `Tensor::deallocate` records only when a device buffer is
actually freed—host tensors and shared references may legitimately omit it. `NO_DISPATCH`
does not provide real allocation addresses or execution evidence, while `NORMAL` does.
Capture level and disabled fields must travel with any conclusion; a synthetic fast
subgraph cannot prove the same nested calls as a slow captured subgraph.

### Where the report makes it concrete

Detailed page records include `device_id`, address, core/bank, page index/address/size,
and `BufferType` values; versioned `buffer_pages_by_address` distinguishes address reuse.
`extract_levelized_graph(max_level)` converts nesting into vertices with `in_edges`,
`out_edges`, and `internals`. The report's broadcast-add example demonstrates why this
matters: top-level `ttnn::add` contains `ttnn::repeat`, primitive/device operations,
buffer allocations and later deallocations. A flat operation list would hide both the
implicit broadcast and its temporary-buffer lifetime.
Versioned address timelines matter for the same reason: an address reused after free is
a new allocation lifetime, not a data edge to the prior tensor.

### How the decision is tested

Capture `ttnn::add` with broadcasting in `NORMAL` fast, `NORMAL` slow/full, and
`NO_DISPATCH`. Check tensor-ID edges and top-level structure agree; require the slow
trace to expose the real nested `repeat`/primitive graph, and label the fast version's
equivalent nodes synthetic. Enable detailed buffer tracing and verify allocation,
page placement, and actual deallocation against a known shared-reference case. Force a
timeout with `TT_METAL_OPERATION_TIMEOUT_SECONDS` and confirm the unfinished start is
reported as incomplete. Finally compare model outputs with capture disabled. Report
capture overhead separately and join device timing only through profiler evidence—the
graph's `duration_ns` is wall-clock and cannot alone locate a Tensix stall.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md):

- **Capture mode.** `full_graph_capture(..., slow_dispatch=True)` temporarily selects
  `enable_fast_runtime_mode=False` and captures nested `Operation` subgraphs;
  `slow_dispatch=False` retains `FastOperation` records and synthetic subgraphs. Record
  the chosen mode because the two graphs carry different evidence.

- **Node semantics.** Examples such as `ttnn::add` and `ttnn::matmul` should be traced
  from Python/C++ operation through nested fast operation and tensor edges. Validate
  node IDs, input/output shapes, and ordering before using the graph to infer fusion or
  device timing.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    Graph tracing captures operation calls, tensor producer-consumer edges, durations,
    memory information, and optional stack/buffer details so developers can reconstruct
    what TT-NN executed and identify graph, lifetime, or performance problems.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Each operation and tensor must have a stable identity within the trace, and every
    edge must connect the actual producer to its consumers. Capture must observe rather
    than change operation semantics; overhead and omitted detail must be recorded when
    interpreting timing.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A TT-NN operation enters the tracing wrapper → operation attributes, stack/context,
    input tensor IDs, and timing are recorded → output tensor IDs create producer edges
    → optional memory/page data is attached → the report is serialized →
    visualizer/database reconstructs the graph for queries.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Tracer APIs, `FastOperation` handling, run modes,
    file/database schema, captured fields, stack/page options, and overhead are
    version-specific.

    **Durable model.** Represent execution as identities plus causal edges, make capture
    level explicit, preserve a machine-readable format, distinguish logical graph time
    from device-kernel time, and use graph evidence to select a smaller profiling
    experiment.

## Source and delta

- **Original source:** [`tech_reports/ttnn/graph-tracing.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/graph-tracing.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
