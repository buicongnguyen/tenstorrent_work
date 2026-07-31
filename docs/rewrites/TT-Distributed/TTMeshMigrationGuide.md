<!-- rewrite-status: seed -->
# TTNN Device to MeshDevice Migration Guide

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md"><code>tech_reports/TT-Distributed/TTMeshMigrationGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/TT-Distributed/TTMeshMigrationGuide.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 143 |
| Section headings | 9 |
| Fenced code examples | 4 |
| Markdown images | 0 |

### Section outline

- Limitations
- Migration Steps (Applicable to C++ Users Only)
  - 1. Update Device Management
  - 2. Remove Device/IDevice
  - 3. Remove command_queue() calls
  - 4. Event synchronization
  - 5. Manual calls to Metal APIs
  - Possible issues
    - OwnedStorage vs MultiDeviceHostStorage

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The guide migrates C++ code written for a single `Device` to `MeshDevice` and
    mesh-aware buffers/queues while preserving single-device behavior first, then enabling
    multi-device distribution deliberately. The first milestone is compatibility, not
    immediate scaling.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A one-device mesh must reproduce the original program's tensor contents, addresses
    within the new abstraction, operation order, completion semantics, and resource
    lifetime. Distribution must not be introduced implicitly during a mechanical API
    migration.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Original device creation becomes a one-device mesh open → device tensors become mesh
    tensors/buffers with an explicit mapper → operations submit through mesh-aware APIs
    → results are composed/read back → synchronization and close release all mesh-owned
    resources.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Renamed APIs, unsupported features, C++ migration steps,
    queue types, and temporary limitations apply to the documented TT-NN revision.

    **Durable model.** Migrate through a compatibility configuration, keep behavior
    parity tests, change construction/ownership before adding distribution, and make
    mapping/composition explicit so scaling is an intentional second step.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/TTMeshMigrationGuide.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/TTMeshMigrationGuide.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
