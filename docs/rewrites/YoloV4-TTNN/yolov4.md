<!-- rewrite-status: improved-draft -->
# YOLOv4 in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md"><code>tech_reports/YoloV4-TTNN/yolov4.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

YOLOv4 is a branched, multi-scale graph, so the next consumer—not the current
convolution alone—determines layout and lifetime. Five downsample modules retain
different-resolution routes; the neck upsamples deep features and concatenates them
with earlier maps; the head emits three raw detection tensors. The pinned TT-NN design
therefore centralizes convolution policy in `common.py`'s `Conv`: batch-normalization
parameters are folded into weights/bias, `Conv2dConfig` selects shard layout, dtype,
fidelity, reshard, and activation lifetime, and each branch explicitly preserves a
tensor until its final concat/add. This reduces separate BN traffic and allows adjacent
ops to retain shards, but makes an incorrect deallocation or concat order a model
correctness failure.

### How work and data move

`TtYOLOv4` produces `d1` through `d5`, releases `d1/d2` after their only downstream
consumers, and passes `[d5,d4,d3]` into `TtNeck`. In Downsample1, `conv3` preserves the
left branch while `conv4`-`conv7` form a residual path; after the add, both branches are
converted to `ROW_MAJOR_LAYOUT` because concat requires it. A height-sharded output
config with shard shape `[512,128]` combines two `[512,64]` shards along channels,
then `conv8` consumes the result. The CB/layout transformation is therefore driven by
the concat's semantic C-axis, not merely by tensor size.

The neck applies spatial-pyramid max pools (5x5, 9x9, 13x13) to the 10x10 feature,
normalizes their layouts, and concatenates `[pool_3,pool_2,pool_1,output]`. Two paths
convert to row-major, upsample with `(1,4,1)`, return to tile layout, and concat with
retained 20x20 and 40x40 features. It returns three maps to `TtHead`; the head alternates
convolutions, downsampling, and route concats, finally returning `conv2`, `conv10`, and
`conv18` outputs as the three scales. Those three convolutions use `fused_op=False`
because they are detection outputs rather than conv+BN blocks in the pinned graph.

### What must never break

Every retained feature must come from the named downsample/neck branch and remain live
until its concat. Channel concatenation order is semantic: reversing pool or route
inputs changes learned weight interpretation even when shape is valid. Upsampling must
align the same spatial cells expected by the skip feature. BN folding must implement
the checkpoint's running mean/variance, scale, and bias exactly; the source formula has
no epsilon term shown, so the actual preprocessing implementation must be the oracle.
`deallocate_activation=True` is legal only when no later branch consumes the input;
the report explicitly keeps inputs to Downsample1 `conv3` and `conv5`. Physical shard
padding, `bfloat8_b` weights, and LoFi math must still meet raw-head and task accuracy
contracts.

### Where the report makes it concrete

`Conv.__call__` uses `weights_dtype=ttnn.bfloat8_b`, `MathFidelity.LoFi`, approximate
math, `fp32_dest_acc_enabled=False`, optional `act_block_h_override`,
`reshard_if_not_optimal`, and a chosen `TensorMemoryLayout`. The pinned heuristic uses
height sharding when `N*H*W >> C`, block when the quantities are comparable, and width
when C dominates: its examples are `[1,128,128,32]`, `[1,32,32,640]`, and
`[1,16,16,1024]`. This is a candidate-selection rule, not a proof. The report's
neck/head plots cite a maximum-kernel-duration reduction from about 80,000 ns to 50,000
ns after changing convolution weight dtype, but the measurement is tied to that model,
device, and profiler snapshot.

### How the decision is tested

Freeze one image and checkpoint, then compare TT-NN with Torch at every downsample
output, residual add, neck pre/post-upsample concat, and each raw head. Record logical
NHWC shape, shard spec/core count, layout, dtype, PCC plus an error metric, and verify
decoded boxes/mAP separately. Run liveness poisoning around each
`deallocate_activation`/`ttnn.deallocate` boundary to catch a surviving branch. For
performance, A/B one convolution layout or weight dtype at a time while measuring
kernel duration, reshard/layout-conversion bytes, peak L1/DRAM, and full-model latency;
include warm cached runs. Accept the source heuristic only when the higher core count
reduces end-to-end time after adjacent conversions and all three raw heads plus detection
accuracy remain within the predeclared tolerance.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md):

- **Lifetime and placement.** `ttnn.deallocate(tensor)` releases intermediates whose
  final consumer has completed; `BLOCK_SHARDED`, `HEIGHT_SHARDED`, and `WIDTH_SHARDED`
  choose ownership for later operators. Early release or mismatched resharding is a
  correctness failure before it is a memory optimization.

- **Precision and configuration.** `bfloat8_b`, `MathFidelity::LoFi`, and helpers in
  `common.py` trade accuracy for footprint/throughput through model-specific configs.
  Validate each module and detection output while measuring conversion and kernel time,
  not only one convolution microbenchmark.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report maps YOLOv4's staged convolutional backbone, route/shortcut branches,
    neck, and three detection heads into TT-NN, then optimizes layouts and convolution
    configurations while preserving multi-scale feature semantics. Branch-heavy
    dataflow makes intermediate validation especially important.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every downsample, residual, route, upsample, and concatenation must produce the
    reference shape and channel order; the three head outputs must remain associated
    with their intended spatial scales and anchor/post-processing interpretation.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    An image enters TT preprocessing → five downsampling/backbone stages produce
    multi-scale feature maps → route/shortcut tensors feed the neck → upsample and
    concatenation combine high- and low-resolution features → three heads emit detection
    tensors → host post-processing decodes boxes/classes.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Model-specific configs, convolution program choices, shard
    layouts, supported image/batch sizes, weight-download path, device grid, and
    reported performance depend on the TT-NN snapshot and chip.

    **Durable model.** Validate branch boundaries and shapes, name multi-scale tensors
    explicitly, follow each consumer before choosing layout, avoid repeated conversion
    at concatenations, and test raw heads separately from host decoding.

## Source and delta

- **Original source:** [`tech_reports/YoloV4-TTNN/yolov4.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/YoloV4-TTNN/yolov4.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
