<!-- rewrite-status: seed -->
# New model bring-up in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md"><code>tech_reports/ttnn/TTNN-model-bringup.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/TTNN-model-bringup.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 182 |
| Section headings | 17 |
| Fenced code examples | 7 |
| Markdown images | 11 |

### Section outline

- 1. Overview
- 2. New model bringup flow in TTNN
  - 2.1 Recommended steps for model bringup
  - 2.2 Create a model Card
  - 2.3 Using the reference model in Torch
  - 2.4 Create the torch model graph
  - 2.5 Extract the model summary
  - 2.6 Create issues for potential bugs or missing TTNN ops
- 3. End to end model in TTNN
- 3.1 Create TTNN unit tests per module and per op
- 3.2 PCC
- 3.3 Optimization
- 4.  End to end model performance
  - 4.1 Performance Sheet
  - 4.2 Visualizer
  - 4.3 Trace and 2cq
- 5. Conclusion

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
