<!-- rewrite-status: seed -->
# Deprecating `DPRINT` in favor of `DEVICE_PRINT`

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md"><code>tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 250 |
| Section headings | 12 |
| Fenced code examples | 13 |
| Markdown images | 0 |

### Section outline

- 1. Why we changed it
- 2. Deprecation plan
  - Phase 1 – Opt‑in (completed)
  - Phase 2 – Deprecation window (completed)
  - Phase 3 – Alias and cleanup (completed)
- 3. Usage examples – `DPRINT` vs `DEVICE_PRINT`
  - 3.1 Basic value printing
  - 3.2 Number formatting
  - 3.3 Enum printing
  - 3.4 Tile / `TileSlice` printing
  - 3.5 Core-specific prints
  - 3.6 Enabling `DEVICE_PRINT` (historical — transition only)

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md). During
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

- **Original source:** [`tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
