<!-- rewrite-status: improved-draft -->
# TT-Fabric Architecture Specification

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md"><code>tech_reports/TT-Fabric/TT-Fabric-Architecture.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to explain separately the data/control planes and
routing, transport, and session problems: route selection, deadlock/flow control, packet
delivery/order, API semantics, and topology-specific resource allocation.

### How work and data move

The complete path is a command/payload from source NoC through local fabric router
ring/virtual channel, routing-table and dimension-order decision, Ethernet/NoC hop with
bubble/credit state, destination ejection, session completion, and buffer reclamation.

### What must never break

The non-negotiable invariant is that channel dependencies remain deadlock-safe, a router
forwards only with required downstream space, packet metadata/payload survive every hop,
and required delivery/order is acknowledged at the destination session.

### Where the report makes it concrete

The report makes the decision concrete by connecting the report to `FabricNodeId`,
`{MeshId, ChipId}`, routing tables/planes, per-VC buffers, bubble flow control, and
topology APIs under `tt_metal/fabric/hw/inc/linear|mesh/api.h`.

### How the decision is tested

The controlled procedure is to construct two competing flows that share a link/VC and
vary available bubble space. **Expected observation:** backpressure prevents
overwrite, dimension-ordered routing avoids cyclic wait under stated assumptions, and
congestion appears on the predicted hop.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md):

- **Address and route.** `FabricNodeId` and `{MeshId, ChipId}` identify endpoints;
  routing tables, planes, and topology APIs under
  `tt_metal/fabric/hw/inc/linear|mesh/api.h` select the legal next hop. Verify
  coordinate and topology assumptions before packet injection.

- **Per-hop safety.** Per-virtual-channel buffers and bubble flow control prevent
  overwrite and cyclic waiting under the report's routing assumptions. Trace
  reservation, forward, credit/bubble return, destination ejection, and completion
  before reclaiming the source packet buffer.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
