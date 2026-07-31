<!-- rewrite-status: seed -->
# TT-NN Graph Tracing

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md"><code>tech_reports/ttnn/graph-tracing.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/graph-tracing.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 938 |
| Section headings | 48 |
| Fenced code examples | 31 |
| Markdown images | 2 |

### Section outline

- Table of Contents
- Quick Start
  - Python (5 lines)
  - C++
  - Save to File (for ttnn-visualizer)
- Core Concepts
  - What Gets Captured
  - Two-Phase Architecture
  - How Operations Are Tracked
  - FastOperation vs Operation
  - Tensor Connectivity
  - Run Modes
- Basic Usage
  - Extracting Operation Durations
  - Tracking Memory Usage
  - Generating Visualizations
- Saving Reports
  - Save Complete Report to File
  - Import into Visualizer Database
    - Import Behavior
- Advanced Features
  - Stack Trace Capture
  - Buffer Page Capture
  - Reducing Capture Overhead
- … 24 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Specify the structural questions requiring capture—unexpected
   operation, tensor fan-out, allocation lifetime, graph break, stack origin—and choose
   slow/full or fast capture fields accordingly; do not call it a device stall profiler.

2. **Flow to make explicit.** Draw operation entry through tracer wrapper, parameter/input
   tensor IDs, producer-consumer edge creation, output IDs, optional stack/buffer
   pages/timing, report serialization, database import, and visualizer query.

3. **Invariant to prove.** Prove every operation/tensor has stable identity, edges reflect
   actual producers/consumers, capture does not change semantics, and omitted or
   overhead-heavy fields are declared when interpreting the result.

4. **TT-Metal evidence to connect.** Connect modes to `full_graph_capture`,
   `slow_dispatch=True`, `enable_fast_runtime_mode=False`, `Operation`, `FastOperation`, and
   examples such as `ttnn::add` and `ttnn::matmul`.

5. **Experiment and expected observation.** Capture one branching graph in fast and full
   modes, then join a chosen operation to profiler identity; expected result: identical
   graph semantics, declared detail/overhead differences, and no inference of device stalls
   from structure alone.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
