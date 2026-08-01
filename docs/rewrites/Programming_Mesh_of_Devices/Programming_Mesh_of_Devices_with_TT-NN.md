<!-- rewrite-status: improved-draft -->
# Programming Mesh of Devices with TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md"><code>tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

`MeshDevice` is designed as a logical 2-D device because TT-NN operations need one
dispatch target while distributed tensors still need explicit ownership. The runtime can
broadcast compilation artifacts, distribute commands through mesh-aware queues, and run
the same op on every constituent device (SPMD), but it does not guess whether tensor
dimension 0, 3, or neither is partitioned. That split is deliberate: coordinated
dispatch removes repetitive host control, while mesh mappers preserve the information
needed to reason about memory capacity and communication.

The core architectural object is therefore a MeshTensor: one logical tensor plus a
collection of per-device shards or replicas indexed by mesh coordinate. An elementwise
op such as `ttnn.gelu` is local when every output element depends only on its local
input. A tensor-parallel linear layer can produce a partial width shard, but a later
layer needing the full width introduces an explicit `ttnn.all_gather`. Making that
boundary visible prevents an abstraction from silently moving large tensors between
devices.

### How work and data move

Opening `ttnn.open_mesh_device(ttnn.MeshShape(y, x))` maps a logical rectangle onto the
physically connected system selected for the process. `ttnn.visualize_system_mesh()`
and `ttnn.visualize_mesh_device()` expose that mapping. On the host, a mapper defines
placement along each mesh axis. The report's explicit form uses
`ttnn.create_mesh_mapper(..., MeshMapperConfig(placements=[PlacementReplicate(),
PlacementShard(3)]))`; examples also use `ShardTensorToMesh(mesh_device, dim=3)` and
`ReplicateTensorToMesh(mesh_device)`. `ttnn.from_torch` constructs the host MeshTensor,
and supplying `device=mesh_device` or calling `ttnn.to_device` allocates/transfers the
corresponding shard to each device's DRAM.

For the report's `(1,1,32,64)` tensor on a 1x2 mesh, sharding dimension 3 produces two
`(1,1,32,32)` device tensors: values 1 on device 0 and values 2 on device 1. A call to
`ttnn.gelu(mesh_tensor)` dispatches the same kernel to both devices and preserves that
partition because GELU is elementwise. In contrast, ring
`ttnn.all_gather(mesh_tensor, dim=3, num_links=1)` circulates shards until every device
owns their concatenation. A line gather with `cluster_axis=0` on a 2x4 mesh runs four
independent two-device lines; each device's width grows from 32 to 64, not to the full
eight-device width. `cluster_axis` therefore defines the participant set, while `dim`
defines tensor concatenation.

The same ownership rules define parallel strategies. Data parallel shards activations
on batch dimension 0 with `ShardTensorToMesh` and replicates Falcon MLP parameters; no
collective is needed between independent examples before host composition with
`ConcatMeshToTensor`. Tensor parallel replicates activations, shards both linear weights
on width, and inserts all-gather after GELU so the second linear sees the required full
activation. Hybrid execution calls `mesh_device.create_submeshes(MeshShape(2,4))`, runs
one model replica per submesh, then captures the whole parent-mesh sequence with
`begin_trace_capture` and replays it through `execute_trace` so replicas launch in
parallel.

Process-level ownership sits below these tensor semantics. `TT_VISIBLE_DEVICES` limits
PCIe-visible cards before device open; each concurrent process also needs a distinct
`TT_METAL_CACHE` to prevent compilation-cache races. `tt-run` supplies rank bindings,
`TT_MESH_ID`, `TT_MESH_HOST_RANK`, the MGD path, and per-rank isolation for multi-process
big-mesh or independent-mesh launches.

### What must never break

Mapper and composer must be inverses for the declared logical tensor: every shard has the
expected shape/order, every logical element has the intended owner(s), and replication
contains identical values. Each local operator's dependency must be satisfiable from its
local shard; otherwise an explicit collective is required before it executes. All
collective participants must agree on participant axis, operation order, tensor
dimension, shape, layout, dtype, topology, and link count. Logical mesh coordinates
must map stably to process-owned physical devices for the lifetime of tensors and traces.

