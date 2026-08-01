<!-- rewrite-status: improved-draft -->
# Programming Multiple Meshes

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md"><code>tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Multi-Mesh exists for a different dependency graph than Big-Mesh. In Big-Mesh, ranks
cooperate on one logical mesh and execute the same operation sequence in lockstep; that
fits tensor/data parallel work whose partials participate in collectives. In Multi-Mesh,
each rank owns an independent mesh with its own kernels, allocations, and execution
state. Stages may run different code and progress asynchronously, exchanging only
declared tensors through sockets. That isolation fits pipeline parallelism, heterogeneous
stage sizes, and separate models, but removes implicit shared state: every cross-stage
edge needs topology, endpoint, buffer, and completion contracts.

The architecture separates three descriptions that solve different ambiguity. A Mesh
Graph Descriptor (MGD) says which meshes exist and how physical Ethernet channels
connect them. Rank bindings say which process owns each `mesh_id` and which PCIe devices
it can see. `SocketConfig` says which device/core endpoints exchange a particular tensor.
Combining these into application code would make the program topology-specific and let
ranks disagree; the declarative split allows early validation before costly device open.

### How work and data move

At launch, `tt-run` either consumes a legacy rank-binding YAML or performs auto
allocation from `--mesh-graph-descriptor` plus `--hosts`/mock mapping. It sets
`TT_MESH_ID`, `TT_MESH_HOST_RANK`, `TT_MESH_GRAPH_DESC_PATH`, and per-rank environment.
For Multi-Mesh, each rank has a distinct `mesh_id` and `mesh_host_rank: 0`; ranks sharing
one mesh with host ranks 0,1,... would instead be the Big-Mesh pattern. `TT_VISIBLE_DEVICES`
constrains which PCIe devices a rank can see; exclusivity comes from assigning disjoint
sets in the rank bindings/launcher configuration, because the environment variable
alone cannot prevent two processes from selecting the same device. The launcher also
isolates runtime state before `open_mesh_device` resolves that rank's mesh.

The `.textproto` MGD defines `mesh_descriptors` (architecture, device/host dimensions,
channel policy) and graph instances/connections. The report's Galaxy split creates two
4x4 Wormhole meshes and a two-channel inter-mesh connection; its Closetbox example
nests four 2x4 meshes per POD and four PODs per cluster. Initialization validates mesh
dimensions, architecture compatibility, and whether physical links can satisfy strict or
relaxed channel counts. The program then calls
`ttnn.set_fabric_config(ttnn.FabricConfig.FABRIC_2D)` before opening devices. In this
pinned report, `FABRIC_2D` is the only listed configuration supporting inter-mesh
traffic; 1-D modes are reserved for customized intra-mesh routes.

Application transfer begins with a list of `SocketConnection`s. Each pairs a sender
`MeshCoreCoord(device_coord, CoreCoord(0,0))` with its receiver counterpart; the 4x4
example creates 16 one-to-one connections. `SocketMemoryConfig(BufferType.L1, 4096)`
selects a 4 KB circular endpoint buffer; DRAM is an alternative with greater capacity
and latency. `SocketConfig` adds `sender_rank=0` and `receiver_rank=1`, and both ranks
construct `MeshSocket` from the identical config. Socket creation performs routing,
buffer, and endpoint setup, so it is reused rather than recreated per tensor.

The sender enqueues `ttnn.experimental.send_async(tensor, socket)`. The receiver first
allocates a tensor with a matching `.spec`, then calls `recv_async`. The socket's
circular state supplies flow control so a producer cannot lap an unconsumed receiver;
Fabric packets carry data and completion metadata. Both calls are non-blocking, allowing
stage overlap. A dependent device op implicitly waits for received data, while
`ttnn.synchronize_device` gives an explicit device completion point and
`ttnn.distributed_context_barrier()` coordinates process teardown.

### What must never break

