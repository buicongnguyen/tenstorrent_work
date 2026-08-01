<!-- rewrite-status: improved-draft -->
# YOLOv4 in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md"><code>tech_reports/YoloV4-TTNN/yolov4.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to treat each downsample, residual/route, neck
upsample/concat, and three detection heads as a named tensor contract; identify where
sharding, format, or deallocation should follow the next branch consumer.

### How work and data move

The complete path is one image through five downsample stages, retained multi-scale
feature maps, neck routes/upsamples/concats, scale-specific heads, raw output tensors,
and host decoding.

### What must never break

The non-negotiable invariant is that feature shape/channel order, route source, concat
order, upsample alignment, and head-to-scale/anchor meaning; physical padding or
sharding must not change logical multi-scale semantics.

### Where the report makes it concrete

The report makes the decision concrete by connecting the plan to
`ttnn.deallocate(tensor)`, `bfloat8_b`, `BLOCK_SHARDED`, `HEIGHT_SHARDED`,
`WIDTH_SHARDED`, `common.py`, and `MathFidelity::LoFi` choices in the source.

### How the decision is tested

The controlled procedure is to capture raw values and layouts at every neck merge and
head before decoding, then remove one conversion/deallocation boundary. **Expected observation:** exact/PCC parity at raw heads and a measurable end-to-end benefit without
higher peak memory.

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
