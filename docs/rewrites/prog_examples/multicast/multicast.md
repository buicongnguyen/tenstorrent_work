<!-- rewrite-status: seed -->
# **Data Multicasting**

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md"><code>tech_reports/prog_examples/multicast/multicast.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/prog_examples/multicast/multicast.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 458 |
| Section headings | 25 |
| Fenced code examples | 31 |
| Markdown images | 0 |

### Section outline

- **1. Introduction**
- **2. Host-Side Workflow in `multicast.cpp`**
  - **2.1 Defining Logical vs. Physical Core Coordinates**
  - **2.2 Allocating DRAM Buffers and Storing the Tile**
  - **2.3 Circular Buffers for Inbound and Outbound Data**
  - **2.4 Semaphores for Synchronization**
  - **2.5 Kernel Registration and Argument Setting**
- **3. Coordinator Core Workflow in `coordinator_kernel.cpp`**
  - **3.1 Parsing Runtime Arguments**
  - **3.2 Buffer Setup and Tile Read from DRAM**
  - **3.3 DPRINTing a Tile Slice**
  - **3.4 Preparing Semaphores**
  - **3.5 Waiting for Receiver Readiness**
  - **3.6 Multicasting the Tile**
  - **3.7 Signaling Multicast Completion**
  - **3.8 Finalizing the Multicast Operation**
- **4. Receiver Core Workflow in `inbound_kernel.cpp`**
  - **4.1 Parsing Runtime Arguments**
  - **4.2 Buffer Setup for Receiving Tile**
  - **4.3 Preparing Semaphores**
  - **4.4 Notifying Coordinator of Readiness**
  - **4.5 Receiving the Multicasted Tile**
  - **4.6 DPRINTing a Tile Slice or Whole**
  - **4.7 Completing Tile Processing and Acknowledgment**
- … 1 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The example demonstrates one coordinator sending identical data to a group of
    receiver cores through a NoC multicast, replacing repeated point-to-point transfers
    while making receiver readiness and completion explicit. The optimization is valid
    only when all receivers need the same payload.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every target must reserve valid destination storage before the coordinator writes,
    and no receiver may publish the page before arrival. The sender may reuse its source
    only after the required completion/acknowledgement contract is satisfied.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host creates coordinator/receiver kernels, CBs, ranges, and semaphores →
    receivers reserve pages and signal readiness → the coordinator issues one multicast
    to the physical destination rectangle → transport completes → receivers
    signal/publish arrival → local consumers process their copies.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** NoC multicast APIs, coordinate conversion, rectangular range
    restrictions, semaphore placement, alignment, and destination encoding depend on
    TT-Metal and the chip topology.

    **Durable model.** Use multicast for genuine one-to-many reuse, prove all
    destinations are ready, distinguish transport completion from local publication, and
    compare saved source traffic with synchronization and fanout cost.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/multicast/multicast.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/multicast/multicast.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
