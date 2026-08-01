<!-- rewrite-status: improved-draft -->
# TTNN Operation Parameter Tracing

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md"><code>tech_reports/ttnn/operation-tracing.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Operation tracing answers a narrower question than graph tracing: “with exactly which
Python-visible parameters and returns was each TT-NN operation invoked?” The pinned
implementation writes one JSON file per call so a long workload can be filtered without
loading a monolithic trace. It requires the non-fast runtime path, hence requires
`enable_fast_runtime_mode=false`; when disabled the tracer adds only the documented
boolean check. Tensor metadata is the default because serializing device values would
require a CPU transfer and can dominate execution.
Per-call files also isolate failures: records published before a later crash remain
independently inspectable, subject to the implementation's actual file-write behavior.

### How work and data move

After `ttnn.operation_tracer.enable_tracing(True)`, call number N is written as
`{operation_id}_{operation_name}_{timestamp}.json` under
`generated/ttnn/operation_parameters/` or `ttnn.CONFIG.root_report_path`. The record
contains sequential `operation_id`, `operation_name`, positional `args` with position
and value, `kwargs`, and serialized `return_value`. A `ttnn.Tensor` contributes shape,
dtype, layout, and `storage_type`; a Torch tensor has its corresponding type metadata.
If `enable_tensor_value_serialization(True)` is active, values join the record—device
tensors first move to CPU—then normal execution returns the original result.

### What must never break

The sequential ID and operation name in the JSON must match the file name and actual
call, and argument position/keyword identity must survive serialization. Tensor
metadata may describe an invocation but cannot reproduce it unless values are captured
or supplied separately; the default must never be described as a replay artifact.
Enabling values must not mutate device tensors or their storage. The source does not
state concurrency ordering, atomic file publication, schema versioning, or behavior for
non-serializable custom arguments, so those properties must not be inferred. Trace
directories also require run isolation: stale files can have perfectly valid IDs and
still belong to another workload.

### Where the report makes it concrete

The source's `3_ttnn_add_20260115_104616_345678.json` example encodes logical order and
a timestamp-like suffix; it does not specify uniqueness or collision handling.
`operation_tracing_examples/` is the reference for actual nested JSON values. The
overhead table is qualitative: disabled is one boolean check, metadata-only is
“minimal,” and values are “significant.” Those labels are not
cycle measurements. The primary architecture trade is diagnostic completeness versus
perturbation and storage: keep metadata for broad capture, then rerun the smallest
failing region with values.
That staged workflow avoids moving every model activation to CPU to diagnose one call.

### How the decision is tested

Start with a clean run-specific directory and issue two `ttnn.add` calls that differ in
shape/layout or a keyword. Verify IDs 1 and 2, argument positions, tensor metadata,
returns, and filenames. Repeat with values enabled on tiny host and device tensors;
compare the recorded data and returned tensors exactly while measuring CPU-transfer,
JSON size, and latency separately. Invoke tracing from multiple threads and pass a
custom/non-serializable value to establish the pinned behavior rather than assume it.
Finally disable tracing and fast-mode override, confirm no new files appear and outputs
remain unchanged. A successful metadata record proves observability, not deterministic
replay or cache-key completeness.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
