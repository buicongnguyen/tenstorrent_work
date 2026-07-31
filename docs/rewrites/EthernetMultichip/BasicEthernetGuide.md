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
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

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

1. **Architecture pressure.** Separate local NoC movement, ERISC/channel service, physical
   Ethernet link behavior, remote ejection, and application acknowledgement. Quantify
   small-packet latency and sustained bandwidth as different regimes.

2. **Flow to make explicit.** Draw one packet from a worker/source buffer through local NoC,
   sending Ethernet core, channel packetization, physical link, peer Ethernet core, remote
   NoC, destination storage, and consumer completion/credit.

3. **Invariant to prove.** Prove that both endpoints agree on peer link, channel, packet
   size, route, destination, and flow-control state and that source storage is not reused
   merely because the local NoC write completed.

4. **TT-Metal evidence to connect.** Connect the path to `run_routing()`,
   `eth/dataflow_api.hpp`, `dataflow_api.hpp`, `eth_send_packet()`, and the source report's
   packet-size/channel-count and ring/round-trip measurements.

5. **Experiment and expected observation.** Sweep packet size and channel count on one fixed
   link in both directions; expected result: small messages expose startup latency while
   larger concurrent packets approach the link bandwidth until channel or routing contention
   saturates.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md):

- **Route establishment.** `run_routing()` prepares the host/runtime routing state
  before Ethernet kernels exchange packets. The route, channel assignment, peer
  coordinates, packet size, and packet count must agree at both endpoints before
  throughput or round-trip timing is meaningful.

- **Packet movement.** Ethernet kernels include `eth/dataflow_api.hpp`, while
  worker-side NoC movement uses `dataflow_api.hpp`; `eth_send_packet()` belongs to the
  Ethernet packet path. Keep those address spaces and completion rules separate when
  tracing a ring hop or round trip.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
