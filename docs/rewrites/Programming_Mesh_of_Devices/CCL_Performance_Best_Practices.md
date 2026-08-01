<!-- rewrite-status: improved-draft -->
# CCL Performance Tuning Tips for tt-metal

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md"><code>tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned report treats CCL latency as four causal costs: topology/routing, cross-device
dispatch skew, ownership synchronization, and packet overhead. These cannot be tuned
interchangeably. A ring algorithm needs a fabric configuration and physical links that
actually close the ring; trace mode removes repeated dispatch timing differences but
does not reduce bytes; persistent buffers remove the initial ownership protocol but not
the collective itself; packet size changes header/amortization and L1 pressure. The
architecture workflow is therefore to identify the dominant term for the model's
message shapes before applying a knob.

Fabric must be initialized before `open_mesh_device` because router resources and routes
are part of device setup, not an operation-local choice. In this pinned scope,
`FABRIC_1D_RING` is generally the preferred CCL choice when the hardware/mesh supports
it; the `FABRIC_2D` variants are stated as less suitable for TT-NN CCLs. That guidance is
not permission to request a ring on an incompatible physical topology.

### How work and data move

For `ttnn.experimental.all_gather_async`, each device contributes a local shard. The
selected topology determines which peer receives each packet and relays later chunks;
`num_links` determines the EDM link resources used. The report's rule of thumb is 4 on
Wormhole, 2 on Blackhole, and 1 on T3K, but these are pinned hardware-specific starting
points to verify. Every participant ultimately writes the gathered tensor into its
destination buffer, and the multi-device global semaphore tracks the operation's
cross-device progress.

Without trace, host dispatch reaches devices sequentially. Later devices start their
kernels later, creating device skew. A CCL's internal cross-device synchronization makes
the earliest devices wait for the latest, so dispatch latency appears on the collective
critical path. Trace replay supplies already-captured work to devices without that
per-iteration host sequencing, reducing the skew rather than accelerating Ethernet.

The default async CCL cannot assume a destination is free when devices are at different
iterations. It performs an initial global synchronization to establish that the CCL owns
the destination/intermediate space. The pinned optimization allocates semaphores and
intermediate tensors at global scope and round-robins a pool—eight entries in the
example—so unrelated operations do not allocate over those reserved addresses.
Round-robin selection alone does not make a slot safe: the caller must ensure that the
prior collective using that slot has completed on every participant before the index wraps.
Passing an `intermediate_tensor` plus `multi_device_global_semaphore` to
`ttnn.experimental.all_reduce_async`, or a `persistent_output_buffer` to
`all_gather_async`, gives the operation that ownership proof and allows it to skip the
initial Fabric transaction. Pool index reuse is therefore a synchronization decision,
not merely allocator caching.

Finally, `FabricRouterConfig.max_packet_payload_size_bytes` sets a global maximum at
fabric initialization. The default payload is approximately 4352 B (four Bfp8_b tiles).
The report gives pinned caps of 7616 B on Wormhole and 15232 B on Blackhole and requires
L1 alignment. A larger payload amortizes packet overhead but occupies more buffering and
can change fairness/latency; it affects every CCL in the model.

### What must never break

All participants must invoke a compatible collective order with matching tensor
partition, dimension, topology, link count, and semaphore generation. A persistent or
intermediate buffer slot cannot be reused until the prior operation using that slot has
completed on every relevant device. Trace replay requires captured addresses, program
configuration, fabric configuration, and resource lifetimes to remain valid. Packet
payload must respect L1 alignment and the pinned architecture cap. Violating these rules
can corrupt a later iteration even when one isolated collective test passes.

### Where the report makes it concrete

The report's example combines the mechanisms but makes their ownership visible:
`ttnn.create_global_semaphore(mesh_device, sub_device_crs, 0)` allocates one semaphore
per pool slot; `ttnn.from_torch(..., memory_config=intermediate_mem_config,
mesh_mapper=ttnn.ShardTensor2dMesh(...))` allocates matching intermediates;
`i % num_buffers` selects the next candidate slot. Eight entries increase the reuse
distance but are not themselves a completion proof; safe reuse still depends on the
number of in-flight iterations and their synchronization. In its sample shape,
`all_gather [1,1,768,256]` moves from about 54 microseconds naïvely to about 45
microseconds with preallocation and an 8 KB packet. That one data point demonstrates a
combined effect; it does not isolate how many microseconds each mechanism contributes.

### How the decision is tested

Use an ablation matrix at the model's real collective shapes: baseline; trace only;
persistent resources only; packet-size change only; then combinations. Record per-device
kernel start timestamps to measure skew, initial-sync duration, Fabric bytes/link
utilization, end-to-end collective latency, and model latency. Sweep pool depth while
checking that a slot is never reused in flight, and sweep aligned packet payloads through
the legal pinned range. Test both warm steady state and startup; trace/preallocation can
look excellent after compilation while leaving first-token latency unchanged. The
expected signatures differ: trace narrows device start spread, preallocation removes an
initial synchronization transaction, and packet tuning changes transfer efficiency.
Select on end-to-end model CCL time, because the global packet setting may improve one
all-gather while degrading another collective shape.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md):

- **Fabric selection.** `mesh_device` topology plus `FABRIC_1D`, `FABRIC_1D_RING`,
  `FABRIC_2D`, and torus variants select available routes and links. The collective
  algorithm and packetization should match that topology instead of assuming a ring or
  full wraparound exists.

- **Steady-state measurement.** Preallocate buffers, hold operation parameters and
  packet size constant, warm program caches, then use trace mode only when replay
  invariants hold. Compare payload bandwidth and link balance, not launch time hidden
  inside a single aggregate number.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report tunes collective communication by removing avoidable setup/dispatch
    overhead and matching packetization, buffers, topology, and operation-specific
    parameters to the message, so links and fabric routers remain supplied.
    Optimization begins only after collective correctness is established across ranks.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every rank must invoke compatible collectives in the same logical order with
    matching tensor counts/shapes, and source/output buffers must remain valid until
    completion. Trace replay or pre-allocation may optimize execution only while
    captured addresses and lifetimes stay valid.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A tensor shard is read from each participant → the CCL operation packetizes it →
    fabric/links forward packets along the collective topology → intermediate nodes
    reduce, gather, or relay → final shards land in destination buffers → completion
    makes the collective result visible to subsequent compute.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Trace APIs, CCL algorithms, packet-size knobs, buffer counts,
    link topology, queue behavior, and best parameter values depend on the collective,
    message size, chip generation, and TT-Metal revision.

    **Durable model.** Initialize once, reuse storage, separate launch overhead from
    wire time, choose an algorithm/topology from traffic volume, keep enough packets in
    flight, overlap only with explicit dependencies, and validate all ranks under the
    same schedule.

## Source and delta

- **Original source:** [`tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
