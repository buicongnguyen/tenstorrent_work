<!-- rewrite-status: seed -->
# Advanced Performance Optimizations for Models

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md"><code>tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 613 |
| Section headings | 20 |
| Fenced code examples | 7 |
| Markdown images | 8 |

### Section outline

- Contents
- Introduction
- 1. Metal Trace
  - 1.1 Overview
  - 1.2 APIs
  - 1.3 Programming Examples
    - 1.3.1 Trace With Persistent DRAM Input
    - 1.3.2 Trace with Non-Persistent L1 Input
- 2. Multiple Command Queues
  - 2.1 Overview
  - 2.2 APIs
  - 2.3 Programming Examples
    - 2.3.1 Opening and Configuring a Mesh Device
    - 2.3.2 Ops and Output Readback on CQ0, Input Writes on CQ1
    - 2.3.3 Ops on CQ0, Input Writes and Output Readback on CQ1
- 3. Combining Trace and Multiple Command Queues
  - 3.1 Overview
  - 3.2 APIs
  - 3.3 Programming Examples
    - 3.3.1 Trace with Persistent DRAM Input

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md). During
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

- **Original source:** [`tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
