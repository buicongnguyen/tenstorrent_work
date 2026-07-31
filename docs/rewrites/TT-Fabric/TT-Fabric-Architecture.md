<!-- rewrite-status: seed -->
# TT-Fabric Architecture Specification

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md"><code>tech_reports/TT-Fabric/TT-Fabric-Architecture.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/TT-Fabric/TT-Fabric-Architecture.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1026 |
| Section headings | 38 |
| Fenced code examples | 9 |
| Markdown images | 10 |

### Section outline

- Table of Contents
- 1.1 Operational Structure <a id="structure"></a>
  - 1.1.1 Data Plane <a id="dataplane"></a>
  - 1.1.2 Control Plane <a id="controlplane"></a>
- 1.2 Some Additional Notes <a id="notes"></a>
- 2.1 Layers 1, 2 <a id="layer_12"></a>
- 2.2 TT-routing (Layer 3) <a id="layer_3"></a>
  - 2.2.1 Routing Tables <a id="routing_tables"></a>
    - 2.2.1.1 L0 Routing (Intra-Mesh a.k.a Scale-up) <a id="intramesh"></a>
    - 2.2.1.2 L1 Routing (Inter-Mesh a.k.a Scale-out) <a id="intermesh"></a>
  - 2.2.2 Routing Planes <a id="routing_planes"></a>
- 2.3 TT-transport (Layer 4) <a id="layer_4"></a>
  - 2.3.1 Bubble Flow Control <a id="dvc"></a>
  - 2.3.2 Control Virtual Channel <a id="cvc"></a>
- 2.4 TT-session (Layer 5) <a id="layer_5"></a>
- 3.1 Buffers and Virtual Channels <a id="rb_per_vc"></a>
  - 3.1.1 1D Line Virtual Channel <a id="1dlvc"></a>
    - 3.1.1.1 Dataflow between two fabric routers over Ethernet <a id="ethflow"></a>
    - 3.1.1.2 Dataflow between two fabric routers over NOC <a id="nocflow"></a>
  - 3.1.2 2D Mesh Virtual Channel <a id="2dmvc"></a>
- Fabric Node Model
- Fabric APIs and Topologies
- Fabric and NoC Level Commands
- 6.1 Dimension Ordered Routing <a id="dim_order_routing"></a>
- … 14 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Source and delta

- **Original source:** [`tech_reports/TT-Fabric/TT-Fabric-Architecture.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Fabric/TT-Fabric-Architecture.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
