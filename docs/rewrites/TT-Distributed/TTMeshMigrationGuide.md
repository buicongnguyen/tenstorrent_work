<!-- rewrite-status: improved-draft -->
# TTNN Device to MeshDevice Migration Guide

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md"><code>tech_reports/TT-Distributed/TTMeshMigrationGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to separate mechanical ownership/API migration from
actual distribution. First reproduce single-device behavior on a one-device
`MeshDevice`; only then choose sharding, replication, and multi-device collectives.

### How work and data move

The complete path is original `CreateDevice`/buffer/queue/operation/close alongside
`open_mesh_device`, mesh tensor aggregation/distribution, mesh-aware operation,
compose/readback, synchronization, and teardown.

### What must never break

The non-negotiable invariant is that the one-device mesh preserves tensor contents,
operation order, completion, and lifetime before adding another device; each
distribution change must have an explicit inverse composition and parity test.

### Where the report makes it concrete

The report makes the decision concrete by connecting migration steps to `CreateDevice`,
`ttnn::open_device`, `ttnn::open_mesh_device`, `CreateDevices`, `get_device_tensors`,
`aggregate_as_tensor`, and `aggregate_as_tensor(host_tensors).to(mesh_device)`.

### How the decision is tested

The controlled procedure is to convert one representative program to a one-device mesh,
then add a second device with one mapping change. **Expected observation:** parity at
stage one and an attributable, reversible distribution delta at stage two.

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
