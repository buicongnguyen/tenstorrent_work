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
    establishes provenance, a reading map, and review prompts; its technical
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

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

Before rewriting this page, answer from the original:

1. What concrete bottleneck, correctness constraint, or programming task is
   this report addressing?
2. What is one invariant that must remain true?
3. Trace one unit of data or one control event from producer to consumer.
4. Which claims are architecture-specific, and which form a durable mental
   model across Tenstorrent generations?

## Source and delta

- **Original source:** [`tech_reports/YoloV4-TTNN/yolov4.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/YoloV4-TTNN/yolov4.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
