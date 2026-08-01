<!-- rewrite-status: improved-draft -->
# TTNN Device to MeshDevice Migration Guide

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md"><code>tech_reports/TT-Distributed/TTMeshMigrationGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The migration is an ownership change, not just a class rename. In the pinned design,
TT-NN stops managing one tensor and one dispatch thread per exposed device; TT-Metal
owns a `MeshDevice`, lock-step `MeshBuffer` allocations, and `MeshWorkload` dispatch.
A 1x1 unit mesh preserves explicit single-chip control while using the same abstraction
as a full cluster. This removes the invalid hybrid state where user code interleaves a
mesh handle with a raw `Device` already owned by that mesh. It also explains the key
limitation: buffers on all member devices receive the same address, so arbitrary
per-device addresses and tensors from different mesh owners cannot be aggregated.

### How work and data move

C++ device creation changes from `CreateDevice(device_id)` to
`distributed::MeshDevice::create_unit_mesh(device_id)`; `ttnn::open_device` becomes
`ttnn::open_mesh_device`, and `CreateDevices` becomes `create_unit_meshes`. The returned
`shared_ptr` owns teardown through RAII, with `device->close()` only for early close.
Submission moves from `device->command_queue()` to `mesh_command_queue()`: a manual
`Program` is inserted with `workload.add_program(device->get_view().coord_range(),
std::move(program))`, then passed to `distributed::EnqueueMeshWorkload`.

Memory follows the same lowering. `allocate_tensor_on_device(tensor_spec,
device.get())` is preferred; direct buffers combine a `ReplicatedBufferConfig` or
other `MeshBufferConfig` with `DeviceLocalBufferConfig` in `MeshBuffer::create`.
`WriteShard` and `ReadShard` select a mesh coordinate rather than pretending the
distributed object is a single raw buffer. `get_device_tensors` now returns a
single-device view backed by the same `MeshBuffer`; device tensors may be
`aggregate_as_tensor` only when they share that backing buffer. Independent host
shards must be aggregated first and then transferred with
`aggregate_as_tensor(host_tensors).to(mesh_device)`.

### What must never break

No code may retain an `IDevice`/`Device` pointer or call `command_queue()` through a
`MeshDevice`; the pinned implementation promises an exception for that queue access.
All device shards of one logical tensor must reference the same lock-step allocation,
and no raw device may be operated independently while managed by the mesh. RAII must
outlive queued work. Event semantics also split deliberately: `ttnn::record_event` is a
mesh-CQ-to-mesh-CQ event and avoids host propagation, whereas
`record_event_to_host` creates the evidence required by `event_synchronize`. Replacing
the old host-visible event mechanically with the local form can make host code observe
unfinished work.

### Where the report makes it concrete

The old `CreateBuffer` configuration collapses into two scopes: the report's example
sets page size and buffer type in `DeviceLocalBufferConfig`, then requests the same
`dram_buffer_size` on every device through `ReplicatedBufferConfig`. Likewise the old
`WriteToBuffer` becomes a coordinate-aware `WriteShard`, and `ReadFromBuffer` becomes
`ReadShard`. This preserves the distinction between a distributed allocation and one
selected shard. The source also flags a storage-type compatibility edge: tensors that
previously appeared as `OwnedStorage` can surface as `MultiDeviceHostStorage` with one
owned buffer, so exhaustive storage-type branches must be updated rather than cast.

### How the decision is tested

First convert to `create_unit_mesh` without changing tensor layout and compare buffer
contents, queue ordering, event completion, and output bit-for-bit. Exercise both
mesh-local and host-visible events to prove the host waits only on the latter. Then use
two devices: verify addresses are equal, `get_device_tensors` yields correct views, and
host-first aggregation composes distinct shards in the intended order. Negative tests
should attempt `command_queue()`, aggregation across unrelated `MeshBuffer`s, and mixed
raw-device/mesh use; each must fail explicitly. Finally profile host threads and
metadata-return latency. The report claims simplification and significant performance
benefit at its migration snapshot, but those benefits must be measured separately from
correctness and not inferred merely because the API compiles.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md):

- **Open-device migration.** Compare `CreateDevice` and `ttnn::open_device` with
  `ttnn::open_mesh_device`/`CreateDevices`: lifetime, device ordering, queue creation,
  and teardown move from one device handle to a mesh-owned set.

- **Tensor aggregation.** `get_device_tensors`, `aggregate_as_tensor`, and
  `aggregate_as_tensor(host_tensors).to(mesh_device)` distinguish device shards, host
  components, and a logical mesh tensor. Preserve shard order and placement so migration
  does not silently replicate or permute data.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The guide migrates C++ code written for a single `Device` to `MeshDevice` and
    mesh-aware buffers/queues while preserving single-device behavior first, then enabling
    multi-device distribution deliberately. The first milestone is compatibility, not
    immediate scaling.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A one-device mesh must reproduce the original program's tensor contents, addresses
    within the new abstraction, operation order, completion semantics, and resource
    lifetime. Distribution must not be introduced implicitly during a mechanical API
    migration.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Original device creation becomes a one-device mesh open → device tensors become mesh
    tensors/buffers with an explicit mapper → operations submit through mesh-aware APIs
    → results are composed/read back → synchronization and close release all mesh-owned
    resources.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Renamed APIs, unsupported features, C++ migration steps,
    queue types, and temporary limitations apply to the documented TT-NN revision.

    **Durable model.** Migrate through a compatibility configuration, keep behavior
    parity tests, change construction/ownership before adding distribution, and make
    mapping/composition explicit so scaling is an intentional second step.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/TTMeshMigrationGuide.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/TTMeshMigrationGuide.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
