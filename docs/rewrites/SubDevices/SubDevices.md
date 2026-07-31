<!-- rewrite-status: seed -->
# Sub-Devices

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md"><code>tech_reports/SubDevices/SubDevices.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/SubDevices/SubDevices.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 234 |
| Section headings | 12 |
| Fenced code examples | 1 |
| Markdown images | 2 |

### Section outline

  - Note that this feature is still under active development and features/apis may change.
- Contents
- Introduction
- 1. Sub-Devices
  - 1.1 Sub-Devices and Sub-Device Managers
  - 1.2 Allocators
  - 1.3 Programs
  - 1.4 Synchronization
- 2. Global Semaphores
- 3. Global Circular Buffers
  - 3.1 Host APIs
  - 3.2 Kernel APIs

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    Sub-devices partition one chip's cores and dispatch resources so independent
    workloads can be launched and synchronized at a narrower scope. Global semaphores
    and circular buffers then provide deliberate coordination across those partitions
    when isolation alone is insufficient.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Sub-device core ranges and owned resources must not overlap illegally; commands
    targeted to one sub-device must not consume another's local resources.
    Cross-sub-device state becomes visible only through an explicitly shared object and matching
    synchronization protocol.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host defines disjoint core sets → the runtime creates sub-device managers/queues
    → a command is targeted to one partition → its kernels use local CBs and cores → a
    global semaphore or global CB carries the required cross-partition dependency →
    completion can be waited at sub-device or device scope.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Sub-device APIs, dispatch-core allocation, permitted core
    ranges, global-object implementation, and synchronization capabilities depend on
    device and runtime version.

    **Durable model.** Partition resources to reduce interference and synchronization
    scope, make ownership exclusive by default, share only named channels, and match
    every cross-partition data transfer with a happens-before edge.

## Source and delta

- **Original source:** [`tech_reports/SubDevices/SubDevices.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/SubDevices/SubDevices.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
