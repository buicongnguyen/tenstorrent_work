<!-- rewrite-status: seed -->
# Basic Ethernet Multichip

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md"><code>tech_reports/EthernetMultichip/BasicEthernetGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/EthernetMultichip/BasicEthernetGuide.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 867 |
| Section headings | 43 |
| Fenced code examples | 18 |
| Markdown images | 19 |

### Section outline

- Ethernet Core Type: Ethernet
- Ethernet Core (ERISC)
- Ethernet Link
  - Link Health and Retraining
- Ethernet and Cluster Connectivity
  - Topology and connectivity
    - N300
    - T3000
    - Galaxy
  - Ethernet routing firmware
- Sending Data Over The Ethernet Link
  - Ethernet Writes Compared To On Chip NoC Writes
  - Ethernet Transaction Command Queues
  - End-to-End Flow Control
- Bidirectional Bandwidth - By Packet Size and Max Channel Count
- Bidirectional Bandwidth -By Packet Size and Fixed Channel Count
- Ring Ping Latency
- Single Ethernet Link Round-Trip Latency
- Multichip Programming Challenges
  - Tensor And Semaphore Lifetime and Address Resolution Problems
  - Asynchronous Program Start
  - Asynchronous Program Completion Problem
  - Fixed Datapath Resources Problem (Through ERISC)
    - Static Routing
- … 19 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report explains how to move data between chips through active Ethernet cores and
    links, including topology discovery, packet/channel behavior, latency and bandwidth,
    and the extra coordination required when a NoC address is no longer enough.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The sender may reuse storage only after the protocol says the receiver has accepted
    the data; both endpoints must agree on link peer, channel, packet size, destination,
    and flow-control state. A local NoC barrier alone cannot acknowledge remote
    consumption.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A worker or host prepares a source buffer → local NoC traffic reaches the sending
    Ethernet core → ERISC packetizes and transmits on the selected channel/link → the
    peer Ethernet core receives and validates flow-control state → remote NoC movement
    places bytes at the destination → a semaphore/message makes them visible to the
    consumer.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Ethernet-core types, channel count, packet-size curves, link
    bandwidth, physical topology, ERISC firmware, and measured latency are device- and
    snapshot-specific.

    **Durable model.** Separate local transport, link transport, routing, flow control,
    and application ownership; measure both small-message latency and sustained
    bandwidth; and design explicit end-to-end completion rather than assuming link
    delivery equals consumption.

## Source and delta

- **Original source:** [`tech_reports/EthernetMultichip/BasicEthernetGuide.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/EthernetMultichip/BasicEthernetGuide.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
