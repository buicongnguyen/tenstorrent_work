<!-- rewrite-status: seed -->
# TT-NN Graph Tracing

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md"><code>tech_reports/ttnn/graph-tracing.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/graph-tracing.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 938 |
| Section headings | 48 |
| Fenced code examples | 31 |
| Markdown images | 2 |

### Section outline

- Table of Contents
- Quick Start
  - Python (5 lines)
  - C++
  - Save to File (for ttnn-visualizer)
- Core Concepts
  - What Gets Captured
  - Two-Phase Architecture
  - How Operations Are Tracked
  - FastOperation vs Operation
  - Tensor Connectivity
  - Run Modes
- Basic Usage
  - Extracting Operation Durations
  - Tracking Memory Usage
  - Generating Visualizations
- Saving Reports
  - Save Complete Report to File
  - Import into Visualizer Database
    - Import Behavior
- Advanced Features
  - Stack Trace Capture
  - Buffer Page Capture
  - Reducing Capture Overhead
- … 24 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md). During
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

- **Original source:** [`tech_reports/ttnn/graph-tracing.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/graph-tracing.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
