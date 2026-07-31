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
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

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

1. **Architecture pressure.** Define socket direction, endpoint ownership, transfer mode,
   ring depth, backing memory, producer/consumer rates, and host/device failure/teardown
   semantics for the intended streaming workload.

2. **Flow to make explicit.** Draw slot reservation, payload fill/reference, publication,
   PCIe/DMA transfer, remote availability, consumer read, completion, credit return,
   wraparound, and endpoint close for both H2D and D2H.

3. **Invariant to prove.** Prove a producer never overwrites an unread slot, a consumer
   never reads an unpublished slot, credits/indices describe the same ring state, and
   endpoints/buffers outlive every in-flight transfer.

4. **TT-Metal evidence to connect.** Connect the design to `H2DSocket`, `D2HSocket`,
   `MeshSocket`, and `tt_metal/api/tt-metalium/experimental/sockets/`, including the
   report's transfer-mode and flow-control APIs.

5. **Experiment and expected observation.** Run producer faster than consumer and then
   reverse the rates across multiple wraparounds; expected result: bounded backpressure
   prevents corruption/underrun and steady-state throughput separates from
   connection/fill/drain latency.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md):

- **Direction and ownership.** `H2DSocket` and `D2HSocket` make PCIe transfer direction
  explicit. `MeshSocket` is named only as the device-to-device contrast and is outside
  this report's scope; do not import its TT-Fabric behavior into the host/device socket
  model.

- **Flow control.** The APIs under `tt_metal/api/tt-metalium/experimental/sockets/`
  define connection, send/receive, and completion semantics. Match credits or
  acknowledgements with buffer reuse; host enqueue completion alone does not prove a
  remote consumer finished.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