Every physical device must have one process owner, every rank must resolve the same MGD,
and each bound `mesh_id` must exist with the expected shape. Fabric configuration occurs
before any mesh opens, and the live link set must satisfy the chosen MGD policy. Both
socket endpoints must use matching connection order, ranks, buffer placement/size, and
tensor spec; no core may appear twice in one socket's connection list. The receiver
buffer must outlive `recv_async`, and the sender cannot overwrite socket space that flow
control has not reclaimed. Async completion must be respected before consuming output,
reusing resources, or closing a device. A final process barrier prevents one rank from
tearing down Fabric while its peer still transfers.

### Where the report makes it concrete

The pinned two-stage test makes control and data ownership explicit. Both ranks seed and
construct the same 1024x1024 sharded input so they agree on tensor metadata. Rank 0
computes ReLU and sends; rank 1 preallocates from `ttnn_input.spec`, receives, computes
Exp, composes with `ConcatMesh2dToTensor`, and checks
`torch.exp(torch.relu(torch_input))`. The duplicated initial tensor is a test convenience
for matching spec/reference, not a requirement that production receivers duplicate
payload. `create_socket_pair` provides the same transport pattern for two MeshDevices in
one process without distributed rank exchange.

The cost model follows the ownership boundary: Multi-Mesh gains independent scheduling,
failure domains, and pipeline overlap, but pays socket buffers, point-to-point transfer,
and stage balancing. A Big-Mesh avoids explicit stage sockets for collective-compatible
work but requires uniform lockstep state. Each can contain the other—multiple independent
meshes may internally use TP/DP—so the choice belongs at each communication edge.

### How the decision is tested

Validate in layers. Run `tt-run --dry-run --verbose` and inspect rank-tagged device
visibility, mesh IDs, MGD path, and cache isolation. Initialize with strict mode on a
known-good cluster and confirm invalid dimensions, duplicate ownership, or missing links
fail before workload execution; use relaxed policy only when reduced routing planes are
an accepted tradeoff. Next send a coordinate-coded tensor through every socket
connection and assert exact shape, dtype, layout, per-device placement, and value order.
Stress multiple sends with a deliberately slow receiver to verify flow control rather
than buffer overwrite.

Finally pipeline ReLU -> send/recv -> Exp as in the report. Measure stage compute,
one-time socket setup, reused transfer, sender/receiver wait, and steady-state cadence.
Sweep L1/DRAM buffer size and in-flight microbatches while preserving the final barrier.
A useful mapping overlaps stages without making the slowest stage or socket buffer the
new bottleneck; correctness must match the composed host reference.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md):

- **Deployment description.** The `.textproto` and `tt_metal/fabric/MGD_README.md`
  define mesh groups, hosts, and fabric connectivity consumed by `tt-run`. Validate that
  every physical device appears in the intended mesh exactly once.

- **Process identity.** `mesh_id`, `mesh_host_rank`, and `TT_VISIBLE_DEVICES` connect a
  launched process to its local portion of a logical mesh. A mismatch can produce a
  valid local open on the wrong global rank, so log these values before collective
  traffic begins.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report extends programming from one mesh to several meshes and hosts by
    describing physical topologies, mesh-graph descriptors, rank bindings, launch,
    multiprocessing, and fabric configuration. The central difficulty is consistent
    global identity across independent controllers.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every physical device must have one unambiguous owner/rank, every process must
    interpret the same mesh graph and bindings, and cross-mesh communication must be
    configured before dependent work is submitted. Conflicting ownership or collective
    order can hang the system.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A mesh-graph descriptor defines logical meshes and connectivity → `tt-run`/the
    launcher binds ranks and processes to local devices → each process opens its mesh →
    fabric links and routes are configured → local SPMD work executes → cross-mesh
    operations synchronize through the shared topology.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Descriptor schema, rank-launch syntax, process model,
    supported topologies, fabric modes, and resource limits are current-runtime details.

    **Durable model.** Keep topology and rank assignment declarative, enforce single
    ownership, separate launch/control-plane coordination from data-plane traffic,
    validate the graph on every process, and make distributed failure diagnostics rank
    aware.

## Source and delta

- **Original source:** [`tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
