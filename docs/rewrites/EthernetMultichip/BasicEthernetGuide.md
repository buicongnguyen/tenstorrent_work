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

## Source and delta

- **Original source:** [`tech_reports/EthernetMultichip/BasicEthernetGuide.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/EthernetMultichip/BasicEthernetGuide.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
