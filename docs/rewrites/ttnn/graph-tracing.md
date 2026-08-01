<!-- rewrite-status: improved-draft -->
# TT-NN Graph Tracing

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md"><code>tech_reports/ttnn/graph-tracing.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to specify the structural questions requiring
capture—unexpected operation, tensor fan-out, allocation lifetime, graph break, stack
origin—and choose slow/full or fast capture fields accordingly; do not call it a device
stall profiler.

### How work and data move

The complete path is operation entry through tracer wrapper, parameter/input tensor IDs,
producer-consumer edge creation, output IDs, optional stack/buffer pages/timing, report
serialization, database import, and visualizer query.

### What must never break

The non-negotiable invariant is that every operation/tensor has stable identity, edges
reflect actual producers/consumers, capture does not change semantics, and omitted or
overhead-heavy fields are declared when interpreting the result.

### Where the report makes it concrete

The report makes the decision concrete by connecting modes to `full_graph_capture`,
`slow_dispatch=True`, `enable_fast_runtime_mode=False`, `Operation`, `FastOperation`,
and examples such as `ttnn::add` and `ttnn::matmul`.

### How the decision is tested

The controlled procedure is to capture one branching graph in fast and full modes, then
join a chosen operation to profiler identity. **Expected observation:** identical
graph semantics, declared detail/overhead differences, and no inference of device stalls
from structure alone.

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
