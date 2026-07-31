<!-- rewrite-status: seed -->
# TTNN Operation Parameter Tracing

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md"><code>tech_reports/ttnn/operation-tracing.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/operation-tracing.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 127 |
| Section headings | 14 |
| Fenced code examples | 8 |
| Markdown images | 0 |

### Section outline

- Quick Start
  - With pytest
  - In Python code
- API Reference
- Trace File Format
  - File Naming
  - JSON Structure
  - Tensor Fields
- Configuration
  - Custom Output Directory
  - Tensor Value Serialization
- Performance
- Limitations
- Troubleshooting

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    Operation tracing records TT-NN operation names and parameter values in a structured
    stream so a developer can reproduce, audit, or analyze which configurations actually
    reached the runtime without enabling a heavier full graph capture.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A record must correspond to exactly one invocation and serialize enough
    type/shape/configuration context to distinguish variants, while tracing remains
    thread-safe and does not alter ordering or tensor lifetime.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    An application calls a TT-NN operation → the operation wrapper serializes selected
    arguments/attributes and invocation metadata → the trace writer appends the record →
    later tools filter or aggregate the file → a suspicious configuration is replayed in
    a focused test.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Configuration flags, supported argument serialization, trace
    schema/path, buffering, overhead, and limitations are tied to the current
    implementation.

    **Durable model.** Prefer structured events over ad hoc text, include stable
    identity and version metadata, make missing/unserializable fields visible, decouple
    logging from execution, and convert observations into reproducible minimal cases.

## Source and delta

- **Original source:** [`tech_reports/ttnn/operation-tracing.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/operation-tracing.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
