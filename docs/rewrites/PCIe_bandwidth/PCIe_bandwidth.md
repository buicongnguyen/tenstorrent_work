<!-- rewrite-status: seed -->
# PCIe Bandwidth Measurement

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md"><code>tech_reports/PCIe_bandwidth/PCIe_bandwidth.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 111 |
| Section headings | 12 |
| Fenced code examples | 2 |
| Markdown images | 0 |

### Section outline

- Table of Contents
- Host-Side Tests (WriteShard / ReadShard)
  - Host Write (H2D) — p150 / Blackhole
  - Host Read (D2H) — p150 / Blackhole
- Device-Side Tests (Kernel NOC)
  - Test Setup
  - Kernel Structure
  - Sweep Parameters
  - Device Read Bandwidth Sweep
  - Device Write Bandwidth Sweep
- Running the Tests
- Notes

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report measures host-to-device and device-to-host PCIe throughput through both
    host-side shard APIs and device-side NoC kernels, separating PCIe limits from
    on-device placement and transfer overhead. It therefore requires controlled direction,
    size, synchronization, and placement.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The timed interval must move a known byte count in one declared direction, all
    asynchronous work must complete before the timer stops, source and destination
    buffers must remain valid, and readback must verify that the expected bytes arrived.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    For a write, a pinned host buffer feeds the runtime transfer → PCIe carries data to
    device DRAM/L1 shards → optional device NoC movement distributes it → a completion
    boundary makes it consumable. The read path reverses those stages before host
    validation.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** PCIe generation/width, host platform, DMA granularity, device
    bank topology, sharding API, transfer size, and measured GB/s are machine- and
    snapshot-specific.

    **Durable model.** Report payload bytes and direction, warm and synchronize
    consistently, sweep transfer sizes, separate link throughput from device
    redistribution, validate data, and compare against the negotiated-link ceiling
    rather than a marketing maximum.

## Source and delta

- **Original source:** [`tech_reports/PCIe_bandwidth/PCIe_bandwidth.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
