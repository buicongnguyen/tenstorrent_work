<!-- rewrite-status: improved-draft -->
# New model bring-up in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md"><code>tech_reports/ttnn/TTNN-model-bringup.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned workflow orders correctness before performance because an end-to-end model
contains too many coupled transformations to debug from its final output. A model card,
Torch graph, and model summary first freeze the semantic inventory: modules, operator
types, shapes, parameters, and preprocessing. For the YOLOv4 example that inventory is
nine modules and operations including convolution, max-pool, concat, batch norm, Mish,
LeakyReLU, upsample, and add. Only then are TT-NN op and module tests written. This
creates checkpoints narrow enough to distinguish a missing kernel or unsupported
configuration from a composition bug, before sharding, lower precision, trace, or
multiple command queues make the execution harder to compare.

### How work and data move

The Torch implementation produces the graph and golden tensors; a summary script such
as `models/demos/yolov4/reference/yolov4_summary.py` exposes every op's arguments. Each
TT-NN op is tested against Torch with PCC, followed by a module test such as YOLOv4
Downsample1, and then the composed model. Missing functionality is isolated in an issue
(the report cites ConvTranspose2D issue 6326) or temporarily falls back to Torch rather
than being hidden in a full-model mismatch.

After parity, optimization moves through three boundaries. Per-op changes select
height/width/block sharding, `bfloat8_b`, and `MathFidelity.LoFi` subject to PCC.
Module/full-model changes preserve layouts across consecutive consumers and set
`deallocate_activation=True` only after the final graph consumer. A profiler build and
`tools/tracy/profile_this.py` generate the CSV performance sheet; device-kernel duration,
core count, and the report's utilization formula
`(PM ideal / device kernel duration) * (108 / core_count)` select measured targets.
Trace and two CQs are introduced independently, tested independently, then combined.

### What must never break

Reference and TT-NN checkpoints must see identical inputs, weights, preprocessing,
module boundaries, and output interpretation. PCC thresholds must be chosen before
tuning and paired with task-level accuracy where correlation alone is insufficient.
Sharding or dtype may change physical representation, but logical shape, channel/token
order, and graph dependencies must remain. A tensor may be deallocated only after its
last fan-out consumer. Trace replay and 2-CQ overlap must preserve the queue/event
dependencies of the proven single-CQ sequence. A profiler's fastest kernel cannot be
accepted if it introduces an adjacent reshard that worsens end-to-end time.

### Where the report makes it concrete

The source names executable evidence: max-pool and convolution unit-test directories,
YOLOv4 Torch/TT-NN Downsample1 modules, `test_ttnn_yolov4.py` PCC checks, Tracy's CSV,
and visualizer configuration fields such as `enable_detailed_buffer_report`. It also
gives a safe sequencing rule for advanced performance: first make trace alone correct,
then 2CQ alone, then their combination, with a separate unit test for each. This is an
architectural isolation strategy—each stage changes one control mechanism—rather than
a ceremonial checklist.

### How the decision is tested

Freeze inputs and weights, save Torch outputs for every op/module boundary, and bring up
one TT-NN boundary at a time. Record PCC and an error metric appropriate to the output,
then run the complete task accuracy test. Once correct, profile cold and steady-state
runs; sort device-kernel duration, but include reshard/conversion and host overhead in
the optimization delta. For each selected change—sharding, dtype, fidelity,
deallocation, trace, or 2CQ—rerun the smallest unit, affected module, full model, peak
memory, and end-to-end latency. The expected result is not merely “higher utilization”:
the same accepted semantics must complete faster or with lower memory, and attribution
must point to the one changed boundary.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md):

- **Module checkpoint.** For every model module, name the TT-NN operations,
  preprocessing utility, tensor shape/layout/dtype, and golden implementation used by
  its unit test. This is the executable contract that localizes the first divergence.

- **Program and performance.** Connect each operation to its device program/config,
  cached-program identity, and profiler zone. Optimize only a measured boundary, then
  rerun the module and end-to-end accuracy checks so a faster representation change
  cannot bypass the model contract.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report gives a bottom-up model-porting workflow: implement TT-NN
    operations/modules, compare each against a reference, assemble end to end, then
    optimize only after correctness and obtain reliable performance measurements.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every module checkpoint must receive semantically identical inputs and produce the
    reference shape/order with an agreed error metric such as PCC. An optimization may
    change layout, sharding, or precision only if the model contract remains satisfied.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Reference inputs are preprocessed → individual TT-NN ops are unit-tested → ops form
    modules with checkpoint comparisons → modules assemble into the end-to-end model →
    output post-processing compares with the golden implementation → profiling
    identifies the next bottleneck → one optimization is applied.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Current TT-NN APIs, supported operators, program configs,
    data types, model utilities, profiler commands, and device performance are
    snapshot-specific.

    **Durable model.** Port bottom-up, keep an executable golden model, validate at
    narrowing checkpoints, separate correctness from performance phases, record
    shapes/layouts explicitly, and optimize one measured bottleneck at a time.

## Source and delta

- **Original source:** [`tech_reports/ttnn/TTNN-model-bringup.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/TTNN-model-bringup.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
