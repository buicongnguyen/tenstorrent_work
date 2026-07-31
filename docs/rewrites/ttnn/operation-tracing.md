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
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

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

1. **Architecture pressure.** Define the minimum structured invocation schema needed to
   reproduce cache/config behavior—operation ID/name, shapes, dtypes, layouts,
   memory/program configs, scalar parameters, version, and unsupported-field markers.

2. **Flow to make explicit.** Draw TT-NN wrapper entry through parameter serialization,
   unique filename/record append, generated operation-parameter directory, offline
   filtering/aggregation, and minimal reproducer construction.

3. **Invariant to prove.** Prove one record corresponds to one invocation, preserves
   thread-safe order/identity, distinguishes program-selecting variants, and exposes missing
   values instead of silently producing an incomplete replay description.

4. **TT-Metal evidence to connect.** Connect the workflow to
   `enable_fast_runtime_mode=false`, `generated/ttnn/operation_parameters/`, record fields
   `operation_id`/`operation_name`, JSON examples such as `3_ttnn_add_...json`, and
   `operation_tracing_examples/`.

5. **Experiment and expected observation.** Trace two calls differing in one
   program-selecting attribute and replay from their records; expected result: distinct
   captured configurations/cache identities with equivalent outputs to the original calls.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md):

- **Trace activation.** `enable_fast_runtime_mode=false` selects the path that emits
  operation-parameter records under `generated/ttnn/operation_parameters/`. Verify the
  directory is clean or run-scoped so old JSON is not attributed to the current
  workload.

- **Record identity.** `operation_id` and `operation_name` connect files such as
  `3_ttnn_add_...json` to execution order; `operation_tracing_examples/` shows
  consumption. Preserve tensor/config fields and reject missing IDs before
  reconstructing or replaying a sequence.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
