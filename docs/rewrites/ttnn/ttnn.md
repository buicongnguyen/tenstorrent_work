<!-- rewrite-status: seed -->
# TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md"><code>tech_reports/ttnn/ttnn.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/ttnn.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 35 |
| Section headings | 6 |
| Fenced code examples | 0 |
| Markdown images | 5 |

### Section outline

- Roadmap
- High Level Structure Overview
- ML Framework
- OP Library
- OP Infra
- TT-NN Runtime

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The overview explains TT-NN's layered path from ML-framework-facing tensor
    operations through the operation library and infrastructure to program generation,
    caching, dispatch, and TT-Metal device execution. Its programming task is defining
    clean contracts across those layers.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Across every layer, a tensor's logical shape, dtype, layout, placement, ownership,
    and dependency state must remain coherent. An operation may lower or transform
    representation, but its public result must satisfy the declared semantic contract.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A framework/user calls a TT-NN operation → validation and operation infrastructure
    select an implementation → a device operation computes program identity and creates
    or reuses a program → runtime arguments bind tensors → command queues dispatch
    kernels → output tensors return through TT-NN to the caller.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Class names, roadmap, registration mechanisms, program-cache
    hooks, runtime internals, supported frontends, and exact module boundaries evolve
    with TT-NN.

    **Durable model.** Layer semantic APIs over specialized kernels, validate contracts
    before lowering, cache specialization separately from runtime state, keep tensor
    metadata first-class, and expose profiling/debugging boundaries between layers.

## Source and delta

- **Original source:** [`tech_reports/ttnn/ttnn.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/ttnn.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