Visibility and cache isolation must be established before opening devices. Two processes
cannot own the same PCIe devices, and a process cannot interpret local device ID 0 as a
global physical ID after `TT_VISIBLE_DEVICES` remapping. Memory addresses and program
configuration referenced by a trace cannot be repurposed before replay completes. The
pinned report shows `release_trace` immediately after a non-blocking `execute_trace` but
does not define whether release is queue-ordered or which Python handles the runtime
retains, so host-object lifetime should be verified against the pinned API rather than
inferred from that short example.

### Where the report makes it concrete

The Falcon MLP examples expose the communication decision. In data parallel, batch 4 is
split over a 1x4 mesh and both `dense_h_to_4h` and `dense_4h_to_h` weights are replicated;
each device computes a complete result for its samples. In tensor parallel on a 2x4
mesh, width-sharded weights reduce per-device parameter memory, but
`gelu = ttnn.all_gather(gelu, dim=3, num_links=1)` becomes a mandatory dependency
between the linears. The benefit—larger models and distributed compute—comes with
collective latency and replicated activation pressure. The pinned hybrid Llama example
reports near-linear aggregate throughput across larger replica count, but slightly lower
per-user throughput; those are distinct scaling metrics rather than a single “3.8x
faster” claim.

### How the decision is tested

Start with a coordinate-coded host tensor and inspect every per-device shard before and
after `to_device`. Execute a local op, compose with the matching
`ConcatMeshToTensor`/2-D composer, and compare exactly or with an appropriate numerical
tolerance. For all-gather, assert both per-device output shape and concatenation order;
test ring and line participant sets separately. For DP and TP, compare the complete
Falcon output with the same PyTorch reference while recording per-device memory,
operation time, collective bytes, and slowest-device completion.

Then test control-plane assumptions: print visible PCIe IDs per process, use unique cache
paths, run `tt-run --dry-run` to inspect rank environments, and verify topology with the
visualizers. Introduce one deliberate mapper or `cluster_axis` mismatch and confirm the
shape/element assertion catches it before interpreting performance. A valid optimization
shows the declared distribution in memory, the predicted collective at the dependency
boundary, correct recomposition, and improved end-to-end throughput—not merely parallel
kernel launches.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md):

- **Process isolation.** `TT_VISIBLE_DEVICES`, `/dev/tenstorrent/<id>`, and
  `TT_METAL_CACHE` decide which physical devices and cache namespace a process owns.
  Multiprocess tests must assign disjoint ownership or an explicitly supported sharing
  model before opening a mesh.

- **Tensor distribution.** `MeshDevice` plus mapper/composer APIs convert a logical
  tensor into per-device shards and reconstruct the result. Record mesh shape, device
  ordering, shard dimension, replication rules, and output composition so rank-local
  success implies the intended global tensor.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The task is expressing one logical computation across a mesh: open devices as a
    coordinated `MeshDevice`, distribute or replicate tensors, execute SPMD operations,
    run collectives, and compose results without leaking physical-device bookkeeping
    into every model layer.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The mapping between logical mesh coordinates and physical devices must remain stable
    for a tensor's lifetime, and distribute/compose operations must preserve the
    tensor's logical element set. All participants in a collective must agree on shape,
    order, and communicator.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A host tensor enters a mapper → shards or replicas are placed in per-device mesh
    buffers → the same TT-NN operation runs on participating devices → CCL moves/reduces
    data when the model crosses shard boundaries → a composer reconstructs the requested
    host/logical tensor.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** `MeshDevice`, mapper/composer APIs, supported mesh shapes,
    collective implementations, async modes, and topology details are tied to the
    current TT-NN distributed runtime.

    **Durable model.** Separate logical partitioning from physical placement, make
    distribution reversible, use SPMD where possible, introduce communication only at
    true dependency boundaries, and test both local shards and recomposed results.

## Source and delta

- **Original source:** [`tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
