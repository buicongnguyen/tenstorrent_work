<!-- rewrite-status: seed -->
# H2D / D2H PCIe Socket: Technical Report

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md"><code>tech_reports/TT-Distributed/HDSocketsModel.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/TT-Distributed/HDSocketsModel.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 791 |
| Section headings | 46 |
| Fenced code examples | 10 |
| Markdown images | 41 |

### Section outline

- Table of Contents
- 1. Background: H2D / D2H PCIe Sockets
  - 1.1 Blackhole Hardware Facts Relevant to This Guide
  - 1.2 Training & Inference Use Cases for PCIe Sockets
- 2. Transfer Modes and Flow Control
  - 2.1 H2D: HOST\_PUSH
  - 2.2 H2D: DEVICE\_PULL
  - 2.3 D2H
  - 2.4 Flow control (shared)
- 3. API Walkthrough
  - 3.1 Host Side: Setup
  - 3.2 Device Side: Initialization
  - 3.3 D2H Kernel: `pcie_socket_sender.cpp`
  - 3.4 H2D HOST\_PUSH Kernel: `h2d_throughput_host_push.cpp`
  - 3.5 H2D DEVICE\_PULL Kernel: `h2d_throughput_device_pull.cpp`
- 4. Performance Results
  - Hardware Overview: PCIe Link Asymmetry
  - 4.1 Galaxy Rev A/B (Gen 4 PCIe)
    - 4.1.1 D2H Throughput
    - 4.1.2 D2H Latency
    - 4.1.3 H2D Throughput
    - 4.1.4 H2D Latency
    - 4.1.5 Multi-Chip Throughput
  - 4.2 Galaxy Rev C (Gen 5 PCIe)
- … 22 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report designs high-throughput host-to-device and device-to-host PCIe sockets as
    long-lived streams rather than isolated tensor copies. Transfer modes, ring buffers,
    and flow control must support multiple hosts/devices without overwrite or
    starvation.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Producer and consumer indices/credits must describe the same ring state: a producer
    cannot overwrite an unread slot, a consumer cannot read an unpublished slot, and
    backing buffers plus socket endpoints must outlive all in-flight transfers.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A producer reserves a socket/ring slot → fills or points it at payload → publishes
    availability → PCIe/DMA moves data across the host-device boundary → the consumer
    waits on the matching state, reads the payload, and returns credit → the producer
    may reuse the slot.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Socket APIs, transfer modes, queue depths, buffer placement,
    PCIe topology, synchronization implementation, and reported bandwidth/latency are
    snapshot-specific.

    **Durable model.** Use bounded queues with explicit backpressure, separate
    reservation from publication and reclamation, preserve endpoint lifetime, batch
    transfers enough to amortize setup, and measure steady-state streaming independently
    from startup.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/HDSocketsModel.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/HDSocketsModel.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
