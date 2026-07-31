<!-- rewrite-status: seed -->
# TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md"><code>tech_reports/ttnn/ttnn.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/ttnn.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 35 |
| Section headings | 6 |
| Fenced code examples | 0 |
| Markdown images | 5 |

### Section outline

- Roadmap
- High Level Structure Overview
- ML Framework
- OP Library
- OP Infra
- TT-NN Runtime

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Source and delta

- **Original source:** [`tech_reports/ttnn/ttnn.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/ttnn.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
