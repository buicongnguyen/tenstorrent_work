<!-- rewrite-status: seed -->
# TT-NN Comparison Mode

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md"><code>tech_reports/ttnn/comparison-mode.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/comparison-mode.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 24 |
| Section headings | 1 |
| Fenced code examples | 1 |
| Markdown images | 0 |

### Section outline

- How to Use it?

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    Comparison mode automatically runs or obtains a golden implementation for TT-NN
    operations and reports numerical differences, shortening the search from an
    incorrect model output to the first operation whose contract diverges.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Golden and device executions must see the same logical inputs, parameters,
    broadcasting, shape semantics, and operation order. The configured tolerance/PCC
    threshold must reflect the expected numerical format rather than being loosened
    until a failure disappears.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A TT-NN operation call is intercepted → comparison infrastructure records its
    inputs/configuration → a golden path computes the reference → the device operation
    executes → outputs are converted to comparable form → error/PCC is reported with
    operation identity → the first divergence guides debugging.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Enablement APIs, golden-function coverage, report format,
    supported operations, conversion behavior, and default thresholds depend on the
    TT-NN release.

    **Durable model.** Use differential testing close to operation boundaries, keep
    inputs identical, select justified metrics, preserve the first failing context, and
    treat automatic comparison as localization evidence rather than proof of root cause.

## Source and delta

- **Original source:** [`tech_reports/ttnn/comparison-mode.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/comparison-mode.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
