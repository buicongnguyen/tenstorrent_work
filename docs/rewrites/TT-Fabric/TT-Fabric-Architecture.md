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

1. **Architecture pressure.** Explain separately the data/control planes and routing,
   transport, and session problems: route selection, deadlock/flow control, packet
   delivery/order, API semantics, and topology-specific resource allocation.

2. **Flow to make explicit.** Draw a command/payload from source NoC through local fabric
   router ring/virtual channel, routing-table and dimension-order decision, Ethernet/NoC hop
   with bubble/credit state, destination ejection, session completion, and buffer
   reclamation.

3. **Invariant to prove.** Prove channel dependencies remain deadlock-safe, a router
   forwards only with required downstream space, packet metadata/payload survive every hop,
   and required delivery/order is acknowledged at the destination session.

4. **TT-Metal evidence to connect.** Connect the report to `FabricNodeId`, `{MeshId,
   ChipId}`, routing tables/planes, per-VC buffers, bubble flow control, and topology APIs
   under `tt_metal/fabric/hw/inc/linear|mesh/api.h`.

5. **Experiment and expected observation.** Construct two competing flows that share a
   link/VC and vary available bubble space; expected result: backpressure prevents
   overwrite, dimension-ordered routing avoids cyclic wait under stated assumptions, and
   congestion appears on the predicted hop.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    TT-Fabric supplies routed, flow-controlled communication across chips and meshes.
    The report separates data/control planes and routing, transport, and session
    responsibilities so packet forwarding, congestion control, reliability, and
    application semantics are not collapsed into one firmware path.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A router may forward only when the next virtual channel has sufficient credit/bubble
    space, and routing choices must remain deadlock-safe. Packet metadata, payload, and
    required ordering/reliability must survive every hop until the destination session
    accepts them.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A source worker issues a fabric/NoC command → the local router places a packet in
    the selected virtual channel → dimension-ordered routing selects each hop → Ethernet
    or NoC links move it under credit/bubble flow control → the destination router
    ejects it to local NoC/storage → session completion reaches the consumer.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Router-core placement, ring-buffer sizes, virtual-channel
    mapping, packet formats, routing tables, topology, Ethernet behavior, and command
    encodings are device/firmware specific.

    **Durable model.** Separate routing from transport and session semantics, use
    virtual channels and an acyclic routing policy to prevent deadlock, apply
    backpressure before overflow, and define completion at the final consumer boundary.

## Source and delta

- **Original source:** [`tech_reports/TT-Fabric/TT-Fabric-Architecture.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Fabric/TT-Fabric-Architecture.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
