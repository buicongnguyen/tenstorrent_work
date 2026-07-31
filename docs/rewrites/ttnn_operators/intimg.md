<!-- rewrite-status: seed -->
# Tenstorrent `tt-metal`: Integral Image (Summed-Area Table) Kernels — High-Level Guide (Axis Spec: **[B, W, H, C]**)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md"><code>tech_reports/ttnn_operators/intimg.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn_operators/intimg.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 403 |
| Section headings | 29 |
| Fenced code examples | 9 |
| Markdown images | 0 |

### Section outline

- 0) TL;DR — mental model (with **[B, W, H, C]**)
- 1) What the kernel computes (the math)
- 2) Key vocabulary (TT-metal essentials)
- 3) Global tiling layout
- 4) Reader kernel — orchestrating input & initializing state
  - 4.1 Functions and intent
  - 4.2 Control flow
- 5) Compute kernel — turning tiles into an integral image
  - 5.1 W cumulative sum: `cumsum_cube_axis_2(...)`
  - 5.2 W propagation across blocks: `propagate_tile_into_cube(...)`
  - 5.3 H cumulative sum within tile: `cumsum_cube_axis_3(...)`
  - 5.4 H propagation (add from the upper block): `get_and_propagate_adder_cube(...)`
  - 5.5 Putting it together: `perform_intimg_along_row_chunk(...)`
- 6) Writer kernel — exporting results and feeding back vertical context
  - 6.1 Basic export: `output_block(...)`
  - 6.2 Import the upper block & broadcast last row (H propagation)
- 7) Axis mapping cheat-sheet (coherent with **[B, W, H, C]**)
- 8) Correctness sketch vs. classic formula (with **[1, W, H, C]**)
- 9) Performance & robustness notes
- 10) Walk‑through on a tiny example
- 11) Signals & buffers (by role)
- 12) Diagrams
  - a) 📐 What’s an Integral Image (toy 4×4)
  - b) ↕️↔️ Two-Pass View (cumsum over height then width)
- … 5 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md). During
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

- **Original source:** [`tech_reports/ttnn_operators/intimg.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn_operators/intimg.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
