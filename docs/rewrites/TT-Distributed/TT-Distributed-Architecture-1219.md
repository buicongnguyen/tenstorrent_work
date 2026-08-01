<!-- rewrite-status: improved-draft -->
# TT-Metalium Distributed

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md"><code>tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

This pinned document is an architecture specification with sections marked for V1 and
V1.2, so its proposed structures must not be presented as timeless implemented APIs.
Its governing constraint is to extend the single-device `Device`/`Program` model to a
virtual mesh without making TT-NN create and synchronize one object per chip. A
`MeshDevice` therefore combines a logical coordinate query layer, lock-step allocator,
and virtual fast-dispatch interfaces; physical devices remain hidden. `MeshBuffer`
virtualizes `(device_y, device_x, bank_id, address)`, and `MeshWorkload` preserves the
useful hierarchy: first optimize a `Program` for one device, then place programs or
vary runtime arguments over `LogicalDeviceRange`s.

### How work and data move

A user obtains a `DeviceHandle` from `CreateMeshDevice`, then a VCQ via
`GetCommandQueue(device, cq_id)`. A replicated or sharded `MeshBuffer::create` asks the
mesh allocator for one lock-step address and combines a mesh-level config with
`DeviceLocalBufferConfig` (`page_size`, `BufferType`, local layout and optional
`ShardSpecBuffer`). A homogeneous operation inserts one `Program` over
`MaxDeviceRange`; heterogeneous work uses disjoint `LogicalDeviceRange`s, or preserves
one broadcastable program and calls distributed `SetRuntimeArgs` per coordinate. The
VCQ lowers broadcastable commands through TT-Fabric and unicasts differing runtime
arguments.

The forward dispatch path described in the source is credit-coupled:
`Mcast Prefetch_h` feeds a Packetizer, fabric routers deliver to Depacketizers, a DRAM
spill buffer prevents a full L1 CB from backpressuring shared fabric resources, and
`Mcast Prefetch_d` supplies the Dispatcher. Broadcast/unicast transitions require
ordering—either counterpart event commands on a type toggle or transaction IDs read by
the Dispatcher. Completion returns through a per-mesh Event Notification Table or a
device Aggregator/Event Notification Queue, avoiding one host reader thread per device.

### What must never break

Lock-step allocation means the same buffer address and identical SubDevice
configuration must hold across the virtual mesh; a workload cannot target an allocation
that violates that assumption. Program `LogicalDeviceRange`s must be in bounds and
disjoint where programs differ, and one program cannot span multiple SubDevices in the
described constraint. Consecutive mesh workloads may overlap on different devices or
SubDevices, so order exists only where a `MeshEvent` or same-SubDevice dependency makes
it explicit. Broadcast and unicast commands feeding one Dispatcher must retain host
enqueue order. Finally `MeshEventSynchronize`/`Finish` may report completion only after
every device in the event's `device_range` has acknowledged the intended `event_id`.

### Where the report makes it concrete

The data-parallel matmul example wraps `create_program` with
`InsertProgramInMeshWorkload`; the all-gather example keeps one Program but calls
`update_runtime_args_for_device_coord` for each logical coordinate. Event APIs
distinguish mesh-local `EnqueueRecordMeshEvent` from host-visible
`EnqueueRecordMeshEventToHost`; `BeginMeshTraceCapture`, `EndMeshTraceCapture`, and
`EnqueueMeshTrace` cache fast-dispatch commands in distributed trace regions. These
interfaces expose the main benefit—broadcast common configuration once—while retaining
the tradeoff that spatially heterogeneous workloads can allocate unused buffers on
devices and require more host construction.

### How the decision is tested

On a two-by-two mesh, allocate replicated and sharded buffers and verify equal physical
addresses plus correct coordinate-to-shard contents. Submit (1) one broadcast Program,
(2) the same Program with coordinate-stamped runtime args, and (3) two Programs on
disjoint ranges; confirm exactly-once placement and permitted overlap. Interleave
broadcast and unicast commands that touch the same buffer to test the chosen ordering
mechanism, then stall one receiver until its spill-buffer credits reach zero: unrelated
fabric paths must still progress. Record a host-visible `MeshEvent` and ensure it does
not complete early; compare Event Notification Table polling with aggregation if both
exist. Because much of the pinned text is a proposed delivery plan, the test must first
map each claimed symbol to the pinned implementation status rather than assuming every
sketched API is available.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md):

- **Virtualized resources.** `MeshDevice`, virtual command queues, `MeshBuffer`, and
  `MeshAllocator` present global-looking objects over per-device resources. Review how
  mesh coordinates, buffer regions, and queue IDs translate at each local device.

- **Workload control.** `MeshWorkload` and the controller distribute programs and
  synchronization across the mesh. The virtualization contract is correct only if
  ownership, enqueue order, completion, and failure are preserved when one logical
  action becomes many physical actions.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The architecture virtualizes many devices behind TT-NN mesh
    abstractions—`MeshDevice`, virtual command queues, `MeshBuffer`/allocator, and
    `MeshWorkload`—so programs can scale without manually issuing every per-device
    operation. It coordinates logical intent with distributed physical ownership.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A logical mesh coordinate must resolve to the same owning physical device throughout
    buffer and workload lifetimes. Queue dependencies, allocation views, and per-device
    programs must collectively implement the logical operation exactly once on every
    intended shard.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A TT-NN distributed operation targets a logical mesh tensor → a virtual command
    queue accepts the work → `MeshWorkload` expands or references per-device programs →
    mesh buffers resolve local allocations → owning controllers submit commands →
    fabric/CCL moves cross-device data → logical completion is reported.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Class names, virtual-CQ implementation, allocator metadata,
    workload APIs, host scaling model, mesh sizes, and fabric integration are tied to
    the dated architecture specification.

    **Durable model.** Virtualize placement behind stable logical identities, preserve
    explicit ownership and lifetimes, lower global work into local programs plus
    communication, and ensure logical completion aggregates every required physical
    dependency.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
