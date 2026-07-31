<!-- rewrite-status: seed -->
# YOLOv4 in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md"><code>tech_reports/YoloV4-TTNN/yolov4.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/YoloV4-TTNN/yolov4.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1703 |
| Section headings | 25 |
| Fenced code examples | 25 |
| Markdown images | 27 |

### Section outline

- Contents
- 1. Overview
- 2. YOLOv4 TT-NN Optimization Techniques
  - 2.1 Sharding on all relevant OPs
  - 2.2 Deallocate Unused tensors
  - 2.3 Data type Optimization
  - 2.4 Use best shardlayout for convolution
    - How to generate the graph?
- 3. YOLOv4 Architecture
- 3.1 Downsample1 :-
  - Let’s examine how some of the aforementioned optimization techniques contributed to enhancing the performance of the Downsample1 sub-module, accompanied by graphical visualizations.
- 3.2 Downsample2 :-
  - Let’s examine how some of the aforementioned optimization techniques contributed to enhancing the performance of the Downsample2 sub-module, accompanied by graphical visualizations.
- 3.3 Downsample3 :-
  - Let’s examine how some of the aforementioned optimization techniques contributed to enhancing the performance of the Downsample3 sub-module, accompanied by graphical visualizations.
- 3.4 Downsample4 :-
  - Let’s examine how some of the aforementioned optimization techniques contributed to enhancing the performance of the Downsample4 sub-module, accompanied by graphical visualizations.
- 3.5 Downsample5 :-
  - Let’s examine how some of the aforementioned optimization techniques contributed to enhancing the performance of the Downsample5 sub-module, accompanied by graphical visualizations.
- 3.6 Neck :-
  - Let’s examine how some of the aforementioned optimization techniques contributed to enhancing the performance of the Neck sub-module, accompanied by graphical visualizations.
- 3.7 Head :-
  - Let’s examine how some of the aforementioned optimization techniques contributed to enhancing the performance of the Head sub-module, accompanied by graphical visualizations.
- 4. Auto download weights
- … 1 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Treat each downsample, residual/route, neck upsample/concat,
   and three detection heads as a named tensor contract; identify where sharding, format, or
   deallocation should follow the next branch consumer.

2. **Flow to make explicit.** Draw one image through five downsample stages, retained
   multi-scale feature maps, neck routes/upsamples/concats, scale-specific heads, raw output
   tensors, and host decoding.

3. **Invariant to prove.** Prove feature shape/channel order, route source, concat order,
   upsample alignment, and head-to-scale/anchor meaning; physical padding or sharding must
   not change logical multi-scale semantics.

4. **TT-Metal evidence to connect.** Connect the plan to `ttnn.deallocate(tensor)`,
   `bfloat8_b`, `BLOCK_SHARDED`, `HEIGHT_SHARDED`, `WIDTH_SHARDED`, `common.py`, and
   `MathFidelity::LoFi` choices in the source.

5. **Experiment and expected observation.** Capture raw values and layouts at every neck
   merge and head before decoding, then remove one conversion/deallocation boundary;
   expected result: exact/PCC parity at raw heads and a measurable end-to-end benefit
   without higher peak memory.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
