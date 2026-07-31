<!-- rewrite-status: seed -->
# Programming Mesh of Devices with TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md"><code>tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1086 |
| Section headings | 41 |
| Fenced code examples | 36 |
| Markdown images | 2 |

### Section outline

- Contents
- 1. Overview
- 2. MeshDevice
  - 2.1 System Topology
    - 2.1.1 SystemMesh Visualization
  - 2.2 MeshDevice Management
    - 2.2.1 MeshDevice Initialization/Close
    - 2.2.1 MeshDevice Visualization
  - 2.3 Controlling Device Visibility
    - Usage Examples
    - Running Concurrent Processes On A Single Host
  - 2.4 Distributed Process Launch with tt-run
    - 2.4.1 Overview and Design Philosophy
    - 2.4.2 Configuration and Usage
    - 2.4.3 Usage Patterns
- 3. Distributing Tensor to MeshDevice
  - 3.1 Distribution Strategies
  - 3.2 Programming Example: Sharding
- 4. Single-Program Multiple Device
  - 4.1 Execution Model
  - 4.2 Single Device to Multiple Device Execution
    - 4.2.1 Single Device Execution
    - 4.2.2 Mesh Device Execution
- 5. MeshDevice and Collective Communication Library (CCL)
- … 17 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Define the logical mesh tensor semantics first—partition or
   replication, mesh shape, device mapping, operation scope, collective boundary, and
   composition—before choosing physical devices or launch mode.

2. **Flow to make explicit.** Draw host tensor mapping into mesh shards/replicas, per-device
   TT-NN/SPMD execution, collective communication, mesh completion, composition/readback,
   and resource teardown.

3. **Invariant to prove.** Prove logical mesh coordinates map stably to owned physical
   devices and that distribute/compose preserves every logical element; all collective
   participants must agree on order, count, shape, and communicator.

4. **TT-Metal evidence to connect.** Connect setup and isolation to `TT_VISIBLE_DEVICES`,
   `/dev/tenstorrent/<id>`, `TT_METAL_CACHE`, `MeshDevice`, mapper/composer APIs, and the
   visible-device multiprocess test path named by the report.

5. **Experiment and expected observation.** Run the same operation on one-device and
   multi-device meshes, compose results, and compare with host reference; expected result:
   semantic parity plus per-device work/communication matching the declared distribution.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
