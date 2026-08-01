<!-- rewrite-status: improved-draft -->
# TT-Fabric Architecture Specification

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md"><code>tech_reports/TT-Fabric/TT-Fabric-Architecture.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

TT-Fabric extends NoC-style addressed operations across Ethernet hops, so one monolithic
“send” abstraction would conflate four different constraints. Hardware TT-link supplies
Layer 2 delivery using a 16-byte header and Go-Back-N ARQ; TT-routing chooses NoC versus
Ethernet hops from `MeshId`/`DeviceId` and source routes; TT-transport supplies ordered
virtual-channel buffers and flow control; TT-session exposes independent asynchronous
packets whose headers contain the final memory address. Synchronous producer/consumer
semantics are added by sockets over those writes, not assumed by the packet layer. A
separate PCIe control plane launches, monitors, and can reconfigure the data plane, so
a broken data route does not remove the mechanism needed to diagnose it.

### How work and data move

A worker injects a packet with destination mesh/device, final NoC command/address, a
routing plane, and an intra-mesh source route. Each fabric router consumes the next
route action: intra-chip forwarding uses NoC and inter-chip forwarding uses TT-link
Ethernet. Within one mesh the source route remains unchanged; at a mesh boundary, the
entry router replaces it with a route to the final device or the next exit node selected
by the L1 inter-mesh table. Sender channels distinguish locally injected from
pass-through/turning traffic, while a receiver channel can consume locally, forward, or
both for multicast. The pinned transport provides one user-visible bidirectional VC per
router, plus a smaller dedicated control VC, and serializes sources sharing a VC while
preserving order.

Parallel links are isolated into deterministic routing planes: the source cites four
per direction on Wormhole and two on Blackhole, with possible additional Blackhole
up/down links. A client selects a plane and packets do not cross between planes. This
gains bandwidth without allowing hop-by-hop load balancing to reorder traffic, at the
cost of potential imbalance when one plane is hotter.

### What must never break

TT-link may expose a packet upward only after its sequence protocol guarantees delivery;
Layer 3 must preserve destination and valid source-route progress at every hop. Packets
on the same VC must remain ordered, and control traffic must retain its reserved VC so
data congestion cannot prevent recovery. Injection and turning channels must obey
bubble flow control—on a ring/torus, a packet enters only when at least two first-hop
slots are free. Intra-mesh routes follow dimension order (the source's example is X then
Y) to break cyclic dependencies. This does not prove inter-mesh deadlock freedom around
sparse exit nodes; the report explicitly points to hierarchical VCs/switches as further
mitigation. The architecture must provide a bounded way to detect or recover a packet
that cannot progress rather than let it consume buffers forever. The pinned report
proposes TTL, router-head timeout, draining, and control-plane notification for that
purpose in its Roadmap section; those are design requirements there, not evidence that
the pinned implementation already deploys them.

### Where the report makes it concrete

The L0 table stores a source route for every device (up to the report's 256-device mesh
model); the L1 table chooses an exit node among up to 1024 meshes. In a 1-D line VC, two
sender channels feed one 16-slot receiver channel in the illustrated configuration; a
2-D mesh needs four sender channels because traffic can arrive from three neighbors or
a local worker. These slot counts are examples constrained by router SRAM, not protocol
constants. The architectural overview lists pause/flush/resume, routing-table
reconfiguration, and removal of unhealthy mesh rows/columns as possible control-plane
actions. Detailed Ethernet Fallback Channels, TTL, timeout recovery, and the fabric
model appear under the report's explicit Roadmap heading. Automatic rerouting is also
described earlier as TT-routing behavior, so the document is internally ambiguous about
implementation status; a learner must check the target build rather than turn either
passage into a universal deployment claim.

### How the decision is tested

Generate coordinate-stamped unicast and multicast traffic across NoC-only, one-hop
Ethernet, multi-hop intra-mesh, and inter-mesh paths; compare every hop against the
serialized L0/L1 tables and verify same-VC order. Saturate local injection and turning
channels on rings and toruses, checking the two-free-slot bubble rule and proving X-then-Y
routes drain under the cyclic pattern used in the report. On a build that advertises
automatic rerouting, fail one parallel link and verify the documented pause followed by
reduced-rate recovery or an explicit no-route notification. Test fallback-channel
assignment only when that Roadmap mechanism is implemented. Corrupt a route in a model
where TTL/timeout is implemented and verify drop/drain/report semantics. The pinned
document mixes architecture, current support, and roadmap; test results must label
which class each mechanism belongs to before claiming end-to-end reliability.

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
